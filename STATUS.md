# Shared project status

Updated 30 October 2026 after normal Run 3. Authoritative plan: `updated_plan.md`; detailed commands/history: `LOG.md`. This is saved progress, not a live process monitor.

| Workstream | State | Evidence / next closure |
|---|---|---|
| Five-run takeover | Runs 1–3 complete; exclusive Run 4 prepared, not started | `reports/takeover/progress.json`; `reports/takeover/run3/EXCLUSIVE_RUN_4.md`. Explicit user start required. Plan 5–6 hours, reserve 7. |
| Repository consolidation | Completed | Original 10,722 files preserved; 328 transferable artifacts verified. `maintenance/consolidation-verification.json`. |
| Original A Run 1 and A5/F12 | Completed independent block, A5 resolved | C1/final-model mismatch diagnosed; all 768 final-model channels verified. Original failure preserved. `analysis/person_a/a5/closure.json`. |
| FP16/INT8 pipeline and dense ladder | Completed | C1/C2 reports and manifests; s4 remains the preselected recipe. |
| Main network/fixed-node, hard follow-up, swaps and sparse quality | Completed | Original main scores plus A tables/figures; sparse losses are findings, not unfinished implementations. |
| Fixed-time Study C | Completed canonical analysis | Exactly 2,437 matched IDs at 200/800 ms; T6, F5 and original rows retained. No robust accuracy-per-second gain established. |
| Repeated performance and eight-model coordinates | Completed analysis | 28 valid trials; T2 and F11. s4 median 6,818 versus FP16 4,842 visits/s; session/thermal/clock variability disclosed. |
| Precision, profiles, sparse tactics and roofline | Completed bounded audit | T2/T5 and F6: 164 fixed-weight INT8 GEMMs prove 97.8517% of matrix arithmetic in standalone s4; 30 attention MatMuls unresolved. lc0 traces prove execution, not full operation coverage. Sparse standalone tactics selected, modest 6–8% gain. |
| GPU energy | Outputs complete; idle subtraction provisional | T3/F7 retain total and above-idle metrics. 49 impossible inactive power samples across 23 trials prevent validating historical idle baselines. Under-load counter/sample means agree within 0.60%; Run 4 controlled idle check prepared. No CPU/equal-energy claim. |
| Match and Elo/CI | Size frozen; production pending | 250 pairs/500 games, unchanged 10+0.1 rules and 50-opening book. Two-game duration pilot is planning only. Production Run 4; paired/opening-aware statistics Run 5. |
| Dataset integrity | A audit complete; final packaging pending | Seven cross-pool symmetry groups, three measured IDs affected; limits documented without changing original corpus. |
| Figures/tables | Available analysis complete; match outputs pending | F1–F7, F9, F11/F12 and supplements available; F8/F10 omitted. F6 is a partial, explicitly scoped roofline; F7 idle qualification retained. |
| Fresh reproduction | Clean source/Python/artifact preparation complete; GPU validation pending | External clone at eb9e8cf, independently installed 21 pinned packages, verified 758 MB subset. Same native host/tools reused. Fifteen checked Run 4 jobs prepared; no GPU reproduction yet. |
| Final report/deck/video/full package/C4 | Pending shared final integration | Run 4 actual measurements/demo capture, then normal Run 5 reconciliation, rendered deliverables and audit. |

Run 3 details: `analysis/person_a/run3_findings.md`. No GPU workload, process termination, model/cohort/scorer change, commit/push or teammate message occurred in Run 3. Original Run 2 frozen inputs/outputs and failure evidence remain preserved. Background flags are informational under the user-approved continuation policy; AC, monitor errors, one-workload locks and exit/output/identity checks remain enforced. Codex activity is not assumed identical across trials.

The selected s4 supports the faster-inference/more-search portion of the hypothesis. Saturated timed accuracy and unrun production matches leave better quality per second/strength unproven. Magnitude pruning's accuracy/search-throughput regression, the adverse hard-root observation, modest standalone sparse gains and idle-energy limitation are explicitly retained. The cumulative alignment check is reported in conversation without a separate gate file.

Use the adopted trimmed pipeline. R32/search-calibration/training/equal-energy accuracy/batch-accuracy/CPU-energy branches remain omitted. Do not relaunch legacy/manual Run 2 commands or interpret old A-side external handoff waits as a new dependency on Ritwik.
