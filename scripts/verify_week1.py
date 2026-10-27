"""Final A-side evidence audit, independent native spot checks and result caveats."""
import collections
import gc
import json
import subprocess
import sys
import time

import chess
import chess.syzygy
import numpy as np

from week1_common import PROJECT, RUNTIME, artifact, base, baseline_review_open, frozen, progress, read, save
from lc0_inputs import input_object, legal_policy, native_encode, wdl_from_qd
from prepare_pilot import group_id
from datasets_week1 import TABLES, labels


def native_spot_check(rows):
    # Deterministic one-per-cell check, selected without prediction scores.
    cells = {}
    for row in sorted(rows, key=lambda r: r['id']):
        cells.setdefault((row['family'], row['side_to_move'], row['root_outcome']), row)
    chosen = [cells[key] for key in sorted(cells)]
    assert len(chosen) == 16
    prior_path=PROJECT/'environment/week1-native-check.json'
    if prior_path.exists():
        prior=read(prior_path)
        assert prior['status']=='passed' and [r['id'] for r in prior['positions']]==[r['id'] for r in chosen]
        assert base.sha256(prior['outputs']['path'])==prior['outputs']['sha256']
        return
    save(PROJECT/'environment/week1-native-check-protocol.json', {
        'registered_at_utc': base.now(), 'selection': 'Lexically first ID in each of 16 material/side/root-outcome cells, independent of predictions',
        'ids': [r['id'] for r in chosen], 'purpose': 'Additional final-audit spot check against native Eigen CPU; no tuning or baseline replacement',
        'limits': read(PROJECT/'environment/step5-tolerances.json')})
    sys.path.insert(0, str(base.RUNTIME/'build/lc0-tools'))
    import backends
    checkpoint = read(PROJECT/'models/source/checkpoint.json')
    backend = backends.Backend(weights=backends.Weights(str(PROJECT/checkpoint['relative_path'])), backend='eigen', options='batch_size=1,threads=2')
    native = native_encode(chosen)
    with np.load(PROJECT/'results/week1/test-R32_CUDA-outputs.npz', allow_pickle=False) as data:
        lookup = {v: i for i,v in enumerate(data['ids'])}
        expected = {n: data[n][[lookup[r['id']] for r in chosen]].copy() for n in ['logits', 'wdl', 'moves_left']}
    checked = []; native_logits = []; native_wdl = []; native_mlh = []
    for row, encoded, expected_logits, expected_wdl, expected_mlh in zip(chosen, native, expected['logits'], expected['wdl'], expected['moves_left']):
        output, = backend.evaluate(input_object(backends, encoded))
        raw = np.asarray(output.p_raw(*range(1858)), dtype=np.float32)
        wdl = wdl_from_qd(output.q(), output.d())
        _, p, move = legal_policy(raw, chess.Board(row['fen']))
        _, q, other = legal_policy(expected_logits, chess.Board(row['fen']))
        probability = float(abs(p-q).max())
        divergence = float(np.sum(p.astype(float)*np.log(np.maximum(p,1e-30)/np.maximum(q,1e-30))))
        wdl_difference = float(abs(wdl-expected_wdl).max())
        assert probability <= .0002 and divergence <= .00001 and wdl_difference <= .0005
        np.testing.assert_allclose([output.m()], expected_mlh, atol=.02, rtol=.0002)
        checked.append({'id': row['id'], 'native_move': move, 'R32_move': other,
            'legal_probability_max_abs': probability, 'policy_KL': divergence, 'WDL_max_abs': wdl_difference,
            'native_move_outcome': row['move_outcomes'][move], 'R32_move_outcome': row['move_outcomes'][other]})
        native_logits.append(raw); native_wdl.append(wdl); native_mlh.append([output.m()])
    output_path = PROJECT/'results/week1/native-test-spot-check.npz'
    np.savez_compressed(output_path, ids=np.array([r['id'] for r in chosen]), logits=np.stack(native_logits),
                        wdl=np.stack(native_wdl), moves_left=np.array(native_mlh, dtype=np.float32))
    del backend; gc.collect()
    save(PROJECT/'environment/week1-native-check.json', {'status': 'passed', 'verified_at_utc': base.now(),
        'selection_protocol': artifact(PROJECT/'environment/week1-native-check-protocol.json'), 'positions': checked,
        'outputs': artifact(output_path), 'interpretation': 'Independent native CPU evaluator agrees with R32 export within original gates. This is a spot check, not native evaluation of all 10,000 roots.'})


def pair_metrics(rows):
    output = {}
    data = {}
    for name in ['R32_CUDA', 'F16_TRT']:
        with np.load(PROJECT/f'results/week1/test-{name}-outputs.npz', allow_pickle=False) as d:
            assert list(d['ids']) == [r['id'] for r in rows]
            data[name] = {k: d[k].copy() for k in ['logits','wdl','moves_left']}
    kl = []; probability = []
    for row, a, b in zip(rows, data['R32_CUDA']['logits'], data['F16_TRT']['logits']):
        _,p,_ = legal_policy(a,chess.Board(row['fen'])); _,q,_ = legal_policy(b,chess.Board(row['fen']))
        kl.append(float(np.sum(p.astype(float)*np.log(np.maximum(p,1e-30)/np.maximum(q,1e-30)))))
        probability.append(float(abs(p-q).max()))
    a, b = data['R32_CUDA'], data['F16_TRT']
    result = {'status': 'measured_not_a_new_acceptance_gate', 'F16_against_R32': {
        'legal_policy_KL_mean': float(np.mean(kl)), 'legal_policy_KL_max': max(kl),
        'legal_probability_max_abs': max(probability), 'WDL_component_MAE': float(np.mean(abs(a['wdl']-b['wdl']))),
        'WDL_component_max_abs': float(np.max(abs(a['wdl']-b['wdl']))),
        'scalar_value_MAE': float(np.mean(abs((a['wdl'][:,0]-a['wdl'][:,2])-(b['wdl'][:,0]-b['wdl'][:,2])))),
        'moves_left_MAE': float(np.mean(abs(a['moves_left']-b['moves_left']))),
        'moves_left_max_abs': float(np.max(abs(a['moves_left']-b['moves_left'])))},
        'sanity': {'self_KL': 0.0, 'self_value_MAE': 0.0},
        'interpretation': 'Numerical differences between the two already accepted baseline artifacts; independent tablebase accuracy is recorded separately. Large observed differences are disclosed, not silently accepted under a new gate.'}
    save(PROJECT/'results/week1/baseline-numerical-comparison.json', result)
    return result


def plot_refinement():
    # Presentation refinement from cached calibration statistics, no GPU rerun.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    summary = read(PROJECT/'results/week1/calibration-outliers.json')
    groups = summary['groups']; ordered = sorted(groups, key=lambda m:m['largest_over_median_channel_max'], reverse=True)
    with np.load(PROJECT/'results/week1/calibration-channel-statistics.npz', allow_pickle=False) as d:
        arrays = {m['index']: d[f'g{m["index"]}_activation_channel_max'].copy() for m in ordered[:5]}
    fig, axes = plt.subplots(1,2,figsize=(12,4.5),constrained_layout=True)
    ratios = [m['largest_over_median_channel_max'] for m in groups]
    axes[0].hist(ratios, bins=np.geomspace(min(ratios),max(ratios)*1.001,26),color='#245ea5',edgecolor='white')
    axes[0].set(xscale='log',xlabel='Largest / median channel maximum',ylabel='Activation tensors',title='Channel imbalance across selected inputs')
    for m in ordered[:5]:
        values = arrays[m['index']]
        axes[1].plot(np.linspace(0,1,len(values)),np.sort(values)/max(np.median(values),1e-12),label=m['tensor'].replace('/encoder','/e')[-40:])
    axes[1].set(yscale='log',xlabel='Channel quantile',ylabel='Channel maximum / median',title='Five most imbalanced inputs')
    axes[1].legend(fontsize=6)
    path=PROJECT/'docs/figures/week1-channel-outliers.png';fig.savefig(path,dpi=150);plt.close(fig)
    return artifact(path)


def main():
    frozen()
    base.identities()
    progress('W1-A12','IN_PROGRESS',detail='Auditing all A-side artifacts, independent native/scoring spot checks and handoff boundaries; no Week 2 work.')
    state = read(PROJECT/'environment/week1-progress.json')['tasks']
    for task in ['W1-A06P','W1-A06R','W1-A07','W1-A08','W1-A09','W1-A10','W1-A11']:
        assert state[task]['status'] == 'DONE' or (task=='W1-A09' and state[task]['status']=='REVIEW_REQUIRED'), task
    manifest = read(PROJECT/'data/syzygy/manifest.json')
    excluded = set()
    for name in ['pilot','export-confirmation']:
        excluded.update(read(PROJECT/f'data/{name}/exclusions.json')['symmetry_groups'])
    groups = set(excluded); split_rows={}; checks=[]
    for split, record in manifest['splits'].items():
        for field in ['positions','inputs']:
            assert base.sha256(record[field]['path']) == record[field]['sha256']
        rows=[json.loads(s) for s in (PROJECT/f'data/syzygy/{split}.jsonl').read_text().splitlines()]
        assert len(rows)==record['count']
        for row in rows:
            b=chess.Board(row['fen'])
            assert b.is_valid() and b.halfmove_clock==0 and b.ep_square is None and not b.castling_rights
            assert row['symmetry_group']==group_id(b) and row['symmetry_group'] not in groups
            groups.add(row['symmetry_group'])
            assert set(row['move_outcomes']) == {m.uci() for m in b.legal_moves}
        split_rows[split]=rows
    with chess.syzygy.open_tablebase(str(TABLES),max_fds=64) as tb:
        # Reprobe a deterministic sample and transformed boards. The original
        # construction already checked every original legal child.
        for split,rows in split_rows.items():
            for row in rows[::max(1,len(rows)//64)]:
                board=chess.Board(row['fen']); expected=labels(board,tb)
                assert all(row[k]==v for k,v in expected.items())
                mirror=labels(board.mirror(),tb)
                assert expected['root_outcome']==mirror['root_outcome']
                for uci,u in expected['move_outcomes'].items():
                    move=chess.Move.from_uci(uci)
                    reflected=chess.Move(chess.square_mirror(move.from_square),chess.square_mirror(move.to_square),promotion=move.promotion)
                    assert mirror['move_outcomes'][reflected.uci()]==u
                checks.append(row['id'])
    for file in read(PROJECT/'environment/week1-tablebases.json')['files']:
        assert base.sha256(file['path'])==file['sha256']
    scope=read(PROJECT/'environment/step6-scope-v2.json')
    assert scope['selected_candidate']=='160' and len(scope['targets'])==160
    for key in ['127','160']:
        r=read(PROJECT/f'environment/week1-i1-engine-{key}.json')
        assert r['status']=='passed' and r['mapped_INT8_targets']==int(key) and not r['unmapped_targets']
        assert base.sha256(r['engine_path'])==r['engine_sha256']
        assert base.sha256(r['graph']['path'])==r['graph']['sha256']
    for item in ['graph','engine','wrapper']:
        r=read(PROJECT/'environment/week1-int8-pilot.json')[item]
        assert base.sha256(r['path'])==r['sha256']
    test=split_rows['test'];native_spot_check(test)
    numerical=pair_metrics(test)
    figure=plot_refinement()
    report=read(PROJECT/'results/week1/baseline-accuracy.json')
    for name in ['R32_CUDA','F16_TRT']:
        predictions=[json.loads(s) for s in (PROJECT/f'results/week1/test-{name}-predictions.jsonl').read_text().splitlines()]
        assert [r['id'] for r in predictions]==[r['id'] for r in test]
        for original,prediction in zip(test,predictions):
            u=original['move_outcomes'][prediction['move']]
            assert prediction['selected_outcome']==u
            assert prediction['error']==(u<original['root_outcome'])
        assert sum(r['error'] for r in predictions)==report['baselines'][name]['all']['errors']
        for split in ['calibration','validation','test']:
            metadata=read(PROJECT/f'results/week1/{split}-{name}-inference.json')
            for field in ['inputs','outputs']:
                assert base.sha256(metadata[field]['path'])==metadata[field]['sha256']
    hard=report['baselines']['F16_TRT']['hard']
    caveats=[
        {'id':'HARD-FLOOR','finding':f'The predefined signed-margin hard subset has {hard["n"]} roots and zero accuracy for both baselines. Validation tau is negative, so baseline failure on this subset follows from the rule. Further degradation has a floor effect.',
         'action':'Preserve the original subset/results. Before Week 2 claims, discuss a separately registered baseline-correct/near-boundary supplemental subset using validation, with joint approval and explicit post-selection safeguards. Do not retroactively replace the current metric or tune from these test results.'},
        {'id':'NAIVE-PTQ','finding':'The engineering I1 pilot has substantial numerical drift and no latency gain over F16. Expanded coverage was chosen by the preregistered coverage/latency rule, not by accuracy.',
         'action':'Week 2 uses the registered full-calibration ladder and validation selection. Do not present the pilot as a successful accuracy/speed optimization or final test result.'},
        {'id':'WEIGHT-STORAGE','finding':'The ModelOpt Q/DQ ONNX pilot stores selected weight source constants in FP16 followed by QuantizeLinear; TensorRT folds constants and executes INT8 operands. 99.9905% is selected matrix-parameter coverage, not a claim that 99.9905% of ONNX-file bytes are INT8.',
         'action':'Report ONNX and saved-engine sizes separately. If compact INT8 initializers are needed in Week 2, treat canonical constant folding as an explicit serializer change, verify numerical equivalence and re-audit resulting engines.'},
        {'id':'MIXED-RUNTIME','finding':'INT8 matrix kernels use INT32 accumulation and may output FP32 dequantized intermediates, FP16 or requantized INT8. The four unselected weighted operations use FP16, with FP32 normalization computation requested.',
         'action':'Use per-layer inspector/kernel evidence. Do not describe all non-INT8 execution as uniformly FP16 or claim all model parameters are INT8.'},
        {'id':'C1-OPEN','finding':'Actual lc0 GPU backend integration, fixed-node and one-second search, systems/energy evidence, DTZ move ranking and teammate review are unverified.',
         'action':'A-side Week 1 completion is distinct from joint C1. Resolve B01-B08 and joint review before opening comparable Week 2 studies.'},
        {'id':'REPRODUCIBILITY','finding':'The accepted F16 engine is device/runtime-specific and has a user-accepted original numerical exception. Engine rebuilds can select different tactics.',
         'action':'Preserve the exact binary. Rebuilding or integrating a different engine requires fresh parity/precision checks; the old exception is not blanket acceptance.'}]
    drift_path=PROJECT/'environment/week1-baseline-drift-review.json'
    if drift_path.exists():
        caveats.insert(0,{'id':'BASELINE-DRIFT','finding':'Full testing revealed F16/R32 WDL component drift up to 23.24 points; native reference checks confirm the larger F16 discrepancy. The earlier 1.96-point observation does not automatically cover it.',
            'action':'Record explicit user acceptance of the expanded documented drift or reopen baseline engineering. Keep measurements and raw failures intact. Review remains open: '+str(baseline_review_open()),
            'evidence':'environment/week1-baseline-drift-review.json'})
    save(PROJECT/'results/week1/plan-review-findings.json',{'recorded_at_utc':base.now(),'findings':caveats})
    audit={'status':'passed_A_side','verified_at_utc':base.now(),'prior_frozen_Step5_Step6_artifacts_unchanged':True,
        'all_13072_root_groups_recomputed_and_disjoint':True,'prior_exclusions':len(excluded),
        'all_saved_dataset_input_and_position_hashes_verified':True,'tablebase_files_hash_verified':40,
        'reprobed_roots_and_move_mirror_checks':len(checks),'reprobed_ids':checks,
        'INT8_scope_and_saved_engines': 'Both candidates graph/engine hashes and actual executed-target coverage rechecked; selected 160',
        'additional_native_check':artifact(PROJECT/'environment/week1-native-check.json'),
        'baseline_numerical_comparison':artifact(PROJECT/'results/week1/baseline-numerical-comparison.json'),
        'calibration_plot':figure,'pytorch_feasibility':artifact(PROJECT/'environment/week1-torch-feasibility.json'),
        'findings':artifact(PROJECT/'results/week1/plan-review-findings.json'),
        'no_optimizer_steps_or_Week2_variants':True,'joint_C1_complete':False,
        'script':artifact(PROJECT/'scripts/verify_week1.py')}
    save(PROJECT/'environment/week1-audit.json',audit)
    frozen()
    if baseline_review_open():
        audit['status']='technical_checks_passed_baseline_acceptance_open'
        audit['baseline_drift_review']=artifact(drift_path)
        audit['A_side_week1_unconditionally_complete']=False
        save(PROJECT/'environment/week1-audit.json',audit)
        progress('W1-A12','AWAITING_USER_DECISION','environment/week1-audit.json','Technical evidence audit passed. Newly observed FP16 baseline drift requires explicit acceptance or reopened engineering. B work/joint C1 remain unverified; no Week 2 work begun.')
    else:
        progress('W1-A12','DONE','environment/week1-audit.json','A-side evidence audit and native/scoring checks passed. Handoff and explicit plan limitations recorded; B work and joint C1 remain unverified. No Week 2 implementation authorized or performed.')
    print('Technical audit passed',len(checks),'reprobed roots; acceptance status',audit['status'],flush=True)


if __name__=='__main__': main()
