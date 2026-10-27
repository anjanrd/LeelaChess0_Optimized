"""Collect exact per-channel calibration summaries without accessing held-out inputs."""
import collections
import gc
import json
import time

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

from week1_common import PROJECT, RUNTIME, artifact, base, frozen, progress, read, save
from quantize_week1 import session


def main():
    assert read(PROJECT/'results/week1/baseline-accuracy.json')['status'] == 'passed'
    frozen()
    progress('W1-A10', 'IN_PROGRESS', detail='Collecting calibration-only channel maxima/means/RMS from the stable FP32 diagnostic graph; no validation/test activation analysis.')
    scope = read(PROJECT/'environment/step6-scope-v2.json')
    inventory = read(PROJECT/'environment/step6-inventory.json')['matrix_operations']
    rows = [r for r in inventory if r['name'] in scope['targets']]
    groups = collections.defaultdict(list)
    for row in rows: groups[row['inputs'][0]].append(row)
    source = PROJECT/'models/onnx/bt3-r32.onnx'
    model = onnx.load(source)
    initials = {i.name: numpy_helper.to_array(i) for i in model.graph.initializer}
    arrays = {}; meta = []; names = []
    for index, (tensor, consumers) in enumerate(groups.items()):
        representative = consumers[0]
        rank = len(representative['shapes_by_batch']['1']['a']); k = representative['shapes_by_batch']['1']['K']
        axes = list(range(rank-1)); prefix = f'/calibration_stats/{index}'
        absolute, square = prefix+'/abs', prefix+'/square'
        model.graph.node.extend([helper.make_node('Abs', [tensor], [absolute], name=prefix+'/abs'),
                                 helper.make_node('Mul', [tensor, tensor], [square], name=prefix+'/square')])
        for suffix, operation, value in [('max', 'ReduceMax', absolute), ('mean_abs', 'ReduceMean', absolute), ('mean_square', 'ReduceMean', square)]:
            output = prefix+'/'+suffix
            model.graph.node.append(helper.make_node(operation, [value], [output], name=output, axes=axes, keepdims=0))
            model.graph.output.append(helper.make_tensor_value_info(output, TensorProto.FLOAT, [k]))
            names.append(output)
        weights = [initials[r['weight']['name']] for r in consumers]
        assert all(w.shape[0] == k for w in weights)
        weight_max = np.maximum.reduce([np.max(abs(w), axis=1) for w in weights])
        arrays[f'g{index}_weight_input_channel_max'] = weight_max
        meta.append({'index': index, 'tensor': tensor, 'shape_at_batch1': representative['shapes_by_batch']['1']['a'],
            'channel_axis': rank-1, 'channels': k, 'selected_consumers': [r['name'] for r in consumers],
            'all_consumers': representative['activation_consumers'],
            'shared_weights': [r['weight']['name'] for r in consumers if len(r['weight']['consumers']) > 1]})
    work = RUNTIME/'outliers'; work.mkdir(parents=True, exist_ok=True)
    graph = work/'calibration-statistics.onnx'
    onnx.checker.check_model(model, full_check=True); onnx.save(model, graph)
    del model, initials; gc.collect()
    runner = session(graph)
    with np.load(PROJECT/'data/syzygy/calibration-inputs.npz', allow_pickle=False) as d: planes = d['planes'].copy(); ids = d['ids'].copy()
    with np.load(PROJECT/'results/week1/calibration-R32_CUDA-outputs.npz', allow_pickle=False) as d:
        expected = [d[n][:8].copy() for n in ['logits', 'wdl', 'moves_left']]
    output_names = base.OUTPUTS + names
    maxima = [np.zeros(m['channels']) for m in meta]
    sums = [np.zeros(m['channels']) for m in meta]; squares = [np.zeros(m['channels']) for m in meta]
    started = time.perf_counter(); max_diffs = []
    for offset in range(0, len(planes), 8):
        result = runner.run(output_names, {'/input/planes': planes[offset:offset+8]})
        if offset == 0:
            max_diffs = [float(np.max(abs(a-b))) for a,b in zip(result[:3], expected)]
            assert max_diffs[0] < 0.01 and max_diffs[1] < 0.0005 and max_diffs[2] < 0.02, max_diffs
        batch_n = len(planes[offset:offset+8])
        for j, m in enumerate(meta):
            mx, mean, ms = result[3+3*j:6+3*j]
            assert all(np.isfinite(v).all() for v in [mx, mean, ms])
            maxima[j] = np.maximum(maxima[j], mx)
            sums[j] += mean*batch_n; squares[j] += ms*batch_n
        if offset % 256 == 0: print('Activation inputs', offset+batch_n, '/', len(planes), flush=True)
    del runner; gc.collect()
    for j, m in enumerate(meta):
        mx = maxima[j]; mean = sums[j]/len(planes); rms = np.sqrt(squares[j]/len(planes))
        arrays[f'g{j}_activation_channel_max'] = mx
        arrays[f'g{j}_activation_channel_mean_abs'] = mean
        arrays[f'g{j}_activation_channel_rms'] = rms
        m.update({'channel_max_median': float(np.median(mx)), 'channel_max_maximum': float(mx.max()),
            'largest_over_median_channel_max': float(mx.max()/max(np.median(mx), 1e-12)),
            'channel_max_quantiles': {str(q): float(np.quantile(mx, q)) for q in [0, .25, .5, .75, .95, .99, 1]},
            'channels_above_10x_median': int((mx > 10*np.median(mx)).sum()),
            'largest_channel_peak_over_own_RMS': float(np.max(mx/np.maximum(rms, 1e-12))),
            'largest_channel_indices': list(map(int, np.argsort(mx)[-10:][::-1]))})
    destination = PROJECT/'results/week1/calibration-channel-statistics.npz'
    np.savez_compressed(destination, ids=ids, **arrays)
    summary = {'status': 'passed', 'created_at_utc': base.now(), 'calibration_positions': len(planes),
        'analysis_precision': 'FP32 CUDA reference diagnostic graph, TF32 off. This is an activation analysis of the source network, not a claim to inspect fused TensorRT FP16/INT8 internal values.',
        'source': artifact(source), 'calibration_inputs': artifact(PROJECT/'data/syzygy/calibration-inputs.npz'),
        'scope': artifact(PROJECT/'environment/step6-scope-v2.json'), 'statistics': artifact(destination),
        'instrumented_outputs_vs_uninstrumented_max_abs': dict(zip(['logits', 'wdl', 'moves_left'], max_diffs)),
        'n_unique_activation_tensors': len(groups), 'n_selected_matrix_consumers': len(rows), 'groups': meta,
        'definitions': 'Last axis is input channel K; reduce all other axes. Maxima are exact over all 1024 calibration positions. Mean/RMS aggregate equal-size batch statistics; reported quantiles are across channel maxima, not elementwise activation percentiles.',
        'shared_consumer_rules': 'An explicit branch Div plus compensation of each selected XW weight can preserve untouched residual/unselected branches. Moving a scale into upstream normalization requires compensating every consumer. Shared Smolgen weights require one scale consistent across every use, or explicitly cloned weights with storage changes disclosed. Do not smooth each occurrence of a shared initializer independently.',
        'week2_bounded_search': {'alpha_values': [0, .25, .5, .75, 1], 'max_candidates': 5,
            'scale': 's_j=max(a_j,eps)^alpha / max(w_j,eps)^(1-alpha); X/s and diag(s)W, eps=1e-8; bound numeric ranges before implementation',
            'selection': 'Validation only: mean legal policy KL, then scalar-value MAE; exact floating equivalence and unchanged selected-node coverage before quantized evaluation',
            'calibration_methods': ['max', 'entropy'], 'test_tuning': False},
        'seconds': time.perf_counter()-started, 'script_sha256': base.sha256(__file__)}
    save(PROJECT/'results/week1/calibration-outliers.json', summary)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    ordered = sorted(meta, key=lambda m: m['largest_over_median_channel_max'], reverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    values = [m['largest_over_median_channel_max'] for m in meta]
    axes[0].hist(values, bins=25, color='#245ea5', edgecolor='white')
    axes[0].set(xlabel='Largest / median channel maximum', ylabel='Activation tensors', title='Channel imbalance across selected inputs')
    for m in ordered[:5]:
        mx = maxima[m['index']]
        axes[1].plot(np.linspace(0, 1, len(mx)), np.sort(mx)/max(np.median(mx), 1e-12), label=m['tensor'].replace('/encoder', '/e')[-40:])
    axes[1].set(xlabel='Channel quantile', ylabel='Channel maximum / median', yscale='log', title='Five most imbalanced inputs')
    axes[1].legend(fontsize=6)
    figures = PROJECT/'docs/figures'; figures.mkdir(exist_ok=True)
    fig.savefig(figures/'week1-channel-outliers.png', dpi=150); plt.close(fig)
    note = ['# Week 1 calibration activation analysis', '', f'{len(planes):,} calibration positions; {len(groups)} unique selected activation tensors; {len(rows)} selected matrix consumers.', '',
        'The plots summarize FP32 source-network activations. They do not measure production TensorRT internal activations or latency.', '',
        '![Channel outlier summaries](figures/week1-channel-outliers.png)', '', '| Tensor | Max / median channel maximum | Channels above 10x median |', '| --- | ---: | ---: |']
    note += [f'| `{m["tensor"]}` | {m["largest_over_median_channel_max"]:.2f} | {m["channels_above_10x_median"]} |' for m in ordered[:12]]
    note += ['', summary['shared_consumer_rules'], '', 'Week 2 may compare five smoothing strengths (0, 0.25, 0.5, 0.75, 1) using validation only, after floating equivalence and shared-consumer checks. No smoothing or QAT is performed in this step.', '']
    (PROJECT/'docs/week1-activation-analysis.md').write_text('\n'.join(note))
    progress('W1-A10', 'DONE', 'results/week1/calibration-outliers.json', 'All calibration-only per-channel maxima/means/RMS, named consumers, plots and a bounded validation-only smoothing search recorded.')
    print('Activation analysis verified', len(meta), 'unique inputs', flush=True)


if __name__ == '__main__': main()
