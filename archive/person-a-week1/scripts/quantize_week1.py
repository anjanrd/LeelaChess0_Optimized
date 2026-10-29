"""Registered scope review, validated opset bridge and bounded naive INT8 pilot."""
import argparse
import gc
import json
import os
import re
import gzip
import subprocess
import time
from pathlib import Path

import numpy as np
import onnx

from week1_common import PROJECT, RUNTIME, TensorRunner, artifact, base, frozen, progress, read, save

WORK = RUNTIME / "int8"
BRIDGE = PROJECT / "models/onnx/bt3-f16-opset19.onnx"


def review():
    frozen()
    profile = read(PROJECT / "environment/week1-baseline-profile.json")
    assert profile["status"] == "passed"
    rows = read(PROJECT / "environment/step6-inventory.json")["matrix_operations"]
    old = [r["name"] for r in rows if r["selected"]]
    expanded = [r["name"] for r in rows if r["weight"] and all(s["K"] >= 16 and s["N"] >= 16 for s in r["shapes_by_batch"].values())]
    assert len(old) == 127 and len(expanded) == 160
    candidate = {"recorded_at_utc": base.now(), "status": "reviewed_pending_registered_pilot", "authority": "User authorized autonomous remaining A-side Week 1 tasks and evidence-based scope review",
        "profile_sha256": base.sha256(PROJECT / "environment/week1-baseline-profile.json"),
        "old_scope_sha256": base.sha256(PROJECT / "environment/step6-scope.json"),
        "profiled_excluded_weighted_fraction": {b: v["excluded_weighted_layer_fraction"] for b,v in profile["F16_TRT"].items()},
        "rationale": "Excluded weighted layers are material in measured F16 layer time at batch 1; test expanding the large weight matrices rather than relying on 97% MAC coverage",
        "candidates": {"127": old, "160": expanded}, "preferred_if_registered_checks_pass": "160",
        "tiny_weighted_exclusions": [r["name"] for r in rows if r["weight"] and r["name"] not in expanded],
        "dynamic_products": "31 remain floating as a separate explicit scope choice; no fixed learned weights in these products",
        "probe_protocol": "environment/week1-profile-protocol.json", "scope_selection_not_based_on_accuracy": True,
        "final_common_scope": "pending actual execution and registered relative latency checks in Step 7"}
    save(PROJECT / "environment/step6-scope-review.json", candidate)
    progress("W1-A06R", "DONE", "environment/step6-scope-review.json", "Reviewed scope; 127 versus expanded 160 registered for pilot. Final scope awaits actual execution and latency evidence.")
    progress("W1-A07", "IN_PROGRESS", detail="7A registered two coverage candidates, legal pilot calibration and unchanged baselines; validating opset bridge next.")


def session(path):
    import onnxruntime as ort
    ort.preload_dlls()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.log_severity_level = 3
    result = ort.InferenceSession(str(path), sess_options=options, providers=[("CUDAExecutionProvider", {"use_tf32": "0", "cudnn_conv_use_max_workspace": "0"}), "CPUExecutionProvider"])
    result.disable_fallback()
    return result


def bridge():
    WORK.mkdir(parents=True, exist_ok=True)
    frozen()
    source = PROJECT / "models/onnx/bt3-f16.onnx"
    model = onnx.load(source)
    converted = onnx.version_converter.convert_version(model, 19)
    assert [i.SerializeToString() for i in model.graph.initializer] == [i.SerializeToString() for i in converted.graph.initializer]
    assert [n.SerializeToString() for n in model.graph.node] == [n.SerializeToString() for n in converted.graph.node]
    onnx.checker.check_model(converted, full_check=True)
    onnx.save(converted, BRIDGE)
    del model, converted
    gc.collect()
    with np.load(PROJECT / "data/pilot/inputs.npz", allow_pickle=False) as data:
        planes = data["planes"][:16].astype(np.float16)
    results = []
    for path in [source, BRIDGE]:
        runner = session(path)
        batches = {}
        for batch in [1, 8]:
            chunks = [runner.run(base.OUTPUTS, {"/input/planes": planes[s:s+batch]}) for s in range(0,16,batch)]
            batches[str(batch)] = [np.concatenate([c[j] for c in chunks]) for j in range(3)]
        results.append(batches)
        del runner
        gc.collect()
    assert all(np.array_equal(a,b) for batch in ['1','8'] for a,b in zip(results[0][batch],results[1][batch]))
    save(PROJECT / "environment/week1-opset-bridge.json", {"status": "passed", "verified_at_utc": base.now(),
        "source": artifact(source), "bridge": artifact(BRIDGE), "opsets": [17,19], "node_and_initializer_serialization_unchanged": True,
        "comparison": "Bit-identical CUDA FP16 outputs for original versus bridge on 16 legal pilot positions at batches 1 and 8",
        "baseline_engine": "Exact accepted TensorRT engine retained; original versus bridge graph semantics and parameters unchanged; no replacement FP16 engine built",
        "script_sha256": base.sha256(__file__)})
    print("7B: opset bridge checked; nodes/weights unchanged and outputs bit-identical", flush=True)


def quantize(key):
    assert read(PROJECT / "environment/week1-opset-bridge.json")["status"] == "passed"
    targets = read(PROJECT / "environment/step6-scope-review.json")["candidates"][key]
    import torch
    import onnxruntime as ort
    site = Path(torch.__file__).resolve().parents[1]
    libraries = [site / 'nvidia/cudnn/lib', site / 'nvidia/cublas/lib', site / 'nvidia/cuda_runtime/lib', site / 'torch/lib']
    os.environ['LD_LIBRARY_PATH'] = ':'.join(str(p) for p in libraries if p.exists()) + ':' + os.environ.get('LD_LIBRARY_PATH','')
    ort.preload_dlls()
    from modelopt.onnx.quantization import int8 as modelopt_int8
    from onnxruntime.quantization import CalibrationDataReader
    class Reader(CalibrationDataReader):
        def __init__(self):
            with np.load(PROJECT / "data/pilot/inputs.npz", allow_pickle=False) as data: self.data=data["planes"].astype(np.float16)
            self.index=0
        def get_next(self):
            if self.index == len(self.data): return None
            value={"/input/planes":self.data[self.index:self.index+1]}
            self.index+=1
            return value
        def get_first(self): return {"/input/planes":self.data[:1]}
        def rewind(self): self.index=0
    original = modelopt_int8.quantize_static
    def per_tensor(*args, **kwargs):
        kwargs['per_channel'] = False
        return original(*args, **kwargs)
    modelopt_int8.quantize_static = per_tensor
    output = WORK / f"bt3-i1-scope{key}.onnx"
    started = time.perf_counter()
    try:
        quantized_model = modelopt_int8.quantize(str(BRIDGE), calibration_method='max',
            calibration_data_reader=Reader(), calibration_shapes='/input/planes:1x112x8x8', calibration_eps=['cuda:0'],
            nodes_to_quantize=['^'+re.escape(n)+'$' for n in targets], op_types_to_quantize=['MatMul'],
            nodes_to_exclude=[], high_precision_dtype='fp16', direct_io_types=True, passes=[],
            enable_gemv_detection_for_trt=False, intermediate_generated_files=[],
            opset=19, log_level='WARNING')
        onnx.save(quantized_model,output)
        del quantized_model
    finally:
        modelopt_int8.quantize_static = original
    model = onnx.load(output)
    # ORT's shared activation Q/DQ replacement can also reroute consumers that
    # were never selected. Restore their original floating edges explicitly.
    # This preserves selective placement instead of silently rounding branches.
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
    onnx.save(model,output)
    onnx.checker.check_model(model, full_check=True)
    producer={o:n for n in model.graph.node for o in n.output}
    initials={i.name:i for i in model.graph.initializer}
    quantized=[]
    for node in model.graph.node:
        if node.op_type != 'MatMul': continue
        dqs=[producer.get(v) for v in node.input]
        has=[d is not None and d.op_type=='DequantizeLinear' for d in dqs]
        if any(has):
            assert all(has), (node.name,has)
            assert node.name in targets,node.name
            quantized.append(node.name)
            for dq in dqs:
                assert np.prod(initials[dq.input[1]].dims,dtype=int)==1, 'I1 scale is not scalar'
                zp=initials[dq.input[2]]
                assert zp.data_type==onnx.TensorProto.INT8 and np.all(onnx.numpy_helper.to_array(zp)==0)
    assert set(quantized)==set(targets),(len(quantized),len(targets))
    destination = PROJECT / f"models/onnx/bt3-i1-scope{key}.onnx"
    __import__('shutil').copy2(output,destination)
    save(PROJECT / f"environment/week1-i1-graph-{key}.json", {"status":"passed","created_at_utc":base.now(),
        "graph":artifact(destination),"parent":artifact(BRIDGE),"targets":targets,"quantized_matmuls":len(quantized),
        "weight_scaling":"per-tensor","activation_scaling":"per-tensor","signed_symmetric":True,
        "calibration":"64 existing legal pilot positions, max; not final evaluation data",
        "adapter":"Direct ModelOpt INT8 API with explicit named placement, GEMV detection disabled, and process-local quantize_static wrapper per_channel=False; installed packages unchanged. High-level MHA exclusions had silently omitted 15 selected Smolgen operations and are bypassed.",
        "floating_edges_restored_after_shared_qdq":restored,
        "calibration_provider":"CUDA EP with explicit existing wheel-library paths and preload; CPU initial attempt retained as failed diagnostic",
        "quantization_seconds":time.perf_counter()-started,"script_sha256":base.sha256(__file__)})
    print("7C/D quantized and audited",key,flush=True)


def build(key):
    import torch
    import tensorrt as trt
    graph=read(PROJECT/f"environment/week1-i1-graph-{key}.json")['graph']
    logger=trt.Logger(trt.Logger.WARNING)
    builder=trt.Builder(logger)
    network=builder.create_network(0)
    parser=trt.OnnxParser(network,logger)
    if not parser.parse_from_file(graph['path']): raise RuntimeError('\n'.join(str(parser.get_error(i)) for i in range(parser.num_errors)))
    targets=set(read(PROJECT/'environment/step6-scope-review.json')['candidates'][key])
    norms=[]
    for i in range(network.num_layers):
        layer=network.get_layer(i)
        if layer.type==trt.LayerType.NORMALIZATION:
            layer.__class__=trt.INormalizationLayer
            layer.compute_precision=trt.float32
            norms.append(layer.name)
        elif layer.type==trt.LayerType.MATRIX_MULTIPLY and layer.name not in targets:
            layer.precision=trt.float16
    config=builder.create_builder_config()
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE,536870912)
    config.set_flag(trt.BuilderFlag.FP16)
    config.set_flag(trt.BuilderFlag.OBEY_PRECISION_CONSTRAINTS)
    config.clear_flag(trt.BuilderFlag.TF32)
    config.max_aux_streams=0
    config.builder_optimization_level=3
    config.profiling_verbosity=trt.ProfilingVerbosity.DETAILED
    profile=builder.create_optimization_profile()
    profile.set_shape('/input/planes',(1,112,8,8),(4,112,8,8),(8,112,8,8))
    config.add_optimization_profile(profile)
    started=time.perf_counter()
    serialized=builder.build_serialized_network(network,config)
    assert serialized is not None,'INT8 build failed'
    path=WORK/f'bt3-i1-scope{key}.plan'
    path.write_bytes(bytes(serialized))
    save(PROJECT/f'environment/week1-i1-engine-{key}.json',{'status':'built_pending_execution_audit','engine_path':str(path),
        'engine_sha256':base.sha256(path),'graph':graph,'scope':key,'tf32':False,'workspace_bytes':536870912,
        'profile':[1,4,8],'normalization_fp32_compute':norms,'tensorrt':trt.__version__,
        'gpu':torch.cuda.get_device_name(0),'build_seconds':time.perf_counter()-started,'script_sha256':base.sha256(__file__)})
    print('7E engine built',key,flush=True)


def wrap():
    scope=read(PROJECT/'environment/step6-scope-v2.json')
    key=scope['selected_candidate']
    engine=read(PROJECT/scope['pilot_engine'])
    assert engine['status']=='passed'
    source=Path(engine['graph']['path'])
    destination=PROJECT/'models/wrapped/bt3-i1-pilot.pb.gz'
    destination.parent.mkdir(parents=True,exist_ok=True)
    binary=base.RUNTIME/'build/lc0-tools/lc0'
    command=[str(binary),'onnx2leela','--input='+str(source),'--output='+str(destination),
        '--input-format=INPUT_CLASSICAL_112_PLANE','--policy-format=POLICY_ATTENTION',
        '--value-format=VALUE_WDL','--moves-left-format=MOVES_LEFT_V1',
        '--onnx-input=/input/planes','--onnx-output-policy=/output/policy',
        '--onnx-output-wdl=/output/wdl','--onnx-output-mlh=/output/mlh']
    result=subprocess.run(command,check=True,capture_output=True,text=True)
    payload=gzip.open(destination,'rb').read()
    assert source.read_bytes() in payload,'Wrapper changed or omitted the full ONNX payload'
    described=subprocess.run([str(binary),'describenet','--weights='+str(destination)],capture_output=True,text=True,check=True)
    save(PROJECT/'environment/week1-int8-pilot.json',{'status':'passed_A_side','verified_at_utc':base.now(),
        'scope':'environment/step6-scope-v2.json','graph':artifact(source),'engine':artifact(engine['engine_path']),
        'wrapper':artifact(destination),'wrapper_embedded_graph_byte_identical':True,'command':command,
        'wrapper_metadata':result.stdout+result.stderr,'native_description':described.stdout+described.stderr,
        'numerical_and_precision_report':scope['pilot_engine'],
        'lc0_GPU_integration':'UNVERIFIED: current lc0 tool build has Eigen CPU/export/wrapper support only. Actual lc0 onnx-trt execution and resulting engine/precision/parity remain Person B W1-B03 and joint C1. Standalone engine evidence is not substituted for integrated results.',
        'source_checkpoint':read(PROJECT/'models/source/checkpoint.json')['sha256_compressed']})
    frozen()
    progress('W1-A07','DONE','environment/week1-int8-pilot.json','A-side naive INT8 graph, actual precision, saved-engine reload, coverage choice and byte-identical lc0 wrapper verified. B-side GPU integration remains unverified; C1 is not complete.')
    print('7G: A-side pilot and wrapper verified; B-side lc0 GPU integration remains explicit',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['review','bridge','quantize','build','wrap'])
    p.add_argument('--scope',choices=['127','160'],default='160')
    a=p.parse_args()
    {'review':review,'bridge':bridge,'quantize':lambda:quantize(a.scope),'build':lambda:build(a.scope),'wrap':wrap}[a.stage]()
