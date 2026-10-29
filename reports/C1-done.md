# C1-done review

C1-day1 explicitly approved by user; day-1 summary copied verbatim into LOG.md. Pre-flight dependencies and configured paths verified. No pipeline code/config edited in this turn.

build --only s4, hw --parts bench, and study --models fp16 --limit 50 all exited 0.

| Model | Search nps | Raw batch-256 nps | Search SM mean MHz | Search SM min MHz | Search max C |
|---|---|---|---|---|---|
| fp16 | 4349 | 3176 | 2175.43 | 1875 | 87 |
| native | 4358 | 3067 | 2159.27 | 1725 | 87 |
| s4 | 5685 | 4239 | 2268.68 | 1965 | 87 |

Clock locking was optional and was not attempted. Recorded clocks are shown above. All saved bench and study warning lists were empty.

## Study B sizing

Final progress: `[fp16 B] 50/50  0.94s/item  eta 0.0 min`

This progress measures all budgets 100, 400, 800, 1600 together per position. It is not the 1600-node-only cost.
At the 1600-node budget: mean wall **0.341638 s/position**; mean lc0-reported time **0.340760 s/position**, over 50 positions.
Actual nodes: min 1601, mean 1811.38, max 2200. Threads=1, MinibatchSize=256, SmartPruningFactor=0; test split.

No overnight study size selected and no timing extrapolation made.

## LN outputs

FFN input encoder ln1: 20.0..69.0 before -> 3.2..5.2 after SmoothQuant.
QKV input LN outputs: 4.6..20.4 before -> 3.5..4.4 after.
Smolgen ln1: 2.1..5.4 before -> 2.3..5.2 after.
Head-feeding /encoder14/ln2: 665019.9 -> 124666.6 (max 52.76, median 7.933e-05 before smoothing).
Full per-output ratios: reports/C1_LN_outliers.md. Original: reports/outliers.txt.

## Resume commands (from leela-int8)

`..\.venv\Scripts\python.exe -u ladder.py hw --parts bench` reruns the bench sequence; existing benchmark JSON is not a skip condition.
`..\.venv\Scripts\python.exe -u ladder.py study --models fp16 --limit 50` skips completed position/budget records.

# Top 15 kernels tagged other

Shares are of ALL captured GPU kernel time; labels are name-based inference, not measured operand precision.

| Rank | Total ns | Share | Looks like | Kernel |
|---|---|---|---|---|
| 1 | 447450214 | 6.2223% | non-matmul (name-based) | `__myl_CastMul_0x9698266d4f8a2c42b3ee5030474f1e88_com_vec` |
| 2 | 376231329 | 5.2319% | non-matmul (name-based) | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce7fb8c_com_vec` |
| 3 | 319075746 | 4.4371% | non-matmul (name-based) | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_com_vec` |
| 4 | 302974486 | 4.2132% | non-matmul (name-based) | `__myl_CastMulAddReshTranReshMove_0x0340c5e5be98d9cff14028d435e46a87_com_vec` |
| 5 | 169936666 | 2.3632% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x5670ba801b2de8a2907d63de1165fdb4` |
| 6 | 154229791 | 2.1447% | non-matmul (name-based) | `__myl_CastMulAddReshTranReshMove_0x132535db0b518e0a175a5158bc1b1139_com_vec` |
| 7 | 133882345 | 1.8618% | non-matmul (name-based) | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce7fb8c_vec` |
| 8 | 103491656 | 1.4392% | non-matmul (name-based) | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_vec` |
| 9 | 88060935 | 1.2246% | non-matmul (name-based) | `__myl_MoveReshTran_0x7bfad93cb08ea2697ad4d01ea85ce2ff_com_vec` |
| 10 | 84982118 | 1.1818% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x1fe1cc1fc70208fa1b2cf8ace9d12c4f` |
| 11 | 84982039 | 1.1818% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x7f1aba88ddd93d06bfd656f26231a9bf` |
| 12 | 84979997 | 1.1817% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0xa3cb0d93fdf10f031368b0c1d43bf756` |
| 13 | 84970010 | 1.1816% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x4362f572a7cf6cb4ad2c8c19dbcd894e` |
| 14 | 84967008 | 1.1816% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x188def927c4090eca727b3bc88fcb84c` |
| 15 | 84964450 | 1.1815% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x8e523ab71e8f56bda53303a6b0159433` |

Interpretation: day1.log records s2 as 164 weight nodes + 0 act-act. ladder.py builds s2 with per-channel minmax without --act-act-matmul. The bundled ORT and optimize=8 permit FP16 fallback (README trap 4). Thus the _gemm_mha_v2 entries look like FP16 attention matmuls; this is a contextual inference, not a measured precision. Cast/Mul/Mean/Sqrt/Div/Mish-like, transpose and move kernels are non-matmul even when operating on mixed precision tensors. No classifier or pipeline code changed.

