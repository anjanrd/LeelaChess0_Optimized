"""Acquire verified Syzygy dependencies and freeze the Week 1 standalone splits."""
import argparse
import collections
import json
import random
import subprocess
import time
import urllib.request
from pathlib import Path

import chess
import chess.syzygy
import numpy as np

from week1_common import PROJECT, RUNTIME, artifact, base, frozen, progress, read, save
from prepare_pilot import FAMILIES, SEED, group_id, sample_board
from lc0_inputs import classical_planes, dense_planes, legal_move_indices, native_encode

TABLES = base.RUNTIME / 'syzygy'
SOURCE = base.RUNTIME / 'source/syzygy-tb'
DEST = PROJECT / 'data/syzygy'
ROOT_FAMILIES = ['KQvKQ', 'KQvKR', 'KPvKP', 'KPvKR']


def acquire():
    TABLES.mkdir(parents=True, exist_ok=True)
    dependencies = sorted(set(chess.syzygy.all_dependencies(ROOT_FAMILIES)))
    commit = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    checker = SOURCE / 'src/tbcheck'
    assert checker.exists()
    expected = {}
    for kind in ['wdl', 'dtz']:
        text = (SOURCE / f'checksums/{kind}345.txt').read_text()
        expected.update(dict(line.strip().split(': ') for line in text.splitlines() if ': ' in line))
    files = []
    for name in dependencies:
        for kind, suffix, magic in [('wdl', 'rtbw', b'\x71\xe8\x23\x5d'), ('dtz', 'rtbz', b'\xd7\x66\x0c\xa5')]:
            filename = name + '.' + suffix
            url = f'https://tablebase.lichess.ovh/tables/standard/3-4-5-{kind}/{filename}'
            path = TABLES / filename
            if not path.exists():
                partial = TABLES / (filename + '.partial')
                for attempt in range(3):
                    try:
                        with urllib.request.urlopen(url, timeout=90) as src, partial.open('wb') as dst:
                            while chunk := src.read(1024 * 1024):
                                dst.write(chunk)
                        partial.replace(path)
                        break
                    except Exception:
                        if attempt == 2: raise
                        time.sleep(2)
            with path.open('rb') as f:
                assert f.read(4) == magic, filename
            computed = subprocess.run([str(checker), '-t', '2', filename], cwd=TABLES, capture_output=True, text=True, check=True)
            transcript = computed.stdout + computed.stderr
            assert 'OK' in transcript and 'FAIL' not in transcript and 'Could not' not in transcript, transcript
            embedded = subprocess.check_output([str(checker), '-p', filename], cwd=TABLES, text=True).strip().split(': ')[-1]
            assert embedded == expected[filename], (filename, embedded, expected[filename])
            files.append(dict(artifact(path), filename=filename, bytes=path.stat().st_size, url=url,
                              published_cityhash_checksum=embedded, full_file_checksum_verified=True))
            print('Verified', filename, path.stat().st_size, flush=True)
    save(PROJECT / 'environment/week1-tablebases.json', {
        'status': 'passed', 'verified_at_utc': base.now(), 'root_materials': ROOT_FAMILIES,
        'dependencies': dependencies, 'directory': str(TABLES), 'files': files,
        'checksum_tool': artifact(checker), 'checksum_source_commit': commit,
        'checksum_source': 'https://github.com/syzygy1/tb/tree/' + commit + '/checksums',
        'verification': 'tbcheck recomputes full-file checksum and checks embedded checksum; embedded value independently matches published official list. These are not MD5 checksums.',
        'checker_build': 'make -B -j2 tbcheck FLAGS=-DBMI2,-DUSE_POPCNT,-DTBPIECES=7,-DCOMPRESSION_THREADS=2,-DREGULAR LDFLAGS= (space-separated FLAGS); optional zstd unavailable and unnecessary for checksum checks',
        'total_bytes': sum(r['bytes'] for r in files), 'script_sha256': base.sha256(__file__)})


def sign(value):
    return int(value > 0) - int(value < 0)


def outcome(board, tb):
    if board.is_checkmate(): return -1
    if board.is_stalemate() or board.is_insufficient_material(): return 0
    return sign(tb.probe_wdl(board))


def labels(board, tb):
    raw = tb.probe_wdl(board)
    root = sign(raw)
    moves = {}
    for move in sorted(board.legal_moves, key=lambda m: m.uci()):
        child = board.copy(stack=False)
        child.push(move)
        moves[move.uci()] = -outcome(child, tb)
    assert moves and max(moves.values()) == root, (board.fen(), raw, moves)
    return {'root_wdl5': raw, 'root_outcome': root, 'root_dtz': tb.probe_dtz(board),
            'cursed_or_blessed': abs(raw) == 1, 'move_outcomes': moves,
            'preserving_moves': [m for m, u in moves.items() if u == root],
            'decision_sensitive': any(u < root for u in moves.values())}


def scoring_checks(tb):
    fixtures = [
        ('KQK-win', '7k/8/6K1/8/8/8/2Q5/8 w - - 0 1', 1),
        ('KRK-win', '7k/8/6K1/8/8/8/2R5/8 w - - 0 1', 1),
        ('mate', '7k/6Q1/6K1/8/8/8/8/8 b - - 0 1', -1),
        ('stalemate', '7k/5Q2/6K1/8/8/8/8/8 b - - 0 1', 0),
        ('insufficient', '7k/8/6K1/8/8/8/8/8 w - - 0 1', 0)]
    results = []
    for name, fen, expected in fixtures:
        b = chess.Board(fen)
        assert b.is_valid() and outcome(b, tb) == expected
        assert outcome(b.mirror(), tb) == expected
        if list(b.legal_moves) and not b.is_game_over(): labels(b, tb)
        results.append({'name': name, 'fen': fen, 'outcome': expected, 'mirror_agrees': True})
    # A mate-in-one and a queen capture independently exercise mover sign.
    mate = chess.Board('7k/8/5KQ1/8/8/8/8/8 w - - 0 1')
    mate.push_uci('g6g7')
    assert mate.is_checkmate() and -outcome(mate, tb) == 1
    capture = chess.Board('7k/8/8/8/8/8/2q5/2K5 w - - 0 1')
    capture.push_uci('c1c2')
    assert capture.is_insufficient_material() and -outcome(capture, tb) == 0
    missing = chess.Board('7k/8/6K1/8/8/8/Q7/R7 w - - 0 1')
    assert missing.is_valid()
    try: tb.probe_wdl(missing)
    except chess.syzygy.MissingTableError: pass
    else: raise AssertionError('Missing material was silently accepted')
    assert sign(-1) == -1 and sign(1) == 1
    return {'fixtures': results, 'mate_in_one_sign': True, 'capture_terminal_sign': True,
            'missing_tables_raise': True, 'five_way_mapping': {-2: -1, -1: -1, 0: 0, 1: 1, 2: 1},
            'note': 'Cursed/blessed mapping checked by explicit mapping and any naturally sampled cases; no fabricated tablebase fixture'}


def build():
    assert read(PROJECT / 'environment/week1-int8-pilot.json')['status'] == 'passed_A_side'
    assert read(PROJECT / 'environment/week1-tablebases.json')['status'] == 'passed'
    frozen()
    progress('W1-A08', 'IN_PROGRESS', detail='Verified complete Syzygy dependencies; constructing and cross-checking registered standalone W/D splits.')
    DEST.mkdir(parents=True, exist_ok=True)
    plan = {'version': '1.0', 'registered_at_utc': base.now(), 'seed': SEED,
        'counts': {'calibration': 1024, 'validation': 2048, 'test': 10000},
        'cells': 'Equal four material families x side to move x theoretical W/D (16 cells)',
        'distribution': 'Uniform random placements of both kings and two family pieces, fixed side; reject illegal, terminal, fewer-than-two-move, unwanted-outcome, duplicate symmetry and prior-development groups; rejection sampling within each cell',
        'history': 'standalone FEN; history_fill=no; halfmove=0; fullmove=1; no castling/EP',
        'exclusions': 'All 221 pilot/fixture/numerical-confirmation groups excluded from every new split',
        'trajectory': 'No generated game trajectories; each accepted root forms one independent symmetry group. Future search calibration must originate in training pool and filter visited states against held-out groups.',
        'hard_subset': 'Decision-sensitive roots only; m=max FP16 preserving probability-max FP16 degrading probability; validation 20th percentile tau; freeze tau before test scoring',
        'dtz': 'Root DTZ recorded. No DTZ-optimal move ranking claimed; B04 requires separate validation.',
        'test_usage': 'Baselines scored in A09; INT8 pilot used only prior development data; no test-driven tuning',
        'root_labels': 'theoretical WDL sign, ignoring fifty-move clock; preserve cursed/blessed tags',
        'feasibility_rule': 'Retain original counts unless missing coverage or measured runtime prevents completion; no result-driven adjustment'}
    plan_path = DEST / 'protocol.json'
    if plan_path.exists():
        old = read(plan_path)
        plan['registered_at_utc'] = old['registered_at_utc']
        assert old == plan
    else: save(plan_path, plan)
    excluded = set()
    for name in ['pilot', 'export-confirmation']:
        excluded.update(read(PROJECT / f'data/{name}/exclusions.json')['symmetry_groups'])
    assert len(excluded) == 221
    seen = set(excluded)
    rng = random.Random(SEED)
    manifests = {}; all_groups = {}; began = time.perf_counter()
    with chess.syzygy.open_tablebase(str(TABLES), max_fds=64) as tb:
        checks = scoring_checks(tb)
        save(PROJECT / 'environment/week1-scoring-checks.json', dict(checks, status='passed', verified_at_utc=base.now()))
        for split, count in plan['counts'].items():
            rows = []; attempts = collections.Counter(); counts = collections.Counter(); start = time.perf_counter()
            for family, pieces in FAMILIES.items():
                for side in [chess.WHITE, chess.BLACK]:
                    for required in [1, 0]:
                        cell = f'{family}:{"white" if side else "black"}:{"W" if required else "D"}'
                        while counts[cell] < count // 16:
                            b = sample_board(rng, pieces, side)
                            attempts[cell] += 1
                            if attempts[cell] > 2000000: raise RuntimeError('Sampling feasibility limit: '+cell)
                            if sign(tb.probe_wdl(b)) != required: continue
                            group = group_id(b)
                            if group in seen: continue
                            info = labels(b, tb)
                            row = {'id': f'{split}-{len(rows):05d}', 'family': family, 'side_to_move': 'white' if side else 'black',
                                   'fen': b.fen(en_passant='fen'), 'moves': [], 'symmetry_group': group, **info}
                            rows.append(row); seen.add(group); counts[cell] += 1
            # Seeded random order prevents material/label blocks in later batches.
            rng.shuffle(rows)
            positions = DEST / f'{split}.jsonl'
            positions.write_text(''.join(json.dumps(r, sort_keys=True) + '\n' for r in rows))
            planes = np.empty((count, 112, 8, 8), dtype=np.float32)
            for offset in range(0, count, 128):
                batch = rows[offset:offset + 128]
                native = native_encode(batch)
                for j, (row, enc) in enumerate(zip(batch, native)):
                    value = dense_planes(enc)
                    assert np.array_equal(value, classical_planes(row)), row['id']
                    assert dict(enc['legal']) == legal_move_indices(chess.Board(row['fen']))
                    assert enc['transform'] == 0
                    planes[offset+j] = value
            inputs = DEST / f'{split}-inputs.npz'
            np.savez_compressed(inputs, planes=planes, ids=np.array([r['id'] for r in rows]))
            groups = {r['symmetry_group'] for r in rows}
            assert len(groups) == count and not (groups & excluded)
            for other in all_groups.values(): assert not (other & groups)
            all_groups[split] = groups
            manifests[split] = {'count': count, 'cells': dict(counts), 'sampling_attempts': dict(attempts),
                'decision_sensitive': sum(r['decision_sensitive'] for r in rows),
                'cursed_blessed': sum(r['cursed_or_blessed'] for r in rows),
                'positions': artifact(positions), 'inputs': artifact(inputs),
                'seconds': time.perf_counter()-start, 'native_encoder_and_python_planes_all_exact': True,
                'all_legal_children_labeled_and_root_consistency_checked': True}
            print('Frozen', split, count, 'seconds', round(time.perf_counter()-start, 2), flush=True)
    save(DEST / 'manifest.json', {'status': 'passed', 'created_at_utc': base.now(), 'protocol': artifact(plan_path),
        'splits': manifests, 'excluded_prior_groups': len(excluded), 'all_split_symmetry_groups_disjoint': True,
        'all_root_halfmove_clocks_zero': True, 'tablebases': artifact(PROJECT/'environment/week1-tablebases.json'),
        'scoring_checks': artifact(PROJECT/'environment/week1-scoring-checks.json'), 'total_seconds': time.perf_counter()-began,
        'script_sha256': base.sha256(__file__)})
    progress('W1-A08', 'DONE', 'data/syzygy/manifest.json', 'All 13,072 roots, all legal child outcomes, exact native encodings and symmetry-disjoint splits verified. Hard membership awaits floating validation outputs in A09.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('stage', choices=['acquire', 'build']); a = p.parse_args()
    {'acquire': acquire, 'build': build}[a.stage]()
