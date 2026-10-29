# Sparse quality finding

Both sparse source graphs satisfy <=2 nonzeros per four along K for all 150 unique target matrices. SparseGPT uses 98 dependency stages and 512 calibration inputs. Across the 150 reported matrices, median reconstruction error is 0.00690805 versus 0.0895317 for magnitude; SparseGPT is lower on 150 matrices. These are calibration reconstruction losses measured against the corresponding stage targets, not test move-error rates or a guarantee of global forward equivalence.

The sparse model improves substantially over magnitude pruning in raw accuracy, but still has persistent losses after search; the 1,600-node s1sp error cases are retained in sparse-move-errors.csv. Several matrices have few calibration rows relative to K; these warnings and sequential-target differences are limitations, not a demonstrated cause of the remaining chess errors. No retraining, repruning or additional calibration was performed.

**WAIT R1/R2:** whether sparse tactics execute and whether they accelerate either lc0 or standalone trtexec. A valid 2:4 mask and a better reconstruction objective do not establish those hardware claims.
