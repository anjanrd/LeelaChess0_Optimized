# Shared project status

Updated 30 October 2026. Authoritative plan: `updated_plan.md`. Detailed history: `LOG.md`; original imported status: `archive/person-b-import/STATUS.md`. Status below is saved progress, not a live process monitor.

| Workstream | State | Evidence / next closure |
|---|---|---|
| New five-run takeover | Runs 1 and 2 complete; normal Run 3 ready | Original 35 verified jobs plus ten v2 jobs cover all 45 planned jobs, 28 benchmark trials and two pilot games. Background flags are informational under the approved v2 policy; activity/AC/exit/output/identity checks remain. All experiment processes stopped, GPU idle and awake request released. Current verification/state: reports/takeover/progress.json and run2/codex-continuation-v2/state.json. |
| Repository consolidation | Completed | 10,722 original files preserved with matching hashes; 328 transferable artifacts verified; six regression tests and exact reproduction of five saved scoring outputs passed. See maintenance/consolidation-verification.json. |
| Person A Run 1 | Completed independent block — A5 resolved | A1–A10 available/preparation portions verified. A5 traced the old arrays to C1; the final-model CPU diagnostic verifies all 768 channels. F12 completed; see analysis/person_a/a5/closure.json and BEFORE_RUN_2.md. Final systems/shared delivery remain pending. |
| FP16/INT8 lc0 setup and wrapping gate | Completed | reports/C1-done.md; earlier INT8 capture under reports/trt/. |
| Dense s1-s4 recipe selection/build | Completed | reports/C2-recipe-choice.json, C2-build-manifest.json; best=s4. |
| Main network/fixed-node studies | Completed | reports/scores_test.md/json; n=2437 test roots. |
| s4aa, SparseGPT and both swaps | Completed | Models, sidecars, main A/B results. SparseGPT accuracy loss is a completed finding. |
| Magnitude pruning | In progress | Model/raw and supplemental search results exist; dense/sparse hardware profiles and three lc0 benchmark trials collected. Actual sparse-tactic interpretation remains for Run 3. |
| Hard low-budget follow-up | Completed analysis | Six models × five budgets on 43 roots consolidated; actual-node/paired counts retained; supplementary figure reviewed. |
| Fixed-time Study C | In progress — A review ready | All 2437 IDs matched at 200/800ms; actual node/time/paired table and provisional interpretation ready. B owns canonical final report/F5. |
| Basic speed/GPU energy/reduced batch sweep | Repeated measurement collection complete; final analysis pending | Five FP16/s4 trials each; three each for s1/s2/s3/s4aa/s0/s1sp. Original reduced batch sweep remains preserved. Final variability/thermal/session analysis and publication outputs are Run 3. |
| Detailed profiles, precision/sparse coverage and roofline | In progress — collection verified, interpretation pending | Scoped child PATH resolved the GPU plugin loader. Six profiles, three ceiling microbenchmarks and eight lc0 traces are retained under reports/takeover/run2/. Precision/fallback/sparse mapping and roofline analysis remain for Run 3. Historical failed evidence is preserved. |
| All-model comparable frontier speed | Measurement collection complete; frontier analysis pending | All 28 benchmark trials verified; old flagged attempt excluded and preserved. Run 3 integrates speed/quality, variability and session review. Keep lc0 and standalone trtexec measurements separate. |
| Matches and Elo/CI | Pilot complete; production pending | Two-game estimate: 26.9723 seconds/game; provisional 250 pairs estimates 3.7461 hours excluding broader overhead/uncertainty. Run 3 freezes final size; Run 4 runs production. Pilot is not strength evidence. |
| Dataset final integrity closure | A-side audit complete; shared closure pending | Seven cross-split groups; affected measured IDs 611/627/965 documented. Primary corpus unchanged; final shared package/audit still pending. |
| Final figures/tables | In progress | F1–F4, F12, hard supplement and A tables verified/visually reviewed. Systems/F11 outputs await Ritwik. |
| Report/presentation/demo | In progress — A draft/preparation ready | A report/references, slide outline, demo and reproduction plans and deliverable checklist exist. Final shared outputs remain pending. |
| Fresh experimental reproduction and C4 audit | Pending | Consolidation checks are not the final scientific reproduction. |

Current source/model/runtime conventions are Person B's accepted trimmed pipeline. F8/F10, training/search-calibration/partial-INT8 branches and CPU energy are outside the adopted scope. Do not reopen them as implied tasks.

Current sequence: docs/takeover_runs.md. Remaining R1–R5 work is executed here; old references to waiting for Ritwik describe earlier ownership. Original resource-flagged evidence and the manual launch's pre-GPU PID-gate failure remain unchanged. The user then explicitly authorized Codex orchestration and disabled background-interference blocking. A separate v2 manifest/session/output tree records that change; it does not relabel the original 35 jobs or accept the old flagged trial. Original controller/scientific code and model bytes remain unchanged.

Run 2 closure verified all 72 continuation inputs, 558 output files (2,157,379,271 bytes), exact 45-job coverage, model trial counts, positive per-position nodes/time/energy and two valid pilot games. All 62 offline tests pass. No background flags were logged in the ten new jobs. The initial implausible idle power query is preserved for telemetry review; measured search energy-counter/sample means agree within 0.60%. Cross-session/thermal/clock review, actual precision/sparse/roofline interpretation and final statistics are Run 3. The read-only cumulative alignment gate was reported in conversation, without a separate gate file. Run 3, production matches, commit/push and teammate messages have not started.
