"""Offline continuation safeguards. Fake commands/engines; no GPU workload."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import chess
import chess.pgn
from execution import benchmark as bench
from execution import match_runner as match
from execution import prepare, resources, run_jobs
from execution.support import (ROOT, atomic_json, fingerprint, identity, read_json,
                               require_session, scoped_environment, single_workload, strict_jsonl)


def envelope(gi,result='1/2-1/2'):
    board=chess.Board()
    moves=match.opening_moves(gi//2)
    for mv in moves:board.push_uci(mv)
    white,black=('fp16','s4') if gi%2==0 else ('s4','fp16')
    sw={'1-0':1.0,'0-1':0.0,'1/2-1/2':0.5}[result]
    record={'game':gi,'pair':gi//2,'opening':(gi//2)%len(match.OPENINGS),'white':white,'black':black,
            'result':result,'score_a':sw if gi%2==0 else 1-sw,'plies':len(moves),
            'reason':'max_plies','seconds':30.0}
    pgn=chess.pgn.Game.from_board(board)
    pgn.headers.update({'White':white,'Black':black,'Result':result,'Round':str(gi+1),
                        'TimeControl':'10+0.1','Termination':'max_plies'})
    return record,str(pgn)


def contract():return {'engine_names':['fp16','s4'],'settings':{'tc':'10+0.1','pairs':2}}


class SupportTests(unittest.TestCase):
    def test_scoped_dll_path_does_not_mutate_environment(self):
        with tempfile.TemporaryDirectory(prefix='lc0-path-') as temp:
            base=Path(temp);lib=base/'trt/lib';lib.mkdir(parents=True)
            (lib/'nvinfer_plugin_10.dll').write_bytes(b'fixture')
            cfg={'trtexec':str(base/'trt/bin/trtexec.exe'),'lc0':str(base/'lc0/lc0.exe')}
            before=dict(os.environ);env=scoped_environment(cfg,{'PATH':'original'})
            self.assertEqual(env['PATH'].split(os.pathsep)[0],str(lib))
            self.assertEqual(dict(os.environ),before)

    def test_nan_and_torn_json_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='lc0-json-') as temp:
            path=Path(temp)/'record.json'
            with self.assertRaises(ValueError):atomic_json(path,{'bad':float('nan')})
            self.assertFalse(path.exists())
            path.write_text('{"a":1}\n{"a":',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Malformed JSONL'):strict_jsonl(path)

    def test_concurrent_lock_is_refused(self):
        with tempfile.TemporaryDirectory(prefix='lc0-lock-') as temp:
            p=Path(temp)/'active.json'
            with single_workload(p):
                with self.assertRaises(FileExistsError):
                    with single_workload(p):pass
                self.assertTrue(p.exists())
            self.assertFalse(p.exists())

    def test_exclusive_template_or_stale_session_cannot_launch(self):
        with tempfile.TemporaryDirectory(prefix='lc0-session-') as temp:
            p=Path(temp)/'session.json';atomic_json(p,{'exclusive_authorized':False})
            with self.assertRaisesRegex(RuntimeError,'explicitly authorized'):require_session(p)
            atomic_json(p,{'exclusive_authorized':True,'work_saved':True,'ac_power_confirmed':True,
                          'other_work_paused':True,'created_unix':time.time()-13*3600,'root':str(ROOT)})
            with self.assertRaisesRegex(RuntimeError,'stale'):require_session(p)


class BenchmarkTests(unittest.TestCase):
    def test_missing_or_wrong_batch_is_not_a_measurement(self):
        for rows in ([],[{'batch':32,'nps':10,'ms':1}],[{'batch':64,'nps':0,'ms':1}]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):bench.validate_backend_rows(rows,64)
        self.assertEqual(bench.validate_backend_rows([{'batch':64,'nps':5000,'ms':12.8}],64)['batch'],64)

    def test_missing_search_or_energy_data_is_rejected(self):
        with self.assertRaises(ValueError):bench.validate_search({'nodes':0},10)
        with self.assertRaises(ValueError):bench.validate_search({'nodes':10,'time_ms':1,'nps':10000,'positions':10},10)


class MatchTests(unittest.TestCase):
    def test_atomic_games_recover_interrupted_combined_exports(self):
        with tempfile.TemporaryDirectory(prefix='lc0-match-') as temp:
            c=contract()
            for gi in (0,1):match.commit_game(temp,c,*envelope(gi))
            (Path(temp)/'games.jsonl').write_text('torn',encoding='utf-8')
            result=match.export_journal(temp,c)
            self.assertEqual(result['complete_color_pairs'],1)
            self.assertEqual(len(strict_jsonl(Path(temp)/'games.jsonl')),2)
            self.assertFalse(result['ci_reportable'])
            match.export_estimate(temp,c)
            self.assertEqual(read_json(Path(temp)/'estimate.json')['seconds_per_game'],30)

    def test_settings_change_or_overwrite_is_refused(self):
        with tempfile.TemporaryDirectory(prefix='lc0-match-change-') as temp:
            c=contract();record,pgn=envelope(0);match.commit_game(temp,c,record,pgn)
            with self.assertRaises(FileExistsError):match.commit_game(temp,c,record,pgn)
            changed=copy.deepcopy(c);changed['settings']['tc']='1+0'
            with self.assertRaisesRegex(ValueError,'different'):match.journal_records(temp,changed)

    def test_result_pgn_color_and_duplicate_guards(self):
        c=contract();record,pgn=envelope(0,'1-0')
        e={'contract':fingerprint(c),'record':record,'pgn':pgn}
        wrong=copy.deepcopy(e);wrong['record']['score_a']=0
        with self.assertRaisesRegex(ValueError,'score disagree'):match.validate_envelope(wrong,c,fingerprint(c))
        wrong=copy.deepcopy(e);wrong['record']['white']='s4'
        with self.assertRaisesRegex(ValueError,'color'):match.validate_envelope(wrong,c,fingerprint(c))
        with self.assertRaisesRegex(ValueError,'Duplicate'):match.checked_summary([e,e],c)

    def test_degenerate_interval_is_not_presented_as_certainty(self):
        c=contract();records=[]
        for gi in range(4):
            record,pgn=envelope(gi);records.append({'contract':fingerprint(c),'record':record,'pgn':pgn})
        s=match.checked_summary(records,c)
        self.assertEqual(s['imported_summary']['elo_pairs'],0)
        self.assertFalse(s['ci_reportable']);self.assertIsNone(s['elo_ci95_reportable'])

    def test_imported_clock_accounting_and_move_flow_are_preserved(self):
        args=SimpleNamespace(tc='10+0.1',syzygy=None,max_plies=2,no_flag=False,
                             resign_cp=1000,draw_after=80,draw_cp=10)
        class Engine:
            def __init__(self,move):self.move=move;self.clock=None
            def newgame(self):pass
            def go(self,**kwargs):
                self.clock=kwargs['clock'];return {'bestmove':self.move,'nodes':25}
        white,black=Engine('e2e4'),Engine('e7e5')
        with patch('eval.match.time.perf_counter',side_effect=[100,100.12,101,101.2]):
            board,moves,result,reason,stats,clock=match.Game(args).play(white,black,[])
        self.assertEqual(moves,['e2e4','e7e5']);self.assertEqual(result,'1/2-1/2')
        self.assertEqual(reason,'max_plies');self.assertAlmostEqual(clock[chess.WHITE],9980)
        self.assertAlmostEqual(clock[chess.BLACK],9900)
        self.assertEqual(black.clock['wtime'],clock[chess.WHITE])


class FakeMonitor:
    def __init__(self,path):self.path=Path(path)
    def __enter__(self):self.path.write_text('CPU fixture; no GPU\n',encoding='utf-8');return self
    def __exit__(self,*args):pass
    def report(self,root):return {'flags':[],'monitor_errors':[],'samples':2}


class JobTests(unittest.TestCase):
    def test_frozen_schedule_has_expected_repeats_and_no_profile_dependency_for_lc0(self):
        cfg=prepare.load_config(ROOT/'config.json');protocol=read_json(ROOT/'execution/protocol.json')
        with patch('execution.prepare.identity',side_effect=lambda p:{'path':str(p),'sha256':'fixture','bytes':1}):
            manifest=prepare.make_manifest(cfg,protocol)
        jobs=run_jobs.validate_manifest(manifest)
        self.assertEqual(len(jobs),45)
        trials=[j for j in jobs if j['kind']=='benchmark']
        self.assertEqual(len(trials),28)
        for name in protocol['models']:
            n=sum(j['id'].startswith('bench-'+name+'-') for j in trials)
            self.assertEqual(n,5 if name in ('fp16','s4') else 3)
        for job in jobs:
            if job['kind'] in ('capture','benchmark','pilot'):
                self.assertFalse(job['profiling_branch'])
        pilot=jobs[-1]['command']
        self.assertEqual(pilot[pilot.index('--estimate')+1],'2')

    def setup_fixture(self,temp):
        base=Path(temp);session=base/'session.json'
        atomic_json(session,{'exclusive_authorized':True,'work_saved':True,'ac_power_confirmed':True,
              'other_work_paused':True,'created_unix':time.time(),'root':str(ROOT),
              'resource_preflight_passed':True,'runtime':{'gpu':'CPU TEST ONLY'}})
        command=[sys.executable,'-B','-c',"from pathlib import Path;Path(r'{attempt}/result.json').write_text('{\"ok\":true}')"]
        job={'id':'toy','kind':'benchmark','command':command,'outputs':['result.json'],'depends_on':[]}
        return {'sources':[],'tools':{},'output':str(base/'out'),'jobs':[job]},session

    def execute(self,manifest,session):
        with patch('execution.resources.ActivityMonitor',FakeMonitor),patch('execution.run_jobs.scoped_environment',return_value=dict(os.environ)):
            return run_jobs.execute(manifest,session)

    def test_verified_resume_checks_hashes_and_does_not_repeat_work(self):
        with tempfile.TemporaryDirectory(prefix='lc0-jobs-') as temp:
            manifest,session=self.setup_fixture(temp)
            first=self.execute(manifest,session);second=self.execute(manifest,session)
            self.assertEqual(first['jobs'],second['jobs'])
            self.assertEqual(len(list((Path(temp)/'out/toy').glob('attempt-*'))),1)
            output=Path(first['jobs']['toy']['outputs'][0]['path']);output.write_text('changed',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'output changed'):self.execute(manifest,session)

    def test_known_plugin_failure_defers_only_its_branch(self):
        with tempfile.TemporaryDirectory(prefix='lc0-plugin-') as temp:
            manifest,session=self.setup_fixture(temp);benchjob=copy.deepcopy(manifest['jobs'][0])
            probe=copy.deepcopy(benchjob);probe.update(id='probe',kind='probe')
            probe['command']=[sys.executable,'-B','-c',"print('Unable to open library: nvinfer_plugin_10.dll');raise SystemExit(1)"]
            profile=copy.deepcopy(benchjob);profile.update(id='profile',kind='profile',profiling_branch=True,depends_on=['probe'])
            manifest['jobs']=[probe,profile,benchjob];result=self.execute(manifest,session)
            self.assertEqual(result['jobs']['probe']['status'],'deferred_known_plugin')
            self.assertEqual(result['jobs']['profile']['status'],'deferred_known_plugin')
            self.assertEqual(result['jobs']['toy']['status'],'verified')

    def test_unexpected_failure_stops_without_running_next_job(self):
        with tempfile.TemporaryDirectory(prefix='lc0-stop-') as temp:
            manifest,session=self.setup_fixture(temp);later=copy.deepcopy(manifest['jobs'][0]);later['id']='later'
            manifest['jobs'][0]['command']=[sys.executable,'-B','-c',"print('unexpected failure');raise SystemExit(2)"]
            manifest['jobs'].append(later)
            with self.assertRaisesRegex(RuntimeError,'exited 2'):self.execute(manifest,session)
            state=read_json(Path(temp)/'out/state.json')
            self.assertEqual(state['jobs']['toy']['status'],'BLOCKED');self.assertNotIn('later',state['jobs'])

    def test_raw_artifact_tampering_also_prevents_reuse(self):
        with tempfile.TemporaryDirectory(prefix='lc0-raw-') as temp:
            manifest,session=self.setup_fixture(temp);first=self.execute(manifest,session)
            raw=Path(first['jobs']['toy']['attempt'])/'activity.log'
            raw.write_text('changed raw evidence',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'output changed'):self.execute(manifest,session)

    def test_launch_exception_is_recorded_blocked(self):
        with tempfile.TemporaryDirectory(prefix='lc0-launch-') as temp:
            manifest,session=self.setup_fixture(temp)
            manifest['jobs'][0]['command']=[str(Path(temp)/'absent-executable.exe')]
            with self.assertRaises(FileNotFoundError):self.execute(manifest,session)
            state=read_json(Path(temp)/'out/state.json')
            self.assertEqual(state['jobs']['toy']['status'],'BLOCKED')

    def test_forward_dependencies_and_false_plugin_matches_are_rejected(self):
        self.assertTrue(run_jobs.known_plugin_failure('Unable to open library: nvinfer_plugin_10.dll'))
        self.assertFalse(run_jobs.known_plugin_failure('Loaded nvinfer_plugin_10.dll; out of memory'))
        self.assertFalse(run_jobs.known_plugin_failure('Unable to open library: unrelated.dll'))
        with self.assertRaises(ValueError):
            run_jobs.validate_manifest({'jobs':[{'id':'a','kind':'probe','command':['x'],'depends_on':['b']}]})

    def test_plan_mode_does_not_execute_its_command(self):
        with tempfile.TemporaryDirectory(prefix='lc0-dry-') as temp:
            manifest,_=self.setup_fixture(temp);path=Path(temp)/'plan.json';atomic_json(path,manifest)
            for extra in ([],['--plan']):
                result=subprocess.run([sys.executable,'-B','-m','execution.run_jobs','--manifest',str(path)]+extra,
                                      cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(json.loads(result.stdout)['GPU_workloads_started'],0)
            self.assertFalse(Path(manifest['output']).exists())


class ResourceTests(unittest.TestCase):
    def samples(self):
        return [{'unix':i*2,'ac_line':1,'logical_cpus':8,'gpu_compute_pids':[200],
                'processes':[{'pid':100,'ppid':1,'name':'python.exe','cpu_seconds':i*.01},
                  {'pid':200,'ppid':100,'name':'lc0.exe','cpu_seconds':i*8.0},
                  {'pid':300,'ppid':1,'name':'other.exe','cpu_seconds':i*0.01}]} for i in range(4)]

    def test_own_workload_is_not_mistaken_for_interference(self):
        self.assertEqual(resources.external_flags(self.samples(),100),[])

    def test_external_cpu_gpu_and_ac_interference_are_flagged(self):
        samples=self.samples()
        for i,s in enumerate(samples):s['processes'][2]['cpu_seconds']=i*1.0
        self.assertTrue(any('CPU' in x for x in resources.external_flags(samples,100)))
        samples=self.samples();samples[-1]['gpu_compute_pids'].append(999)
        self.assertTrue(any('GPU' in x for x in resources.external_flags(samples,100)))
        samples=self.samples();samples[-1]['ac_line']=0
        self.assertIn('AC power disconnected',resources.external_flags(samples,100))

    @unittest.skipUnless(os.name=='nt','Windows host observation')
    def test_native_snapshot_is_cpu_only_and_has_current_process(self):
        s=resources.snapshot()
        self.assertIn(os.getpid(),{p['pid'] for p in s['processes']})
        self.assertGreater(s['logical_cpus'],0)

    @unittest.skipUnless(os.name=='nt','Windows PE metadata')
    def test_actual_trtexec_metadata_is_x64_without_loading_it(self):
        cfg=prepare.load_config(ROOT/'config.json');data=prepare.pe_info(cfg['trtexec'])
        self.assertEqual(data['architecture'],'AMD64');self.assertTrue(data['imports'])


if __name__=='__main__':unittest.main()
