# Run 3 measured findings and evidence limits

30 October 2026; `anjan`; Run 3 source baseline `eb9e8cf8811f2426884d293e780a55d68240be48`. This run analyses saved measurements on CPU, prepares publication outputs and a fresh reproduction workspace, and freezes match size. It launches no GPU inference, chess experiment or production match. Run 2 raw data, failed attempts, model bytes and scientific code remain unchanged.

## Repeated lc0 performance

Source: the 35 original verified jobs plus ten approved-policy continuation jobs. The old resource-flagged trial and failed manual launcher are preserved and excluded. All eight models use the common measured search configuration; FP16 and s4 have five trials each, the other models three. See [trial data](../tables/T2-speed-trials.csv), [summaries](../tables/T2-speed.csv), [NN batches](../tables/T2-network-batch-summary.csv) and [session review](../tables/T2-session-review.csv).

| Model | Median visits/s | Median batch-64 NN latency, ms | Raw preserving moves / 2,437 |
|---|---:|---:|---:|
| fp16 | 4,842 | 18.08 | 2,431 |
| s1 | 6,946 | 12.20 | 2,424 |
| s2 | 7,436 | 12.18 | 2,427 |
| s3 | 7,111 | 12.18 | 2,431 |
| s4, selected before these measurements | 6,818 | 13.04 | 2,431 |
| s4aa | 5,956 | 14.48 | 2,431 |
| s0, magnitude pruning | 3,775 | 13.07 | 1,958 |
| s1sp, SparseGPT | 5,316 | 12.99 | 2,415 |

s4's median search throughput is **40.81% higher** and batch-64 network latency **27.88% lower** than FP16. The headline trial ranges are 4,820–4,952 and 6,745–6,908 visits/s. These are observed repeats with min/max, IQR and standard deviation, not independent-trial confidence intervals. The NN-only batch measurements and search NPS are distinct workloads. Batch 32 gives the smallest measured full-batch latency among 32/64/128/256; this is not a claim of globally optimal batching or best search latency.

The original/v2 session median NPS is 4,847/4,837.5 for FP16 and 6,755/6,826.5 for s4. The s4 session change is about 1.06%, much smaller than the observed headline difference, but does not prove absence of confounding. Median trial mean temperatures are approximately 84.4/85.2 C, with floating SM clocks around 2.23/2.27 GHz. Clock locking was denied; AC and the recorded Windows power mode were retained. Background flags were informational in v2 under explicit user approval. Codex bursts are not assumed identical across trials.

## Actual precision, fusion and sparse execution

[T2 operation mapping](../tables/T2-operation-precision.csv) uses exact original ONNX names in TensorRT inspector metadata, preferring a unique GEMM region. Ambiguous/missing names remain unresolved. [Layer times](../tables/T2-engine-layers.csv) count each engine region once, including fused regions; they are not duplicated across source operations.

The active graph has **195 matrix operations: 164 fixed-weight and 31 dynamic-input multiplications**, with 9,078,490,112 arithmetic operations (4,539,245,056 MACs) per position. In the standalone s4 engine, all 164 fixed-weight operations map to GEMMs with INT8 inputs and actual `i8…i32` tensor tactics. Their arithmetic represents **97.8517% of matrix work**. This percentage is neither a fraction of stored parameters nor all-operation/runtime coverage. One remaining mapped policy multiplication uses FP16; **30 attention matrix operations are unresolved in inspector metadata**. FP16 metadata maps all 195 operations, but fused internal precision remains opaque where not explicitly exposed. Do not label those internals from boundary tensor formats.

All eight saved lc0 traces were exported to new SQLite files, with source/export hashes, on CPU. Name-tagged INT8 and FP16 execution is visible; whole-capture kernel-time fractions include startup/warm-up and cannot establish per-operation coverage. Standalone trtexec layer mappings describe those engines, not an uninspected internal lc0 engine. See [export verification](../../reports/takeover/run3/kernel-export-verification.json).

[T5](../tables/T5-sparsity.csv) proves **126 magnitude and 125 SparseGPT selected sparse GEMM tactics**, versus zero in their dense counterparts. The legacy saved `sparse_layers_reported=0` was a narrow regex summary; it is not the actual selected-tactic count and is preserved unchanged. At batch 256, standalone non-profile GPU times are 57.9641/53.8161 ms (dense/sparse magnitude) and 57.4444/53.8747 ms (SparseGPT), about **1.077×/1.066×**. These are single build/configuration observations, not repeated significance tests. The lc0 benchmark did not enable the standalone sparsity flag; no lc0 sparse acceleration claim follows.

## Profiles and roofline

[F6 data](../tables/F6-roofline-points.csv) includes 496 directly attributed, single-matrix GEMM observations for FP16/s4 at batches 64/256. Packed/opaque fused work is excluded from the point plot and remains visible in the profile breakdown. TensorRT profile sums include profiler overhead; separate non-profile engine times are in [T2](../tables/T2-standalone-profiles.csv). Normalization/softmax categories can include attention fusion and are not pure normalization cost.

Measured GEMM reference rates are 48.92 TFLOP/s FP16 and 108.72 integer TOP/s INT8. The bandwidth microbenchmark models weight traffic at 248.71 GB/s. Arithmetic intensity uses visible logical matrix inputs/weights/output bytes; **these are not measured DRAM transactions**. Reference microbenchmarks and layers differ in shape, clocks, accumulation and fusion; the lines are not universal hardware ceilings. Thirty-nine points exceed this empirical reference and remain plotted, rather than clipped or concealed. The result supports a qualified first-order systems analysis, not a measured cache/dataflow explanation or proof the entire model is memory/compute bound.

## GPU energy: new measurement limitation

Review of raw activity logs found **49 implausible power samples across 23 of 28 trials**, typically approximately 590 W during inactive phases on the 120 W-cap laptop GPU. This corrects the earlier interpretation that the preflight anomaly was isolated. Historical logs and summaries are preserved.

Under measured search load, energy-counter average power and sampled means agree within **0.5983%**, with plausible 80.67–91.79 W means and a maximum sampled 102.027 W. Total GPU energy per visit has medians **17.3372 mJ FP16 / 12.7155 mJ s4**. This is internal NVML consistency, not independent physical-meter validation.

The separately measured counter-derived idle baseline is plausible (about 40–47 W), but its instantaneous cross-check is unreliable. Therefore the reported above-idle medians **8.4357 / 6.2434 mJ** remain **provisional**. [T3](../tables/T3-energy.csv) and F7 retain total and above-idle values and disclose the distinction. A controlled three-window idle check is prepared for exclusive Run 4; even a successful new check cannot retroactively prove every old idle baseline. An unresolved idle check permits timing/matches to proceed with this documented energy limitation. No CPU/whole-machine energy or equal-energy accuracy claim is made.

## Canonical timed results and quality

[T6](../tables/T6-timed-canonical.csv) is recomputed from original Study C rows and exactly reproduces the earlier matched review. It scores exactly the same 2,437 IDs per condition; extra historical rows remain preserved. [Per-root observations](../tables/T6-timed-positions.csv) retain actual nodes and elapsed time.

| Nominal budget | Correct FP16 / s4 | Mean visits FP16 / s4 | Mean wall ms FP16 / s4 |
|---|---|---|---|
| 200 ms | 2,436 / 2,437 | 3,711.26 / 3,768.61 | 184.35 / 183.83 |
| 800 ms | 2,437 / 2,437 | 14,975.07 / 18,084.29 | 606.42 / 594.68 |

There is only one discordant 200 ms outcome (exact paired p=1), and both models saturate at 800 ms. Mean visits improve 1.55%/20.76%; distributions are skewed and actual search often stops early. These settings/roots differ from throughput benchmarks, so these ratios need not equal the 40.81% benchmark gain. **Improved fixed-time accuracy is not established.** WDL-head numerical drift, selected-move correctness and playing strength remain different measurements.

The earlier 43-root hard-subset result has one adverse s4 result at 200 requested nodes (42 correct versus FP16's 43, p=1). Magnitude pruning has large raw/search losses and its search throughput is about 22% below FP16 despite faster NN-only inference. SparseGPT also loses quality. Extending attention quantization (s4aa) is slower than s4 without an aggregate raw-quality gain. These contradict blanket claims that every quantization/pruning variant improves the entire chain. They do not erase the selected dense s4 throughput gain.

F11 compares raw-policy preserving-move quality with independently measured search throughput, with explicit workload labels; it is not a fixed-time or playing-strength frontier. The 3–5-piece synthetic corpus, near-ceiling accuracy, seven symmetry groups crossing pools (three measured IDs affected), and test-defined hard subset limit generalization. No new recipe or cohort is selected using these results.

## Frozen next work

The production match is **250 complete color-swapped pairs / 500 games**, 50 openings repeated five times, 10+0.1 time control with unchanged imported adjudication/search rules. Size is frozen before production using the two-game duration pilot, not its draw outcomes. Pilot timing predicts 3.746 hours of games; plan **5–6 hours, reserve 7** including fresh GPU builds/checks and demo. Two pilot games provide an uncertain planning estimate. No outcome-based early stopping/resizing is allowed. Final Run 5 statistics must preserve color pairs and account for repeated openings; imported clipped/degenerate CIs are not accepted as reliable uncertainty.

A clean clone at the source baseline, independently created Python environment with 21 exact package pins, and a verified 758,074,355-byte FP16/s4/SparseGPT artifact subset are ready outside the checkout. Existing same-host native tools are reused by hash; no old virtual environment or serialized engine cache was copied. Native/driver caches may still be reused; logs must record actual builds. This is same-host source/Python/artifact reproduction, not a cross-machine or native-tool reinstall test. A separately hashed external driver is declared as an overlay, rather than misattributed to the clean clone's commit.

Run 4's ordered checks are declared in [the manifest](../../reports/takeover/run3/run4-manifest.json): idle telemetry, three 32-root raw/fixed-node checks, numerical comparison, three common-setting benchmarks, three execution captures, sparse profile, systems comparison, then production match and actual demo capture. Raw value/policy limits and the 80–120% performance review band are frozen before execution. Unexplained numerical/performance changes stop for review, not silent retuning. GPU reproduction, production strength, final report/deck/video, full package and C4 remain pending.
