# Active model artifacts

This directory holds Person B's generated models and sidecars. Active names: `fp16`, `s1`, `s2`, `s3`, `s4` (best), `s4aa`, `s0`, `s1sp`, `swap_pol8`, `swap_val8`; `bt3_fp32.onnx` is the exported source graph. Original hashes are in `reports/C2-build-manifest.json` and the consolidation manifest.

ONNX/wrapped network binaries remain local and are ignored by Git; recipe `.json` sidecars are shared. Use `maintenance/artifacts.py` and `artifacts/manifest.json` to transfer/verify binaries. Source BT3 is in `nets/`. Earlier A models are in `archive/person-a-week1/models/` and are distinct artifacts.
