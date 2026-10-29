#!/usr/bin/env python3
"""Check quant/lc0_encode.py bit for bit against lc0's Python bindings
(built with lc0-bindings.patch) for every input format.

    python tests/test_encoder.py --lc0-py /path/to/lc0/build --proto /path/to/lc0/proto/net.proto \
        --tbset data/tbset.jsonl --games 300
"""
import argparse
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import chess
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "quant"))
sys.path.insert(0, str(ROOT))
from lc0_encode import encode  # noqa: E402
from make_calib import planes_of  # noqa: E402
from common import read_jsonl  # noqa: E402

FORMATS = [1, 2, 3, 4, 5, 132, 133]


def games(rng, n):
    out = []
    for _ in range(n):
        b = chess.Board()
        mv, last = [], {}
        for _ in range(rng.randint(1, 220)):
            legal = list(b.legal_moves)
            if not legal:
                break
            # bias toward shuffling back, to create repetitions
            back = [m for m in legal if last.get(b.turn) and m.from_square == last[b.turn].to_square
                    and m.to_square == last[b.turn].from_square]
            m = back[0] if back and rng.random() < 0.35 else rng.choice(legal)
            last[b.turn] = m
            b.push(m)
            mv.append(m.uci())
            if b.is_game_over(claim_draw=False):
                break
        while mv and b.is_game_over():
            b.pop()
            mv.pop()
        out.append((None, mv))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lc0-py", required=True)
    ap.add_argument("--proto", required=True)
    ap.add_argument("--tbset", default=None)
    ap.add_argument("--games", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    sys.path.insert(0, a.lc0_py)
    import backends as lb
    rng = random.Random(a.seed)
    cases = games(rng, a.games)
    # FEN-only cases: game positions (castling/ep), halfmove forced to 0, and TB FENs
    for fen_src, mv in list(cases)[: a.games // 2]:
        b = chess.Board()
        for m in mv:
            b.push_uci(m)
        f = b.fen().split()
        f[4] = "0"
        cases.append((" ".join(f), []))
    if a.tbset:
        for r in read_jsonl(a.tbset)[:400]:
            cases.append((r["fen"], []))
    td = Path(tempfile.mkdtemp())
    bad = 0
    for fmt in FORMATS:
        net = td / f"toy_{fmt}.pb.gz"
        subprocess.check_call([sys.executable, str(ROOT / "tests" / "make_toy_bt.py"), "--proto", a.proto,
                               "--out", str(net), "--input-format", str(fmt), "--layers", "1"],
                              stdout=subprocess.DEVNULL)
        w = lb.Weights(str(net))
        be = lb.Backend(weights=w, backend="trivial")
        if be.capabilities().input_format() != fmt:
            be = lb.Backend(weights=w, backend="onnx-cpu")
        assert be.capabilities().input_format() == fmt
        nbad = 0
        reps = 0
        for fen, mv in cases:
            g = lb.GameState(fen=fen, moves=mv) if fen else lb.GameState(moves=mv)
            ref = planes_of(g.as_input(be))
            ref_idx = dict(zip(g.moves(), g.policy_indices()))
            pl, idx, ucis = encode(fen, mv, fmt)
            mine_idx = dict(zip(ucis, idx))
            reps += int(ref[12].any() or ref[25].any())
            if not np.array_equal(ref, pl) or ref_idx != mine_idx:
                nbad += 1
                if nbad <= 3:
                    diff = sorted(set(np.where(ref != pl)[0].tolist()))
                    print(f"  format {fmt} MISMATCH fen={fen} moves={len(mv)} planes={diff[:10]} "
                          f"policy_ok={ref_idx == mine_idx}")
        print(f"format {fmt:3d}: {len(cases) - nbad}/{len(cases)} identical "
              f"({reps} with repetition planes set)")
        bad += nbad
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
