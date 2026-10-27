"""Bounded FP16/INT8 batch tuning with separate response-time/throughput optima."""
import argparse
import gc
import json
import random
import time
from pathlib import Path

import numpy as np

from complete_week1_v2 import (PROJECT, WORK, DEST, I1_ENGINE, FLOAT_ENGINE,
    PROTOCOL, TensorRunner, artifact, base, read, save, inputs, rows,
    diagnostics, selected_indices, run_chunks, verify_outputs, checkpoint, frozen)
from refresh_int8_week1 import build_engine, audit_engine
from profile_week1 import telemetry


def stats(values):
    return {'median_ms':float(np.median(values)),'p10_ms':float(np.percentile(values,10)),
        'p95_ms':float(np.percentile(values,95)),'samples_ms':list(map(float,values))}


def measure(model,planes,repeats,warmup):
    torch = model.torch
    output = model.run(planes); verify_outputs(output,len(planes))
    # Input is resident; shape selection/allocation and output transfer excluded.
    model.prepare(len(planes))
    for _ in range(warmup): assert model.context.execute_async_v3(model.stream.cuda_stream)
    model.stream.synchronize()
    start,stop = torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True)
    gpu,host = [],[]
    for _ in range(repeats):
        begin = time.perf_counter()
        start.record(model.stream)
        assert model.context.execute_async_v3(model.stream.cuda_stream)
        stop.record(model.stream); stop.synchronize()
        host.append((time.perf_counter()-begin)*1000)
        gpu.append(float(start.elapsed_time(stop)))
    transfers = []
    for _ in range(repeats):
        begin = time.perf_counter(); again = model.run(planes)
        transfers.append((time.perf_counter()-begin)*1000)
    assert all(np.array_equal(a,b) for a,b in zip(output,again))
    batch = len(planes)
    return {'batch':batch,'resident_gpu':stats(gpu),'resident_synchronized_host':stats(host),
        'host_pipeline':stats(transfers),'resident_amortized_ms_per_position':float(np.median(gpu)/batch),
        'resident_positions_per_second':float(1000*batch/np.median(gpu)),
        'host_amortized_ms_per_position':float(np.median(transfers)/batch),
        'host_positions_per_second':float(1000*batch/np.median(transfers))}


def combine(rounds):
    result = {}
    for name in ['F16_TRT','I1_TRT']:
        result[name] = {}
        batches = sorted({int(b) for r in rounds for b in r[name]})
        for b in batches:
            parts = [r[name][str(b)] for r in rounds if str(b) in r[name]]
            row = {'batch':b}
            for metric in ['resident_gpu','resident_synchronized_host','host_pipeline']:
                row[metric] = stats([x for part in parts for x in part[metric]['samples_ms']])
            row['resident_amortized_ms_per_position'] = row['resident_gpu']['median_ms']/b
            row['resident_positions_per_second'] = 1000*b/row['resident_gpu']['median_ms']
            row['host_amortized_ms_per_position'] = row['host_pipeline']['median_ms']/b
            row['host_positions_per_second'] = 1000*b/row['host_pipeline']['median_ms']
            result[name][str(b)] = row
    return result


def objective(row,which):
    if which == 'resident_latency': return row['resident_gpu']['median_ms']
    if which == 'host_latency': return row['host_pipeline']['median_ms']
    if which == 'resident_throughput': return row['resident_amortized_ms_per_position']
    if which == 'host_throughput': return row['host_amortized_ms_per_position']
    raise ValueError(which)


OBJECTIVES = ['resident_latency','host_latency','resident_throughput','host_throughput']


def sweep(label,records,candidates,repeats=40,round_count=2):
    path = DEST/f'batch-sweep-{label}.json'
    if path.exists():
        old = read(path)
        assert old['engine_records'] == {n:artifact(p) for n,p in records.items()}
        assert old['batch_candidates'] == list(candidates)
        return old
    before = telemetry()
    planes = inputs('calibration')[0]
    runners = {name:TensorRunner(p) for name,p in records.items()}
    samples = []; rng = random.Random(20261027)
    for r in range(round_count):
        sample = {name:{} for name in records}
        ordered = list(candidates); rng.shuffle(ordered)
        for j,b in enumerate(ordered):
            names = list(records)
            if (r+j)%2: names.reverse()
            for name in names:
                sample[name][str(b)] = measure(runners[name],planes[:b],repeats,20)
            a,brow = [sample[n][str(b)] for n in ['F16_TRT','I1_TRT']]
            print(label,'round',r+1,'batch',b,'GPU ms F16/I1',round(a['resident_gpu']['median_ms'],4),round(brow['resident_gpu']['median_ms'],4),flush=True)
        samples.append(sample)
    for runner in runners.values(): runner.close()
    del runners; gc.collect()
    result = {'status':'passed','label':label,'created_at_utc':base.now(),'before':before,'after':telemetry(),
        'engine_records':{n:artifact(p) for n,p in records.items()},'batch_candidates':list(candidates),
        'rounds':samples,'combined':combine(samples),'repeats_per_round':repeats,'warmups_per_measurement':20,
        'boundaries':read(PROTOCOL)['timing']['metrics'],'script':artifact(Path(__file__))}
    save(path,result)
    return result


def verify_expanded(record_path,name):
    # Tactic changes are diagnostic, never selected using prediction agreement.
    index = selected_indices(); planes = inputs('calibration')[0][index]
    records = [rows('calibration')[i] for i in index]
    original = TensorRunner(FLOAT_ENGINE if name=='F16_TRT' else I1_ENGINE)
    expected = run_chunks(original.run,planes,8)
    original.close(); del original; gc.collect()
    model = TensorRunner(record_path)
    candidate = run_chunks(model.run,planes,8)
    batch1 = run_chunks(model.run,planes,1)
    # Distinct legal inputs exercise the large-batch shape; compare all of them
    # to this same engine at batch 8, without requiring bit-identical tactics.
    maxbatch = read(record_path)['profile'][-1]
    big = inputs('calibration')[0][:maxbatch]
    big_expected = run_chunks(model.run,big,8)
    big_output = model.run(big); verify_outputs(big_output,len(big))
    consistency = diagnostics(rows('calibration')[:maxbatch],big_expected,big_output)
    difference = diagnostics(records,expected,candidate)
    small_batch = diagnostics(records,batch1,candidate)
    model.close(); del model; gc.collect()
    # Reload exact saved timing engine; no build-time cache inference.
    again = TensorRunner(record_path); reloaded = run_chunks(again.run,planes,8)
    assert all(np.array_equal(a,b) for a,b in zip(candidate,reloaded))
    again.close(); del again; gc.collect()
    path = DEST/(Path(record_path).stem+'-parity.json')
    save(path,{'status':'valid_separate_timing_engine_with_disclosed_drift',
        'vs_preserved_engine':difference,'batch1_vs8':small_batch,'batch8_vs_max':consistency,
        'reload_exact_output_match':True,'selection_used_accuracy':False,
        'note':'Builder profile/tactics differ; original FP16 baseline predictions and primary I1 validation remain attached to original saved engines. Broad-engine timings are labeled separately.'})
    return path


def run():
    assert read(PROJECT/'environment/week1-v2-int8-pilot.json')['status']=='verified_pending_batch_sweep'
    protocol = read(PROTOCOL)['timing']
    original = {'F16_TRT':FLOAT_ENGINE,'I1_TRT':I1_ENGINE}
    original_result = sweep('preserved',original,list(range(1,9)))
    broad = {'F16_TRT':build_engine('F16',(1,32,128),'-wide128'),
             'I1_TRT':build_engine('I1',(1,32,128),'-wide128')}
    parity_paths = []
    for name,path in broad.items():
        if read(path)['status'] != 'passed_execution': audit_engine(path,(1,8,128))
        parity_paths.append(verify_expanded(path,name))
    broad_result = sweep('wide128',broad,protocol['batch_candidates'])
    results = [original_result,broad_result]
    active_records = broad; max_batch = 128
    at_boundary = any(min(broad_result['combined'][name].values(),key=lambda row:objective(row,'resident_throughput'))['batch']==128 for name in broad)
    if at_boundary:
        # One predeclared extension, not an unlimited builder optimization search.
        import torch
        free,total = torch.cuda.mem_get_info()
        if free > 3*1024**3:
            extended = {'F16_TRT':build_engine('F16',(1,64,256),'-wide256'),
                        'I1_TRT':build_engine('I1',(1,64,256),'-wide256')}
            for name,path in extended.items():
                if read(path)['status'] != 'passed_execution': audit_engine(path,(1,8,256))
                parity_paths.append(verify_expanded(path,name))
            candidates = protocol['batch_candidates']+[160,192,224,256]
            results.append(sweep('wide256',extended,candidates))
            active_records=extended; max_batch=256
    # Refine within the final common profile around all latency/throughput optima.
    latest = results[-1]['combined']
    tested = sorted({int(b) for b in latest['F16_TRT']})
    extra = set()
    for name in latest:
        for which in OBJECTIVES:
            best = min(latest[name].values(),key=lambda row:objective(row,which))['batch']
            j = tested.index(best)
            low = tested[max(0,j-1)]; high = tested[min(len(tested)-1,j+1)]
            extra.update([best-1,best+1,(low+best)//2,(best+high)//2])
    extra = sorted(b for b in extra if 1<=b<=max_batch and b not in tested)
    if extra: results.append(sweep('refinement',active_records,extra))
    # Finalists are selected by inference timing only. Recheck each model's top
    # two candidates per objective/engine with longer, fresh paired measurements.
    finalists = {}
    for result in results:
        record_key = tuple(p['path'] for p in result['engine_records'].values())
        group = finalists.setdefault(record_key,{'records':{n:Path(v['path']) for n,v in result['engine_records'].items()},'batches':set()})
        for name in result['combined']:
            for which in OBJECTIVES:
                group['batches'].update(row['batch'] for row in sorted(result['combined'][name].values(),key=lambda row:objective(row,which))[:2])
    finals = []
    for j,group in enumerate(finalists.values()):
        finals.append(sweep('finalists'+str(j),group['records'],sorted(group['batches']),repeats=100))
    optima = {}
    for name in original:
        options = []
        for result in finals:
            for row in result['combined'][name].values():
                options.append(dict(row,engine_record=result['engine_records'][name],timing_source=result['label']))
        optima[name] = {which:min(options,key=lambda row:objective(row,which)) for which in OBJECTIVES}
    ratios = {which:objective(optima['I1_TRT'][which],which)/objective(optima['F16_TRT'][which],which) for which in OBJECTIVES}
    report = {'status':'passed_bounded_batch_tuning','created_at_utc':base.now(),
        'protocol':artifact(PROTOCOL),'tested_profiles':[r['label'] for r in results],
        'sweeps':[artifact(DEST/f'batch-sweep-{r["label"]}.json') for r in results+finals],
        'separate_engine_checks':[artifact(p) for p in parity_paths],'optima':optima,'I1_over_F16':ratios,
        'best_complete_batch_latency':'resident_latency and host_latency; lower is faster',
        'best_amortized_latency':'resident_throughput and host_throughput; ms/batch divided by B, not response latency',
        'search_strength_or_MCTS_measured':False,
        'limitations':'Optima within tested batch/profile candidates and this laptop state; no universal global optimum. Larger batches wait for work and do not imply more effective MCTS nodes/s or stronger one-second search. Broad engines are separate artifacts with their own tactic/numerical evidence; original baseline engine preserved.'}
    save(DEST/'batch-tuning.json',report)
    record_path=PROJECT/'environment/week1-v2-int8-pilot.json'; pilot=read(record_path)
    pilot.update(status='passed_A_side',batch_tuning=artifact(DEST/'batch-tuning.json'))
    save(record_path,pilot)
    frozen()
    checkpoint('W1-A15','DONE','environment/week1-v2-int8-pilot.json','Naive INT8 calibration, actual 160-target INT8 execution, validation, reload, wrapper and broad/refined FP16-INT8 batch tuning verified. Next: calibration activation statistics and targeted port check.')
    print('BATCH TUNING COMPLETE',json.dumps({name:{which:{'batch':row['batch'],'value_ms':objective(row,which),'engine':row['timing_source']} for which,row in values.items()} for name,values in optima.items()}),flush=True)
    print('I1 / F16 ratios',ratios,flush=True)


if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args(); run()
