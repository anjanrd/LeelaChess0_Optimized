# Step 4: trusted BT3 inputs and pilot positions

Status: passed on 2026-10-21. Evidence: `environment/step4-verification.json` and `environment/step4-bridge.json`.

## Objective and intuition

Make sure a chess position becomes the intended model input, and that an output index becomes the intended legal move. An encoding or mapping error can otherwise look like damage caused by INT8. This step establishes the input/output boundary before any ONNX export.

The checkpoint uses `INPUT_CLASSICAL_112_PLANE` (enum 1). Each input is a C-contiguous float32 array with shape `[B,112,8,8]`. A later FP16 export will receive the same values cast to its declared input dtype.

## Plane layout

The first 104 planes are eight history slots of 13 planes each, newest first. Every slot is oriented to the **current** player, including historical boards.

| Planes | Meaning |
| --- | --- |
| `13*t + 0..5` | Current player's pawn, knight, bishop, rook, queen, king positions at history slot t |
| `13*t + 6..11` | Opponent's corresponding piece positions at history slot t |
| `13*t + 12` | All ones if that historical position occurred previously in the supplied game history; otherwise zero |
| 104 / 105 | Current player's queenside / kingside castling rights, each broadcast over the board |
| 106 / 107 | Opponent's queenside / kingside rights |
| 108 | All ones when the current player is Black; zero for White |
| 109 | Raw halfmove-clock value, broadcast over the board; **not divided by 100** for this input format |
| 110 | Zero |
| 111 | One |

Within a plane, bit 0 / array `[0,0]` is a1 in the mover-oriented coordinates; bit 7 is h1. For Black to move, ranks are reflected and colors are assigned to our/their channels. Files are not reversed. This indexing is not a conventional chess diagram's top-to-bottom rank order.

Missing history uses `no`, not repeated copies of the FEN. For the 64 pilot FENs, slots 1 through 7 are all zero. Genuine supplied move sequences retain up to eight real states. An explicit en-passant flag lets lc0 infer one predecessor by undoing the known double pawn push; the diagnostic checks cover this native exception. Pilot endgame roots have no EP flag.

## Why there is a native bridge

The pinned Python binding's `GameState.as_input()` hard-codes `FillEmptyHistory::FEN_ONLY`. It cannot select our contracted `no` setting. The difference was observed on a pilot FEN, and the binding's output was separately checked against native `fen_only`.

`src/native/encoder_bridge.cc` calls the unmodified pinned lc0 encoder with the requested history mode. It is linked against the already-built lc0 objects, replacing only the executable's main object. The vendor checkout remains clean. Its compiled binary and object files stay under Ubuntu's development directory, outside this project.

`scripts/lc0_inputs.py` supplies an independent python-chess-based interpretation of all 112 planes. Its dense arrays must match the native bridge exactly. Saved pilot tensors come from the native bridge after that comparison, not from an unchecked reimplementation. This helper is deliberately restricted to this checkpoint's classical input format; canonical formats require their own validated handling.

## Policy and value conventions

- Policy has 1,858 logits. An independently enumerated policy vocabulary matched all 1,858 native entries, and native legal move sets/indices matched python-chess on every case.
- Castling's policy key points to the rook square even though the returned standard UCI move points to the king's destination. Do not index it by an unadjusted UCI string.
- Knight promotions use the ordinary from/to slot. Queen, rook, and bishop promotions use their explicit extra slots. Both colors and capture promotions are covered.
- Mask illegal moves, compute stable softmax over legal logits in float32 at temperature 1, and choose the highest probability. Exact ties use lexical UCI order. Illegal logits cannot win even if numerically much larger than legal ones.
- Positions with no legal moves have no legal policy distribution; checkmate/stalemate are handled separately. Invalid shapes and nonfinite logits are rejected.
- WDL order is win/draw/loss, from the side-to-move perspective. Native lc0 exposes `q=W-L` and `d=D`; reconstruct `W=(1-D+q)/2` and `L=(1-D-q)/2`. A Black-to-move q is not automatically a White-perspective score.
- Preserve the moves-left output. Finite, nonnegative native values were checked; it is not a tablebase distance-to-zero label.
- Native `p_softmax` uses approximate `FastExp`. The standard float32 NumPy softmax remains our metric definition. The diagnostic comparison allows absolute 0.0003 / relative 0.003 error for that approximation; these are **not** the future ONNX/FP16 parity tolerances.

## Pilot artifacts

| File under `data/pilot/` | Purpose |
| --- | --- |
| `positions.jsonl` | 64 fixed legal, nonterminal four-piece positions with at least two legal moves |
| `fixtures.jsonl` | 22 cases covering history, repetition, castling, promotion, EP, rule-50 values, terminals, and a forced evasion |
| `inputs.npz` | Native-verified `planes` array `[64,112,8,8]` and matching `ids`; load with `allow_pickle=False` |
| `native_reference.npz` | Native Eigen CPU policy logits, reconstructed WDL, and moves-left for eight selected pilot IDs |
| `exclusions.json` | 93 symmetry groups covering pilot/fixture positions and supplied historical states; reject from the eventual final test |
| `manifest.json` | Seed, material/side counts, input convention, checkpoint identity, and artifact hashes |

Seed: 20261021. Each of KQkq, KQkr, KPkp, and KPkr has eight White-to-move and eight Black-to-move positions. Standalone pilot roots have halfmove clock 0, fullmove number 1, and no castling or EP rights. Diagnostic fixtures intentionally exercise cases outside those restrictions.

Symmetry grouping ignores move counters but includes board, side, castling, and EP state. It uses color/rank mirror only when castling rights exist; horizontal reflection plus color/rank mirror when pawns exist; and the full eight spatial square symmetries plus color/rank mirror for pawnless positions without castling/EP. Identity checks passed under the applicable transformations. Final splits are still constructed in Step 8.

No tablebases have been acquired in this step. `tablebase_label: null` means unknown, not draw. These pilot positions are for compatibility and debugging, not a statistically representative strength evaluation.

## Verification results

- 86 positions checked: 64 pilot plus 22 diagnostic fixtures.
- All 112 input planes matched the pinned native encoder exactly: maximum difference 0.
- 1,194 legal move-to-policy-index mappings checked; complete 1,858-entry vocabulary matched.
- Coverage included all four promotion types, both colors, EP, castling, repetition, raw halfmove clock 99, checkmate, stalemate, and a one-move evasion.
- Eight actual BT3 native CPU evaluations produced finite policy logits, normalized legal probabilities, valid reconstructed WDL, and finite nonnegative moves-left outputs. Their outputs are saved as development references, not playing-strength results.
- The checkpoint SHA-256 and native bridge binary/source identity were rechecked.

## Reproduce

From PowerShell, run the two commands in sequence:

```powershell
wsl -d Ubuntu-22.04 -- /home/anjanrd/.local/share/lc0-int8/venv/bin/python /mnt/c/Users/HP/Desktop/LC0/scripts/build_encoder_bridge.py
wsl -d Ubuntu-22.04 -- bash -c 'OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 /home/anjanrd/.local/share/lc0-int8/venv/bin/python /mnt/c/Users/HP/Desktop/LC0/scripts/prepare_pilot.py'
```

The builder requires Step 3's lc0 build objects. The preparation script verifies the bridge identity, checks the complete input/output boundary, and records results. It refuses to silently change existing pilot IDs/FENs/move histories. Temporary build output remains outside the project.

The primary source is the pinned lc0 commit: [encoder](https://github.com/LeelaChessZero/lc0/blob/9f45ea446baf9ce55e299250cde3053b7e93a035/src/neural/encoder.cc), [Python binding](https://github.com/LeelaChessZero/lc0/blob/9f45ea446baf9ce55e299250cde3053b7e93a035/src/python/weights.h), and [native value interpretation](https://github.com/LeelaChessZero/lc0/blob/9f45ea446baf9ce55e299250cde3053b7e93a035/src/neural/backends/blas/network_blas.cc).

Step 5 remains separate: export the checkpoint, establish numerical tolerances, and validate ONNX/FP16 against the native reference. This step makes no ONNX, INT8, tablebase-accuracy, timing, or strength claim.
