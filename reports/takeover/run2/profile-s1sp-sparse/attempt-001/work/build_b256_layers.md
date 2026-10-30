# TensorRT layer precision

GEMM/conv-like layers: 169 of 367 engine layers
count by precision: fp16=4, fp32=1, int8=39, int8+sparse=125
time: all 55.994 ms, gemm-like 22.445 ms; fp16 1.1%, fp32 0.2%, int8 98.7%, sparse 74.9%

4 Myelin ForeignNode layer(s): fused regions whose per-op precision is not visible here; use `kernels` on an nsys capture.

| ms | precision | sparse | type | layer |
|---|---|---|---|---|
| 0.6871 | fp16 |  | kgen | `_gemm_mha_v2_myl1_69` |
| 0.6871 | fp16 |  | kgen | `_gemm_mha_v2_myl1_113` |
| 0.6871 | fp16 |  | kgen | `_gemm_mha_v2_myl1_289` |
| 0.6870 | fp16 |  | kgen | `_gemm_mha_v2_myl1_157` |
| 0.6861 | fp16 |  | kgen | `_gemm_mha_v2_myl1_267` |
| 0.6861 | fp16 |  | kgen | `_gemm_mha_v2_myl1_333` |
| 0.6860 | fp16 |  | kgen | `_gemm_mha_v2_myl1_201` |
| 0.6851 | fp16 |  | kgen | `_gemm_mha_v2_myl1_179` |
| 0.6851 | fp16 |  | kgen | `_gemm_mha_v2_myl1_91` |
| 0.6851 | fp16 |  | kgen | `_gemm_mha_v2_myl1_245` |
| 0.6851 | fp16 |  | kgen | `_gemm_mha_v2_myl1_311` |
| 0.6850 | fp16 |  | kgen | `_gemm_mha_v2_myl1_25` |
| 0.6841 | fp16 |  | kgen | `_gemm_mha_v2_myl1_135` |
| 0.6840 | fp16 |  | kgen | `_gemm_mha_v2_myl1_47` |
| 0.6821 | fp16 |  | kgen | `_gemm_mha_v2_myl1_223` |
| 0.3031 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_208` |
| 0.3020 | int8 |  | kgen | `__myl_ReshCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_10` |
| 0.3000 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_54` |
| 0.2991 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_318` |
| 0.2990 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_274` |
| 0.2990 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_120` |
| 0.2989 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_164` |
| 0.2980 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_296` |
| 0.2980 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_98` |
| 0.2980 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_76` |
| 0.2979 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_252` |
| 0.2969 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_186` |
| 0.2960 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_32` |
| 0.2960 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_230` |
| 0.2960 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_142` |
| 0.2898 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_50` |
| 0.2888 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_28` |
| 0.2795 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_116` |
| 0.2785 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_270` |
| 0.2765 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_94` |
| 0.2755 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_72` |
| 0.2755 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_138` |
| 0.2755 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_248` |
| 0.2755 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_336` |
| 0.2755 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_182` |
| 0.2755 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_204` |
| 0.2754 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_314` |
| 0.2754 | int8 |  | kgen | `__myl_CastMul_myl1_106` |
| 0.2745 | int8 |  | kgen | `__myl_CastMul_myl1_238` |
| 0.2744 | int8 |  | kgen | `__myl_CastMul_myl1_84` |
| 0.2744 | int8 |  | kgen | `__myl_CastMul_myl1_304` |
| 0.2744 | int8 |  | kgen | `__myl_CastMul_myl1_172` |
| 0.2744 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_226` |
| 0.2744 | int8 |  | kgen | `__myl_CastMul_myl1_128` |
| 0.2744 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_292` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_62` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_260` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_150` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_326` |
| 0.2734 | int8 |  | kgen | `__myl_CastMul_myl1_18` |
| 0.2725 | int8 |  | kgen | `__myl_CastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_myl1_160` |
| 0.2725 | int8 |  | kgen | `__myl_CastMul_myl1_194` |
| 0.2724 | int8 |  | kgen | `__myl_CastMul_myl1_282` |
| 0.2714 | int8 |  | kgen | `__myl_CastMul_myl1_40` |
| 0.2714 | int8 |  | kgen | `__myl_CastMul_myl1_216` |
