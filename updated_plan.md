# Unified BT3 INT8 project plan

Version 2.0 — 29 October 2026. Owners: Person A (Anjan, model/analysis) and Person B (Ritwik, systems/experiments).

This is the current plan for the shared repository. It supersedes the two earlier roadmaps for future work. The original proposal and plan remain under `archive/person-a-week1/`; the imported pipeline documentation remains under `archive/person-b-import/`.

## Objective and interpretation

Test whether W8A8 inference inside lc0 provides higher throughput and enough additional search to preserve or improve playing quality per second. Faster inference, more nodes, and better accuracy are separate measurements. An unchanged or negative strength result is a valid outcome; completion does not require proving a speedup or strength gain.

Completed work counts toward the project regardless of which teammate produced it. The week labels organize responsibilities and dependencies; they do not require repeating experiments already completed ahead of schedule.

Status definitions:

- **Completed:** the specified output exists in the imported evidence.
- **In progress:** partial outputs exist, but the item is not closed; this includes blocked work and measurements awaiting consolidation.
- **Pending:** no completed output was found.
- **Omitted:** deliberately outside the adopted trimmed scope, not a completed deliverable.

## Adopted protocol and scope

| Item | Current convention |
|---|---|
| Authoritative implementation | The former `LC0-B/leela-int8` pipeline, now at the repository root. |
| Network | BT3 checkpoint SHA256 `e3067757d1fc2dfc66947b21d15ace0cedf4c54254fc1de83d77c378a3e8b8e1`. |
| Baseline | `fp16`: exported ONNX wrapped for lc0, executed with `onnx-trt`, `optimize=6`. The raw BT3 checkpoint on the same backend is a wrapping/reference check, not an independent native-CUDA baseline. |
| INT8 | Signed symmetric W8A8 QDQ from the imported ORT/custom calibration implementation, executed with `optimize=8`; non-INT8 work can remain floating point. Do not describe the whole network as uniformly INT8. |
| Precision evidence | Observed INT8 kernels establish real low-precision execution. Complete per-model precision/fallback and sparse coverage are still pending; kernel-name time fractions are not operation coverage. |
| Data | Existing `data/tbset.jsonl`: 11,200 synthetic legal roots labelled with local 3–5-piece Syzygy tables; calibration/development/test pools 1,120/3,360/6,720. FEN halfmove clocks are zero. |
| Calibration | Existing `data/calib.npz`: 256 random-game inputs plus 256 tablebase inputs. Existing development inputs contain 3,360 positions. Preserve supplied history for random-game calibration and the imported FEN-only convention for standalone roots. |
| Scoring | Preserve the root win/draw outcome. Adopt the imported category mapping: Syzygy +2 is win, -2 loss, and 0/±1 draw. Secondary DTZ-optimal score follows the imported scorer. These are move-selection scores, not WDL-head classification accuracy. |
| Main evaluated cohort | 2,437 selected test roots. Use matching IDs, splits, model variants and conditions in every paired comparison. Do not pool extra historical Study C rows into unequal cohorts. |
| Study A | Raw policy move, approximate policy KL/top-1 from lc0's printed priors, value error, tablebase accuracy and DTZ secondary score. Explain printed-prior precision limits. |
| Study B | Requested budgets 100/400/800/1,600; record actual nodes because batches overshoot. Threads=1, MinibatchSize=256, smart pruning off. Raw network is the budget-0 comparison. |
| Hard follow-up | Existing 43-position subset: FP16 raw move wrong or less than 80% correct-move policy mass. Existing supplementary budgets 10/25/50/100/200. Treat test-defined hard analysis as descriptive; do not tune models on it. |
| Study C | Existing 200/800 ms conditions, FP16 and best dense INT8 (`s4`), default search Threads/smart pruning, MoveOverheadMs=20. Report actual elapsed time and early stopping. |
| Matches | Paired openings/colors, FP16 versus best dense INT8, configured 10+0.1 time control; estimate runtime before setting the final pair count. The current 250-pair configuration is provisional, not an executed match. |
| Swaps | Two stitched network bodies inside lc0; fixed-node accuracy analysis only. Exclude swap models from speed comparisons and the speed frontier. |
| Energy | GPU energy above idle through NVML. CPU RAPL is unavailable on the current Windows stack; no CPU or whole-machine energy claim. |
| Batch study | Reduced MinibatchSize sweep 32/64/128/256 for FP16 and best dense INT8, measuring nodes/s and GPU energy/node. |
| Timing controls | One GPU workload at a time, plugged-in fixed power mode, warm-up and recorded temperature/clocks. Clock locking was denied. Final headline measurements need repeats/medians and disclosed variability; the imported single-pass results remain preliminary. |
| Configuration | `config.example.json` is the shared frozen recipe; ignored `config.json` supplies this machine's paths. Historical run snapshots are evidence, not configurations to execute verbatim after relocation. |

### Accepted omissions and replacements

- Omit search-visited calibration (`s5`), partial INT8, QAT, KD and sparse recovery training from the current PTQ project. Preserve earlier A-side PyTorch work as reference only.
- Replace ModelOpt with the imported quantizer, the separate Python swap MCTS with stitched lc0 models, the original broad batch study with four points, and the fixed 1,000-game match with a runtime-sized paired match.
- Omit the original separate R32_CUDA experimental baseline, one-second timed condition, independent native-CUDA reference and CPU energy from the active suite. Retain earlier artifacts as historical evidence.
- **Omit original F8 (accuracy at equal energy) and F10 (fixed-time accuracy versus batch size).** The current pipeline does not measure them. GPU joules/node and batch throughput must not be presented as substitutes.
- Timed Study C and the main match cover FP16 and best dense INT8. Sparse models retain accuracy and hardware studies; sparse fixed-time/match experiments are not required by the adopted trimmed run sequence.
- Custom kernels, additional networks/GPUs and a new middlegame accuracy corpus remain outside scope. Benchmark positions used only for performance are not an added accuracy test set.

## Week-wise work and ownership

| ID | Week | Person A responsibility and status | Person B responsibility and status | Completion evidence / dependency |
|---|---|---|---|---|
| W1.1 | 1 | **Completed:** checkpoint, input/model definitions and initial export. | **Completed:** lc0, runtime/tool installation and machine inventory. | `nets/`, `models/`, imported inventory and C1 records. |
| W1.2 | 1 | **Completed:** wrapped ONNX and initial INT8 model. | **Completed:** wrapped/native agreement, FP16/INT8 lc0 execution and initial INT8 kernel capture. | `reports/C1-done.md`, `reports/trt/`, `LOG.md`. Detailed coverage remains W3.5. |
| W1.3 | 1 | **Completed:** calibration/development inputs and outlier diagnostics. | **Completed:** dataset, WDL/DTZ scorer, hard subset and baseline A/B measurements. | `data/`, `reports/outliers.txt`, `reports/scores_test.*`. Final integrity closure is W4.4. |
| W1.4 | 1 | **Completed:** FP16 NN-level measurements. | **In progress:** baseline hardware evidence; throughput/GPU energy exist, detailed layer profile remains. | Complete the missing profile under W3.5; do not repeat completed baseline accuracy. |
| W2.1 | 2 | **Completed:** s1 per-tensor, s2 per-channel, s3 percentile 99.999, s4 SmoothQuant alpha 0.7; best=s4 frozen from development selection. | **Completed:** build/load all dense variants in lc0. | `models/*.json`, `reports/C2-recipe-choice.json`, `reports/C2-build-manifest.json`. |
| W2.2 | 2 | **Completed:** Study A metrics and model-side comparison. | **Completed:** main Study B, paired tests and node-equivalent tables. | `results/<model>/study_a.jsonl`, `study_b.jsonl`, `reports/scores_test.*`. |
| W2.3 | 2 | **Completed:** magnitude 2:4 (`s0`) model and accuracy measurements. | **In progress:** sparse-versus-dense hardware comparison and sparse-tactic verification. | Model and supplemental search results exist; hardware completion depends on W3.5. |
| W3.1 | 3 | **Completed:** s4aa attention extension, sequential SparseGPT (`s1sp`), both stitched policy/value swaps. | **Completed:** associated network/fixed-node evaluations. | Model sidecars, C2 manifest, swap provenance and score tables. Sparse accuracy loss is a finding, not incomplete implementation. |
| W3.2 | 3 | **In progress:** consolidate/interpret the completed low-budget hard-subset follow-up and saturation. | **Completed:** six dense models at 10/25/50/100/200 requested nodes. | `results/hard_lowbudget/`; final matched supplemental table still needed. |
| W3.3 | 3 | **Pending:** interpret time/strength tradeoffs using paired results. | **In progress:** Study C raw runs complete; consolidate exactly the common 2,437 IDs at 200/800 ms, score and document actual elapsed time. | `results/studyc/`; preserve extra historical rows and filter them explicitly. |
| W3.4 | 3 | **Pending:** document openings and interpret strength results. | **Pending:** runtime estimate, final pair count, complete match and Elo/CI. | `eval/match.py`; final match summary and PGN. Dependency: stable benchmark environment and frozen models. |
| W3.5 | 3 | **Pending:** operation counts, FLOPs/bytes and roofline interpretation at chosen small/large batch conditions. | **In progress, blocked:** detailed TensorRT profiles, precision/fallback audit, sparse/dense engines, measured compute/bandwidth peaks and roofline timing inputs. | Last run failed loading `nvinfer_plugin_10.dll`. Resolve and verify before resuming this stage. Preserve failure evidence. |
| W3.6 | 3 | **Pending:** explain model accuracy versus measured speed, including sparse negative findings. | **In progress:** initial speed/GPU energy and four-point batch sweep complete. Obtain comparable speed evidence for every model placed on the frontier; repeat headline measurements and summarize medians/variability. | Frontier model set: fp16,s1,s2,s3,s4,s4aa,s0,s1sp. Separate lc0 speed from standalone sparse-enabled trtexec probes; never mix them on one axis without labelling. |
| W4.1 | 4 | **In progress:** numerical tables exist. Finish ablation, accuracy/nodes, node-equivalent, swap and matched before/after SmoothQuant figures and interpretation. | **In progress:** reduced batch plot exists. Finish timed, match, hardware/roofline, energy and frontier figures. | Deliverable mapping below; use the frozen cohorts, report uncertainty and avoid claims unsupported by saturated data. |
| W4.2 | 4 | **Pending:** background, quantization/pruning methods, NN/fixed-node findings and swap/outlier analysis. | **Pending:** harness/runtime, benchmarking, timed/strength and hardware sections. | Final report sources and rendered report. |
| W4.3 | 4 | **Pending, shared:** abstract/introduction, related work, discussion/limitations/conclusion, presentation and playing demo. | **Pending, shared.** | Include accepted scope reductions and distinguish throughput from demonstrated strength. |
| W4.4 | 4 | **Pending, shared:** final split-integrity closure, model/data identities, report-number/citation audit, artifact packaging and fresh reproduction. | **Pending, shared:** verify usable setup/resume instructions and hardware-specific engine rebuilding. | Resolve/document the known small cross-split symmetry overlap without overwriting history. Validate the revised reproduction package; the consolidation smoke check is not a full experimental reproduction. |
| W4.5 | 4 | **Pending, shared:** final deliverable-by-deliverable sign-off. | **Pending, shared.** | Every retained item below has a real output file, owner, evidence/configuration and recorded status; every omission is declared. |

## Remaining execution order

1. Consolidation is an infrastructure/documentation task only: preserve evidence, relocate paths and validate imports/configuration. Do not mark hardware or chess experiments complete because files were moved.
2. Close the hardware loader issue and obtain W3.5 outputs, keeping one GPU job active and respecting agreed checkpoints.
3. Finish matched Study C/hard-subset reporting, comparable per-model speed and headline repeats. Finalize W3.4 match sizing/run. CPU-only analysis can happen while the other teammate owns the GPU.
4. Freeze the final experimental inputs/results (C3). Then complete figures, writing, reproducibility, package, presentation/demo and the C4 checklist.

Do not rerun `tbset`, `calib`, selection or all-model builds merely to consolidate. A changed recipe, cohort or search protocol is a new version and must be agreed/documented before execution.

## Updated deliverable register

Paths below are intended final locations; a pending path does not imply a file already exists. `reports/` retains imported evidence; new publication tables and figures belong in `analysis/tables/` and `analysis/figures/`. Final report/presentation/demo outputs belong in `deliverables/`.

| ID | Retained deliverable | Owner | Status at consolidation | Existing evidence / remaining output |
|---|---|---|---|---|
| D1 | Shared code, setup and reproduction instructions | Shared | **In progress** | Active code at root; README and local configuration. Fresh setup and full reproduction still pending. |
| D2 | Model artifacts, calibration, recipes and engine identities | A+B | **In progress** | `models/`, `nets/`, `data/`, model/build manifests. Final profile engines/package pending; engine binaries are local/GPU-specific. |
| D3 | Labelled root lists, splits, hard IDs and scoring scripts | Shared | **In progress** | `data/tbset.jsonl`, `reports/hard/ids.txt`, `tb/`, `eval/`. Generation/scoring complete; final integrity documentation pending. |
| T1 | Ablation table: Studies A/B, DTZ secondary, paired statistics and node-equivalents | A | **Completed** | `reports/scores_test.md` and `.json`; publication formatting and supplementary low-budget consolidation under W4.1. |
| T2 | Latency, NN evals/s, nodes/s, precision/sparse coverage and raw-checkpoint reference | B | **In progress** | `reports/c3_hw/bench/` and initial kernel capture; finish coverage, comparable per-model speed, repeats and `analysis/tables/T2-speed.*`. |
| T3 | GPU energy above idle per node | B | **In progress** | Existing benchmark/sweep JSON; finish `analysis/tables/T3-energy.*`. CPU/whole-machine energy explicitly excluded. |
| T4 | Paired-match Elo, confidence interval and game count | B | **Pending** | Match results/PGN plus `analysis/tables/T4-matches.*`. |
| T5 | Magnitude/SparseGPT sparse-enabled versus dense execution, per-layer/end-to-end evidence | B | **Pending** | `analysis/tables/T5-sparsity.*`; include a documented no-sparse-tactics result if that is what the runtime chooses. |
| F1 | Dense ablation ladder | A | **Pending** | Data ready; `analysis/figures/F1-ablation.*`. |
| F2 | Accuracy versus requested/actual node budget | A | **Pending** | Main and supplementary data ready; `analysis/figures/F2-nodes.*`. |
| F3 | Node-equivalents | A | **Pending** | Numerical table ready; `analysis/figures/F3-node-equivalents.*`, with saturation caveat. |
| F4 | Policy/value swaps | A | **Pending** | Both swaps evaluated; `analysis/figures/F4-swaps.*`, accuracy only. |
| F5 | Accuracy versus time, with realized nodes and elapsed-time context | B | **In progress** | Raw matched runs ready; `analysis/figures/F5-time.*`. |
| F6 | Per-layer time breakdown and roofline | A+B | **Pending** | Profiles/peaks blocked; `analysis/figures/F6-profile-roofline.*`. |
| F7 | GPU joules per node | B | **In progress** | Measurement data ready; `analysis/figures/F7-energy.*`. |
| F8 | Accuracy at equal energy | — | **Omitted** | Not measured by the trimmed pipeline; do not claim stronger per joule from energy/node alone. |
| F9 | Nodes/s versus four batch settings | B | **Completed** | `reports/c3_hw/batch_sweep/sweep.png`, `.csv`, `.json`; optional publication styling does not require rerunning. |
| F10 | Fixed-time accuracy versus batch size | — | **Omitted** | Not measured by the reduced speed/energy sweep. |
| F11 | Headline accuracy-versus-nodes/s frontier for all retained single-body models | A+B | **Pending** | Comparable per-model speed plus `analysis/figures/F11-frontier.*`. State accuracy condition, actual nodes and batch setting explicitly; exclude double-body swaps. |
| F12 | Matched activation-channel outliers before/after SmoothQuant | A | **In progress** | Text reports and selected channel diagnostics exist. Finish same-input/same-layer comparison and `analysis/figures/F12-outliers.*`; label inserted smoothing correctly. |
| D4 | Final report with methods, results and limitations | A+B | **Pending** | `deliverables/report/`; explicitly record scope reductions and separate speed, search throughput and strength claims. |
| D5 | Presentation | Shared | **Pending** | `deliverables/presentation/`. |
| D6 | Short INT8-lc0 playing demo with visible nodes/s | Shared | **Pending** | `deliverables/demo/`. |
| D7 | Portable artifact inventory/package and fresh reproduction | Shared | **Pending** | Small metadata in Git; large binaries/logs in a checksum-verified artifact bundle. One fresh reproduction including FP16, best PTQ and sparse outputs or their documented runtime limitation. |
| D8 | Final numerical/citation audit and C4 sign-off | Shared | **Pending** | `deliverables/completion-checklist.md`: item -> path -> supporting run/config -> owner -> verification. Include every retained register row. |

## Consolidation closure

Repository consolidation is **Completed**: original-file preservation, configuration portability, artifact inventory/transfer regression checks and saved-score reproduction passed. Evidence: `maintenance/consolidation-verification.json`. This closes the repository task only; scientific statuses below are unchanged.

## Gates and present position

- **C1 pipeline:** completed under the imported gate definition. Original detailed baseline profiling is still owed under W3.5.
- **C2 dense recipe/studies:** completed. The original hardware-inclusive sparse ceiling remains unfinished.
- **C3 final experiment freeze:** in progress, currently blocked in profiling; matches and final speed/report consolidation remain.
- **C4 final deliverables freeze:** pending.

The main model implementations do not need to be redone. Person A's remaining work is chiefly analysis, figures, roofline support and writing. Person B's remaining work is chiefly hardware completion, comparable/repeated speed measurements, timed consolidation and matches. The adopted scope yields all retained deliverables; it does not silently restore omitted outputs from the original PDF.

## Revision record

| Date | Version | Decision |
|---|---|---|
| 2026-10-29 | 2.0 | Adopt LC0-B's conventions/trimmed PTQ pipeline; credit all completed work regardless of producer; incorporate per-model frontier speed, matched SQ figure, final evidence checklist and explicit F8/F10 omissions. Consolidate both repositories without executing new research experiments. |
