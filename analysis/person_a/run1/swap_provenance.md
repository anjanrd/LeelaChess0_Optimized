# Policy/value swap review

Model and source ONNX/wrapped SHA256 identities match the frozen provenance. swap_pol8 routes policy from s4, value and moves-left from the FP16-side graph; swap_val8 reverses them. Each stitched model evaluates two bodies. Both use optimize=8 with a floating branch, rather than running two independently frozen engines.

Chosen-move accuracy ties on this cohort do not establish equal importance of policy and value errors. The FP16-policy swap also has small printed-policy differences from the reference; source routing is verified, but numerical execution is not a perfectly isolated head replacement. Moves-left changes with the value branch. Requested-budget comparisons retain actual-node context. Neither swap is eligible for speed/energy/frontier input.
