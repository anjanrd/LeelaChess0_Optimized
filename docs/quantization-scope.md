# Step 6: intended INT8 scope

Status: **Step 6 complete and verified. Step 7 has not started.**

## Objective and intuition

Choose exactly which calculations the dense INT8 variants will change. Keep that placement fixed so differences between techniques can be interpreted. This step inventories the graph; actual INT8 execution is a Step 7 gate.

## Frozen placement v1.0

Select **127 of 195 MatMul operations**, representing **97.0036% of estimated matrix MACs**. There are no Gemm nodes. Shapes were resolved for every batch from 1 through 8. FP32 and FP16 exports have identical node connectivity, attributes and initializer dimensions.

Select an operation only when its second input is a fixed rank-2 learned weight, M/N exceed 1, and K/N are at least 16 throughout the batch profile. The geometry rule follows the pinned ModelOpt heuristic. It is a performance choice, not a universal hardware-support restriction. Exclude the union across batches, rather than letting the calibration batch change coverage.

| Region | Matrix operations | INT8 targets | Target MACs per position |
| --- | ---: | ---: | ---: |
| attn_body | 4 | 3 | 112,459,776 |
| 15 encoder blocks | 180 | 120 | 4,175,953,920 |
| policy | 5 | 3 | 113,246,208 |
| value | 3 | 1 | 1,572,864 |
| mlh | 3 | 0 | 0 |

The 68 excluded matrix operations comprise 31 activation-by-activation attention/policy products and 37 weighted operations that fail the profile-wide vector/small-dimension rule. The larger fixed-weight scope includes Q/K/V and output projections, FFNs, smolgen compression/shared weight generation, and eligible embedding/policy/value projections.

The graph has 4,539,245,056 matrix multiply-accumulates per position, of which 4,403,232,768 are targeted. These are unfused arithmetic counts, excluding elementwise/layout work. They do not establish runtime coverage or a speedup.

Normalization, softmax, Mish, biases, residual additions and indexing/layout operations receive no explicit INT8 placement. Retain their floating graph semantics. TensorRT may fuse work; report actual execution and floating precision exceptions later.

## Controlled variants and shared tensors

I1 uses symmetric signed INT8 weights with one scale per weight tensor, per-tensor activation scales and max calibration. I2 changes only weight granularity to per-output-channel scaling, RHS axis 1. Subsequent dense variants retain these named targets unless a versioned coverage amendment is made before comparisons.

There are 113 unique selected weight tensors with 63,950,848 parameters, out of 150 unique matrix-weight tensors with 102,036,992 parameters (62.67% of matrix-weight elements). Several excluded vector operations have large weight matrices. The 97% arithmetic coverage therefore does not imply that 97% of weights, storage, memory traffic or runtime become INT8. Engine storage is a separate measurement.

In particular, `/const/smolgen_w` is shared by all 15 encoder blocks. The inventory records every selected activation/weight consumer. SmoothQuant or any algebraic transformation must compensate all affected consumers, or explicitly clone a branch/weight; an uncompensated shared residual/attention consumer would change the floating model before quantization.

## Tool constraints to handle in Step 7

1. ModelOpt 0.47.0's INT8 entry point hardcodes per-channel weights. Use its lower-level static quantizer or a recorded process-local adapter to request per-tensor I1 weights, then audit scale shapes. Leave installed packages unchanged. [Pinned INT8 source](https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/quantization/int8.py#L274).

2. ONNX opset 17 QuantizeLinear does not accept FP16 input/scales; opset 19 does. ModelOpt's FP16 converter enforces at least 19. Validate an unquantized bridge from the same FP16 weights before inserting Q/DQ, preserving node mapping and output semantics. Keep the accepted Step 5 engine and evidence intact. Changes in execution/numerics are a gate, not permission to accept a different baseline silently. [ONNX schema](https://onnx.ai/onnx/operators/onnx__QuantizeLinear.html#quantizelinear-19), [pinned converter](https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/autocast/convert.py#L253).

3. Check the exact named targets after preprocessing and Q/DQ insertion. Confirm scalar I1 weight scales, signed zero points, per-tensor activations and unchanged floating exclusions. Explicit selection bypasses some defaults, but the tool can still apply exclusions. [Pinned geometry/selection source](https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/quantization/graph_utils.py#L1094).

4. A Q/DQ graph is not hardware proof. Build/reload and inspect/profile the INT8 engine in Step 7. Record actual INT8 Tensor Core matrix execution, compiler fusion, conversion boundaries and any fallback. A backend-required placement change needs an explicit scope version before comparisons.

## Verification and reproduction

The installed ModelOpt geometry exclusion helper was executed without calibration/inference at batches 1, 4 and 8 and matched the independent inventory exactly: 37 exclusions at batch 1, four at batches 4/8. Broadcast/M/K/N arithmetic, full matrix coverage, exact-name patterns, tied weights, source hashes and the unchanged Step 5 frozen artifacts were checked. No chess positions or INT8 results informed selection.

Machine-readable artifacts: `environment/step6-inventory.json`, `environment/step6-scope.json`, and `environment/step6-verification.json`. The verification record hashes this report, the script, the scope and the inventory. No graph conversion, quantization, calibration or engine build was performed.

In the activated pinned WSL environment, run:

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 python scripts/inventory_step6.py verify
```

The initial `inventory` command refuses to overwrite an existing frozen scope. Version changes deliberately instead of silently regenerating placement.
