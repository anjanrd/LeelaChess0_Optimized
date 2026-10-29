"""Resume resized Study C once, verify at 55 s, then run queued hw serially."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'reports/c3-part1'
old = ROOT / 'reports/c3_part1_run.py'
# Reuse only definitions/setup, not its original main/one-use launch sequence.
tree = ast.parse(old.read_text(encoding='utf-8'))
assert isinstance(tree.body[-1], ast.Try)
tree.body.pop()
ns = {'__file__': str(old), '__name__': 'c3_reused_helpers'}
exec(compile(tree, str(old), 'exec'), ns)
record, append, state = (ns[n] for n in ('record', 'append', 'state'))
baseline = json.loads((BASE / 'resize-baseline.json').read_text(encoding='utf-8'))
prior = json.loads((BASE / 'state.json').read_text(encoding='utf-8'))
ns['completed'].extend(prior.get('completed', []))

def snapshot_rows(path):
    data = path.read_bytes() if path.exists() else b''
    lines = data.splitlines()
    rows = []
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            # Concurrent append may expose an unfinished active final line;
            # ignore it in this read-only check, never modify a running result.
            if index != len(lines) - 1 or data.endswith(b'\n'):
                raise
    return data, rows

def verify_resume(start, code):
    ids = set(baseline['selected_ids'])
    audit = {'elapsed_seconds': round(time.monotonic() - start, 3), 'process_exit': code, 'models': {}}
    summaries = []
    for name, before in baseline['files'].items():
        path = Path(before['path'])
        data, rows = snapshot_rows(path)
        assert hashlib.sha256(data[:before['size']]).hexdigest() == before['sha256'], f'{name}: prior bytes changed'
        keys = {(r['id'], r['movetime']) for r in rows}
        assert len(rows) == len(keys), f'{name}: duplicate result keys'
        previous = {tuple(k) for k in before['keys']}
        assert previous <= keys
        new = keys - previous
        assert all(i in ids for i, t in new), f'{name}: new positions outside resized selection'
        info = {'prior_prefix_retained': True, 'duplicate_keys': 0, 'new_keys': len(new), 'times': {}}
        for t in (200, 800):
            count = sum(i in ids and mt == t for i, mt in keys)
            old_count = baseline['models'][name][str(t)]['selected_existing']
            info['times'][str(t)] = dict(before=old_count, now=count, remaining=2437 - count)
            summaries.append(f'{name} {t}ms: already done before resume={old_count}/2437; at check={count}/2437; remaining={2437-count}')
        audit['models'][name] = info
    new_log = (ROOT / 'reports/logs/c3_b_studyc.log').read_bytes()[baseline['log_size']:].decode('utf-8', errors='replace')
    assert 'fp16: 2437 positions' in new_log, 'Resumed command did not report target 2437'
    remaining = baseline['models']['fp16']['800']['remaining']
    assert f'/{remaining} ' in new_log or code == 0, 'No remaining-work progress denominator in resumed output'
    assert audit['models']['fp16']['new_keys'] > 0 or code == 0, 'No new progress seen at first-minute check'
    assert all(mt == 800 for i, mt in ({(r['id'], r['movetime']) for r in snapshot_rows(Path(baseline['files']['fp16']['path']))[1]} - {tuple(k) for k in baseline['files']['fp16']['keys']}))
    (BASE / 'resize-one-minute.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    record('First-minute resume verification PASS; original byte prefixes retained, no duplicated keys, new rows restricted to the Studies A/B IDs; completed fp16 200ms skipped.\n' + '\n'.join(summaries) + '\nEvidence reports/c3-part1/resize-one-minute.json\nStartup/resume key output:\n' + '\n'.join(new_log.splitlines()[-8:]))
    append(ROOT / 'STATUS.md', '| Study C first-minute resume check | done | Prior bytes/keys retained, no duplicates; target 2437 matches Studies A/B; reports/c3-part1/resize-one-minute.json |')

def main():
    with (BASE / 'resize-launch.json').open('x', encoding='utf-8') as f:
        json.dump({'pid': __import__('os').getpid(), 'time': ns['stamp']()}, f)
    ns['gpu_check']('resized b_studyc', cool=True)
    argv = baseline['command']
    exact = subprocess.list2cmdline(argv)
    log = ROOT / 'reports/logs/c3_b_studyc.log'
    record('User-authorized Study C resume after manual stop; same exact command: ' + exact + '; log appended=' + str(log) + '; no automatic retry; hw remains queued. Backup and pre-existing counts: reports/c3-part1/resize-baseline.json')
    append(ROOT / 'STATUS.md', '| Study C resize | running | User continuation supersedes prior stop-helper BLOCKED; studyc.limit=2437 in reports/c3-part1/config.studyc.json; resume command: ' + exact + ' |')
    start = time.monotonic()
    with log.open('a', encoding='utf-8') as output:
        output.write('\n[' + ns['stamp']() + '] $ ' + exact + '\n')
        output.flush()
        p = subprocess.Popen(argv, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, env=ns['ENV'], creationflags=subprocess.CREATE_NO_WINDOW)
        state('b_studyc resized resume', child_pid=p.pid, command=exact, log=str(log), output='results/studyc; reports/c3_studyc')
        try:
            code = p.wait(timeout=55)
        except subprocess.TimeoutExpired:
            code = None
        if code not in (None, 0):
            raise RuntimeError(f'Study C exit={code}: ' + ns['tail'](log))
        verify_resume(start, code)
        code = p.wait()
    record(f'Study C resized command finished; exit={code}; command={exact}; output=results/studyc; reports/c3_studyc; key lines:\n' + ns['tail'](log))
    if code:
        raise RuntimeError(f'Study C exit={code}: ' + ns['tail'](log))
    # Verify every resized target exists without removing older outside-target rows.
    ids = set(baseline['selected_ids'])
    for name, info in baseline['files'].items():
        rows = snapshot_rows(Path(info['path']))[1]
        for t in (200, 800):
            count = len({r['id'] for r in rows if r['movetime'] == t} & ids)
            assert count == 2437, (name, t, count)
            record(f'Study C completion count {name} {t}ms: {count}/2437 selected positions; prior extra rows preserved')
    ns['completed'].append('b_studyc')
    append(ROOT / 'STATUS.md', '| C3 b_studyc resized | done | exit 0; fp16/s4, 200/800ms, all 2437 selected positions each; results/studyc; reports/logs/c3_b_studyc.log |')
    state('b_studyc resized finished')
    ns['gpu_check']('c_hw', cool=True)
    ns['run_stage']('c_hw', [sys.executable, '-u', str(ROOT / 'reports/c3_hw_guard.py'), '--config', str(BASE / 'config.hw.json')], 'reports/c3_hw')
    append(ROOT / 'STATUS.md', '| CHECKPOINT C3-part1: ready for review | done | reports/s1sp_errors.md; reports/c3_swap_provenance.json; results/s0_search; results/hard_lowbudget; results/studyc (2437 selected IDs); reports/c3_hw; reports/logs/c3_*.log; no score or match run |')
    record('CHECKPOINT C3-part1: ready for review; resized Study C and queued hw completed. Stopped. No score or match run. Clock lock was previously denied permission and skipped; no escalation.')
    state('CHECKPOINT C3-part1', 'done')

try:
    main()
except Exception as error:
    message = f'{type(error).__name__}: {error}'
    state('resized resume failure', 'BLOCKED', error=message)
    record('BLOCKED; stopped on first failure; ' + message)
    append(ROOT / 'STATUS.md', '| C3-part1 resumed | BLOCKED | ' + message.replace('\n', ' ').replace('|', '/') + ' |')
    sys.exit(1)
