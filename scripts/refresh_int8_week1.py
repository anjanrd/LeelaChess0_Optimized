"""Refresh the fixed naive I1 recipe with v2 calibration data only."""
import argparse
import collections
import gc
import gzip
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import chess
import numpy as np
import onnx

import complete_week1_v2 as active
from complete_week1_v2 import (PROJECT, WORK, DEST, DATA, I1_GRAPH, I1_ENGINE,
    FLOAT_ENGINE, PROTOCOL, TensorRunner, artifact, base, checkpoint, frozen,
    read, save, selected_indices, inputs, rows, verify_outputs, run_chunks,
    infer, score, load_outputs, diagnostics)

BRIDGE = PROJECT / 'models/onnx/bt3-f16-opset19.onnx'


def quantize():
    checkpoint('W1-A15','IN_PROGRESS',detail='Recalibrating fixed 160-operation naive INT8 recipe on all 1024 v2 calibration roots only.')
    frozen()
    bridge = read(PROJECT/'environment/week1-opset-bridge.json')
    assert base.sha256(BRIDGE) == bridge['bridge']['sha256']
    targets = read(PROJECT/'environment/step6-scope-v2.json')['targets']
    assert len(targets) == 160
    import torch
    import onnxruntime as ort
    site = Path(torch.__file__).resolve().parents[1]
    libraries = [site/'nvidia/cudnn/lib',site/'nvidia/cublas/lib',site/'nvidia/cuda_runtime/lib',site/'torch/lib']
    os.environ['LD_LIBRARY_PATH'] = ':'.join(str(p) for p in libraries if p.exists()) + ':' + os.environ.get('LD_LIBRARY_PATH','')
    ort.preload_dlls()
    from modelopt.onnx.quantization import int8 as modelopt_int8
    from onnxruntime.quantization import CalibrationDataReader
    class Reader(CalibrationDataReader):
        def __init__(self):
            self.data = inputs('calibration')[0].astype(np.float16); self.index = 0
        def get_next(self):
            if self.index == len(self.data): return None
            value = {'/input/planes':self.data[self.index:self.index+8]}
            self.index += 8
            if self.index % 256 == 0: print('Calibrated',self.index,'/1024',flush=True)
            return value
        def get_first(self): return {'/input/planes':self.data[:8]}
        def rewind(self): self.index = 0
    original = modelopt_int8.quantize_static
    def per_tensor(*args,**kwargs):
        kwargs['per_channel'] = False
        return original(*args,**kwargs)
    modelopt_int8.quantize_static = per_tensor
    begun = time.perf_counter()
    output = WORK/'bt3-i1-v2.onnx'
    try:
        model = modelopt_int8.quantize(str(BRIDGE),calibration_method='max',
            calibration_data_reader=Reader(),calibration_shapes='/input/planes:8x112x8x8',
            calibration_eps=['cuda:0'],nodes_to_quantize=['^'+re.escape(n)+'$' for n in targets],
            op_types_to_quantize=['MatMul'],nodes_to_exclude=[],high_precision_dtype='fp16',
            direct_io_types=True,passes=[],enable_gemv_detection_for_trt=False,
            intermediate_generated_files=[],opset=19,log_level='WARNING')
        onnx.save(model,output); del model
    finally: modelopt_int8.quantize_static = original
    model = onnx.load(output)
    producer = {o:n for n in model.graph.node for o in n.output}
    restored = []
    for node in model.graph.node:
        if node.name in targets or node.op_type in {'QuantizeLinear','DequantizeLinear'}: continue
        for i,value in enumerate(node.input):
            dq = producer.get(value)
            if dq is not None and dq.op_type == 'DequantizeLinear':
                q = producer.get(dq.input[0])
                if q is not None and q.op_type == 'QuantizeLinear':
                    node.input[i] = q.input[0]
                    restored.append({'consumer':node.name,'input':i,'float_tensor':q.input[0]})
    producer = {o:n for n in model.graph.node for o in n.output}
    initials = {i.name:i for i in model.graph.initializer}
    quantized = []
    for node in model.graph.node:
        if node.op_type != 'MatMul': continue
        dqs = [producer.get(v) for v in node.input]
        has = [d is not None and d.op_type == 'DequantizeLinear' for d in dqs]
        if any(has):
            assert all(has) and node.name in targets, node.name
            quantized.append(node.name)
            for dq in dqs:
                scale = onnx.numpy_helper.to_array(initials[dq.input[1]])
                zp = initials[dq.input[2]]
                assert scale.size == 1 and np.isfinite(scale).all() and (scale>0).all()
                assert zp.data_type == onnx.TensorProto.INT8 and np.all(onnx.numpy_helper.to_array(zp)==0)
    assert set(quantized) == set(targets)
    onnx.checker.check_model(model,full_check=True)
    onnx.save(model,output)
    assert not I1_GRAPH.exists(), 'Versioned output already exists; do not overwrite'
    shutil.copy2(output,I1_GRAPH)
    save(PROJECT/'environment/week1-v2-i1-graph.json',{'status':'passed','created_at_utc':base.now(),
        'graph':artifact(I1_GRAPH),'parent':artifact(BRIDGE),'targets':targets,
        'calibration':artifact(DATA/'calibration-inputs.npz'),'n_calibration':1024,'calibration_batch':8,
        'signed_symmetric':True,'activation_scaling':'per-tensor','weight_scaling':'per-tensor',
        'calibration_method':'max','quantized_matmuls':len(quantized),
        'adapter':'Same process-local lower-level ModelOpt adapter and shared-QDQ floating-edge restoration as historical pilot; installed packages unchanged.',
        'restored_floating_edges':restored,'seconds':time.perf_counter()-begun,'script':artifact(Path(__file__))})
    print('INT8 graph verified:',len(quantized),'targets; all 1024 calibration roots',flush=True)


def build_engine(kind,profile=(1,4,8),suffix=''):
    import torch
    import tensorrt as trt
    graph = I1_GRAPH if kind == 'I1' else PROJECT/'models/onnx/bt3-f16.onnx'
    label = ('i1' if kind == 'I1' else 'f16') + suffix
    record_path = I1_ENGINE if kind == 'I1' and not suffix else PROJECT/f'environment/week1-v2-{label}-engine.json'
    if record_path.exists():
        record = read(record_path)
        assert record['profile'] == list(profile) and record['graph'] == artifact(graph)
        assert base.sha256(record['engine_path']) == record['engine_sha256']
        return record_path
    targets = set(read(PROJECT/'environment/step6-scope-v2.json')['targets']) if kind == 'I1' else set()
    logger = trt.Logger(trt.Logger.WARNING)
    builder = trt.Builder(logger); network = builder.create_network(0)
    parser = trt.OnnxParser(network,logger)
    if not parser.parse_from_file(str(graph)):
        raise RuntimeError('\n'.join(str(parser.get_error(i)) for i in range(parser.num_errors)))
    norms = []; constrained = []
    for i in range(network.num_layers):
        layer = network.get_layer(i)
        if layer.type == trt.LayerType.NORMALIZATION:
            layer.__class__ = trt.INormalizationLayer
            layer.compute_precision = trt.float32; norms.append(layer.name)
        elif layer.type == trt.LayerType.MATRIX_MULTIPLY and layer.name not in targets:
            layer.precision = trt.float16
            if kind == 'F16': layer.set_output_type(0,trt.float16)
            constrained.append(layer.name)
    config = builder.create_builder_config()
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE,536870912)
    config.set_flag(trt.BuilderFlag.FP16); config.set_flag(trt.BuilderFlag.OBEY_PRECISION_CONSTRAINTS)
    config.clear_flag(trt.BuilderFlag.TF32)
    config.max_aux_streams = 0; config.builder_optimization_level = 3
    config.profiling_verbosity = trt.ProfilingVerbosity.DETAILED
    p = builder.create_optimization_profile()
    p.set_shape('/input/planes',*((b,112,8,8) for b in profile)); config.add_optimization_profile(p)
    begun = time.perf_counter()
    serialized = builder.build_serialized_network(network,config)
    assert serialized is not None
    path = WORK/f'bt3-{label}.plan'; path.write_bytes(bytes(serialized))
    save(record_path,{'status':'built_pending_execution_audit','kind':kind,'engine_path':str(path),
        'engine_sha256':base.sha256(path),'engine_bytes':path.stat().st_size,'graph':artifact(graph),
        'profile':list(profile),'TF32':False,'workspace_bytes':536870912,'builder_optimization_level':3,
        'max_aux_streams':0,'normalization_fp32_compute':norms,'floating_matmuls_fp16':constrained,
        'tensorrt':trt.__version__,'gpu':torch.cuda.get_device_name(0),
        'purpose':'Primary I1 pilot' if not suffix else 'Separate batch-tuning engine; exact accepted FP16 baseline preserved, not replaced',
        'build_seconds':time.perf_counter()-begun,'script':artifact(Path(__file__))})
    print('Built',label,'profile',profile,flush=True)
    return record_path


def audit_engine(record_path,batches=(1,8)):
    import torch
    import tensorrt as trt
    record_path = Path(record_path); record = read(record_path)
    runner = TensorRunner(record_path)
    planes = inputs('calibration')[0]
    for batch in batches:
        output = runner.run(planes[:batch]); verify_outputs(output,batch)
    inspector = runner.engine.create_engine_inspector(); inspector.execution_context = runner.context
    info = json.loads(inspector.get_engine_information(trt.LayerInformationFormat.JSON))
    inspected = WORK/(record_path.stem+'-inspector.json'); save(inspected,info)
    targets = set(read(PROJECT/'environment/step6-scope-v2.json')['targets'])
    mapped = set(); layers = []
    for layer in info['Layers']:
        origins = set(re.findall(r'\[ONNX Layer: ([^\]]+)\]',layer.get('Metadata','')))
        tactic = layer.get('TacticName','').lower()
        if layer.get('LayerType') in {'gemm','fusion'} and any(s in tactic for s in ['i8i8','i8f32_i8i32','s8','imma']):
            mapped |= origins & targets
            layers.append({'name':layer['Name'],'targets':sorted(origins&targets),'tactic':layer.get('TacticName'),'inputs':layer.get('Inputs'),'outputs':layer.get('Outputs')})
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA]) as profiler:
        for batch in batches: runner.run(planes[:batch])
    trace = WORK/(record_path.stem+'-kernels.json'); profiler.export_chrome_trace(str(trace))
    kernels = collections.Counter(e['name'] for e in read(trace)['traceEvents'] if e.get('cat')=='kernel')
    integer = {n:c for n,c in kernels.items() if any(s in n.lower() for s in ['i8i8','i8f32_i8i32','s8','imma'])}
    half = {n:c for n,c in kernels.items() if ('gemm' in n.lower() and any(s in n.lower() for s in ['f16f16','hgemm','half','tensorop','hmma']))}
    if record['kind'] == 'I1':
        assert mapped == targets, sorted(targets-mapped)
        assert integer
    else: assert half, 'No executed FP16 matrix kernels'
    runner.close(); del runner; gc.collect(); torch.cuda.empty_cache()
    record.update(status='passed_execution',actual_INT8_targets=len(mapped),unmapped_INT8_targets=sorted(targets-mapped) if record['kind']=='I1' else [],
        int8_layers=layers,executed_INT8_kernels=integer,executed_FP16_kernels=half,
        precision_evidence=[artifact(inspected),artifact(trace)],verified_batches=list(batches),
        precision_detail='Selected INT8xINT8/INT32 accumulation may emit FP32 dequantized intermediates, FP16 or requantized INT8. Other matrices constrained FP16 and normalization FP32 compute. QDQ ONNX source constants remain FP16; not an all-integer model.')
    save(record_path,record)
    print('Execution audited',record_path.name,'INT8 targets',len(mapped),'INT8 kernels',len(integer),'FP16 kernels',len(half),flush=True)


def quality():
    assert read(I1_ENGINE)['status'] == 'passed_execution'
    indices = selected_indices(); p = inputs('calibration')[0][indices]
    reference_records = [rows('calibration')[i] for i in indices]
    runner = TensorRunner(I1_ENGINE)
    first = run_chunks(runner.run,p,1); batch = run_chunks(runner.run,p,8)
    runner.close(); del runner; gc.collect()
    reloaded = TensorRunner(I1_ENGINE); again = run_chunks(reloaded.run,p,8)
    assert all(np.array_equal(a,b) for a,b in zip(batch,again)), 'Saved engine reload changed predictions'
    reloaded.close(); del reloaded; gc.collect()
    batch_check = diagnostics(reference_records,first,batch)
    np.savez_compressed(DEST/'I1-reload-check.npz',ids=np.array([r['id'] for r in reference_records]),**dict(zip(active.KEYS,batch)))
    infer('validation','I1_TRT')
    scoring,predictions = score('validation','I1_TRT')
    output = load_outputs('validation','I1_TRT')
    comparisons = {}
    for baseline in ['F16_TRT','R32_CUDA']:
        comparison = diagnostics(rows('validation'),load_outputs('validation',baseline),output)
        path = DEST/f'validation-I1-vs-{baseline}-drift.json'; save(path,comparison)
        comparisons[baseline] = {'summary':comparison['summary'],'wdl_mae':comparison['wdl_mae'],'report':artifact(path)}
    save(DEST/'int8-validation.json',{'status':'passed_valid_pilot','created_at_utc':base.now(),
        'scoring':scoring,'comparisons':comparisons,'saved_engine_reload_byte_equal_outputs':True,
        'batch1_vs_batch8_diagnostics':batch_check,'final_test_evaluated':False,
        'interpretation':'Naive quantization starting point; numerical/quality degradation is recorded, not a recovery pass or a reason to alter scope.'})
    print('INT8 validation accuracy',scoring['strata']['all']['accuracy'],flush=True)


def wrap():
    assert read(DEST/'int8-validation.json')['status'] == 'passed_valid_pilot'
    destination = PROJECT/'models/wrapped/bt3-i1-v2.pb.gz'
    assert not destination.exists()
    binary = base.RUNTIME/'build/lc0-tools/lc0'
    command = [str(binary),'onnx2leela','--input='+str(I1_GRAPH),'--output='+str(destination),
        '--input-format=INPUT_CLASSICAL_112_PLANE','--policy-format=POLICY_ATTENTION',
        '--value-format=VALUE_WDL','--moves-left-format=MOVES_LEFT_V1',
        '--onnx-input=/input/planes','--onnx-output-policy=/output/policy',
        '--onnx-output-wdl=/output/wdl','--onnx-output-mlh=/output/mlh']
    result = subprocess.run(command,check=True,capture_output=True,text=True)
    with gzip.open(destination,'rb') as f: assert I1_GRAPH.read_bytes() in f.read()
    described = subprocess.run([str(binary),'describenet','--weights='+str(destination)],check=True,capture_output=True,text=True)
    save(PROJECT/'environment/week1-v2-int8-pilot.json',{'status':'verified_pending_batch_sweep',
        'created_at_utc':base.now(),'graph':artifact(I1_GRAPH),'engine':artifact(read(I1_ENGINE)['engine_path']),
        'wrapper':artifact(destination),'wrapper_embedded_graph_byte_identical':True,
        'wrapper_command':command,'wrapper_metadata':result.stdout+result.stderr,
        'native_description':described.stdout+described.stderr,
        'graph_audit':artifact(PROJECT/'environment/week1-v2-i1-graph.json'),
        'precision_audit':artifact(I1_ENGINE),'validation':artifact(DEST/'int8-validation.json'),
        'lc0_GPU_integration':'UNVERIFIED; Person B and joint C1', 'INT8_test_evaluated':False})
    frozen()
    print('Wrapper embedded graph verified; batch sweep still pending',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['quantize','build','audit','quality','wrap'])
    action = parser.parse_args().action
    {'quantize':quantize,'build':lambda:build_engine('I1'),'audit':lambda:audit_engine(I1_ENGINE),
     'quality':quality,'wrap':wrap}[action]()
