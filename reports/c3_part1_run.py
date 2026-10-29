"""Serial background C3-part1 controller. No score or match; no automatic retry."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
BASE = REPORTS / 'c3-part1'
LOGS = REPORTS / 'logs'
STATE = BASE / 'state.json'
PY = sys.executable
ENV = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
TMP = BASE / 'tmp'
TMP.mkdir(exist_ok=True)
ENV.update(TEMP=str(TMP), TMP=str(TMP), TMPDIR=str(TMP))
os.chdir(ROOT)

def stamp():
    return time.strftime('%Y-%m-%d %H:%M:%S %z')

def append(path, text):
    # Explicit UTF-8 PowerShell append; never read or rewrite old LOG/STATUS.
    command = '$text=[Console]::In.ReadToEnd(); Add-Content -LiteralPath ' + "'" + str(path).replace("'", "''") + "'" + ' -Value $text -Encoding utf8'
    p = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command], input=text, encoding='utf-8', errors='replace', capture_output=True, env=ENV)
    if p.returncode:
        raise RuntimeError('UTF-8 append failed: ' + p.stderr)

def record(text):
    text = f'[{stamp()}] {text}'
    print(text, flush=True)
    append(ROOT / 'LOG.md', '\n' + text)

completed = []
def state(phase, status='running', **extra):
    data = dict(time=stamp(), controller_pid=os.getpid(), phase=phase, status=status, completed=completed, **extra)
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    temp.replace(STATE)

def gpu_check(phase, cool=False):
    while True:
        full = subprocess.run(['nvidia-smi'], capture_output=True, text=True, encoding='utf-8', errors='replace', env=ENV)
        query_cmd = ['nvidia-smi', '--query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used', '--format=csv,noheader,nounits']
        q = subprocess.run(query_cmd, capture_output=True, text=True, env=ENV)
        proc_cmd = ['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader']
        procs = subprocess.run(proc_cmd, capture_output=True, text=True, env=ENV)
        record(f'{phase} GPU preflight: nvidia-smi exit={full.returncode}; {subprocess.list2cmdline(query_cmd)} exit={q.returncode}; {subprocess.list2cmdline(proc_cmd)} exit={procs.returncode}\n{full.stdout}{full.stderr}\ntemperature C, SM clock MHz, utilization %, memory MiB: {q.stdout.strip()}\ncompute processes: {procs.stdout.strip() or "none"}')
        if full.returncode or q.returncode or procs.returncode:
            raise RuntimeError('nvidia-smi preflight failed')
        temperature, clock, utilization, memory = [int(x.strip()) for x in q.stdout.strip().splitlines()[0].split(',')]
        idle = utilization == 0 and not procs.stdout.strip()
        if idle and (not cool or temperature < 60):
            return
        state(phase + ' waiting for idle/cool GPU', temperature=temperature, sm_clock=clock, utilization=utilization)
        time.sleep(30)

def tail(path, count=18):
    return '\n'.join(path.read_bytes().decode('utf-8', errors='replace').splitlines()[-count:])

def run_stage(name, argv, result):
    path = LOGS / f'c3_{name}.log'
    exact = subprocess.list2cmdline(argv)
    record(f'Launching {name} in background controller, exact command: {exact}; cwd={ROOT}; output={path}; result={result}; resume command={exact}; no automatic resume')
    append(ROOT / 'STATUS.md', f'| C3 {name} | running | {exact}; logs reports/logs/c3_{name}.log; output {result} |')
    with path.open('a', encoding='utf-8') as f:
        f.write(f'\n[{stamp()}] $ {exact}\n')
        f.flush()
        p = subprocess.Popen(argv, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, env=ENV, creationflags=subprocess.CREATE_NO_WINDOW)
        state(name, child_pid=p.pid, command=exact, log=str(path), output=result)
        code = p.wait()
    lines = tail(path)
    record(f'Finished {name}; exact command: {exact}; exit={code}; output={path}; result={result}; key output:\n{lines}')
    if code:
        raise RuntimeError(f'{name} exit {code}: {lines}')
    completed.append(name)
    append(ROOT / 'STATUS.md', f'| C3 {name} | done | exit 0; output {result}; log reports/logs/c3_{name}.log |')
    state(name + ' finished')

def main():
    # One-use guard avoids duplicate controllers, preserving prior output.
    with (BASE / 'launch.json').open('x', encoding='utf-8') as f:
        json.dump(dict(pid=os.getpid(), time=stamp()), f)
    cfg = json.loads((ROOT / 'config.json').read_text(encoding='utf-8-sig'))
    gpu_check('a0')
    lines = (LOGS / 'study.log').read_text(encoding='utf-8', errors='replace').splitlines()
    original = next(line[2:].split() for line in reversed(lines) if line.startswith('$ ') and ' --name s0 ' in line)
    a0 = original.copy()
    a0[a0.index('--budgets') + 1] = '100,400'
    a0[a0.index('--out-dir') + 1] = str(ROOT / 'results/s0_search')
    assert original[original.index('--limit') + 1] == '2437'
    run_stage('a0_s0', a0, 'results/s0_search/s0')
    for name in cfg['study']['models'].split(','):
        gpu_check('a_' + name)
        cmd = [PY, '-u', str(ROOT / 'eval/run_study.py'), '--lc0', cfg['lc0'], '--name', name, '--weights', str(ROOT / 'models' / (name + '.pb.gz')), '--backend', cfg['backend'], '--backend-opts', cfg['fp16_opts'] if name == 'fp16' else cfg['int8_opts'], '--tbset', str(ROOT / 'data/tbset.jsonl'), '--split', 'test', '--ids-file', str(REPORTS / 'hard/ids.txt'), '--limit', '0', '--budgets', '10,25,50,100,200', '--threads', str(cfg['study']['threads']), '--minibatch', str(cfg['study']['minibatch']), '--out-dir', str(ROOT / 'results/hard_lowbudget')]
        run_stage('a_' + name, cmd, 'results/hard_lowbudget/' + name)
    gpu_check('b_studyc', cool=True)
    lock_cmd = ['nvidia-smi', '-lgc', '1500,1500']
    lock = subprocess.run(lock_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', env=ENV)
    record(f'Optional clock lock: {subprocess.list2cmdline(lock_cmd)}; exit={lock.returncode}; {lock.stdout}{lock.stderr}; if unavailable/admin-required, skipped per explicit user instruction; no escalation')
    gpu_check('b_studyc after optional clock-lock attempt', cool=True)
    run_stage('b_studyc', [PY, '-u', str(ROOT / 'ladder.py'), 'studyc', '--config', str(BASE / 'config.studyc.json')], 'results/studyc; reports/c3_studyc')
    gpu_check('c_hw', cool=True)
    run_stage('c_hw', [PY, '-u', str(REPORTS / 'c3_hw_guard.py'), '--config', str(BASE / 'config.hw.json')], 'reports/c3_hw')
    append(ROOT / 'STATUS.md', '| CHECKPOINT C3-part1: ready for review | done | reports/s1sp_errors.md; reports/c3_swap_provenance.json; results/s0_search; results/hard_lowbudget; results/studyc; reports/c3_hw; reports/logs/c3_*.log; no score or match run |')
    record('CHECKPOINT C3-part1: ready for review. All requested stages exited 0; result paths in STATUS.md. Stopped; no score or match run.')
    state('CHECKPOINT C3-part1', 'done')

try:
    main()
except Exception as error:
    message = f'{type(error).__name__}: {error}'
    state('failure', 'BLOCKED', error=message)
    record('BLOCKED; stop on first failure; ' + message)
    append(ROOT / 'STATUS.md', '| C3-part1 | BLOCKED | ' + message.replace('\n', ' ').replace('|', '/') + ' |')
    sys.exit(1)
