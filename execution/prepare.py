"""CPU-only Run 1 preparation. No native engine/profiler is launched here."""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ladder import load_config
from execution.support import atomic_json, identity, read_json, scoped_environment


def pe_info(path):
    """Read PE architecture/import names without loading a DLL or CUDA."""
    data=Path(path).read_bytes()
    if data[:2]!=b'MZ':raise ValueError('Not a Windows PE file')
    pos=struct.unpack_from('<I',data,0x3c)[0]
    if data[pos:pos+4]!=b'PE\0\0':raise ValueError('Invalid PE signature')
    machine,sections=struct.unpack_from('<HH',data,pos+4)
    size=struct.unpack_from('<H',data,pos+20)[0];optional=pos+24
    magic=struct.unpack_from('<H',data,optional)[0]
    if magic!=0x20b or machine!=0x8664:raise ValueError('Expected 64-bit Windows executable/DLL')
    table=optional+size
    def offset(rva):
        for i in range(sections):
            s=table+40*i
            virtual_size,address,raw_size,raw_pointer=struct.unpack_from('<IIII',data,s+8)
            if address<=rva<address+max(virtual_size,raw_size):return raw_pointer+rva-address
        raise ValueError('Unmapped PE RVA')
    import_rva=struct.unpack_from('<I',data,optional+112+8)[0]
    names=[]
    if import_rva:
        here=offset(import_rva)
        for i in range(512):
            row=struct.unpack_from('<IIIII',data,here+20*i)
            if not any(row):break
            start=offset(row[3]);end=data.index(b'\0',start)
            names.append(data[start:end].decode('ascii'))
    return {'architecture':'AMD64','imports':names}


def model_args(cfg,name):
    return ["--lc0",cfg['lc0'],"--weights",str(ROOT/'models'/f'{name}.pb.gz'),
            "--backend-opts",cfg['fp16_opts'] if name=='fp16' else cfg['int8_opts']]


def make_manifest(cfg,protocol):
    output=ROOT/'reports/takeover/run2';py=sys.executable
    jobs=[]
    def add(key,kind,args,outputs,profile=False,deps=()):
        jobs.append({'id':key,'kind':kind,'command':list(map(str,args)),
                     'outputs':outputs,'profiling_branch':profile,'depends_on':list(deps)})
    gpu=[py,'-B','-m','execution.gpu_job']
    common=['--session','{session}','--out','{attempt}/work']
    add('trt-probe','probe',gpu+['probe','--trtexec',cfg['trtexec']]+common,['work/result.json'])
    for name in ('fp16','s4'):
        graph=ROOT/'models'/('bt3_fp32.onnx' if name=='fp16' else f'{name}.onnx')
        add('profile-'+name,'profile',gpu+['profile','--onnx',graph,'--trtexec',cfg['trtexec']]+
            ([] if name=='fp16' else ['--int8'])+common,['work/result.json'],True,['trt-probe'])
    for name in ('s0','s1sp'):
        for sparse in (False,True):
            key=f'profile-{name}-'+('sparse' if sparse else 'dense')
            add(key,'profile',gpu+['profile','--onnx',ROOT/'models'/f'{name}.onnx','--trtexec',cfg['trtexec'],
                '--int8','--large-only']+(['--sparsity'] if sparse else [])+common,
                ['work/result.json'],True,['trt-probe'])
    add('measured-ceilings','peaks',gpu+['peaks','--trtexec',cfg['trtexec']]+common,
        ['work/result.json'],True,['trt-probe'])
    for name in protocol['models']:
        add('capture-'+name,'capture',[cfg['nsys'],'profile','--trace=cuda,nvtx','--sample=none',
             '-o','{attempt}/trace']+gpu+['capture']+model_args(cfg,name)+common,
             ['work/result.json','trace.nsys-rep'])
    others=[m for m in protocol['models'] if m not in protocol['headline_models']]
    for repeat in range(protocol['headline_repetitions']):
        order=list(protocol['headline_models'])
        if repeat%2:order.reverse()
        if repeat<protocol['other_repetitions']:
            shift=(2*repeat)%len(others);order+=others[shift:]+others[:shift]
        for name in order:
            add(f'bench-{name}-r{repeat+1}','benchmark',
                [py,'-B','-m','execution.benchmark','--name',name]+model_args(cfg,name)+common+
                ['--positions',protocol['search_positions'],'--movetime',protocol['search_movetime_ms'],
                 '--threads',protocol['search_threads'],'--minibatch',protocol['search_minibatch'],
                 '--batches',protocol['network_batches_per_trial'],
                 '--conditioning-seconds',protocol['minimum_conditioning_wall_seconds']],['work/result.json'])
    a=f"fp16={ROOT/'models/fp16.pb.gz'}:{cfg['fp16_opts']}"
    b=f"s4={ROOT/'models/s4.pb.gz'}:{cfg['int8_opts']}"
    add('match-estimate-2','pilot',[py,'-B','-m','execution.match_runner','--name','fp16_vs_s4_pilot',
        '--lc0',cfg['lc0'],'--a',a,'--b',b,'--syzygy',cfg['syzygy'],'--tc',protocol['match']['time_control'],
        '--pairs',protocol['match']['provisional_pairs'],'--estimate','2','--session','{session}',
        '--out-dir','{attempt}/work'],['work/pilot/estimate.json','work/pilot/contract.json','work/pilot/summary.json'],
        deps=['bench-fp16-r1','bench-s4-r1'])
    paths=set()
    for file in (ROOT/'execution').glob('*.py'):paths.add(file)
    paths.add(ROOT/'execution/protocol.json');paths.add(ROOT/'config.json')
    for folder in ('hw','eval'):
        paths.update((ROOT/folder).glob('*.py'))
    paths.add(ROOT/'common.py');paths.add(Path(sys.executable));paths.add(ROOT/'data/calib.npz')
    for name in protocol['models']:
        paths.add(ROOT/'models'/f'{name}.pb.gz')
        if name!='fp16':
            paths.add(ROOT/'models'/f'{name}.onnx');paths.add(ROOT/'models'/f'{name}.json')
    paths.add(ROOT/'models/bt3_fp32.onnx')
    for key in ('lc0','trtexec','nsys'):paths.add(Path(cfg[key]))
    for directory in (Path(cfg['lc0']).parent,Path(cfg['trtexec']).parent.parent/'lib'):
        for pattern in ('nvinfer*.dll','nvonnxparser*.dll','onnxruntime*.dll','cudart*.dll','cublas*.dll','cudnn*.dll'):
            paths.update(directory.glob(pattern))
    return {'schema_version':1,'output':str(output),'tools':{k:cfg[k] for k in ('lc0','trtexec','nsys')},
            'sources':[identity(p) for p in sorted(paths)],'jobs':jobs,
            'scientific_acceptance':'Run 3 reviews environmental validity and actual precision; job hashes/exit codes alone are not scientific sign-off',
            'estimated_hours':[3,7],'recommended_exclusive_reservation_hours':8,
            'estimate_basis':'28 benchmark trials, 8 lc0 captures, 6 profile builds plus same-engine reloads, 3 ceiling microbenchmarks and a two-game pilot. Compilation time unmeasured; no GPU timing performed in Run 1.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='reports/takeover/run1')
    a=ap.parse_args();out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True)
    if (out/'run2_jobs.json').exists():raise FileExistsError('Freeze already exists; preserve it and choose a new output version')
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if branch!='anjan':raise RuntimeError('Use anjan for this authorized run')
    cfg=load_config(ROOT/'config.json');protocol=read_json(ROOT/'execution/protocol.json')
    for key in ('lc0','trtexec','nsys','syzygy'):
        if not Path(cfg[key]).exists():raise FileNotFoundError(cfg[key])
    env=scoped_environment(cfg)
    if Path(tempfile.gettempdir()).resolve().is_relative_to(ROOT):
        raise RuntimeError('OS TEMP must be outside the project')
    library=Path(cfg['trtexec']).parent.parent/'lib'
    runtime={}
    for p in [Path(cfg['lc0']),Path(cfg['trtexec']),library/'nvinfer_10.dll',
              library/'nvinfer_plugin_10.dll',library/'nvonnxparser_10.dll']:
        runtime[str(p)]={**identity(p),**pe_info(p)}
    # This prints the child's PATH *membership*, never the user's full PATH.
    membership=subprocess.run([sys.executable,'-B','-c',
         "import os,sys;sys.exit(0 if sys.argv[1] in os.environ['PATH'].split(os.pathsep) else 1)",str(library)],
         env=env,cwd=ROOT,capture_output=True,text=True)
    if membership.returncode:raise RuntimeError('Scoped child PATH check failed')
    manifest=make_manifest(cfg,protocol)
    from execution.run_jobs import validate_manifest
    validate_manifest(manifest)
    atomic_json(out/'runtime_preflight.json',{'branch':branch,'tools':runtime,
                'scoped_child_PATH_membership_check_exit_code':membership.returncode,
                'global_PATH_unchanged':True,'GPU_validation':'PENDING exclusive Run 2',
                'DLL_loaded_or_engine_started':False,'disk_free_bytes':shutil.disk_usage(ROOT).free,
                'os_temp_outside_checkout':True,'syzygy_files':len(list(Path(cfg['syzygy']).glob('*.rtbw'))),
                'prior_A5_verified':read_json(ROOT/'analysis/person_a/run1/progress.json')['steps']['A5']['status']=='verified'})
    atomic_json(out/'run2_jobs.json',manifest)
    atomic_json(out/'exclusive_session_template.json',{'root':str(ROOT),'created_unix':0,
                'exclusive_authorized':False,'work_saved':False,'ac_power_confirmed':False,
                'other_work_paused':False,'resource_preflight_passed':False,'runtime':{},
                'note':'Template only. During exclusive Run 2, record actual GPU UUID/driver/power scheme, inspect activity, save observations and confirm these fields. Never use this template as proof of quiet conditions.'})
    print(json.dumps({'status':'prepared_CPU_only','jobs':len(manifest['jobs']),
                       'source_identities':len(manifest['sources']),'scoped_PATH_check':'passed',
                       'exclusive_run2_estimated_hours':manifest['estimated_hours'],'GPU_workloads':0},indent=2))


if __name__=='__main__':main()
