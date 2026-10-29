# GPU kernels in C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0_cuda_gpu_kern_sum.csv

all kernel time by tag: int8 50.5%, other 47.3%, fp32 1.2%, fp16 1.0%
GEMM-like kernel time by tag: int8 73.5%, other 24.1%, fp32 1.7%, fp16 0.7%

| % time | instances | tags | kernel |
|---|---|---|---|
| 43.73 | 33824 | int8 | `sm80_xmma_gemm_i8i8_i8i32_f32_tn_n_tilesize128x128x64_stage3_warpsize2x2x1_tensor16x8x32_execute_kernel_trt` |
| 6.22 | 1650 |  | `__myl_CastMul_0x9698266d4f8a2c42b3ee5030474f1e88_com_vec` |
| 5.23 | 3300 |  | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce...` |
| 5.16 | 4530 | int8 | `sm75_xmma_fprop_implicit_gemm_interleaved_i8i8_i8i32_f32_nchw_vect_c_32kcrs_vect_c_32_nchw_vect_c_32_tilesize128x128x...` |
| 4.44 | 1760 |  | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_com_vec` |
| 4.21 | 3300 |  | `__myl_CastMulAddReshTranReshMove_0x0340c5e5be98d9cff14028d435e46a87_com_vec` |
| 2.36 | 604 |  | `_gemm_mha_v2_0x5670ba801b2de8a2907d63de1165fdb4` |
| 2.14 | 1650 |  | `__myl_CastMulAddReshTranReshMove_0x132535db0b518e0a175a5158bc1b1139_com_vec` |
| 1.86 | 5760 |  | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce...` |
| 1.44 | 3072 |  | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_vec` |
| 1.22 | 1650 |  | `__myl_MoveReshTran_0x7bfad93cb08ea2697ad4d01ea85ce2ff_com_vec` |
| 1.18 | 302 | fp32 | `_gemm_mha_v2_0xc5e1df17f326bb0acdf956581133cde2` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x1fe1cc1fc70208fa1b2cf8ace9d12c4f` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x7f1aba88ddd93d06bfd656f26231a9bf` |
| 1.18 | 302 |  | `_gemm_mha_v2_0xa3cb0d93fdf10f031368b0c1d43bf756` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x4362f572a7cf6cb4ad2c8c19dbcd894e` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x188def927c4090eca727b3bc88fcb84c` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x8e523ab71e8f56bda53303a6b0159433` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x916e750f5fe2a6f85fdda9ed10fb3a26` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x7c5e2a1a7e738844c5cd295f7218cf2c` |
| 1.18 | 302 |  | `_gemm_mha_v2_0xc6427f6492575c48cba1f2cb774869a7` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x272ddac71277ded0dfb3c7e43feb3246` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x470d36d515ee4c30a019cd14bb6fdb8c` |
| 1.18 | 302 |  | `_gemm_mha_v2_0x7cf0991643142488783ef6b89f8b520a` |
| 1.05 | 6040 | int8 | `sm80_xmma_gemm_i8i8_i8i32_f32_tn_n_tilesize128x64x64_stage3_warpsize2x2x1_tensor16x8x32_execute_kernel_trt` |
| 0.89 | 2880 |  | `__myl_CastMul_0x9698266d4f8a2c42b3ee5030474f1e88_vec` |
| 0.82 | 5760 |  | `__myl_CastMulAddReshTranReshMove_0x0340c5e5be98d9cff14028d435e46a87_vec` |
| 0.53 | 4832 | int8 | `sm80_xmma_gemm_i8i8_i8i32_f32_tn_n_tilesize64x64x64_stage4_warpsize2x2x1_tensor16x8x32_execute_kernel_trt` |
| 0.50 | 302 | fp16 | `sm80_xmma_gemm_f16f16_f16f16_f16_tn_n_tilesize64x32x64_stage5_warpsize2x2x1_tensor16x8x16_aligna4_alignc4_execute_ker...` |
| 0.41 | 2880 |  | `__myl_CastMulAddReshTranReshMove_0x132535db0b518e0a175a5158bc1b1139_vec` |
| 0.29 | 2880 |  | `__myl_MoveReshTran_0x7bfad93cb08ea2697ad4d01ea85ce2ff_vec` |
| 0.27 | 110 |  | `__myl_CastMulAddExpAddLogLteSeleTanhMulCastMeanSubMulMeanAddSqrtDivMulCastMulAddReshMulAddMulMinEtc_0x3a8306f934fdfa6...` |
| 0.25 | 2880 | fp16 | `__myl_CastMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0xf169f4206b1b4779adbe74d8c024b8ab_vec` |
| 0.24 | 1650 | fp16 | `__myl_CastMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0xf169f4206b1b4779adbe74d8c024b8ab_com_vec` |
| 0.21 | 110 |  | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xf9a3d7f84e1cc381972431d2bba01e24_com_vec` |
| 0.18 | 110 |  | `__myl_ReshCastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x23ac8c059f65793ee18c9b5...` |
| 0.16 | 110 |  | `__myl_CastMulAddMulMinMaxRounCastReshSlic_0x03c2870252d5afe977f75d1238955178_com_vec` |
| 0.14 | 110 |  | `__myl_CastMulAdd_0xe6df7ff68d345137106e7b12ad9978cf_com_vec` |
| 0.13 | 192 |  | `__myl_CastMulAddExpAddLogLteSeleTanhMulCastMeanSubMulMeanAddSqrtDivMulCastMulAddReshMulAddMulMinEtc_0x3a8306f934fdfa6...` |
| 0.07 | 2880 |  | `__myl_CastMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x3d2a068ed99bed3f6ac90757dbdce535_vec` |
