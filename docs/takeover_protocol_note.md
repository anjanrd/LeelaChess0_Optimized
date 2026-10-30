# Procedural diff for the takeover runners

30 October 2026. Authorized scope: new autonomous Run 1 preparation for the accepted five-run plan. No GPU experiment was authorized or performed in this run.

## Scientific definitions preserved

The BT3 checkpoint, selected alpha0.7/percentile99.999 recipe, encoding/history convention, datasets, primary2437-ID cohort, WDL/DTZ move scorer, network/fixed-node/timed results, model bytes and sparse masks remain unchanged. No edits were made to `ladder.py`, `common.py`, `quant/`, `eval/` or `hw/`; all350 frozen original files still match. No new model/calibration/selection branch was introduced.

Study B remains Threads1/Minibatch256 with smart pruning off. Study C remains200/800ms on its original configuration/cohort. Existing measurements retain their original conditions; new quiet-testbed measurements do not retroactively upgrade historical conditions.

## New hardware measurement conditions

The new performance trials fix a common search MinibatchSize64, using the existing four-point sweep as prior evidence, with the imported benchmark's default thread setting (CLI0 means leave the engine default) and smart pruning. This is a declared hardware operating point for all eight models, not a change to Study B/C or another accuracy-tuning pass. NN batches are32/64/128/256 and are actual backendbench batches; they are distinct from MCTS MinibatchSize.

Headline FP16/s4: five trials each, adjacent alternating model order. Other six models: three trials each, rotated order. Each trial has200 backend batches at each NN batch size, the original first10 fixed halfmove-zero performance FENs, 10000ms requested search per FEN and20ms move overhead. Engine loading, a common minimum30-second wall conditioning phase and warm-up are excluded from measurements; idle power is observed for10seconds before NN work and again before search. Conditioning is not claimed to prove thermal equilibrium. Natural temperature/clocks and actual early stopping/time are recorded. NN/search latency, engine-time nodes/s, wall nodes/s and GPU energy remain distinct fields.

Standalone TensorRT profiles use the same dynamic min/opt/max4/256/1024 and build optimization5. FP16 and s4 use one serialized engine each for64/256 profiles. The FP32 LayerNorm name constraint is a preference and its actual effect must be inspected. Sparse probes compare enable versus disabled using identical sparse ONNX bytes; never force sparsity or modify weights. These standalone builds are not asserted identical to lc0/ORT graph partitioning. Actual lc0 Nsight captures provide independent execution evidence; kernel-name time tags alone are not operation coverage.

Ceilings retain full raw microbenchmark logs, layer evidence and generated test graphs. FP16/INT8 achieved candidates require actual precision inspection. The bandwidth number is effective modeled weight traffic for the imported GEMV-like probe, not measured DRAM bytes or a specification-sheet peak. The legacy roofline's fixed-format/specification fallbacks must not become observed facts in final analysis.

## Match execution and statistics

The new wrapper delegates move selection, wall-clock accounting and adjudication to the unchanged imported `Game.play`. It retains10+0.1,50ms move overhead, imported default threads/batch, no pondering,50 openings/color swaps, normal time forfeits, existing resignation/draw/ply-cap rules and arbiter-only Syzygy at<=5 pieces. One unscored2000ms warm-up per engine precedes match clocks to exclude cold initialization; each game still calls the imported new-game flow.

The two-game estimate is a separate, saved pilot. Production requires a Run3 sizing record declaring its pair count frozen before production; no outcome-based resizing/stopping. Atomic game+PGN envelopes are authoritative; aggregate JSONL/PGN exports are rebuildable. Contracts include models, native executable, imported rules/UCI source, wrapper source, openings and settings. Incompatible/corrupt resumes fail closed.

The imported pentanomial/normal-approximation summary is retained unmodified under `imported_summary`. The wrapper adds a reporting guard: insufficient pairs, zero observed pair variance or normal intervals outside probability bounds do not produce a reportable reliable Elo interval. Repeated openings and approximation limitations stay explicit. This does not silently substitute a new statistical method; final match interpretation is reviewed in Run5.

## Failure and activity controls

Only the exact initial `Unable to open library: nvinfer_plugin_10.dll` failure can take the approved profiling-deferral branch. That does not close R1/F6 or affected T2/T5 work. Other new errors, invalid output, changed artifacts and detected interference preserve BLOCKED evidence and stop. Negative/inconclusive scientific outcomes, such as no sparse tactic selected or no strength gain, remain valid findings.

Windows/driver/security/Codex processes remain running. Identified nonessential user jobs can be stopped after Anjan saves work and starts an exclusive session. Native counters/NVML observations flag app/compute/AC activity and sustained external CPU activity (5% machine CPU for3 successive2-second samples). Their visibility limits and quiet-session observations are recorded; output structure alone is not scientific validity. Normal runs never terminate apps or launch GPU measurements.

## Approved Run 2 continuation v2: Codex orchestration, background flags informational

On 30 October 2026 the user explicitly abandoned manual launching and authorized Codex
to complete Run 2 after disabling the background interference stop. Activity/CPU/app/GPU
flags remain logged but do not block new v2 trials. AC checks, single-GPU-workload locks,
monitoring failures, child exit codes, required numerical outputs and artifact identity
checks remain enforced. No resource flag is erased or used to discard a slow result.

`execution/codex_run2.py` uses a separate continuation manifest/output tree and references
the original 35 verified jobs; it does not rewrite their policy or accept the old flagged
trial retroactively. The original resource guard/controller, model/search commands and
failed manual-launch evidence remain unchanged. Remaining jobs run in the original order.
New receipts identify this approved policy/session. Codex activity is not assumed identical
across trials; Run 3 must review cross-session temperature, clocks, variability and energy
telemetry before pooling results or claiming a controlled speed/strength improvement.
