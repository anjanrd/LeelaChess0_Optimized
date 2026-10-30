# Five-run autonomous takeover

Accepted by Anjan on 30 October 2026. Remaining Person B work is now executed here by Codex on `anjan`, alongside the waiting A-side work. This workflow absorbs the former Person A autonomous Run 2. The scientific scope and completed evidence in `updated_plan.md` remain authoritative.

| New run | Mode | Work and completion gate |
|---|---|---|
| 1 | Normal; laptop usable | Verify evidence/runtime layout; prepare checked commands, counters, persistence and tests. Complete when CPU checks and input/command manifests verify. No GPU experiments. |
| 2 | Exclusive | Scoped TensorRT PATH fix and real GPU probe; profiles/sparsity/ceilings; eight-model repeated benchmarks and precision captures; two-game match estimate. Collect R1/R2 and pilot evidence for Run 3 review. |
| 3 | Normal; laptop usable | Review conditions and precision evidence; finish available A6/A7/frontier and canonical existing timed reporting (R3); finalize match size before production; prepare a fresh environment and declared reproduction subset. |
| 4 | Exclusive | Fresh FP16/s4/sparse GPU reproduction first; production paired match (R4); capture demo after measurements; retain runtime/reproduction evidence (R5). |
| 5 | Normal; laptop usable | Final paired statistics, A/B writing/figures/report/deck; artifact bundle/restore and reproduction reconciliation; retained-deliverable audit and C4. Requires unresolved required profiling work to be closed. |

If the initial GPU probe still fails with the known plugin-load error, preserve it and defer only that standalone profiling/ceiling branch. Independent lc0 captures, benchmarks and the pilot continue. F6 and affected T2/T5 portions remain pending. Insert a later exclusive profiling/repair block before Run 5 sign-off if necessary. Other unexpected failures stop execution for review.

## Current checkpoint

Runs 1 and 2 are complete. Run 2 has 45 verified job identities: 35 preserved original jobs and ten approved-policy continuation jobs under `reports/takeover/run2/codex-continuation-v2/`. All 28 benchmark trials and two pilot games are verified. The pilot measured26.9723seconds/game;250 pairs provisionally estimate3.7461hours before overhead/uncertainty. Final match size is frozen in Run 3, not inferred from the two pilot outcomes.

The original CPU-resource failure is preserved. The manual route passed its quiet preflight and recorded retry review, but failed before any GPU work because Windows virtual-environment Python adds an intermediate process and the worker gate assumed a direct PID relationship. That failure and its original source/session/review remain unchanged. The user then explicitly authorized Codex orchestration with background-interference flags informational. The separate v2 controller/manifest records that policy; it does not alter the old guard, model/search commands or failed evidence. AC, monitor errors, one-workload locks and command/output/identity validation remain enforced. Do not relaunch legacy/manual commands against the preserved original state.

Closure verified 72 frozen continuation inputs and 558 output files (2,157,379,271 bytes), exact model trial counts,112 NN-batch rows,280 actual-node/time search records and two pilot games. All62 offline tests pass. No new background flags were observed. The initial implausible idle-power query is preserved for energy review; measured search counter/sample means agree within0.60%. GPU idle/process shutdown, released awake request and absent active locks were checked. Next is normal Run 3: final precision/sparse/roofline, thermal/session/variability/frontier/timed review, sizing and reproduction preparation. No Run 3, production match, commit or push has started.

Execution code is in `execution/`. Original A-side outcomes, A5/F12 and prior manifests are preserved as historical checkpoints. `analysis/person_a/readiness.py` still describes the old final-integration intake; its waiting R1–R5 state does not mean this takeover waits for Ritwik.

Current metadata: `reports/takeover/progress.json`. Original freeze: `reports/takeover/run1/run2_jobs.json`. The v2 continuation manifest links the immutable original manifest/state, its35 reusable jobs and the ten newly collected jobs. An initial CPU-only draft is preserved in `run1/initial-cpu-draft/`; it is historical preparation, not an execution target.

## Run 1 outputs and execution checks

- All 350 original source/evidence identities are preserved; source/config/model bytes are not rewritten. Original A5 diagnosis and measured pair remain unchanged.
- `execution/support.py`: structured argv, scoped child PATH, strict records, OS-temporary atomic JSON commits and a single-workload lock. TEMP must share the destination volume and remain outside the checkout.
- `execution/benchmark.py`: fail-closed exit checks and required NN/search/energy data; actual per-position visits/time; four NN batches and common search settings. Build/warm-up/conditioning are excluded from measured intervals.
- `execution/match_runner.py`: calls the imported `Game.play` without altering clocks, openings or adjudication. Atomic game+PGN envelopes recover interrupted aggregate exports. Model/rule/settings identities prevent incompatible resumption. A separate two-game pilot is retained. Degenerate/clipped imported intervals are flagged, rather than presented as reliable uncertainty.
- `execution/resources.py`: read-only Windows process/AC observations plus NVML during jobs. It never terminates a process. WDDM graphics visibility is limited, so closing nonessential applications and pausing other work remain necessary.
- `execution/gpu_job.py`: exclusive-gated probe, profile, ceiling and lc0 capture commands. Import/CPU tests do not start them.
- `execution/run_jobs.py`: default plan mode; explicit exclusive-session gate for execution; sequential, checksummed job attempts; verified-checkpoint reuse; raw/engine artifact checks; recorded BLOCKED states on errors. Scientific interpretation is reviewed in Run 3.

The adopted measurement settings and procedural diff are recorded in `execution/protocol.json` and `docs/takeover_protocol_note.md`.

## Before each exclusive run

At the preceding run's handoff, Codex must state the next run is exclusive, give an updated duration estimate and repeat these preparations:

1. Anjan saves work and pauses laptop use. Plug into AC, keep the lid open and cooling unobstructed, and keep one documented power/performance mode across experimental sessions. Normal runs permit unrelated work; avoid changing LC0 files/runtime concurrently.
2. Close nonessential applications and stop competing jobs/VMs/downloads/sync. Codex may gracefully close or terminate identified nonessential user processes after work is saved. Preserve Windows, security, drivers, Codex and experiment processes. No blanket process-name kill for all Python/system tasks.
3. Inspect current GPU processes, CPU/background activity, AC state, power mode and temperature. Record the observations and closed job PIDs. Do not act on historical controller PIDs. Wait for quiet conditions before starting.
4. Make a fresh exclusive-session record from `reports/takeover/run1/exclusive_session_template.json`. Its default flags are false and cannot authorize execution. Runtime identity contains stable GPU UUID/driver/power mode fields; temperatures/clocks belong in observations, not the stable fingerprint. Confirm actual resource preflight; booleans alone are not proof of isolation.
5. Run one GPU workload at a time. Keep lightweight monitoring; do not run unrelated rendering/analysis during measured intervals. Headline throughput/energy excludes profiler and screen-recording overhead. Clock locking was previously denied; record floating clocks and thermal behavior honestly.
6. The controller flags nonessential application presence, external compute PIDs, AC disconnection and sustained external CPU activity (>5% of total logical-machine capacity over 3 consecutive 2-second samples). Preserve flagged attempts and stop for review. Do not discard results because they are slow or unfavorable. Unknown/short graphics interference can require manual review even without an automatic flag.

## Run 2 commands and resumption gate

Safe inspection only:

```powershell
.\.venv\Scripts\python.exe -B -m execution.run_jobs
```

Only after an explicitly started exclusive Run 2 and the real session preflight; a recorded BLOCKED attempt additionally requires explicit review before retry:

```powershell
.\.venv\Scripts\python.exe -B -m execution.run_jobs --execute --session reports/takeover/run2/session.json
```

The child environment prepends `.runtime/tools/TensorRT-10.12.0.36/lib` and the lc0 tool directory to PATH. It does not change the machine-wide PATH or swap DLL files. Static PE checks and a CPU child PATH check passed in Run 1; actual GPU loading and all six full profiles passed in Run 2. Historical plugin failures remain preserved.

The 45-job order is frozen: one small probe; six model profile jobs (FP16/s4 each reuse one engine at batches64/256; four sparse/dense configurations at256); one three-microbenchmark ceiling job; eight actual lc0 captures; 28 benchmark trials; a two-game pilot. Headline FP16/s4 each have five trials with alternating adjacent order; the other six models each have three with rotated order. The pilot uses the same imported 10+0.1 rules; 250 pairs remains provisional until Run 3 sizing.

Estimated exclusive Run 2: **3–7 hours; reserve up to 8 hours for the first session**. This is a planning range, not a measured ETA. There are at least14minutes of common conditioning, about9minutes of idle observations, and up to47minutes of requested search time across28 trials, plus NN measurements, cold caches, profile/ceiling builds, captures and pilot. Compilation/cooling dominate the uncertainty. Refine the estimate after the first real build. Production matches are in Run 4, whose estimate must use the pilot.

## Resumption and preservation

Every attempt has its command log, activity log, condition review data and receipt. Completed raw logs, detailed profiles, engines and traces are checksummed as well as summary JSON. Verified jobs are skipped only when source/manifest/runtime/output identities agree. Different settings/runtime need a new reviewed execution version; never silently pool conditions.

An interrupted controller can leave `ACTIVE.json`. Confirm the owner process and all experiment children are stopped before explicitly removing a stale lock; preserve its identity and log the action. Never start a second GPU controller alongside a live one. Failed attempts are not automatically retried. An interrupted unverified short job can be repeated after review; retain the old attempt. Production matches recover committed individual games under the same frozen contract; corrupt/mismatched records are not silently skipped.

Store models/engines/traces/raw logs locally with inventories. New numerical metadata stays Git-visible. Keep OS temporary files outside the project. No commit/push or teammate message is implied by execution authorization.
