# Unified BT3 INT8 project plan

Version 2.5 — 30 October 2026. Original roles: Person A (Anjan, model/analysis) and Person B (Ritwik, systems/experiments). Anjan/Codex now executes the remaining work of both roles.

This is the current plan for the shared repository. It supersedes the two earlier roadmaps for future work. The original proposal and plan remain under `archive/person-a-week1/`; the imported pipeline documentation remains under `archive/person-b-import/`.

Person A Run 1's independent block is complete. See [person_a_execution_plan.md](person_a_execution_plan.md), [original Run 1 verification](analysis/person_a/run1/verification.json) and [subsequent A5 closure](analysis/person_a/a5/closure.json). **A5/F12 is resolved and verified.** Final systems-dependent conclusions and shared delivery remain pending.

The accepted [five-run takeover](docs/takeover_runs.md) replaces the external wait for Ritwik and includes the former Person A autonomous Run 2. Runs 1–3 are complete. Run 2 verified 35 original jobs plus ten continuation jobs, covering all 45 planned jobs, 28 benchmark trials and the two-game pilot. The GPU loader is resolved; profiles/ceiling microbenchmarks/lc0 captures and repeats are collected. Run 3 has completed the bounded precision/sparse/roofline, repeat/session/frontier and canonical timed analysis, with energy qualifications. Match size is frozen at250 pairs; fresh source/Python/artifacts and15 Run4 jobs are prepared, not executed. Week-wise responsibilities below remain the deliverable mapping; completed work is not repeated. Current checkpoint: [progress](reports/takeover/progress.json).

The manual workflow was abandoned after its preserved pre-GPU PID-gate failure. The user explicitly requested Codex orchestration and disabled background-interference blocking. `execution/codex_run2.py` records this approved policy in a separate continuation manifest/output tree, preserving the original 35 results and failures. Background flags remain logged; AC, monitor failures, single-workload locks and command/output/identity checks remain enforced. The ten remaining jobs completed in original order. Run 3 records cross-session thermal/clock/energy variability; Codex activity is not assumed equal across trials. No new accuracy, production-strength or final reproduction result is implied by collection completion.

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
| Precision evidence | INT8 execution observed in all eight lc0 captures. Standalone s4 maps164 fixed-weight INT8 GEMMs (97.8517% of matrix arithmetic);30 attention MatMuls unresolved. Fused internals and lc0 operation coverage are not inferred from kernel-time fractions. |
| Data | Existing `data/tbset.jsonl`: 11,200 synthetic legal roots labelled with local 3–5-piece Syzygy tables; calibration/development/test pools 1,120/3,360/6,720. FEN halfmove clocks are zero. |
| Calibration | Existing `data/calib.npz`: 256 random-game inputs plus 256 tablebase inputs. Existing development inputs contain 3,360 positions. Preserve supplied history for random-game calibration and the imported FEN-only convention for standalone roots. |
| Scoring | Preserve the root win/draw outcome. Adopt the imported category mapping: Syzygy +2 is win, -2 loss, and 0/±1 draw. Secondary DTZ-optimal score follows the imported scorer. These are move-selection scores, not WDL-head classification accuracy. |
| Main evaluated cohort | 2,437 selected test roots. Use matching IDs, splits, model variants and conditions in every paired comparison. Do not pool extra historical Study C rows into unequal cohorts. |
| Study A | Raw policy move, approximate policy KL/top-1 from lc0's printed priors, value error, tablebase accuracy and DTZ secondary score. Explain printed-prior precision limits. |
| Study B | Requested budgets 100/400/800/1,600; record actual nodes because batches overshoot. Threads=1, MinibatchSize=256, smart pruning off. Raw network is the budget-0 comparison. |
| Hard follow-up | Existing 43-position subset: FP16 raw move wrong or less than 80% correct-move policy mass. Existing supplementary budgets 10/25/50/100/200. Treat test-defined hard analysis as descriptive; do not tune models on it. |
| Study C | Existing 200/800 ms conditions, FP16 and best dense INT8 (`s4`), default search Threads/smart pruning, MoveOverheadMs=20. Report actual elapsed time and early stopping. |
| Matches | 250 color-swapped pairs/500 games frozen in Run3 from duration pilot;50 openings repeated five times,10+0.1 and unchanged adjudication. Production pending Run4; final uncertainty must account for repeated openings. |
| Swaps | Two stitched network bodies inside lc0; fixed-node accuracy analysis only. Exclude swap models from speed comparisons and the speed frontier. |
| Energy | GPU energy via NVML; retain total under-load and reported above-idle values. Historical idle cross-check is anomalous, so subtraction is provisional. Controlled Run4 diagnostic prepared. No CPU/whole-machine/equal-energy accuracy claim. |
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
| W1.4 | 1 | **Completed:** FP16 NN-level measurements. | **Completed bounded audit:** repeated hardware evidence and standalone profile mapped in Run3. | T2/F6; opaque fusion and partial operation coverage disclosed. |
| W2.1 | 2 | **Completed:** s1 per-tensor, s2 per-channel, s3 percentile 99.999, s4 SmoothQuant alpha 0.7; best=s4 frozen from development selection. | **Completed:** build/load all dense variants in lc0. | `models/*.json`, `reports/C2-recipe-choice.json`, `reports/C2-build-manifest.json`. |
| W2.2 | 2 | **Completed:** Study A metrics and model-side comparison. | **Completed:** main Study B, paired tests and node-equivalent tables. | `results/<model>/study_a.jsonl`, `study_b.jsonl`, `reports/scores_test.*`. |
| W2.3 | 2 | **Completed:** magnitude2:4 model and accuracy measurements. | **Completed:** dense/sparse tactic audit and repeated lc0 speed; substantial chess loss and slower search are retained findings. | T2/T5/F6/F11; standalone sparse gain is not lc0 sparse acceleration. |
| W3.1 | 3 | **Completed:** s4aa attention extension, sequential SparseGPT (`s1sp`), both stitched policy/value swaps. | **Completed:** associated network/fixed-node evaluations. | Model sidecars, C2 manifest, swap provenance and score tables. Sparse accuracy loss is a finding, not incomplete implementation. |
| W3.2 | 3 | **Completed:** hard-subset paired/actual-node tables and descriptive interpretation. | **Completed:** six dense models at10/25/50/100/200 requested nodes. | Original results/hard_lowbudget plus analysis/tables/hard-lowbudget*.csv and supplemental figure. |
| W3.3 | 3 | **Completed:** canonical paired timed analysis. | **Completed:** exactly2437 matching IDs at200/800ms, actual nodes/time and score consolidation. | T6-timed-canonical.csv, T6-timed-positions.csv, F5-time; extras preserved. |
| W3.4 | 3 | **In progress:** book/pairing review and frozen250-pair design complete; strength interpretation awaits games. | **In progress:** pilot and sizing complete; production Run4, statistics Run5. | reports/takeover/run3/match-sizing.json; plan5–6h/reserve7 for Run4. |
| W3.5 | 3 | **Completed bounded analysis:** operation/precision/fusion mapping, logical traffic and partial measured-reference roofline. | **Completed bounded analysis:** profiles, eight execution captures and sparse tactic review. Fresh validation pending W4.4. | T2/T5/F6;30 attention MatMuls unresolved, modeled bytes not DRAM, reference curves not hard ceilings. |
| W3.6 | 3 | **Completed:** eight-model quality/throughput coordinates and limitations. | **Completed:**28 repeated speed trials, variability/session/thermal review. Energy idle subtraction remains provisional. | T2/T3/F11; five trials each FP16/s4, three each others. |
| W4.1 | 4 | **In progress:** available A figures/tables complete and visually checked, including F6/F11. | **In progress:** F5/F6/F7/F11 complete with limits; match figure awaits Run4/5. | F7 retains energy qualification; F8/F10 omitted. |
| W4.2 | 4 | **In progress:** evidence-linked A report draft and checked reference scope ready; final dependent discussion/shared integration pending. | **Pending:** harness/runtime, benchmarking, timed/strength and hardware sections. | Final report sources and rendered report. |
| W4.3 | 4 | **Pending, shared:** abstract/introduction, related work, discussion/limitations/conclusion, presentation and playing demo. | **Pending, shared.** | Include accepted scope reductions and distinguish throughput from demonstrated strength. |
| W4.4 | 4 | **In progress:** integrity/source/artifact audit and clean setup complete; final numerical/citation/package closure pending. | **In progress:** fresh source/Python/artifact workspace and checked GPU commands ready; actual reproduction Run4, final bundle/audit Run5. | Source eb9e8cf,21 pinned packages,758MB subset; same-host native tools reused. |
| W4.5 | 4 | **Pending, shared:** final deliverable-by-deliverable sign-off. | **Pending, shared.** | Every retained item below has a real output file, owner, evidence/configuration and recorded status; every omission is declared. |

## Remaining execution order

1. Consolidation is an infrastructure/documentation task only: preserve evidence, relocate paths and validate imports/configuration. Do not mark hardware or chess experiments complete because files were moved.
2. Runs2/3 collection and bounded analysis are verified under documented sessions. Preserve flagged/manual failures, partial precision coverage and provisional idle-energy subtraction.
3. Exclusive Run4 first checks fresh reproduction and idle telemetry, then executes frozen250 pairs and captures demo. Current setup and canonical timed/frontier/profile analysis are complete.
4. Freeze the final experimental inputs/results (C3). Then complete figures, writing, reproducibility, package, presentation/demo and the C4 checklist.

Do not rerun `tbset`, `calib`, selection or all-model builds merely to consolidate. A changed recipe, cohort or search protocol is a new version and must be agreed/documented before execution.

## Current autonomous execution sequence

| New run | Mode | Output / dependency gate |
|---|---|---|
| 1 | Normal - completed preparation | Evidence, checked wrappers and tests ready; subsequent Run2 verified GPU PATH fix. |
| 2 | Exclusive - completed and verified | All45 job identities/28 trials/pilot verified; bounded interpretation completed in Run3. Original failed/manual evidence preserved. |
| 3 | Normal - completed and verified | Bounded R1/R2/A6/A7/frontier and R3 analysis,250-pair freeze, fresh setup/subset and15 Run4 jobs ready; no GPU work. |
| 4 | Exclusive — pending | Fresh FP16/s4/sparse GPU checks, paired production match (R4), demo after measurements and runtime/reproduction evidence (R5). |
| 5 | Normal — pending | Final paired statistics, both roles' writing/figures/report/deck, package/restore/reproduction audit and C4. Requires every retained item; unresolved profiling needs a later exclusive repair block first. |

Before each future exclusive run, remind Anjan to save/pause work, use AC and consistent power/cooling, close competing jobs, and state an updated duration estimate. Run 2 is complete. Run3 froze250 pairs using duration only, not pilot outcomes. Run4 planning range is5–6h, reserve7, with uncertain first-build/two-game extrapolation. Read reports/takeover/run3/EXCLUSIVE_RUN_4.md. Details and procedural differences: `docs/takeover_runs.md`, `docs/takeover_protocol_note.md` and `execution/protocol.json`.

## Updated deliverable register

Paths below are intended final locations; a pending path does not imply a file already exists. `reports/` retains imported evidence; new publication tables and figures belong in `analysis/tables/` and `analysis/figures/`. Final report/presentation/demo outputs belong in `deliverables/`.

| ID | Retained deliverable | Owner | Current status | Existing evidence / remaining output |
|---|---|---|---|---|
| D1 | Shared code, setup and reproduction instructions | Shared | **In progress** | Clean source/Python setup and subset restore verified; actual GPU reproduction and final documentation pending Run4/5. |
| D2 | Model artifacts, calibration, recipes and engine identities | A+B | **In progress** | All existing models/engines/receipts preserved; final fresh-engine/runtime freeze and package Run4/5. |
| D3 | Labelled root lists, splits, hard IDs and scoring scripts | Shared | **In progress** | Data/scorer preserved; A-side cohort/symmetry audit complete in analysis/person_a/run1/cohort_audit.json. Shared final integrity/package closure pending. |
| T1 | Ablation table: Studies A/B, DTZ secondary, paired statistics and node-equivalents | A | **Completed** | `reports/scores_test.md` and `.json`; publication formatting and supplementary low-budget consolidation under W4.1. |
| T2 | Latency, NN evals/s, nodes/s, bounded precision/sparse coverage and wrapping reference | B | **Completed bounded analysis** | analysis/tables/T2-*.csv; repeat/session/thermal review; imported C1 raw-checkpoint/wrapping reference retained, not a new native baseline. Standalone mapping and lc0 execution evidence separately scoped. |
| T3 | GPU energy above idle per node, with total under-load comparison | B | **In progress — provisional idle subtraction** | T3-energy.csv and idle-telemetry-review.csv preserve both metrics. Under-load internal consistency checked; Run4 diagnostic and final limitation decision pending. CPU/whole-machine energy excluded. |
| T4 | Paired-match Elo, confidence interval and game count | B | **Pending** | Match results/PGN plus `analysis/tables/T4-matches.*`. |
| T5 | Magnitude/SparseGPT sparse-enabled versus dense execution | B | **Completed bounded analysis** | T5-sparsity.csv;126/125 selected sparse GEMMs;1.077x/1.066x standalone speed ratios, single configuration; no lc0 sparse claim. |
| F1 | Dense ablation ladder | A | **Completed analysis output** | Data ready; `analysis/figures/F1-ablation.*`. |
| F2 | Accuracy versus requested/actual node budget | A | **Completed analysis output** | Main and supplementary data ready; `analysis/figures/F2-nodes.*`. |
| F3 | Node-equivalents | A | **Completed analysis output** | Numerical table ready; `analysis/figures/F3-node-equivalents.*`, with saturation caveat. |
| F4 | Policy/value swaps | A | **Completed analysis output** | Both swaps evaluated; `analysis/figures/F4-swaps.*`, accuracy only. |
| F5 | Accuracy versus time with actual nodes/elapsed context | B | **Completed analysis output** | analysis/figures/F5-time.* and T6 canonical tables; no robust accuracy gain established. |
| F6 | Layer-time breakdown and partial measured-reference roofline | A+B | **Completed bounded analysis output** | F6-profile-breakdown.* and F6-roofline.*; exact mapping where available, logical bytes, opaque fusion and empirical-reference limits disclosed. |
| F7 | GPU joules per node | B | **Completed provisional analysis output** | F7-energy.* retains total and above-idle metrics; historical idle subtraction unvalidated, qualification required in final report. |
| F8 | Accuracy at equal energy | — | **Omitted** | Not measured by the trimmed pipeline; do not claim stronger per joule from energy/node alone. |
| F9 | Nodes/s versus four batch settings | B | **Completed** | `reports/c3_hw/batch_sweep/sweep.png`, `.csv`, `.json`; optional publication styling does not require rerunning. |
| F10 | Fixed-time accuracy versus batch size | — | **Omitted** | Not measured by the reduced speed/energy sweep. |
| F11 | Raw NN quality versus search-throughput coordinates, eight single-body models | A+B | **Completed analysis output** | F11-frontier.* with repeat range and marginal accuracy intervals; workloads differ, not a strength/fixed-time frontier; swaps excluded. |
| F12 | Matched activation-channel outliers before/after SmoothQuant | A | **Completed** | analysis/figures/F12-outliers.{png,pdf,svg}; final alpha-0.7 model, matched CPU measurements on 512 frozen inputs; 101-group build summary kept separate. Provenance and original mismatch preserved. |
| D4 | Final report with methods, results and limitations | A+B | **In progress — A draft ready** | deliverables/report/person_a_sections.md plus checked references and F12; systems-dependent/shared final integration remains. |
| D5 | Presentation | Shared | **Pending** | `deliverables/presentation/`. |
| D6 | Short INT8-lc0 playing demo with visible nodes/s | Shared | **Pending** | `deliverables/demo/`. |
| D7 | Portable artifact inventory/package and fresh reproduction | Shared | **In progress** | Fresh source/Python setup and FP16/s4/SparseGPT subset restored and checked. Actual GPU reproduction Run4; full portable package and final restore audit Run5. |
| D8 | Final numerical/citation audit and C4 sign-off | Shared | **Pending** | `deliverables/completion-checklist.md`: item -> path -> supporting run/config -> owner -> verification. Include every retained register row. |

## Consolidation closure

Repository consolidation is **Completed**: original-file preservation, configuration portability, artifact inventory/transfer regression checks and saved-score reproduction passed. Evidence: `maintenance/consolidation-verification.json`. This closes the repository task only; scientific statuses below are unchanged.

## Gates and present position

- **C1 pipeline:** completed under the imported gate definition. Detailed baseline profiling has a bounded Run3 audit under W3.5.
- **C2 dense recipe/studies:** completed. Standalone sparse execution/empirical-reference analysis is complete with explicit scope limits.
- **C3 final experiment freeze:** in progress; Run2 measurements and Run3 analysis verified; production matches and actual fresh GPU reproduction remain.
- **C4 final deliverables freeze:** pending.

The main model implementations do not need to be redone. Remaining work is fresh GPU validation, production matches, final shared statistics/writing/report/deck/video/package and C4. Current analysis outputs retain their uncertainty and adverse findings. The adopted scope yields all retained deliverables; it does not silently restore omitted outputs from the original PDF.

## Revision record

| Date | Version | Decision |
|---|---|---|
| 2026-10-29 | 2.0 | Adopt LC0-B's conventions/trimmed PTQ pipeline; credit all completed work regardless of producer; incorporate per-model frontier speed, matched SQ figure, final evidence checklist and explicit F8/F10 omissions. Consolidate both repositories without executing new research experiments. |
| 2026-10-29 | 2.1 | Execute Person A Run 1 independent analysis on anjan; verify tables/figures, sparse masks, geometry, timed/opening review and report/delivery preparation. User explicitly deferred A5/F12; reminder required before Run 2. No scientific protocol/model change or new engine/GPU experiment. |
| 2026-10-29 | 2.2 | User authorized A5 resolution. Established C1/C2 model-version mismatch; collected matched final-model activations on CPU using the unchanged 512 calibration inputs; verified scaling, completed F12 and refreshed report/status. No quantizer, scorer, model, calibration or scientific protocol change; no new chess/search/GPU performance experiment. Run 2 still awaits reviewed B inputs. |
| 2026-10-30 | 2.3 | User takes over remaining B work through five autonomous runs, including old A Run2. Execute only new normal Run1: preserve originals, prepare scoped DLL PATH, declared repeated operating points, checked/resumable wrappers and resource controls; 40 offline tests. No imported quant/eval/hw edits, model/scorer/cohort changes, GPU experiment, global PATH/power change or process termination. Exclusive Run2 awaits user start. |
| 2026-10-30 | 2.4 | Complete all45 Run2 job identities/28 trials/pilot under preserved original and approved background-monitor-only v2 sessions. Failed/manual evidence unchanged. |
| 2026-10-30 | 2.5 | Complete CPU-only Run3 profile/sparse/roofline/repeat/frontier/canonical timed analysis and figures; freeze250 pairs, prepare independent source/Python/artifact subset and checked Run4 jobs. Flag repeated anomalous idle telemetry; retain provisional above-idle values and total energy separately. No GPU experiment or scientific model/scorer/cohort change. |
