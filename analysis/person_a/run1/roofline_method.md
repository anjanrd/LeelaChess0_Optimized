# Model-side roofline preparation

The archived geometry is reused only after checking all active operator protobufs, integer shape constants, matrix names/inputs/outputs and fixed-weight dimensions against the current graph. Floating coefficients can differ slightly between exports without changing geometry. This does not import A's old quantization scope.

For [...,M,K] @ [...,K,N], MACs = output_elements × K; arithmetic ops = 2 × MACs. Independent-position work scales by the actual inference batch; MCTS MinibatchSize need not be that batch. Only matrix arithmetic is inventoried; softmax, normalization, conversion and scheduling overhead remain.

First-order logical bytes = A_elements×A_bytes + W_or_B_elements×B_bytes + output_elements×output_bytes. Use actual operand/output representations and distinguish INT32 accumulation from stored outputs. Weights do not multiply by batch for unique storage; shared weights are counted once for storage but can be read by multiple operations. Logical traffic is not measured DRAM traffic or cache reuse.

R1 intake: require successful nonempty layer info/timing, matching model hash, batch, build flags and runtime. Use actual recorded small/large batches. Start mapping with hw/roofline.py::map_layers, inspect fused/ForeignNode regions and retain unmatched regions. Sum associated work once and charge a measured fused-region duration once. Never assign the whole fused duration to each member and sum it repeatedly. Reconcile attributed versus engine time.

Achieved ops/s = associated arithmetic work / measured seconds. Intensity = modeled ops / modeled bytes. Compare with min(measured precision-appropriate compute peak, measured bandwidth×intensity). Opaque/mixed regions retain unknowns. Use FLOP/s for floating arithmetic and ops/s for integer arithmetic. The current hw/roofline.py assumes simplified byte formats and has SPEC_4060 fallback constants; these must not silently become observed precision or measured peaks in the final report. B should supply actual inputs; this preparation does not edit his hardware code or resolve the DLL failure.

**WAIT R1:** precision-aware bytes at measured conditions, region timing mapping, peaks, final roofline plot and bottleneck claims. A partial batch handoff can be reviewed without inventing the other batch.
