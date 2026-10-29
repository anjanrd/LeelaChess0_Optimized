"""Analysis regression checks; no engine, model inference or source mutation."""
import importlib.util
import json
from pathlib import Path
import unittest

import chess

ROOT=Path(__file__).resolve().parents[1]


def load(name,relative):
    s=importlib.util.spec_from_file_location(name,ROOT/relative)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


RUN=load('person_a_run1','analysis/person_a/run1.py')
READY=load('person_a_readiness','analysis/person_a/readiness.py')


class PersonARegression(unittest.TestCase):
    def test_duplicate_result_keys_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            RUN.keyed([{'id':1,'budget':100},{'id':1,'budget':100}],['id','budget'])

    def test_symmetry_equivalence_preserves_mirror_and_allowed_transforms(self):
        pawn=chess.Board('7k/8/8/8/8/2P5/8/K7 w - - 0 1')
        self.assertEqual(RUN.group_id(pawn),RUN.group_id(pawn.mirror()))
        self.assertEqual(RUN.group_id(pawn),RUN.group_id(pawn.transform(chess.flip_horizontal)))
        pawnless=chess.Board('7k/8/8/8/8/2Q5/8/K7 w - - 0 1')
        self.assertEqual(RUN.group_id(pawnless),RUN.group_id(pawnless.transform(chess.flip_diagonal)))

    def test_paired_direction_and_move_correctness(self):
        tb={1:{'correct':['a']},2:{'correct':['a']},3:{'correct':['a']}}
        ref={1:{'best':'a'},2:{'best':'b'},3:{'best':'a'}}
        model={1:{'best':'b'},2:{'best':'a'},3:{'best':'a'}}
        p=RUN.paired(tb,[1,2,3],model,ref)
        self.assertEqual((p['correct'],p['worse'],p['better']),(2,1,1))
        self.assertEqual(p['mcnemar_p'],1)

    def test_only_explicit_A5_deferral_bypasses_A6(self):
        state={'steps':{'A5':{'status':'deferred_user_authorized'}},'A5_deferred_by_user':True}
        self.assertTrue(RUN.prerequisite_allowed('A6',state))
        self.assertFalse(RUN.prerequisite_allowed('A7',state))
        state['A5_deferred_by_user']=False
        self.assertFalse(RUN.prerequisite_allowed('A6',state))

    def test_A5_remains_a_run2_reminder_until_explicitly_cleared(self):
        p={'steps':{'A5':{'status':'deferred_user_authorized'}}}
        deps={'R1':{'status':'RECEIVED_AND_REVIEWED'}}
        self.assertFalse(READY.assess(p,deps)['ready_for_run2'])
        self.assertTrue(READY.assess(p,deps)['A5_reminder_required'])
        p['steps']['A5']['status']='verified'
        self.assertTrue(READY.assess(p,deps)['ready_for_run2'])

    def test_actual_main_score_regression_including_JSON_budget_keys(self):
        tb,data,cohort,_=RUN.context()
        _,result=RUN.SCORER.score(tb,data,'fp16',RUN.MODELS,set(cohort))
        normalized=json.loads(json.dumps(result))
        saved=RUN.read('reports/scores_test.json')
        for name in RUN.MODELS:
            self.assertEqual(normalized['models'][name]['A'],saved['models'][name]['A'],name)
            if name!='s0':self.assertEqual(normalized['models'][name]['B'],saved['models'][name]['B'],name)

    def test_frontier_preparation_has_no_fabricated_speed_or_swaps(self):
        records=RUN.csvread('analysis/tables/frontier-quality-ready.csv')
        self.assertEqual({r['model'] for r in records},set(RUN.FRONTIER))
        self.assertTrue(all(int(r['n'])==2437 for r in records))
        self.assertNotIn('nps',records[0])


if __name__=='__main__':
    unittest.main()
