"""Prepare a frozen, default-plan-only Run4 DAG. No model inference/GPU jobs."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from execution.support import ROOT, read_json, atomic_json, identity
from analysis.person_a.run3_systems import REPORT, csvread, catalog
from analysis.person_a.run3_finish import jsonlines


def prepare():
    setup = read_json(REPORT / 'fresh_setup.json'); fresh = Path(setup['repo']); control = Path(setup['workspace']) / 'control'
    py = str(Path(setup['venv']) / 'Scripts/python.exe'); out = ROOT / 'reports/takeover/run4'
    original = read_json(ROOT / 'reports/takeover/run1/run2_jobs.json'); tools = original['tools']
    old_runtime = read_json(ROOT / 'reports/takeover/run2/session.json')['runtime']
    ids = {int(i) for i in (ROOT / 'analysis/person_a/run1/cohort_ids.txt').read_text().split()}
    tb = {r['id']: r for r in jsonlines(ROOT / 'data/tbset.jsonl')}
    by_class = {}
    for ident in sorted(ids): by_class.setdefault(tb[ident]['cls'], []).append(ident)
    selected = []
    while len(selected) < 32:
        for group in by_class.values():
            if group and len(selected) < 32: selected.append(group.pop(0))
    selected.sort()
    ids_path = control / 'repro-ids.txt'; ids_path.write_text('\n'.join(map(str, selected)) + '\n', encoding='utf-8')
    (REPORT / 'repro-ids.txt').write_bytes(ids_path.read_bytes())
    speed = {r['model']: r for r in csvread(ROOT / 'analysis/tables/T2-speed.csv')}
    batch = {r['model']: r for r in csvread(ROOT / 'analysis/tables/T2-network-batch-summary.csv') if r['batch'] == '64'}
    models = {}
    for name in ('fp16', 's4', 's1sp'):
        a = {r['id']: r for r in jsonlines(ROOT / 'results' / name / 'study_a.jsonl')}
        b = {r['id']: r for r in jsonlines(ROOT / 'results' / name / 'study_b.jsonl') if r['budget'] == 100}
        models[name] = {'fresh_weights': str(fresh / 'models' / (name + '.pb.gz')),
                        'weights_sha256': identity(ROOT / 'models' / (name + '.pb.gz'))['sha256'],
                        'reference_A': [a[i] for i in selected], 'reference_B100': [b[i] for i in selected]}
    contract = {'schema_version': 1, 'declared_before_reproduction': True, 'declared_unix': time.time(),
                'source_revision': setup['source_revision'], 'fresh_root': str(fresh), 'fresh_venv': setup['venv'],
                'ids': selected, 'selection': '32 deterministic roots, round-robin over classes from the frozen2437-ID cohort; no outcome-based selection',
                'roots': [tb[i] for i in selected], 'models': models, 'tools': tools,
                'canonical_s4_weights': str(ROOT / 'models/s4.pb.gz'),
                'benchmark_reference': {n: {'nps': float(speed[n]['engine_nps_median']),
                    'batch64_latency_ms': float(batch[n]['latency_ms_median'])} for n in models},
                'tolerances': {'value_absolute': {'wl': .005, 'd': .005, 'v': .005, 'm': .25},
                               'normalized_policy_max_absolute': .005,
                               'raw_tablebase_outcome_vector_must_match_reference': True,
                               'search_exact_moves_required': False,
                               'performance_ratio_review_band': [.8, 1.2]},
                'tolerance_rationale': 'Same frozen bytes/runtime; absolute0.005 for printed WL/d/V and normalized policy,0.25 moves-left. These are numerical reproduction limits, not chess-error limits. Different raw preserving outcomes or drift outside limits stops for review. Fixed-node search differences are descriptive because search is not bitwise deterministic.',
                'scope': 'same-host fresh source/Python/artifact functional and numeric reproduction; not an independent accuracy holdout or cross-machine test',
                'idle_validation_path': str(out / 'energy-validation.json'),
                'sparse_acceptance': 'record actual selected sparse tactics; zero can be a documented runtime limitation, never a sparse-speed claim',
                'benchmark_scope': 'one fresh common-setting trial/model; performance outside80-120% of source median requires review, not silent rerun'}
    contract_path = control / 'reproduction-contract.json'; atomic_json(contract_path, contract)
    atomic_json(REPORT / 'reproduction-contract.json', contract)
    driver = control / 'run4_checks.py'; shutil.copy2(ROOT / 'execution/run4_checks.py', driver)
    if identity(driver)['sha256'] != identity(ROOT / 'execution/run4_checks.py')['sha256']: raise ValueError('Driver copy mismatch')
    # Clarify production settings while preserving the already frozen count/time.
    sizing_path = REPORT / 'match-sizing.json'; sizing = read_json(sizing_path)
    sizing['pilot_settings'] = copy.deepcopy(sizing['settings'])
    sizing['production_settings'] = {**sizing['settings'], 'estimate': 0}
    atomic_json(sizing_path, sizing)
    jobs = []
    def add(name, kind, argv, cwd, required, evidence, depends):
        jobs.append({'id': name, 'kind': kind, 'command': list(map(str, argv)), 'cwd': str(cwd),
                     'required_outputs': list(map(str, required)), 'evidence_dirs': list(map(str, evidence)), 'depends_on': depends})
    studies = out / 'fresh/studies'; benchmarks = out / 'fresh/benchmarks'; captures = out / 'fresh/captures'; sparse = out / 'fresh/sparse'
    for name in models:
        add('fresh-study-' + name, 'gpu_study', [py, '-B', fresh / 'eval/run_study.py', '--lc0', tools['lc0'],
            '--weights', models[name]['fresh_weights'], '--name', name, '--backend-opts', 'optimize=6' if name == 'fp16' else 'optimize=8',
            '--tbset', fresh / 'data/tbset.jsonl', '--ids', ids_path, '--budgets', '0,100', '--threads', '1', '--minibatch', '256', '--out-dir', studies],
            fresh, [studies / name / 'study_a.jsonl', studies / name / 'study_b.jsonl', studies / name / 'meta.json'], [studies / name], [])
    common = [py, '-B', driver]
    # Insert the controlled idle observation before any GPU work. An unresolved
    # idle cross-check is reported as a limitation, not changed into an energy claim.
    idle_job = {'id': 'idle-telemetry', 'kind': 'controlled_idle',
        'command': list(map(str, common + ['idle-telemetry', '--root', fresh, '--contract', contract_path,
                                         '--session', '{fresh_session}', '--output', out / 'energy-validation.json'])),
        'cwd': str(fresh), 'required_outputs': [str(out / 'energy-validation.json')],
        'evidence_dirs': [], 'depends_on': []}
    jobs.insert(0, idle_job)
    for job in jobs[1:]: job['depends_on'] = ['idle-telemetry']
    add('fresh-study-check', 'cpu_check', common + ['compare-study', '--root', fresh, '--contract', contract_path,
        '--studies', studies, '--output', out / 'fresh/study-verification.json'], fresh,
        [out / 'fresh/study-verification.json'], [], ['fresh-study-' + n for n in models])
    for name in models:
        add('fresh-bench-' + name, 'gpu_benchmark', [py, '-B', '-m', 'execution.benchmark', '--name', name,
            '--lc0', tools['lc0'], '--weights', models[name]['fresh_weights'], '--backend-opts',
            'optimize=6' if name == 'fp16' else 'optimize=8', '--session', '{fresh_session}', '--out', benchmarks / name,
            '--positions', '10', '--movetime', '10000', '--threads', '0', '--minibatch', '64', '--batches', '200', '--conditioning-seconds', '30'],
            fresh, [benchmarks / name / 'result.json'], [benchmarks / name], ['fresh-study-check'])
    for name in models:
        old_job = next(j for j in original['jobs'] if j['id'] == 'capture-' + name)
        argv = []
        for arg in old_job['command']:
            if arg == original['jobs'][0]['command'][0]: arg = py
            if arg == str(ROOT / 'models' / (name + '.pb.gz')): arg = models[name]['fresh_weights']
            argv.append(arg.replace('{attempt}', str(captures / name)).replace('{session}', '{fresh_session}'))
        add('fresh-capture-' + name, 'gpu_capture', argv, fresh,
            [captures / name / 'trace.nsys-rep', captures / name / 'work/result.json'], [captures / name], ['fresh-bench-' + n for n in models])
    sparse_job = next(j for j in original['jobs'] if j['id'] == 'profile-s1sp-sparse')
    argv = []
    for arg in sparse_job['command']:
        if arg == original['jobs'][0]['command'][0]: arg = py
        if arg == str(ROOT / 'models/s1sp.onnx'): arg = str(fresh / 'models/s1sp.onnx')
        argv.append(arg.replace('{attempt}/work', str(sparse)).replace('{session}', '{fresh_session}'))
    add('fresh-sparse-profile', 'gpu_profile', argv, fresh,
        [sparse / 'result.json', sparse / 'build_b256_layers.json'], [sparse], ['fresh-capture-' + n for n in models])
    add('fresh-systems-check', 'cpu_check', common + ['compare-speed', '--root', fresh, '--contract', contract_path,
        '--benchmarks', benchmarks, '--captures', captures, '--sparse', sparse, '--output', out / 'fresh/systems-verification.json'],
        fresh, [out / 'fresh/systems-verification.json'], [out / 'fresh'], ['fresh-sparse-profile'])
    match = out / 'match'; settings = sizing['production_settings']
    command = [sys.executable, '-B', '-m', 'execution.match_runner', '--lc0', tools['lc0'],
        '--a', 'fp16=' + str(ROOT / 'models/fp16.pb.gz') + ':optimize=6',
        '--b', 's4=' + str(ROOT / 'models/s4.pb.gz') + ':optimize=8', '--name', 'fp16_vs_s4_production',
        '--syzygy', str((ROOT / read_json(ROOT / 'config.json')['syzygy']).resolve()), '--tc', '10+0.1',
        '--pairs', '250', '--estimate', '0', '--sizing', sizing_path, '--session', '{session}', '--out-dir', match]
    for key in ('threads', 'minibatch', 'move_overhead', 'tb_men', 'resign_cp', 'draw_cp', 'draw_after', 'max_plies'):
        command += ['--' + key.replace('_', '-'), str(settings[key])]
    add('production-match', 'gpu_match', command, ROOT,
        [match / 'production/summary.json', match / 'production/games.jsonl', match / 'production/games.pgn'],
        [match], ['fresh-study-check', 'fresh-systems-check'])
    add('demo-capture', 'gpu_demo', [sys.executable, '-B', driver, 'demo-capture', '--root', ROOT,
        '--contract', contract_path, '--session', '{session}', '--output', out / 'demo'], ROOT,
        [out / 'demo/demo-capture.json'], [out / 'demo'], ['production-match'])
    source_paths = {row['path'] for row in read_json(ROOT / 'reports/takeover/run2/codex-continuation-v2/manifest.json')['sources']}
    source_paths.update(map(str, [ROOT / 'execution/run4.py', ROOT / 'execution/run4_checks.py', driver,
          contract_path, ids_path, sizing_path, Path(setup['venv']) / 'Scripts/python.exe', fresh / 'config.json',
          control / 'installed-packages.txt']))
    source_paths.update(spec['fresh_weights'] for spec in models.values())
    source_paths.add(str(fresh / 'models/s1sp.onnx'))
    source_paths.update(str(fresh / p) for p in ('data/tbset.jsonl', 'nets/BT3.pb.gz',
                                               'requirements/windows-prep.lock.txt'))
    for directory in ('quant', 'eval', 'tb', 'hw', 'execution'):
        source_paths.update(str(p) for p in (fresh / directory).rglob('*.py'))
    for relative in ('common.py', 'eval/run_study.py', 'eval/lc0uci.py', 'execution/benchmark.py',
                     'execution/gpu_job.py', 'execution/support.py', 'hw/trt_layers.py', 'hw/bench.py', 'hw/energy.py'):
        source_paths.add(str(fresh / relative))
    manifest = {'schema_version': 1, 'output': str(out), 'fresh_root': str(fresh), 'fresh_venv': setup['venv'],
                'source_revision_at_preparation': setup['source_revision'], 'driver_overlay_external_to_clean_clone': str(driver),
                'runtime': old_runtime, 'tools': tools, 'sizing': str(sizing_path),
                'policy': {'background_flags_informational': True, 'activity_logging': True,
                           'AC_monitor_exit_output_identity_failures_stop': True, 'one_GPU_workload': True},
                'jobs': jobs, 'sources': [identity(p) for p in sorted(source_paths)],
                'production_resume': 'Stable match output path and original atomic game journal; failed controller attempt requires review before resumption',
                'GPU_workloads_started_in_preparation': 0}
    atomic_json(REPORT / 'run4-manifest.json', manifest)
    template = {'root': str(ROOT), 'created_unix': 0, 'exclusive_authorized': False, 'work_saved': False,
                'ac_power_confirmed': False, 'other_work_paused': False, 'resource_preflight_passed': False,
                'runtime': old_runtime, 'note': 'Template only; replace with actual Run4 preflight observations after explicit user start'}
    atomic_json(REPORT / 'run4-session-template.json', template)
    atomic_json(REPORT / 'run4-preparation.json', {'status': 'prepared_not_executed', 'job_order': [j['id'] for j in jobs],
        'fresh_source_revision': setup['source_revision'], 'fresh_models': list(models), 'reproduction_positions': selected,
        'manifest': identity(REPORT / 'run4-manifest.json'), 'external_driver': identity(driver), 'sizing': identity(sizing_path),
        'no_GPU_work_started': True, 'native_tools_same_host_reused': True})
    print('PREPARED_RUN4_JOBS', len(jobs), 'FROZEN_SOURCES', len(source_paths), flush=True)


if __name__ == '__main__': prepare()
