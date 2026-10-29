# C2-done

s3 s3_p99999.onnx: lowest finite dev KL 2.20e-02, top-1 0.844; s3 ties use higher top-1. Alpha 0.7: lowest eligible dev KL 4.13e-03, top-1 0.891 >= s3 0.844. best=s4. KL ties favor unsmoothed s3; equal alpha rows use smaller alpha deterministically.

Recipe: {"s3_method": "percentile", "s3_percentile": 99.999, "s4_alpha": 0.7}; best=s4; study.limit=2437.

Warnings: WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md; WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md; C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py:154: RuntimeWarning: invalid value encountered in divide; warning: /attn_body/embedding/preprocess/matmul/w: 512 calibration rows for K=768 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder0/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder1/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder2/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder3/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder4/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder5/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder6/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder7/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder8/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder9/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder10/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder11/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder12/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder13/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /encoder14/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /value/dense1/matmul/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help); warning: /mlh/dense1/matmul/w: 512 calibration rows for K=512 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)

Resume study from leela-int8: `..\.venv\Scripts\python.exe -u ladder.py study`. Then `..\.venv\Scripts\python.exe -u ladder.py score`.

# Scores (test), reference = fp16

## Study A: raw network (budget 0)

| model | n | tb accuracy [95% CI] | DTZ-optimal | KL vs ref | top-1 agree | mean abs dV |
|---|---|---|---|---|---|---|
| fp16 | 2437 | 0.9975 [0.995,0.999] | 0.9302 | 0.00e+00 | 1.0000 | 0.0000 |
| s1 | 2437 | 0.9947 [0.991,0.997] | 0.9192 | 3.08e-02 | 0.8203 | 0.0145 |
| s2 | 2437 | 0.9959 [0.992,0.998] | 0.9183 | 2.84e-02 | 0.8071 | 0.0125 |
| s3 | 2437 | 0.9975 [0.995,0.999] | 0.9216 | 2.23e-02 | 0.8363 | 0.0143 |
| s4 | 2437 | 0.9975 [0.995,0.999] | 0.9290 | 4.49e-03 | 0.8880 | 0.0054 |
| s4aa | 2437 | 0.9975 [0.995,0.999] | 0.9261 | 5.27e-03 | 0.8794 | 0.0050 |
| s0 | 2437 | 0.8034 [0.787,0.819] | 0.6373 | 7.46e-01 | 0.4407 | 1.4042 |
| s1sp | 2437 | 0.9910 [0.986,0.994] | 0.9097 | 7.41e-02 | 0.7920 | 0.0339 |
| swap_pol8 | 2437 | 0.9975 [0.995,0.999] | 0.9290 | 4.49e-03 | 0.8880 | 0.0001 |
| swap_val8 | 2437 | 0.9975 [0.995,0.999] | 0.9311 | 7.61e-06 | 0.9807 | 0.0054 |

## Study B: fixed node budgets

Accuracy (paired vs ref: −worse/+better, McNemar p), mean actual nodes.

| model | n | raw | 100 nodes | 400 nodes | 800 nodes | 1600 nodes |
|---|---|---|---|---|---|---|
| fp16 | 2437 | 0.9975 | 0.9996 @187 | 1.0000 @548 | 1.0000 @951 | 1.0000 @1794 |
| s1 | 2437 | 0.9947 | 0.9992 (−1/+0, p=1) @187 | 1.0000 (−0/+0, p=1) @529 | 1.0000 (−0/+0, p=1) @963 | 1.0000 (−0/+0, p=1) @1825 |
| s2 | 2437 | 0.9959 | 0.9996 (−0/+0, p=1) @190 | 1.0000 (−0/+0, p=1) @530 | 1.0000 (−0/+0, p=1) @957 | 1.0000 (−0/+0, p=1) @1823 |
| s3 | 2437 | 0.9975 | 0.9996 (−0/+0, p=1) @191 | 0.9996 (−1/+0, p=1) @534 | 1.0000 (−0/+0, p=1) @956 | 1.0000 (−0/+0, p=1) @1824 |
| s4 | 2437 | 0.9975 | 0.9996 (−0/+0, p=1) @194 | 1.0000 (−0/+0, p=1) @535 | 1.0000 (−0/+0, p=1) @943 | 1.0000 (−0/+0, p=1) @1832 |
| s4aa | 2437 | 0.9975 | 0.9996 (−0/+0, p=1) @193 | 1.0000 (−0/+0, p=1) @540 | 1.0000 (−0/+0, p=1) @943 | 1.0000 (−0/+0, p=1) @1818 |
| s1sp | 2437 | 0.9910 | 0.9938 (−14/+0, p=0.00012) @185 | 0.9930 (−17/+0, p=1.5e-05) @519 | 0.9943 (−14/+0, p=0.00012) @944 | 0.9943 (−14/+0, p=0.00012) @1807 |
| swap_pol8 | 2437 | 0.9975 | 0.9996 (−0/+0, p=1) @175 | 1.0000 (−0/+0, p=1) @528 | 1.0000 (−0/+0, p=1) @929 | 1.0000 (−0/+0, p=1) @1768 |
| swap_val8 | 2437 | 0.9975 | 0.9996 (−0/+0, p=1) @175 | 1.0000 (−0/+0, p=1) @528 | 1.0000 (−0/+0, p=1) @929 | 1.0000 (−0/+0, p=1) @1769 |

### Node-equivalents (FP16 nodes needed ÷ model nodes)

| model | 100 | 400 | 800 | 1600 |
|---|---|---|---|---|
| fp16 | 1.00 | 1.00 | 1.00 | 1.00 |
| s1 | 0.35 | 1.04 | 1.00 | 1.00 |
| s2 | 0.99 | 1.03 | 1.00 | 1.00 |
| s3 | 0.98 | 0.35 | 1.00 | 1.00 |
| s4 | 0.97 | 1.02 | 1.00 | 1.00 |
| s4aa | 0.97 | 1.02 | 1.00 | 1.00 |
| s1sp | 0.00 | 0.00 | 0.00 | 0.00 |
| swap_pol8 | 1.07 | 1.04 | 1.00 | 1.00 |
| swap_val8 | 1.07 | 1.04 | 1.00 | 1.00 |

## Raw accuracy by material class

| class | n | fp16 | s1 | s2 | s3 | s4 | s4aa | s0 | s1sp | swap_pol8 | swap_val8 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KBNvK | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.839 | 1.000 | 1.000 | 1.000 |
| KBPvK | 87 | 1.000 | 0.989 | 1.000 | 1.000 | 1.000 | 1.000 | 0.782 | 1.000 | 1.000 | 1.000 |
| KBPvKB | 87 | 1.000 | 1.000 | 0.977 | 1.000 | 1.000 | 1.000 | 0.908 | 1.000 | 1.000 | 1.000 |
| KBPvKN | 87 | 0.977 | 0.966 | 0.989 | 0.977 | 0.977 | 0.989 | 0.805 | 0.966 | 0.977 | 0.977 |
| KBvKP | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.816 | 1.000 | 1.000 | 1.000 |
| KNPvK | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.724 | 1.000 | 1.000 | 1.000 |
| KNvKP | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.667 | 1.000 | 1.000 | 1.000 |
| KPPvK | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.862 | 1.000 | 1.000 | 1.000 |
| KPPvKN | 87 | 0.989 | 0.989 | 0.989 | 0.989 | 0.989 | 0.989 | 0.644 | 0.977 | 0.989 | 0.989 |
| KPPvKP | 87 | 0.989 | 0.977 | 0.977 | 1.000 | 0.989 | 0.989 | 0.690 | 0.989 | 0.989 | 0.989 |
| KPvK | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.713 | 0.989 | 1.000 | 1.000 |
| KPvKP | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.598 | 0.989 | 1.000 | 1.000 |
| KQPvKQ | 87 | 1.000 | 0.989 | 1.000 | 1.000 | 1.000 | 1.000 | 0.701 | 0.989 | 1.000 | 1.000 |
| KQRvKQ | 87 | 1.000 | 1.000 | 0.989 | 1.000 | 1.000 | 0.989 | 0.805 | 0.989 | 1.000 | 1.000 |
| KQvK | 88 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.932 | 1.000 | 1.000 |
| KQvKP | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.908 | 1.000 | 1.000 | 1.000 |
| KQvKQ | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.989 | 1.000 | 1.000 | 1.000 |
| KQvKR | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.862 | 1.000 | 1.000 | 1.000 |
| KQvKRP | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.805 | 0.989 | 1.000 | 1.000 |
| KRBvKR | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.874 | 1.000 | 1.000 | 1.000 |
| KRNvKR | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.908 | 1.000 | 1.000 | 1.000 |
| KRPvKB | 87 | 1.000 | 0.989 | 1.000 | 1.000 | 1.000 | 1.000 | 0.713 | 0.977 | 1.000 | 1.000 |
| KRPvKR | 87 | 0.989 | 0.989 | 0.989 | 0.989 | 0.989 | 0.989 | 0.828 | 0.989 | 0.989 | 0.989 |
| KRRvKR | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.931 | 1.000 | 1.000 | 1.000 |
| KRvK | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.943 | 1.000 | 1.000 | 1.000 |
| KRvKB | 87 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.805 | 1.000 | 1.000 | 1.000 |
| KRvKN | 87 | 0.989 | 0.977 | 0.989 | 0.977 | 0.989 | 0.989 | 0.621 | 0.989 | 0.989 | 0.989 |
| KRvKP | 87 | 1.000 | 0.989 | 0.989 | 1.000 | 1.000 | 1.000 | 0.759 | 0.989 | 1.000 | 1.000 |
