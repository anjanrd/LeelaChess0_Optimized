# Week 1 network-only baseline accuracy

Test: 10,000 balanced, symmetry-disjoint standalone roots. Error: selected move changes W to D/L or D to L.

**Numerical acceptance remains open:** the final audit found FP16 WDL drift up to 23.24 percentage points, confirmed against native lc0. These are valid measured move accuracies; the earlier drift exception has not been extended automatically. See [the diagnostic](../environment/week1-baseline-drift-review.json) and [handoff](week1-person-a-handoff.md).

| Subset | R32 accuracy | F16 accuracy | n |
| --- | ---: | ---: | ---: |
| all | 55.42% | 55.42% | 10,000 |
| decision_sensitive | 47.16% | 47.16% | 8,436 |
| hard | 0.00% | 0.00% | 1,650 |
| root:W | 47.82% | 47.86% | 5,000 |
| root:D | 63.02% | 62.98% | 5,000 |
| material:KQkq | 51.52% | 51.56% | 2,500 |
| material:KQkr | 36.48% | 36.44% | 2,500 |
| material:KPkp | 75.48% | 75.44% | 2,500 |
| material:KPkr | 58.20% | 58.24% | 2,500 |

F16 minus R32 accuracy: 0.0000 percentage points; paired bootstrap 95% interval [-0.0600, 0.0600] points.
Hard threshold tau: -0.0938719019, fixed from validation FP16 before test inference.

Raw predictions, outputs, strata and uncertainty are in `results/week1/`. These results cover the network-only evaluation. Fixed-node MCTS and one-second MCTS remain Person B / joint C1 work.

Synthetic balanced four-piece standalone roots with zero halfmove clocks and no actual game history; theoretical WDL ignores fifty-move rule. Network-only results are not MCTS results or game strength. No DTZ-optimal-rate claim.
