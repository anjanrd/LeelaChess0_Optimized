# Shared project status

Updated 29 October 2026. Authoritative plan: `updated_plan.md`. Detailed history: `LOG.md`; original imported status: `archive/person-b-import/STATUS.md`. Status below is saved progress, not a live process monitor.

| Workstream | State | Evidence / next closure |
|---|---|---|
| Repository consolidation | Completed | 10,722 original files preserved with matching hashes; 328 transferable artifacts verified; six regression tests and exact reproduction of five saved scoring outputs passed. See maintenance/consolidation-verification.json. |
| FP16/INT8 lc0 setup and wrapping gate | Completed | reports/C1-done.md; earlier INT8 capture under reports/trt/. |
| Dense s1-s4 recipe selection/build | Completed | reports/C2-recipe-choice.json, C2-build-manifest.json; best=s4. |
| Main network/fixed-node studies | Completed | reports/scores_test.md/json; n=2437 test roots. |
| s4aa, SparseGPT and both swaps | Completed | Models, sidecars, main A/B results. SparseGPT accuracy loss is a completed finding. |
| Magnitude pruning | In progress | Model/raw and supplemental search results exist; sparse hardware probe pending. |
| Hard low-budget follow-up | In progress | Six dense models' raw runs complete; final supplemental consolidation/interpretation pending. |
| Fixed-time Study C | In progress | fp16/s4 at 200/800ms complete on common 2437 IDs; matched final scoring/figure pending. |
| Basic speed/GPU energy/reduced batch sweep | Completed, preliminary | reports/c3_hw/bench and batch_sweep. Headline repeats/final variability summary remain. |
| Detailed profiles, precision/sparse coverage and roofline | In progress — BLOCKED | Saved nvinfer_plugin_10.dll load failure; reports/c3-part1/state.json. No retry during consolidation. |
| All-model comparable frontier speed | Pending | Benchmark each included single-body model; separate lc0 from standalone sparse trtexec results. |
| Matches and Elo/CI | Pending | Runtime estimate, final pair count and matches not completed. |
| Dataset final integrity closure | Pending | Preserve raw data; address/document small symmetry-related overlap before final claims. |
| Final figures/tables | In progress | Main numerical tables and F9 batch plot exist; see deliverable register for remaining outputs. |
| Report/presentation/demo | Pending | deliverables/ contains destination notes only. |
| Fresh experimental reproduction and C4 audit | Pending | Consolidation checks are not the final scientific reproduction. |

Current source/model/runtime conventions are Person B's accepted trimmed pipeline. F8/F10, training/search-calibration/partial-INT8 branches and CPU energy are outside the adopted scope. Do not reopen them as implied tasks.
