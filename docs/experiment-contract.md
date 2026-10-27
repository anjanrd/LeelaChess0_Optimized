# BT3 INT8 experiment contract

Version: 1.6 | Latest decision date: 2026-10-25 | Owner: Person A

Version 1.1 records the Step 3 download identity and metadata observations. Experimental choices are unchanged; toolchain execution is verified separately.

Version 1.2 records Step 4's verified encoding boundary and pilot artifacts. The original history-fill and metric choices are unchanged.

Version 1.3 recorded the initial Step 5 export attempt: FP32 conversion passed, but the original FP16 graph failed the frozen WDL numerical gate on a pilot position through both CUDA and TensorRT. Step 5 was unverified at that checkpoint; neither the FP16 baseline nor its acceptance bounds changed. See `docs/onnx-validation.md` and `environment/step5-verification.json`.

Version 1.4 records the user's final two-baseline choice: R32_CUDA is FP32 ONNX through ONNX Runtime CUDA with TF32 disabled, using FP32 CUDA-core matrix computation. F16_TRT is FP16 ONNX through TensorRT with actual FP16 Tensor Core multiplication on eligible matrix operations. FP32 accumulation is permitted; converting matrix multiplication itself to FP32 does not satisfy F16_TRT. Sensitive nonmatrix operations may use disclosed FP32 computation. `environment/step5-baselines.json` is the machine-readable specification. CUDA FP16 and native CPU are diagnostics, not additional required baselines. Existing numerical limits remain unchanged. The user also left node budgets open and selected a one-second wall-time condition for later search evaluation. These choices do not imply Person B's approval.

Version 1.5 recorded verified baseline definitions, diagnostic scope, engine preservation/reload and actual kernel execution evidence from autonomous 5A-5D work. The first constrained FP16 engine passed 86 development cases but failed the original WDL bound on one of 128 fresh confirmation positions (1.9593 percentage points versus 1.5). One universally applied, predeclared FP32-accumulation revision still used actual FP16 Tensor Core multiplication but failed on a development case. Acceptance was unresolved at that checkpoint; no bounds changed.

Version 1.6 records the user's explicit acceptance of the first preserved FP16 engine with documented drift. Its exact SHA-256 is `4271981b85fb44dd1171a8b49cd999626cd9662f184d3f347a8f7bc4b08b8363`. The raw confirmation report remains failed, the original limits remain unchanged, and the exception applies only to this engine and its observed discrepancy. Restored outputs match the archived outputs exactly. Step 5 is complete with documented drift after the 5G integrity, pilot timing and artifact freeze checks. Initial pilot host/CUDA clocks disagreed; the repeat agreed within 1.1%. Final benchmarking must validate timing clocks under its measurement conditions. Step 6 has not started. Evidence: `environment/step5-acceptance.json`, `environment/step5-final-manifest.json`, and `docs/onnx-validation.md`.

This is the Step 2 decision record with subsequent versioned implementation observations. It defines the experimental choices separately from their verification evidence. Quantization, training and lc0 GPU integration are still later work. Team consolidation is deferred; this document does not imply Person B has approved it.

## 1. Question and boundaries

For one fixed BT3 checkpoint on the RTX 4060 Laptop GPU, measure (A) changes to network outputs, (B) search accuracy at equal node budgets, and (C) accuracy at equal actual time. The principal question is whether acceleration compensates for quantization damage. Improvement is a hypothesis, not an acceptance requirement.

Person A's Week 1 scope is model preparation, a pilot INT8 artifact, data splits, FP16 network-level baselines, activation statistics, and bounded PyTorch-conversion feasibility. Full benchmarking, matches, energy, and engine profiling remain Person B responsibilities. Person A completion and the joint C1 gate are distinct.

## 2. Selected checkpoint and execution environment

| Field | Decision |
| --- | --- |
| Checkpoint | `BT3-768x15x24h-swa-2790000` |
| Published architecture | 768 embedding width, 15 transformer blocks, 24 attention heads |
| Source | Lc0's official Best Networks page [1] |
| Weights URL | `https://storage.lczero.org/files/networks-contrib/BT3-768x15x24h-swa-2790000.pb.gz` |
| Remote artifact size | 190,937,780 bytes, observed through HTTP range GET on the decision date |
| File fingerprint | Compressed SHA-256: `e3067757d1fc2dfc66947b21d15ace0cedf4c54254fc1de83d77c378a3e8b8e1`; computed after download, with gzip integrity checked |
| Hardware | RTX 4060 Laptop GPU, 8,188 MiB reported VRAM; Ryzen 7 7840HS; approximately 32 GB host RAM |
| Development environment | Existing Ubuntu 22.04.5 LTS under WSL 2; Python 3.10.12 is present |
| Observed resources | WSL currently sees approximately 15.3 GiB RAM; C: has approximately 585 GiB free |

Rationale: this is a published BT3 rather than a different network family. Lc0 lists approximately 2.6 GB GPU usage for it, which supports starting with the 8 GB GPU but does not establish TensorRT workspace, calibration, large-batch, or training memory requirements. Verify architecture and network-format metadata from the actual weights after download. A failed download or memory test does not authorize silently switching checkpoints.

In Step 2, HEAD returned HTTP 403; a range GET returned HTTP 206, the gzip signature, and total size. In Step 3, the complete file was acquired, its size and gzip integrity were checked, and its SHA-256 was computed. This establishes a reproducible local identity; it is not a publisher-authenticated checksum unless an independent published digest is obtained.

The pinned lc0 loader reports: 15 encoders, 24 heads, embedding size 768, FFN width 1024, `INPUT_CLASSICAL_112_PLANE`, `POLICY_ATTENTION`, `VALUE_WDL`, and `MOVES_LEFT_V1`. The input embedding is `INPUT_EMBEDDING_PE_DENSE`; activation is Mish. Stored weights use `LINEAR16` encoding, which must not be confused with the later FP16 inference/export setting. The loader reports the attention body with multihead format.

## 3. Software and conversion contract

- Source target: lc0 `v0.33.0-rc0`, commit `9f45ea446baf9ce55e299250cde3053b7e93a035` [2]. It is a release candidate, not a final v0.33 release. Preserve the commit even if tags move.
- The targeted commit contains `leela2onnx`, FP32/FP16 export options, `onnx2leela`, and onnx-trt INT8 controls. Export defaults to FP32: FP16 must be requested explicitly [3].
- Use the same source commit and checkpoint for the reference export, FP16 export, wrapper metadata, and later runtime comparisons.
- Step 3 selected and verified TensorRT 10.9.0.34, ONNX Runtime GPU 1.22.0, PyTorch 2.8.0 with CUDA runtime 12.8, ONNX 1.21.0, and ModelOpt 0.47.0 on Python 3.10.12. This retains the plan's ORT <= 1.26 constraint. Complete resolved dependencies are in `requirements/step3.lock`; execution evidence is in `environment/step3-verification.json`. Do not equate the driver's advertised CUDA 13.1 support with an installed toolkit or a mandated toolkit version.
- Start from exporter-supported opset 17. If ModelOpt requires a newer opset, explicitly convert and validate the graph, and derive both compared FP16 and INT8 artifacts from a consistent validated graph. Record final opset and IR versions.
- FP16 backend starting configuration is `optimize=6`; INT8 is `optimize=8`. These enable backend capabilities, not proof of actual kernel precision. Preserve actual engine settings and inspect execution later [4].
- `--onnx2pytorch` exists, but only requests ONNX layer definitions friendlier to the separate conversion package, notably an alternate LayerNorm implementation. It does not export a trainable PyTorch module directly. That conversion and its parity checks remain a bounded Week 1 task [3].
- Engine caches are derived local artifacts, not portable model identities. Record their source graph, checkpoint hash, software versions, device, batch profile, and build settings.

## 4. Input and output semantics

- Exported input is `[B, 112, 8, 8]`, with dynamic batch initially. Lc0 performs the transformer's internal square-token conversion. Do not substitute a hand-written `[B, 64, 768]` input [5].
- Treat the downloaded checkpoint's input-format enum as authoritative. Preserve it in the lc0 wrapper instead of accepting wrapper defaults. Inspect actual metadata in Step 3.
- Use lc0's pinned encoder and move mapping as the reference, including side-to-move orientation, any canonical transform, castling/repetition planes, and rule-50 scaling [6].
- For standalone FEN experiments, initialize history from the FEN with history fill `no`; do not invent earlier moves. For genuine game histories, preserve actual history up to the supported eight positions. Apply the same convention to both precisions and to raw-policy/search comparisons.
- Step 4 found that the stock Python `GameState.as_input()` hard-codes `fen_only`. Use the project native encoder bridge for explicit `no`; it calls the unchanged pinned lc0 implementation. En-passant information can legitimately imply one previous pawn position even with `no`. Exact plane/index verification and the raw classical rule-50 convention are documented in `docs/input-contract.md`.
- For sampled standalone positions, set halfmove clock to zero, fullmove number to one, and no castling or en passant rights. Synthetic history is a declared dataset limitation. Game-based experiments retain their genuine state and history.
- Select `vanilla` policy and `winner` value heads. Expected policy output is 1,858 logits, with legal moves selected through the encoder's actual transform. Confirm WDL/auxiliary head availability and output names from the artifact.
- Network-level policy distribution: mask illegal moves, convert logits to FP32, and apply stable softmax over legal moves with temperature 1.0. Top-move ties are resolved by lexical UCI move order. Terminal positions are tested separately and excluded from ordinary policy metrics.
- WDL order is win/draw/loss from the side-to-move perspective, subject to verification against the reference. Define scalar value as `v = p(win) - p(loss)`.
- Preserve and record the moves-left head if present. A later policy/value swap must control auxiliary outputs rather than silently changing them as well.

## 5. Precision variants

W8A8 means signed 8-bit weights and activations for the selected quantizable operations, represented by explicit Q/DQ. It does not mean every graph operation executes in INT8. Keep normalization, softmax, and unsupported operations in the validated floating-point precision; report coverage. TensorRT supports per-tensor INT8 activation scales and per-tensor/per-axis weight scales [7].

| ID | Variant | Controlled change |
| --- | --- | --- |
| R32_CUDA | FP32 ONNX / CUDA EP | Numerical reference plus separately reported FP32 performance baseline; TF32 disabled |
| F16_TRT | FP16 ONNX / TensorRT | Optimized FP16 baseline; verified FP16 Tensor Core matrix computation, with permitted FP32 accumulation and disclosed nonmatrix exceptions |
| I1 | Naive W8A8 PTQ | Per-tensor weights; max calibration; sampled legal calibration positions, not random tensor noise |
| I2 | I1 + per-channel weights | Change weight scaling granularity only |
| I3 | I2 + improved calibration | Compare max with entropy on validation; choose lower mean policy KL, then lower value MAE if tied; retain max as I2 if entropy does not help |
| I4 | I3 + SmoothQuant | Choose smoothing strength on validation; require numerical equivalence before quantization and correct handling of shared tensor consumers |
| I5 | I4 + search-aware calibration | Replace calibration inputs with training-pool search-visited positions, keeping calibration count controlled |
| I6 | I5 + QAT, optional | Fake-quantization fine-tuning; training data and losses must be registered before training |
| I7 | I6 + distillation, optional | Add FP16 teacher targets; teacher outputs are references, not exact truth |
| S0 | Magnitude 2:4 + INT8 | Prune eligible FP16 weights along the correct reduction dimension, then recalibrate using the selected dense recipe |
| S1 | SparseGPT 2:4 + INT8, optional | Replace magnitude pruning with compensated pruning |
| S2 | S1 + recovery/KD, optional | Preserve the 2:4 mask during recovery |

Inventory eligible layers in Step 6, then freeze a common quantization placement for the dense ladder. A coverage change is a separate recorded change, not a clean one-factor ablation. Calibration seeds, sample counts, and preprocessing stay fixed except for I5's stated input-source change. Tune only on validation, with a declared candidate set and tuning budget before each technique is run. Improvements and identical speeds are not assumed.

S0 is an empirical sparse performance probe, not a guaranteed upper bound. Require actual sparse-tactic evidence in the runtime used for a reported result. Sparse branch and training execution belong to later weeks.

## 6. Dataset policy

- Start with four-piece families KQkq, KQkr, KPkp, and KPkr; KQk and KRk can provide separate basic correctness fixtures. Enumerate the exact required WDL/DTZ dependency files, including capture/promotion-reachable material, before acquisition [8].
- Use legal, nonterminal positions, and state the sampling distribution. Primary scored roots are theoretical wins or draws. Report wins/draws and material families separately; a balanced benchmark does not estimate their natural frequency in games.
- Keep calibration, validation, and test sets disjoint. Group valid symmetry equivalents before splitting, preserving pawn direction and color semantics. Search-aware calibration originates only from the training pool; reject overlap with validation/test identities and group shared trajectories where applicable.
- Initial planning sizes: 64 pilot positions; 1,024 calibration positions; 2,048 validation positions; 10,000 test positions. Seed: 20261021. Target equal material/outcome cells where feasible and disclose actual counts. These are starting sizes, not a statistical-power claim.
- Step 8 may adjust counts following a runtime/coverage pilot. Record the reason and final manifest before evaluating any INT8 variant on the final test set. Do not enlarge or redefine the test because a desired effect fails to appear.
- Keep pilot identities out of the final test. Save manifests with normalized positions, group IDs, labels, split, generator version, seed, and checksums.
- Step 4's 64 pilot roots and 22 diagnostic fixtures are in `data/pilot/`; `exclusions.json` records 93 groups including supplied historical states. Final-test construction must reject these groups. Pilot tablebase labels are still unknown; no strength result follows from their native-reference outputs.
- Step 5 added 128 numerical-confirmation positions under `data/export-confirmation/`, declared before inference with seed 20261025. After their failed numerical gate they became development diagnostics for the single permitted accumulation revision. Final testing must reject their symmetry groups as well: the union of both exclusion files contains 221 groups. The proposed second confirmation set was not generated because its candidate failed development checks. These datasets have no tablebase labels and are not final experiment tests.
- Report the complete sampled test, a decision-sensitive subset with both preserving and degrading legal moves, and a hard subset separately. Do not replace a representative sample with hard cases and retain the same population claim.
- Hard-subset rule: on decision-sensitive positions define `m = max(P_FP16 over preserving moves) - max(P_FP16 over degrading moves)`. Set threshold tau to its 20th percentile on validation, then freeze it. The test hard subset is `m <= tau`. No INT8 outputs determine membership or the threshold.

## 7. Tablebase correctness convention

Primary scoring is explicitly **theoretical WDL ignoring the fifty-move limit**, matching the motivating game-theoretic question rather than silently mixing two rulesets. Map Syzygy's five categories by sign: +2/+1 -> win, 0 -> draw, -1/-2 -> loss. Cursed wins and blessed losses remain separately tagged. This convention is deliberate; it is not the rule-aware three-class mapping [8].

For root s and legal move a to child s', define `u(a) = -sign(probe_wdl(s'))` in the root player's perspective. Handle checkmate/stalemate explicitly before probing. A move is outcome-preserving if its u(a) equals the root's theoretical WDL. Check consistency against the maximum child outcome. Never count missing tables as draws or silently omit affected moves.

Report cursed/blessed cases separately and disclose that lc0's real search/game rules still include the fifty-move rule. DTZ-optimal rate is secondary and must be implemented with a validated DTZ move-ranking procedure; it is not a smallest-absolute-child-DTZ shortcut. Any later claim about actual fifty-move-rule preservation requires clock-aware DTZ/root probing, respecting rounding and zeroing moves. A bare WDL lookup is insufficient for arbitrary nonzero halfmove clocks [8].

## 8. Network metrics and acceptance gates

| Metric | Definition |
| --- | --- |
| Policy KL | Mean `KL(P_FP16 || P_variant)` over legal moves using log-softmax computations; natural logarithms; temperature 1 |
| Top-move agreement | Fraction with the same legal argmax under the fixed tie rule |
| Scalar value error | Mean absolute error of v against FP16 |
| WDL error | Mean absolute probability error across W/D/L components against FP16 |
| Raw-policy tablebase accuracy | Fraction of outcome-preserving top-policy moves under Section 7 |

Report numerical differences against both selected floating-point baselines. FP16 remains the reference for the primary TensorRT quantization comparison and the previously specified hard-subset definition. Neither floating-point baseline is ground truth. Its self-KL/error being zero is a metric sanity check, not a quality result. Tablebase accuracy is the independent outcome measurement. Save per-position outputs and correctness, not just averages. Use paired comparisons and 95% uncertainty intervals; disclose small error counts and clustering by symmetry/trajectory.

Gate sequence: valid checkpoint identity -> correct encoding -> FP32 reference validation against an independent/native evaluator -> FP16 comparison -> INT8 comparison. Two exports from the same converter alone do not independently prove conversion correctness. Before inspecting held-out results in Step 5, record precision-specific numerical tolerances using development fixtures; investigate and justify changes instead of loosening them to obtain a pass. Raw logit error alone does not establish move-quality damage.

Step 5 used 22 development fixtures before freezing `environment/step5-tolerances.json`, then checked the 64-position pilot. FP32 conversion agreed with fresh native Eigen CPU outputs; FP16 exceeded its WDL bound on `pilot-031`. The pilot is development/debug data, not the final experiment test set; after this investigation it must not be described as untouched. No tablebase accuracy or strength inference follows. Further precision placement or acceptance-rule changes require an explicit recorded decision before affected experiment evaluation.

The subsequent first preserved TensorRT engine passed the 86 development cases but exceeded the WDL-component limit on `export-confirm-073` among 128 fresh positions: 0.019593477 versus 0.015 against native lc0. The user explicitly accepted this engine-specific exception in version 1.6. This does not authorize arbitrary future discrepancies or redefine the raw numerical check as passed. Both floating baselines remain separate measured references; Syzygy move correctness remains an independent later evaluation.

Activation profiling uses calibration inputs only. Record the tensor name, shape, channel axis, and maximum absolute value per channel across batches/tokens/spatial axes. Instrument the same named locations for comparisons. Do not use test activations to choose scales or smoothing strengths.

## 9. Later engine comparisons and scope control

The node-budget sweep remains to be selected, superseding the earlier provisional list. Network-only raw policy is a separate evaluation, not literal UCI `go nodes 0`. The selected fixed-time search condition is one second per root position, including search and NN execution but excluding engine loading/building and prior warm-up. Record actual visits and NN evaluations, actual elapsed time, cache/tree reset policy, batch size, search version/options, and any overshoot. Fixed-node comparisons use matched settings. Timing and energy comparisons run on this same physical device with one experiment workload active. Move scoring uses the selected move's tablebase outcome, not the NN's predicted WDL class; winning-to-draw/loss or drawn-to-loss is an error for the primary W/D roots.

The exact search configuration, time-budget sweep, match protocol, energy instrumentation, and batch tuning are later systems decisions, not claimed as frozen by this Person A contract. Keep lc0 tablebase assistance disabled during model/search tests. A Python MCTS fallback changes the scope of timed claims and cannot silently replace lc0 as equivalent evidence.

Step 2 is complete when this decision record has been source-checked. Step 3 downloads and fingerprints the selected checkpoint and pins the executable environment. Metadata validation is a gate there. Export/parity, full data construction, INT8 execution, and statistical sufficiency remain future verification gates. Changes to frozen decisions require a recorded version/reason and must precede affected final test evaluation.

## 10. Primary sources checked on 2026-10-21

1. [Lc0 Best Networks](https://lczero.org/play/networks/bestnets/) and [transformer architecture background](https://lczero.org/blog/2024/02/transformer-progress/).
2. [lc0 v0.33.0-rc0 release](https://github.com/LeelaChessZero/lc0/releases/tag/v0.33.0-rc0), with the full commit independently checked through GitHub's tags API.
3. [Pinned leela2onnx source](https://github.com/LeelaChessZero/lc0/blob/9f45ea446baf9ce55e299250cde3053b7e93a035/src/tools/leela2onnx.cc).
4. [Pinned ONNX backend](https://github.com/LeelaChessZero/lc0/blob/9f45ea446baf9ce55e299250cde3053b7e93a035/src/neural/backends/onnx/network_onnx.cc).
5. [Pinned ONNX converter](https://github.com/LeelaChessZero/lc0/blob/9f45ea446baf9ce55e299250cde3053b7e93a035/src/neural/onnx/converter.cc).
6. [Pinned encoder](https://github.com/LeelaChessZero/lc0/blob/9f45ea446baf9ce55e299250cde3053b7e93a035/src/neural/encoder.cc) and [wrapper conversion](https://github.com/LeelaChessZero/lc0/blob/9f45ea446baf9ce55e299250cde3053b7e93a035/src/tools/onnx2leela.cc).
7. [NVIDIA quantization schemes](https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/quantized-types-schemes.html); the selected TensorRT 10.x version's actual support remains the implementation authority.
8. [python-chess Syzygy documentation](https://python-chess.readthedocs.io/en/latest/syzygy.html).
