"""Measure both frozen floating baselines against external theoretical WDL truth."""
import argparse
import collections
import gc
import json
import math
import time

import chess
import numpy as np

from week1_common import PROJECT, TensorRunner, artifact, base, baseline_review_open, frozen, progress, read, save
from quantize_week1 import session
from lc0_inputs import legal_policy

DATA = PROJECT / 'data/syzygy'
DEST = PROJECT / 'results/week1'


def infer(split, name):
    DEST.mkdir(parents=True, exist_ok=True)
    output_path = DEST / f'{split}-{name}-outputs.npz'
    metadata_path = DEST / f'{split}-{name}-inference.json'
    inputs = DATA / f'{split}-inputs.npz'
    identity = (read(PROJECT/'environment/step5-engine.json')['engine_sha256'] if name == 'F16_TRT'
                else base.sha256(PROJECT/'models/onnx/bt3-r32.onnx'))
    if output_path.exists() and metadata_path.exists():
        old = read(metadata_path)
        assert old['status'] == 'passed' and old['model_identity'] == identity
        assert old['inputs']['sha256'] == base.sha256(inputs)
        assert old['outputs']['sha256'] == base.sha256(output_path)
        return output_path
    with np.load(inputs, allow_pickle=False) as d:
        planes = d['planes'].copy(); ids = d['ids'].copy()
    model = TensorRunner(PROJECT/'environment/step5-engine.json') if name == 'F16_TRT' else session(PROJECT/'models/onnx/bt3-r32.onnx')
    run = model.run if name == 'F16_TRT' else lambda p: model.run(base.OUTPUTS, {'/input/planes': p})
    for _ in range(10): run(planes[:8])
    started = time.perf_counter(); chunks = []
    for offset in range(0, len(planes), 8):
        chunks.append(run(planes[offset:offset+8]))
    outputs = [np.concatenate([c[j] for c in chunks]).astype(np.float32) for j in range(3)]
    assert all(np.isfinite(v).all() for v in outputs)
    assert np.min(outputs[1]) >= 0 and np.max(outputs[1]) <= 1
    assert np.max(abs(outputs[1].sum(axis=1)-1)) < 0.002
    assert np.min(outputs[2]) >= 0
    np.savez_compressed(output_path, ids=ids, logits=outputs[0], wdl=outputs[1], moves_left=outputs[2])
    options = None if name == 'F16_TRT' else model.get_provider_options()
    if name == 'F16_TRT': model.close()
    del model, chunks, outputs, planes
    gc.collect()
    save(metadata_path, {'status': 'passed', 'baseline': name, 'created_at_utc': base.now(),
        'model_identity': identity, 'inputs': artifact(inputs), 'outputs': artifact(output_path),
        'batch': 8, 'seconds_including_host_io_and_output_serialization': time.perf_counter()-started,
        'provider_options': options, 'TF32': False,
        'scope': 'Network inference only; tablebases are external labels, no search', 'script_sha256': base.sha256(__file__)})
    print('Inference verified', split, name, len(ids), flush=True)
    return output_path


def rows(split):
    return [json.loads(s) for s in (DATA/f'{split}.jsonl').read_text().splitlines()]


def score(split, name):
    data = rows(split)
    with np.load(DEST/f'{split}-{name}-outputs.npz', allow_pickle=False) as d:
        assert list(d['ids']) == [r['id'] for r in data]
        logits = d['logits'].copy()
    results = []
    for r, values in zip(data, logits):
        moves, p, best = legal_policy(values, chess.Board(r['fen']))
        good = np.array([r['move_outcomes'][m] == r['root_outcome'] for m in moves])
        margin = float(np.max(p[good])-np.max(p[~good])) if (~good).any() else None
        selected = r['move_outcomes'][best]
        assert r['root_outcome'] in {0, 1} and selected <= r['root_outcome']
        results.append({'id': r['id'], 'family': r['family'], 'side_to_move': r['side_to_move'],
            'root_outcome': r['root_outcome'], 'cursed_or_blessed': r['cursed_or_blessed'],
            'decision_sensitive': r['decision_sensitive'], 'symmetry_group': r['symmetry_group'],
            'move': best, 'selected_outcome': selected, 'error': selected < r['root_outcome'],
            'preserving_probability_mass': float(p[good].sum()), 'FP16_reference_margin' if name == 'F16_TRT' else 'own_policy_margin': margin})
    return results


def wilson(successes, n):
    if not n: return None
    z = 1.959963984540054; p = successes/n; a = 1 + z*z/n
    center = (p + z*z/(2*n))/a
    radius = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/a
    return [center-radius, center+radius]


def summary(predictions):
    n = len(predictions); errors = sum(r['error'] for r in predictions)
    return {'n': n, 'errors': errors, 'accuracy': (n-errors)/n if n else None,
            'accuracy_Wilson95': wilson(n-errors, n),
            'transitions': dict(collections.Counter(f'{"W" if r["root_outcome"] else "D"}->{ {-1:"L",0:"D",1:"W"}[r["selected_outcome"]]}' for r in predictions))}


def report():
    assert read(DATA/'manifest.json')['status'] == 'passed'
    frozen()
    progress('W1-A09', 'IN_PROGRESS', detail='Running independent tablebase move scoring for both preserved floating baselines; validation freezes the hard threshold before test inference.')
    for split in ['calibration', 'validation']:
        for name in ['R32_CUDA', 'F16_TRT']: infer(split, name)
    validation = score('validation', 'F16_TRT')
    margins = np.array([r['FP16_reference_margin'] for r in validation if r['decision_sensitive']])
    assert len(margins)
    tau = float(np.quantile(margins, 0.20, method='linear'))
    threshold = {'status': 'frozen_before_test_inference', 'frozen_at_utc': base.now(), 'tau': tau,
        'quantile': 0.20, 'numpy_quantile_method': 'linear', 'decision_sensitive_validation_n': len(margins),
        'validation_outputs': artifact(DEST/'validation-F16_TRT-outputs.npz'),
        'rule': 'Decision sensitive AND max(P_F16 preserving)-max(P_F16 degrading)<=tau',
        'selection_uses_INT8': False}
    threshold_path = DEST/'hard-subset.json'
    if threshold_path.exists():
        old = read(threshold_path); assert old['tau'] == tau and old['validation_outputs'] == threshold['validation_outputs']
        threshold = old
    else: save(threshold_path, threshold)
    for name in ['R32_CUDA', 'F16_TRT']: infer('test', name)
    results = {name: score('test', name) for name in ['R32_CUDA', 'F16_TRT']}
    f16 = {r['id']: r for r in results['F16_TRT']}
    grouped = {}
    for name, predictions in results.items():
        for r in predictions:
            reference = f16[r['id']]
            r['hard_subset'] = bool(reference['decision_sensitive'] and reference['FP16_reference_margin'] <= tau)
        path = DEST/f'test-{name}-predictions.jsonl'
        path.write_text(''.join(json.dumps(r, sort_keys=True)+'\n' for r in predictions))
        strata = {'all': predictions, 'decision_sensitive': [r for r in predictions if r['decision_sensitive']],
                  'hard': [r for r in predictions if r['hard_subset']],
                  'cursed_blessed': [r for r in predictions if r['cursed_or_blessed']]}
        for family in ['KQkq', 'KQkr', 'KPkp', 'KPkr']:
            strata['material:'+family] = [r for r in predictions if r['family'] == family]
            for outcome in [0, 1]:
                strata[f'{family}:{"W" if outcome else "D"}'] = [r for r in predictions if r['family'] == family and r['root_outcome'] == outcome]
        for outcome in [0, 1]: strata['root:'+('W' if outcome else 'D')] = [r for r in predictions if r['root_outcome'] == outcome]
        for side in ['white', 'black']: strata['side:'+side] = [r for r in predictions if r['side_to_move'] == side]
        grouped[name] = {label: summary(items) for label, items in strata.items()}
    delta = np.array([int(not b['error'])-int(not a['error']) for a, b in zip(results['R32_CUDA'], results['F16_TRT'])])
    n = len(delta)
    assert len({r['symmetry_group'] for r in results['F16_TRT']}) == n
    count = np.array([(delta == -1).sum(), (delta == 0).sum(), (delta == 1).sum()])
    # Respect the fixed 16-cell sampling quotas. Each root is a unique symmetry
    # cluster; paired four-category resampling within each cell preserves both
    # the matching and the benchmark's material/side/outcome distribution.
    rng = np.random.default_rng(20261026)
    bootstrap = np.zeros((50000, 2), dtype=np.int64)
    cells = collections.defaultdict(list)
    for a, b in zip(results['R32_CUDA'], results['F16_TRT']):
        cells[(a['family'], a['side_to_move'], a['root_outcome'])].append((int(not a['error']), int(not b['error'])))
    for items in cells.values():
        categories = np.bincount([a+2*b for a,b in items], minlength=4)
        samples = rng.multinomial(len(items), categories/len(items), size=50000)
        bootstrap[:, 0] += samples[:, 1]+samples[:, 3]
        bootstrap[:, 1] += samples[:, 2]+samples[:, 3]
    differences = (bootstrap[:, 1]-bootstrap[:, 0])/n
    for j, name in enumerate(['R32_CUDA', 'F16_TRT']):
        grouped[name]['all']['accuracy_stratified_bootstrap95'] = list(np.quantile(bootstrap[:, j]/n, [.025, .975]))
    paired = {'F16_minus_R32_accuracy': float(delta.mean()), 'paired_bootstrap95': list(np.quantile(differences, [.025, .975])),
        'F16_correct_R32_wrong': int(count[2]), 'R32_correct_F16_wrong': int(count[0]),
        'both_correct': sum(not a['error'] and not b['error'] for a, b in zip(results['R32_CUDA'], results['F16_TRT'])),
        'both_wrong': sum(a['error'] and b['error'] for a, b in zip(results['R32_CUDA'], results['F16_TRT'])),
        'top_move_agreement': sum(a['move'] == b['move'] for a, b in zip(results['R32_CUDA'], results['F16_TRT']))/n,
        'bootstrap_replicates': 50000, 'seed': 20261026, 'sampling_unit': 'one unique root symmetry group; paired resampling within each of the 16 fixed material/side/outcome cells'}
    report = {'status': 'passed', 'created_at_utc': base.now(), 'test_n': n, 'baselines': grouped, 'paired': paired,
        'hard_subset': threshold, 'dataset_manifest': artifact(DATA/'manifest.json'),
        'predictions': [artifact(DEST/f'test-{name}-predictions.jsonl') for name in results],
        'scoring': 'Error is W->D/L or D->L of the selected legal move, from original mover perspective; not predicted NN WDL category',
        'limitations': 'Synthetic balanced four-piece standalone roots with zero halfmove clocks and no actual game history; theoretical WDL ignores fifty-move rule. Network-only results are not MCTS results or game strength. No DTZ-optimal-rate claim.',
        'F16_acceptance': 'Original exact-engine numerical drift acceptance remains recorded; no new tolerance relaxation',
        'script_sha256': base.sha256(__file__)}
    save(DEST/'baseline-accuracy.json', report)
    lines = ['# Week 1 network-only baseline accuracy', '', f'Test: {n:,} balanced, symmetry-disjoint standalone roots. Error: selected move changes W to D/L or D to L.', '',
        '| Subset | R32 accuracy | F16 accuracy | n |', '| --- | ---: | ---: | ---: |']
    for label in ['all', 'decision_sensitive', 'hard', 'root:W', 'root:D', 'material:KQkq', 'material:KQkr', 'material:KPkp', 'material:KPkr']:
        a, b = grouped['R32_CUDA'][label], grouped['F16_TRT'][label]
        lines.append(f'| {label} | {a["accuracy"]:.2%} | {b["accuracy"]:.2%} | {a["n"]:,} |')
    lo, hi = paired['paired_bootstrap95']
    lines += ['', f'F16 minus R32 accuracy: {delta.mean()*100:.4f} percentage points; paired bootstrap 95% interval [{lo*100:.4f}, {hi*100:.4f}] points.',
        f'Hard threshold tau: {tau:.9g}, fixed from validation FP16 before test inference.', '',
        'Raw predictions, outputs, strata and uncertainty are in `results/week1/`. These results cover the network-only evaluation. Fixed-node MCTS and one-second MCTS remain Person B / joint C1 work.', '', report['limitations'], '']
    (PROJECT/'docs/week1-baseline-results.md').write_text('\n'.join(lines))
    frozen()
    if baseline_review_open():
        progress('W1-A09', 'REVIEW_REQUIRED', 'environment/week1-baseline-drift-review.json', 'All baseline measurements are complete; larger documented FP16 numerical drift still requires an explicit user decision.')
    else:
        progress('W1-A09', 'DONE', 'results/week1/baseline-accuracy.json', 'Both floating baselines scored on all 10,000 test roots; validation-frozen hard subset, complete move-level outputs, strata and paired uncertainty saved.')
    print(json.dumps({'accuracy': {k: v['all'] for k,v in grouped.items()}, 'paired': paired}, indent=2), flush=True)


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args(); report()
