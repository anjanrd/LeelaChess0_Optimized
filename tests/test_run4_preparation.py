"""Fresh reproduction and production acceptance guards; all fixtures are CPU-only."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import chess
from execution import run4_checks, run4
from execution.support import atomic_json, identity


class ReproductionAcceptance(unittest.TestCase):
    def test_impossible_idle_samples_do_not_validate_energy_subtraction(self):
        r = [{'gpu_j': 400, 'seconds': 10, 'power_w_mean': 40}]
        self.assertFalse(run4_checks.idle_diagnosis(r, [{'power_w': 590}])['above_idle_crosscheck_validated'])
        self.assertTrue(run4_checks.idle_diagnosis(r, [{'power_w': 40}])['above_idle_crosscheck_validated'])
        self.assertFalse(run4_checks.idle_diagnosis([], [])['above_idle_crosscheck_validated'])
        self.assertFalse(run4_checks.idle_diagnosis(r, [{'power_w': float('nan')}])['above_idle_crosscheck_validated'])
    def fixture(self, folder):
        weights = folder / 'weights'; weights.write_bytes(b'fixed fixture bytes')
        row = {'id': 1, 'budget': 0, 'best': 'e2e4', 'p': {'e2e4': .6, 'd2d4': .4},
               'wl': .1, 'd': .2, 'v': .3, 'm': 30}
        b = {'id': 1, 'budget': 100, 'best': 'e2e4', 'nodes': 104, 'time_ms': 3, 'wall': .004}
        contract = {'ids': [1], 'roots': [{'id': 1, 'fen': chess.STARTING_FEN, 'correct': ['e2e4']}],
                    'models': {'fixture': {'fresh_weights': str(weights), 'weights_sha256': identity(weights)['sha256'],
                                           'reference_A': [copy.deepcopy(row)], 'reference_B100': [copy.deepcopy(b)]}},
                    'tolerances': {'value_absolute': {'wl': .005, 'd': .005, 'v': .005, 'm': .25},
                                   'normalized_policy_max_absolute': .005}}
        model = folder / 'studies/fixture'; model.mkdir(parents=True)
        (model / 'study_a.jsonl').write_text(json.dumps(row) + '\n')
        (model / 'study_b.jsonl').write_text(json.dumps(b) + '\n')
        atomic_json(model / 'meta.json', {'warnings': []})
        return contract, model, row, b

    def test_same_model_numeric_outputs_pass(self):
        with tempfile.TemporaryDirectory(prefix='lc0-repro-check-') as temp:
            f = Path(temp); contract, model, row, b = self.fixture(f)
            report = run4_checks.check_studies(contract, model.parent, f / 'report.json')
            self.assertEqual(report['status'], 'verified')

    def test_drift_and_changed_raw_move_outcome_are_not_silently_accepted(self):
        for change in ({'wl': .2}, {'best': 'd2d4'}):
            with tempfile.TemporaryDirectory(prefix='lc0-repro-drift-') as temp:
                f = Path(temp); contract, model, row, b = self.fixture(f)
                row.update(change); (model / 'study_a.jsonl').write_text(json.dumps(row) + '\n')
                with self.assertRaisesRegex(RuntimeError, 'requires review'):
                    run4_checks.check_studies(contract, model.parent, f / 'report.json')
                self.assertEqual(json.loads((f / 'report.json').read_text())['status'], 'BLOCKED')

    def test_search_move_differences_are_described_not_bitwise_gated(self):
        with tempfile.TemporaryDirectory(prefix='lc0-repro-search-') as temp:
            f = Path(temp); contract, model, row, b = self.fixture(f)
            b['best'] = 'd2d4'; (model / 'study_b.jsonl').write_text(json.dumps(b) + '\n')
            report = run4_checks.check_studies(contract, model.parent, f / 'report.json')
            self.assertEqual(report['status'], 'verified')
            self.assertEqual(report['models'][0]['search_outcome_changes_descriptive'], [1])

    def test_nonfinite_policy_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='lc0-repro-policy-') as temp:
            f = Path(temp); contract, model, row, b = self.fixture(f)
            row['p']['e2e4'] = float('nan')
            (model / 'study_a.jsonl').write_text(json.dumps(row) + '\n')
            with self.assertRaisesRegex(ValueError, 'nonfinite policy'):
                run4_checks.check_studies(contract, model.parent, f / 'report.json')

    def test_partial_match_cannot_reach_demo(self):
        with patch('execution.match_runner.journal_records', return_value=[]), \
                patch.object(run4, 'read_json', return_value={'complete_color_pairs': 0}), \
                self.assertRaisesRegex(ValueError, '500 games'):
            run4.validate_semantics({'kind': 'gpu_match', 'evidence_dirs': ['fixture']})


if __name__ == '__main__': unittest.main()
