# TensorRT layer precision

GEMM/conv-like layers: 104 of 288 engine layers
count by precision: fp16=103, fp32=1
time: all 17.868 ms, gemm-like 9.429 ms; fp16 99.8%, fp32 0.2%

4 Myelin ForeignNode layer(s): fused regions whose per-op precision is not visible here; use `kernels` on an nsys capture.

| ms | precision | sparse | type | layer |
|---|---|---|---|---|
| 0.2928 | fp16 |  | gemm | `/encoder0/mha/V/w_U87+/encoder0/mha/K/w_U88+/encoder0/mha/Q/w_U89_myl1_11` |
| 0.2867 | fp16 |  | gemm | `/encoder4/mha/V/w_U627+/encoder4/mha/K/w_U628+/encoder4/mha/Q/w_U629_myl1_79` |
| 0.2857 | fp16 |  | gemm | `/encoder8/mha/V/w_U1163+/encoder8/mha/K/w_U1164+/encoder8/mha/Q/w_U1165_myl1_147` |
| 0.2857 | fp16 |  | gemm | `/encoder5/mha/V/w_U761+/encoder5/mha/K/w_U762+/encoder5/mha/Q/w_U763_myl1_96` |
| 0.2857 | fp16 |  | gemm | `/encoder10/mha/V/w_U1431+/encoder10/mha/K/w_U1432+/encoder10/mha/Q/w_U1433_myl1_181` |
| 0.2847 | fp16 |  | gemm | `/encoder2/mha/V/w_U359+/encoder2/mha/K/w_U360+/encoder2/mha/Q/w_U361_myl1_45` |
| 0.2847 | fp16 |  | gemm | `/encoder3/mha/V/w_U493+/encoder3/mha/K/w_U494+/encoder3/mha/Q/w_U495_myl1_62` |
| 0.2847 | fp16 |  | gemm | `/encoder6/mha/V/w_U895+/encoder6/mha/K/w_U896+/encoder6/mha/Q/w_U897_myl1_113` |
| 0.2847 | fp16 |  | gemm | `/encoder12/mha/V/w_U1699+/encoder12/mha/K/w_U1700+/encoder12/mha/Q/w_U1701_myl1_215` |
| 0.2847 | fp16 |  | gemm | `/encoder13/mha/V/w_U1833+/encoder13/mha/K/w_U1834+/encoder13/mha/Q/w_U1835_myl1_232` |
| 0.2847 | fp16 |  | gemm | `/encoder7/mha/V/w_U1029+/encoder7/mha/K/w_U1030+/encoder7/mha/Q/w_U1031_myl1_130` |
| 0.2847 | fp16 |  | gemm | `/encoder9/mha/V/w_U1297+/encoder9/mha/K/w_U1298+/encoder9/mha/Q/w_U1299_myl1_164` |
| 0.2837 | fp16 |  | gemm | `/encoder1/mha/V/w_U225+/encoder1/mha/K/w_U226+/encoder1/mha/Q/w_U227_myl1_28` |
| 0.2837 | fp16 |  | gemm | `/encoder11/mha/V/w_U1565+/encoder11/mha/K/w_U1566+/encoder11/mha/Q/w_U1567_myl1_198` |
| 0.2826 | fp16 |  | gemm | `/encoder14/mha/V/w_U1967+/encoder14/mha/K/w_U1968+/encoder14/mha/Q/w_U1969_myl1_249` |
| 0.2274 | fp16 |  | gemm | `/policy/K/matmul_U2122+/policy/Q/matmul_U2123_myl1_268` |
| 0.1772 | fp16 |  | fusion | `__myl_FcExpAddLogLteSeleTanhMul_myl1_7` |
| 0.1700 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_25` |
| 0.1659 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_263` |
| 0.1658 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_110` |
| 0.1648 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_93` |
| 0.1648 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_212` |
| 0.1628 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_195` |
| 0.1618 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_144` |
| 0.1608 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_76` |
| 0.1608 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_59` |
| 0.1608 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_229` |
| 0.1598 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_127` |
| 0.1598 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_178` |
| 0.1597 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_42` |
| 0.1597 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_161` |
| 0.1597 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_246` |
| 0.1516 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_22` |
| 0.1454 | fp16 |  | kgen | `__myl_ExpAddLogLteSeleTanhMulCastMeanSubMulMeanAddSqrtDivMulCastMulAddReshMulAddResh_myl1_6` |
| 0.1444 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_8` |
| 0.1423 | fp16 |  | gemm | `/encoder4/ffn/dense1/w_U745_myl1_91` |
| 0.1423 | fp16 |  | gemm | `/encoder8/ffn/dense1/w_U1281_myl1_159` |
| 0.1423 | fp16 |  | gemm | `/encoder5/ffn/dense1/w_U879_myl1_108` |
| 0.1413 | fp16 |  | gemm | `/encoder0/ffn/dense1/w_U209_myl1_23` |
| 0.1413 | fp16 |  | gemm | `/encoder3/ffn/dense1/w_U611_myl1_74` |
| 0.1413 | fp16 |  | gemm | `/encoder7/ffn/dense1/w_U1147_myl1_142` |
| 0.1413 | fp16 |  | gemm | `/encoder11/ffn/dense1/w_U1683_myl1_210` |
| 0.1413 | fp16 |  | gemm | `/encoder12/ffn/dense1/w_U1817_myl1_227` |
| 0.1413 | fp16 |  | gemm | `/encoder2/ffn/dense1/w_U477_myl1_57` |
| 0.1413 | fp16 |  | gemm | `/encoder6/ffn/dense1/w_U1013_myl1_125` |
| 0.1413 | fp16 |  | gemm | `/encoder9/ffn/dense1/w_U1415_myl1_176` |
| 0.1413 | fp16 |  | gemm | `/encoder10/ffn/dense1/w_U1549_myl1_193` |
| 0.1413 | fp16 |  | gemm | `/encoder13/ffn/dense1/w_U1951_myl1_244` |
| 0.1403 | fp16 |  | gemm | `/encoder1/ffn/dense1/w_U343_myl1_40` |
| 0.1403 | fp16 |  | gemm | `/encoder14/ffn/dense1/w_U2085_myl1_261` |
| 0.1373 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_192` |
| 0.1372 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_124` |
| 0.1362 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_56` |
| 0.1362 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_209` |
| 0.1362 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_158` |
| 0.1352 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_90` |
| 0.1352 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_107` |
| 0.1352 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_73` |
| 0.1352 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_141` |
| 0.1352 | fp16 |  | fusion | `__myl_FcMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAdd_myl1_175` |
