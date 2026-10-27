"""Audit saved INT8 execution, compare registered scopes and freeze the pilot."""
import argparse
import gc
import json
import re
import time
from collections import Counter

import numpy as np

from week1_common import PROJECT, RUNTIME, TensorRunner, artifact, base, frozen, progress, read, save
from lc0_inputs import legal_policy
import chess


def audit(key):
    import torch
    import tensorrt as trt
    path=PROJECT/f'environment/week1-i1-engine-{key}.json'
    record=read(path)
    runner=TensorRunner(path)
    reference=TensorRunner(PROJECT/'environment/step5-engine.json')
    with np.load(PROJECT/'data/pilot/inputs.npz',allow_pickle=False) as d:
        planes=d['planes'].copy();ids=d['ids'].copy()
    rows=[json.loads(line) for line in (PROJECT/'data/pilot/positions.jsonl').read_text().splitlines()]
    expected=[]
    for start in range(0,64,8):expected.append(reference.run(planes[start:start+8]))
    expected=[np.concatenate([a[j] for a in expected]) for j in range(3)]
    results={'ids':ids};metrics={}
    for batch in [1,8]:
        chunks=[runner.run(planes[s:s+batch]) for s in range(0,64,batch)]
        outputs=[np.concatenate([c[j] for c in chunks]) for j in range(3)]
        for name,values in zip(['logits','wdl','moves_left'],outputs):results[f'b{batch}_{name}']=values
        assert all(np.isfinite(v).all() for v in outputs)
        assert np.min(outputs[1])>=0 and np.max(outputs[1])<=1
        assert np.max(abs(outputs[1].sum(axis=1)-1))<0.002
        assert np.min(outputs[2])>=0
        agreement=0;kl=[];pd=[]
        for row,a,b in zip(rows,expected[0],outputs[0]):
            board=chess.Board(row['fen'])
            _,p,move=legal_policy(a,board);_,q,other=legal_policy(b,board)
            agreement+=move==other
            kl.append(float(np.sum(p.astype(float)*np.log(np.maximum(p,1e-30)/np.maximum(q,1e-30)))))
            pd.append(float(np.max(abs(p-q))))
        metrics[str(batch)]={'top_policy_agreement_with_F16':agreement/64,'policy_KL_mean':float(np.mean(kl)),
            'legal_probability_max_abs':max(pd),'wdl_max_abs':float(np.max(abs(outputs[1]-expected[1]))),
            'wdl_mae':float(np.mean(abs(outputs[1]-expected[1])))}
    timings={}
    for batch in [1,4,8]:
        data=planes[:batch]
        # Pair the two complete host pipelines contemporaneously; no concurrent GPU work.
        for _ in range(40):reference.run(data);runner.run(data)
        samples={'F16_TRT':[],'I1':[]}
        for iteration in range(40):
            ordered=[('F16_TRT',reference),('I1',runner)]
            if iteration%2:ordered.reverse()
            for name,model in ordered:
                t=time.perf_counter();model.run(data);samples[name].append((time.perf_counter()-t)*1000)
        timings[str(batch)]={name:{'median_ms':float(np.median(v)),'samples_ms':v} for name,v in samples.items()}
        timings[str(batch)]['I1_over_F16']=timings[str(batch)]['I1']['median_ms']/timings[str(batch)]['F16_TRT']['median_ms']
    runner.run(planes[:1]);runner.run(planes[:8])
    inspector=runner.engine.create_engine_inspector();inspector.execution_context=runner.context
    inspection=json.loads(inspector.get_engine_information(trt.LayerInformationFormat.JSON))
    inspected=RUNTIME/'int8'/f'inspector-{key}.json';save(inspected,inspection)
    targets=set(read(PROJECT/'environment/step6-scope-review.json')['candidates'][key])
    mapped=set();actual=[]
    for layer in inspection['Layers']:
        names=set(re.findall(r'\[ONNX Layer: ([^\]]+)\]',layer.get('Metadata','')))&targets
        tactic=layer.get('TacticName','').lower()
        if layer.get('LayerType') in {'gemm','fusion'} and any(marker in tactic for marker in ['i8i8','i8f32_i8i32','s8','imma']):
            mapped|=names
            actual.append({'layer':layer['Name'],'targets':sorted(names),'tactic':layer.get('TacticName'),'inputs':layer.get('Inputs')})
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA]) as profiler:
        runner.run(planes[:1]);runner.run(planes[:8])
    trace=RUNTIME/'int8'/f'kernels-{key}.json';profiler.export_chrome_trace(str(trace))
    kernels=Counter(e['name'] for e in read(trace)['traceEvents'] if e.get('cat')=='kernel')
    int8={n:c for n,c in kernels.items() if any(marker in n.lower() for marker in ['i8i8','i8f32_i8i32','s8','imma'])}
    assert int8,'No executed INT8 matrix kernels'
    missing=sorted(targets-mapped)
    result_path=PROJECT/f'data/pilot/week1-i1-scope{key}-outputs.npz'
    np.savez_compressed(result_path,**results)
    runner.close();reference.close();gc.collect();torch.cuda.empty_cache()
    record.update({'status':'passed' if not missing else 'needs_coverage_investigation','verified_at_utc':base.now(),
        'mapped_INT8_targets':len(mapped),'unmapped_targets':missing,'inspected_int8_layers':actual,'executed_int8_kernels':int8,
        'metrics_vs_F16':metrics,'host_pipeline_timings':timings,'outputs':artifact(result_path),
        'runtime_evidence':[artifact(inspected),artifact(trace)],'engine_bytes':__import__('pathlib').Path(record['engine_path']).stat().st_size,
        'interpretation':'Naive numerical differences on calibration/development inputs; no Syzygy accuracy claim; mixed-precision exclusions disclosed',
        'precision_detail':'All floating ONNX inputs, outputs and initializers are FP16. TensorRT fuses INT8 x INT8 / INT32 accumulation with FP32 dequantized intermediates, FP16 outputs or a requantized INT8 output, as listed per layer in the inspector. Nonselected matrix precision is constrained FP16; normalization computation is FP32. These actual mixed intermediates are disclosed, not described as an all-FP16 remainder.',
        'audit_script_sha256':base.sha256(__file__)})
    save(path,record)
    print('Scope',key,'INT8 targets',len(mapped),'/',len(targets),'missing',missing,'timing ratios', {b:round(v['I1_over_F16'],3) for b,v in timings.items()},flush=True)


def choose():
    records={k:read(PROJECT/f'environment/week1-i1-engine-{k}.json') for k in ['127','160']}
    assert all(r['status']=='passed' for r in records.values())
    large=records['160']
    # The protocol compares expanded versus the original candidate, not versus
    # floating-point inference: scope expansion itself must not cost >10%.
    protocol=read(PROJECT/'environment/week1-pilot-protocol.json')
    ratios={b:large['host_pipeline_timings'][b]['I1_over_F16']/records['127']['host_pipeline_timings'][b]['I1_over_F16'] for b in ['1','8']}
    selected='160' if all(x<=1.10 for x in ratios.values()) else '127'
    review=read(PROJECT/'environment/step6-scope-review.json')
    rows=read(PROJECT/'environment/step6-inventory.json')['matrix_operations']
    names=set(review['candidates'][selected]);weights={r['weight']['name']:r['weight']['parameters'] for r in rows if r['name'] in names}
    all_weights={r['weight']['name']:r['weight']['parameters'] for r in rows if r['weight']}
    scope={'version':'2.0','status':'backend_verified_common_scope','recorded_at_utc':base.now(),'targets':sorted(names),
        'selected_candidate':selected,'expanded_over_original_latency_ratio':ratios,'protocol':protocol,'decision':'Broader weight coverage selected only under registered latency allowance; no prediction/accuracy-driven placement changes',
        'parent_scope':'environment/step6-scope.json','review':'environment/step6-scope-review.json',
        'selected_matrix_weight_parameters':sum(weights.values()),'total_matrix_weight_parameters':sum(all_weights.values()),
        'weight_parameter_fraction':sum(weights.values())/sum(all_weights.values()),
        'matrix_MAC_fraction':sum(r['shapes_by_batch']['1']['macs'] for r in rows if r['name'] in names)/sum(r['shapes_by_batch']['1']['macs'] for r in rows),
        'floating_weighted_nodes':[r['name'] for r in rows if r['weight'] and r['name'] not in names],
        'floating_other':'31 dynamic matrix products and nonmatrix operations; FP16 default, sensitive normalization FP32 compute requested',
        'dense_ladder':'I1-I7 keep these targets; future changes require a versioned coverage ablation',
        'pilot_engine':f'environment/week1-i1-engine-{selected}.json','scope_decision_uses_final_test':False}
    save(PROJECT/'environment/step6-scope-v2.json',scope)
    selected_record=records[selected]
    # Reload in this fresh process and compare against archived original outputs.
    runner=TensorRunner(PROJECT/scope['pilot_engine'])
    with np.load(PROJECT/'data/pilot/inputs.npz',allow_pickle=False) as d:planes=d['planes'][:8]
    with np.load(selected_record['outputs']['path'],allow_pickle=False) as d:
        output=runner.run(planes)
        assert all(np.array_equal(v,d['b8_'+name][:8]) for name,v in zip(['logits','wdl','moves_left'],output))
    runner.close()
    frozen()
    progress('W1-A07','IN_PROGRESS','environment/step6-scope-v2.json','INT8 graph/engine audit and fresh-process reload verified; preparing lc0 wrapper metadata and handoff next.')
    print('Registered scope decision:',selected,ratios,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['audit','choose']);p.add_argument('--scope',choices=['127','160'],default='160');a=p.parse_args()
    {'audit':lambda:audit(a.scope),'choose':choose}[a.stage]()
