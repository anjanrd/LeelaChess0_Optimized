"""Exclusive Run 4 controller. Default is plan-only; GPU work needs --execute.

Fresh reproduction gates precede the fixed-size production match; demo is last.
Background flags are informational under the approved Codex policy. Failures stop.
"""
import argparse
import copy
import os
from pathlib import Path
import subprocess
import time

from execution import resources
from execution.codex_run2 import check_conditions
from execution.manual_run2 import keep_awake
from execution.support import (ROOT, atomic_json, fingerprint, identity, read_json,
                               require_session, preserve_command, scoped_environment, single_workload)

MANIFEST = ROOT / 'reports/takeover/run3/run4-manifest.json'


def verify_sources(manifest):
    for row in manifest['sources']:
        if identity(row['path']) != row:
            raise ValueError('Frozen Run4 input changed: ' + row['path'])


def outputs(job, attempt):
    for name in job['required_outputs']:
        path = Path(name.replace('{attempt}', str(attempt)))
        if not path.is_file() or not path.stat().st_size: raise ValueError('Missing output: ' + str(path))
        if path.suffix == '.json' and not read_json(path): raise ValueError('Empty JSON output')
    files = {p.resolve() for p in Path(attempt).rglob('*') if p.is_file() and p.name != 'receipt.json'}
    for directory in job['evidence_dirs']:
        folder = Path(directory.replace('{attempt}', str(attempt)))
        files.update(p.resolve() for p in folder.rglob('*') if p.is_file())
    return [identity(p) for p in sorted(files)]


def validate_semantics(job):
    if job['kind'] != 'gpu_match': return
    from execution.match_runner import journal_records
    folder = Path(job['evidence_dirs'][0]) / 'production'
    records = journal_records(folder, read_json(folder / 'contract.json'))
    summary = read_json(folder / 'summary.json')
    if (len(records) != 500 or {e['record']['game'] for e in records} != set(range(500)) or
            summary['complete_color_pairs'] != 250):
        raise ValueError('Production match must contain500 games/250 complete color pairs')


def execute(manifest, session_path):
    if subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() != 'anjan':
        raise RuntimeError('Run4 is authorized on anjan')
    session = require_session(session_path)
    if not session.get('resource_preflight_passed') or session.get('runtime') != manifest['runtime']:
        raise RuntimeError('Fresh actual runtime/AC preflight required')
    verify_sources(manifest)
    sizing = read_json(manifest['sizing'])
    if sizing.get('pairs') != 250 or not sizing.get('frozen_before_production'):
        raise ValueError('Production count must match the pre-production freeze')
    root = Path(manifest['output']); root.mkdir(parents=True, exist_ok=True)
    fresh_session = copy.deepcopy(session); fresh_session['root'] = manifest['fresh_root']
    fresh_session['same_host_fresh_environment'] = True
    atomic_json(root / 'fresh-session.json', fresh_session)
    h = fingerprint(manifest); state_path = root / 'state.json'
    state = read_json(state_path) if state_path.exists() else {'manifest': h, 'jobs': {}}
    if state['manifest'] != h: raise ValueError('Changed Run4 manifest; preserve old outputs')
    environment = scoped_environment(manifest['tools'])
    with single_workload(ROOT / 'reports/takeover/run2/ACTIVE.json'), single_workload(root / 'ACTIVE.json'):
        for job in manifest['jobs']:
            require_session(session_path)
            prior = state['jobs'].get(job['id'])
            if prior:
                if prior['status'] != 'verified': raise RuntimeError('Prior incomplete/failed job requires review: ' + job['id'])
                if prior['manifest'] != h or prior['runtime'] != fingerprint(session['runtime']): raise ValueError('Resume contract changed')
                for row in prior['outputs']:
                    if identity(row['path']) != row: raise ValueError('Verified output changed')
                continue
            if not set(job.get('depends_on', [])) <= {n for n, r in state['jobs'].items() if r['status'] == 'verified'}:
                raise RuntimeError('Unverified Run4 dependency')
            attempt = root / job['id'] / 'attempt-001'; attempt.mkdir(parents=True)
            replacements = {'{session}': str(Path(session_path).resolve()), '{fresh_session}': str(root / 'fresh-session.json'),
                            '{attempt}': str(attempt)}
            command = list(job['command'])
            for token, value in replacements.items(): command = [arg.replace(token, value) for arg in command]
            row = {'status': 'running', 'manifest': h, 'runtime': fingerprint(session['runtime']),
                   'session': identity(session_path), 'command': command, 'cwd': job['cwd'],
                   'attempt': str(attempt), 'started_unix': time.time(), 'policy': manifest['policy']}
            state['jobs'][job['id']] = row; atomic_json(state_path, state)
            print('START ' + job['id'], flush=True)
            try:
                with resources.ActivityMonitor(attempt / 'activity.log') as monitor:
                    result = preserve_command(command, attempt / 'command.log', env=environment, cwd=job['cwd'])
                report = monitor.report(os.getpid()); report['enforcement'] = manifest['policy']
                atomic_json(attempt / 'conditions.json', report)
                row.update(exit_code=result.returncode, conditions=identity(attempt / 'conditions.json'),
                           elapsed_seconds=time.time() - row['started_unix'])
                check_conditions(report)
                if result.returncode: raise RuntimeError('Run4 command failed: ' + str(result.returncode))
                validate_semantics(job)
                row.update(outputs=outputs(job, attempt), status='verified')
            except BaseException as exc:
                row.update(status='BLOCKED', error=repr(exc), elapsed_seconds=time.time() - row['started_unix'])
                atomic_json(attempt / 'receipt.json', row); atomic_json(state_path, state); raise
            atomic_json(attempt / 'receipt.json', row); atomic_json(state_path, state)
            print('VERIFIED ' + job['id'], flush=True)
        verify_sources(manifest)
        state.update(status='collected_for_Run5_review', production_pairs=250, fresh_reproduction_executed=True)
        atomic_json(state_path, state)
    return state


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--execute', action='store_true')
    ap.add_argument('--session'); args = ap.parse_args(); manifest = read_json(MANIFEST)
    if not args.execute:
        print({'mode': 'plan_only', 'GPU_workloads_started': 0, 'pairs': 250,
               'order': [j['id'] for j in manifest['jobs']]}); return
    if not args.session: raise ValueError('Explicit fresh exclusive session required')
    awake = {}
    try:
        with keep_awake(awake): execute(manifest, Path(args.session).resolve())
    finally: atomic_json(Path(manifest['output']) / 'awake-scope.json', awake)


if __name__ == '__main__': main()
