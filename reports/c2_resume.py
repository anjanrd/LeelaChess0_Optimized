"""Resume existing C2 results; orchestration and reporting only."""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import c2_continue as c

ROOT = c.ROOT
BASELINE = ROOT / 'reports/C2-resume-baseline.json'
PREPARED = ROOT / 'reports/C2-resume-prepared.json'
CONSOLE = ROOT / 'reports/logs/C2-resume-study-console.log'
RESUME = [str(c.PY), '-u', 'ladder.py', 'study']
ORIGINAL_STATUS = c.status

def ps_write(path, text, append):
    """Explicit PowerShell UTF-8; LOG is append-only, never rewritten."""
    verb = 'Add-Content' if append else 'Set-Content'
    literal = str(path).replace("'", "''")
    code = ("$ErrorActionPreference='Stop';"
            "[Console]::InputEncoding=[Text.UTF8Encoding]::new($false);"
            "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
            "$body=[Console]::In.ReadToEnd();"
            f"{verb} -LiteralPath '{literal}' -Value $body -Encoding utf8")
    p = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', code],
                       input=text.encode('utf-8'), capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if p.returncode:
        raise RuntimeError(f'{verb} UTF-8 write failed: {p.stderr.decode("utf-8", errors="replace")}')

def record(title, body):
    text = f'\n## {c.now()} — {title}\n{body}\n'
    ps_write(c.LOG, text, True)
    c.emit(title + '\n' + body)

def status(key, state, result):
    lines = c.STATUS.read_bytes().decode('utf-8-sig', errors='replace').splitlines()
    def replace(k, s, r):
        row = f'| {k} | {s} | {str(r).replace(chr(124), "/").replace(chr(10), "; ")} |'
        for i, line in enumerate(lines):
            if line.startswith(f'| {k} |'):
                lines[i] = row
                break
        else:
            lines.append(row)
    if key == 'CHECKPOINT C2-done' and state == 'done':
        replace('C2 continuation', 'done', 'Study resume and score completed; no work beyond C2-done')
    replace(key, state, result)
    ps_write(c.STATUS, '\n'.join(lines) + '\n', False)
    c.emit(f'| {key} | {state} | {result} |')

c.record = record
c.status = status

def load_json(path):
    return json.loads(Path(path).read_bytes().decode('utf-8-sig'))

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def selected_ids(cfg):
    from argparse import Namespace
    from eval.run_study import positions
    a = Namespace(tbset=str(ROOT/'data/tbset.jsonl'), split=cfg['study']['split'],
                  limit=cfg['study']['limit'], classes=None, ids=None, shard=None)
    return {r['id'] for r in positions(a)}

def snapshot(cfg, concurrent=False):
    ids = selected_ids(cfg)
    budgets = [int(b) for b in cfg['study']['budgets'].split(',') if int(b) > 0]
    counts = {}
    for name in c.STUDY_NAMES:
        a = set(); bs = {b:set() for b in budgets}; duplicates = 0; seen = set()
        total = {}
        for kind in ['a','b']:
            p = ROOT/f'results/{name}/study_{kind}.jsonl'
            data = p.read_bytes().splitlines() if p.exists() else []
            total[kind] = 0
            for n, raw in enumerate(data):
                if not raw.strip(): continue
                try:
                    r = json.loads(raw)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    if concurrent and n == len(data)-1: continue
                    raise
                total[kind] += 1
                if r['id'] not in ids: continue
                key = (kind, r['id'], r.get('budget'))
                duplicates += key in seen
                seen.add(key)
                if kind == 'a': a.add(r['id'])
                elif r['budget'] in bs: bs[r['budget']].add(r['id'])
        complete = set.intersection(*bs.values()) if bs else set()
        counts[name] = {'A':len(a), 'B_all_budgets':len(complete),
                        'B_by_budget':{str(b):len(s) for b,s in bs.items()},
                        'duplicate_selected_keys':duplicates,'total_rows_including_other_splits':total,
                        'B_required':name!='s0'}
    return counts

def count_table(counts):
    out=['| model | selected Study A done | selected Study B complete at all budgets | B done by budget |',
         '|---|---|---|---|']
    for name,r in counts.items():
        b = str(r['B_all_budgets']) if r['B_required'] else 'not required (S0 raw only)'
        out.append(f'| {name} | {r["A"]} | {b} | {json.dumps(r["B_by_budget"])} |')
    return '\n'.join(out)

def prepare():
    cfg = load_json(ROOT/'config.json')
    folder = ROOT/'reports/study-backup'/c.now().replace(':','').replace('+','_')
    folder.mkdir(parents=True, exist_ok=False)
    manifest=[]; prefixes=[]
    files=sorted((ROOT/'results').rglob('study*.jsonl'))
    if not files: raise RuntimeError('No study JSONL files found to back up')
    # Back up every file, and verify every backup, before editing any tail.
    for path in files:
        raw=path.read_bytes(); dest=folder/path.relative_to(ROOT/'results')
        dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,dest)
        if dest.read_bytes()!=raw: raise RuntimeError(f'Backup byte mismatch: {path}')
        manifest.append({'file':str(path),'backup':str(dest),'before_bytes':len(raw),
                         'backup_sha256':digest(raw),'tail_action':'not checked'})
    record('study JSONL backups verified', 'Exact operation: shutil.copy2 for all results/**/study*.jsonl into '+str(folder)+
           '; byte comparison before any edit. Exit code: 0.\n'+json.dumps(manifest,indent=2))
    for item in manifest:
        path=Path(item['file']); raw=path.read_bytes(); lines=raw.splitlines(keepends=True)
        nonblank=[i for i,b in enumerate(lines) if b.strip()]
        if not nonblank:
            item['tail_action']='empty file: no record to parse; unchanged'
        else:
            i=nonblank[-1]; tail=lines[i]
            try:
                json.loads(tail)
                item['tail_action']='last nonempty line parses as JSON; unchanged'
            except (json.JSONDecodeError,UnicodeDecodeError) as exc:
                text=tail.decode('utf-8',errors='replace').rstrip('\r\n')
                truncated = (isinstance(exc,UnicodeDecodeError) and exc.reason=='unexpected end of data') or (
                    isinstance(exc,json.JSONDecodeError) and
                    (exc.pos >= max(0,len(text.rstrip())-1) or exc.msg.startswith('Unterminated string')))
                if not truncated:
                    raise RuntimeError(f'Malformed last line is not clearly truncated; no edit: {path}: {exc}')
                kept=b''.join(lines[:i]+lines[i+1:])
                path.write_bytes(kept)
                if path.read_bytes()!=kept: raise RuntimeError(f'Tail repair verification failed: {path}')
                item['tail_action']=f'removed only final truncated JSON record, physical line {i+1}: {exc}'
                item['removed_bytes']=len(tail)
                record('truncated final line removed',json.dumps(item,indent=2)+'\nAll other bytes retained; backup preserved.')
        checked=path.read_bytes()
        # A complete JSON record without a newline needs a separator before append.
        if checked and not checked.endswith((b'\n',b'\r')):
            json.loads(checked.splitlines()[-1])
            checked += b'\n'; path.write_bytes(checked)
            item['tail_action']+='; appended one LF separator after valid final record; no record removed'
        for n,line in enumerate(checked.splitlines(),1):
            if line.strip():
                try: json.loads(line)
                except Exception as exc: raise RuntimeError(f'Invalid non-final JSONL record, unchanged: {path}:{n}: {exc}')
        item['after_bytes']=len(checked);item['after_sha256']=digest(checked)
        prefixes.append({'file':str(path),'bytes':len(checked),'sha256':digest(checked)})
    counts=snapshot(cfg)
    c.write_json(folder/'manifest.json',manifest)
    baseline={'prepared':c.now(),'backup_folder':str(folder),'files':prefixes,'counts':counts,
              'study_limit':cfg['study']['limit'],'resume_command':subprocess.list2cmdline(RESUME)}
    c.write_json(BASELINE,baseline);c.write_json(PREPARED,{'ready':True,'baseline':str(BASELINE),'time':c.now()})
    record('study tails checked and resume baseline recorded',json.dumps(manifest,indent=2)+'\n'+count_table(counts)+
           '\nExit code: 0. Produced: '+str(folder/'manifest.json')+', '+str(BASELINE)+', '+str(PREPARED))
    status('C2 study backup/tails','done',f'All study JSONL backed up and tail checked; manifest {folder.relative_to(ROOT)}/manifest.json')
    status('C2 evidence read-back','done','Prior report decoding error resolved by byte/replacement reads outside critical path; LOG history preserved')
    status('C2 resume command','todo',subprocess.list2cmdline(RESUME)+'; cwd '+str(ROOT)+'; one resume authorized')

def verify_minute(cfg,baseline,elapsed):
    checks=[]
    for old in baseline['files']:
        with Path(old['file']).open('rb') as f: raw=f.read(old['bytes'])
        same=len(raw)==old['bytes'] and digest(raw)==old['sha256']
        checks.append({'file':old['file'],'retained_prefix_bytes':old['bytes'],'unchanged':same})
        if not same: raise RuntimeError(f'Previously completed study bytes changed: {old["file"]}')
    after=snapshot(cfg,concurrent=True)
    for name,before in baseline['counts'].items():
        a=after[name]
        if a['A']<before['A'] or any(a['B_by_budget'][b]<n for b,n in before['B_by_budget'].items()):
            raise RuntimeError(f'Completed record counts decreased: {name}')
        if a['duplicate_selected_keys']>before['duplicate_selected_keys']:
            raise RuntimeError(f'New duplicate completed keys: {name}; resume may be restarting')
    text=CONSOLE.read_bytes().decode('utf-8',errors='replace')
    progress=[line for line in text.splitlines() if re.search(r'\[\w+ [AB]\]',line)]
    result={'checked':c.now(),'elapsed_seconds':round(elapsed,3),'retained_file_prefixes':checks,
            'before':baseline['counts'],'after':after,'progress_lines':progress[-6:],
            'verdict':'resuming: prior bytes and completed keys retained; no new duplicate keys'}
    c.write_json(ROOT/'reports/C2-resume-one-minute.json',result)
    record('one-minute resume verification',json.dumps(result,indent=2)+'\nPositions already done BEFORE resume:\n'+
           count_table(baseline['counts'])+'\nPositions done AFTER one minute:\n'+count_table(after)+
           '\nExit code: 0. Produced: reports/C2-resume-one-minute.json. No LOG.md reads used.')
    status('C2 one-minute resume check','done',result['verdict']+'; reports/C2-resume-one-minute.json')

def run_study_once(cfg,baseline):
    env=os.environ.copy();env['PYTHONUTF8']='1';env['PYTHONIOENCODING']='utf-8';env['PYTHONUNBUFFERED']='1'
    env.pop('CUDA_VISIBLE_DEVICES',None)
    env['TEMP']=env['TMP']=str(ROOT/'reports/tmp')
    c.phase('study authorized resume 1 of 1')
    status('4 study','running','Authorized resume 1 of 1; canonical reports/logs/study.log appended by ladder.py; console C2-resume-study-console.log')
    status('C2 continuation','running','Existing built artifacts reused; study resume -> score -> C2-done; no checkpoint pauses')
    status('C2 resume command','running',subprocess.list2cmdline(RESUME)+'; cwd '+str(ROOT)+'; PYTHONUTF8=1; no second automatic resume')
    record('authorized study resume start','Exact command: '+subprocess.list2cmdline(RESUME)+'\nCwd: '+str(ROOT)+
           '\nProcess-local PYTHONUTF8=1 and PYTHONIOENCODING=utf-8, no algorithm/code/config changes. '
           'ladder.py appends its own reports/logs/study.log. Outer console is separately appended to '+str(CONSOLE)+
           '\nExit code: running. One resume only; no automatic second launch.')
    p=subprocess.Popen(RESUME,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                       text=True,encoding='utf-8',errors='replace',bufsize=1)
    q=queue.Queue()
    def reader():
        for line in p.stdout: q.put(line)
        q.put(None)
    threading.Thread(target=reader,daemon=True).start()
    tail=deque(maxlen=70);started=time.monotonic();verified=False;ended=False
    try:
        with CONSOLE.open('a',encoding='utf-8',buffering=1) as f:
            f.write('\n# '+c.now()+' $ '+subprocess.list2cmdline(RESUME)+'\n')
            while not ended:
                try: line=q.get(timeout=0.5)
                except queue.Empty: line=''
                if line is None: ended=True
                elif line:
                    f.write(line);tail.append(line.rstrip());c.emit(line.rstrip())
                elapsed=time.monotonic()-started
                if not verified and elapsed>=60:
                    f.flush();verify_minute(cfg,baseline,elapsed);verified=True
            rc=p.wait()
        if rc: raise RuntimeError(f'Study resume failed ({rc}); no further resume authorized.\n'+'\n'.join(tail))
        if not verified: verify_minute(cfg,baseline,time.monotonic()-started)
        c.write_json(ROOT/'reports/logs/C2-resume-study-result.json',{'exit_code':rc,'finished':c.now(),'command':RESUME})
        record('study resume completion','Exact command: '+subprocess.list2cmdline(RESUME)+'\nExit code: '+str(rc)+
               '\nKey output:\n~~~\n'+'\n'.join(tail)+'\n~~~\nOutputs: reports/logs/study.log; '+str(CONSOLE)+'; results/*/study_*.jsonl and meta.json/meta.jsonl; reports/logs/C2-resume-study-result.json')
        status('4 study','done','Authorized resume completed, exit 0; canonical reports/logs/study.log; score follows')
    except Exception:
        if p.poll() is None:
            k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,text=True)
            record('stop owned failed study resume',f'Exact command: taskkill /PID {p.pid} /T /F\nExit code: {k.returncode}\n{k.stdout}\n{k.stderr}')
        raise

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--run',action='store_true')
    a=ap.parse_args()
    if a.prepare: prepare();return
    if not a.run: raise RuntimeError('Choose --prepare or --run')
    if not load_json(PREPARED)['ready']: raise RuntimeError('Study backups/tails not prepared')
    marker=ROOT/'reports/C2-study-authorized-resume-started.json'
    with marker.open('x',encoding='utf-8') as f: json.dump({'started':c.now(),'pid':os.getpid(),'command':RESUME},f)
    cfg=load_json(ROOT/'config.json');choice=load_json(ROOT/'reports/C2-recipe-choice.json')
    baseline=load_json(BASELINE);source_hashes=load_json(ROOT/'reports/C2-source-hashes.json')
    if os.name=='nt':
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    for old in baseline['files']:
        if c.sha(old['file'])!=old['sha256']: raise RuntimeError('Study file changed after tail checks: '+old['file'])
    c.gpu_idle()
    run_study_once(cfg,baseline)
    c.finish(cfg,choice,source_hashes)

if __name__=='__main__':
    try: main()
    except Exception as exc:
        detail=traceback.format_exc()
        record('BLOCKED — C2 authorized resume',f'Phase: {c.CURRENT}\nError: {exc}\n~~~\n{detail}\n~~~\nNo later pipeline command launched.')
        status('C2 continuation','BLOCKED',str(exc)+'; see reports/logs/C2-resume.stdout.log')
        status('4 study' if 'study' in c.CURRENT else 'C2 resume','BLOCKED',str(exc))
        c.write_json(c.STATE,{'state':'BLOCKED','phase':c.CURRENT,'error':str(exc),'pid':os.getpid(),'updated':c.now()})
        sys.exit(1)
