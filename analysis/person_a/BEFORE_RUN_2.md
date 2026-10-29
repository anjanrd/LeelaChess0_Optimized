# Reminder before autonomous Run 2

**Address A5 before starting Run 2.** The user explicitly deferred it while authorizing A6–A10 of Run 1.

A5's saved activation arrays failed their consistency check against the current s4 smoothing multipliers. The cause has not been investigated or resolved. See `run1/blocker-A5.json` for the exact check and frozen input identities. Do not rerun A5, relax the tolerance, change the model or collect new activations without the appropriate authorization.

When Run 2 is requested, first remind Anjan of this deferred issue. Resolve/review the diagnostic provenance and F12, or obtain an explicit decision on how to handle it before launching Run 2. Do not mistake a completed independent Run 1 block for A5 completion.

Also check Ritwik's R1–R5 evidence, final systems/report inputs and GPU availability as listed in the execution plan. R3 already has raw timed results; it needs final alignment, not an automatic rerun.
