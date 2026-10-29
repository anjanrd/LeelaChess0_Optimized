"""Select published game/tablebase roots and verify native fen_only inputs.

Source ranges, tables and utility dependencies stay in the external WSL runtime.
Does not run NN inference or change historical datasets/precision acceptances.
"""
import argparse
import collections
import hashlib
import io
import json
import random
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import chess
import chess.syzygy
import numpy as np

from week1_common import PROJECT, base, frozen, read, save, artifact
from lc0_inputs import (classical_planes, replay, dense_planes, native_encode,
                        legal_move_indices)
from prepare_pilot import group_id
from datasets_week1 import labels, sign

DEST = PROJECT / 'data/syzygy-v2'
WORK = base.RUNTIME / 'week1/step1'
TABLES = base.RUNTIME / 'syzygy'
SOURCE_REPO = 'https://github.com/IgorRigolon/chess.endgames'
SOURCE_COMMIT = '2e2f0842c435905940d4bf06c002fa1d463fd859'
SOURCE_SIZE = 1403288476
GENERATION = '1754704938545033'
SOURCE_URL = ('https://storage.googleapis.com/chess_endgames/'
              'chess_endgames_2025-06.parquet?generation=' + GENERATION)
COUNTS = {'calibration': 1024, 'validation': 2048, 'test': 10000}
SEED = 20261027
CELLS = [(n, side, w) for n in [4, 5] for side in [True, False] for w in [1, 0]]


def parquet_module():
    # Dedicated reader only; the pinned model environment is not upgraded.
    sys.path.insert(0, str(base.RUNTIME / 'tools/pyarrow-21.0.0'))
    import pyarrow.parquet as pq
    return pq


class SourceRanges(io.RawIOBase):
    def __init__(self):
        self.pos = 0
        self.directory = WORK / 'source-ranges'
        self.directory.mkdir(parents=True, exist_ok=True)
        self.ranges = {}

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        self.pos = (offset if whence == 0 else self.pos + offset
                    if whence == 1 else SOURCE_SIZE + offset)
        assert 0 <= self.pos <= SOURCE_SIZE
        return self.pos

    def read(self, size=-1):
        size = SOURCE_SIZE - self.pos if size < 0 else min(size, SOURCE_SIZE - self.pos)
        if size <= 0: return b''
        start = self.pos
        path = self.directory / f'{start}-{size}.bin'
        if path.exists():
            data = path.read_bytes()
        else:
            req = urllib.request.Request(SOURCE_URL, headers={
                'Range': f'bytes={start}-{start + size - 1}',
                'User-Agent': 'LC0-week1-data-validation'})
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(req, timeout=90) as f:
                        assert f.status == 206
                        assert f.headers['x-goog-generation'] == GENERATION
                        assert f.headers['Content-Range'] == f'bytes {start}-{start+size-1}/{SOURCE_SIZE}'
                        data = f.read()
                    break
                except Exception:
                    if attempt == 2: raise
                    time.sleep(2)
            assert len(data) == size
            path.write_bytes(data)
        assert len(data) == size
        self.ranges[path.name] = artifact(path)
        self.pos += size
        return data


def fen_only_planes(record):
    """Independent classical-format padding, preserving actual historical slots."""
    result = classical_planes(record)
    _, snapshots = replay(record)
    first = snapshots[0]
    depth = len(snapshots)
    if depth >= 8: return result
    all_castling = chess.BB_A1 | chess.BB_H1 | chess.BB_A8 | chess.BB_H8
    if (first.turn == chess.WHITE and first.board_fen() == chess.STARTING_BOARD_FEN and
            first.castling_rights == all_castling and first.ep_square is None):
        return result  # Native FEN_ONLY stops padding before the initial board.
    # NO already reconstructs one predecessor when the earliest FEN has EP.
    earliest = depth if first.ep_square is not None else depth - 1
    block = result[earliest * 13:(earliest + 1) * 13].copy()
    for i in range(depth, 8): result[i * 13:(i + 1) * 13] = block
    return result


def excluded_groups():
    groups = set()
    for name in ['pilot', 'export-confirmation']:
        groups.update(read(PROJECT / f'data/{name}/exclusions.json')['symmetry_groups'])
    assert len(groups) == 221
    for name in COUNTS:
        for line in (PROJECT / f'data/syzygy/{name}.jsonl').read_text().splitlines():
            groups.add(json.loads(line)['symmetry_group'])
    return groups


def cell_key(cell):
    n, side, w = cell
    return f'{n}piece:{"white" if side else "black"}:{"W" if w else "D"}'


def source():
    """Sample existing source rows, never invent board placements or game moves."""
    WORK.mkdir(parents=True, exist_ok=True)
    if (WORK / 'candidates.json').exists() and (WORK / 'source.json').exists():
        stored = read(WORK / 'source.json')['candidate_file']
        assert base.sha256(stored['path']) == stored['sha256']
        print('Reusing pinned published candidate pool.', flush=True)
        return
    remote = SourceRanges()
    pf = parquet_module().ParquetFile(remote)
    order = list(range(pf.num_row_groups))
    rng = random.Random(SEED)
    rng.shuffle(order)
    pools = {c: [] for c in CELLS}
    seen_groups = excluded_groups()
    source_games = set()
    reasons = collections.Counter()
    target = sum(COUNTS.values()) // 8 + 100
    scanned = []
    for rg in order:
        table = pf.read_row_group(rg, columns=['id', 'fens', 'eval', 'white_to_move'])
        scanned.append(rg)
        for batch in table.to_batches(max_chunksize=32768):
            columns = batch.to_pydict()
            for local, (game, fen, white_eval, turn) in enumerate(zip(
                    columns['id'], columns['fens'], columns['eval'], columns['white_to_move'])):
                if not all(isinstance(x, (int, float)) and np.isfinite(x)
                           for x in [game, white_eval]):
                    reasons['bad_metadata'] += 1; continue
                assert game == int(game) and white_eval == int(white_eval)
                game = str(int(game))
                if game in source_games: continue
                board_part = fen.split()[0]
                n = sum(ch.isalpha() for ch in board_part)
                if n not in [4, 5]: continue
                wdl = int(white_eval) * (1 if turn else -1)
                assert wdl in [-2, -1, 0, 1, 2]
                outcome = sign(wdl)
                if outcome < 0: continue
                # Select an existing position or its exact chess color/rank
                # symmetry. This also corrects the source filter's omission of
                # five-piece Black-to-move rows (it counts the FEN 'b' as a man).
                mirrored = int(hashlib.sha256(game.encode()).hexdigest(), 16) % 2 == 1
                selected_turn = bool(turn) != mirrored
                cell = (n, selected_turn, outcome)
                if len(pools[cell]) >= target: continue
                b = chess.Board(fen)
                assert b.turn == bool(turn)
                if not b.is_valid() or b.castling_rights or b.ep_square is not None:
                    reasons['invalid_or_rights'] += 1; continue
                if b.is_game_over() or b.legal_moves.count() < 2:
                    reasons['terminal_or_forced'] += 1; continue
                if mirrored: b = b.mirror()
                # Registered theoretical-WDL experiment uses clock zero, not
                # game-specific fifty-move/repetition claims; retain source FEN.
                b.halfmove_clock = 0; b.fullmove_number = 1
                group = group_id(b)
                if group in seen_groups:
                    reasons['duplicate_or_prior_group'] += 1; continue
                record = {'fen': b.fen(en_passant='fen'), 'moves': [],
                          'source_fen': fen, 'source_game_id': game,
                          'source_transform': 'color_rank_mirror' if mirrored else 'identity',
                          'source_row_group': rg, 'source_wdl5_stm': wdl,
                          'symmetry_group': group, 'piece_count': n,
                          'side_to_move': 'white' if b.turn else 'black'}
                pools[cell].append(record)
                source_games.add(game); seen_groups.add(group)
            if all(len(v) >= target for v in pools.values()): break
        print('Source row group', rg, 'pool', {cell_key(c): len(v) for c, v in pools.items()}, flush=True)
        del table
        if all(len(v) >= target for v in pools.values()): break
    assert all(len(v) >= target for v in pools.values()), 'Published source coverage insufficient'
    output = []
    for cell, rows in pools.items():
        rng.shuffle(rows)
        output.extend(rows)
    save(WORK / 'candidates.json', output)
    license_url = f'https://raw.githubusercontent.com/IgorRigolon/chess.endgames/{SOURCE_COMMIT}/LICENSE'
    with urllib.request.urlopen(license_url, timeout=40) as f: license_text = f.read().decode()
    save(WORK / 'source.json', {'repository': SOURCE_REPO, 'source_commit': SOURCE_COMMIT,
         'object_url': SOURCE_URL, 'object_generation': GENERATION, 'object_size': SOURCE_SIZE,
         'origin': 'June 2025 Lichess games, published FENs and Syzygy labels by Igor Rigolon',
         'license': 'MIT; underlying Lichess game data CC0', 'license_text': license_text,
         'rows_in_source': pf.metadata.num_rows, 'row_groups_scanned': scanned,
         'selection': 'Seeded row-group order; one accepted root per source game; balanced piece-count/side/W-D cells; no NN outputs used',
         'symmetry': 'Each game deterministically selects identity or color/rank mirror; original FEN retained. No random piece placements.',
         'source_filter_bias': 'Upstream is_tablebase counts piece letters over the whole FEN, so the side-to-move b omits true 5-piece Black roots. Source evaluations converted White -> STM before any mirror.',
         'candidate_count': len(output), 'rejections': dict(reasons),
         'cached_ranges': list(remote.ranges.values()), 'candidate_file': artifact(WORK / 'candidates.json'),
         'reader': 'pyarrow 21.0.0 installed in isolated utility target; model environment unchanged',
         'integrity_limit': 'Selected ranges hashed and immutable GCS generation pinned; full 1.4GB object not downloaded or claimed fully hashed'})


def acquire():
    rows = read(WORK / 'candidates.json')
    roots = sorted({chess.syzygy.calc_key(chess.Board(r['fen'])) for r in rows})
    deps = sorted(set(chess.syzygy.all_dependencies(roots)))
    src = base.RUNTIME / 'source/syzygy-tb'
    checker = src / 'src/tbcheck'
    expected = {}
    for kind in ['wdl', 'dtz']:
        expected.update(dict(line.strip().split(': ') for line in
                        (src / f'checksums/{kind}345.txt').read_text().splitlines() if ': ' in line))
    jobs = [(name, kind, ext) for name in deps for kind, ext in [('wdl', 'rtbw'), ('dtz', 'rtbz')]]

    def one(job):
        name, kind, ext = job
        filename = f'{name}.{ext}'
        path = TABLES / filename
        url = f'https://tablebase.lichess.ovh/tables/standard/3-4-5-{kind}/{filename}'
        if not path.exists():
            partial = TABLES / (filename + '.partial')
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(url, timeout=90) as f, partial.open('wb') as out:
                        while data := f.read(1024 * 1024): out.write(data)
                    partial.replace(path)
                    break
                except Exception:
                    if attempt == 2: raise
                    time.sleep(2)
        test = subprocess.run([str(checker), '-t', '2', filename], cwd=TABLES,
                              capture_output=True, text=True, check=True)
        transcript = test.stdout + test.stderr
        assert 'OK' in transcript and 'FAIL' not in transcript and 'Could not' not in transcript
        embedded = subprocess.check_output([str(checker), '-p', filename], cwd=TABLES, text=True).strip().split(': ')[-1]
        assert embedded == expected[filename], filename
        return dict(artifact(path), filename=filename, bytes=path.stat().st_size,
                    url=url, published_cityhash=embedded, full_checksum_verified=True)

    files = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for item in pool.map(one, jobs):
            files.append(item)
            if len(files) % 20 == 0: print('Verified tables', len(files), '/', len(jobs), flush=True)
    save(WORK / 'tables.json', {'root_materials': roots, 'dependencies': deps,
         'files': files, 'total_bytes': sum(f['bytes'] for f in files),
         'checksum_tool': artifact(checker),
         'checksum_source_commit': subprocess.check_output(['git', '-C', str(src), 'rev-parse', 'HEAD'], text=True).strip()})


def build():
    frozen()
    DEST.mkdir(parents=True, exist_ok=True)
    protocol = {'version': '2.0', 'seed': SEED, 'counts': COUNTS,
       'selection': 'Published game/tablebase roots or their color/rank mirrors; 4 and 5 pieces equally; W/D and sides equally; no generated board placements',
       'interpretation': 'Stratified benchmark, not the natural frequency distribution of endgames or a measure of Elo',
       'source': read(WORK / 'source.json'), 'history_fill': 'fen_only',
       'counters': 'Effective halfmove=0/fullmove=1; original source FEN preserved; theoretical WDL ignores fifty-move rule',
       'groups': 'One root per source game globally, valid symmetry groups disjoint; exclude all old 13,072 roots plus 221 development groups',
       'test_usage': 'New selected test roots: no project NN outputs inspected before split freeze; old inspected benchmark retained unchanged; use validation for model choices',
       'labels': 'Independent local Syzygy WDL and all legal-child outcomes; verify against published root label; DTZ root diagnostic only',
       'registered_before_model_inference': True, 'tables': read(WORK / 'tables.json')}
    protocol_path = DEST / 'protocol.json'
    if protocol_path.exists(): assert read(protocol_path) == protocol
    else: save(protocol_path, protocol)
    candidates = read(WORK / 'candidates.json')
    available = {c: [] for c in CELLS}
    for r in candidates:
        available[(r['piece_count'], r['side_to_move'] == 'white', sign(r['source_wdl5_stm']))].append(r)
    selected = set(); manifests = {}; rng = random.Random(SEED)
    with chess.syzygy.open_tablebase(str(TABLES), max_fds=128) as tb:
        for split, count in COUNTS.items():
            rows = []
            for cell in CELLS:
                for _ in range(count // 8):
                    r = available[cell].pop()
                    b = chess.Board(r['fen'])
                    info = labels(b, tb)
                    assert info['root_wdl5'] == r['source_wdl5_stm'], ('Published-label mismatch', r, info)
                    assert r['source_game_id'] not in selected
                    selected.add(r['source_game_id'])
                    row = dict(r, family=chess.syzygy.calc_key(b), **info)
                    rows.append(row)
            rng.shuffle(rows)
            for i, r in enumerate(rows): r['id'] = f'v2-{split}-{i:05d}'
            positions = DEST / f'{split}.jsonl'
            payload = ''.join(json.dumps(r, sort_keys=True) + '\n' for r in rows)
            if positions.exists(): assert positions.read_text() == payload
            else: positions.write_text(payload)
            planes = np.empty((count, 112, 8, 8), dtype=np.float32)
            for offset in range(0, count, 128):
                chunk = rows[offset:offset + 128]
                encoded = native_encode(chunk, fill='fen_only')
                for j, (row, enc) in enumerate(zip(chunk, encoded)):
                    value = dense_planes(enc)
                    assert np.array_equal(value, fen_only_planes(row)), row['id']
                    assert dict(enc['legal']) == legal_move_indices(chess.Board(row['fen']))
                    planes[offset + j] = value
            assert np.isfinite(planes).all()
            inputs = DEST / f'{split}-inputs.npz'
            if inputs.exists():
                with np.load(inputs, allow_pickle=False) as saved:
                    assert np.array_equal(saved['planes'], planes)
                    assert list(saved['ids']) == [r['id'] for r in rows]
            else: np.savez_compressed(inputs, planes=planes, ids=np.array([r['id'] for r in rows]))
            manifests[split] = {'count': count, 'positions': artifact(positions), 'inputs': artifact(inputs),
                 'piece_counts': dict(collections.Counter(r['piece_count'] for r in rows)),
                 'cells': dict(collections.Counter(cell_key((r['piece_count'], r['side_to_move']=='white', r['root_outcome'])) for r in rows)),
                 'material_counts': dict(collections.Counter(r['family'] for r in rows)),
                 'cursed_blessed': sum(r['cursed_or_blessed'] for r in rows),
                 'all_native_planes_and_move_indices_match': True,
                 'all_root_and_legal_child_WDL_checked': True}
            print('Built and verified', split, count, manifests[split]['piece_counts'], flush=True)
    save(DEST / 'manifest.json', {'status': 'passed', 'protocol': artifact(protocol_path),
         'splits': manifests, 'created_at_utc': base.now(), 'script': artifact(Path(__file__))})


def verify():
    frozen()
    m = read(DEST / 'manifest.json')
    assert m['status'] == 'passed'
    seen = excluded_groups(); all_games = set(); checks = []; published_roots = set()
    source_meta = read(WORK / 'source.json')
    for record in [source_meta['candidate_file'], *source_meta['cached_ranges']]:
        assert base.sha256(record['path']) == record['sha256']
    for split, n in COUNTS.items():
        rows = [json.loads(x) for x in (DEST / f'{split}.jsonl').read_text().splitlines()]
        assert len(rows) == n
        with np.load(DEST / f'{split}-inputs.npz', allow_pickle=False) as d:
            assert d['planes'].shape == (n, 112, 8, 8) and d['planes'].dtype == np.float32
            assert list(d['ids']) == [r['id'] for r in rows]
            assert np.isfinite(d['planes']).all()
        for row in rows:
            board = chess.Board(row['fen'])
            assert board.is_valid() and len(board.piece_map()) == row['piece_count']
            original = chess.Board(row['source_fen'])
            assert row['source_transform'] in ['identity', 'color_rank_mirror']
            if row['source_transform'] == 'color_rank_mirror': original = original.mirror()
            original.halfmove_clock = 0; original.fullmove_number = 1
            assert original.fen(en_passant='fen') == row['fen']
            group = group_id(board)
            assert group == row['symmetry_group'] and group not in seen
            assert row['source_game_id'] not in all_games
            seen.add(group); all_games.add(row['source_game_id'])
            published_roots.add((row['source_game_id'], row['source_fen']))
        cells = collections.Counter((r['piece_count'], r['side_to_move']=='white', r['root_outcome']) for r in rows)
        assert all(cells[c] == n // 8 for c in CELLS)
        for name in ['inputs', 'positions']:
            rec = m['splits'][split][name]
            assert base.sha256(rec['path']) == rec['sha256']
        checks.append({'split': split, 'count': n, 'unique_games': n, 'hashes_valid': True,
            'piece_counts': dict(collections.Counter(r['piece_count'] for r in rows)),
            'source_transforms': dict(collections.Counter(r['source_transform'] for r in rows)),
            'source_board_reconstruction_all_exact': True, 'eight_cells_balanced': True})
    # Independent provenance audit: find every original FEN/game pair again in
    # the pinned raw Parquet source, rather than trusting our derived JSON rows.
    raw = parquet_module().ParquetFile(SourceRanges())
    wanted_games = {int(game) for game, _ in published_roots}
    found = set()
    for rg in source_meta['row_groups_scanned']:
        table = raw.read_row_group(rg, columns=['id', 'fens'])
        for batch in table.to_batches(max_chunksize=32768):
            data = batch.to_pydict()
            for game, fen in zip(data['id'], data['fens']):
                if game in wanted_games and (str(int(game)), fen) in published_roots:
                    found.add((str(int(game)), fen))
        del table
    assert found == published_roots and len(found) == sum(COUNTS.values())
    fixtures = [json.loads(x) for x in (PROJECT / 'data/pilot/fixtures.jsonl').read_text().splitlines()]
    encoded = native_encode(fixtures, fill='fen_only')
    for row, value in zip(fixtures, encoded):
        assert np.array_equal(fen_only_planes(row), dense_planes(value)), row['id']
        board, _ = replay(row)
        assert dict(value['legal']) == legal_move_indices(board), row['id']
    report = {'status': 'passed', 'verified_at_utc': base.now(),
        'dataset_manifest': artifact(DEST / 'manifest.json'), 'splits': checks,
        'all_split_games_and_symmetry_groups_disjoint': True,
        'all_old_positions_and_prior_development_groups_excluded': True,
        'all_13072_native_inputs_and_legal_maps_exact': True,
        'history_and_edge_fixtures': len(fixtures), 'fixture_planes_and_legal_maps_exact': True,
        'source_url': SOURCE_REPO, 'source_commit': SOURCE_COMMIT,
        'source_object_generation': GENERATION,
        'source_ranges_and_candidate_hashes_verified': True,
        'all_13072_original_FEN_game_pairs_relocated_in_published_raw_source': True,
        'source_filter_bias_and_symmetry_handling': source_meta['source_filter_bias'],
        'published_source_root_WDL_independently_verified': True,
        'test_project_NN_outputs_inspected_before_freeze': False,
        'old_hard_subset_not_applied_to_new_data': True,
        'input_shape': '[B,112,8,8]', 'network_computation_graph_changed': False,
        'network_inference_or_INT8_recalibration_run': False,
        'historical_frozen_Step5_Step6_unchanged': True,
        'script': artifact(Path(__file__))}
    save(PROJECT / 'environment/week1-input-refresh.json', report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['source', 'acquire', 'build', 'verify'])
    args = parser.parse_args()
    globals()[args.action]()
