"""Calibration-only activation refresh and bounded existing-port forward check."""
import argparse
import collections
import gc
import time
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto,helper,numpy_helper

from complete_week1_v2 import (PROJECT,WORK,DEST,DATA,PROTOCOL,KEYS,artifact,base,
    checkpoint,frozen,read,save,inputs,rows,selected_indices,load_outputs,diagnostics)
from quantize_week1 import session


def statistics():
    checkpoint('W1-A16','IN_PROGRESS',detail='Refreshing all calibration-only activation statistics and checking the existing PyTorch port; no training.')
    frozen()
    scope = read(PROJECT/'environment/step6-scope-v2.json')
    inventory = read(PROJECT/'environment/step6-inventory.json')['matrix_operations']
    selected = [r for r in inventory if r['name'] in scope['targets']]
    groups = collections.defaultdict(list)
    for row in selected: groups[row['inputs'][0]].append(row)
    source = PROJECT/'models/onnx/bt3-r32.onnx'; model = onnx.load(source)
    initials = {i.name:numpy_helper.to_array(i) for i in model.graph.initializer}
    arrays = {}; meta = []; names = []
    for index,(tensor,consumers) in enumerate(groups.items()):
        representative = consumers[0]
        rank = len(representative['shapes_by_batch']['1']['a'])
        k = representative['shapes_by_batch']['1']['K']
        axes = list(range(rank-1)); prefix = f'/calibration_stats/{index}'
        absolute,square = prefix+'/abs',prefix+'/square'
        model.graph.node.extend([helper.make_node('Abs',[tensor],[absolute],name=prefix+'/abs'),
            helper.make_node('Mul',[tensor,tensor],[square],name=prefix+'/square')])
        for suffix,op,value in [('max','ReduceMax',absolute),('mean_abs','ReduceMean',absolute),('mean_square','ReduceMean',square)]:
            output = prefix+'/'+suffix
            model.graph.node.append(helper.make_node(op,[value],[output],name=output,axes=axes,keepdims=0))
            model.graph.output.append(helper.make_tensor_value_info(output,TensorProto.FLOAT,[k])); names.append(output)
        weights = [initials[r['weight']['name']] for r in consumers]
        assert all(w.shape[0]==k for w in weights)
        arrays[f'g{index}_weight_input_channel_max'] = np.maximum.reduce([np.max(abs(w),axis=1) for w in weights])
        meta.append({'index':index,'tensor':tensor,'shape_at_batch1':representative['shapes_by_batch']['1']['a'],
            'channel_axis':rank-1,'channels':k,'selected_consumers':[r['name'] for r in consumers],
            'all_consumers':representative['activation_consumers'],
            'shared_weights':[r['weight']['name'] for r in consumers if len(r['weight']['consumers'])>1]})
    graph = WORK/'calibration-statistics.onnx'
    onnx.checker.check_model(model,full_check=True); onnx.save(model,graph)
    del model,initials; gc.collect()
    runner = session(graph); planes,ids = inputs('calibration')
    expected = load_outputs('calibration','R32_CUDA')
    maxima = [np.zeros(m['channels']) for m in meta]
    sums = [np.zeros(m['channels']) for m in meta]; squares = [np.zeros(m['channels']) for m in meta]
    started = time.perf_counter(); diffs = np.zeros(3)
    for offset in range(0,len(planes),8):
        result = runner.run(base.OUTPUTS+names,{'/input/planes':planes[offset:offset+8]})
        current = np.array([np.max(abs(a-b[offset:offset+8])) for a,b in zip(result[:3],expected)])
        diffs = np.maximum(diffs,current)
        assert current[0]<.01 and current[1]<.0005 and current[2]<.02, current
        n = len(planes[offset:offset+8])
        for j,m in enumerate(meta):
            mx,mean,ms = result[3+3*j:6+3*j]
            assert all(np.isfinite(v).all() for v in [mx,mean,ms])
            maxima[j] = np.maximum(maxima[j],mx); sums[j] += mean*n; squares[j] += ms*n
        if offset%256 == 0: print('Activation inputs',offset+n,'/',len(planes),flush=True)
    del runner; gc.collect()
    for j,m in enumerate(meta):
        mx = maxima[j]; mean = sums[j]/len(planes); rms = np.sqrt(squares[j]/len(planes))
        arrays[f'g{j}_activation_channel_max'] = mx
        arrays[f'g{j}_activation_channel_mean_abs'] = mean
        arrays[f'g{j}_activation_channel_rms'] = rms
        m.update(channel_max_median=float(np.median(mx)),channel_max_maximum=float(mx.max()),
            largest_over_median_channel_max=float(mx.max()/max(np.median(mx),1e-12)),
            channel_max_quantiles={str(q):float(np.quantile(mx,q)) for q in [0,.25,.5,.75,.95,.99,1]},
            channels_above_10x_median=int((mx>10*np.median(mx)).sum()),
            largest_channel_peak_over_own_RMS=float(np.max(mx/np.maximum(rms,1e-12))),
            largest_channel_indices=list(map(int,np.argsort(mx)[-10:][::-1])))
    destination = DEST/'calibration-channel-statistics.npz'
    np.savez_compressed(destination,ids=ids,**arrays)
    result = {'status':'passed','created_at_utc':base.now(),'calibration_positions':len(planes),
        'source':artifact(source),'calibration_inputs':artifact(DATA/'calibration-inputs.npz'),
        'scope':artifact(PROJECT/'environment/step6-scope-v2.json'),'statistics':artifact(destination),
        'n_unique_activation_tensors':len(groups),'n_selected_matrix_consumers':len(selected),'groups':meta,
        'instrumented_outputs_vs_uninstrumented_all1024_max_abs':dict(zip(KEYS,map(float,diffs))),
        'definitions':'Last axis is channel K; reduce all other axes. Exact maxima over all 1024 calibration roots. Mean and RMS are elementwise aggregate statistics. Quantiles are across channel maxima, not elementwise activation percentiles.',
        'precision':'FP32 source-network instrumented diagnostic; TF32 off. Not fused TRT internal values or production latency.',
        'shared_consumer_rules':read(PROJECT/'results/week1/calibration-outliers.json')['shared_consumer_rules'],
        'training_smoothing_or_Week2_search_performed':False,'seconds':time.perf_counter()-started,'script':artifact(Path(__file__))}
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    ordered = sorted(meta,key=lambda m:m['largest_over_median_channel_max'],reverse=True)
    fig,axes = plt.subplots(1,2,figsize=(12,4.5),constrained_layout=True)
    axes[0].hist([m['largest_over_median_channel_max'] for m in meta],bins=25,color='#245ea5',edgecolor='white')
    axes[0].set(xlabel='Largest / median channel maximum',ylabel='Activation tensors',title='Channel imbalance: 1,024 new calibration roots')
    for m in ordered[:5]:
        mx = maxima[m['index']]
        axes[1].plot(np.linspace(0,1,len(mx)),np.sort(mx)/max(np.median(mx),1e-12),label=m['tensor'].replace('/encoder','/e')[-40:])
    axes[1].set(xlabel='Channel quantile',ylabel='Channel maximum / median',yscale='log',title='Five most imbalanced inputs')
    axes[1].legend(fontsize=6)
    figure = PROJECT/'docs/figures/week1-v2-channel-outliers.png'
    fig.savefig(figure,dpi=150); plt.close(fig)
    result['figure'] = artifact(figure)
    save(DEST/'calibration-outliers.json',result)
    note = ['# Active Week 1 activation analysis','',f'{len(planes):,} calibration positions; {len(groups)} unique selected activation tensors; {len(selected)} matrix consumers. No validation/test activations used.','',
        'FP32 source-network activations with TF32 disabled; this does not measure production TensorRT internal values or latency.','',
        '![Channel outlier summaries](figures/week1-v2-channel-outliers.png)','','| Tensor | Max / median channel maximum | Channels above 10x median |','| --- | ---: | ---: |']
    note += [f'| `{m["tensor"]}` | {m["largest_over_median_channel_max"]:.2f} | {m["channels_above_10x_median"]} |' for m in ordered[:12]]
    note += ['',result['shared_consumer_rules'],'','All 1,024 instrumented network outputs were checked against the original FP32 model. Named statistics are in [the report](../results/week1-v2/calibration-outliers.json). No smoothing, training, optimizer update, QAT or distillation was performed.','']
    (PROJECT/'docs/week1-v2-activation-analysis.md').write_text('\n'.join(note))
    print('Activation analysis verified',len(groups),'unique tensors',flush=True)


def port():
    import torch
    from torch_feasibility_week1 import BT3Module
    assert read(DEST/'calibration-outliers.json')['status']=='passed'
    old = read(PROJECT/'environment/week1-torch-feasibility.json')
    assert old['status']=='passed_feasibility' and old['optimizer_steps']==0
    assert old['source']['sha256']==base.sha256(PROJECT/'models/onnx/bt3-r32.onnx')
    assert old['script']['sha256']==base.sha256(PROJECT/'scripts/torch_feasibility_week1.py')
    torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
    torch.set_float32_matmul_precision('highest')
    indices=selected_indices(); planes=inputs('calibration')[0][indices]
    records=[rows('calibration')[i] for i in indices]
    expected=load_outputs('calibration','R32_CUDA',indices)
    model=BT3Module(PROJECT/'models/onnx/bt3-r32.onnx').cuda().eval()
    results={}; started=time.perf_counter()
    with torch.no_grad():
        for batch in [1,8]:
            chunks=[[v.cpu().numpy() for v in model(torch.from_numpy(planes[s:s+batch]).cuda())] for s in range(0,len(planes),batch)]
            output=[np.concatenate([c[j] for c in chunks]) for j in range(3)]
            comparison=diagnostics(records,expected,output,'f32')
            assert not comparison['gate_failures'],comparison['gate_failures']
            results[str(batch)]=comparison
    count=len(model.weights); parameters=sum(p.numel() for p in model.parameters())
    del model; gc.collect(); torch.cuda.empty_cache()
    save(PROJECT/'environment/week1-v2-torch-check.json',{'status':'passed','created_at_utc':base.now(),
        'calibration_cases':32,'indices':indices,'batches':[1,8],'parity':results,
        'unique_trainable_initializer_tensors':count,'trainable_parameters':parameters,
        'source':artifact(PROJECT/'models/onnx/bt3-r32.onnx'),'port_script':artifact(PROJECT/'scripts/torch_feasibility_week1.py'),
        'historical_gradient_feasibility_reused':artifact(PROJECT/'environment/week1-torch-feasibility.json'),
        'optimizer_steps':0,'backward_passes_this_refresh':0,'QAT_or_distillation_performed':False,
        'scope':'Existing exact-operator port forward compatibility only; historical single-backward feasibility is not training convergence or full optimizer-memory proof.',
        'seconds':time.perf_counter()-started,'script':artifact(Path(__file__))})
    frozen()
    save(PROJECT/'environment/week1-v2-analysis.json',{'status':'passed','activation_statistics':artifact(DEST/'calibration-outliers.json'),
        'port_check':artifact(PROJECT/'environment/week1-v2-torch-check.json'),'training_performed':False})
    checkpoint('W1-A16','DONE','environment/week1-v2-analysis.json','All 1024 calibration-only activation statistics, plots and 32-case batch1/8 PyTorch forward parity verified. No training. Next: Person A audit and handoff.')
    print('Port forward parity verified', {b:r['summary'] for b,r in results.items()},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('action',choices=['statistics','port'])
    globals()[p.parse_args().action]()
