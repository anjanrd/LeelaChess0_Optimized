"""Read-only CPU analysis and preparation; never launches a subprocess or engine."""
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORTS = ROOT / 'reports'
STAMP = datetime.now().astimezone().isoformat(timespec='seconds')
protected = [ROOT / x for x in ('eval/run_study.py', 'eval/score.py', 'hw/bench.py', 'ladder.py', 'config.json')]
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}

def deny(*args, **kwargs):
    raise RuntimeError('CPU-only audit forbids subprocess/engine launch')

subprocess.Popen = deny
subprocess.run = deny
subprocess.call = deny

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

study = module('cpu_prep_run_study', 'eval/run_study.py')
study.Lc0 = deny
study.make_engine = deny
score = module('cpu_prep_score', 'eval/score.py')
cfg = json.loads((ROOT / 'config.json').read_text(encoding='utf-8-sig'))
args = dict(tbset=str(ROOT / 'data/tbset.jsonl'), split=cfg['study']['split'], classes=None, shard=None)
full = study.positions(SimpleNamespace(**args, ids=None, limit=cfg['study']['limit']))
hard = study.positions(SimpleNamespace(**args, ids=str(REPORTS / 'hard/ids.txt'), limit=0))
full_ids = {r['id'] for r in full}
hard_ids = {int(x) for x in (REPORTS / 'hard/ids.txt').read_text(encoding='utf-8-sig').split()}
assert len(full) == len(full_ids) == 2437
assert len(hard) == len(hard_ids) == 43
assert {r['id'] for r in hard} == hard_ids <= full_ids
truth = {r['id']: set(r['correct']) for r in full}
print(f'DRY RUN: default selection={len(full)}; --ids reports/hard/ids.txt --limit 0 selection={len(hard)}; exact ID match; subprocess and engine creation disabled')

notes = []
def rows(path):
    if not path.exists():
        return []
    lines = path.read_bytes().splitlines()
    out = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except (ValueError, UnicodeDecodeError):
            if i != len(lines) - 1:
                raise
            notes.append(f'{path.relative_to(ROOT)}: incomplete active final line ignored in read-only snapshot; file unchanged')
    return out

names = cfg['study']['models'].split(',') + ['swap_pol8', 'swap_val8', 's1sp', 's0']
# Include any additional result directories with fully completed raw results.
names += sorted(p.name for p in (ROOT / 'results').iterdir() if p.is_dir() and p.name not in names and (p / 'study_a.jsonl').exists())
raw = {n: {r['id']: r for r in rows(ROOT / 'results' / n / 'study_a.jsonl') if r['id'] in full_ids} for n in names}
assert set(raw['fp16']) == full_ids
finished = [n for n in names if set(raw[n]) == full_ids]
pending = {n: len(raw[n]) for n in names if n not in finished}
ref = raw['fp16']

tables = {}
md = ['# Study A paired McNemar against fp16', '', f'Snapshot: {STAMP}. Existing raw results only; no lc0/scorer execution and no results modified.', '',
      'Correct means the recorded raw `best` move belongs to the tablebase record\'s `correct` moves, matching eval/score.py. Each comparison uses the identical selected position IDs. Historical dev rows are excluded. Exact two-sided binomial McNemar p-values use the unchanged scorer\'s `mcnemar_p`; p-values are unadjusted for multiple comparisons.', '',
      'Worse = fp16 correct / model wrong; better = fp16 wrong / model correct. The hard subset is the existing 43 IDs, selected using fp16, so its results are conditional on that selection.', '']
for label, ids in [('Full selected test set', full_ids), ('Existing hard IDs', hard_ids)]:
    md += [f'## {label} (n={len(ids)})', '', '| Model | Correct | Accuracy | fp16 correct | Worse | Better | Exact p |', '|---|---:|---:|---:|---:|---:|---:|']
    entries = []
    for n in finished:
        outcomes = [(ref[i]['best'] in truth[i], raw[n][i]['best'] in truth[i]) for i in sorted(ids)]
        rc = sum(a for a, b in outcomes)
        mc = sum(b for a, b in outcomes)
        worse = sum(a and not b for a, b in outcomes)
        better = sum(b and not a for a, b in outcomes)
        p = score.mcnemar_p(worse, better)
        row = dict(model=n, n=len(ids), correct=mc, ref_correct=rc, worse=worse, better=better, p=p)
        entries.append(row)
        line = f'| {n} | {mc}/{len(ids)} | {mc/len(ids):.6f} | {rc} | {worse} | {better} | {p:.10g} |'
        md.append(line)
        print(label + ' ' + line)
    tables[label] = entries
    md.append('')
md += ['Incomplete raw models omitted: ' + ', '.join(f'{n}={v}/2437' for n, v in pending.items()) + '.', '']
md += notes
(REPORTS / 'study_a_mcnemar.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

log = (REPORTS / 'logs/study.log').read_text(encoding='utf-8', errors='replace')
progress = {}
terminal = {}
context = ''
for line in log.splitlines():
    if line.startswith('$ '):
        context = line
    m = re.search(r'\[([^\]]+) ([AB])\]\s+(\d+)/(\d+)\s+([\d.]+)s/item', line)
    if m and '--split test' in context and '--limit 2437' in context:
        n, stage, count, total, seconds = m.groups()
        key = (n, stage)
        progress[key] = dict(count=int(count), total=int(total), seconds=seconds, line=line.strip())
        if count == total:
            terminal[key] = progress[key]
budgets = [int(x) for x in cfg['study']['budgets'].split(',') if int(x) > 0]
runtime = []
for n in names:
    b = {(r['id'], r['budget']) for r in rows(ROOT / 'results' / n / 'study_b.jsonl') if r['id'] in full_ids and r['budget'] in budgets}
    complete_b = sum(all((i, v) in b for v in budgets) for i in full_ids)
    info = dict(model=n, A=len(raw[n]), B_positions=complete_b, A_final=terminal.get((n, 'A')), B_final=terminal.get((n, 'B')), latest_B=progress.get((n, 'B')))
    runtime.append(info)
    print('RUNTIME', json.dumps(info))

python = ROOT.parent / '.venv/Scripts/python.exe'
def psquote(s):
    return "'" + str(s).replace("'", "''") + "'"

commands = []
for n in cfg['study']['models'].split(','):
    argv = ['-u', 'eval/run_study.py', '--lc0', cfg['lc0'], '--name', n, '--weights', f'models/{n}.pb.gz', '--backend', cfg['backend'], '--backend-opts', cfg['fp16_opts'] if n == 'fp16' else cfg['int8_opts'], '--tbset', 'data/tbset.jsonl', '--split', 'test', '--ids', 'reports/hard/ids.txt', '--limit', '0', '--budgets', '10,25,50,100,200', '--threads', str(cfg['study']['threads']), '--minibatch', str(cfg['study']['minibatch']), '--out-dir', 'results/hard_lowbudget']
    commands.append((f'hard-lowbudget {n}', argv, f'hard_lowbudget_{n}'))
commands += [('studyc', ['-u', 'ladder.py', 'studyc'], 'studyc_prepared'), ('hw', ['-u', 'ladder.py', 'hw'], 'hw_prepared')]
doc = ['# Prepared GPU commands — NOT RUN', '', f'Prepared {STAMP}; run from `{ROOT}`. Existing study remains untouched.', '',
       'Run only after the existing study/score has finished and nvidia-smi confirms GPU idle. Use one script at a time. Each launcher runs hidden in the background, writes stdout/stderr logs, and stops on its first nonzero model exit. Rerunning the same command resumes completed JSONL keys.', '',
       'Hard low-budget study: existing --ids option, 43 positions, six models, five budgets; output is results/hard_lowbudget/<model>/study_b.jsonl. Study A is not requested. Threads=1 and MinibatchSize=256 preserve current config uniformly; nodes can overshoot the requested low budgets by up to a minibatch (README trap 6), so compare recorded actual nodes. This does not promise exact 10/25/50/100/200-node searches.', '',
       'studyc uses current config: fp16 and s4; 200,800 ms; limit=0 (all test positions); default engine Threads; MoveOverheadMs=20. hw uses all configured parts: bench,sweep,trt,roofline. Its bench models are hardcoded in ladder.py as fp16,best,native = fp16,s4,native. s4aa cannot be added through config; no code/config changed.', '']
for label, subset in [('hard_lowbudget', commands[:6]), ('studyc', commands[6:7]), ('hw', commands[7:])]:
    script = ["$ErrorActionPreference = 'Stop'", f'Set-Location -LiteralPath {psquote(ROOT)}', "$env:PYTHONUTF8 = '1'", "$env:PYTHONIOENCODING = 'utf-8'", '# PREPARED ONLY. Confirm GPU idle manually before invoking this script.',
              "$gpu = & nvidia-smi 2>&1", "$gpu | Set-Content -LiteralPath 'reports/logs/" + label + "_gpu_check.log' -Encoding utf8", "if ($LASTEXITCODE -ne 0) { throw 'nvidia-smi failed' }", "if (Get-Process -Name lc0 -ErrorAction SilentlyContinue) { throw 'lc0 is already running; leave it untouched and wait' }"]
    doc += [f'## {label}', '', '```powershell']
    for title, argv, prefix in subset:
        cli = '& ' + psquote(python) + ' ' + ' '.join(psquote(x) for x in argv)
        doc.append(cli)
        # All argv here are space-free; protect each from Start-Process's joining behavior regardless.
        argline = ' '.join('"' + str(x).replace('"', '\\"') + '"' for x in argv)
        script += [f'$exact = {psquote(cli)}', f'$p = Start-Process -FilePath {psquote(python)} -ArgumentList {psquote(argline)} -WorkingDirectory {psquote(ROOT)} -WindowStyle Hidden -RedirectStandardOutput {psquote("reports/logs/" + prefix + ".stdout.log")} -RedirectStandardError {psquote("reports/logs/" + prefix + ".stderr.log")} -PassThru -Wait',
                   "$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss K'", 'Add-Content -LiteralPath LOG.md -Encoding utf8 -Value "[$stamp] Command: $exact; exit=$($p.ExitCode); stdout/stderr: reports/logs/' + prefix + '.*.log"', "if ($p.ExitCode -ne 0) { Add-Content -LiteralPath STATUS.md -Encoding utf8 -Value ('| " + title + " | BLOCKED | exit=' + $p.ExitCode + '; see reports/logs/" + prefix + ".stderr.log |'); exit $p.ExitCode }"]
    doc += ['```', '', 'Prepared background launcher (not executed):', '', '```powershell', "Start-Process -FilePath powershell.exe -WindowStyle Hidden -ArgumentList " + psquote('-NoProfile -ExecutionPolicy Bypass -File "' + str(REPORTS / ('prepared_' + label + '.ps1')) + '"'), '```', '']
    (REPORTS / ('prepared_' + label + '.ps1')).write_text('\n'.join(script) + '\n', encoding='utf-8-sig')
(REPORTS / 'prepared_gpu_commands.md').write_text('\n'.join(doc) + '\n', encoding='utf-8')

assert hashes == {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
audit = dict(timestamp=STAMP, selected_full=len(full), selected_hard=len(hard), subprocesses=0, engine_launches=0, source_and_config_hashes=hashes, finished_A=finished, pending_A=pending, tables=tables, runtime=runtime, snapshot_notes=notes, commands=[dict(step=t, command='& ' + psquote(python) + ' ' + ' '.join(psquote(x) for x in a)) for t, a, _ in commands])
(REPORTS / 'cpu_prep_audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
print('UNCHANGED: eval/run_study.py eval/score.py hw/bench.py ladder.py config.json (SHA256 verified)')
print('PRODUCED: reports/study_a_mcnemar.md; reports/cpu_prep_audit.json; reports/prepared_gpu_commands.md; reports/prepared_{hard_lowbudget,studyc,hw}.ps1 (NOT RUN)')
