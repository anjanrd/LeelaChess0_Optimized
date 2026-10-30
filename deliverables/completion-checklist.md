# Final deliverable checklist - after normal Run 3

**A5/F12 and new Runs1–3 are verified.** R1/R2/R3 are internal evidence checkpoints now; production and fresh GPU reproduction await exclusive Run4. Final report/deck/video/package/C4 await Run5. This is not C4 sign-off.

| ID | deliverable | status | evidence | remaining_check |
|---|---|---|---|---|
| D1 | Shared code/setup | In progress | README.md; maintenance/artifacts.py | R5 fresh setup/reproduction |
| D2 | Models/calibration/recipes/engine identities | In progress | models/; data/; frozen manifests | R5 final engine/runtime freeze |
| D3 | Root lists/splits/scorer | A-side audit complete; shared closure pending | analysis/person_a/run1/cohort_audit.json | R5 final shared package |
| T1 | Network/search ablation | Completed numerical/publication tables | analysis/tables/T1-network.md; T1-search.csv | final report styling only |
| T2 | Speed/coverage/reference | Completed bounded analysis | analysis/tables/T2-*.csv; F6 | precision/fusion and workload limits retained |
| T3 | GPU energy | Analysis produced; idle subtraction provisional | analysis/tables/T3-energy.csv and T3-idle-telemetry-review.csv | Run4 diagnostic/final qualification; total under-load separately reported |
| T4 | Paired-match Elo/CI | WAIT R4 | no completed match evidence | R4 games and reviewed uncertainty |
| T5 | Sparse hardware | Completed bounded analysis | analysis/tables/T5-sparsity.csv | standalone selected tactics; no lc0 sparse claim |
| F1 | Dense ablation | Generated; visual QA recorded separately | analysis/figures/F1-ablation.png | final shared report styling |
| F2 | Accuracy/nodes | Generated; visual QA recorded separately | analysis/figures/F2-nodes.png | caption preserves actual-node context |
| F3 | Node-equivalents | Generated; visual QA recorded separately | analysis/figures/F3-node-equivalents.png | saturation convention disclosed |
| F4 | Output swaps | Generated; visual QA recorded separately | analysis/figures/F4-swaps.png | accuracy only; head importance inconclusive |
| F5 | Accuracy/time | Completed canonical analysis and visual QA | analysis/figures/F5-time.png; T6-timed-canonical.csv | final report integration; near-ceiling limit |
| F6 | Layer profile/roofline | Completed bounded analysis and visual QA | F6-profile-breakdown.*; F6-roofline.*; T2 mapping | logical traffic, opaque fusion and empirical-reference limits |
| F7 | GPU energy/node | Completed provisional figure and visual QA | analysis/figures/F7-energy.* | above-idle historical subtraction remains unvalidated |
| F8 | Accuracy/equal energy | Omitted | updated_plan.md | no substitute claim |
| F9 | Batch throughput | Completed reduced sweep | reports/c3_hw/batch_sweep/sweep.png | B final caption |
| F10 | Accuracy/batch | Omitted | updated_plan.md | no substitute claim |
| F11 | Quality/throughput coordinates | Completed analysis and visual QA | analysis/figures/F11-frontier.*; analysis/tables/F11-frontier.csv | raw NN quality versus separate search workload, not strength |
| F12 | Activation illustration | Completed; visual QA recorded separately | analysis/figures/F12-outliers.png; analysis/person_a/run1/smoothquant_verification.json | retain final-model/CPU provenance; no speed claim |
| D4 | Report | A draft ready; shared final pending | deliverables/report/person_a_sections.md | R1–R5 final integration |
| D5 | Presentation | A outline ready; final pending | deliverables/presentation/person_a_slides.md | final figures/results and rendered deck |
| D6 | Playing demo | Outline ready; recording pending | deliverables/demo/recording_plan.md | R5 runtime + exclusive GPU slot |
| D7 | Package/fresh reproduction | Source/Python/subset preparation verified | reports/takeover/run3/fresh-cpu-smoke.json; fresh-artifact-restore.json | actual GPU reproduction Run4 and full bundle/restore Run5 |
| D8 | Numbers/citations/C4 | A-side checks prepared; final pending | deliverables/completion-checklist.md | every retained row verified; R inputs integrated |
