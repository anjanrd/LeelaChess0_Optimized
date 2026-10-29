# Person A slide contribution

Prepared content for the shared deck; not a rendered final presentation.

1. **Question and outputs:** one BT3 checkpoint; policy, WDL and moves-left; separate network drift, move accuracy and game strength. Use the report's model/input diagram description.
2. **Compression ladder:** per-tensor -> per-channel -> percentile -> SmoothQuant; attention and sparse branches separate. Use F1 and the recipe table.
3. **Search:** use F2/F3 and the hard supplement. Explain actual-node overshoot, near-ceiling results and why node-equivalents can be ambiguous.
4. **Policy/value swap:** use F4. Explain both routes, moves-left co-swap and why ties do not establish equal importance.
5. **Sparse quality:** verified masks, lower calibration reconstruction loss and persistent chess errors. Hardware conclusions WAIT R1/R2.
6. **Activation mechanism:** explain compensating rescaling algebraically. A5/F12 is DEFERRED; no unverified channel plot is included. Address it before Run 2.
7. **Model work meets hardware:** static 195-operation inventory ready. Final profile/roofline WAIT R1; quality-versus-throughput WAIT R2. Keep actual lc0 separate from standalone sparse probes.
8. **Does speed pay off?:** existing timed review is near ceiling; final speed/match findings WAIT R2/R3/R4. Include negative/inconclusive outcomes and uncertainty.
9. **Limits and reproduction:** synthetic endgames, one network/device, split caveat, printed priors, scope omissions; final systems reproduction WAIT R5.

Final deck: combine with B's systems slides, verify numbers against source CSVs, remove placeholders only when evidence arrives, render/review and rehearse. Shared abstract/introduction/related work/discussion/limitations/conclusion must agree with the report.
