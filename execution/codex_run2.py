"""Approved Run 2 continuation: background interference flags are informational.

Original inputs/evidence remain immutable. This controller writes a separate
manifest/session/output tree and references the original 35 verified jobs.
Command failure, invalid output, monitoring failure and AC loss still stop work.
"""
import argparse
import copy
import os
from pathlib import Path
import subprocess
import time

from execution import run_jobs, resources
from execution.manual_run2 import audit, observe_runtime, keep_awake
from execution.support import (ROOT, atomic_json, fingerprint, identity, preserve_command,
                               read_json, require_session, scoped_environment, single_workload)

ORIGINAL = ROOT / 'reports/takeover/run2'
PREPARED = ROOT / 'reports/takeover/run1/run2_jobs.json'
OUTPUT = ORIGINAL / 'codex-continuation-v2'
POLICY = {'version': 'run2-background-monitor-only-v2',
          'authorization': 'User explicitly disabled interference blocking and resumed Codex orchestration',
          'background_interference_blocks': False, 'activity_logging': True,
          'AC_loss_blocks': True, 'monitor_error_blocks': True,
          'command_and_output_validation': True, 'single_GPU_workload': True,
          'limits': 'Codex spikes are not assumed equal across trials; review session/thermal variability'}


def check_conditions(report):
    if report['monitor_errors']:
        raise RuntimeError('Activity/telemetry monitor failed: ' + repr(report['monitor_errors']))
    if 'AC power disconnected' in report['flags']:
        raise RuntimeError('AC power disconnected')
    # All other original background CPU/app/GPU flags remain recorded, not blocking.


def verify_parent(manifest):
    for item in manifest['sources'] + manifest['previous_failures']:
        if identity(item['path']) != item:
            raise ValueError('Frozen execution input changed: ' + item['path'])
    for name in ('original_manifest', 'original_state'):
        if identity(manifest[name]['path']) != manifest[name]:
            raise ValueError('Original checkpoint changed: ' + name)
    original = read_json(manifest['original_manifest']['path'])
    state = read_json(manifest['original_state']['path'])
    checked = audit(original, state, manifest['runtime'])
    if checked['verified'] != manifest['adopted_verified_jobs']:
        raise ValueError('Original verified reference set changed')
    return checked


def prepare():
    if (OUTPUT / 'manifest.json').exists():
        raise FileExistsError('Prepared continuation already exists; inspect/resume it without overwriting')
    original = read_json(PREPARED); state = read_json(ORIGINAL / 'state.json')
    old_session = read_json(ORIGINAL / 'session.json')
    checked = audit(original, state, old_session['runtime'])
    if len(checked['verified']) != 35 or len(checked['remaining']) != 10:
        raise ValueError('Unexpected original checkpoint')
    jobs = [copy.deepcopy(j) for j in original['jobs'] if j['id'] in checked['remaining']]
    sources = list(original['sources']) + [identity(__file__), identity(ROOT / 'execution/manual_run2.py'),
                                         identity(ROOT / 'docs/takeover_protocol_note.md')]
    manifest = {'schema_version': 2, 'output': str(OUTPUT), 'policy': POLICY,
                'original_manifest': identity(PREPARED), 'original_state': identity(ORIGINAL / 'state.json'),
                'runtime': old_session['runtime'], 'sources': sources, 'tools': original['tools'],
                'adopted_verified_jobs': checked['verified'], 'jobs': jobs,
                'previous_failures': [identity(ORIGINAL / 'bench-s1sp-r3/attempt-001/receipt.json'),
                    identity(ORIGINAL / 'manual-resume-1793352599487248700/summary.json')],
                'scientific_settings': 'Original job argv/order/dependencies unchanged; output/session paths are new'}
    atomic_json(OUTPUT / 'manifest.json', manifest)
    return manifest


def execute(manifest, session_path):
    if subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() != 'anjan':
        raise RuntimeError('Use branch anjan')
    session = require_session(session_path)
    if session.get('resource_preflight_passed') is not True or session['runtime'] != manifest['runtime']:
        raise RuntimeError('Fresh actual resource/runtime observations are required')
    if manifest['policy'] != POLICY:
        raise ValueError('Unexpected activity policy')
    verify_parent(manifest)
    output = Path(manifest['output']); manifest_hash = fingerprint(manifest)
    state_path = output / 'state.json'
    state = read_json(state_path) if state_path.exists() else {
        'manifest': manifest_hash, 'policy': POLICY, 'adopted_verified_jobs': manifest['adopted_verified_jobs'], 'jobs': {}}
    if state['manifest'] != manifest_hash:
        raise ValueError('Changed continuation manifest')
    env = scoped_environment(manifest['tools'])
    runtime_hash = fingerprint(session['runtime'])
    # Shared original lock prevents a simultaneous legacy/manual GPU controller.
    with single_workload(ORIGINAL / 'ACTIVE.json'), single_workload(output / 'ACTIVE.json'):
        for job in manifest['jobs']:
            require_session(session_path)
            prior = state['jobs'].get(job['id'], {})
            if run_jobs.reusable(prior, job, manifest_hash, runtime_hash):
                continue
            if prior:
                raise RuntimeError('Unverified continuation attempt requires review: ' + job['id'])
            completed = set(manifest['adopted_verified_jobs']) | {
                n for n, r in state['jobs'].items() if r['status'] == 'verified'}
            if not set(job.get('depends_on', [])) <= completed:
                raise RuntimeError('Unverified dependency: ' + job['id'])
            attempt = output / job['id'] / 'attempt-001'; attempt.mkdir(parents=True)
            command = run_jobs.render_command(job, attempt, session_path)
            row = {'status': 'running', 'manifest': manifest_hash, 'job': fingerprint(job),
                   'runtime': runtime_hash, 'session': identity(session_path), 'policy': POLICY,
                   'attempt': str(attempt), 'command': command, 'started_unix': time.time()}
            state['jobs'][job['id']] = row; atomic_json(state_path, state)
            print('START ' + job['id'], flush=True)
            try:
                with resources.ActivityMonitor(attempt / 'activity.log') as monitor:
                    result = preserve_command(command, attempt / 'command.log', env=env)
                report = monitor.report(os.getpid())
                report['enforcement'] = POLICY
                atomic_json(attempt / 'conditions.json', report)
                row.update(conditions=identity(attempt / 'conditions.json'), exit_code=result.returncode,
                           elapsed_seconds=time.time() - row['started_unix'])
                check_conditions(report)
                if result.returncode != 0:
                    raise RuntimeError('Child command exited ' + str(result.returncode))
                row['outputs'] = run_jobs.validate_outputs(job, attempt)
                row.update(status='verified', background_flags_observed=report['flags'],
                           verification_scope='Exit/output/identity/telemetry checks; background flags recorded under approved v2 policy')
            except BaseException as exc:
                row.update(status='BLOCKED', error=repr(exc), elapsed_seconds=time.time() - row['started_unix'])
                atomic_json(attempt / 'receipt.json', row); atomic_json(state_path, state)
                raise
            atomic_json(attempt / 'receipt.json', row); atomic_json(state_path, state)
            print('VERIFIED ' + job['id'], flush=True)
        verify_parent(manifest)
        if len(state['jobs']) != len(manifest['jobs']) or len(state['jobs']) + len(manifest['adopted_verified_jobs']) != 45:
            raise RuntimeError('Incomplete combined Run 2 job set')
        state.update(status='collected_for_run3_review', combined_verified_jobs=45,
                     combined_benchmark_trials=28, cross_session_review_required=True)
        atomic_json(state_path, state)
    return state


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--prepare', action='store_true'); mode.add_argument('--execute', action='store_true')
    ap.add_argument('--session')
    args = ap.parse_args()
    if args.prepare:
        manifest = prepare()
    else:
        manifest = read_json(OUTPUT / 'manifest.json')
    if not args.execute:
        print({'mode': 'plan_only', 'jobs': len(manifest['jobs']), 'adopted': len(manifest['adopted_verified_jobs']),
               'policy': POLICY, 'GPU_workloads_started': 0}); return
    if not args.session:
        raise ValueError('Explicit fresh session required')
    awake = {}
    try:
        with keep_awake(awake):
            state = execute(manifest, Path(args.session).resolve())
            print(state['status'], flush=True)
    finally:
        atomic_json(OUTPUT / 'awake-scope.json', awake)


if __name__ == '__main__':
    main()
