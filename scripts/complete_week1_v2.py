"""Active Week 1 refresh: approved A14-A17, preserving historical evidence.

Run with the pinned WSL venv and PYTHONDONTWRITEBYTECODE=1.  Scratch artifacts
live under the external lc0-int8 runtime; only intended results are committed.
"""
import argparse
import collections
import gc
import json
import re
import sys
import time
from pathlib import Path

import chess
import numpy as np

from week1_common import PROJECT, TensorRunner, artifact, base, frozen, read, save
from quantize_week1 import session
from lc0_inputs import (dense_planes, input_object, legal_policy, native_encode,
                        wdl_from_qd)
from baselines_week1 import summary

DATA = PROJECT / 'data/syzygy-v2'
DEST = PROJECT / 'results/week1-v2'
WORK = base.RUNTIME / 'week1-v2'
PROTOCOL = PROJECT / 'environment/week1-v2-protocol.json'
FLOAT_ENGINE = PROJECT / 'environment/step5-engine.json'
I1_ENGINE = PROJECT / 'environment/week1-v2-i1-engine.json'
I1_GRAPH = PROJECT / 'models/onnx/bt3-i1-v2.onnx'
KEYS = ['logits', 'wdl', 'moves_left']
SPLITS = ['calibration', 'validation', 'test']


def checkpoint(task, status, evidence=None, detail=''):
    state_path = PROJECT / 'environment/week1-progress.json'
    state = read(state_path)
    entry = state['tasks'][task]
    if status == 'IN_PROGRESS':
        assert all(state['tasks'][p]['status'] == 'DONE' for p in entry['depends_on'])
    entry.update(status=status, implementation_started=True,
                 verification_status='PASSED' if status == 'DONE' else 'IN_PROGRESS',
                 evidence=evidence, progress_detail=detail)
    if status == 'DONE': entry['completed_at_utc'] = base.now()
    state['updated_at_utc'] = base.now()
    state['roadmap']['technical_sequence_status'] = f'{task}_{status}'
    state['roadmap']['next_action'] = detail
    if task == 'W1-A14': state['active_dataset']['network_predictions_on_new_dataset_run'] = True
    if task == 'W1-A17' and status == 'DONE':
        state['roadmap']['A_side_week1_complete'] = True
        state['roadmap']['next_action'] = 'Person A Week 1 complete; Person B and joint C1 remain separately unverified'
        state['workflow']['mode'] = 'approved_block_completed'
    save(state_path, state)
    path = PROJECT / 'docs/project-roadmap.md'
    text = path.read_text()
    text = re.sub(r'Current next task: \*\*.*?\*\*', 'Current next task: **' + state['roadmap']['next_action'] + '**', text, count=1)
    text = re.sub(r'Execution state: \*\*.*?\*\*', f'Execution state: **{task} {status}. Approved autonomous A14-A17 block; verify each before advancing. Person B and joint C1 remain separate.**', text, count=1)
    marker = '\n### Verified active completion block (2026-10-27)\n'
    if marker not in text: text += marker + '\n'
    line = f'- **{task}: {status}** - {detail}' + (f' ([evidence](../{evidence}))' if evidence else '')
    pattern = rf'^- \*\*{task}: [^\n]*$'
    if re.search(pattern, text, re.M): text = re.sub(pattern, lambda _: line, text, flags=re.M)
    else: text += line + '\n'
    path.write_text(text)
    print(task, status, detail, flush=True)


def rows(split):
    return [json.loads(s) for s in (DATA / f'{split}.jsonl').read_text().splitlines()]


def inputs(split):
    with np.load(DATA / f'{split}-inputs.npz', allow_pickle=False) as d:
        return d['planes'].copy(), d['ids'].copy()


def selected_indices():
    return read(PROTOCOL)['native_check']['indices']


def initialize():
    DEST.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    frozen()
    dataset = read(DATA / 'manifest.json')
    for entry in dataset['splits'].values():
        for key in ['positions', 'inputs']:
            assert base.sha256(entry[key]['path']) == entry[key]['sha256']
    buckets = collections.defaultdict(list)
    for i, r in enumerate(rows('calibration')):
        buckets[(r['piece_count'], r['side_to_move'], r['root_outcome'])].append(i)
    chosen = [i for cell in sorted(buckets) for i in buckets[cell][:4]]
    assert len(chosen) == 32
    protocol = {'status': 'AGREED', 'agreed_at_utc': base.now(),
        'authority': 'User agreed Steps 2, 4, 5 and Step 3 with wider batch tuning; explicitly authorized autonomous Codex execution and verification between steps.',
        'dataset': artifact(DATA / 'manifest.json'), 'history': 'native fen_only; real histories retained',
        'native_check': {'selection': 'First four calibration roots in each of eight piece/side/W-D cells; chosen before inference', 'indices': chosen, 'ids': [rows('calibration')[i]['id'] for i in chosen]},
        'floating_models': {'R32_CUDA': artifact(PROJECT / 'models/onnx/bt3-r32.onnx'), 'F16_TRT': artifact(read(FLOAT_ENGINE)['engine_path'])},
        'baseline_use_policy': 'Keep exact FP16 engine as independent baseline after correctness checks, report raw numerical failures and drift. Do not require matching predictions or erase old failures. FP32 native fidelity remains required.',
        'chess_scoring': 'Highest legal policy move; T=1 stable float32 softmax, lexical UCI ties. W->D/L or D->L is error by external theoretical Syzygy WDL, ignoring fifty-move rule. Not NN WDL argmax.',
        'bulk_batch': 8, 'scales': 'All 1024 calibration roots only; signed symmetric per-tensor W8A8/max, scope v2 160 targets',
        'INT8_quality': 'All 2048 validation roots only; no INT8 final-test inference in Week 1',
        'timing': {'data': 'Calibration inputs only; method/batch selected without test outputs',
            'batch_candidates': list(range(1,17)) + [24,32,48,64,96,128],
            'preserved_engine_range': [1,8],
            'expanded_engine_profile': [1,32,128],
            'expanded_engine_policy': 'Separate timing engines from same graphs and precision controls; preserve exact accepted baseline. Verify precision and predictions; label tactic/profile differences. No replacement baseline or accuracy-driven builder search.',
            'refinement': 'Evaluate neighboring integer batch sizes around the best measured latency and best amortized time; if boundary best for throughput, extend once to 256 if memory permits. Report bounded optimum, never global guarantee.',
            'warmup_calls': 20, 'measurement_calls': 40, 'finalist_calls': 100,
            'rounds': 2, 'order': 'Seeded randomized batch order and alternating FP16/INT8 order, one GPU workload at a time',
            'metrics': ['Resident GPU median complete-batch latency, CUDA events and synchronized host clock', 'Host input to host output complete-batch median latency', 'Latency divided by batch and positions/s; explicitly amortized, not single-position response time'],
            'notes': 'Exclude loading/build/warmup; include full network conversions. Record thermal/device state. No MCTS batching/wait/search-strength conclusion.'},
        'later_weeks': 'No training, optimizer steps, smoothing application, PTQ ladder, B-side MCTS, energy or GPU lc0 integration.'}
    if PROTOCOL.exists():
        previous = read(PROTOCOL)
        assert previous['dataset'] == protocol['dataset']
    else: save(PROTOCOL, protocol)
    state_path = PROJECT / 'environment/week1-progress.json'
    state = read(state_path)
    state['authority'] = protocol['authority']
    state['workflow'].update(mode='approved_autonomous_completion_block', block_implementation_agreed=True,
        agreement_required_before_each_step_implementation=False, failure_returns_to_same_step_discussion=False,
        execution_mode_and_learning_option_required=False)
    state['combined_completion_protocol'].update(status='AGREED', execution_mode='CODEX',
        authority=protocol['authority'], active_protocol='environment/week1-v2-protocol.json')
    state['combined_completion_protocol']['defaults']['A15']['timing'] = protocol['timing']
    for name in ['W1-A14','W1-A15','W1-A16','W1-A17']:
        state['tasks'][name].update(discussion_status='AGREED', implementation_agreed=True, execution_mode='CODEX', approved_protocol='environment/week1-v2-protocol.json')
    save(state_path, state)
    roadmap = PROJECT / 'docs/project-roadmap.md'
    text = roadmap.read_text()
    text += '\n### Approved combined execution amendment (2026-10-27)\n\nThe user explicitly agreed A14-A17 and authorized autonomous Codex execution with verification between steps. This replaces separate discussion/mode gates for this block only. A15 now includes a broad batch-size sweep and refinement, with separate preserved and expanded-profile timing engines, and explicit batch-latency versus amortized-throughput reporting. FP16 numerical drift is disclosed rather than forced to match FP32; genuine correctness faults still require repair. See [active protocol](../environment/week1-v2-protocol.json). Earlier awaiting-agreement text is historical.\n'
    if '### Approved combined execution amendment (2026-10-27)' not in roadmap.read_text(): roadmap.write_text(text)
    print('Approved protocol and pre-inference native sample recorded', flush=True)


def verify_outputs(output, n):
    assert [v.shape for v in output] == [(n,1858),(n,3),(n,1)]
    assert all(np.isfinite(v).all() for v in output)
    assert np.min(output[1]) >= 0 and np.max(output[1]) <= 1
    assert abs(output[1].sum(axis=1)-1).max() < .002
    assert np.min(output[2]) >= 0


def run_chunks(run, planes, batch):
    chunks = [run(planes[s:s+batch]) for s in range(0,len(planes),batch)]
    result = [np.concatenate([c[j] for c in chunks]).astype(np.float32) for j in range(3)]
    verify_outputs(result, len(planes))
    return result


def make_runner(name):
    if name in {'F16_TRT','I1_TRT'}:
        model = TensorRunner(FLOAT_ENGINE if name == 'F16_TRT' else I1_ENGINE)
        return model, model.run
    model = session(PROJECT / 'models/onnx/bt3-r32.onnx')
    assert model.get_providers()[0] == 'CUDAExecutionProvider'
    assert model.get_provider_options()['CUDAExecutionProvider']['use_tf32'] == '0'
    return model, lambda p: model.run(base.OUTPUTS, {'/input/planes': p})


def close(model):
    if isinstance(model, TensorRunner): model.close()


def infer(split, name):
    output_path = DEST / f'{split}-{name}-outputs.npz'
    record_path = DEST / f'{split}-{name}-inference.json'
    identity = (read(FLOAT_ENGINE if name == 'F16_TRT' else I1_ENGINE)['engine_sha256']
                if name != 'R32_CUDA' else base.sha256(PROJECT/'models/onnx/bt3-r32.onnx'))
    inp = DATA / f'{split}-inputs.npz'
    if output_path.exists() and record_path.exists():
        old = read(record_path)
        assert old['status'] == 'passed' and old['model_identity'] == identity
        assert old['inputs']['sha256'] == base.sha256(inp)
        assert old['outputs']['sha256'] == base.sha256(output_path)
        return
    planes, ids = inputs(split)
    model, run = make_runner(name)
    for _ in range(10): run(planes[:8])
    started = time.perf_counter()
    output = run_chunks(run, planes, 8)
    elapsed = time.perf_counter()-started
    np.savez_compressed(output_path, ids=ids, **dict(zip(KEYS,output)))
    options = model.get_provider_options() if name == 'R32_CUDA' else None
    close(model); del model, output, planes; gc.collect()
    save(record_path, {'status':'passed','created_at_utc':base.now(),'name':name,
        'model_identity':identity, 'inputs':artifact(inp),'outputs':artifact(output_path),
        'batch':8,'bulk_run_seconds_including_host_copies':elapsed,'provider_options':options,
        'TF32':False,'script':artifact(Path(__file__))})
    print('Bulk inference verified', split, name, len(ids), flush=True)


def load_outputs(split, name, indices=None):
    with np.load(DEST/f'{split}-{name}-outputs.npz', allow_pickle=False) as d:
        return [d[key].copy() if indices is None else d[key][indices].copy() for key in KEYS]


def score(split, name):
    records = rows(split)
    with np.load(DEST/f'{split}-{name}-outputs.npz', allow_pickle=False) as d:
        assert list(d['ids']) == [r['id'] for r in records]
        logits = d['logits'].copy()
    predictions = []
    for r, values in zip(records,logits):
        moves, probs, best = legal_policy(values,chess.Board(r['fen']))
        selected = r['move_outcomes'][best]
        assert r['root_outcome'] in {0,1} and selected <= r['root_outcome']
        predictions.append({k:r[k] for k in ['id','piece_count','family','side_to_move','root_outcome','decision_sensitive','symmetry_group']} | {
            'move':best,'selected_outcome':selected,'error':selected<r['root_outcome'],
            'preserving_probability_mass':float(sum(p for m,p in zip(moves,probs) if r['move_outcomes'][m]==r['root_outcome']))})
    path = DEST/f'{split}-{name}-predictions.jsonl'
    path.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in predictions))
    strata = {'all':predictions,'decision_sensitive':[r for r in predictions if r['decision_sensitive']]}
    for key in ['piece_count','side_to_move','root_outcome']:
        for value in sorted({r[key] for r in predictions}): strata[f'{key}:{value}']=[r for r in predictions if r[key]==value]
    return {'strata':{k:summary(v) for k,v in strata.items()},'predictions':artifact(path)}, predictions


def diagnostics(records, reference, candidate, precision='f16'):
    # The legacy comparator aborts at a 0.001 probability-sum error even when
    # enforce=False. Keep that failure visible while applying the pre-existing
    # standalone-runner validity bound of 0.002. Never renormalize raw outputs.
    verify_outputs(candidate,len(records))
    gates = base.INITIAL_GATES[precision]
    rp,rw,rm = reference; cp,cw,cm = candidate
    per_position = []; failures = []
    for i,record in enumerate(records):
        row = {'id':record['id'],'raw_logit_max_abs':float(abs(cp[i]-rp[i]).max()),
            'wdl_max_abs':float(abs(cw[i]-rw[i]).max()),
            'q_abs':float(abs((cw[i,0]-cw[i,2])-(rw[i,0]-rw[i,2]))),
            'moves_left_abs':float(abs(cm[i,0]-rm[i,0])),
            'wdl_probability_sum_abs_error':float(abs(cw[i].sum()-1))}
        for metric,limit in [('wdl_max_abs',gates['wdl_max_abs']),('q_abs',gates['q_max_abs']),
            ('moves_left_abs',gates['moves_left_atol']+gates['moves_left_rtol']*abs(rm[i,0])),
            ('wdl_probability_sum_abs_error',.001)]:
            if row[metric] > limit: failures.append({'id':record['id'],'metric':metric,'observed':row[metric],'limit':float(limit)})
        board = chess.Board(record['fen'])
        moves,p,best = legal_policy(rp[i],board)
        _,q,other = legal_policy(cp[i],board)
        from lc0_inputs import legal_move_indices
        indices = [legal_move_indices(board)[m] for m in moves]
        logp,logq = base.log_probabilities(rp[i],indices),base.log_probabilities(cp[i],indices)
        kl = max(0.,float(np.sum(np.exp(logp)*(logp-logq))))
        margin = float(np.sort(p)[-1]-np.sort(p)[-2]) if len(p)>1 else 1.
        row.update(legal_probability_max_abs=float(abs(p-q).max()),legal_kl=kl,
            reference_best=best,candidate_best=other,top_agrees=best==other,reference_top_margin=margin)
        for metric,limit in [('legal_probability_max_abs',gates['legal_probability_max_abs']),('legal_kl',gates['legal_kl_max'])]:
            if row[metric]>limit: failures.append({'id':record['id'],'metric':metric,'observed':row[metric],'limit':limit})
        if best!=other and margin>2*gates['legal_probability_max_abs']:
            failures.append({'id':record['id'],'metric':'top_move_flip_outside_tie_bound','observed':margin,'limit':2*gates['legal_probability_max_abs']})
        per_position.append(row)
    result = {'summary':{'positions':len(records),'nonterminal_positions':len(records),
        **{key:max(r[key] for r in per_position) for key in ['raw_logit_max_abs','legal_probability_max_abs','wdl_max_abs','wdl_probability_sum_abs_error']},
        'legal_kl_max':max(r['legal_kl'] for r in per_position),
        'legal_kl_mean':float(np.mean([r['legal_kl'] for r in per_position])),
        'top_move_agreement':float(np.mean([r['top_agrees'] for r in per_position])),
        'q_max_abs':max(r['q_abs'] for r in per_position),'moves_left_max_abs':max(r['moves_left_abs'] for r in per_position)},
        'per_position':per_position,'gate_failures':failures,
        'wdl_mae':float(abs(reference[1]-candidate[1]).mean()),
        'failed_position_count':len({r['id'] for r in failures}),
        'raw_outputs_renormalized':False,'standalone_validity_sum_bound':.002,'legacy_comparison_sum_bound':.001}
    return result


def native_check():
    indices = selected_indices()
    records = [rows('calibration')[i] for i in indices]
    planes = inputs('calibration')[0][indices]
    encoded = native_encode(records,fill='fen_only')
    assert np.array_equal(planes,np.stack([dense_planes(x) for x in encoded]))
    sys.path.insert(0,str(base.RUNTIME/'build/lc0-tools'))
    import backends
    weights = backends.Weights(str(PROJECT/read(PROJECT/'models/source/checkpoint.json')['relative_path']))
    backend = backends.Backend(weights=weights,backend='eigen',options='batch_size=1,threads=2')
    chunks = []
    for item in encoded:
        o, = backend.evaluate(input_object(backends,item))
        chunks.append([o.p_raw(*range(1858)),wdl_from_qd(o.q(),o.d()),[o.m()]])
    native = [np.array([c[j] for c in chunks],dtype=np.float32) for j in range(3)]
    del backend,weights; gc.collect()
    np.savez_compressed(DEST/'native-calibration32-outputs.npz',ids=np.array([r['id'] for r in records]),**dict(zip(KEYS,native)))
    checks = {}
    for name,precision in [('R32_CUDA','f32'),('F16_TRT','f16')]:
        model,run = make_runner(name)
        b1 = run_chunks(run,planes,1); b8 = run_chunks(run,planes,8)
        comparison = diagnostics(records,native,b1,precision)
        batching = base.batch_check(records,b1,b8,base.INITIAL_GATES[precision],enforce=False)
        checks[name] = {'vs_native':comparison,'batch1_vs_batch8':batching}
        if precision == 'f32':
            assert not comparison['gate_failures'], comparison['gate_failures']
            assert not batching['gate_failures'], batching
        close(model); del model; gc.collect()
    save(DEST/'native-check.json',{'status':'passed_correctness_with_disclosed_F16_drift','indices':indices,
        'checks':checks,'native_outputs':artifact(DEST/'native-calibration32-outputs.npz'),
        'input_planes_exactly_equal_native':True,'FP16_policy':read(PROTOCOL)['baseline_use_policy']})
    print('Native check verified', {k:v['vs_native']['summary'] for k,v in checks.items()},flush=True)


def baselines():
    checkpoint('W1-A14','IN_PROGRESS',detail='Refreshing floating baselines on frozen v2 data; preselected native check first.')
    native_check()
    report = {'status':'passed_with_disclosed_FP16_drift','created_at_utc':base.now(),'splits':{},
        'protocol':artifact(PROTOCOL),'native_check':artifact(DEST/'native-check.json'),
        'scoring':read(PROTOCOL)['chess_scoring'],
        'limitations':'Stratified published four/five-piece game positions and documented color/rank mirrors, clocks normalized, standalone fen_only; not natural frequency, MCTS or Elo. Both history and corpus differ from historical 55.42%, so no isolated history-effect claim.',
        'FP16_policy':read(PROTOCOL)['baseline_use_policy']}
    for split in SPLITS:
        results = {}; predictions = {}
        for name in ['R32_CUDA','F16_TRT']:
            infer(split,name)
            results[name], predictions[name] = score(split,name)
        r32, f16 = load_outputs(split,'R32_CUDA'), load_outputs(split,'F16_TRT')
        diff = diagnostics(rows(split),r32,f16)
        diff_path = DEST/f'{split}-F16-vs-R32-drift.json'; save(diff_path,diff)
        paired = collections.Counter()
        for a,b in zip(predictions['R32_CUDA'],predictions['F16_TRT']):
            paired[f'R32_{"wrong" if a["error"] else "correct"}_F16_{"wrong" if b["error"] else "correct"}'] += 1
        results['paired'] = dict(paired) | {'top_move_agreement':sum(a['move']==b['move'] for a,b in zip(predictions['R32_CUDA'],predictions['F16_TRT']))/len(predictions['R32_CUDA'])}
        results['drift'] = {'report':artifact(diff_path),'summary':diff['summary'],'failed_position_count_at_historical_limits':diff['failed_position_count']}
        report['splits'][split] = results
        print('Accuracy',split,{n:v['strata']['all']['accuracy'] for n,v in results.items() if 'strata' in v},flush=True)
    frozen()
    save(DEST/'baseline-accuracy.json',report)
    save(PROJECT/'environment/week1-v2-baselines.json',{'status':'passed','report':artifact(DEST/'baseline-accuracy.json'),
        'FP16_use':'explicitly accepted with documented drift; raw failures retained','protocol':artifact(PROTOCOL)})
    checkpoint('W1-A14','DONE','environment/week1-v2-baselines.json','Floating baselines and native/batch correctness verified on active data; raw FP16 drift and all-split chosen-move accuracy saved. Next: naive INT8 refresh and broad batch sweep.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['initialize','baselines'])
    globals()[p.parse_args().action]()
