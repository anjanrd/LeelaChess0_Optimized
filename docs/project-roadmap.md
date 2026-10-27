# BT3 INT8 project: active roadmap and progress record

Roadmap version: **1.5 - Step 1 verified; published 4/5-piece dataset active**  
Last updated: **2026-10-27, Asia/Kolkata**  
Current phase: **Week 1 - complete Person A model/data deliverables; joint C1 tracked separately**  
Current next task: **Recalibrating fixed 160-operation naive INT8 recipe on all 1024 v2 calibration roots only.**  
Execution state: **W1-A15 IN_PROGRESS. Approved autonomous A14-A17 block; verify each before advancing. Person B and joint C1 remain separate.**

## 1. How Codex must use this document

This is the active four-week execution roadmap, current progress tracker and revision record. Read the current-state section, relevant task and latest revision before resuming project work. Update this file after each verified task or material decision. Keep this one document current instead of creating competing roadmap copies.

The original [proposal](../Leela_INT8_Proposal.pdf) and [four-week plan](../plan.pdf) supply the research questions and original work breakdown. The [experiment contract v1.6](experiment-contract.md) supplies recorded experimental decisions. R1.0 approved profiling and coverage review before the main ladder. R1.4 replaces the unexecuted R1.2/R1.3 completion proposals with five minimal Person A steps, W1-A13 through W1-A17, below. The new discussion workflow is already required by the user, but proposed technical choices still require agreement. This document does not silently alter any model, precision definition, numerical limit or previously frozen artifact.

The original PDFs use global Steps 1-18 and separate ablation Steps 0-7. Our expanded Person A Week 1 workflow uses Steps 1-12. Use the stable IDs below to avoid confusing these numbering systems. W1-A07 means our Week 1 INT8 pilot; W2-01 corresponds to original global Step 7, the main quantization ladder.

### Evidence and status rules

- **DONE:** the task's verification requirements are met and evidence is linked.
- **ACCEPTED_WITH_DRIFT:** explicit human acceptance of a recorded exception; the raw numerical failure remains a failure.
- **IN_PROGRESS:** actual execution has begun; record the last verified checkpoint and remaining work.
- **NEXT:** the immediate task to present under the user's execution-mode protocol; execution has not begun.
- **NOT_STARTED:** planned work without execution evidence.
- **UNVERIFIED:** no result has been checked in this chat, especially for work assigned to Person B. Do not infer that Person B has or has not performed it.
- **REVIEW_REQUIRED:** existing evidence is valid, but a design choice must be reviewed before it governs later experiments.
- **OPTIONAL_NOT_ENABLED:** a conditional branch, not authorization or a claim that it will run.
- **AWAITING_USER_DECISION:** required experimental acceptance is open; technical results remain preserved and independent work may finish.
- **PROPOSED:** planning item awaiting roadmap approval and its own implementation discussion; no execution is implied.
- **DISCUSSION:** the user has opened the step's discussion; implementation agreement is still required and no experiment is implied.
- **SUPERSEDED:** an unexecuted planning proposal replaced by a later roadmap; this is not a completed experiment.

Completion requires the stated checks, not simply a script finishing. A failed experiment can be a valid completed investigation if its failure is preserved and the resulting scope decision is explicit. Never mark a checkpoint complete while mandatory work is missing.

Historical records describe their own freeze date. For example, Step 5's ledger and frozen documents say Step 6 had not started; the later Step 6 verification supersedes that progress statement. Do not edit old evidence merely to make its historical status text current.

### User workflow

**Current authorization, 2026-10-27:** the user replaced autonomous progression with a mandatory discussion-and-thinking phase for each new Week 1 completion step. Discuss the implementation and revise it together until explicitly agreed; only then implement and verify that step. After reporting its verified outcome, begin the next step's discussion. Approval of the current roadmap opens Step 1 / W1-A13 discussion and does not authorize its implementation. The 2026-10-26 autonomous authorization is historical and does not override this new workflow. This turn authorizes planning/documentation only.

**Latest steering:** the user approved Step 1 in Codex mode, retaining split sizes but requesting tablebase-backed roots of 4, 5, 6 or 7 pieces rather than our generated four-piece boards. A13 selected published four/five-piece game positions and documented color/rank mirrors; labels and inputs are verified. A narrower 6/7-only tracker note was stale relative to the current explicit user instruction and has been superseded. The agreed history design is implemented. A14-A17 still need their own protocol/mode agreement. Expected numerical drift is reported; existing raw failures/acceptances remain intact and any new acceptance is explicit. No identical-WDL, minimum accuracy or INT8 speed-win requirement is added.

**Latest workflow amendment:** the user requested all remaining discussion points together, followed by autonomous Codex execution of A14-A17 once the combined protocol is agreed. Present one compact proposal; wait for agreement before implementation. That agreement will replace separate mode/approval rounds for this named block only. Verify each step before advancing and stop for essential unresolved faults or required human intervention, not solely for negative measurements. A13 remains verified and unchanged.

At each step, agree its scope, configuration, data, resource/diagnostic budget, pass conditions, handling of failure and execution mode. A failed check returns to that step's discussion; it does not authorize a different experiment, a relaxed threshold or an automatic transition. Continue independent work only within the currently agreed step. Preserve the user's learning/manual-execution option and required execution-mode format below.

1. Work one presented task at a time. Give its objective, intuition, what we are doing and why in simple terms, and execution instructions appropriate to the selected mode.
2. Verify completion before advancing. At completion, update task status, evidence and the execution log here.
3. Before presenting the next task, use this format:
   - **Keeping token efficiency in mind, is it possible for Codex to complete the entire step end to end?** Answer **yes**, **no (manual)**, or **no (coordination)**.
   - **Learning option:** if useful, say "Codex can complete the next step; however ..." and briefly explain what the user learns by doing it. Offer manual execution with click-by-click instructions.
4. Wait for the user's mode selection before starting that next task. The user may authorize a named set of substeps to proceed autonomously with verification between them, as happened for 5A-5G. Do not extend that authorization to unrelated tasks.
5. Prefer CLI/API work over expensive computer control. Ask the user to perform manual actions when that materially improves token efficiency or learning, and explain required manual intervention when encountered.
6. Keep only intended source, documentation, data and evidence in the repository. Put builds, engines, traces and temporary experiments in the existing WSL runtime or system temporary storage. Do not create a project `tmp` folder.
7. Planning approval is not a completed experiment. This document's creation does not execute profiling, quantization, training or teammate tasks.

## 2. Current state and decisions that carry forward

### Verified progress

| Work | Current status | Evidence and practical limit |
| --- | --- | --- |
| Person A Steps 1-4 | DONE, with input-convention review | Environment, checkpoint, native encoding and move mapping verified. Matching encoders establishes compatibility, not the suitability of empty history for playing quality. |
| Person A Step 5A-5G | Historical ACCEPTED_WITH_DRIFT; active reuse REVIEW_REQUIRED | Exact floating artifacts preserved. A13 applies agreed inputs; A14 checks basic correctness and explicitly records how remaining measured drift is handled. No identical-WDL requirement. |
| Person A Step 6 inventory | DONE | All 195 matrix operations inventoried; shapes checked at batches 1-8. Re-inventory only if an agreed graph change affects it. |
| Scope review/profile, A06P/A06R | DONE for the historical standalone run | Both coverage candidates tested; v2 selected 160 INT8 targets. Reconfirm active execution after any input-dependent recalibration and inside lc0. |
| A07 naive INT8 pilot | Historical standalone checks DONE; active reuse REVIEW_REQUIRED | Q/DQ, actual INT8 execution, reload and wrapper checked. Corrected-input calibration and real lc0 integration remain open. |
| A08 historical data / A13 active refresh | DONE and verified | Old data preserved; active v2 has 13,072 published 4/5-piece roots, separate games/symmetry groups, native fen_only inputs and 290 verified table files. B retains DTZ-ranking/hard-subset work. |
| A09 floating NN accuracy | Historical measurements DONE; active baseline REVIEW_REQUIRED | Both scored 55.42% under empty history. A14 refreshes network metrics with a small native correctness check, not a mandatory full native rerun. |
| A10 activation analysis | Historical analysis DONE; input-dependent refresh pending | Exact calibration-only statistics exist for old inputs; A16 refreshes affected statistics. |
| A11 trainable port | Feasibility DONE; targeted new-input parity check pending | Forward/backward feasibility verified. Reuse the port; do not repeat conversion or begin QAT. |
| A12 audit | Historical technical audit DONE; current closure PENDING | A17 closes current Person A evidence and handoff; joint C1 is a separate checkpoint. |
| Person B implementation and joint checkpoints | UNVERIFIED | B01-B08 retain systems/scoring/search responsibilities. They do not become Person A tasks; joint C1 remains separate. |

### Fixed experimental choices

- **Owner:** the user is Person A for Week 1. Person A owns the model work; Person B owns the primary systems/engine work. Codex operates on Person A tasks according to the chosen mode. A focused early model-runtime profile is now also an A-side prerequisite, coordinated with B's fuller profiling work when available.
- **Machine:** experiments run on this physical RTX 4060 Laptop GPU, with 8,188 MiB reported VRAM, through the pinned Ubuntu-22.04 WSL environment. Separate development is permitted; measured GPU workloads run one at a time. Team consolidation mechanics remain deferred.
- **Checkpoint:** `BT3-768x15x24h-swa-2790000`; compressed SHA-256 `e3067757d1fc2dfc66947b21d15ace0cedf4c54254fc1de83d77c378a3e8b8e1`.
- **Software:** lc0 commit `9f45ea446baf9ce55e299250cde3053b7e93a035`; TensorRT 10.9.0.34; ORT GPU 1.22.0; ModelOpt 0.47.0. Full package lock: [step3.lock](../requirements/step3.lock). Changes require explicit provenance and revalidation of affected results.
- **R32_CUDA baseline:** FP32 ONNX through ORT CUDAExecutionProvider, TF32 disabled, verified FP32 matrix computation. This remains a separately measured baseline.
- **F16_TRT baseline:** FP16 ONNX through TensorRT, verified FP16 Tensor Core multiplication; disclosed sensitive floating computation and wider accumulation are allowed. Its accepted exact engine SHA-256 is `4271981b85fb44dd1171a8b49cd999626cd9662f184d3f347a8f7bc4b08b8363`.
- **Drift exception:** the selected F16 engine passed all 86 development cases but exceeded the original WDL-component bound on one of 128 fresh numerical-confirmation positions: 1.9593 percentage points against a 1.5-point limit. The user explicitly accepted this exact engine. Original limits and the raw failed report remain unchanged. Acceptance is not blanket permission for new engine drift and says nothing about tablebase move correctness.
- **Primary speed comparison:** INT8 TensorRT versus F16_TRT holds runtime constant. Comparison with R32_CUDA changes runtime as well as precision; do not attribute all gains to quantization.
- **Inputs:** the historical registered setting is standalone FEN history fill `no`, with classical 112 planes, fixed legal masking, float32 softmax and lexical UCI ties. It remains a historical result definition, not an endorsed choice for new work. Native `fen_only` for standalone FENs with genuine supplied history/repetition preserved is implemented and verified in A13; active inputs are in data/syzygy-v2. Preserve all three outputs and side-to-move conventions.
- **Ground truth:** theoretical tablebase WDL ignoring the fifty-move limit under the current contract, with cursed/blessed cases tagged separately. Score the selected move from the original mover's perspective. On primary winning/drawn roots, W to D/L and D to L are errors. A change in the NN's predicted WDL class is not this error metric.
- **Evaluation levels:** network-only top legal policy move; NN plus MCTS with a fixed-node sweep; NN plus MCTS with a fixed **one-second** wall-time budget per root. The node budgets are still open. Loading/build/warm-up are excluded from the one-second search budget; search and NN execution are included, with elapsed time/overshoot recorded.
- **Data:** calibration, validation and test splits must be disjoint under valid symmetry/trajectory grouping. The 221 groups in the union of pilot and numerical-confirmation exclusions are excluded from final testing. Their labels are not yet available. Use calibration data for activation analysis and validation for technique selection; never tune on final test results.
- **Search:** disable tablebase assistance inside lc0 during measured model/search tests. The tablebase is the external judge. Python MCTS is permitted for the isolated fixed-node swap study; it cannot silently replace lc0 in equivalent timed claims.

### What Step 6 actually established

Scope v1.0 in [step6-scope.json](../environment/step6-scope.json) targets 127 of 195 matrix multiplications. It excludes 37 fixed-weight multiplications under vector/small-dimension rules and 31 activation-by-activation products. These are intentional starting exclusions, not demonstrated hardware impossibilities.

| Quantity | Selected | Outside the starting INT8 scope | Meaning |
| --- | ---: | ---: | --- |
| Unique matrix-weight parameters | 63,950,848 (62.67%) | 38,086,144 (37.33%) | Count shared weight matrices once |
| Matrix MACs per position | 4,403,232,768 (97.0036%) | 136,012,288 (2.9964%) | Count each use of a weight/activation product; includes all 195 matrix operations in the denominator |

The excluded fixed-weight operations account for 38,494,720 MACs per position; the excluded dynamic products account for 97,517,568. Additional biases, normalization parameters and floating constants remain floating. The broader count of all floating initializer values outside the scope is approximately 37.64%; it is not a pure learned-matrix-parameter count.

Most excluded matrix weights lie in the two Smolgen dense layers in each of the 15 blocks (31,457,280 weights total), followed by input embedding preprocessing (6,291,456). The remaining 337,408 are in promotion/value/moves-left calculations. Full named locations, shapes and consumers are in [step6-inventory.json](../environment/step6-inventory.json).

MAC coverage is neither a latency percentage nor a memory-traffic percentage. Large matrix-vector operations may consume meaningful time moving weights even though their MAC count is small. Mixed precision is technically valid, but the suitability of these particular exclusions remains to be tested. There is no already-scheduled later conversion of all 37; any expansion must be an explicit coverage decision.

**Active update after A07:** the paragraphs/table above describe preserved scope v1. The measured review selected [scope v2](../environment/step6-scope-v2.json): 160 intended and executed INT8 fixed-weight operations, 99.9905% of unique matrix-weight parameters and 97.8425% of all matrix MACs. The remaining weighted operations are policy promotion, final value projection, moves-left embedding and final moves-left projection (9,728 matrix parameters total). All 31 dynamic products remain floating. Actual TensorRT INT8 kernels can emit FP32 dequantized intermediates, FP16 or requantized INT8; the remainder is not uniformly FP16. The Q/DQ ONNX stores selected weight source constants in FP16 followed by quantization; INT8 operand execution and saved-engine size are separately verified. Do not equate operator coverage with ONNX-file storage composition.

**New acceptance gate:** the full 10,000-root baseline run found 111 positions with a WDL component difference greater than 1.5 points between F16 and R32, with a maximum of 23.2399 points. Native Eigen checks on the eight largest cases confirm R32 within the original gates and reproduce the larger F16 discrepancy at batches 1 and 8. [Evidence and options](../environment/week1-baseline-drift-review.json). Both frozen artifacts scored 55.42% tablebase move preservation; that does not remove the numerical/search concern. The original engine-specific acceptance is preserved and has not been extended to the new observation automatically.

**Later clarification diagnostic:** on the same 16 roots from the prior native audit, native lc0, R32_CUDA and F16_TRT each scored 9/16 with empty history and 16/16 with `fen_only`. The diagnostic checked that only historical planes changed and that manually encoded `fen_only` matched the native binding on checked examples. This is conversation-level diagnostic evidence, not a new full-set baseline. The history design is now agreed but unimplemented. A13 checks inputs and A14 refreshes measured baseline results. Record remaining FP16 differences after basic correctness checks; no promise is made that changing history removes them.

## 3. Dependency map and checkpoints

The completed A-side path is `W1-A01 -> A02 -> A03 -> A04 -> A05 -> A06 inventory`.

The historical immediate path was `W1-A06P profile -> A06R scope decision -> A07 INT8 pilot -> A08 data -> A09 baseline scoring -> A10 outliers -> A12 review`. Those outputs are retained, with their current reuse limits recorded above.

The proposed Person A path is `W1-A13 data use and consistent inputs -> A14 floating NN baselines -> A15 naive INT8 refresh -> A16 affected activation/port checks -> A17 Person A handoff`. Each arrow requires verification of the previous step and a fresh discussion/agreement before implementation. Completed export, inventory, scope, tablebase and conversion work is reused. B01-B08 and joint C1 run on their own dependencies; A17 does not require pretending those are complete.

W1-A11 PyTorch feasibility is a bounded branch after the floating pipeline; it must report feasibility or a limitation, not hold the mandatory PTQ path indefinitely. W1-B tasks can progress independently when their prerequisites are met. Coordinate GPU access rather than running measurement workloads concurrently.

| Gate | Required evidence | Current state |
| --- | --- | --- |
| Coverage gate, before core ladder comparisons | Baseline timings, justified intended placement, verified pilot execution, explicit final common scope/version | Historical standalone evidence DONE; A15 refreshes active-input execution. B03 owns integrated-runtime confirmation. |
| **C1: Week 1 integration** | Person A deliverables plus real lc0 GPU execution, both floating baseline accuracy/search checks, systems profile/throughput and supported energy instrumentation | UNVERIFIED / NOT COMPLETE |
| **C2: Week 2 PTQ checkpoint** | Dense I1-I5 evaluated on the same validated scope; best PTQ artifact frozen; empirical S0 result or verified unsupported-tactic finding | NOT_STARTED |
| **C3: Week 3 result freeze** | Mandatory timed/hardware studies and enabled optional branches completed or explicitly closed; all final results/configurations frozen | NOT_STARTED |
| **C4: Week 4 delivery** | Audited report, code, reproduction procedure, artifacts and presentation/demo | NOT_STARTED |

Weeks are dependency phases, not a claim about elapsed calendar time. A missed deadline triggers a documented scope decision, not an unverified pass or silent removal of mandatory work. C2 supplies the original plan's core PTQ fallback if optional training/sparsity recovery fails; it does not make unfinished promised benchmarking/reporting complete.

## 4. Week 1: establish and validate the complete pipeline

### W1-A01 - environment and device inventory

- **Owner / priority / status:** A / MUST / DONE.
- **Purpose:** establish the machine, OS and GPU resources so subsequent work uses a reproducible environment.
- **Verification/evidence:** recorded Windows/WSL hardware and environment; [environment.md](environment.md). No dual boot or cloud migration is required by the current plan.

### W1-A02 - checkpoint and experiment contract

- **Owner / priority / status:** A, with joint decisions pending as appropriate / MUST / DONE for initial A-side specification.
- **Depends on:** W1-A01.
- **Purpose:** fix the network, input/output semantics, precision definitions, dataset/scoring rules and variant ladder before results influence choices.
- **Verification/evidence:** [experiment-contract.md](experiment-contract.md). Subsequent versions and exceptions are recorded rather than rewriting history. This does not imply B's approval.

### W1-A03 - pinned toolchain and checkpoint acquisition

- **Owner / priority / status:** A / MUST / DONE.
- **Depends on:** W1-A02.
- **Purpose/work:** acquire and hash the exact checkpoint; pin dependencies/source; build the CPU reference/export tools and verify real GPU runtime smoke tests.
- **Verification/evidence:** [step3-verification.json](../environment/step3-verification.json), [checkpoint identity](../models/source/checkpoint.json), [requirements lock](../requirements/step3.lock). The current lc0 development binary is an Eigen CPU/export build, not the final GPU engine binary.

### W1-A04 - trusted encoding, legal moves and pilot positions

- **Owner / priority / status:** A / MUST / DONE.
- **Depends on:** W1-A03.
- **Purpose/work:** prove that a chess state maps to the right input and policy move; create legal development positions and diagnostic fixtures.
- **Verification/evidence:** [input contract](input-contract.md), [step4-verification.json](../environment/step4-verification.json), [pilot manifest](../data/pilot/manifest.json). Native planes/move vocabulary match; 64 pilot roots and 22 fixtures are development evidence, not final test data or measured tablebase accuracy.

### W1-A05 - ONNX exports and two preserved floating baselines

- **Owner / priority / status:** A / MUST / ACCEPTED_WITH_DRIFT.
- **Depends on:** W1-A04.
- **Completed substeps:** 5A definitions; 5B diagnostic versus baseline scope; 5C explicit serialization/cache diagnosis/reloads; 5D actual kernel precision evidence; 5E development comparisons; 5F fresh numerical confirmation and human exception; 5G integrity, pilot timing and final freeze.
- **Verification/evidence:** [Step 5 report](onnx-validation.md), [final manifest](../environment/step5-final-manifest.json), [acceptance](../environment/step5-acceptance.json). Use the accepted first F16 engine; the rejected accumulation revision remains archived.
- **Limit:** no chess-strength inference from numerical agreement. Original optional builder timing cache was overwritten by the rejected build; the exact accepted engine and outputs remain intact. A rebuild is not promised to reproduce its tactics or outputs.

### W1-A06 - graph inventory and starting scope v1.0

- **Owner / priority / status:** A / MUST / DONE; historical v1 placement superseded by verified v2 after A07.
- **Depends on:** W1-A05.
- **Purpose/work:** map names, shapes, constant/dynamic operands, shared consumers, estimated MACs and candidate quantization rules.
- **Verification/evidence:** [scope report](quantization-scope.md), [inventory](../environment/step6-inventory.json), [verification](../environment/step6-verification.json). Shape/tool checks are valid. Do not promote the 127-operation candidate to a performance-validated scope using its 97% MAC count.

### W1-A06P - NEW: focused floating-baseline profile

- **Owner / priority / status:** A; reuse/coordinate B evidence when available / MUST / DONE.
- **Depends on:** W1-A05 and W1-A06. Existing direct TensorRT/ORT runners permit this investigation before the full lc0 GPU integration is ready.
- **Objective/intuition:** measure where time goes, particularly whether the 37 excluded weighted operations are expensive because they move large weights. The aim is to test the scope rationale before the main quantization ladder.
- **Work:**
  1. Verify original model/engine identities and recorded outputs; load the accepted engine without rebuilding it.
  2. Use fixed legal pilot inputs at batches 1, 4 and 8. Log power state, temperature, clocks, device, versions and warm-up/repetition protocol. One measured GPU workload runs at a time.
  3. Measure the actual F16_TRT baseline first, then the separate R32_CUDA reference where useful. Record resident-GPU inference and host-input-to-host-output timing boundaries separately. Validate host/CUDA clock agreement; the Step 5 pilot initially disagreed and its repeat agreed within 1.1%.
  4. Obtain layer/kernel timings using supported profiling APIs. Map execution back to selected XW, excluded XW, dynamic attention products, nonmatrix work and conversions. Report mixed/unattributed fused layers honestly; never double-count time or invent a 195-row timing decomposition when fusion prevents it.
  5. Distinguish measured timings from shape-derived arithmetic/byte estimates. Use available memory/compute counters if accessible, but do not label an operation conclusively bandwidth-bound solely from its MAC count or parameter count. A diagnostic unfused/microbenchmark run, if needed, is not equivalent to production-engine latency.
  6. Compare profiled and uninstrumented totals to expose measurement overhead. Verify outputs/identities again and save raw evidence outside the project, with a small reproducible summary inside it.
- **Verification/deliverable:** repeatable latency breakdown, source-operation mapping and uncertainty, excluded-37 time contribution, relevant memory-traffic evidence/estimates and a concrete scope-review recommendation. No minimum speedup or coverage percentage is assumed.
- **Evidence:** [baseline profile](../environment/week1-baseline-profile.json) and [registered protocol](../environment/week1-profile-protocol.json). Excluded weighted GEMM layers account for 14.61% of instrumented layer time at batch 1 (profiler overhead disclosed). No DRAM counter or conclusive bandwidth-bound claim. W3-08 remains the complete final roofline study.

### W1-A06R - NEW: decide and record the common quantization scope

- **Owner / priority / status:** A; joint coordination before the main ladder / MUST / DONE.
- **Depends on:** W1-A06P.
- **Objective/intuition:** select a defensible common scope using real costs, rather than permanently excluding a large weight fraction on a geometry heuristic alone.
- **Work:** inspect each excluded group, not just the aggregate. Decide whether to retain v1.0 or target additional fixed-weight operations, especially embedding preprocessing and the 30 Smolgen dense multiplications. Consider expected bandwidth/storage benefit, kernel support, conversion cost and reproducibility. The 31 dynamic products remain an explicit separate scope decision; they are not automatically included by expanding learned-weight coverage.
- **Decision rule:** declare the evidence and bounded candidate set before any coverage probes. If profiling alone is insufficient, register a limited pilot comparison for W1-A07; do not tune scope using final test results. Broader INT8 is not assumed to be faster or more accurate.
- **Verification/deliverable:** an explicit retain/expand decision, exact named targets and floating exceptions, weight/MAC coverage, unresolved backend checks and a versioned record. Preserve v1.0 and its evidence; a revised scope gets a new artifact/version and an active reference here. Keep matched placement across I1-I7 unless a separately named coverage ablation is registered.
- **Gate:** intended placement is reviewed here; W1-A07 must confirm execution before it is accepted as the final common scope for Week 2. Unexpected backend/numerical changes return to this decision with evidence rather than being silently accepted.
- **Verified decision:** [scope v2](../environment/step6-scope-v2.json) selects 160 fixed-weight MatMuls, covering 99.9905% of unique matrix-weight parameters and 97.8425% of all matrix MACs. Four tiny weighted operations and 31 dynamic products remain floating. The expanded/original normalized host latency ratios were 0.9685 at batch 1 and 1.0626 at batch 8, within the registered 1.10 allowance. Placement was not selected from prediction accuracy. Actual lc0 integration remains B's check.

### W1-A07 - first naive INT8 pilot and preparation for lc0 integration

- **Owner / priority / status:** A; B owns full GPU engine integration / MUST / DONE.
- **Depends on:** W1-A06R; W1-B01/W1-B02 are needed for the real lc0 check, but not the standalone pilot.
- **Objective/intuition:** turn the reviewed specification into an executable quantized model and verify that low-precision computation actually happens.
- **Planned verified substeps, with autonomous progression only if the user selects that mode:**
  - **7A:** lock the reviewed scope, legal pilot/calibration inputs, protocol, hashes and a bounded diagnostic budget. Keep these experiments separate from final datasets.
  - **7B:** validate the required unquantized opset bridge. Current exports are opset 17; ModelOpt's FP16 Q/DQ path requires at least opset 19. Check model semantics, node mapping and output agreement before quantization. Derive compared graphs consistently; retain both accepted baseline artifacts. Investigate changed TensorRT tactics/numerics rather than extending the old engine-specific exception automatically.
  - **7C:** create naive I1 with signed symmetric W8A8, per-tensor weights, per-tensor activations and max calibration. ModelOpt 0.47.0 hardcodes per-channel weights in its high-level INT8 path; use an explicitly recorded adapter/lower-level path. Do not silently produce I2 instead, and do not edit installed packages without a separate justified change.
  - **7D:** audit exact Q/DQ placement, scale shapes/axes, zero points, shared consumers, all heads and declared floating exceptions. Check the complete graph, finite outputs and input/output conventions.
  - **7E:** build, preserve and reload the INT8 engine; inspect/profile actual INT8 Tensor Core multiplication, INT32 accumulation where applicable, actual coverage, conversion boundaries and fallbacks. Representation in ONNX is not execution proof.
  - **7F:** perform the registered pilot numerical/latency checks and any bounded coverage probe from W1-A06R. Include conversions in end-to-end timing; no tablebase-strength claim from prediction differences. If a coverage candidate fails, preserve it and return to the scope decision.
  - **7G:** record the validated common scope/version before the main ladder, prepare correct lc0 wrapper metadata and reproduce a smoke input/output through the available integration path. Joint engine completion is W1-B03/C1, not a claim implied by the standalone runner.
- **Verification/deliverable:** reproducible pilot model/engine, graph and actual-precision audit, recorded numerical differences, measured pilot timings, wrapper/handoff artifacts and final reviewed scope. No predetermined requirement that naive INT8 improve accuracy or speed.
- **Evidence/result:** [pilot handoff](../environment/week1-int8-pilot.json), [registered comparison](../environment/week1-pilot-protocol.json), and [both candidate records](../environment/week1-i1-engine-160.json). All 160 targets execute INT8; expanded/original normalized latency is within the registered allowance. The selected naive pilot remains slower than F16 and has large numerical drift. This is engineering evidence, not successful recovery or final INT8 test accuracy. ModelOpt selection/shared-consumer failures and fixes are retained in [investigations](../environment/week1-investigations.json).

### W1-A08 - Syzygy dependencies and full dataset construction

- **Owner / priority / status:** A; coordinate label/scoring implementation with B / MUST / DONE.
- **Depends on:** W1-A04 and W1-A07 engineering pilot; scoring validation can progress with W1-B04.
- **Objective/intuition:** create trusted, separated data for calibration, technique selection and final measurement.
- **Work:** enumerate all required tablebase files, including capture/promotion dependencies; acquire and verify them; implement root/child outcome checks; sample legal positions from the registered families/distribution; group valid symmetries and shared trajectories before splitting. Reject the 221 prior-development groups from final testing. Handle terminal/missing-table cases explicitly.
- **Starting counts:** 1,024 calibration, 2,048 validation and 10,000 test positions, subject to a documented runtime/coverage feasibility pilot before final evaluation. Final counts, seeds, balance, manifests and fingerprints must be recorded. Do not enlarge/redefine testing after seeing a preferred result.
- **Verification/deliverable:** verified probe/scoring tests, complete table dependencies, reproducible split/label manifests, disjointness proof, complete sampled set and registered decision-sensitive/hard subsets. Freeze the hard threshold using validation FP16 outputs, not INT8 test outputs.
- **Evidence/result:** [full manifest](../data/syzygy/manifest.json), [40 verified files](../environment/week1-tablebases.json), [scoring fixtures](../environment/week1-scoring-checks.json). Original counts retained: 1,024/2,048/10,000, balanced over 16 material/side/W-D cells. All native planes and legal maps match the independent encoder; all legal child outcomes and root consistency checked; every split is symmetry-disjoint and excludes all 221 prior groups. Hard threshold was frozen before test inference in A09.

### W1-A09 - network-only accuracy for both floating baselines

- **Owner / priority / status:** A / MUST / REVIEW_REQUIRED.
- **Depends on:** W1-A08; accepted baseline identities remain fixed or explicitly revalidated if the bridge required derived comparison artifacts.
- **Objective/intuition:** measure baseline move quality against independent tablebase truth, rather than treating numerical agreement with another network as correctness.
- **Work/verification:** run both R32_CUDA and F16_TRT under the same input/legal-move convention; score highest-probability legal moves; save per-position predictions, chosen moves and theoretical outcomes; report material/outcome/hard-subset strata and paired uncertainty. Keep numerical prediction differences distinct from tablebase move errors. No tuning on final results.
- **Deliverable:** reproducible network-level baseline outputs and accuracy report. This is the first of the user's three evaluation levels; the other two are W1-B05/W1-B06 and later full studies.
- **Measured evidence:** [baseline accuracy](../results/week1/baseline-accuracy.json), [readable results](week1-baseline-results.md), [numerical differences](../results/week1/baseline-numerical-comparison.json), [native spot checks](../environment/week1-native-check.json). Both score 55.42%; paired accuracy difference is 0.0000 points with 95% stratified paired-bootstrap interval [-0.0600, 0.0600] points. **Closure is REVIEW_REQUIRED** because [additional FP16 drift diagnostics](../environment/week1-baseline-drift-review.json) exceed the previously accepted observation. No model rebuild, tolerance relaxation or test-driven tuning occurred.

### W1-A10 - calibration activation/outlier analysis

- **Owner / priority / status:** A / MUST / DONE.
- **Depends on:** W1-A08 and the reviewed quantization locations.
- **Purpose/work:** collect per-channel activation statistics at named locations on calibration inputs only; record axes/shapes and plot maxima/distributions to identify whether outliers motivate SmoothQuant.
- **Verification/deliverable:** reproducible statistics/plots, handling of shared consumers and a bounded Week 2 smoothing/calibration search. An absence of strong outliers is a valid finding; do not choose locations or scales using test activations.
- **Evidence/result:** [statistics](../results/week1/calibration-outliers.json), [analysis and plot](week1-activation-analysis.md). All 1,024 calibration positions, 113 unique activation tensors and 160 selected matrix consumers checked. FP32 diagnostic statistics agree with original graph outputs; they are not production TensorRT intermediate measurements. Shared-weight/fan-out rules and five candidate smoothing strengths are documented; no smoothing was implemented.

### W1-A11 - bounded PyTorch-conversion feasibility

- **Owner / priority / status:** A / SHOULD / DONE.
- **Depends on:** W1-A05; can be a parallel development branch when GPU use is coordinated.
- **Purpose/work:** attempt a trainable conversion using the supported exporter-friendly graph or a bounded port. `--onnx2pytorch` changes export compatibility; it does not itself export a trainable module. Declare a time/effort budget before work.
- **Verification/deliverable:** checked forward parity, heads/encoding and a small gradient/memory feasibility check, or a documented limitation and stopped branch. No silent approximation of the architecture. This task does not authorize QAT or distillation training; W2-05 decides that branch.
- **Evidence/result:** [feasibility](../environment/week1-torch-feasibility.json), [reconstruction script](../scripts/torch_feasibility_week1.py). FP32 forward parity passed on 16 calibration roots at batches 1 and 4; every trainable tensor has finite gradients in a batch-1 backward check, with peak allocated CUDA memory 886,057,984 bytes. No optimizer step, QAT or distillation was run. Scalar multipliers remain fixed; full optimizer/convergence feasibility remains open.

### W1-A12 - Person A review and joint C1 handoff

- **Owner / priority / status:** A-side audit / MUST / REVIEW_REQUIRED; current refresh is A17. C1 remains joint and separate.
- **Depends on:** W1-A07 through W1-A10; W1-A11 has a recorded outcome if attempted.
- **Work/verification:** audit all A-side deliverables, active scope/version, model/engine hashes, dependencies, seeds, data exclusions and reproducibility commands. Record missing systems dependencies rather than calling A completion the joint checkpoint. Review the plan/definitions with B before freezing shared experimental choices for the main ladder.
- **Deliverable:** A-side checklist with evidence; joint C1 decision only after W1-B requirements are verified.
- **Technical evidence:** [historical audit](../environment/week1-audit.json) and [historical handoff](week1-person-a-handoff.md). All 13,072 root groups, 193 original/transformed root/child probes and 16 independent native CPU references were checked. Their original identities remain evidence. A13-A17 now supply the minimal current Person A refresh and handoff. A-side completion does not require completing B tasks. Joint C1 and all B-side rows below remain unverified.

### Week 1 systems work and joint dependencies

All rows below are **UNVERIFIED** in this chat. They are assignments/planned requirements, not claims that B has done no work.

| Stable ID | Owner | Work and purpose | Dependencies and verification |
| --- | --- | --- | --- |
| W1-B01 | B | Build the pinned lc0 GPU/onnx-trt harness and resolve supported profiling tooling | A03 metadata/source. Verify actual GPU backend execution; the current Eigen CPU tool binary is insufficient. Do not silently upgrade pinned versions. |
| W1-B02 | B | Run the accepted floating models through the appropriate engine paths; record stock native lc0 FP16 as a diagnostic | B01, A05. Check input/output parity and actual providers/kernel precision. Stock native FP16 is not a third required baseline. |
| W1-B03 | B with A | Run the pilot wrapped INT8 file in real lc0 and inspect partition/fallback behaviour | A07 and B01. Check selected-operation precision and report any CUDA/CPU fallback. Python MCTS cannot silently replace equivalent timed lc0 claims. |
| W1-B04 | B with A | Implement and independently validate theoretical WDL move scoring; define DTZ secondary ranking correctly | A04 and table dependencies. Root/child sign, terminal, cursed/blessed and missing-table cases must pass. No minimum-absolute-child-DTZ shortcut. |
| W1-B05 | B | Select/register node budgets, batch/cache/tree policy and search options; measure both floating baselines at fixed nodes | B02, B04, A08. Same positions/options, reset policy and preserved chosen moves/visits/evals. Node counts remain open until recorded. |
| W1-B06 | B | Verify the one-second-per-root condition for both floating baselines and record an initial baseline measurement | B02/B04, A08, registered search protocol. Include actual search/NN time, elapsed overshoot and visits; exclude prior load/build/warm-up. Full timed comparisons remain W3-04. |
| W1-B07 | B | Baseline throughput/profile by batch and measurement controls; share results with A06P | B02. Record standalone latency/throughput, lc0 nodes/s and layer information; distinguish standalone and integrated engines. Check clock locking if available, otherwise log power/clocks/temperature and repeated warmed timings. |
| W1-B08 | B | Verify energy instrumentation and prepare measurement scripts | Check available GPU NVML energy/power and CPU RAPL access on this machine/WSL. Calibrate idle subtraction and units. Report unavailable CPU/GPU coverage explicitly; no invented whole-system measurement. |

**C1 acceptance:** floating inference works end to end in lc0; both baseline definitions and all three baseline evaluation levels are checked; pilot INT8 integration/coverage and data/scoring work; baseline nodes/s, profile/throughput, supported energy instrumentation and initial baseline energy readings are recorded. Unsupported counters/clock locks need an explicit limitation and an agreed alternative protocol, not fabricated results or silent removal of a deliverable.

### R1.4: five remaining steps for Person A

**Current status:** A13 is DONE and verified; A14-A17 remain PROPOSED and NOT_STARTED. The earlier R01-R08 proposal IDs are superseded planning entries, not completed experiments. History agreement carries forward to A13. Original A01-A12 evidence, numerical failures and exceptions remain preserved.

**Protocol for every step:** discuss and agree the few relevant rules/data/checks and execution mode; implement only that agreement; verify and explain the outcome; then open the next discussion. Roadmap approval alone does not authorize implementation. Routine technical details stay within the agreed scope. A concrete correctness failure returns to discussion; expected precision differences, lower native NN accuracy or a slower naive pilot do not automatically trigger an optimization project.

| Previously listed issue | Completion step |
| --- | --- |
| 1. Inputs/results still use old missing history | A13 |
| 2. Floating NN baseline results are stale | A14 |
| 3. INT8 calibration used old inputs | A15 |
| 4. Activation analysis/port checks need affected refresh | A16 |
| 5. Evaluation-data exposure/use needs clarity | A13, before new final measurements |
| 6. Person A handoff is outdated | A17 |

#### W1-A13 - Step 1: settle data use and update the inputs

- **Status:** DONE / Codex / verified. The current user instruction allowed 4/5/6/7-piece roots; the implemented dataset uses 4 and 5 pieces. Published provenance, mirrors and original FENs are recorded.
- **Objective / intuition:** all later results should use the same agreed description of the position and a clear distinction between calibration, validation and testing.
- **Agree first:** which existing splits to reuse, how previously inspected test data will be labeled/used, and the small input checks. Native `fen_only` for standalone FENs and preserving actual history/repetition are already agreed. A new holdout is an explicit option, not an automatic requirement.
- **Implement:** reuse valid board lists, labels and table files; update affected encoded inputs under the agreed history convention. Version affected outputs and preserve the old run.
- **Verify / done:** independent/native inputs match on agreed checks, split separation/exclusions remain valid, and data identities and the exposure decision are recorded. Do not tune on final test outputs.
- **Deliverable / mapping:** current input tensors plus a concise data-use/input record; updates A02/A04/A08. Agreement and verification are complete.

**Verified Step 1 outcome:** [active dataset manifest](../data/syzygy-v2/manifest.json), [input/data protocol](../data/syzygy-v2/protocol.json), [verification report](../environment/week1-input-refresh.json) and [reproduction script](../scripts/refresh_inputs_week1.py). Calibration has 512 four-piece + 512 five-piece roots; validation 1,024 + 1,024; test 5,000 + 5,000. Each split is equally W/D and White/Black within piece count. There is one root per source game, all prior project/development groups are excluded, and all 13,072 original FEN/game pairs were independently relocated in the pinned raw source.

Some roots use exact color/rank mirrors to balance sides: the source filter counts the FEN side-to-move 'b' as a piece, omitting true five-piece Black rows. Original FEN, game ID and transform are preserved. Effective counters remain halfmove=0/fullmove=1 under the theoretical-WDL contract. All 290 required 3-5-piece WDL/DTZ files (983,957,920 bytes) passed full-file/official checksums. Every root and legal child outcome was checked, all 13,072 input planes/legal maps match native encoding, and all 22 history/edge fixtures pass exactly.

Shape is still [B,112,8,8] and the NN graph is unchanged. No project NN predictions were inspected on the new test roots before freeze. Old inspected data, models and numerical failures remain unchanged. This is a stratified benchmark rather than a natural-frequency/Elo estimate; B still owns hard-subset and DTZ-optimal ranking work.

**Reproduce:** in the pinned WSL venv with `PYTHONDONTWRITEBYTECODE=1`, run `scripts/refresh_inputs_week1.py` actions `source`, `acquire`, `build`, `verify` sequentially. The reader is isolated pyarrow 21.0.0 under the external runtime tools directory, leaving the model environment unchanged. Source ranges, tables and reader dependencies stay outside the project. Source generation/code identities and range hashes are pinned in the protocol. No NN inference, INT8 recalibration, activation reanalysis or training was run.

### Combined Steps 2-5 discussion proposal (awaiting agreement)

The machine-readable full defaults are in [week1-progress.json](../environment/week1-progress.json), under combined_completion_protocol. This proposal authorizes no experiment yet.

- **Step 2:** reuse exact floating artifacts and active data; infer all three splits, separating diagnostic calibration/validation results from main test accuracy. Select 32 balanced calibration roots for native correctness and batch-1/batch-8 spot checks; use batch 8 for bulk inference. Keep the registered highest-legal-policy/tablebase move-error rule. After basic setup checks, retain F16 as a separately measured baseline and report remaining drift/raw numerical failures rather than requiring identical values. This baseline-use decision needs explicit agreement; historical raw failures are not rewritten as passes.
- **Step 3:** use all 1,024 calibration roots for the existing naive symmetric per-tensor W8A8/max recipe and 160-operation scope. Verify actual precision/coverage, reload and wrapper identity. Use 2,048 validation roots for pilot quality, reserving INT8 final-test inference for later work. Run brief matched timing at batches 1/4/8, primary comparison against F16 and separately labeled R32. Record practical warmups/repetitions before timings. A valid slower/less accurate pilot is reported without starting a tuning campaign.
- **Step 4:** refresh existing activation statistics/plots on calibration only; compare the existing port with FP32 on the same 32 calibration cases. Reuse completed conversion/gradient checks; no training.
- **Step 5:** audit current A deliverables and reproduction instructions, preserve old artifacts and freeze the A handoff. B work and joint C1 remain independent.

Keep data and definitions fixed, make no calibration/method decisions from test outputs, and handle routine technical choices/fixes autonomously. Only essential unresolvable correctness failures, required manual intervention or a material scope change require another discussion. Once the user agrees, verify each named step before continuing through A17; do not ask for mode selection again between them.

#### W1-A14 - Step 2: refresh the floating network baselines

- **Depends on:** verified A13. Use active `data/syzygy-v2`; historical scripts/results hardcode old data. History AND root distribution differ, so new accuracy is not a controlled history-only comparison with the old 55.42%.
- **Objective / intuition:** record what the two real floating baselines do with corrected inputs.
- **Agree first:** evaluation cohort, highest-legal-policy move scoring, a small native cross-check and how remaining FP16 differences will be reported/accepted. Reuse the existing W-to-D/L or D-to-L rule and existing output conventions unless explicitly changed. Keep raw old tolerance failures and earlier acceptance intact; any decision to retain larger drift is explicit, not an automatically passed numerical check.
- **Implement:** rerun R32_CUDA and the exact preserved F16_TRT on the agreed data. Check a small fixed diagnostic sample against native lc0 to catch input/export mistakes. Save the policy, WDL and moves-left outputs and resulting NN-level metrics.
- **Verify / done:** outputs and move scoring are valid/reproducible, basic correctness problems are resolved, and each baseline's observed accuracy and numerical differences are documented with their identities. No identical-WDL requirement, arbitrary accuracy target or obligatory full native accuracy run. If the setup is correct, ordinary precision drift is a measured baseline property; material unresolved faults still require discussion.
- **Deliverable / mapping:** updated two-baseline NN report and outputs, with a brief native sanity check and explicit treatment of remaining drift; updates A05/A09.

#### W1-A15 - Step 3: refresh the naive INT8 pilot

- **Depends on:** verified A14.
- **Objective / intuition:** make sure the starting INT8 model was calibrated on the inputs we will actually use.
- **Agree first:** calibration inputs, the existing naive recipe/160-operation placement, and brief execution/quality/timing checks. Reuse the reviewed scope and prior profiling rather than reopening the placement study.
- **Implement:** refresh affected calibration, build the resulting naive INT8 artifact and saved engine, and update the lc0 wrapper. Recheck actual INT8 execution and reload. Compare a bounded set of outputs/moves and preliminary latency with F16 under matched controls; label pilot quality figures as diagnostics, not final INT8 test results.
- **Verify / done:** agreed placement executes INT8, outputs are valid, the wrapped graph matches, and preliminary quality/speed are honestly recorded. A slower or less accurate naive result is allowed; it does not establish a final optimization success or failure. No quantization ladder, extensive tuning or new hardware study.
- **Deliverable / mapping:** current naive INT8 ONNX/engine/wrapper, execution evidence and a brief diagnostic summary; updates A07 and the affected A06P/A06R evidence. Actual lc0 GPU integration remains B03.

#### W1-A16 - Step 4: refresh activation analysis and check the existing port

- **Depends on:** verified A15; use A13's agreed calibration inputs.
- **Objective / intuition:** give Week 2 an activation analysis that reflects the actual inputs, while reusing the completed model reconstruction.
- **Agree first:** calibration-only statistics/plots and a small forward comparison for the existing PyTorch port.
- **Implement:** recompute affected per-channel activation statistics and plots, and run the targeted port compatibility check. Reuse the architecture and already verified gradient feasibility; repeat additional conversion/backward work only if a concrete change requires it.
- **Verify / done:** statistics use calibration data only, named tensors/consumers are correct, plots are current, and port output compatibility is checked.
- **Deliverable / mapping:** updated activation/outlier analysis and a short port-check result; updates A10/A11. No smoothing application, optimizer step, QAT or distillation.

#### W1-A17 - Step 5: finalize Person A's Week 1 handoff

- **Depends on:** verified A13-A16.
- **Objective / intuition:** make the model-side work easy to identify, reproduce and hand over.
- **Agree first:** a short checklist covering current models, input/data decisions, NN baseline results, INT8 pilot, activation analysis and port check; explicitly identify B dependencies.
- **Implement:** update the existing handoff, current artifact identities and reproduction commands. Retain historical runs and failed checks; distinguish a reported negative result from a missing deliverable.
- **Verify / done:** every Person A deliverable has current evidence, there is no unresolved model/input correctness fault, and the agreed treatment of precision drift is recorded. Mark Person A completion separately from Person B work and joint C1; teammate approval is not inferred.
- **Deliverable / mapping:** a concise verified Person A handoff and completion checklist; updates A12. B-side integration/search/scoring/energy and joint C1 remain independently open until verified.

### Scope and four-week boundaries

Person B keeps lc0 GPU integration, provider/fallback inspection, scoring/DTZ and hard-subset definition, fixed-node/fixed-time runs, systems profiling and energy instrumentation. Person A supplies the model/data/output interface needed for those tasks. The existing 0%-baseline hard subset needs B/joint review; A13-A17 do not silently redefine it or claim it resolved. Any changed test set, format, precision or metric needed by joint studies is shared explicitly.

A13-A17 do not require FP16 to reproduce FP32 exactly, the native NN to reach an invented accuracy target, or the naive INT8 pilot to beat FP16. They do require valid inputs/models/scoring and honest measurements. An existing numerical exception is not silently broadened: retain its raw failure and make any new baseline-use decision explicit in A14.

The earlier six remedies retain their boundaries: corrected inputs/baselines are A13/A14; matched pilot checks are A15 with the already completed focused profile reused. Representative GEMM/roofline work stays W3-08, quantization recipes stay W2-01, extensive batch/runtime work stays W3-07, and the QAT/KD decision stays W2-05. Baseline MCTS readiness remains B's Week 1 responsibility; controlled variant studies stay Week 2 and the full timed comparison stays W3-04. Week 4 remains analysis, reproduction and delivery.

**Person A exit checklist:** current input/data record; two floating NN baselines; valid refreshed naive INT8 artifacts; current activation analysis and targeted port check; reproducible A handoff. Completion of this checklist does not close joint C1 or authorize Week 2 by itself.

## 5. Week 2: controlled INT8 ladder and empirical sparsity probe

The reviewed, backend-validated common placement from W1-A06R/A07 is a prerequisite. Do not begin core ladder comparisons on an unreviewed v1.0 scope merely because its static verification passed. If C1 has open integration/scoring issues, resolve or explicitly revise them before comparable studies.

### W2-01 - dense PTQ variants I1-I5 (original global Step 7)

- **Owner / priority / status:** A / MUST / NOT_STARTED.
- **Depends on:** coverage gate, C1 and frozen full datasets.
- **Work:** create full-data I1 naive per-tensor/max; I2 per-output-channel weights only; I3 compare max/entropy calibration under the contract's validation rule; I4 SmoothQuant with predeclared strengths and a floating equivalence check; I5 search-visited calibration from training-pool positions with count/preprocessing controlled. A Week 1 pilot I1 is engineering evidence, not a substitute for the registered full-data recipe.
- **Verification/deliverable:** one reproducible configuration/model/engine per variant, exact same target-node set, calibration provenance and actual INT8 execution/coverage. Respect shared activation/weight consumers during smoothing. Fix accidental selected-node fallback before evaluation. A deliberate expansion/exclusion is a separate scope revision, not a claimed one-factor improvement.
- **Selection rule:** validation only; I3 uses lower mean policy KL then lower value MAE on ties, retaining max if entropy does not help. Register tuning budgets before each technique. Percentile calibration is not silently added to the current max/entropy choice. Do not assume these variants run at identical speeds; record measured differences.

### W2-02 - Study A, network metrics for every variant (original Step 8, A side)

- **Owner / priority / status:** A / MUST / NOT_STARTED.
- **Depends on:** each verified W2-01 variant and W1-A09 scoring pipeline.
- **Work/verification:** numerical policy/value/WDL differences against both floating references; legal top-move agreement; independent tablebase move accuracy. Retain per-position outputs, uncertainty and material/outcome/hard-subset breakdowns. Keep final test data out of model selection. Freeze the recipe before its registered final evaluation.

### W2-03 - per-variant engines and Study B, fixed nodes (original Steps 7-8, B side)

- **Owner / priority / status:** B / MUST / NOT_STARTED.
- **Depends on:** verified variants, common search settings and W1-B05.
- **Work/verification:** preserve/reload an engine per variant; verify actual precision/partitioning; run the same fixed-node sweep. Save tablebase correctness, actual visits/evals, batch/reset/cache choices and uncertainty. Compute node-equivalents with a documented interpolation/comparison rule, not invented search counts. Both floating baselines remain separately reported.

### W2-04 - S0 magnitude 2:4 plus INT8 (original Step 9)

- **Owner / priority / status:** B primary; A supports model identity / MUST probe / NOT_STARTED.
- **Depends on:** best dense recipe and a declared eligible sparse-weight scope.
- **Work:** prune along the correct reduction dimension, preserve exactly the 2:4 pattern, recalibrate on the pruned network using the chosen dense recipe and build a sparse-capable engine. This remains Week 2 work; Week 1 recovery does not enable S0 early.
- **Verification/deliverable:** mask correctness, actual sparse tactics and per-layer/end-to-end measurements. "Speed ceiling" is the original label; S0 is an empirical probe, not a proven upper bound or guaranteed 2x result. If sparse tactics are unavailable, record the evidence and close downstream sparse branches explicitly; do not claim sparse execution from zero weights alone.

### W2-05 - mid-week QAT/KD feasibility decision (original Step 10)

- **Owner / priority / status:** A; shared schedule decision / MUST decision / NOT_STARTED.
- **Depends on:** W1-A11 outcome, available training hardware and best PTQ evidence.
- **Work/verification:** decide whether a numerically checked trainable model, memory and time budget exist. Training feasibility is not assumed from FP16 inference fitting in 8 GB. Record resources, registered data/losses and a bounded plan before enabling W3-01. If infeasible, drop I6/I7 and S2; preserve PTQ and the hardware analysis path. No cloud expenditure or machine migration is implied.

**C2 acceptance:** I1-I5 results and common coverage audited; best PTQ graph/scales/recipe frozen using validation; S0 probe completed or supported sparse-tactic failure documented; QAT decision recorded. Mandatory fixed-time/hardware/report work still follows even if all optional training branches are dropped.

## 6. Week 3: optional training/sparsity and final systems studies

### W3-01 - I6 QAT, I7 distillation and optional S2 recovery (original Step 11)

- **Owner / priority / status:** A models, B engines / SHOULD; S2 COULD / OPTIONAL_NOT_ENABLED.
- **Depends on:** C2 and an affirmative W2-05 decision. S2 also requires a verified sparse mask/candidate and training feasibility.
- **Work/verification:** register training inputs, losses, teacher configuration, budget and checkpoints; fine-tune with the same quantization scope; add distillation as a separate controlled change. Preserve masks during sparse recovery. Export and check quantization semantics, forward outputs, actual engine precision and the same metrics. Teacher outputs are references, not tablebase truth.

### W3-02 - S1 SparseGPT 2:4 (original Step 12)

- **Owner / priority / status:** A pruning, B builds/benchmarks / SHOULD / OPTIONAL_NOT_ENABLED.
- **Depends on:** C2, functioning S0 sparse execution and a bounded implementation budget.
- **Work/verification:** use calibration-only curvature/Hessian information for compensated pruning; verify the reduction-axis pattern and updated weights; recalibrate with the selected dense recipe; confirm actual sparse/INT8 execution and measure quality/speed. SparseGPT does not automatically change the active dense quantization scope (v1 excluded 37 weighted matrices; v2 excludes four).

### W3-03 - Study B2, policy/value swap (original Step 13)

- **Owner / priority / status:** A / MUST / NOT_STARTED.
- **Depends on:** frozen best INT8 and floating reference outputs, validated scoring and registered fixed-node search.
- **Work/verification:** use a small validated Python MCTS to swap policy/value outputs between complete F16 and INT8 networks. Compare both swaps with full-reference and full-INT8 search on matched positions/nodes. Keep this study at fixed nodes; two network evaluations make its timing incomparable to ordinary lc0 inference. Merely leaving one small head floating would not isolate body-generated policy/value error.

### W3-04 - Study C, fixed-time evaluation (original Step 14)

- **Owner / priority / status:** B / MUST / NOT_STARTED.
- **Depends on:** C2, verified lc0 integration, frozen compared models and W1-B06 protocol.
- **Work/verification:** compare R32_CUDA, F16_TRT, best dense INT8 and best verified sparse INT8 when available at **one second per root**. Same physical GPU, matched search/reset conventions, no tablebase assistance, repeated warmed runs and logged conditions. Save actual elapsed time, overshoot, nodes/evals and tablebase correctness with paired uncertainty. Resolve timing-clock inconsistencies before final absolute latency claims.

### W3-05 - matches (original Step 15)

- **Owner / priority / status:** A/B openings, B execution / MUST subject to a registered feasible budget / NOT_STARTED.
- **Depends on:** frozen best candidates and stable timed engine operation.
- **Work/verification:** register opening pairs, colors, seed, adjudication/rule settings and stopping criteria. Original target: about 1,000 best-INT8 versus F16 games at 100 ms per move, with sparse comparison if feasible. This match condition is separate from the one-second tablebase study. Report actual games and Elo uncertainty; a shortened budget is an explicit revision, not an unnoticed omission or guaranteed statistical conclusion.

### W3-06 - energy per node and equal-energy accuracy (original Step 16)

- **Owner / priority / status:** B / MUST within supported instrumentation / NOT_STARTED.
- **Depends on:** W1-B08 validation and stable frozen engine configurations.
- **Work/verification:** measure supported GPU and CPU energy above idle, units/counter behaviour, integration/sampling uncertainty and measurement boundaries. Report joules/node and equal-energy accuracy for the floating references and best verified quantized candidates. A missing CPU counter is an explicitly limited measurement; GPU power alone is not whole-machine energy.

### W3-07 - search minibatch sweep (original Step 17)

- **Owner / priority / status:** B / MUST / NOT_STARTED.
- **Depends on:** frozen models, registered search protocol and memory feasibility.
- **Work/verification:** investigate throughput and fixed-node/fixed-time accuracy over a declared feasible subset of the original 8-512 search-batch range; include the small-batch context from W1-A06P. Record actual batching/effective batches, latency/throughput, search quality and memory failures. Register selection using development/validation evidence.
- **Engine constraint:** the accepted F16 engine profile currently supports batches 1-8. Larger batches require explicitly versioned/validated derived profiles and engine identities; do not feed out-of-profile inputs or compare newly tuned INT8 against an unsuitable floating profile. Preserve old baselines and check numerical behaviour of new builds. Profile changes do not silently authorize new prediction drift.

### W3-08 - full per-layer roofline (original Step 18)

- **Owner / priority / status:** A analysis when QAT is dropped, B profiling; coordinate otherwise / SHOULD / NOT_STARTED.
- **Depends on:** final measured candidates and W1-A06P mapping/protocol.
- **Work/verification:** relate final layer timings to shape-derived work/bytes at one small and one larger batch, using measured conditions and justified compute/bandwidth references. Distinguish estimates from measured DRAM traffic and handle fusion/overhead without double counting. Original mapping effort is capped at one day; preserve unresolved attribution as a limitation. Explain remaining bottlenecks, especially retained floating large-weight/vector operations and conversion costs.

### W3-09 - optional sensitivity-based partial-INT8 extension (original undated afternote)

- **Owner / priority / status:** A/B / COULD, outside original proposal / OPTIONAL_NOT_ENABLED.
- **Enabling condition:** the best PTQ result has a clear validation/hard-subset accuracy problem, QAT was dropped, and the team explicitly registers the extension before C3.
- **Work/verification:** a bounded per-layer sensitivity study may retain one or two sensitive layers in higher precision. This is a separately named coverage variant with its own precision/coverage record and timed-study entry. It is not an already-approved expansion to all remaining FP16 weights, nor permission to tune on final test errors. Distinguish it from W1-A06R's earlier performance-driven coverage review.

**C3 acceptance:** all mandatory enabled comparisons completed; optional branches have results or explicit closures; model/engine identities, scopes, configurations and final result logs frozen. Do not start new models or experiments after C3 without reopening the gate in a recorded revision.

## 7. Week 4: analysis, reproduction and delivery

| Stable ID | Owner / priority / status | Work | Verification/deliverable |
| --- | --- | --- | --- |
| W4-01 | A / MUST / NOT_STARTED | Analyse the quantization ladder, network/fixed-node results, node-equivalents, swaps and activation outliers | Every table/plot traces to frozen per-position/run evidence; uncertainty and negative findings retained |
| W4-02 | B / MUST / NOT_STARTED | Analyse timed accuracy, matches, profiles, roofline, energy and batch-size effects; assemble accuracy-versus-nodes/s frontier | All points identify graph/engine, actual precision/coverage, workload and timing conditions; no layout-only sketches passed off as results |
| W4-03 | A / MUST / NOT_STARTED | Write background, methods, quantization ablation, NN/fixed-node and policy/value results | Explain reviewed mixed-precision scope and actual floating exceptions; do not describe selective W8A8 as every parameter being INT8 |
| W4-04 | B / MUST / NOT_STARTED | Write harness, TensorRT pipeline, measurement protocol, timing/energy and hardware findings | Actual backend/partition/precision evidence and unavailable instrumentation disclosed; separate runtime changes from precision effects |
| W4-05 | A+B / MUST / NOT_STARTED | Joint abstract/introduction/related work/discussion/limitations/conclusion; independently check sources and quoted prior results | Research questions answered with measured outcomes, including no-speedup/no-quality-gain outcomes; one network/device and endgame/engine limitations clear |
| W4-06 | A+B / MUST / NOT_STARTED | Reproduce from a clean checkout/environment using documented artifact acquisition and pinned versions | Verify checkpoint/graph hashes, data and recipes. Exact accepted engine reuse and tactic variability/engine-specific acceptance are documented; do not promise bit-identical rebuilds without evidence |
| W4-07 | A+B / MUST / NOT_STARTED | Package source, configurations, model/wrapper identities, calibration/split manifests, logs, final report, presentation and an lc0 demo | Audit all final numbers against logs; provide reproduction commands and intended artifact locations; demo uses the measured engine/configuration |

**C4 acceptance:** checked report/code/artifacts/presentation with a successful documented reproduction test or explicit unresolved limitations. Original final outputs include T1 ablation, T2 speed/precision coverage, T3 energy, T4 matches, T5 sparse probe; figures for the ladder, fixed nodes, node-equivalents, swaps, timed accuracy, roofline/profile, energy, batch sweeps, frontier and outliers. Report unsupported/dropped optional outputs explicitly rather than fabricating them.

## 8. Open decisions and boundaries

| Decision | Owner / due task | Current state |
| --- | --- | --- |
| Retain or expand the 127-operation starting scope | A, coordinate B / W1-A06R and A07 gate | A-side CLOSED: v2 selects 160, actual standalone execution checked; B integration/joint review remains open |
| Actual contribution of excluded operations to latency/bandwidth | A/B / W1-A06P | Instrumented layer-time contribution measured (14.61% at B1); profiler overhead disclosed; no DRAM counters/conclusive bandwidth classification |
| Exact scope-review candidate/probe budget and acceptance criteria | A / before any probe in A06R/A07 | FROZEN before measurements: two coverage candidates, prefer 160 if normalized latency allowance <=1.10 at B1/B8 and actual execution checks pass |
| Node budgets, reset/cache/search and batching protocol | B with A / W1-B05 before studies | OPEN; original provisional node list is not frozen |
| Full split counts/coverage and hard-subset threshold | A/B / W1-A08/A09 before INT8 final testing | Historical input-v1 freeze: 1,024/2,048/10,000; tau=-0.0938719019, 1,650 hard test roots at 0% baseline accuracy. Retained unchanged as old evidence; A13 settles input/holdout use; B04 owns any active hard-rule revision using validation before final testing. |
| Opset bridge behaviour and per-tensor ModelOpt adapter | A / W1-A07 | VERIFIED: opset 19 bridge has identical nodes/weights and matching outputs; explicit per-tensor adapter and exact placement audit pass |
| Input history and newly discovered larger F16 drift | User with A / A13-A14; share with B | History design agreed; apply/check inputs, refresh the two NN baselines, and explicitly record how remaining measured drift is handled. No requirement to eliminate inherent FP16 differences. |
| Final-test exposure and hard-subset usability | A13 for split use; B04 for hard-rule work | Agree data reuse/exposure before new final measurements. Hard-rule changes remain B/joint, validation-based and explicitly recorded. |
| Teammate's actual implementation state and checkpoint approvals | A+B / consolidation checkpoints | UNVERIFIED in this chat |
| Clock locking, stable timing clocks and CPU/GPU energy availability | B; A06P needs timing controls | NOT ESTABLISHED for final benchmarking; use logged supported alternatives |
| Training hardware, conversion viability, QAT/KD and sparse branch resources | A+B / W2-05 | Exact-operator conversion and one FP32 batch-1 backward check passed; optimizer memory, convergence and QAT/KD/sparsity branches remain OPEN |
| Large-batch profiles and feasible sweep range | B / W3-07, registered before final sweep | OPEN; current accepted engine is limited to batch 8 |
| Match budget and statistical stopping rule | A+B / W3-05 before execution | OPEN; original approximate target retained as a target |

Do not resolve an experimental acceptance decision silently. Routine implementation choices within the selected task can proceed in the user's execution mode. Unexpected numerical drift, changed precision definitions, changed datasets/metrics or changed comparison scope require a clear recorded decision before dependent final evaluation. The original plan requires both people to agree to model-format, precision-definition, test-set or metric changes after Week 1; this A-side record cannot manufacture that agreement.

## 9. Revision and progress maintenance protocol

For a material roadmap change, increment the roadmap version and append a revision row with date, authority, reason, old/new behaviour, affected task IDs, impact on evidence and approval state. Do not erase a failed candidate, previous numerical gate or superseded scope. Preserve versioned artifacts and identify the active one here.

For ordinary progress, update the task/current-state status, last-updated date and execution log. A status-only update need not increment the design version. Add actual evidence paths only after the files exist. When a gate fails, record the failure, completed checks, remaining dependency and concrete next action; never change a threshold merely to obtain a pass.

Review changes to an existing frozen contract through a versioned addendum/new record. Do not edit Step 5 or Step 6 frozen documents in place and invalidate their manifests just to reflect this roadmap's current progress. The baseline acceptance and inventory remain valid historical evidence while the suitability of the scope is reviewed.

### Revision log

| Revision | Date | Authority / state | Change and reason | Affected work / evidence impact |
| --- | --- | --- | --- | --- |
| R1.0 | 2026-10-26 | Direct user instruction: proceed with the profiling recommendation and create the updated reference/progress roadmap; APPROVED A-side sequencing | Create this active four-week roadmap. Insert W1-A06P and W1-A06R because 97% MAC coverage does not validate leaving 37.33% of matrix weights floating. Require reviewed and backend-validated coverage before the main ladder. | A06 inventory stays DONE; its placement becomes REVIEW_REQUIRED as a final scope. A07 now depends on A06R. Week 2 requires the coverage gate. No model, engine, original numerical bound, scoring definition or frozen artifact changed. No teammate approval or experiment execution is claimed. |
| R1.1 | 2026-10-26 | Direct user authorization to complete remaining A-side Week 1 autonomously; routine reviewed scope choice delegated | Profiled exact baselines; registered/tested 127 versus 160 targets; v2 selects 160 under the predeclared latency allowance. Verified pilot, complete datasets, baseline measurements, activation analysis and trainable-port feasibility. | Original Step 5/6 frozen artifacts unchanged. New full-data FP16 drift opens an essential acceptance gate at A09/A12; old acceptance not extended. Original hard subset retained despite its baseline floor effect. B/joint C1 and Week 2 remain unopened. |
| R1.2 | 2026-10-27 | User explicitly requested planning plus discussion/agreement before every remaining implementation step. Workflow ACTIVE; technical sequence PROPOSED pending roadmap approval. | Add R01-R08 to resolve input/fidelity questions and complete original Week 1 deliverables. Correct stale summary rows, distinguish historical results from active reuse, and map the six proposed remedies back to their existing weeks. | No new experiment, calibration, baseline acceptance or model change executed. Later-week ladder, training, full batch/roofline/energy/timed studies remain in place. Original frozen manifests remain untouched; current roadmap/progress are intentional planning revisions of their earlier snapshot versions. |
| R1.3 | 2026-10-27 | User requested minimal planning; simplified R01 PROPOSED, not implementation approval. | Replace the unapproved large R01 comparison proposal with three targeted checks using a small fixed sample and known problem cases. Carry forward the agreed history convention and original fidelity bounds. | No experiment performed. Full data/baseline evaluation remains R03; profiling remains R02; original Week 1 deliverables and later-week boundaries are retained. |
| R1.4 | 2026-10-27 | User requested minimal stepwise completion of Person A work, agreement before every implementation; sequence PROPOSED. | Replace unexecuted R01-R08 proposals with five A-only steps A13-A17. Put data-use agreement before refreshed measurements; preserve history agreement and verified prior work. Ordinary FP16 drift and a negative naive INT8 pilot are observations, not automatic optimization tasks. | No experiment or new drift acceptance executed. B responsibilities/joint C1 remain separate; original frozen artifacts and later-week studies remain intact. |
| R1.5 | 2026-10-27 | Current user approved revised Step 1 roots from the allowed 4/5/6/7 range and Codex implementation; A13 DONE. | Selected published four/five-piece game roots or documented color/rank mirrors, preserving 1,024/2,048/10,000 counts. Verified source membership, separate games/symmetry groups, official tables, root/child labels and native fen_only planes. Corrected the narrower stale 6/7-only tracker description. | Active data is data/syzygy-v2. Old datasets, models, raw failures and frozen manifests preserved. Shape/NN graph unchanged; no NN inference, INT8 recalibration or training run. A14-A17 still require agreement. |

Earlier experimental decisions are sourced rather than assigned invented roadmap revisions: the initial contract/encoding on 2026-10-21; the user's two-baseline definition, first-engine drift acceptance and verified inventory on 2026-10-25; and the 2026-10-26 clarification that selective INT8 coverage needs performance justification. See the linked contract and Step 5/6 evidence for their exact records.

### Execution log

| Date | Task | Status / verified result | Evidence / next action |
| --- | --- | --- | --- |
| 2026-10-21 | W1-A01 through W1-A04 | DONE; environment/checkpoint/input/pilot boundary established | Existing environment, Step 3 and Step 4 reports; no new claim about tablebase accuracy |
| 2026-10-25 | W1-A05 (5A-5G) | ACCEPTED_WITH_DRIFT; preserved first F16 engine and both baselines verified | Step 5 final manifest/acceptance; raw confirmation remains failed |
| 2026-10-25 | W1-A06 inventory | DONE; scope v1.0 generated and static checks passed | Step 6 inventory/scope/verification; actual INT8 execution not started |
| 2026-10-26 | R1.0 roadmap amendment | Created the approved early profiling/scope-review sequence; verified all 43 task IDs, local links and unchanged Step 5/6 frozen-artifact hashes | This document; next task W1-A06P awaits execution-mode selection. Documentation only; no profiling or INT8 execution performed. |
| 2026-10-26 | W1-A06P/A06R/A07 | DONE A-side: exact-baseline profile, registered coverage decision, two actual INT8 engines and selected 160-operation wrapper verified | `environment/week1-baseline-profile.json`, `step6-scope-v2.json`, `week1-int8-pilot.json` |
| 2026-10-26 | W1-A08 | DONE: 40 tablebase files and all 13,072 split roots/labels/encodings verified | `data/syzygy/manifest.json`; all 221 prior groups excluded |
| 2026-10-26 | W1-A09 | Full measurements complete; REVIEW_REQUIRED for larger FP16 numerical drift | Both baseline move accuracies 55.42%; native diagnostics confirm up to 23.24-point WDL drift; no automatic acceptance |
| 2026-10-26 | W1-A10/A11 | DONE: calibration-only channel analysis; trainable exact-operator forward/backward feasibility | `results/week1/calibration-outliers.json`, `environment/week1-torch-feasibility.json`; no optimizer/training |
| 2026-10-26 | W1-A12 | Technical audit verified; AWAITING_USER_DECISION | `environment/week1-audit.json`, `docs/week1-person-a-handoff.md`; stop at new baseline acceptance gate |
| 2026-10-27 | R1.2 completion planning | PROPOSED, implementation NOT_STARTED | Checked original Week 1 assignments; added concerns, deliverable inventory, eight discussion-gated completion steps and later-week boundaries. No technical choice is approved by writing this plan. |
| 2026-10-27 | W1-R01 discussion | DISCUSSION, implementation NOT_STARTED | User said "begin with step 1". Reviewed existing input/tolerance records and pinned encoder source; begin with the history convention before agreeing the implementation protocol. |
| 2026-10-27 | W1-R01 history decision | Design AGREED; implementation NOT_STARTED | User agreed native fen_only for standalone FENs and preservation of real history. Comparison coverage, gates, budget/failure handling and execution mode remain under discussion. |
| 2026-10-27 | W1-R01 minimal replanning | PROPOSED, implementation NOT_STARTED | User rejected excessive protocol complexity. Replaced unapproved comparison scope with three targeted checks; agreed history decision retained. |
| 2026-10-27 | R1.4 Person A completion planning | PROPOSED; implementation NOT_STARTED | Recorded five discussion-gated A-only steps for the six remaining issues; no calibration, inference, training or acceptance performed. |
| 2026-10-27 | W1-A13 discussion | DISCUSSION; implementation NOT_STARTED | User said "begin". Proposed reuse of existing splits with test-exposure disclosure, versioned corrected inputs and basic encoding/disjointness checks; agreement and execution mode remain open. |
| 2026-10-27 | W1-A13 implementation authorized | IN_PROGRESS | Earlier tracker recorded Codex authorization with a narrower 6/7-only description; R1.5 aligns it with the current user instruction allowing 4/5/6/7. Counts unchanged. |
| 2026-10-27 | W1-A13 implementation and verification | DONE | environment/week1-input-refresh.json; 13,072 roots/source pairs/native planes, all root-child WDL checks, 22 fixtures and 290 table files verified. Next: A14 discussion. |
| 2026-10-27 | Combined A14-A17 discussion | PROPOSED; implementation NOT_STARTED | User requested one agreement covering all four remaining steps, then autonomous verified progression. Current model/data identities and old evidence preserved. |

### Resume checklist for the next Codex turn

- Read the five-step R1.4 Person A roadmap and the latest user agreement. The old R01-R08 proposals are superseded; do not resume their larger scope.
- A13 is DONE: use active data/syzygy-v2 and its verification report. Discuss/agree A14 protocol and mode before NN inference. Historical scripts hardcode old paths; adapt to the active version before running them.
- Reuse verified checkpoint, exports, operation inventory, scope, tablebase files/labels and reconstruction. Refresh affected results without overwriting historical frozen evidence.
- After each agreed step, verify/report and update progress before opening the next discussion. Return concrete faults or changed scope to discussion; do not manufacture a speed/accuracy target or silently waive a numerical failure.
- A17 closes Person A work only. B04 owns DTZ/hard-set issues; B01-B08 and joint C1 remain separate. No Week 2 experiment is authorized by this planning update.

### Autonomous execution checkpoints

The following are the historical 2026-10-26 autonomous-run checkpoints. They retain their evidence and do not override the new discussion protocol or the active reuse limits above.

- **W1-A06P: DONE** - [environment/week1-baseline-profile.json](../environment/week1-baseline-profile.json). Accepted engine profiled without rebuild at batches 1/4/8; actual excluded-weight layer contribution recorded; precision/shape evidence preserved.
- **W1-A06R: DONE** - [environment/step6-scope-v2.json](../environment/step6-scope-v2.json). Final common scope v2 selected 160 targets after the registered actual-execution and latency checks; 99.9905% unique matrix-weight coverage, no accuracy-driven placement.
- **W1-A07: DONE** - [environment/week1-int8-pilot.json](../environment/week1-int8-pilot.json). A-side naive INT8 graph, actual precision, saved-engine reload, coverage choice and byte-identical lc0 wrapper verified. B-side GPU integration remains unverified; C1 is not complete.
- **W1-A08: DONE** - [data/syzygy/manifest.json](../data/syzygy/manifest.json). All 13,072 roots, legal child outcomes and native encodings verified; all split groups disjoint and exclude 221 prior groups. Validation-based hard threshold subsequently frozen in A09.
- **W1-A09: REVIEW_REQUIRED** - [environment/week1-baseline-drift-review.json](../environment/week1-baseline-drift-review.json). Full baseline accuracy measurements are complete, but final numerical audit found larger FP16 WDL drift; native checks confirm the discrepancy. Existing acceptance is not extended silently.
- **W1-A10: DONE** - [results/week1/calibration-outliers.json](../results/week1/calibration-outliers.json). All calibration-only per-channel maxima/means/RMS, named consumers, plots and a bounded validation-only smoothing search recorded.
- **W1-A11: DONE** - [environment/week1-torch-feasibility.json](../environment/week1-torch-feasibility.json). Exact-operator FP32 forward parity and a batch-1 finite-gradient/memory check verified. No optimizer step, QAT or distillation performed.
- **W1-A12: AWAITING_USER_DECISION** - [environment/week1-audit.json](../environment/week1-audit.json). Technical evidence audit passed. Newly observed FP16 baseline drift requires explicit acceptance or reopened engineering. B work/joint C1 remain unverified; no Week 2 work begun.


### Approved combined execution amendment (2026-10-27)

The user explicitly agreed A14-A17 and authorized autonomous Codex execution with verification between steps. This replaces separate discussion/mode gates for this block only. A15 now includes a broad batch-size sweep and refinement, with separate preserved and expanded-profile timing engines, and explicit batch-latency versus amortized-throughput reporting. FP16 numerical drift is disclosed rather than forced to match FP32; genuine correctness faults still require repair. See [active protocol](../environment/week1-v2-protocol.json). Earlier awaiting-agreement text is historical.

### Verified active completion block (2026-10-27)

- **W1-A14: DONE** - Floating baselines and native/batch correctness verified on active data; raw FP16 drift and all-split chosen-move accuracy saved. Next: naive INT8 refresh and broad batch sweep. ([evidence](../environment/week1-v2-baselines.json))
- **W1-A15: IN_PROGRESS** - Recalibrating fixed 160-operation naive INT8 recipe on all 1024 v2 calibration roots only.
