# Shared project status

Updated 29 October 2026. Authoritative plan: `updated_plan.md`. Detailed history: `LOG.md`; original imported status: `archive/person-b-import/STATUS.md`. Status below is saved progress, not a live process monitor.

| Workstream | State | Evidence / next closure |
|---|---|---|
| Repository consolidation | Completed | 10,722 original files preserved with matching hashes; 328 transferable artifacts verified; six regression tests and exact reproduction of five saved scoring outputs passed. See maintenance/consolidation-verification.json. |
| Person A Run 1 | Completed independent block — A5 deferred | A1–A4 and A6–A10 available/preparation portions verified; 7 regression tests, 350 frozen-source hashes and 5 figure visual reviews passed. Address A5 BEFORE Run 2; see analysis/person_a/BEFORE_RUN_2.md. |
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
| Final figures/tables | In progress | F1–F4 + hard supplement and A tables verified/visually reviewed. F12 is deferred; systems/F11 outputs await Ritwik. |
| Report/presentation/demo | In progress — A draft/preparation ready | A report/references, slide outline, demo and reproduction plans and deliverable checklist exist. Final shared outputs remain pending. |
| Fresh experimental reproduction and C4 audit | Pending | Consolidation checks are not the final scientific reproduction. |

Current source/model/runtime conventions are Person B's accepted trimmed pipeline. F8/F10, training/search-calibration/partial-INT8 branches and CPU energy are outside the adopted scope. Do not reopen them as implied tasks.
