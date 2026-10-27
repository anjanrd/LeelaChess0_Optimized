# Step 5: export and numerical validation

Status: **Step 5 complete with explicitly accepted FP16 numerical drift.** R32_CUDA passed its numerical checks. The first preserved F16_TRT engine was accepted by the user on 2026-10-25; its original confirmation report still records the failed bound. Step 6 has not started.

On 2026-10-25 the user authorized autonomous substeps 5A-5G, verifying each before progression. 5A records the final baselines in `environment/step5-baselines.json`: FP32 ONNX / CUDA EP, with TF32 disabled, and FP16 ONNX / TensorRT, with actual FP16 Tensor Core matrix multiplication. FP32 accumulation and disclosed nonmatrix precision exceptions are permitted. CUDA FP16 is diagnostic only. Historical failures below remain evidence; none is erased by this scope clarification. Numerical acceptance bounds have not changed.

## Current checkpoint after autonomous execution on 2026-10-25

Summary: `environment/step5-resume-summary.json`. Ledger: `environment/step5-progress.json`.

- **5A passed:** exact two-baseline definitions, unchanged graph identities, allowed accumulation and hardware requirements recorded.
- **5B passed:** selected-baseline status separated from CUDA-FP16 diagnostics; TF32 evidence is backend-specific; historical outputs/reports preserved.
- **5C passed:** the original cache failure was reproduced on a controlled graph. ORT 1.22 incorporates the graph name `org.lczero/converted` into its default cache filename; the slash introduces a missing intermediate directory, and the source's file-write path does not check success. A safe custom prefix saved the same toy engine successfully. Evidence: `environment/step5-cache-diagnosis.json`. The BT3 baseline runner uses the TensorRT Runtime API directly and explicitly serializes its engine instead. Two fresh processes reload each candidate and produce bit-identical results at the same tested batch sizes, without invoking a builder.
- **5D passed:** CUPTI kernel traces show executed strict-FP32 SGEMMs for R32_CUDA and FP16 `tensor16x8x16` GEMMs for F16_TRT. Engine inspection and execution traces accompany the settings. PyTorch only allocates/copies buffers and owns streams/profiling; TensorRT executes the network. No performance-counter permissions or new profiler installation were needed. This is actual kernel-name/tactic evidence, not a Tensor Core utilization counter or a machine-instruction audit of every fused operation.
- **5E passed:** the selected first engine passed all original limits on the 86 pilot/fixture positions. The rejected accumulation revision is retained separately.
- **5F accepted with documented drift:** the user selected the first engine after reviewing its one-position confirmation exception. `environment/step5-acceptance.json` records that decision separately from the still-failed raw confirmation report. The original numerical limits were not edited.
- **5G complete:** restored outputs, including the accepted outlier, are bit-identical to the saved first-engine outputs. Pilot timings, integrity evidence and the final artifact manifest are recorded. Step 6 has not started.

| Preserved candidate | Development result | Fresh confirmation | Actual matrix execution |
| --- | --- | --- | --- |
| **Selected:** `4271981b85fb44dd...` | Passed all original limits on 86 pilot/fixture positions; max WDL difference 0.56 percentage points | One of 128 new positions exceeded the 1.5-point WDL limit: `export-confirm-073`, 1.9593 points. All other numerical/batch gates passed. Top move matched native on 127/128; this is not tablebase accuracy. | FP16 Tensor Core GEMMs with native/FP16 accumulation tactics observed |
| **Rejected:** `524853bcd0d3ee2d...` | A single predeclared global FP32-accumulation revision was checked on all 214 now-known positions. Failed on `pilot-031`: 12.9210-point WDL difference, scalar and legal-probability bounds also exceeded. | Not run: development failed, so no second confirmation data was generated | FP16 Tensor Core multiplication with FP32 accumulation, verified by executed `f16f16_f16f32_f32` tactics; no FP32 SGEMM substitution |

Both engines are around 209 MB and remain in WSL's `step5-preserved/` runtime directory, outside the project. Each candidate's reports are preserved under `environment/step5-history/<engine-hash-prefix>/`. Canonical reports `environment/step5-engine.json`, `step5-precision.json`, `step5-diagnosis.json`, and `step5-confirmation.json` now refer to the selected first engine. Original graph hashes and all numerical limits remain unchanged. The first confirmation's raw data and outputs remain in `data/export-confirmation/`.

The first candidate is numerically stronger on the measured positions and was selected by explicit human acceptance of its known exception. The accumulation revision used TensorRT's documented strongly typed cast-around-GEMM pattern on every matrix operation, not a per-position/per-layer tuning search. Strong typing also changes compiler/fusion/tactic choices, so its worse result does not establish that wider accumulation inherently worsens accuracy. Normalization's explicit compute-precision setter was ignored by TensorRT in strongly typed mode; its default/type-derived behavior applies, and no claim relies on that ignored setter overriding the compiler.

The 128-position confirmation was generated with seed 20261025, with 16 positions per material/side cell, before its inference. Its engine hash, model identities and unchanged limits were fixed in `data/export-confirmation/protocol.json`. After its failure, those positions were disclosed as development data for the one accumulation revision. Any future numerical confirmation must be new and symmetry-disjoint; the never-created second-round plan used seed 20261026. These are numerical checks, not final experiment test data or statistical chess-strength evidence.

Final-test construction must reject the union of `data/pilot/exclusions.json` and `data/export-confirmation/exclusions.json`: **221 groups**. Tablebase labels remain unknown. No Syzygy accuracy, INT8, MCTS, or strength result was produced. The limited runtime timing check below is separate.

The acceptance decision is resolved. It applies to the exact engine SHA-256 `4271981b85fb44dd1171a8b49cd999626cd9662f184d3f347a8f7bc4b08b8363` and its measured exception, not to arbitrary future engines or unseen numerical discrepancies. The maximum WDL-component difference was 1.9593 percentage points against native lc0, versus the original 1.5-point limit. This is a prediction discrepancy; whether the selected move loses a theoretical win/draw remains a later Syzygy measurement. The failed result is not relabeled as a numerical pass.

## Timing sanity check and final records

`environment/step5-timing.json` records warmed inference at batch sizes 1 and 8. Inputs/outputs are preallocated on the GPU for the resident comparison; each host-wall measurement includes API submission and completion. A second boundary includes host-array transfers and float32 host outputs. Build, model loading and warm-up are excluded. Baselines alternate execution order and do not execute concurrently. The Windows power policy was Balanced; GPU clocks/power were not locked.

The final resident host-wall pilot measured about 9.54 ms versus 3.31 ms at batch 1, and 15.21 ms versus 4.04 ms at batch 8, for R32_CUDA and F16_TRT respectively. These are preliminary pipeline checks, not final benchmark claims. In the initial pilot, CUDA-event intervals were approximately 8% longer than synchronized host-wall times; the cause is not established. In the final repeat, the two clocks agreed within 1.1%. Both clocks are saved independently, and final benchmarking must check their agreement under its measurement conditions. Precision and runtime both change in this comparison, so its speed difference cannot be attributed to precision alone. The JSON contains the final repeat's exact samples and clock ratios.

`environment/step5-final-integrity.json` verifies restored-engine outputs against archived results. `environment/step5-final-manifest.json` freezes the selected model/engine, acceptance, bounds, scripts, documentation and evidence hashes. Original source snapshots and runtime traces remain outside the project. The engine binary and reload outputs are intact. The original shared builder timing cache was overwritten by the rejected build; it cannot reproduce the first build. Future builds use hash-specific cache filenames. Reuse the exact serialized engine; a rebuild is not promised to select identical tactics or outputs.

## Objective and intuition

Convert the downloaded lc0 checkpoint into ONNX, a graph that our GPU tools can run. Check how closely the conversion and execution preserve the network's outputs. FP32 is the diagnostic bridge to native lc0 and a separately recorded baseline; FP16 TensorRT is the optimized baseline for the primary INT8 comparison. A working file is not sufficient evidence of numerical agreement.

## Artifacts and identity

- `models/onnx/bt3-r32.onnx`: native lc0 FP32 export, 410,354,293 bytes.
- `models/onnx/bt3-f16.onnx`: native lc0 FP16 export, 205,236,356 bytes.
- `models/onnx/manifest.json`: checkpoint/source identity, graph hashes, arguments, graph structure, and input/output metadata.
- `environment/step5-development-protocol.json`: bounds recorded before development inference.
- `environment/step5-development.json`: 22 development fixtures, including special chess states and two terminal positions.
- `environment/step5-tolerances.json`: bounds frozen after development and before pilot confirmation. They have not been loosened.
- `environment/step5-verification.json`: full pilot results, failures, per-position comparisons, batch checks, and provider execution evidence.
- `data/pilot/onnx_reference.npz`: IDs and native/ONNX outputs, load with `allow_pickle=False`. Native outputs cover all 64 roots; `f32_*` and `f16_*` use CUDA EP; `trt_f16_*` use TensorRT EP.
- `environment/step5-initial-f16-failure.json`: original failure and numerical investigation.
- `environment/step5-tensorrt-diagnostic.json`: separate TensorRT investigation of the same FP16 graph.

Both graphs use opset 17, IR 9, dynamic input `[B,112,8,8]`, policy head `vanilla`, and value head `winner`. Outputs are `/output/policy` `[B,1858]` logits, `/output/wdl` `[B,3]` W/D/L probabilities, and `/output/mlh` `[B,1]` moves-left. Inputs, floating initializers, and outputs use the explicitly requested export dtype. Full ONNX checker/shape validation passed. Neither graph contains Q/DQ.

Source is unchanged lc0 commit `9f45ea446baf9ce55e299250cde3053b7e93a035`, with the Step 3 checkpoint SHA-256. The exporter itself supports these options; no unverified converter substitutes for the FP32/native comparison.

Large ONNX graphs are intended project artifacts, excluded from Git. Native builds, trial graphs, engine caches, and profile scratch stay outside the project, under WSL's development directory or system temporary storage. Trial precision variants were not adopted as baseline graphs.

## Historical EP procedure and frozen gates

First run all 22 diagnostic fixtures through CUDA EP against fresh native Eigen CPU outputs. Compare singleton and batch-4 inference, with terminal policy comparisons excluded. Only after these pass, freeze the gates and check all 64 pilot roots at batch sizes 1 and 8. TensorRT was added during failure investigation, using the same frozen numerical limits. These pilot roots are development/debug data and already excluded from final experiment testing. Their confirmation failed; do not describe them as an untouched holdout after investigating that failure.

ONNX Runtime CUDA EP uses TF32 disabled. Profiles must show actual GPU matrix execution; substantial CPU computation is rejected. TensorRT validation uses the same FP16 graph, batch profile 1/4/8, 512 MiB workspace limit, and `trt_layer_norm_fp32_fallback=true`. TensorRT must appear in executed profile events. These checks do not establish each internal kernel's precision, optimal performance, or playing strength. Backend precision settings and graph dtypes alone are not a kernel audit.

| Per-position check | FP32 gate | FP16 gate |
| --- | ---: | ---: |
| Maximum legal-move probability difference | 0.0002 | 0.015 |
| Legal policy KL, maximum | 0.00001 | 0.003 |
| Maximum WDL component difference | 0.0005 | 0.015 |
| Scalar W-L difference | 0.001 | 0.03 |
| Moves-left absolute/relative tolerance | 0.02 + 0.0002 × reference | 0.5 + 0.01 × reference |
| Singleton/batched legal probability difference | 0.0002 | 0.005 |

Also require finite outputs, valid normalized WDL, nonnegative moves-left, and no top-move flip outside twice the probability bound. Raw logit differences are recorded as diagnostics rather than probabilities. KL uses log-softmax in float64 for stable measurement, with float32 logits and the Step 4 legal-move convention; negative numerical residue is clamped to zero. No tablebase labels are involved.

## Historical findings from 2026-10-21

Both precisions passed CUDA development checks. Pilot results against native lc0 are:

| Runtime/precision | Maximum WDL difference | Top legal move agreement |
| --- | ---: | ---: |
| CUDA FP32, batch 1 | 0.0018 percentage points | 64/64 |
| CUDA FP32, batch 8 | 0.0042 percentage points | 64/64 |
| CUDA FP16, batch 1 | 8.43 percentage points | 64/64 |
| CUDA FP16, batch 8 | 5.82 percentage points | 63/64 |
| TensorRT FP16, final build, batch 1 and 8 | 15.19 percentage points | 63/64 |

All FP32 checks passed. The FP16 WDL/scalar failures occur on `pilot-031`. The final TensorRT build also exceeds the legal-probability bound there. CUDA FP16's WDL outputs differ by up to 2.64 percentage points between singleton/batch-8 runs, failing batch consistency. TensorRT's final-build outputs are identical across those two batch sizes.

That position is `6K1/8/8/8/8/r7/5Qk1/8 b - - 0 1`. Native lc0 reports roughly 54.8% draw / 45.2% loss. The original FP16 graph through CUDA EP reports roughly 63.2% draw / 36.7% loss at batch 1. An initial TensorRT diagnostic showed a 2.0-point WDL discrepancy; a subsequent separately built session showed 15.2 points. Both failed the frozen 1.5-point WDL limit. These observations establish sensitivity across these builds; they do not isolate TensorRT tactic selection as the cause. Engine identities and precision choices must be controlled before accepting a baseline. All these are model predictions, not tablebase truth.

The changed top move is on `pilot-037`, where native top probabilities are separated by only 0.00032. That flip falls within the predeclared near-tie allowance and is not itself a gate failure. It still must be reported; it does not establish chess-strength loss without tablebase labels.

FP32 conversion agrees closely on the problematic position too. Intermediate probes locate substantial error growth near the final transformer block. A diagnostic retaining FP32 arithmetic but rounding all floating weights to FP16 gives roughly a 1.2-point WDL difference. This demonstrates that weight rounding contributes and that the full FP16 arithmetic adds further sensitivity; it does not isolate every contributing operation.

Keeping normalization, softmax and additions in FP32 did not meet the existing limit. A separate candidate keeping the final transformer block in FP32 also missed it under CUDA EP. Neither candidate replaced the intended FP16 graph. Broader mixed precision would change the reference configuration and requires an explicit experimental decision; repeatedly adjusting placement to this position is not independent validation.

The conclusion at that historical checkpoint was a successful FP32 conversion and a demonstrated numerical limitation of the original FP16 execution. It was not evidence of a broken move encoder, an invalid ONNX file, INT8 damage, or a change in chess strength. Work paused for investigation; the later engine-specific acceptance is documented above.

## Historical EP-check reproduction

In the already activated WSL environment, from `/mnt/c/Users/HP/Desktop/LC0`:

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python scripts/export_step5.py export
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python scripts/export_step5.py develop
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python scripts/export_step5.py verify
```

`develop` is for the initial run and refuses to overwrite frozen gates. `verify` repeats the historical EP-based diagnostic, now writing separate current-EP evidence instead of overwriting original files. It is not the preserved-engine acceptance runner. It can rebuild TensorRT and yield different results between builds; use the serialized-engine scripts and records for the resumed work. The original cache failure described here has since been independently explained above.

The resumed scripts are `scripts/step5_engine.py` (explicit build, reload and cross-process checks), `scripts/step5_precision.py` (engine inspection and actual kernel traces), and `scripts/step5_numerics.py` (raw development and confirmation checks). They preserve numerical failures rather than applying the human acceptance exception. Sources used for the first-candidate build/check are archived outside the project under WSL's `step5-preserved/history/4271981b85fb44dd/`.

To verify the accepted baseline, use the activated WSL environment and existing preserved engine:

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 python scripts/finalize_step5.py verify
```

This checks identities, unchanged bounds, acceptance scope, evidence hashes and exact restored outputs, without rebuilding the engine. It updates the integrity report's verification timestamp; if intentionally updating the frozen evidence, rerun `python scripts/finalize_step5.py freeze` afterward. `timing` reruns only the pilot timing check. Retain the accepted `.plan` at the path in `environment/step5-engine.json`, the WSL runtime evidence and pinned dependency environment. No cross-device or cross-version engine portability is claimed. Step 6 remains subject to the user's execution-mode choice.
