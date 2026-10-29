# Shared project status

Updated 30 October 2026. Authoritative plan: `updated_plan.md`. Detailed history: `LOG.md`; original imported status: `archive/person-b-import/STATUS.md`. Status below is saved progress, not a live process monitor.

| Workstream | State | Evidence / next closure |
|---|---|---|
| New five-run takeover | Run 1 normal preparation completed; Run 2 awaits exclusive start | Anjan/Codex now executes remaining B work and A integration. 40 offline tests; scoped PATH/static x64 checks; 45-job manifest; original 350 inputs preserved. No GPU validation/measurement yet. See reports/takeover/progress.json and run1/verification.json. |
| Repository consolidation | Completed | 10,722 original files preserved with matching hashes; 328 transferable artifacts verified; six regression tests and exact reproduction of five saved scoring outputs passed. See maintenance/consolidation-verification.json. |
| Person A Run 1 | Completed independent block — A5 resolved | A1–A10 available/preparation portions verified. A5 traced the old arrays to C1; the final-model CPU diagnostic verifies all 768 channels. F12 completed; see analysis/person_a/a5/closure.json and BEFORE_RUN_2.md. Final systems/shared delivery remain pending. |
| FP16/INT8 lc0 setup and wrapping gate | Completed | reports/C1-done.md; earlier INT8 capture under reports/trt/. |
| Dense s1-s4 recipe selection/build | Completed | reports/C2-recipe-choice.json, C2-build-manifest.json; best=s4. |
| Main network/fixed-node studies | Completed | reports/scores_test.md/json; n=2437 test roots. |
| s4aa, SparseGPT and both swaps | Completed | Models, sidecars, main A/B results. SparseGPT accuracy loss is a completed finding. |
| Magnitude pruning | In progress | Model/raw and supplemental search results exist; sparse hardware probe pending. |
| Hard low-budget follow-up | Completed analysis | Six models × five budgets on 43 roots consolidated; actual-node/paired counts retained; supplementary figure reviewed. |
| Fixed-time Study C | In progress — A review ready | All 2437 IDs matched at 200/800ms; actual node/time/paired table and provisional interpretation ready. B owns canonical final report/F5. |
| Basic speed/GPU energy/reduced batch sweep | Completed, preliminary | reports/c3_hw/bench and batch_sweep. Headline repeats/final variability summary remain. |
| Detailed profiles, precision/sparse coverage and roofline | In progress — BLOCKED | Saved nvinfer_plugin_10.dll load failure; reports/c3-part1/state.json. No retry during consolidation. |
| All-model comparable frontier speed | Pending | Benchmark each included single-body model; separate lc0 from standalone sparse trtexec results. |
| Matches and Elo/CI | Pending | Runtime estimate, final pair count and matches not completed. |
| Dataset final integrity closure | A-side audit complete; shared closure pending | Seven cross-split groups; affected measured IDs 611/627/965 documented. Primary corpus unchanged; final shared package/audit still pending. |
| Final figures/tables | In progress | F1–F4, F12, hard supplement and A tables verified/visually reviewed. Systems/F11 outputs await Ritwik. |
| Report/presentation/demo | In progress — A draft/preparation ready | A report/references, slide outline, demo and reproduction plans and deliverable checklist exist. Final shared outputs remain pending. |
| Fresh experimental reproduction and C4 audit | Pending | Consolidation checks are not the final scientific reproduction. |

Current source/model/runtime conventions are Person B's accepted trimmed pipeline. F8/F10, training/search-calibration/partial-INT8 branches and CPU energy are outside the adopted scope. Do not reopen them as implied tasks.

Current sequence: docs/takeover_runs.md. Remaining R1–R5 evidence will be produced here; old references to awaiting Ritwik describe the earlier division of labor. Next exclusive Run 2 is provisionally 3–7 hours (reserve up to 8); no production matches until Run 4. Its known plugin failure remains unverified until the GPU probe.
