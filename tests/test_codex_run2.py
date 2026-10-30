"""Approved monitor-only policy tests; no engines or GPU workloads."""
import unittest
import tempfile
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import redirect_stdout
from execution import codex_run2 as controller
from execution.codex_run2 import check_conditions
from execution.support import atomic_json, read_json


class MonitorPolicy(unittest.TestCase):
    def test_background_flags_are_information_not_a_stop(self):
        check_conditions({'monitor_errors': [], 'flags': [
            'sustained external CPU activity: ChatGPT.exe',
            'external GPU compute PID: 123', 'close nonessential application: msedge.exe']})

    def test_measurement_failures_and_ac_loss_still_stop(self):
        for row in ({'monitor_errors': ['NVML unavailable'], 'flags': []},
                    {'monitor_errors': [], 'flags': ['AC power disconnected']}):
            with self.subTest(row=row), self.assertRaises(RuntimeError):
                check_conditions(row)

    def fake_execution(self, returncode):
        with tempfile.TemporaryDirectory(prefix='lc0-policy-v2-') as temp:
            root = Path(temp); old = root / 'original'; old.mkdir(); output = root / 'new'; output.mkdir()
            manifest = {'output': str(output), 'policy': controller.POLICY, 'runtime': {}, 'tools': {},
                        'adopted_verified_jobs': ['old-' + str(i) for i in range(43)],
                        'jobs': [{'id': str(i), 'command': ['fake', '{attempt}'], 'depends_on': [],
                                  'outputs': ['work/result.json']} for i in range(2)]}
            class Monitor:
                def __init__(self, path): self.path = path
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def report(self, pid):
                    return {'flags': ['sustained external CPU activity: ChatGPT.exe'], 'monitor_errors': []}
            calls = []
            def command(argv, log, **kwargs):
                calls.append(argv)
                atomic_json(Path(argv[1]) / 'work/result.json', {'fixture': True})
                return SimpleNamespace(returncode=returncode)
            session = root / 'session.json'; atomic_json(session, {})
            with patch.object(controller, 'ORIGINAL', old), \
                    patch.object(controller.subprocess, 'check_output', return_value='anjan'), \
                    patch.object(controller, 'require_session', return_value={'resource_preflight_passed': True, 'runtime': {}}), \
                    patch.object(controller, 'verify_parent'), \
                    patch.object(controller, 'scoped_environment', return_value={}), \
                    patch.object(controller.resources, 'ActivityMonitor', Monitor), \
                    patch.object(controller, 'preserve_command', side_effect=command), redirect_stdout(io.StringIO()):
                if returncode:
                    with self.assertRaisesRegex(RuntimeError, 'Child command exited'):
                        controller.execute(manifest, session)
                    self.assertEqual(len(calls), 1)
                    self.assertEqual(read_json(output / 'state.json')['jobs']['0']['status'], 'BLOCKED')
                else:
                    state = controller.execute(manifest, session)
                    self.assertEqual(len(calls), 2)
                    self.assertEqual(state['status'], 'collected_for_run3_review')
                    self.assertTrue(state['jobs']['0']['background_flags_observed'])
                self.assertFalse((old / 'ACTIVE.json').exists())

    def test_background_spike_is_recorded_and_jobs_continue(self): self.fake_execution(0)

    def test_engine_failure_still_stops_the_sequence(self): self.fake_execution(1)


if __name__ == '__main__':
    unittest.main()
