"""Finish the approved Run 2 from external PowerShell with Codex fully closed.

Default/--check is read-only and starts no GPU job. --execute additionally needs
operator confirmations and approval for exactly the preserved host-CPU failure.
The original manifest, controller, resource rule and scientific code stay frozen.
"""
import argparse
import contextlib
import copy
import csv
import ctypes
from ctypes import wintypes as wt
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time

from execution import resources, run_jobs
from execution.support import (ROOT, atomic_json, fingerprint, identity, read_json,
                               single_workload)

MANIFEST = ROOT / 'reports/takeover/run1/run2_jobs.json'
BASE = ROOT / 'reports/takeover/run2'
MANIFEST_SHA = '9300e77242ed09d7a3f7fbd270512a6a2d24830ae39bb783139ce213ac4a1fea'
RETRY_JOB = 'bench-s1sp-r3'
FAILED_SHA = '32d081af30df79797f1400de2fea0291b1cd24629e4d880a427776a9201e7811'
HOSTS = {'chatgpt.exe', 'codex.exe'}


def hosts(sample):
    return [p for p in sample['processes'] if p['name'].lower() in HOSTS]


def require_external_terminal(sample, pid):
    catalog = {p['pid']: p for p in sample['processes']}
    seen = set()
    while pid in catalog and pid not in seen:
        seen.add(pid)
        row = catalog[pid]
        if row['name'].lower() in HOSTS:
            raise RuntimeError('Use PowerShell opened from Windows Start, not a Codex terminal')
        pid = row['ppid']


def audit(manifest, state, runtime):
    """Validate immutable inputs and every reusable receipt/output, without inference."""
    if fingerprint(manifest) != MANIFEST_SHA or state['manifest'] != MANIFEST_SHA:
        raise ValueError('Frozen manifest changed; do not regenerate it to resume')
    if Path(manifest['output']).resolve() != BASE.resolve():
        raise ValueError('Wrong Run 2 output directory')
    jobs = {j['id']: j for j in run_jobs.validate_manifest(manifest)}
    if not set(state['jobs']) <= set(jobs):
        raise ValueError('Unexpected job in saved state')
    for item in manifest['sources']:
        if identity(item['path']) != item:
            raise ValueError('Frozen input changed: ' + item['path'])
    verified = []
    for name, row in state['jobs'].items():
        if row['status'] != 'verified':
            continue
        if read_json(Path(row['attempt']) / 'receipt.json') != row:
            raise ValueError('Receipt/state disagree: ' + name)
        if not run_jobs.reusable(row, jobs[name], MANIFEST_SHA, fingerprint(runtime)):
            raise ValueError('Checkpoint cannot be reused: ' + name)
        conditions = read_json(row['conditions']['path'])
        if conditions['flags'] or conditions['monitor_errors']:
            raise ValueError('Verified job has flagged conditions: ' + name)
        verified.append(name)
    return {'verified': verified, 'remaining': [n for n in jobs if n not in verified],
            'frozen_sources': len(manifest['sources'])}


def known_failure(state):
    """Approve no new failure, no generic BLOCKED reset and no altered old evidence."""
    row = state['jobs'].get(RETRY_JOB, {})
    path = BASE / RETRY_JOB / 'attempt-001/receipt.json'
    if identity(path)['sha256'] != FAILED_SHA or read_json(path) != row:
        raise RuntimeError('Only the reviewed original host-CPU attempt may be retried')
    if row.get('status') != 'BLOCKED' or row.get('exit_code') != 0:
        raise RuntimeError('This attempt needs a separate review')
    conditions = read_json(row['conditions']['path'])
    if identity(row['conditions']['path']) != row['conditions']:
        raise ValueError('Original conditions changed')
    if conditions['flags'] != ['sustained external CPU activity: ChatGPT.exe'] or conditions['monitor_errors']:
        raise RuntimeError('Different resource failure; separate review required')
    if any(r['status'] != 'verified' for n, r in state['jobs'].items() if n != RETRY_JOB):
        raise RuntimeError('Another incomplete/failed attempt requires review')
    inventory = read_json(BASE.parent / 'progress.json')['runs']['2']['checkpoint']['blocked_attempt_inventory']
    if not inventory or {x['path'] for x in inventory} != {
            str(p.resolve()) for p in path.parent.rglob('*') if p.is_file()}:
        raise ValueError('Original failed-attempt inventory is incomplete')
    for item in inventory:
        if identity(item['path']) != item:
            raise ValueError('Original failed evidence changed: ' + item['path'])
    return inventory


def authorize_retry(state, folder, session, inventory):
    """Keep the BLOCKED receipt immutable; record the exact prior row before transition."""
    if (BASE / 'ACTIVE.json').exists():
        raise RuntimeError('An active/stale controller lock requires review')
    if read_json(BASE / 'state.json') != state:
        raise RuntimeError('Checkpoint changed during preflight; preserve and review')
    review = {'approved_job': RETRY_JOB, 'approved_receipt_sha256': FAILED_SHA,
              'authorization': 'User approved standalone resumption; operator supplied --approve-retry',
              'unix': time.time(), 'manifest': MANIFEST_SHA,
              'state_before': identity(BASE / 'state.json'),
              'prior_row': copy.deepcopy(state['jobs'][RETRY_JOB]),
              'preserved_attempt_inventory': inventory, 'session': identity(session),
              'policy': 'one fresh attempt; guard unchanged; no automatic further retry'}
    review_path = folder / 'retry-review.json'
    if review_path.exists():
        raise FileExistsError(review_path)
    atomic_json(review_path, review)
    updated = copy.deepcopy(state)
    updated['jobs'][RETRY_JOB]['status'] = 'reviewed_retry'
    updated['jobs'][RETRY_JOB]['retry_review'] = identity(review_path)
    atomic_json(BASE / 'state.json', updated)


def observe_runtime(old):
    query = ['nvidia-smi', '--query-gpu=name,uuid,driver_version,memory.total,power.limit',
             '--format=csv,noheader,nounits']
    raw = subprocess.check_output(query, text=True)
    rows = list(csv.reader(raw.strip().splitlines(), skipinitialspace=True))
    if len(rows) != 1 or len(rows[0]) != 5:
        raise RuntimeError('Expected the original single-GPU testbed')
    values = [x.strip() for x in rows[0]]
    power = subprocess.check_output(['powercfg', '/getactivescheme'], text=True).strip()
    actual = dict(zip(('GPU_name', 'GPU_uuid', 'driver_version', 'memory_MiB',
                       'power_limit_query'), values))
    actual.update(power_scheme=power, python=platform.python_version(),
                  platform=platform.platform(), prepared_manifest=MANIFEST_SHA,
                  OEM_mode=old['OEM_mode'])
    # OEM state was not observable originally. Its unchanged status is an explicit
    # operator confirmation, not an invented hardware observation.
    if actual != old:
        raise RuntimeError('Runtime/power identity differs; do not pool sessions: ' + repr(actual))
    return actual, {'gpu_query_argv': query, 'gpu_query_stdout': raw,
                    'powercfg_stdout': power, 'OEM_mode': 'not observed; operator confirms unchanged'}


def wait_for_host_exit(timeout=600):
    print('Waiting for Codex to fully close. Keep this external PowerShell window open.', flush=True)
    end = time.monotonic() + timeout
    polls = 0
    while True:
        active = hosts(resources.snapshot())
        if not active:
            break
        if polls % 15 == 0:
            print('Still present: ' + ', '.join(p['name'] + ' PID' + str(p['pid']) for p in active), flush=True)
        if time.monotonic() >= end:
            raise RuntimeError('Codex processes are still present; no experiment started')
        time.sleep(2)
        polls += 1


def validate_quiet(samples, report):
    if report['flags'] or report['monitor_errors']:
        raise RuntimeError('Quiet preflight failed: ' + repr(report))
    if not samples or any(s.get('ac_line') != 1 for s in samples):
        raise RuntimeError('AC power must be positively observed throughout preflight')
    if any(hosts(s) for s in samples):
        raise RuntimeError('Codex reopened during preflight')
    if any(s.get('gpu', {}).get('util', 100) > 5 for s in samples):
        raise RuntimeError('GPU is not quiet; no experiment started')


def quiet_preflight(folder):
    print('Checking a 60-second quiet window; leave the laptop unused.', flush=True)
    with resources.ActivityMonitor(folder / 'preflight-activity.log') as monitor:
        time.sleep(60)
    report = monitor.report(os.getpid())
    atomic_json(folder / 'preflight.json', report)
    validate_quiet(monitor.samples, report)
    return report


@contextlib.contextmanager
def keep_awake(record):
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.SetThreadExecutionState.argtypes = [wt.DWORD]
    k.SetThreadExecutionState.restype = wt.DWORD
    if not k.SetThreadExecutionState(0x80000003):
        raise ctypes.WinError(ctypes.get_last_error())
    record['requested'] = True
    try:
        yield
    finally:
        record['released'] = bool(k.SetThreadExecutionState(0x80000000))
        if not record['released']:
            raise ctypes.WinError(ctypes.get_last_error())


class WindowsJob:
    """Contain only this launcher's worker/descendants, including on Ctrl+C/crash.

    API/layout: https://learn.microsoft.com/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information
    The worker waits for a gate, so it cannot spawn a GPU child before assignment.
    No affinity, priority, memory or CPU-rate limit is applied.
    """
    def __init__(self):
        class Basic(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                        ('flags', wt.DWORD), ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t),
                        ('active_limit', wt.DWORD), ('affinity', ctypes.c_size_t),
                        ('priority', wt.DWORD), ('scheduling', wt.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in ('reads', 'writes', 'other', 'read_bytes', 'write_bytes', 'other_bytes')]
        class Limits(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', IO), ('process_memory', ctypes.c_size_t),
                        ('job_memory', ctypes.c_size_t), ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]
        class Accounting(ctypes.Structure):
            _fields_ = [(n, ctypes.c_longlong) for n in ('user', 'kernel', 'period_user', 'period_kernel')] + [
                (n, wt.DWORD) for n in ('faults', 'total', 'active', 'terminated')]
        self.accounting = Accounting
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([ctypes.c_void_p, wt.LPCWSTR], wt.HANDLE),
            'SetInformationJobObject': ([wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD], wt.BOOL),
            'AssignProcessToJobObject': ([wt.HANDLE, wt.HANDLE], wt.BOOL),
            'QueryInformationJobObject': ([wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.c_void_p], wt.BOOL),
            'TerminateJobObject': ([wt.HANDLE, wt.UINT], wt.BOOL),
            'OpenProcess': ([wt.DWORD, wt.BOOL, wt.DWORD], wt.HANDLE),
            'CloseHandle': ([wt.HANDLE], wt.BOOL)}
        for name, (args, ret) in signatures.items():
            f = getattr(self.k, name); f.argtypes = args; f.restype = ret
        self.handle = self.k.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        info = Limits(); info.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE only
        if not self.k.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            error = ctypes.get_last_error(); self.k.CloseHandle(self.handle); self.handle = None
            raise ctypes.WinError(error)

    def assign(self, pid):
        process = self.k.OpenProcess(0x0101, False, pid)  # SET_QUOTA | TERMINATE
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.k.AssignProcessToJobObject(self.handle, process):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.k.CloseHandle(process)

    def close(self):
        if not self.handle:
            return
        try:
            if not self.k.TerminateJobObject(self.handle, 1):
                raise ctypes.WinError(ctypes.get_last_error())
            end = time.monotonic() + 10
            while True:
                info = self.accounting()
                if not self.k.QueryInformationJobObject(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                if not info.active:
                    break
                if time.monotonic() >= end:
                    raise RuntimeError('Owned worker processes have not exited; review cleanup')
                time.sleep(0.05)
        finally:
            self.k.CloseHandle(self.handle); self.handle = None


def worker(folder):
    control = read_json(folder / 'worker.json')
    end = time.monotonic() + 120
    while not (folder / 'start.json').exists():
        if time.monotonic() >= end:
            raise RuntimeError('Worker was not assigned to its cleanup job; no experiment started')
        time.sleep(0.1)
    gate = read_json(folder / 'start.json')
    if gate != {'worker_pid': os.getpid(), 'parent_pid': os.getppid()}:
        raise RuntimeError('Worker gate identity mismatch')
    if identity(__file__) != control['launcher_source'] or hosts(resources.snapshot()):
        raise RuntimeError('Launcher changed or Codex is still open')
    state = run_jobs.execute(read_json(MANIFEST), Path(control['session']))
    if state.get('status') != 'collected_for_run3_review':
        raise RuntimeError('Run 2 did not collect every required branch')


def run_worker(folder, session):
    atomic_json(folder / 'worker.json', {'session': str(session), 'launcher_source': identity(__file__)})
    command = [sys.executable, '-B', '-u', '-m', 'execution.manual_run2', '--worker', str(folder)]
    atomic_json(folder / 'worker-command.json', {'argv': command, 'cwd': str(ROOT)})
    job = WindowsJob(); process = None; reader = None; assigned = False
    try:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                   errors='replace', creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        job.assign(process.pid); assigned = True
        def tee():
            with (folder / 'controller.log').open('x', encoding='utf-8') as stream:
                for line in process.stdout:
                    stream.write(line); stream.flush(); print(line, end='', flush=True)
        reader = threading.Thread(target=tee, daemon=True); reader.start()
        atomic_json(folder / 'start.json', {'worker_pid': process.pid, 'parent_pid': os.getpid()})
        while True:
            try:
                code = process.wait(timeout=2)
                break
            except subprocess.TimeoutExpired:
                if hosts(resources.snapshot()):
                    raise RuntimeError('Codex reopened during measurement; owned experiment processes will stop')
        atomic_json(folder / 'worker-exit.json', {'exit_code': code, 'unix': time.time()})
        if code != 0:
            raise RuntimeError('Controller stopped; inspect controller.log and the latest receipt')
    finally:
        # A failure assigning the still-gated worker cannot leave a GPU child.
        if process is not None and not assigned and process.poll() is None:
            process.kill()
        try:
            job.close()
        finally:
            if process is not None:
                process.wait(timeout=15)
            if reader is not None:
                reader.join(timeout=10)
            if process is not None and process.stdout is not None:
                process.stdout.close()


def record_interruption(folder, error):
    """Reconcile an abruptly killed owned controller only after its job is empty."""
    state_path = BASE / 'state.json'
    state = read_json(state_path)
    for row in state['jobs'].values():
        if row.get('status') == 'running':
            row.update(status='BLOCKED', error='Manual launcher stopped owned worker: ' + error,
                       elapsed_seconds=time.time() - row['started_unix'])
            receipt = Path(row['attempt']) / 'receipt.json'
            if receipt.exists():
                raise RuntimeError('Interrupted receipt already exists; preserve and review')
            atomic_json(receipt, row)
    atomic_json(state_path, state)
    lock = BASE / 'ACTIVE.json'
    if lock.exists():
        # Do not remove this lock automatically; future review checks its owner.
        atomic_json(folder / 'stale-controller-lock.json', read_json(lock))


def require_complete(manifest, state, runtime):
    checked = audit(manifest, state, runtime)
    if checked['remaining'] or state.get('status') != 'collected_for_run3_review':
        raise RuntimeError('Required jobs remain incomplete')
    if sum(j['kind'] == 'benchmark' for j in manifest['jobs']) != 28:
        raise RuntimeError('Wrong benchmark count')
    pilot = Path(state['jobs']['match-estimate-2']['attempt']) / 'work/pilot'
    estimate = read_json(pilot / 'estimate.json')
    from execution.match_runner import journal_records
    games = journal_records(pilot, read_json(pilot / 'contract.json'))
    if (estimate['games'] != 2 or len(games) != 2 or
            sorted(e['record']['game'] for e in games) != [0, 1] or
            estimate['seconds_per_game'] <= 0):
        raise RuntimeError('Two completed pilot games are required')
    return checked


def launch(args, manifest, old_session):
    if not args.confirm_exclusive or not args.confirm_same_power_mode or args.approve_retry != RETRY_JOB:
        raise RuntimeError('Supply all operator confirmations and the specific --approve-retry job')
    require_external_terminal(resources.snapshot(), os.getpid())
    with single_workload(BASE / 'MANUAL_ACTIVE.json'):
        folder = BASE / ('manual-resume-' + str(time.time_ns()))
        folder.mkdir()
        source = identity(__file__)
        summary = {'status': 'waiting_for_host_exit', 'started_unix': time.time(),
                   'launcher_source': source, 'manifest': MANIFEST_SHA,
                   'operator_confirmations': vars(args),
                   'awake_request': {'requested': False, 'released': False},
                   'mode': 'external PowerShell; Codex fully closed; original guard unchanged'}
        atomic_json(folder / 'summary.json', summary)
        print('Evidence folder: ' + str(folder), flush=True)
        worker_started = False
        try:
            with keep_awake(summary['awake_request']):
                wait_for_host_exit()
                # Re-read after the operator closes Codex; never rely on a stale plan snapshot.
                state = read_json(BASE / 'state.json')
                checked = audit(manifest, state, old_session['runtime'])
                inventory = known_failure(state)
                if len(checked['verified']) != 35 or len(checked['remaining']) != 10:
                    raise RuntimeError('Unexpected checkpoint; separate review required')
                runtime, observations = observe_runtime(old_session['runtime'])
                atomic_json(folder / 'runtime.json', observations)
                quiet_preflight(folder)
                session = {'root': str(ROOT), 'created_unix': time.time(),
                           'exclusive_authorized': True, 'work_saved': True,
                           'ac_power_confirmed': True, 'other_work_paused': True,
                           'resource_preflight_passed': True, 'runtime': runtime,
                           'preflight': str(folder / 'preflight.json'),
                           'authorization': 'Approved manual Run2 continuation; explicit operator CLI confirmations',
                           'operator_same_OEM_and_Windows_power_mode': True,
                           'session_difference': 'Codex fully closed; review thermal/clock conditions across sessions',
                           'launcher_source': source}
                session_path = folder / 'session.json'; atomic_json(session_path, session)
                authorize_retry(state, folder, session_path, inventory)
                summary['status'] = 'running'; atomic_json(folder / 'summary.json', summary)
                worker_started = True
                run_worker(folder, session_path)
                checked = require_complete(manifest, read_json(BASE / 'state.json'), runtime)
                if identity(__file__) != source:
                    raise RuntimeError('Launcher source changed during execution')
                for item in inventory:
                    if identity(item['path']) != item:
                        raise RuntimeError('Original failed evidence changed')
                summary.update(status='COLLECTED_AWAITING_CODEX_VERIFICATION',
                               verified_jobs=len(checked['verified']), benchmark_trials=28, pilot_games=2)
        except BaseException as exc:
            summary.update(status='BLOCKED', error=repr(exc))
            if worker_started:
                try:
                    record_interruption(folder, repr(exc))
                except Exception as reconcile_error:
                    summary['reconciliation_error'] = repr(reconcile_error)
            print('BLOCKED: ' + str(exc), flush=True)
        finally:
            summary.update(ended_unix=time.time())
            atomic_json(folder / 'summary.json', summary)
        print(summary['status'] + ' | ' + str(folder / 'summary.json'), flush=True)
        return 0 if summary['status'] == 'COLLECTED_AWAITING_CODEX_VERIFICATION' else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--execute', action='store_true')
    ap.add_argument('--confirm-exclusive', action='store_true')
    ap.add_argument('--confirm-same-power-mode', action='store_true')
    ap.add_argument('--approve-retry', choices=[RETRY_JOB])
    ap.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.worker is not None:
        worker(args.worker.resolve()); return 0
    if Path.cwd().resolve() != ROOT or subprocess.check_output(
            ['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() != 'anjan':
        raise RuntimeError('Run from the repository root on anjan')
    manifest = read_json(MANIFEST); state = read_json(BASE / 'state.json')
    original = read_json(BASE / RETRY_JOB / 'attempt-001/receipt.json')
    if identity(original['session']['path']) != original['session']:
        raise RuntimeError('Original session record changed')
    old_session = read_json(original['session']['path'])
    if Path(sys.executable).resolve() != Path(manifest['jobs'][0]['command'][0]).resolve():
        raise RuntimeError('Use the original .venv Python')
    if (BASE / 'ACTIVE.json').exists() or (BASE / 'MANUAL_ACTIVE.json').exists():
        raise RuntimeError('An active/stale lock requires review; do not delete it blindly')
    checked = audit(manifest, state, old_session['runtime'])
    if not args.execute:
        print(json.dumps({'mode': 'read_only_check', 'GPU_workloads_started': 0,
                          'verified_jobs': len(checked['verified']), **checked}, indent=2))
        return 0
    if not checked['remaining']:
        require_complete(manifest, state, old_session['runtime'])
        print('ALREADY COLLECTED - reopen Codex for verification'); return 0
    return launch(args, manifest, old_session)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt) as exc:
        print('BLOCKED: ' + repr(exc), file=sys.stderr)
        sys.exit(1)
