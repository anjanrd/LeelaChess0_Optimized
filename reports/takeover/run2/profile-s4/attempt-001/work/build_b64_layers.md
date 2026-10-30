# TensorRT layer precision

GEMM/conv-like layers: 169 of 367 engine layers
count by precision: fp16=4, fp32=1, int8=164
time: all 14.890 ms, gemm-like 8.213 ms; fp16 1.5%, fp32 0.3%, int8 98.3%

4 Myelin ForeignNode layer(s): fused regions whose per-op precision is not visible here; use `kernels` on an nsys capture.

| ms | precision | sparse | type | layer |
|---|---|---|---|---|
| 0.1270 | fp16 |  | kgen | `_gemm_mha_v2_myl1_47` |
| 0.1249 | fp16 |  | kgen | `_gemm_mha_v2_myl1_245` |
| 0.1239 | fp16 |  | kgen | `_gemm_mha_v2_myl1_157` |
| 0.1239 | fp16 |  | kgen | `_gemm_mha_v2_myl1_289` |
| 0.1229 | fp16 |  | kgen | `_gemm_mha_v2_myl1_311` |
| 0.1229 | fp16 |  | kgen | `_gemm_mha_v2_myl1_267` |
| 0.1229 | fp16 |  | kgen | `_gemm_mha_v2_myl1_201` |
| 0.1229 | fp16 |  | kgen | `_gemm_mha_v2_myl1_333` |
| 0.1219 | fp16 |  | kgen | `_gemm_mha_v2_myl1_223` |
| 0.1219 | fp16 |  | kgen | `_gemm_mha_v2_myl1_69` |
| 0.1219 | fp16 |  | kgen | `_gemm_mha_v2_myl1_91` |
| 0.1219 | fp16 |  | kgen | `_gemm_mha_v2_myl1_113` |
| 0.1208 | fp16 |  | kgen | `_gemm_mha_v2_myl1_179` |
| 0.1208 | fp16 |  | kgen | `_gemm_mha_v2_myl1_135` |
| 0.1126 | fp16 |  | kgen | `_gemm_mha_v2_myl1_25` |
| 0.0889 | int8 |  | gemm | `/encoder5/smolgen/smol_weight_gen_U873_myl1_127` |
| 0.0870 | int8 |  | kgen | `__myl_CastMulAddExpAddLogLteSeleTanhMulCastMeanSubMulMeanAddSqrtDivMulCastMulAddReshMulAddMulMinEtc_myl1_6` |
| 0.0840 | int8 |  | gemm | `/encoder10/ffn/dense1/w_U1596_myl1_249` |
| 0.0840 | int8 |  | gemm | `/encoder14/ffn/dense1/w_U2096_myl1_337` |
| 0.0829 | int8 |  | gemm | `/encoder12/ffn/dense1/w_U1846_myl1_293` |
| 0.0829 | int8 |  | gemm | `/encoder9/ffn/dense1/w_U1471_myl1_227` |
| 0.0819 | int8 |  | gemm | `/encoder5/ffn/dense1/w_U971_myl1_139` |
| 0.0819 | int8 |  | gemm | `/encoder6/ffn/dense1/w_U1096_myl1_161` |
| 0.0819 | int8 |  | gemm | `/encoder11/ffn/dense1/w_U1721_myl1_271` |
| 0.0819 | int8 |  | gemm | `/encoder13/ffn/dense1/w_U1971_myl1_315` |
| 0.0819 | int8 |  | gemm | `/encoder0/ffn/dense1/w_U346_myl1_29` |
| 0.0819 | int8 |  | gemm | `/encoder4/ffn/dense1/w_U846_myl1_117` |
| 0.0819 | int8 |  | gemm | `/encoder8/ffn/dense1/w_U1346_myl1_205` |
| 0.0809 | int8 |  | gemm | `/attn_body/ffn/dense1/w_U217_myl1_7` |
| 0.0809 | int8 |  | gemm | `/encoder1/ffn/dense1/w_U471_myl1_51` |
| 0.0809 | int8 |  | gemm | `/encoder3/ffn/dense1/w_U721_myl1_95` |
| 0.0809 | int8 |  | gemm | `/encoder7/ffn/dense1/w_U1221_myl1_183` |
| 0.0809 | int8 |  | gemm | `/encoder2/ffn/dense1/w_U596_myl1_73` |
| 0.0797 | int8 |  | gemm | `/encoder4/smolgen/smol_weight_gen_U748_myl1_105` |
| 0.0778 | int8 |  | gemm | `/encoder14/smolgen/smol_weight_gen_U1998_myl1_325` |
| 0.0777 | int8 |  | gemm | `/encoder9/mha/V/w_U1384_myl1_217` |
| 0.0768 | int8 |  | gemm | `/encoder13/smolgen/smol_weight_gen_U1873_myl1_303` |
| 0.0758 | int8 |  | gemm | `/policy/dense1/matmul_U2141_myl1_353` |
| 0.0725 | int8 |  | kgen | `__myl_CastMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_322` |
| 0.0724 | int8 |  | gemm | `/encoder5/smolgen/dense1/w_U861_myl1_123` |
| 0.0715 | int8 |  | kgen | `__myl_CastMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_234` |
| 0.0704 | int8 |  | kgen | `__myl_CastMul_myl1_172` |
| 0.0696 | int8 |  | gemm | `/attn_body/ffn/dense2/w_U222_myl1_9` |
| 0.0686 | int8 |  | gemm | `/encoder5/ffn/dense2/w_U976_myl1_141` |
| 0.0676 | int8 |  | gemm | `/encoder1/ffn/dense2/w_U476_myl1_53` |
| 0.0676 | int8 |  | gemm | `/encoder11/ffn/dense2/w_U1726_myl1_273` |
| 0.0676 | int8 |  | gemm | `/encoder3/ffn/dense2/w_U726_myl1_97` |
| 0.0676 | int8 |  | gemm | `/encoder7/ffn/dense2/w_U1226_myl1_185` |
| 0.0676 | int8 |  | gemm | `/encoder9/ffn/dense2/w_U1476_myl1_229` |
| 0.0676 | int8 |  | gemm | `/encoder13/ffn/dense2/w_U1976_myl1_317` |
| 0.0666 | int8 |  | gemm | `/encoder4/ffn/dense2/w_U851_myl1_119` |
| 0.0666 | int8 |  | gemm | `/encoder14/ffn/dense2/w_U2101_myl1_339` |
| 0.0666 | int8 |  | gemm | `/encoder0/ffn/dense2/w_U351_myl1_31` |
| 0.0666 | int8 |  | gemm | `/encoder2/ffn/dense2/w_U601_myl1_75` |
| 0.0666 | int8 |  | gemm | `/encoder8/ffn/dense2/w_U1351_myl1_207` |
| 0.0666 | int8 |  | gemm | `/encoder10/ffn/dense2/w_U1601_myl1_251` |
| 0.0666 | int8 |  | gemm | `/encoder12/ffn/dense2/w_U1851_myl1_295` |
| 0.0655 | int8 |  | gemm | `/encoder6/ffn/dense2/w_U1101_myl1_163` |
| 0.0633 | int8 |  | kgen | `__myl_CastMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_300` |
| 0.0615 | int8 |  | kgen | `__myl_CastMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_256` |
