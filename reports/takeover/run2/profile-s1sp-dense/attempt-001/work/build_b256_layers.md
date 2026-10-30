# TensorRT layer precision

GEMM/conv-like layers: 169 of 367 engine layers
count by precision: fp16=4, fp32=1, int8=164
time: all 60.231 ms, gemm-like 26.234 ms; fp16 1.0%, fp32 0.2%, int8 98.8%

4 Myelin ForeignNode layer(s): fused regions whose per-op precision is not visible here; use `kernels` on an nsys capture.

| ms | precision | sparse | type | layer |
|---|---|---|---|---|
| 0.8282 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_182` |
| 0.6861 | fp16 |  | kgen | `_gemm_mha_v2_myl1_179` |
| 0.6861 | fp16 |  | kgen | `_gemm_mha_v2_myl1_311` |
| 0.6861 | fp16 |  | kgen | `_gemm_mha_v2_myl1_47` |
| 0.6860 | fp16 |  | kgen | `_gemm_mha_v2_myl1_333` |
| 0.6851 | fp16 |  | kgen | `_gemm_mha_v2_myl1_223` |
| 0.6850 | fp16 |  | kgen | `_gemm_mha_v2_myl1_113` |
| 0.6850 | fp16 |  | kgen | `_gemm_mha_v2_myl1_267` |
| 0.6841 | fp16 |  | kgen | `_gemm_mha_v2_myl1_91` |
| 0.6841 | fp16 |  | kgen | `_gemm_mha_v2_myl1_69` |
| 0.6841 | fp16 |  | kgen | `_gemm_mha_v2_myl1_135` |
| 0.6841 | fp16 |  | kgen | `_gemm_mha_v2_myl1_157` |
| 0.6841 | fp16 |  | kgen | `_gemm_mha_v2_myl1_289` |
| 0.6830 | fp16 |  | kgen | `_gemm_mha_v2_myl1_245` |
| 0.6830 | fp16 |  | kgen | `_gemm_mha_v2_myl1_201` |
| 0.6830 | fp16 |  | kgen | `_gemm_mha_v2_myl1_25` |
| 0.2949 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_98` |
| 0.2948 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_32` |
| 0.2939 | int8 |  | kgen | `__myl_ReshCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_10` |
| 0.2928 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_208` |
| 0.2919 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_120` |
| 0.2919 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_54` |
| 0.2918 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_142` |
| 0.2918 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_296` |
| 0.2918 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_274` |
| 0.2909 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_76` |
| 0.2908 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_318` |
| 0.2908 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_186` |
| 0.2908 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_164` |
| 0.2899 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_252` |
| 0.2898 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_230` |
| 0.2867 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_28` |
| 0.2785 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_50` |
| 0.2765 | int8 |  | kgen | `__myl_CastMul_myl1_18` |
| 0.2754 | int8 |  | kgen | `__myl_CastMul_myl1_40` |
| 0.2754 | int8 |  | kgen | `__myl_CastMul_myl1_150` |
| 0.2744 | int8 |  | kgen | `__myl_CastMul_myl1_172` |
| 0.2744 | int8 |  | kgen | `__myl_CastMul_myl1_216` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_128` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_194` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_326` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_260` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_304` |
| 0.2724 | int8 |  | kgen | `__myl_CastMul_myl1_84` |
| 0.2724 | int8 |  | kgen | `__myl_CastMul_myl1_238` |
| 0.2724 | int8 |  | kgen | `__myl_CastMul_myl1_106` |
| 0.2724 | int8 |  | kgen | `__myl_CastMul_myl1_282` |
| 0.2714 | int8 |  | kgen | `__myl_CastMul_myl1_62` |
| 0.2693 | int8 |  | gemm | `/encoder7/ffn/dense1/w_U1221_myl1_183` |
| 0.2663 | int8 |  | gemm | `/encoder0/ffn/dense1/w_U346_myl1_29` |
| 0.2662 | int8 |  | gemm | `/encoder8/ffn/dense1/w_U1346_myl1_205` |
| 0.2662 | int8 |  | gemm | `/encoder13/ffn/dense1/w_U1971_myl1_315` |
| 0.2662 | int8 |  | gemm | `/encoder6/ffn/dense1/w_U1096_myl1_161` |
| 0.2652 | int8 |  | gemm | `/encoder3/ffn/dense1/w_U721_myl1_95` |
| 0.2652 | int8 |  | gemm | `/encoder14/ffn/dense1/w_U2096_myl1_337` |
| 0.2652 | int8 |  | gemm | `/encoder2/ffn/dense1/w_U596_myl1_73` |
| 0.2652 | int8 |  | gemm | `/encoder4/ffn/dense1/w_U846_myl1_117` |
| 0.2652 | int8 |  | gemm | `/encoder11/ffn/dense1/w_U1721_myl1_271` |
| 0.2652 | int8 |  | gemm | `/encoder12/ffn/dense1/w_U1846_myl1_293` |
| 0.2643 | int8 |  | gemm | `/encoder5/ffn/dense1/w_U971_myl1_139` |
