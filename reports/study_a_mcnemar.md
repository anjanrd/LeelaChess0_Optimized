# Study A paired McNemar against fp16

Snapshot: 2026-10-28T10:57:04+05:30. Existing raw results only; no lc0/scorer execution and no results modified.

Correct means the recorded raw `best` move belongs to the tablebase record's `correct` moves, matching eval/score.py. Each comparison uses the identical selected position IDs. Historical dev rows are excluded. Exact two-sided binomial McNemar p-values use the unchanged scorer's `mcnemar_p`; p-values are unadjusted for multiple comparisons.

Worse = fp16 correct / model wrong; better = fp16 wrong / model correct. The hard subset is the existing 43 IDs, selected using fp16, so its results are conditional on that selection.

## Full selected test set (n=2437)

| Model | Correct | Accuracy | fp16 correct | Worse | Better | Exact p |
|---|---:|---:|---:|---:|---:|---:|
| fp16 | 2431/2437 | 0.997538 | 2431 | 0 | 0 | 1 |
| s1 | 2424/2437 | 0.994666 | 2431 | 7 | 0 | 0.015625 |
| s2 | 2427/2437 | 0.995897 | 2431 | 6 | 2 | 0.2890625 |
| s3 | 2431/2437 | 0.997538 | 2431 | 1 | 1 | 1 |
| s4 | 2431/2437 | 0.997538 | 2431 | 1 | 1 | 1 |
| s4aa | 2431/2437 | 0.997538 | 2431 | 1 | 1 | 1 |
| swap_pol8 | 2431/2437 | 0.997538 | 2431 | 1 | 1 | 1 |
| swap_val8 | 2431/2437 | 0.997538 | 2431 | 0 | 0 | 1 |

## Existing hard IDs (n=43)

| Model | Correct | Accuracy | fp16 correct | Worse | Better | Exact p |
|---|---:|---:|---:|---:|---:|---:|
| fp16 | 37/43 | 0.860465 | 37 | 0 | 0 | 1 |
| s1 | 32/43 | 0.744186 | 37 | 5 | 0 | 0.0625 |
| s2 | 34/43 | 0.790698 | 37 | 5 | 2 | 0.453125 |
| s3 | 37/43 | 0.860465 | 37 | 1 | 1 | 1 |
| s4 | 37/43 | 0.860465 | 37 | 1 | 1 | 1 |
| s4aa | 37/43 | 0.860465 | 37 | 1 | 1 | 1 |
| swap_pol8 | 37/43 | 0.860465 | 37 | 1 | 1 | 1 |
| swap_val8 | 37/43 | 0.860465 | 37 | 0 | 0 | 1 |

Incomplete raw models omitted: s1sp=1215/2437, s0=0/2437, native=0/2437.

