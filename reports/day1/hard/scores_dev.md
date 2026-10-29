# Hard subset (dev): 3 positions where native's raw top move is wrong or <80% raw policy mass is on correct moves

## Study A: raw network (budget 0)

| model | n | tb accuracy [95% CI] | DTZ-optimal | KL vs ref | top-1 agree | mean abs dV |
|---|---|---|---|---|---|---|
| native | 3 | 0.6667 [0.208,0.939] | 0.6667 | 0.00e+00 | 1.0000 | 0.0000 |
| fp16 | 3 | 0.6667 [0.208,0.939] | 0.6667 | 0.00e+00 | 1.0000 | 0.0001 |
| s2 | 3 | 0.3333 [0.061,0.792] | 0.3333 | 6.55e-02 | 0.6667 | 0.0158 |
