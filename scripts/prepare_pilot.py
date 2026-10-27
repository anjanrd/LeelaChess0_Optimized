"""Create and verify Step 4 pilot inputs; this does not export BT3 to ONNX."""

import hashlib
import json
import os
import random
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import chess
import numpy as np

from acquire_checkpoint import fingerprint
from lc0_inputs import (BRIDGE, RUNTIME, VOCABULARY, classical_planes, dense_planes,
                        input_object, legal_move_indices, legal_policy, native_encode,
                        replay, wdl_from_qd)

PROJECT = Path(__file__).resolve().parents[1]
SEED = 20261021
FAMILIES = {"KQkq": [(chess.QUEEN, chess.WHITE), (chess.QUEEN, chess.BLACK)],
            "KQkr": [(chess.QUEEN, chess.WHITE), (chess.ROOK, chess.BLACK)],
            "KPkp": [(chess.PAWN, chess.WHITE), (chess.PAWN, chess.BLACK)],
            "KPkr": [(chess.PAWN, chess.WHITE), (chess.ROOK, chess.BLACK)]}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group_id(board):
    # Castling fixes king/rook files. Pawns fix their forward direction.
    if board.castling_rights:
        spatial = [board]
    elif board.pawns or board.ep_square is not None:
        spatial = [board, board.transform(chess.flip_horizontal)]
    else:
        transforms = [lambda bb: bb, chess.flip_horizontal, chess.flip_vertical,
                      lambda bb: chess.flip_horizontal(chess.flip_vertical(bb)),
                      chess.flip_diagonal, chess.flip_anti_diagonal,
                      lambda bb: chess.flip_horizontal(chess.flip_diagonal(bb)),
                      lambda bb: chess.flip_vertical(chess.flip_diagonal(bb))]
        spatial = [board.transform(transform) for transform in transforms]
    variants = spatial + [item.mirror() for item in spatial]
    key = min(" ".join(item.fen(en_passant="fen").split()[:4]) for item in variants)
    return hashlib.sha256(key.encode()).hexdigest()


def sample_board(rng, pieces, side, require_one_move=False):
    for _ in range(100000):
        squares = rng.sample(list(chess.SQUARES), 4)
        board = chess.Board(None)
        board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        for square, (piece, color) in zip(squares[2:], pieces):
            board.set_piece_at(square, chess.Piece(piece, color))
        board.turn = side
        board.halfmove_clock = 0
        board.fullmove_number = 1
        if not board.is_valid():
            continue
        count = board.legal_moves.count()
        if require_one_move:
            if count == 1 and board.is_check():
                return board
        elif count >= 2 and not board.is_game_over():
            return board
    raise RuntimeError("Could not sample a position meeting the criteria")


def pilot_positions():
    rng = random.Random(SEED)
    records, groups = [], set()
    for family, pieces in FAMILIES.items():
        for side in [chess.WHITE, chess.BLACK]:
            added = 0
            while added < 8:
                board = sample_board(rng, pieces, side)
                group = group_id(board)
                if group in groups:
                    continue
                groups.add(group)
                records.append({"id": f"pilot-{len(records):03d}", "family": family,
                                "side_to_move": "white" if side else "black",
                                "fen": board.fen(en_passant="fen"), "moves": [],
                                "symmetry_group": group, "role": "pilot_only",
                                "tablebase_label": None})
                added += 1
    return records


def diagnostic_fixtures():
    cases = []

    def add(name, fen=chess.STARTING_FEN, moves=()):
        cases.append({"id": name, "fen": fen, "moves": list(moves), "role": "diagnostic_only"})

    add("start-white")
    add("start-black", chess.STARTING_FEN.replace(" w ", " b "))
    castle = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    add("castle-white", castle.fen())
    add("castle-black", castle.mirror().fen())
    promotion = chess.Board("1r5k/P7/8/8/8/8/8/7K w - - 0 1")
    add("promote-white", promotion.fen())
    add("promote-black", promotion.mirror().fen())
    add("after-knight-promotion", promotion.fen(), ["a7a8n"])
    add("after-promotion-capture", promotion.fen(), ["a7b8q"])
    ep = chess.Board("7k/8/8/3pP3/8/8/8/K7 w - d6 0 1")
    add("en-passant-white", ep.fen(en_passant="fen"))
    add("en-passant-black", ep.mirror().fen(en_passant="fen"))
    add("after-en-passant", ep.fen(en_passant="fen"), ["e5d6"])
    add("rule50-zero", "7k/8/8/8/8/8/2Q5/K7 w - - 0 50")
    add("rule50-99", "7k/8/8/8/8/8/2Q5/K7 w - - 99 50")
    add("checkmate", "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
    add("stalemate", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    opening = "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7".split()
    add("one-known-ply", moves=opening[:1])
    add("opening-black", moves=opening[:9])
    add("opening-white", moves=opening)
    add("capture-history", moves="e2e4 d7d5 e4d5 d8d5 b1c3 d5a5".split())
    repetition = "g1f3 g8f6 f3g1 f6g8".split()
    add("second-occurrence", moves=repetition)
    add("third-occurrence", moves=repetition * 2)
    forced = sample_board(random.Random(SEED + 1), FAMILIES["KQkr"], chess.BLACK, True)
    add("one-legal-evasion", forced.fen())
    return cases


def must_reject(function):
    try:
        function()
    except ValueError:
        return
    raise AssertionError("Invalid input was accepted")


def main():
    bridge_record = json.loads((PROJECT / "environment/step4-bridge.json").read_text())
    assert sha256(BRIDGE) == bridge_record["binary_sha256"]
    assert sha256(PROJECT / "src/native/encoder_bridge.cc") == bridge_record["adapter_source_sha256"]
    checkpoint = json.loads((PROJECT / "models/source/checkpoint.json").read_text())
    assert fingerprint(PROJECT / checkpoint["relative_path"]) == checkpoint["sha256_compressed"]
    pilot, fixtures = pilot_positions(), diagnostic_fixtures()
    previous_path = PROJECT / "data/pilot/positions.jsonl"
    if previous_path.exists():
        previous = [json.loads(line) for line in previous_path.read_text().splitlines()]
        assert [(r["id"], r["fen"], r["moves"]) for r in previous] == [
            (r["id"], r["fen"], r["moves"]) for r in pilot], "Pilot identities changed; version the dataset explicitly"
    records = pilot + fixtures
    native = native_encode(records)
    native_vocab = json.loads(subprocess.check_output([str(BRIDGE), "vocab"], text=True))
    assert native_vocab == VOCABULARY
    all_planes, move_counts = [], []
    coverage = Counter()
    for record, encoded in zip(records, native):
        board, snapshots = replay(record)
        assert group_id(board) == group_id(board.mirror())
        if not board.castling_rights:
            assert group_id(board) == group_id(board.transform(chess.flip_horizontal))
        if not board.castling_rights and not board.pawns and board.ep_square is None:
            assert group_id(board) == group_id(board.transform(chess.flip_diagonal))
        planes = dense_planes(encoded)
        expected = classical_planes(record)
        if not np.array_equal(planes, expected):
            changed = np.argwhere(planes != expected)
            raise AssertionError(f"{record['id']}: plane mismatch at {changed[:12].tolist()}")
        assert encoded["transform"] == 0
        expected_moves = legal_move_indices(board)
        assert dict(encoded["legal"]) == expected_moves, record["id"]
        assert len(set(expected_moves.values())) == len(expected_moves)
        assert all(0 <= index < 1858 for index in expected_moves.values())
        assert bool(encoded["repetitions"]) == board.is_repetition(2)
        move_counts.append(len(expected_moves))
        all_planes.append(planes)
        for move in board.legal_moves:
            if board.is_castling(move): coverage["castling_moves"] += 1
            if board.is_en_passant(move): coverage["en_passant_moves"] += 1
            if move.promotion: coverage["promotion_" + chess.piece_symbol(move.promotion)] += 1
        if board.is_checkmate(): coverage["checkmate"] += 1
        if board.is_stalemate(): coverage["stalemate"] += 1
        if board.is_check() and len(expected_moves) == 1: coverage["forced_evasion"] += 1
        if expected_moves:
            logits = np.full(1858, 1e6, dtype=np.float32)
            for i, uci in enumerate(sorted(expected_moves)):
                logits[expected_moves[uci]] = 10000 + i / 16
            moves, probs, best = legal_policy(logits, board)
            assert best in expected_moves and best == moves[-1]
            np.testing.assert_allclose(probs.sum(), 1, atol=2e-7)
            assert np.isfinite(probs).all() and np.min(probs) >= 0
            assert legal_policy(np.zeros(1858), board)[2] == min(expected_moves)
        else:
            must_reject(lambda: legal_policy(np.zeros(1858), board))
    for label in ["castling_moves", "en_passant_moves", "promotion_q", "promotion_r",
                  "promotion_b", "promotion_n", "checkmate", "stalemate", "forced_evasion"]:
        assert coverage[label] > 0, label
    for fixture_id in ["rule50-zero", "rule50-99"]:
        idx = next(i for i, r in enumerate(records) if r["id"] == fixture_id)
        assert np.all(all_planes[idx][109] == (99 if fixture_id.endswith("99") else 0))
    for fixture_id in ["second-occurrence", "third-occurrence"]:
        idx = next(i for i, r in enumerate(records) if r["id"] == fixture_id)
        assert np.all(all_planes[idx][12] == 1)
    assert all(np.count_nonzero(planes[13:104]) == 0 for planes in all_planes[:64])
    np.testing.assert_allclose(wdl_from_qd(.75, .15), [.8, .15, .05], atol=1e-7)
    must_reject(lambda: wdl_from_qd(2, 0))
    must_reject(lambda: replay({"fen": "8/8/8/8/8/8/8/8 w - - 0 1"}))
    must_reject(lambda: replay({"fen": chess.STARTING_FEN, "moves": ["e2e5"]}))
    must_reject(lambda: legal_policy(np.zeros(1857), chess.Board()))
    must_reject(lambda: legal_policy(np.full(1858, np.nan), chess.Board()))
    print(f"Exact input-plane and move-map checks passed on {len(records)} positions", flush=True)

    sys.path.insert(0, str(RUNTIME / "build/lc0-tools"))
    import backends
    weights = backends.Weights(str(PROJECT / checkpoint["relative_path"]))
    assert weights.input_format() == 1
    backend = backends.Backend(weights=weights, backend="eigen", options="batch_size=1,threads=2")
    binding_input = backends.GameState(fen=pilot[0]["fen"]).as_input(backend)
    default_native = native_encode(pilot[:1], fill="fen_only")[0]
    for plane, (mask, value) in enumerate(default_native["planes"]):
        assert binding_input.mask(plane) == mask and binding_input.val(plane) == value
    assert not np.array_equal(dense_planes(default_native), all_planes[0])
    for plane in [0, 13, 109, 111]:
        copied = input_object(backends, native[0]).clone()
        assert copied.mask(plane) == native[0]["planes"][plane][0]
        assert copied.val(plane) == native[0]["planes"][plane][1]

    selected = list(range(0, 64, 8))  # One example per material/side cell.
    reference_logits, reference_wdl, reference_mlh, summaries = [], [], [], []
    started = time.perf_counter()
    for index in selected:
        output, = backend.evaluate(input_object(backends, native[index]))
        raw = np.asarray(output.p_raw(*range(1858)), dtype=np.float32)
        board, _ = replay(pilot[index])
        moves, probs, best = legal_policy(raw, board)
        wdl = wdl_from_qd(output.q(), output.d())
        np.testing.assert_allclose(wdl.sum(), 1, atol=1e-6)
        assert np.isfinite(output.m()) and output.m() >= 0
        native_prob = np.asarray(output.p_softmax(*[legal_move_indices(board)[m] for m in moves]))
        np.testing.assert_allclose(probs, native_prob, atol=3e-4, rtol=3e-3)
        reference_logits.append(raw)
        reference_wdl.append(wdl)
        reference_mlh.append(output.m())
        summaries.append({"id": pilot[index]["id"], "top_legal_move": best,
                          "q_side_to_move": output.q(), "draw_probability": output.d(),
                          "wdl": wdl.tolist(), "moves_left": output.m()})
        print("Native CPU output checked:", pilot[index]["id"], flush=True)

    destination = PROJECT / "data/pilot"
    destination.mkdir(parents=True, exist_ok=True)
    exclusion_groups = sorted({group_id(snapshot) for record in records for snapshot in replay(record)[1]})
    exclusions = {"symmetry_groups": exclusion_groups,
                  "identity": "Canonical board/side/castling/en-passant; clocks excluded",
                  "symmetries": "Castling: color/rank mirror only; pawns: horizontal plus color/rank mirror; otherwise full D4 plus color/rank mirror",
                  "required_use": "Reject these groups from the eventual final test set"}
    (destination / "exclusions.json").write_text(json.dumps(exclusions, indent=2) + "\n")
    for filename, rows in [("positions.jsonl", pilot), ("fixtures.jsonl", fixtures)]:
        (destination / filename).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    np.savez_compressed(destination / "inputs.npz", planes=np.stack(all_planes[:64]),
                        ids=np.array([row["id"] for row in pilot]))
    np.savez_compressed(destination / "native_reference.npz", ids=np.array([pilot[i]["id"] for i in selected]),
                        logits=np.stack(reference_logits), wdl=np.stack(reference_wdl),
                        moves_left=np.asarray(reference_mlh, dtype=np.float32))
    files = {name: sha256(destination / name) for name in
             ["positions.jsonl", "fixtures.jsonl", "inputs.npz", "native_reference.npz", "exclusions.json"]}
    manifest = {"seed": SEED, "pilot_positions": len(pilot), "diagnostic_fixtures": len(fixtures),
                "material_side_counts": dict(Counter(r["family"] + ":" + r["side_to_move"] for r in pilot)),
                "input_shape": [64, 112, 8, 8], "dtype": "float32", "history_fill": "no",
                "input_format": "INPUT_CLASSICAL_112_PLANE", "checkpoint_sha256": checkpoint["sha256_compressed"],
                "pilot_and_fixture_exclusion": "Exclude these positions, replayed states, and valid symmetry equivalents from final test",
                "tablebase_labels": "not acquired in Step 4; null means unknown, not draw",
                "files_sha256": files}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    report = {"verified_at_utc": datetime.now(timezone.utc).isoformat(),
              "positions_checked": len(records), "pilot_positions": len(pilot), "diagnostic_fixtures": len(fixtures),
              "native_input_plane_max_abs_difference": 0.0, "native_policy_vocabulary_entries_matched": 1858,
              "legal_move_mappings_checked": sum(move_counts), "special_case_coverage": dict(coverage),
              "input_shape": [64, 112, 8, 8], "history_fill": "no", "native_binding_default_mismatch_detected": True,
              "excluded_symmetry_groups": len(exclusion_groups), "symmetry_identity_checks": "passed",
              "checkpoint_sha256_rechecked": checkpoint["sha256_compressed"],
              "native_bridge_sha256": bridge_record["binary_sha256"],
              "native_binding_fen_only_parity": "passed", "negative_input_guards": "passed",
              "policy_masking_numerical_stability_and_tie_rule": "passed",
              "native_reference_positions": len(selected), "native_reference_backend": "eigen CPU",
              "native_reference_elapsed_seconds": time.perf_counter() - started,
              "reference_outputs": summaries, "manifest_sha256": sha256(destination / "manifest.json"),
              "scope": "Pilot input/output semantics only; no ONNX export, tablebase scoring, or engine-strength claim"}
    (PROJECT / "environment/step4-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Step 4 passed; pilot files and verification evidence saved.", flush=True)


if __name__ == "__main__":
    main()
