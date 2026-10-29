"""C2 command orchestration only. Does not modify quantization/scoring code.

Waits for the already-running select --alpha, freezes the mechanical choice,
builds, studies (one nonfatal retry), scores, and writes the final checkpoint.
"""
from __future__ import annotations
import argparse
from collections import deque
from datetime import datetime
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
from zoneinfo import ZoneInfo

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
PY = ROOT.parent / '.venv/Scripts/python.exe'
LOG = ROOT / 'LOG.md'
STATUS = ROOT / 'STATUS.md'
STATE = ROOT / 'reports/C2-controller-state.json'
MODEL_NAMES = ['s1', 's2', 's3', 's4', 's4aa', 's0', 's1sp', 'swap_pol8', 'swap_val8']
STUDY_NAMES = ['fp16', 's1', 's2', 's3', 's4', 's4aa', 'swap_pol8', 'swap_val8', 's1sp', 's0']
CURRENT = 'starting'

def now():
    return datetime.now(ZoneInfo('Asia/Kolkata')).isoformat(timespec='seconds')

def write_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)

def emit(message):
    print(f'{now()} {message}', flush=True)

def record(title, body):
    with LOG.open('a', encoding='utf-8') as f:
        f.write(f'\n## {now()} — {title}\n{body}\n')
    emit(title)

def status(key, state, result):
    result = str(result).replace('|', '/').replace('\n', '; ')
    row = f'| {key} | {state} | {result} |'
    lines = STATUS.read_text(encoding='utf-8-sig').splitlines()
    prefix = f'| {key} |'
    found = False
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = row
            found = True
            break
    if not found:
        lines.append(row)
    STATUS.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    emit(row)

def phase(name):
    global CURRENT
    CURRENT = name
    write_json(STATE, {'state': 'running', 'phase': name, 'pid': os.getpid(), 'updated': now()})
    emit('PHASE ' + name)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def inside(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT):
        raise RuntimeError(f'Path outside workspace: {path}')
    return path

def run(args, output, cpu=True, check=True, stage_total=None):
    args = [str(a) for a in args]
    output = inside(output)
    env = os.environ.copy()
    env['TEMP'] = env['TMP'] = str(ROOT / 'reports/tmp')
    env['PYTHONUNBUFFERED'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    if cpu:
        env['CUDA_VISIBLE_DEVICES'] = '-1'
    else:
        env.pop('CUDA_VISIBLE_DEVICES', None)
    command = subprocess.list2cmdline(args)
    record('command start', f'Phase: {CURRENT}\nCwd: {ROOT}\nExact command: `{command}`\n'
           f'CPU-only environment: {cpu}; TEMP/TMP={env["TEMP"]}\nOutput: {output}\nExit code: running.')
    tail = deque(maxlen=80)
    switched = False
    started = time.monotonic()
    with output.open('a', encoding='utf-8', buffering=1) as f:
        f.write(f'\n# {now()} $ {command}\n')
        p = subprocess.Popen(args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', bufsize=1)
        for line in p.stdout:
            f.write(line)
            tail.append(line.rstrip())
            emit(line.rstrip())
            if stage_total:
                m = re.search(r'stage (\d+):.*\(([\d.]+)s\)', line)
                if m:
                    stage, elapsed = int(m[1]), float(m[2])
                    projected = elapsed / stage * stage_total
                    decision = (f'SparseGPT timing: elapsed={elapsed:.1f}s, completed stages={stage}, '
                                f'total stages={stage_total}; {elapsed:.1f}/{stage}*{stage_total}'
                                f'={projected:.1f}s, threshold=5400s (90 minutes).')
                    record('SparseGPT stage projection', decision)
                    if projected > 5400 and p.poll() is None:
                        # This is the user's expressly authorized one-model restart.
                        # Kill the owned process tree, including Windows venv's redirector child.
                        kill = ['taskkill', '/PID', str(p.pid), '/T', '/F']
                        k = subprocess.run(kill, capture_output=True, text=True)
                        record('authorized SparseGPT switch', f'Exact command: `{subprocess.list2cmdline(kill)}`\n'
                               f'Exit code: {k.returncode}\n~~~\n{k.stdout}\n{k.stderr}\n~~~\n'
                               'Reason: stage projection exceeds 90 minutes. Restart only SparseGPT with --one-shot.')
                        if k.returncode:
                            raise RuntimeError('Failed to stop the owned sequential SparseGPT process tree')
                        switched = True
                        break
        p.wait()
    rc = p.returncode
    record('command completion', f'Exact command: `{command}`\nExit code: {rc}\n'
           f'Elapsed command seconds: {time.monotonic()-started:.3f}\n'
           f'Authorized timing switch: {switched}\nOutput file: {output}\nKey output:\n~~~\n' + '\n'.join(tail) + '\n~~~')
    write_json(output.with_suffix(output.suffix + '.result.json'), {'command': args, 'exit_code': rc, 'timing_switch': switched, 'finished': now()})
    if rc and check and not switched:
        raise RuntimeError(f'Command failed ({rc}): {command}; see {output}')
    return rc, switched, '\n'.join(tail)

def read_table(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        cells = line.split()
        if cells and cells[0].endswith('.onnx'):
            if len(cells) != 5:
                raise RuntimeError(f'Unexpected selection report row: {line}')
            rows.append(dict(name=cells[0], kl=float(cells[1]), top1=float(cells[2]), dv=float(cells[3]), tb_acc=float(cells[4])))
    if not rows:
        raise RuntimeError(f'No candidate rows: {path}')
    return rows

def valid_scales(path):
    import numpy as np
    import onnx
    from onnx import numpy_helper
    m = onnx.load(str(path))
    init = {a.name: a for a in m.graph.initializer}
    scales = {n.input[1] for n in m.graph.node if n.op_type in ('QuantizeLinear', 'DequantizeLinear')}
    valid = bool(scales) and all(np.isfinite(a := numpy_helper.to_array(init[s])).all() and (a > 0).all() for s in scales)
    side = json.loads(Path(path).with_suffix('.json').read_text())
    clips = side.get('activation_clip', {})
    valid = valid and all(math.isfinite(v['ratio']) and 0 < v['ratio'] <= 1 and
                          math.isfinite(v['clipped_frac']) and 0 <= v['clipped_frac'] <= 1 for v in clips.values())
    result = {'file': str(path), 'valid': bool(valid), 'scale_tensors': len(scales), 'clip_entries': len(clips)}
    record('scale/clip validation', json.dumps(result))
    return bool(valid)

def freeze_recipe():
    phase('mechanical recipe selection')
    s3 = read_table('reports/select_s3_dev.txt')
    alpha = read_table('reports/select_s4_dev.txt')
    s3_valid = [r for r in s3 if math.isfinite(r['kl']) and math.isfinite(r['top1']) and valid_scales(ROOT/'models/select'/r['name'])]
    if not s3_valid:
        raise RuntimeError('No finite s3 candidate')
    chosen = min(s3_valid, key=lambda r: (r['kl'], -r['top1']))
    mapping = {'s3_p999.onnx': ('percentile', 99.9), 's3_p9999.onnx': ('percentile', 99.99),
               's3_p99999.onnx': ('percentile', 99.999), 's3_entropy.onnx': ('entropy', None)}
    method, percentile = mapping[chosen['name']]
    cfg_path = ROOT/'config.json'
    before = cfg_path.read_text()
    cfg = json.loads(before)
    # The alpha grid must actually have been calibrated on the selected s3 recipe.
    eligible = []
    for r in alpha:
        path = ROOT/'models/select'/r['name']
        finite = math.isfinite(r['kl']) and math.isfinite(r['top1']) and valid_scales(path)
        side = json.loads(path.with_suffix('.json').read_text())
        if side['method'] != method or side['percentile'] != percentile:
            raise RuntimeError(f'Alpha candidate used another s3 recipe: {path}')
        r['alpha'] = float(side['smoothquant'])
        r['qualifies'] = finite and r['top1'] >= chosen['top1']
        if r['qualifies']:
            eligible.append(r)
    best_alpha = min(eligible, key=lambda r: (r['kl'], r['alpha'])) if eligible else None
    cfg['recipe']['s3_method'] = method
    if percentile is not None:
        cfg['recipe']['s3_percentile'] = percentile
    if best_alpha:
        cfg['recipe']['s4_alpha'] = best_alpha['alpha']
    # A KL tie with unsmoothed s3 favors its simpler graph. Otherwise apply
    # the user's alpha eligibility rule, without adding a top-1 improvement test.
    cfg['best'] = 's3' if best_alpha is None or best_alpha['kl'] == chosen['kl'] else 's4'
    if cfg['study']['limit'] != 2437:
        raise RuntimeError('study.limit changed from the authorized 2437')
    untouched_before = {k:v for k,v in json.loads(before).items() if k not in ('recipe','best')}
    untouched_after = {k:v for k,v in cfg.items() if k not in ('recipe','best')}
    if untouched_before != untouched_after:
        raise RuntimeError('Attempt to change configuration outside recipe/best')
    (ROOT/'reports/config.C2-before-alpha-choice.json').write_text(before)
    cfg_path.write_text(json.dumps(cfg, indent=1)+'\n')
    reason = (f's3 {chosen["name"]}: lowest finite dev KL {chosen["kl"]:.2e}, top-1 {chosen["top1"]:.3f}; '
              's3 ties use higher top-1. ')
    if best_alpha:
        reason += (f'Alpha {best_alpha["alpha"]}: lowest eligible dev KL {best_alpha["kl"]:.2e}, '
                   f'top-1 {best_alpha["top1"]:.3f} >= s3 {chosen["top1"]:.3f}. ')
    else:
        reason += 'No finite alpha preserves s3 top-1; best=s3. '
    reason += f'best={cfg["best"]}. KL ties favor unsmoothed s3; equal alpha rows use smaller alpha deterministically.'
    choice = {'s3': chosen, 'alpha': best_alpha, 'alpha_rows': alpha, 'recipe': cfg['recipe'], 'best': cfg['best'], 'reason': reason}
    write_json(ROOT/'reports/C2-recipe-choice.json', choice)
    diff = ''.join(difflib.unified_diff(before.splitlines(True), cfg_path.read_text().splitlines(True), fromfile='config before', tofile='config after'))
    record('C2 mechanical recipe frozen', reason+'\nAll candidate rows:\n'+json.dumps({'s3':s3,'alpha':alpha},indent=2)+'\nConfig diff:\n~~~diff\n'+diff+'\n~~~\nProduced: reports/C2-recipe-choice.json; reports/config.C2-before-alpha-choice.json; config.json.')
    status('3c freeze recipe','done',reason)
    status('CHECKPOINT C2-select','done','CHECKPOINT C2-select: ready for review; user override: continuing through build, study and score')
    return cfg, choice

def backup_s4():
    import shutil
    phase('back up C1 s4')
    dest = inside(ROOT/'reports/c1-s4-backup')
    dest.mkdir(exist_ok=True)
    files = sorted((ROOT/'models').glob('s4.*'))
    required = {'s4.onnx','s4.pb.gz','s4.json'}
    if not required <= {p.name for p in files}:
        raise RuntimeError('C1 s4 files missing before backup')
    manifest = []
    for p in files:
        p = inside(p); out = inside(dest/p.name)
        if out.exists() and sha(out) != sha(p):
            raise RuntimeError(f'Existing backup differs: {out}')
        shutil.copy2(p,out)
        if sha(p) != sha(out):
            raise RuntimeError(f'Backup hash mismatch: {p}')
        manifest.append({'source':str(p),'backup':str(out),'bytes':p.stat().st_size,'sha256':sha(p)})
    record('C1 s4 backup verified before removal','Exact operation: shutil.copy2 for each explicitly listed source/destination, followed by SHA256 comparison.\nExit code: 0\n'+json.dumps(manifest,indent=2))
    for p in files:
        inside(p).unlink()
    write_json(dest/'manifest.json',manifest)
    record('C1 s4 originals removed','Exact operation: Path.unlink for the source paths in the verified manifest above; all are within '+str(ROOT)+'\nExit code: 0\nProduced: reports/c1-s4-backup/manifest.json and backed-up s4.*. Originals removed to force s4 rebuild.')

def sparse_stage_count():
    import onnx
    from quant.sparse_common import targets
    from quant.sparsegpt24 import upstream_targets
    m=onnx.load('models/bt3_fp32.onnx'); tmap=targets(m,None)
    mm={w:ns for w,ns in tmap.items() if ns[0].op_type!='Conv'}
    shared={w for w,ns in mm.items() if len(ns)>1}
    pending=[w for w,ns in mm.items() if len(ns)==1]
    done=(set(tmap)-set(mm))|shared
    stages=int(bool(shared)); up=upstream_targets(m,tmap)
    while pending:
        ready=[w for w in pending if all(up.get(n.input[0],set())<=done for n in mm[w])]
        if not ready: raise RuntimeError('SparseGPT dependency cycle in stage inventory')
        done.update(ready);pending=[w for w in pending if w not in done];stages+=1
    record('SparseGPT dependency stage inventory',f'Exact operation: read-only target/dependency traversal using existing targets/upstream_targets helpers.\nExit code: 0\nPrinted total stages: {stages}; pruning targets: {len(tmap)}.')
    return stages

def build_all():
    phase('build main variants')
    status('4 build','running','CPU only; s1,s2,s3,s4,s4aa,s0; SparseGPT and swaps follow; reports/logs/C2-build-main.log')
    run([PY,'-u','ladder.py','build','--only','s1,s2,s3,s4,s4aa,s0'],ROOT/'reports/logs/C2-build-main.log')
    phase('SparseGPT sequential with timing gate')
    stages=sparse_stage_count()
    cmd=[PY,'-u','quant/sparsegpt24.py','--onnx','models/bt3_fp32.onnx','--calib','data/calib.npz','--out','models/s1sp_fp32.onnx']
    rc,switched,_=run(cmd,ROOT/'reports/logs/C2-sparsegpt-sequential.log',stage_total=stages)
    if switched:
        phase('SparseGPT one-shot authorized by stage timing')
        for p in [ROOT/'models/s1sp_fp32.onnx',ROOT/'models/s1sp_fp32.json']:
            if p.exists():
                raise RuntimeError(f'Unexpected partial SparseGPT output before restart: {p}')
        run(cmd+['--one-shot'],ROOT/'reports/logs/C2-sparsegpt-one-shot.log')
    phase('build SparseGPT quantization and swaps')
    run([PY,'-u','ladder.py','build','--only','s1sp,swap_pol8,swap_val8'],ROOT/'reports/logs/C2-build-extras.log')

def expected_recipe(cfg,name):
    from ladder import recipe_flags
    flags=recipe_flags(cfg,name)
    get=lambda k:flags[flags.index(k)+1] if k in flags else None
    method=get('--method')
    return {'granularity':get('--granularity'),'method':method,
            'percentile':float(get('--percentile')) if method=='percentile' else None,
            'smoothquant':float(get('--smoothquant')) if get('--smoothquant') is not None else None,
            'act_act_matmul':'--act-act-matmul' in flags}

def verify_build(cfg):
    import onnx
    phase('validate all built artifacts and recipes')
    best=cfg['best'];best_side=json.loads((ROOT/f'models/{best}.json').read_text())
    # stitch_swap.py intentionally emits no JSON. Add truthful provenance
    # sidecars as output metadata; never alter its graph or implementation.
    for name in ['swap_pol8','swap_val8']:
        pol,val=(best,'fp16') if name=='swap_pol8' else ('fp16',best)
        pol_path=ROOT/('models/bt3_fp32.onnx' if pol=='fp16' else f'models/{pol}.onnx')
        val_path=ROOT/('models/bt3_fp32.onnx' if val=='fp16' else f'models/{val}.onnx')
        side={'kind':'policy/value swap','recipe_applies_to':'quantized component; other component is FP32 ONNX for FP16 engine fallback',
              'method':best_side['method'],'percentile':best_side['percentile'],'smoothquant':best_side['smoothquant'],
              'policy':{'model':pol,'onnx':str(pol_path),'sha256':sha(pol_path)},
              'value_mlh':{'model':val,'onnx':str(val_path),'sha256':sha(val_path)},
              'generated_by':'reports/c2_continue.py provenance only; stitch_swap.py emits no native JSON'}
        write_json(ROOT/f'models/{name}.json',side)
        m=onnx.load(str(ROOT/f'models/{name}.onnx'))
        p_q=sum(n.op_type=='QuantizeLinear' and n.name.startswith('P') for n in m.graph.node)
        v_q=sum(n.op_type=='QuantizeLinear' and n.name.startswith('V') for n in m.graph.node)
        if not ((p_q>0 and v_q==0) if name=='swap_pol8' else (v_q>0 and p_q==0)):
            raise RuntimeError(f'Swap quantized component mismatch: {name}: P={p_q}, V={v_q}')
        record('swap provenance sidecar',json.dumps(side,indent=2)+f'\nP Q nodes={p_q}; V Q nodes={v_q}\nProduced: models/{name}.json; no graph/code changes.')
    manifest=[]
    for name in MODEL_NAMES:
        paths=[ROOT/f'models/{name}{suffix}' for suffix in ['.onnx','.pb.gz','.json']]
        for p in paths:
            if not p.is_file() or p.stat().st_size==0: raise RuntimeError(f'Missing/empty model file: {p}')
        side=json.loads(paths[2].read_text())
        if not name.startswith('swap_'):
            expected=expected_recipe(cfg,name)
            actual={k:side.get(k) for k in expected}
            if actual!=expected: raise RuntimeError(f'Recipe mismatch {name}: expected {expected}; actual {actual}')
            if not valid_scales(paths[0]): raise RuntimeError(f'Invalid model scales: {name}')
            record('model recipe verified',f'{name}: '+json.dumps(actual)+f'\nExpected from ladder.recipe_flags(config, {name!r}): '+json.dumps(expected))
        manifest.append({'model':name,'recipe':{k:side.get(k) for k in ['method','percentile','smoothquant']},'files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths]})
    for p in [ROOT/'models/fp16.pb.gz',ROOT/'models/bt3_fp32.onnx']:
        if not p.is_file() or p.stat().st_size==0: raise RuntimeError(f'Missing FP16 reference: {p}')
    write_json(ROOT/'reports/C2-build-manifest.json',manifest)
    record('all build artifacts verified',json.dumps(manifest,indent=2)+'\nBaseline exception is intentional: s1/s2 are fixed minmax ablations; selected recipes apply according to ladder.recipe_flags. Swaps mix the best recipe with the FP32 source.\nProduced: reports/C2-build-manifest.json.')
    status('4 build','done','All nine ONNX/pb.gz/JSON sets exist; recipes verified against ladder/config; reports/C2-build-manifest.json; continuing to study')

def gpu_idle():
    phase('GPU idle pre-flight')
    while True:
        r=subprocess.run(['nvidia-smi'],capture_output=True,text=True)
        record('GPU pre-flight',f'Exact command: nvidia-smi\nExit code: {r.returncode}\n~~~\n{r.stdout}{r.stderr}\n~~~')
        if r.returncode: raise RuntimeError('nvidia-smi failed')
        q=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True)
        record('GPU utilization check',f'Exact command: nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits\nExit code: {q.returncode}\n~~~\n{q.stdout}{q.stderr}\n~~~')
        if q.returncode: raise RuntimeError('nvidia-smi utilization query failed')
        vals=[[int(v.strip()) for v in line.split(',')] for line in q.stdout.splitlines() if line.strip()]
        if vals and all(u==0 and mem==0 for u,mem in vals) and 'No running processes found' in r.stdout:
            return
        emit('GPU busy; waiting without launching a GPU job.')
        time.sleep(30)

def study():
    gpu_idle()
    phase('study')
    status('4 study','running','Background: python ladder.py study; canonical reports/logs/study.log, console C2-study-console.log; one nonfatal retry authorized')
    cmd=[PY,'-u','ladder.py','study']
    record('study logging and resume','Exact command: '+subprocess.list2cmdline([str(x) for x in cmd])+'\nladder.py itself appends commands/output to reports/logs/study.log. Controller separately captures console to reports/logs/C2-study-console.log to avoid duplicate writes to the canonical log.\nResume from leela-int8: ..\\.venv\\Scripts\\python.exe -u ladder.py study')
    rc,_,tail=run(cmd,ROOT/'reports/logs/C2-study-console.log',cpu=False,check=False)
    if rc:
        fatal=re.search(r'FileNotFoundError|No such file|not found \(copy|input format .* BT3 uses|INVALID_GRAPH|INVALID_PROTOBUF|CUDA_ERROR_NO_DEVICE|CUDA failure.*out of memory|out of memory|Unable to find.*weights',tail,re.I)
        if fatal: raise RuntimeError(f'Obviously fatal study error ({rc}): {tail[-5000:]}')
        record('one authorized study retry',f'First study exit code: {rc}; no obvious structural/fatal error in the captured tail. Resume once with the same command.\nError evidence:\n~~~\n{tail}\n~~~')
        gpu_idle();phase('study retry 1')
        rc,_,tail=run(cmd,ROOT/'reports/logs/C2-study-console.log',cpu=False,check=False)
        if rc: raise RuntimeError(f'Study failed on authorized retry ({rc}): {tail[-5000:]}')
    status('4 study','done','Exit 0; resumable results complete; canonical reports/logs/study.log; resume: ..\\.venv\\Scripts\\python.exe -u ladder.py study')

def finish(cfg,choice,source_hashes):
    phase('score')
    status('4 score','running','python ladder.py score; reports/logs/C2-score.log')
    run([PY,'-u','ladder.py','score'],ROOT/'reports/logs/C2-score.log')
    for p,h in source_hashes.items():
        if sha(p)!=h: raise RuntimeError(f'Quantization/evaluation/tablebase source changed: {p}')
    scores=json.loads((ROOT/'reports/scores_test.json').read_text())
    md=(ROOT/'reports/scores_test.md').read_text()
    warnings=[]
    for log in [ROOT/'reports/logs/C2-select.log', ROOT/'reports/logs/C2-select-alpha.log',
                ROOT/'reports/logs/C2-build-main.log', ROOT/'reports/logs/C2-build-extras.log',
                ROOT/'reports/logs/C2-sparsegpt-sequential.log', ROOT/'reports/logs/C2-sparsegpt-one-shot.log']:
        if log.exists():
            for line in log.read_text(encoding='utf-8', errors='replace').splitlines():
                if re.search(r'RuntimeWarning|WARNING:root:Please consider|warning:.*calibration rows', line):
                    warnings.append(line.strip())
    a_ns={v['A']['n'] for v in scores['models'].values() if 'A' in v}
    b_ns={v['B']['n'] for v in scores['models'].values() if 'B' in v}
    if len(a_ns)>1 or len(b_ns)>1: warnings.append(f'n mismatch: A={sorted(a_ns)}, B={sorted(b_ns)}')
    for name in STUDY_NAMES:
        p=ROOT/f'results/{name}/meta.json'
        if not p.exists(): raise RuntimeError(f'Missing study metadata: {name}')
        meta=json.loads(p.read_text())
        for w in meta.get('warnings',[]): warnings.append(f'{name}: {w}')
        expected=cfg['study']['limit']
        row=scores['models'].get(name,{})
        if row.get('A',{}).get('n')!=expected: warnings.append(f'{name}: Study A n={row.get("A",{}).get("n")}, requested={expected}')
        if name!='s0' and row.get('B',{}).get('n')!=expected: warnings.append(f'{name}: Study B n={row.get("B",{}).get("n")}, requested={expected}')
        for log in (ROOT/f'results/{name}').glob('*.lc0.log'):
            with log.open(encoding='utf-8',errors='replace') as f:
                for line in f:
                    if 'fp32' in line.lower() and re.search(r'warn|fall.?back|not a valid',line,re.I): warnings.append(f'{name}: {line.strip()}')
    warnings=list(dict.fromkeys(warnings))
    for name in STUDY_NAMES:
        row=scores['models'].get(name,{})
        a=row.get('A',{})
        summary=f'A accuracy={a.get("acc")}, n={a.get("n")}'
        b=row.get('B')
        if b:
            for (budget,v),ne in zip(sorted(b['budgets'].items(),key=lambda z:int(z[0])),b['node_equiv']):
                summary+=f'; B{budget} acc={v["acc"]:.4f} node-equivalent={ne}'
            summary+=f'; B n={b["n"]}'
        else: summary+='; Study A only (runbook S0)'
        record('printed model score',name+': '+summary)
        status('C2 result '+name,'done',summary)
    resume='..\\.venv\\Scripts\\python.exe -u ladder.py study'
    report='# C2-done\n\n'+choice['reason']+f'\n\nRecipe: {json.dumps(cfg["recipe"])}; best={cfg["best"]}; study.limit={cfg["study"]["limit"]}.\n\nWarnings: '+ ('; '.join(warnings) if warnings else 'none (no FP32 warning or n mismatch detected)')+f'\n\nResume study from leela-int8: `{resume}`. Then `..\\.venv\\Scripts\\python.exe -u ladder.py score`.\n\n'+md
    (ROOT/'reports/C2-done.md').write_text(report,encoding='utf-8')
    record('C2 final evidence',report+'\nProduced: reports/C2-done.md, reports/scores_test.md, reports/scores_test.json, reports/hard/; source hashes unchanged. Exit code: 0.')
    status('4 score','done','Exit 0; reports/scores_test.md, scores_test.json and hard/; no scoring code changes')
    status('C2 recipe','done',choice['reason']+f'; recipe={json.dumps(cfg["recipe"])}; best={cfg["best"]}; study.limit={cfg["study"]["limit"]}')
    status('C2 warnings','done','; '.join(warnings) if warnings else 'No FP32 warning or n mismatch detected; entropy selection RuntimeWarning retained in LOG.md, emitted scales finite; all bench/build/study warning evidence retained')
    status('C2 resume command','done',resume+'; then ..\\.venv\\Scripts\\python.exe -u ladder.py score')
    status('CHECKPOINT C2-done','done','CHECKPOINT C2-done: ready for review; study and score completed; recipe, limit and per-model tables in rows above and reports/C2-done.md; stopped')
    write_json(STATE,{'state':'complete','phase':'CHECKPOINT C2-done','pid':os.getpid(),'updated':now(),'report':str(ROOT/'reports/C2-done.md')})
    emit('CHECKPOINT C2-done: ready for review. Stopped; no C3 jobs launched.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plan',action='store_true');args=ap.parse_args()
    if args.plan:
        print('Wait for current select --alpha exit file; mechanical finite selection; back up/remove C1 s4; CPU main build; SparseGPT sequential with 5400s stage projection switch; CPU remaining build; sidecar/file verification; idle GPU; background study with one nonfatal retry; score; C2-done; stop.')
        return
    (ROOT/'reports/tmp').mkdir(exist_ok=True)
    lock=ROOT/'reports/C2-controller-lock.json'
    with lock.open('x',encoding='utf-8') as f: json.dump({'pid':os.getpid(),'started':now()},f)
    if os.name == 'nt':
        import ctypes
        awake=ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        record('process-local awake request',f'Exact API call: SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED), result={awake}. Reversible process/thread lifetime request; no persistent power settings changed.')
    source_hashes={str(p):sha(p) for folder in ['quant','eval','tb'] for p in (ROOT/folder).glob('*.py')}
    write_json(ROOT/'reports/C2-source-hashes.json',source_hashes)
    phase('waiting for already-running select --alpha')
    marker=ROOT/'reports/logs/C2-select-alpha.exitcode'
    record('C2 continuation started',f'Exact command: {PY} -u reports/c2_continue.py\nPID: {os.getpid()}\nAwaiting existing command completion marker: {marker}\nNo second selection job is started. Source hash manifest: reports/C2-source-hashes.json. Controller source: reports/c2_continue.py (orchestration only).')
    while not marker.exists(): time.sleep(20)
    time.sleep(2)
    rc=int(marker.read_text().strip())
    if rc: raise RuntimeError(f'select --alpha failed ({rc}); see reports/logs/C2-select-alpha.log')
    cfg,choice=freeze_recipe()
    backup_s4();build_all();verify_build(cfg);study();finish(cfg,choice,source_hashes)

if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        detail=traceback.format_exc()
        record('BLOCKED — C2 continuation',f'Phase: {CURRENT}\nError: {exc}\n~~~\n{detail}\n~~~\nNo later pipeline command launched.')
        status('C2 continuation','BLOCKED',f'{CURRENT}: {exc}; see LOG.md and reports/logs/C2-controller.stdout.log')
        write_json(STATE,{'state':'BLOCKED','phase':CURRENT,'error':str(exc),'pid':os.getpid(),'updated':now()})
        sys.exit(1)
