# Matched timed review: provisional report alignment

| model | nominal_ms | n | correct | accuracy | worse | better | mcnemar_p | nodes_mean | nodes_median | reported_ms_mean | wall_ms_mean | mean_nodes_ratio_vs_fp16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fp16 | 200 | 2437 | 2436 | 0.9995896594173164 | 0 | 0 | 1.0 | 3711.2560525235945 | 500.0 | 183.25194911776774 | 184.35281083299137 | 1.0 |
| s4 | 200 | 2437 | 2437 | 1.0 | 0 | 1 | 1.0 | 3768.6093557652853 | 731.0 | 182.73779236766515 | 183.82691834222405 | 1.015453879341656 |
| fp16 | 800 | 2437 | 2437 | 1.0 | 0 | 0 | 1.0 | 14975.06565449323 | 2863.0 | 605.30734509643 | 606.4201066885515 | 1.0 |
| s4 | 800 | 2437 | 2437 | 1.0 | 0 | 0 | 1.0 | 18084.294214197784 | 3959.0 | 593.6815757078375 | 594.6756668034469 | 1.207627040270881 |

Both models already have the required raw runs. Extra historical FP16 rows are excluded by frozen IDs, not deleted. At 200ms only one paired correctness discordance separates the models; the exact paired test does not support a robust gain. At 800ms both are perfect on this cohort. More mean nodes does not itself establish a stronger player. Early stopping yields elapsed times below nominal budgets and skewed node distributions, so means, medians and time context are retained.

**R3 is final alignment, not a reason to rerun these experiments.** B owns the canonical F5; A supplies this interpretation. Final throughput conclusions wait R2 and full-game conclusions wait R4.
