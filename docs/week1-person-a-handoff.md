# Person A Week 1: verified work and pending acceptance

Updated 2026-10-26, Asia/Kolkata. All remaining A-side technical tasks have been executed. **Final closure is waiting for one user decision about newly discovered FP16 numerical drift.** Person B's systems work and joint C1 remain unverified. No Week 2 variants or training were run.

The active progress record is [project-roadmap.md](project-roadmap.md); machine-readable status is [week1-progress.json](../environment/week1-progress.json). The original Step 5/6 frozen artifacts and exact accepted FP16 engine were preserved.

## Verified deliverables

| Task | Result | Evidence |
| --- | --- | --- |
| A06P: baseline profile | Exact accepted engine profiled without rebuilding; batch 1/4/8 resident and host timings, layer attribution and overhead recorded | [Profile](../environment/week1-baseline-profile.json) |
| A06R/A07: scope and pilot | Registered 127/160 comparison; all intended targets execute INT8; saved-engine reload and wrapped graph identity verified | [Scope v2](../environment/step6-scope-v2.json), [pilot](../environment/week1-int8-pilot.json) |
| A08: data and truth | 40 tablebase files verified against full-file and official embedded checksums; all legal child outcomes and encodings checked | [Table files](../environment/week1-tablebases.json), [dataset manifest](../data/syzygy/manifest.json) |
| A09: baseline measurements | Full network-only outputs, chosen moves, outcome errors, strata and paired uncertainty saved; new drift acceptance remains open | [Accuracy](../results/week1/baseline-accuracy.json), [numerical comparison](../results/week1/baseline-numerical-comparison.json) |
| A10: outliers | 1,024 calibration inputs, 113 unique activation tensors and 160 selected matrix consumers; per-channel maxima/means/RMS and plots | [Analysis](week1-activation-analysis.md), [statistics](../results/week1/calibration-outliers.json) |
| A11: trainable-port feasibility | Exact-operator FP32 parity at batches 1/4; finite gradients in one batch-1 backward pass; zero optimizer steps | [Feasibility](../environment/week1-torch-feasibility.json) |
| A12: technical audit | All 13,072 root groups rechecked; 193 root/transformed move reprobes; 16 independent native CPU checks; artifact identities intact | [Audit](../environment/week1-audit.json), [native checks](../environment/week1-native-check.json) |

## Required acceptance decision

The user previously accepted the exact FP16 TensorRT engine after a 1.9593-percentage-point WDL-component discrepancy on one of 128 numerical-confirmation positions. The full test now shows:

- 111 of 10,000 roots exceed the original 1.5-point component bound against R32.
- 94 exceed the previously observed 1.9593-point discrepancy.
- The maximum F16/R32 WDL-component difference is **23.2399 percentage points**.
- Native Eigen CPU checks on the eight largest cases agree with R32 within the original FP32 gates. Repeated F16 batch-8 outputs are bit-identical; batch-1 outputs reproduce the large discrepancy.
- No engine was rebuilt and no numerical tolerance was changed.

For example, on `test-07819`, native lc0 predicts about 22.10% draw / 77.90% loss, while F16 predicts 45.34% draw / 54.69% loss. All three evaluators choose the same policy move there. This explains why substantial value-head drift can coexist with close move accuracy; MCTS effects still need measurement.

See [the complete diagnostic and options](../environment/week1-baseline-drift-review.json). The pending choice is either to retain the exact F16 baseline with this larger drift explicitly accepted and reported, or to reopen baseline engineering under a new registered investigation. The [frozen experiment contract](experiment-contract.md), Section 8, retains the numerical limits and says the previous exception does not authorize arbitrary future discrepancies. Existing acceptance is not silently extended.

The baseline accuracy measurements remain valid observations of these specific artifacts. Their final acceptance is separate from whether the measurements were computed correctly.

## Measured network-only baseline results

The test set contains 10,000 synthetic standalone roots, balanced across four materials, two sides to move and theoretical W/D outcomes. A move error means W to D/L or D to L in the original mover's perspective. The NN's predicted WDL category is not the error definition.

| Baseline | Preserving moves | Errors | Accuracy |
| --- | ---: | ---: | ---: |
| R32_CUDA | 5,542 | 4,458 | 55.42% |
| F16_TRT | 5,542 | 4,458 | 55.42% |

The two models agree on the selected move on 98.82% of roots. Five roots improve and five worsen under F16, giving an accuracy difference of 0.0000 points; the stratified paired-bootstrap 95% interval is [-0.0600, 0.0600] points. These results do not estimate normal game-position frequency or engine strength.

The predetermined hard rule was applied unchanged: validation's 20th percentile of the signed preserving/degrading FP16 probability margin gives tau=-0.0938719019. The resulting test hard subset has 1,650 roots and **0% accuracy for both baselines**. A negative margin selects positions FP16 already gets wrong, so measuring further degradation has a floor effect. Preserve this result. Any supplemental baseline-correct/near-boundary subset needs an explicitly registered validation-based definition and joint review; do not redefine the current subset after viewing test results.

Detailed strata and confidence intervals are in [the baseline report](week1-baseline-results.md). Final INT8 test inference has not been run.

## Active INT8 scope and pilot limitations

Scope v2 selects **160 of 164 fixed-weight MatMuls**, covering **99.9905% of unique matrix-weight parameters** and **97.8425% of all matrix MACs**. The four remaining weighted operations contain 9,728 matrix parameters:

- `/policy/promotion/matmul`
- `/value/dense2/matmul`
- `/mlh/embed/matmul`
- `/mlh/dense2/matmul`

All 31 dynamic activation-by-activation products remain floating. Biases, normalization parameters and other floating constants are outside the matrix-weight coverage denominator.

Both operands of selected multiplications execute INT8 with INT32 accumulation. TensorRT can fuse dequantization into FP32 intermediates, emit FP16 or requantize directly to INT8. Unselected weighted matrix operations are constrained to FP16; normalization computation is requested in FP32. Exact tactic/type evidence is retained in the engine records and raw runtime inspectors.

The Q/DQ ONNX representation retains FP16 source weight constants followed by quantization. TensorRT folds constants at build time and executes the audited INT8 kernels. The parameter coverage number is therefore **not** a claim about the fraction of ONNX-file bytes stored as INT8. Report graph and engine sizes separately. A compact-INT8 initializer serializer would be a later explicit change requiring equivalence and engine checks.

The broader engine is 109,301,652 bytes, versus 147,620,084 for the 127-operation candidate. Broader/original latency ratios, normalized by paired F16 timings, are 0.9685 at batch 1 and 1.0626 at batch 8, within the predeclared 1.10 allowance. The selected naive pilot itself is still slower than F16 (about 1.076x at batch 1 and 1.169x at batch 8 in this host pipeline) and has substantial numerical drift. It is an engineering starting point, not a successful optimization or final quantized accuracy result.

The pilot uses the 64 old development positions, per-tensor symmetric weight/activation scaling and max calibration. Week 2's I1-I5 ladder still needs full calibration and validation-only selection. All variants must keep this common placement unless a separate coverage ablation is registered.

## Data, artifacts and execution contract

- Splits: 1,024 calibration, 2,048 validation, 10,000 test; seed 20261021; 16 balanced material/side/outcome cells. All split symmetry groups are disjoint and exclude the 221 previous development groups.
- Standalone FEN history fill `no`, classical 112 planes, halfmove clock zero, fullmove one, no castling/en-passant rights. Genuine game trajectories were not generated.
- Legal policy softmax uses FP32 and lexical UCI ties. Outputs are policy logits `[B,1858]`, side-to-move WDL `[B,3]` and moves-left `[B,1]`.
- Ground truth is theoretical WDL sign, ignoring the fifty-move limit; cursed/blessed flags are retained. No naturally sampled cursed/blessed cases occurred. Root DTZ is recorded; DTZ-optimal move ranking remains unverified B04 work.
- Tablebases stay outside the repository at `/home/anjanrd/.local/share/lc0-int8/syzygy/`. Keep them disabled inside measured search.
- Original R32 and F16 ONNX files remain in `models/onnx/`; the source checkpoint remains in `models/source/`.
- Accepted F16 engine: `/home/anjanrd/.local/share/lc0-int8/step5-preserved/bt3-f16-4271981b85fb44dd.plan`, SHA-256 `4271981b85fb44dd1171a8b49cd999626cd9662f184d3f347a8f7bc4b08b8363`.
- Selected INT8 engine: `/home/anjanrd/.local/share/lc0-int8/week1/int8/bt3-i1-scope160.plan`, SHA-256 `3d3c58b87ae6d3cbfe3b861fa0f21fc2ffee92b9fb39f937425fe663973167a0`.
- Wrapped pilot: `models/wrapped/bt3-i1-pilot.pb.gz`; its embedded ONNX bytes are unchanged. The available lc0 tool binary supports CPU/export/wrapping. Actual GPU execution of the wrapper is still B03/C1, not implied by this standalone engine audit.
- All builders, large raw traces and diagnostics are under the external runtime directory. No project `tmp` folder was created.

## Reproduction entry points

Run one GPU workload at a time in WSL Ubuntu-22.04 using the existing pinned venv. Do not upgrade dependencies or rebuild the accepted F16 engine as a routine reproduction step.

```bash
cd /mnt/c/Users/HP/Desktop/LC0
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
PY=/home/anjanrd/.local/share/lc0-int8/venv/bin/python
```

The scripts correspond to these verified stages:

```bash
$PY scripts/profile_week1.py
$PY scripts/quantize_week1.py review
$PY scripts/quantize_week1.py bridge
$PY scripts/quantize_week1.py quantize --scope 127
$PY scripts/quantize_week1.py build --scope 127
$PY scripts/audit_int8_week1.py audit --scope 127
$PY scripts/quantize_week1.py quantize --scope 160
$PY scripts/quantize_week1.py build --scope 160
$PY scripts/audit_int8_week1.py audit --scope 160
$PY scripts/audit_int8_week1.py choose
$PY scripts/quantize_week1.py wrap
$PY scripts/datasets_week1.py acquire
$PY scripts/datasets_week1.py build
$PY scripts/baselines_week1.py
$PY scripts/outliers_week1.py
$PY scripts/torch_feasibility_week1.py
$PY scripts/verify_week1.py
$PY scripts/investigate_week1_drift.py
```

These are provenance/reproduction entry points, not instructions to overwrite the frozen run in place. Builders and NPZ serialization can change byte identities; copy the project/run records to a dedicated new reproduction location and redirect runtime outputs before rebuilding. Preserve current engines and manifests. The acquisition verifier expects the official Syzygy source/checksum tool at the location recorded in `environment/week1-tablebases.json`; its exact source commit and build flags are recorded there. The final verifier regenerates the log-scale plot from cached statistics.

The PyTorch conversion reconstructs its parameters from the frozen FP32 ONNX and script, avoiding a duplicate large checkpoint. It achieved maximum legal-policy probability differences below 0.000003 and finite gradients for all 408 trainable initializer tensors. Peak allocated CUDA memory was 886,057,984 bytes for the single backward check. Scalar multipliers remain fixed. This does not establish optimizer memory, convergence or QAT training feasibility.

## What is still outside A-side closure

The user's drift decision is the only remaining A-side acceptance gate. After it is recorded, close A09/A12 and refresh the final manifest. B01-B08 and joint C1 require actual lc0 GPU integration and precision/parity checks; selected node budgets and fixed-node evaluation; one-second search evaluation; systems profiling/throughput; supported energy instrumentation; DTZ-ranking validation; and teammate review. Do not mark those complete from standalone Python evidence or start Week 2 before the required joint review.
