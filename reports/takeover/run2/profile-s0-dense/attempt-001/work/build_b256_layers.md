# TensorRT layer precision

GEMM/conv-like layers: 169 of 367 engine layers
count by precision: fp16=4, fp32=1, int8=164
time: all 59.911 ms, gemm-like 26.498 ms; fp16 1.1%, fp32 0.2%, int8 98.7%

4 Myelin ForeignNode layer(s): fused regions whose per-op precision is not visible here; use `kernels` on an nsys capture.

| ms | precision | sparse | type | layer |
|---|---|---|---|---|
| 0.6881 | fp16 |  | kgen | `_gemm_mha_v2_myl1_47` |
| 0.6871 | fp16 |  | kgen | `_gemm_mha_v2_myl1_223` |
| 0.6861 | fp16 |  | kgen | `_gemm_mha_v2_myl1_311` |
| 0.6851 | fp16 |  | kgen | `_gemm_mha_v2_myl1_267` |
| 0.6851 | fp16 |  | kgen | `_gemm_mha_v2_myl1_245` |
| 0.6851 | fp16 |  | kgen | `_gemm_mha_v2_myl1_135` |
| 0.6841 | fp16 |  | kgen | `_gemm_mha_v2_myl1_179` |
| 0.6841 | fp16 |  | kgen | `_gemm_mha_v2_myl1_113` |
| 0.6840 | fp16 |  | kgen | `_gemm_mha_v2_myl1_157` |
| 0.6840 | fp16 |  | kgen | `_gemm_mha_v2_myl1_201` |
| 0.6840 | fp16 |  | kgen | `_gemm_mha_v2_myl1_289` |
| 0.6830 | fp16 |  | kgen | `_gemm_mha_v2_myl1_69` |
| 0.6830 | fp16 |  | kgen | `_gemm_mha_v2_myl1_25` |
| 0.6820 | fp16 |  | kgen | `_gemm_mha_v2_myl1_91` |
| 0.6820 | fp16 |  | kgen | `_gemm_mha_v2_myl1_333` |
| 0.2959 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_230` |
| 0.2959 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_252` |
| 0.2949 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_32` |
| 0.2939 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_296` |
| 0.2938 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_164` |
| 0.2928 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_274` |
| 0.2928 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_98` |
| 0.2928 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_120` |
| 0.2919 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_208` |
| 0.2919 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_76` |
| 0.2919 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_142` |
| 0.2918 | int8 |  | kgen | `__myl_ReshCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_10` |
| 0.2909 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_54` |
| 0.2908 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_318` |
| 0.2908 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_186` |
| 0.2868 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_28` |
| 0.2857 | int8 |  | gemm | `/encoder3/ffn/dense1/w_U721_myl1_95` |
| 0.2847 | int8 |  | gemm | `/encoder8/ffn/dense1/w_U1346_myl1_205` |
| 0.2847 | int8 |  | gemm | `/encoder1/ffn/dense1/w_U471_myl1_51` |
| 0.2847 | int8 |  | gemm | `/encoder7/ffn/dense1/w_U1221_myl1_183` |
| 0.2847 | int8 |  | gemm | `/encoder2/ffn/dense1/w_U596_myl1_73` |
| 0.2847 | int8 |  | gemm | `/encoder5/ffn/dense1/w_U971_myl1_139` |
| 0.2847 | int8 |  | gemm | `/encoder13/ffn/dense1/w_U1971_myl1_315` |
| 0.2847 | int8 |  | gemm | `/encoder14/ffn/dense1/w_U2096_myl1_337` |
| 0.2837 | int8 |  | gemm | `/encoder11/ffn/dense1/w_U1721_myl1_271` |
| 0.2837 | int8 |  | gemm | `/encoder12/ffn/dense1/w_U1846_myl1_293` |
| 0.2837 | int8 |  | gemm | `/encoder6/ffn/dense1/w_U1096_myl1_161` |
| 0.2836 | int8 |  | gemm | `/encoder4/ffn/dense1/w_U846_myl1_117` |
| 0.2827 | int8 |  | gemm | `/encoder9/ffn/dense1/w_U1471_myl1_227` |
| 0.2826 | int8 |  | gemm | `/encoder0/ffn/dense1/w_U346_myl1_29` |
| 0.2816 | int8 |  | gemm | `/encoder10/ffn/dense1/w_U1596_myl1_249` |
| 0.2806 | int8 |  | gemm | `/attn_body/ffn/dense1/w_U217_myl1_7` |
| 0.2796 | fp16 |  | gemm | `/policy/matmul_U2220_myl1_361` |
| 0.2785 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_50` |
| 0.2774 | int8 |  | kgen | `__myl_CastMul_myl1_106` |
| 0.2755 | int8 |  | kgen | `__myl_CastMul_myl1_18` |
| 0.2754 | int8 |  | kgen | `__myl_CastMul_myl1_194` |
| 0.2745 | int8 |  | kgen | `__myl_CastMul_myl1_40` |
| 0.2744 | int8 |  | kgen | `__myl_CastMul_myl1_238` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_128` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_84` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_150` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_260` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_326` |
| 0.2725 | int8 |  | kgen | `__myl_CastMul_myl1_304` |
