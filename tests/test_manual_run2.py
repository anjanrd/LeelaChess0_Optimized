"""Offline manual-launcher safeguards. Temporary fixtures and CPU-only children."""
import contextlib
import copy
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from execution import manual_run2 as manual
from execution.support import atomic_json, fingerprint, identity, read_json


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='lc0-manual-test-') as temp:
        root = Path(temp); base = root / 'run2'; base.mkdir()
        source = root / 'source.txt'; source.write_text('unchanged')
        jobs = [{'id': 'probe', 'kind': 'probe', 'command': ['fake'], 'outputs': ['work/result.json']},
                {'id': manual.RETRY_JOB, 'kind': 'benchmark', 'command': ['fake'], 'outputs': ['work/result.json']},
                {'id': 'match-estimate-2', 'kind': 'pilot', 'command': ['fake'], 'outputs': ['work/result.json']}]
        manifest = {'output': str(base), 'jobs': jobs, 'sources': [identity(source)]}
        runtime = {'fixture_runtime': 1}; state = {'manifest': fingerprint(manifest), 'jobs': {}}
        for name in ('probe', manual.RETRY_JOB):
            folder = base / name / 'attempt-001'; folder.mkdir(parents=True)
            conditions = {'flags': [] if name == 'probe' else ['sustained external CPU activity: ChatGPT.exe'],
                          'monitor_errors': []}
            atomic_json(folder / 'conditions.json', conditions)
            (folder / 'command.log').write_text('preserved fake command')
            atomic_json(folder / 'result.json', {'fixture': True})
            row = {'status': 'verified' if name == 'probe' else 'BLOCKED', 'attempt': str(folder),
                   'exit_code': 0, 'manifest': fingerprint(manifest), 'job': fingerprint(jobs[0]),
                   'runtime': fingerprint(runtime), 'conditions': identity(folder / 'conditions.json')}
            if name == 'probe':
                row['outputs'] = [identity(p) for p in folder.iterdir()]
            atomic_json(folder / 'receipt.json', row); state['jobs'][name] = row
        atomic_json(base / 'state.json', state)
        failed = base / manual.RETRY_JOB / 'attempt-001'
        inventory = [identity(p) for p in failed.iterdir()]
        atomic_json(root / 'progress.json', {'runs': {'2': {'checkpoint': {'blocked_attempt_inventory': inventory}}}})
        session = base / 'test-session.json'; atomic_json(session, {'runtime': runtime})
        folder = base / 'manual-resume-test'; folder.mkdir()
        with patch.object(manual, 'BASE', base), patch.object(manual, 'MANIFEST_SHA', fingerprint(manifest)), \
                patch.object(manual, 'FAILED_SHA', identity(failed / 'receipt.json')['sha256']):
            yield SimpleNamespace(base=base, manifest=manifest, state=state, runtime=runtime,
                                  folder=folder, session=session, inventory=inventory, failed=failed)


class ManualGuards(unittest.TestCase):
    def test_external_terminal_rejects_codex_ancestor(self):
        sample = {'processes': [{'pid': 20, 'ppid': 10, 'name': 'python.exe'},
                                {'pid': 10, 'ppid': 1, 'name': 'ChatGPT.exe'}]}
        with self.assertRaisesRegex(RuntimeError, 'Windows Start'):
            manual.require_external_terminal(sample, 20)
        sample['processes'][1]['name'] = 'powershell.exe'
        manual.require_external_terminal(sample, 20)

    def test_host_wait_and_timeout_do_not_start_jobs(self):
        open_app = {'processes': [{'pid': 1, 'name': 'ChatGPT.exe'}]}
        with patch.object(manual.resources, 'snapshot', side_effect=[open_app, {'processes': []}]), \
                patch.object(manual.time, 'sleep') as sleep, contextlib.redirect_stdout(io.StringIO()):
            manual.wait_for_host_exit(); sleep.assert_called_once_with(2)
        with patch.object(manual.resources, 'snapshot', return_value=open_app), \
                patch.object(manual.time, 'monotonic', side_effect=[0, 2]), \
                contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, 'still present'):
            manual.wait_for_host_exit(timeout=1)

    def test_quiet_preflight_rejects_ac_host_gpu_and_original_flags(self):
        good = {'ac_line': 1, 'processes': [], 'gpu': {'util': 0}}
        report = {'flags': [], 'monitor_errors': []}
        manual.validate_quiet([good], report)
        for change in ({'ac_line': 0}, {'ac_line': None}, {'gpu': {'util': 10}},
                       {'processes': [{'pid': 1, 'name': 'codex.exe'}]}):
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                manual.validate_quiet([{**good, **change}], report)
        with self.assertRaises(RuntimeError):
            manual.validate_quiet([good], {'flags': ['CPU interference'], 'monitor_errors': []})

    def test_reuse_audit_checks_files_without_modifying_them(self):
        with fixture() as f:
            before = identity(f.base / 'state.json')
            result = manual.audit(f.manifest, f.state, f.runtime)
            self.assertEqual(result['verified'], ['probe'])
            self.assertEqual(identity(f.base / 'state.json'), before)
            (f.base / 'probe/attempt-001/result.json').write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError, 'output changed'):
                manual.audit(f.manifest, f.state, f.runtime)

    def test_changed_manifest_and_runtime_cannot_reuse_results(self):
        with fixture() as f:
            changed = copy.deepcopy(f.manifest); changed['jobs'][0]['command'] = ['different']
            with self.assertRaisesRegex(ValueError, 'manifest changed'):
                manual.audit(changed, f.state, f.runtime)
            with self.assertRaisesRegex(ValueError, 'Runtime/power'):
                manual.audit(f.manifest, f.state, {'changed': True})

    def test_only_exact_failed_receipt_can_be_reviewed_and_original_stays_immutable(self):
        with fixture() as f:
            original = (f.failed / 'receipt.json').read_bytes()
            inventory = manual.known_failure(f.state)
            manual.authorize_retry(f.state, f.folder, f.session, inventory)
            self.assertEqual((f.failed / 'receipt.json').read_bytes(), original)
            state = read_json(f.base / 'state.json')
            self.assertEqual(state['jobs'][manual.RETRY_JOB]['status'], 'reviewed_retry')
            self.assertEqual(read_json(f.folder / 'retry-review.json')['prior_row'], f.state['jobs'][manual.RETRY_JOB])
            with self.assertRaisesRegex(RuntimeError, 'original host-CPU'):
                manual.known_failure(state)

    def test_changed_failed_raw_evidence_is_rejected(self):
        with fixture() as f:
            (f.failed / 'command.log').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'failed evidence changed'):
                manual.known_failure(f.state)

    def test_retry_cannot_overwrite_a_changed_state_or_active_controller(self):
        with fixture() as f:
            changed = copy.deepcopy(f.state); changed['different'] = True
            atomic_json(f.base / 'state.json', changed)
            with self.assertRaisesRegex(RuntimeError, 'changed during preflight'):
                manual.authorize_retry(f.state, f.folder, f.session, f.inventory)
            self.assertFalse((f.folder / 'retry-review.json').exists())
            (f.base / 'ACTIVE.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError, 'lock requires review'):
                manual.authorize_retry(f.state, f.folder, f.session, f.inventory)

    def test_runtime_is_observed_not_blindly_copied(self):
        old = dict(GPU_name='GPU', GPU_uuid='uuid', driver_version='driver', memory_MiB='8192',
                   power_limit_query='[N/A]', power_scheme='scheme', python='3.11', platform='Windows',
                   prepared_manifest=manual.MANIFEST_SHA, OEM_mode='unobserved')
        with patch.object(manual.subprocess, 'check_output', side_effect=['GPU, uuid, driver, 8192, [N/A]\n', 'scheme']), \
                patch.object(manual.platform, 'python_version', return_value='3.11'), \
                patch.object(manual.platform, 'platform', return_value='Windows'):
            self.assertEqual(manual.observe_runtime(old)[0], old)
        with patch.object(manual.subprocess, 'check_output', side_effect=['GPU, uuid, NEW, 8192, [N/A]\n', 'scheme']), \
                patch.object(manual.platform, 'python_version', return_value='3.11'), \
                patch.object(manual.platform, 'platform', return_value='Windows'), \
                self.assertRaisesRegex(RuntimeError, 'do not pool'):
            manual.observe_runtime(old)

    def test_missing_operator_confirmations_cannot_launch(self):
        args = SimpleNamespace(confirm_exclusive=False, confirm_same_power_mode=True,
                               approve_retry=manual.RETRY_JOB)
        with self.assertRaisesRegex(RuntimeError, 'confirmations'):
            manual.launch(args, {}, {})

    def test_worker_gate_blocks_execution_before_assignment(self):
        with fixture() as f:
            atomic_json(f.folder / 'worker.json', {'launcher_source': identity(manual.__file__), 'session': str(f.session)})
            atomic_json(f.folder / 'start.json', {'worker_pid': -1, 'parent_pid': -1})
            with patch.object(manual.run_jobs, 'execute') as execute, self.assertRaisesRegex(RuntimeError, 'gate identity'):
                manual.worker(f.folder)
            execute.assert_not_called()

    def test_gated_worker_calls_existing_controller_with_the_fresh_session(self):
        with fixture() as f:
            atomic_json(f.folder / 'worker.json', {'launcher_source': identity(manual.__file__), 'session': str(f.session)})
            atomic_json(f.folder / 'start.json', {'worker_pid': os.getpid(), 'parent_pid': os.getppid()})
            manifest_path = f.base / 'manifest.json'; atomic_json(manifest_path, f.manifest)
            with patch.object(manual, 'MANIFEST', manifest_path), \
                    patch.object(manual.resources, 'snapshot', return_value={'processes': []}), \
                    patch.object(manual.run_jobs, 'execute', return_value={'status': 'collected_for_run3_review'}) as execute:
                manual.worker(f.folder)
                execute.assert_called_once_with(f.manifest, f.session)

    def test_codex_reopen_stops_worker_and_closes_its_cleanup_job(self):
        with fixture() as f:
            class Process:
                pid = 999999
                stdout = io.StringIO('fixture progress\n')
                stopped = False
                def wait(self, timeout=None):
                    if self.stopped: return 1
                    raise subprocess.TimeoutExpired('fixture', timeout)
                def poll(self): return 1 if self.stopped else None
            process = Process()
            class Job:
                closed = False
                def assign(self, pid): self.pid = pid
                def close(self): self.closed = True; process.stopped = True
            job = Job()
            with patch.object(manual.subprocess, 'Popen', return_value=process), \
                    patch.object(manual, 'WindowsJob', return_value=job), \
                    patch.object(manual.resources, 'snapshot', return_value={'processes': [{'name': 'ChatGPT.exe', 'pid': 5}]}), \
                    contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, 'reopened'):
                manual.run_worker(f.folder, f.session)
            self.assertTrue(job.closed)

    def test_collection_requires_both_correctly_numbered_pilot_games(self):
        with fixture() as f:
            pilot = f.folder / 'work/pilot'; pilot.mkdir(parents=True)
            atomic_json(pilot / 'estimate.json', {'games': 2, 'seconds_per_game': 10})
            atomic_json(pilot / 'contract.json', {'fixture': True})
            state = {'status': 'collected_for_run3_review', 'jobs': {'match-estimate-2': {'attempt': str(f.folder)}}}
            manifest = {'jobs': [{'kind': 'benchmark'} for _ in range(28)]}
            for ids in ([0, 1], [0], [1, 2]):
                records = [{'record': {'game': i}} for i in ids]
                with patch.object(manual, 'audit', return_value={'remaining': [], 'verified': list(range(45))}), \
                        patch('execution.match_runner.journal_records', return_value=records):
                    if ids == [0, 1]:
                        self.assertFalse(manual.require_complete(manifest, state, f.runtime)['remaining'])
                    else:
                        with self.assertRaisesRegex(RuntimeError, 'Two completed pilot games'):
                            manual.require_complete(manifest, state, f.runtime)

    def test_interrupted_owned_attempt_is_blocked_without_rewriting_old_receipt(self):
        with fixture() as f:
            original = identity(f.failed / 'receipt.json')
            folder = f.base / 'another/attempt-001'; folder.mkdir(parents=True)
            row = {'status': 'running', 'started_unix': time.time(), 'attempt': str(folder)}
            f.state['jobs']['another'] = row; atomic_json(f.base / 'state.json', f.state)
            manual.record_interruption(f.folder, 'fixture cancellation')
            self.assertEqual(read_json(folder / 'receipt.json')['status'], 'BLOCKED')
            self.assertEqual(identity(f.failed / 'receipt.json'), original)

    def test_incomplete_jobs_cannot_print_collection_success(self):
        with patch.object(manual, 'audit', return_value={'remaining': ['one']}), \
                self.assertRaisesRegex(RuntimeError, 'incomplete'):
            manual.require_complete({}, {}, {})

    def test_launcher_failure_has_fresh_session_and_preserves_old_failure(self):
        with fixture() as f:
            args = SimpleNamespace(confirm_exclusive=True, confirm_same_power_mode=True,
                                   approve_retry=manual.RETRY_JOB, worker=None)
            sample = {'processes': [{'pid': os.getpid(), 'ppid': 1, 'name': 'python.exe'}]}
            @contextlib.contextmanager
            def awake(record):
                record['requested'] = True
                try: yield
                finally: record['released'] = True
            with patch.object(manual.resources, 'snapshot', return_value=sample), \
                    patch.object(manual, 'keep_awake', side_effect=awake), \
                    patch.object(manual, 'wait_for_host_exit'), \
                    patch.object(manual, 'quiet_preflight'), \
                    patch.object(manual, 'observe_runtime', return_value=(f.runtime, {})), \
                    patch.object(manual, 'audit', return_value={'verified': list(range(35)), 'remaining': list(range(10))}), \
                    patch.object(manual, 'run_worker', side_effect=RuntimeError('fixture CPU flag')), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(manual.launch(args, f.manifest, {'runtime': f.runtime, 'created_unix': 1}), 1)
            folders = [p for p in f.base.glob('manual-resume-*') if (p / 'summary.json').exists()]
            self.assertEqual(len(folders), 1)
            summary = read_json(folders[0] / 'summary.json')
            self.assertEqual(summary['status'], 'BLOCKED')
            self.assertTrue(summary['awake_request']['released'])
            session = read_json(folders[0] / 'session.json')
            self.assertGreater(session['created_unix'], 1)
            self.assertTrue(session['resource_preflight_passed'])
            self.assertEqual(identity(f.failed / 'receipt.json')['sha256'], manual.FAILED_SHA)


@unittest.skipUnless(os.name == 'nt', 'native Windows CPU process containment')
class NativeContainment(unittest.TestCase):
    def test_job_close_terminates_only_its_cpu_child_and_grandchild(self):
        # Child is gated before assignment, exactly like the real worker. No DLL,
        # lc0, model inference, NVML or GPU workload is used by this test.
        with tempfile.TemporaryDirectory(prefix='lc0-owned-cpu-') as temp:
            gate = Path(temp) / 'gate'; pid_file = Path(temp) / 'child.pid'
            code = ('import pathlib,time,subprocess,sys\n'
                    'gate=pathlib.Path(sys.argv[1])\n'
                    'while not gate.exists():time.sleep(.01)\n'
                    'p=subprocess.Popen([sys.executable,"-B","-c","import time;time.sleep(120)"])\n'
                    'pathlib.Path(sys.argv[2]).write_text(str(p.pid))\n'
                    'time.sleep(120)\n')
            job = manual.WindowsJob(); process = None
            try:
                process = subprocess.Popen([sys.executable, '-B', '-c', code, str(gate), str(pid_file)],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                job.assign(process.pid); gate.touch()
                end = time.monotonic() + 10
                while not pid_file.exists() and time.monotonic() < end: time.sleep(.02)
                self.assertTrue(pid_file.exists(), 'CPU child did not reach its gate')
                grandchild = int(pid_file.read_text())
                self.assertIn(grandchild, {p['pid'] for p in manual.resources.snapshot()['processes']})
                job.close(); process.wait(timeout=10)
                remaining = {p['pid'] for p in manual.resources.snapshot()['processes']}
                self.assertNotIn(grandchild, remaining)
                self.assertNotIn(process.pid, remaining)
                self.assertIn(os.getpid(), remaining)
            finally:
                job.close()
                if process is not None and process.poll() is None:
                    process.kill(); process.wait(timeout=10)


if __name__ == '__main__':
    unittest.main()
