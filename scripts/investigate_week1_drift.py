"""Diagnose newly observed baseline drift without rebuilding or tuning on test."""
import collections
import json
import sys

import chess
import numpy as np

from week1_common import PROJECT, TensorRunner, artifact, base, frozen, progress, read, save
from lc0_inputs import input_object, legal_policy, native_encode, wdl_from_qd


def main():
    frozen()
    records=[json.loads(s) for s in (PROJECT/'data/syzygy/test.jsonl').read_text().splitlines()]
    with np.load(PROJECT/'data/syzygy/test-inputs.npz',allow_pickle=False) as d: planes=d['planes'].copy()
    data={}
    for name in ['R32_CUDA','F16_TRT']:
        with np.load(PROJECT/f'results/week1/test-{name}-outputs.npz',allow_pickle=False) as d:
            data[name]={k:d[k].copy() for k in ['logits','wdl','moves_left']}
    differences=abs(data['R32_CUDA']['wdl']-data['F16_TRT']['wdl']).max(axis=1)
    indices=list(map(int,np.argsort(differences)[-8:][::-1]))
    selected=[records[i] for i in indices]
    sys.path.insert(0,str(base.RUNTIME/'build/lc0-tools'))
    import backends
    checkpoint=read(PROJECT/'models/source/checkpoint.json')
    backend=backends.Backend(weights=backends.Weights(str(PROJECT/checkpoint['relative_path'])),backend='eigen',options='batch_size=1,threads=2')
    encoded=native_encode(selected)
    native=[]
    for row,enc in zip(selected,encoded):
        o,=backend.evaluate(input_object(backends,enc))
        native.append([np.asarray(o.p_raw(*range(1858)),dtype=np.float32),wdl_from_qd(o.q(),o.d()),np.array([o.m()],dtype=np.float32)])
    runner=TensorRunner(PROJECT/'environment/step5-engine.json')
    results=[]
    for i,row,ref in zip(indices,selected,native):
        start=(i//8)*8
        batch=runner.run(planes[start:start+8]);local=i-start
        assert all(np.array_equal(output[local],data['F16_TRT'][name][i]) for output,name in zip(batch,['logits','wdl','moves_left']))
        single=[o[0] for o in runner.run(planes[i:i+1])]
        _,pn,mn=legal_policy(ref[0],chess.Board(row['fen']))
        _,p32,m32=legal_policy(data['R32_CUDA']['logits'][i],chess.Board(row['fen']))
        _,p16,m16=legal_policy(data['F16_TRT']['logits'][i],chess.Board(row['fen']))
        r32_wdl=float(abs(ref[1]-data['R32_CUDA']['wdl'][i]).max())
        assert r32_wdl<=.0005 and float(abs(pn-p32).max())<=.0002
        results.append({'id':row['id'],'family':row['family'],'fen':row['fen'],
            'native_WDL':ref[1].tolist(),'R32_WDL':data['R32_CUDA']['wdl'][i].tolist(),
            'F16_batch8_WDL':data['F16_TRT']['wdl'][i].tolist(),'F16_batch1_WDL':single[1].tolist(),
            'R32_vs_native_WDL_max_abs':r32_wdl,
            'F16_batch8_vs_native_WDL_max_abs':float(abs(ref[1]-data['F16_TRT']['wdl'][i]).max()),
            'F16_batch1_vs_native_WDL_max_abs':float(abs(ref[1]-single[1]).max()),
            'F16_batch8_repeat_bit_identical':True,'native_move':mn,'R32_move':m32,'F16_move':m16,
            'R32_vs_native_legal_probability_max_abs':float(abs(pn-p32).max()),
            'F16_vs_native_legal_probability_max_abs':float(abs(pn-p16).max())})
    runner.close()
    record={'status':'NEW_BASELINE_DRIFT_REQUIRES_USER_REVIEW','recorded_at_utc':base.now(),
        'engine_identity':read(PROJECT/'environment/step5-engine.json')['engine_sha256'],
        'original_WDL_limit':.015,'previously_accepted_observation':.019593477,
        'test_max_F16_vs_R32_WDL_abs':float(differences.max()),
        'roots_above_original_1_5pp_WDL_limit_vs_R32':int((differences>.015).sum()),
        'roots_above_previous_1_9593pp_observation_vs_R32':int((differences>.019593477).sum()),
        'by_material_above_1_5pp':dict(collections.Counter(r['family'] for r,d in zip(records,differences) if d>.015)),
        'diagnostics':results,'accepted_engine_repeated_outputs_exact':True,
        'native_reference_confirms_R32_on_all_eight_largest_cases':True,
        'no_baseline_rebuild_or_tolerance_change':True,'no_INT8_test_tuning':True,
        'interpretation':'Both baseline move-accuracy measurements remain valid measurements of these frozen artifacts. The previous acceptance does not automatically cover this newly observed larger numerical discrepancy. Further acceptance-dependent comparison work is held for user review.',
        'options':['Retain this exact FP16 baseline with explicit acceptance of the newly measured drift; continue to report both baselines separately.',
                   'Reopen FP16 baseline engineering under a new bounded, registered investigation. Preserve all existing results and reassess held-out validation after any model/runtime changes.'],
        'script':artifact(PROJECT/'scripts/investigate_week1_drift.py')}
    save(PROJECT/'environment/week1-baseline-drift-review.json',record)
    progress('W1-A09','REVIEW_REQUIRED','environment/week1-baseline-drift-review.json','Full baseline accuracy measurements are complete, but final numerical audit found larger FP16 WDL drift; native checks confirm the discrepancy. Existing acceptance is not extended silently.')
    progress('W1-A12','AWAITING_USER_DECISION','environment/week1-baseline-drift-review.json','All remaining A-side engineering, data, activation and conversion work is verified. Final baseline acceptance/handoff is held for explicit review of newly discovered drift; no Week 2 work begun.')
    frozen()
    print(json.dumps({'maximum_WDL_difference':float(differences.max()),'n_above_1_5pp':record['roots_above_original_1_5pp_WDL_limit_vs_R32'],'largest_case':results[0]},indent=2),flush=True)


if __name__=='__main__':main()
