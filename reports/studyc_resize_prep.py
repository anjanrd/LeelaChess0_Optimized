"""Back up stopped Study C output, repair only a truncated final JSONL line."""
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'reports/c3-part1/studyc-work/results'
assert source.resolve().is_relative_to(ROOT)
tag = datetime.now().astimezone().strftime('%Y-%m-%dT%H%M%S_%z')
backup = ROOT / 'reports/studyc-backup' / tag
backup.mkdir(parents=True, exist_ok=False)
manifest = {'backup': str(backup.relative_to(ROOT)), 'source': str(source), 'files': [], 'repairs': []}
paths = sorted(p for p in source.rglob('*') if p.is_file())
for p in paths:
    rel = p.relative_to(source)
    destination = backup / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, destination)
    data = p.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == digest
    info = {'file': str(rel), 'size': len(data), 'sha256': digest}
    manifest['files'].append(info)
    print('BACKUP', json.dumps(info))

# All files were copied before any repair or config mutation.
for p in paths:
    if p.suffix != '.jsonl':
        print('Diagnostic log backed up, not a JSONL results file:', p.relative_to(source))
        continue
    data = p.read_bytes()
    lines = data.splitlines(keepends=True)
    indices = [i for i, line in enumerate(lines) if line.strip()]
    if not indices:
        print('EMPTY JSONL', p.relative_to(source))
        continue
    last = indices[-1]
    for i in indices[:-1]:
        json.loads(lines[i])
    try:
        json.loads(lines[last])
        print('VALID FINAL JSON', p.relative_to(source), 'rows=', len(indices), '; no trimming')
    except json.JSONDecodeError as error:
        # A malformed complete line is not silently repaired.
        payload = lines[last].rstrip(b'\r\n')
        truncated = (not lines[last].endswith(b'\n') and (error.pos >= len(payload) - 2 or error.msg.startswith('Unterminated')))
        assert truncated, f'Final JSONL line invalid but not demonstrably truncated: {p}: {error}'
        repaired = b''.join(lines[:last] + lines[last + 1:])
        p.write_bytes(repaired)
        repair = dict(file=str(p.relative_to(source)), removed_line=last + 1, removed_bytes=len(lines[last]), reason=str(error))
        manifest['repairs'].append(repair)
        print('REMOVED ONLY TRUNCATED FINAL LINE', json.dumps(repair))

config = ROOT / 'reports/c3-part1/config.studyc.json'
shutil.copy2(config, backup / 'config.studyc.before.json')
cfg = json.loads(config.read_text(encoding='utf-8-sig'))
old = cfg['studyc']['limit']
cfg['studyc']['limit'] = 2437
config.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')
print(f'CONFIG ONLY: reports/c3-part1/config.studyc.json studyc.limit {old} -> {cfg["studyc"]["limit"]}; main config.json unchanged; no pipeline source edits')

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'eval'))
spec = importlib.util.spec_from_file_location('resize_positions', ROOT / 'eval/run_study.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
selected = study.positions(argparse.Namespace(tbset=str(ROOT / 'data/tbset.jsonl'), split=cfg['study']['split'], classes=None, ids=None, shard=None, limit=cfg['studyc']['limit']))
ids = {r['id'] for r in selected}
ref = {json.loads(line)['id'] for line in (ROOT / 'results/fp16/study_b.jsonl').read_bytes().splitlines() if json.loads(line)['budget'] == 1600}
assert len(ids) == 2437 and ids == ref, 'Selected positions differ from existing Study A/B reference IDs'
baseline = {'selected_ids': sorted(ids), 'models': {}, 'files': {}, 'manifest': str((backup / 'manifest.json').relative_to(ROOT)), 'command': [str(ROOT.parent / '.venv/Scripts/python.exe'), '-u', str(ROOT / 'ladder.py'), 'studyc', '--config', str(config)]}
for name in ('fp16', cfg['best']):
    p = source / name / 'study_c.jsonl'
    data = p.read_bytes() if p.exists() else b''
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    keys = {(r['id'], r['movetime']) for r in rows}
    assert len(rows) == len(keys), (name, 'pre-existing duplicate keys')
    info = {}
    for t in (200, 800):
        all_done = {i for i, mt in keys if mt == t}
        target_done = all_done & ids
        info[str(t)] = dict(all_existing=len(all_done), selected_existing=len(target_done), remaining=2437 - len(target_done))
        print(f'BASELINE {name} {t}ms: selected existing={len(target_done)}/2437; all stored={len(all_done)}; remaining={2437 - len(target_done)}')
    baseline['models'][name] = info
    baseline['files'][name] = dict(path=str(p), size=len(data), sha256=hashlib.sha256(data).hexdigest(), keys=[list(k) for k in sorted(keys)])
baseline['log_size'] = (ROOT / 'reports/logs/c3_b_studyc.log').stat().st_size
(backup / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(ROOT / 'reports/c3-part1/resize-baseline.json').write_text(json.dumps(baseline, indent=2) + '\n', encoding='utf-8')
print('SELECTED: 2437 positions, exact match to Studies A/B class-balanced IDs; existing out-of-selection rows preserved')
print('RESUME COMMAND:', __import__('subprocess').list2cmdline(baseline['command']))
print('PRODUCED', str(backup.relative_to(ROOT)), 'reports/c3-part1/resize-baseline.json')
