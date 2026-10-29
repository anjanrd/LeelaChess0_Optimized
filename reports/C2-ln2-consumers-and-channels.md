# C2 final LN inspection

Graphs inspected read-only. Calibration input: data/calib.npz. Channel axis is last; |x|max spans all calibration positions and tokens. Median uses channels with nonzero maximum.

| Consumer in s4 | Op | Quantized? |
|---|---|---|
| `/encoder14/ln2/smooth` (only direct consumer) | Mul | Float smoothing; no integer Q/DQ inputs |
| `/encoder14/ln2/smoothed_QuantizeLinear` | QuantizeLinear | Converts smoothed activation to INT8 |
| `/encoder14/ln2/smoothed_DequantizeLinear` | DequantizeLinear | Decodes shared INT8 activation |
| `/policy/dense1/matmul` | MatMul | Yes: INT8 activation Q/DQ and INT8 weight DQ |
| `/value/embed/matmul` | MatMul | Yes: INT8 activation Q/DQ and INT8 weight DQ |
| `/mlh/embed/matmul` | MatMul | Yes: INT8 activation Q/DQ and INT8 weight DQ |

## s4: `/encoder14/ln2`

Live channels: 768 / 768. Median live |x|max: 8.13330552774e-05.

| Channel (zero-based) | Maximum absolute activation | Ratio to median live |
|---|---|---|
| 420 | 56.0252571106 | 688837.483352 |
| 644 | 32.8431091309 | 403810.099336 |
| 401 | 29.0968647003 | 357749.559525 |
| 383 | 25.4995193481 | 313519.752347 |
| 238 | 25.0413208008 | 307886.144390 |

## s4: `/encoder14/ln2/smoothed`

Live channels: 768 / 768. Median live |x|max: 3.2066131098e-05.

| Channel (zero-based) | Maximum absolute activation | Ratio to median live |
|---|---|---|
| 420 | 4.06870698929 | 126884.873540 |
| 401 | 3.48657655716 | 108730.814656 |
| 468 | 2.92885684967 | 91338.017696 |
| 565 | 2.83453202248 | 88396.445889 |
| 682 | 2.20494794846 | 68762.518987 |

## original: `/encoder14/ln2`

Live channels: 768 / 768. Median live |x|max: 7.93288418208e-05.

| Channel (zero-based) | Maximum absolute activation | Ratio to median live |
|---|---|---|
| 420 | 52.7552566528 | 665019.877285 |
| 644 | 31.9671916962 | 402970.608954 |
| 401 | 29.1855373383 | 367905.753675 |
| 240 | 25.877363205 | 326203.718736 |
| 572 | 24.6206893921 | 310362.395656 |

