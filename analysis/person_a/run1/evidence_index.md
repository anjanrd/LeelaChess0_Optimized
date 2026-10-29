# Evidence definitions and limitations

The primary cohort is 2,437 test IDs; the hard subset has 43. The adopted scorer maps Syzygy ±1 to draw. Move accuracy tests selected legal moves against saved tablebase categories; KL/top-1/|ΔV| compare NN outputs. The main policy/value measurements are printed lc0 quantities, not full-precision ONNX tensors. Python ORT is CPU preparation; lc0 bundles its own GPU ORT. QDQ placement is intent, not measured precision coverage.

Seven equivalence groups cross dataset splits; measured test IDs affected: **[611, 627, 965]**. Equivalence uses legal file reflection for pawn positions, D8 for pawnless positions and color/rank mirroring; castling restrictions are respected. This matches archived grouping, not a changed scorer. The primary corpus/results remain unchanged. No test roots were removed or tuning performed. A separate exclusion sensitivity would require an explicitly labelled, agreed analysis.

Synthetic decision-sensitive 3–5-piece endgames do not represent general chess play. The hard subset was defined using viewed FP16 test results and is descriptive. Calibration uses mixed random-game/history and tablebase/FEN-only inputs. The actual calibration cross-group IDs are recorded in cohort_audit.json; membership in the calibration pool alone does not prove a root was used to fit scales.

Network drift, search quality at requested nodes, NN latency, search throughput, timed accuracy and match strength are separate claims. Negative or inconclusive findings are valid. R1–R5 handoffs gate only the corresponding measured conclusions.
