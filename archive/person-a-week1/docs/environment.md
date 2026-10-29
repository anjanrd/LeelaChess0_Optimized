# Person A development environment

Step 3 passed on 2026-10-21. The machine-readable evidence is `environment/step3-verification.json`. A package installation alone is not proof of GPU execution; the report includes actual execution-provider evidence and numerical checks.

## Verified versions and results

| Component | Verified version/result |
| --- | --- |
| Python | 3.10.12 |
| PyTorch | 2.8.0; actual CUDA calculation passed |
| CUDA runtime used by PyTorch | 12.8 |
| ONNX | 1.21.0 |
| ONNX Runtime GPU | 1.22.0; CUDA and TensorRT provider execution passed |
| TensorRT | 10.9.0.34 |
| NVIDIA ModelOpt | 0.47.0; ONNX quantization API import passed |
| NumPy | 1.26.4 |
| Matplotlib | 3.10.7 |
| python-chess / chess | 1.999 / 1.11.2 |
| lc0 | v0.33.0-rc0, commit `9f45ea446baf9ce55e299250cde3053b7e93a035` |
| Package consistency | `pip check`: no broken requirements |

The complete checkpoint was downloaded and passed gzip integrity verification. Compressed SHA-256: `e3067757d1fc2dfc66947b21d15ace0cedf4c54254fc1de83d77c378a3e8b8e1`. The native loader confirmed 15 blocks, 24 heads, width 768, FFN width 1024, classical 112-plane inputs, WDL values, and a moves-left head. The locally computed digest is not a publisher-authenticated checksum.

## Locations

| Item | Location |
| --- | --- |
| Windows project | `C:\Users\HP\Desktop\LC0` |
| Same project from Ubuntu | `/mnt/c/Users/HP/Desktop/LC0` |
| Ubuntu distribution | `Ubuntu-22.04` (WSL 2) |
| Isolated Python environment | `/home/anjanrd/.local/share/lc0-int8/venv` |
| Pinned lc0 source | `/home/anjanrd/.local/share/lc0-int8/source/lc0` |
| lc0 tool/reference build | `/home/anjanrd/.local/share/lc0-int8/build/lc0-tools` |
| Checkpoint | `models/source/BT3-768x15x24h-swa-2790000.pb.gz` |
| Checkpoint identity | `models/source/checkpoint.json` |
| Requested dependencies | `requirements/step3.in` |
| Resolved dependency lock | `requirements/step3.lock`, generated after successful verification |

Large dependency installations and source/build output live in Ubuntu's Linux filesystem. Partial model downloads and smoke-test graphs/profiles use system temporary storage. The checkpoint is an intended project artifact, excluded from Git by `.gitignore`; its small identity manifest is versionable.

## Enter the environment

From PowerShell:

```powershell
wsl -d Ubuntu-22.04
```

Then, inside Ubuntu:

```bash
cd /mnt/c/Users/HP/Desktop/LC0
source /home/anjanrd/.local/share/lc0-int8/venv/bin/activate
```

Use the environment's `python`, not the separate Windows Python installation.

## Reproduction stages

The Ubuntu prerequisites installed for this setup are:

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends build-essential python3-dev python3-venv ca-certificates cmake ninja-build pkg-config zlib1g-dev libabsl-dev libeigen3-dev
```

Run the named stages from the Ubuntu project directory, in order:

```bash
bash scripts/setup_step3.sh bootstrap
bash scripts/setup_step3.sh install
python3 scripts/acquire_checkpoint.py
bash scripts/setup_step3.sh build
bash scripts/setup_step3.sh verify
```

`bootstrap` creates the virtual environment and checks out the exact lc0 commit. `install` uses the requested top-level dependency versions. After verification, use `python -m pip install -r requirements/step3.lock` in an activated matching environment to reproduce the resolved versions; retain the Ubuntu package/build provenance too. Python packages are sourced from PyPI and NVIDIA's TensorRT wheel distribution. The lock records versions, not a fully offline wheel archive or cryptographic hashes for every package.

The setup script uses `$XDG_DATA_HOME/lc0-int8` when configured, otherwise `$HOME/.local/share/lc0-int8`. The paths above describe this device's actual default layout.

## Verification boundary

Step 3 checks package consistency; actual PyTorch CUDA arithmetic; actual ONNX Runtime CUDA and TensorRT execution on a small synthetic matrix graph, with provider evidence from profiling; checkpoint hashing and metadata; lc0 export/wrapper options; and the compiled Python binding.

The lc0 binary built here includes the Eigen CPU backend, exporter, metadata tools, and Python bindings. It is an independent reference/development build. It does not include lc0's GPU backends and must not be used as the final GPU benchmark binary. GPU runtime smoke tests use Python/ONNX Runtime directly.

No CUDA compiler or Linux display driver is installed by this setup. CUDA runtime libraries come from the pinned Python dependencies and use the existing Windows NVIDIA driver exposed to WSL. Native CUDA compilation, final lc0 onnx-trt integration, and `trtexec` are separate later systems work.

The generic matrix checks do not establish BT3 export correctness, INT8 kernel coverage, playing strength, or training feasibility. Those remain later roadmap steps.

The initial Step 5 attempt exported and checked the actual BT3 FP32/FP16 graphs. FP32 conversion passed against native Eigen CPU; the FP16 WDL numerical gate failed on one pilot root through both CUDA and TensorRT. Actual TensorRT execution was checked, but its cache option did not produce a serialized engine, leaving identity/reuse unresolved at that historical checkpoint. No package versions changed.

On 2026-10-25, the resumed Step 5 work explained and reproduced the old ORT cache filename failure, then used direct TensorRT Runtime API serialization. Two approximately 209 MB candidates are preserved under `/home/anjanrd/.local/share/lc0-int8/step5-preserved/`, with engine hashes and fresh-process reload evidence. CUPTI traces establish executed FP32 SGEMMs for the strict CUDA baseline and executed FP16 Tensor Core GEMMs for both TensorRT candidates (native accumulation and requested FP32 accumulation). PyTorch supplies buffers/streams/profiling, not model math. No package/driver changes or new profiler installation were needed. Detailed traces, inspector output, build sources and engine binaries remain outside the project.

The user accepted the first engine, `bt3-f16-4271981b85fb44dd.plan`, with its documented 1.9593-percentage-point WDL discrepancy on one of 128 confirmation positions. Step 5 is complete with that explicit exception; the raw failed confirmation and unchanged original limits remain recorded. Final live reload reproduced saved outputs exactly. Pilot inference timings are recorded separately from future benchmarks: initial CUDA-event and host-clock intervals disagreed, while the final repeat agreed within 1.1%. Final benchmarking must check clock agreement under its measurement conditions. The optional shared builder timing cache was overwritten during the rejected revision; use the intact accepted serialized engine for reproducibility. Future builds use hash-specific cache names, and rebuilding is not promised bit-identical. See `docs/onnx-validation.md`, `environment/step5-final-integrity.json`, and `environment/step5-final-manifest.json`. Step 6 has not started.
