# LOG

All times 2026-10-27, local. Times come from command output or file mtimes. Paths are relative to `C:\Users\HP\Desktop\LC0-B` unless absolute.
Shell: Git Bash unless marked PowerShell.

## Deviations from AGENTS.md (read first)

AGENTS.md (mtime 23:29) appeared while this session was already running. Points where what was done differs from it:
- `.venv\`, `tools\` and `syzygy\` were **created by the agent in this session**, not earlier by someone else. Everything in them is listed below with source URLs and sha256.
- "Reuse his installs ... don't re-download": Anjan's lc0 has only CPU backends (eigen), and his TensorRT 10.9.0.34 is a Python wheel in his venv, so neither could be reused for lc0 onnx-trt or trtexec. These were downloaded. Nsight Systems did not exist anywhere and was downloaded too.
- Syzygy was **copied** from Anjan's WSL env into `syzygy\` (read from his env only), not used by path.
- BT3 was copied to `leela-int8\nets\BT3.pb.gz` (the runbook's location). sha256 checked against Anjan's record.
- "Run nvidia-smi first" before GPU jobs: nvidia-smi ran at 23:19 (GPU idle). It was not rerun just before the onnx-trt smoke test.
- Exit codes: tbset, the smoke test and calib were piped through `tail`, so the exit code recorded is the pipeline's, not the program's. Evidence they succeeded is listed per step.
- No code in quant/, eval/ or tb/ was changed. The only config change is config.json (diff below).

## 23:19 Step 0: inventory

`nvidia-smi` exit 0:
```
NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1
0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
N/A   41C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
No running processes found
```
`nvidia-smi --query-gpu=name,driver_version,memory.total,power.limit,clocks.max.sm --format=csv`:
```
NVIDIA GeForce RTX 4060 Laptop GPU, 592.82, 8188 MiB, [N/A], 3105 MHz
```
`python --version` -> `Python 3.11.9`. `py -0p`: 3.13 (default for `py`) and 3.11 installed.

Native Windows: `where lc0 lc0.exe trtexec trtexec.exe nsys nsys.exe` -> `INFO: Could not find files for the given pattern(s).` No `C:\lc0`, `C:\TensorRT*`, CUDA toolkit or Nsight under `C:\Program Files\NVIDIA Corporation`. No lc0/TensorRT/Nsight/cuDNN zips under Desktop or Downloads. C: has 551G free.

Anjan's repo (read only): `C:\Users\HP\Desktop\LC0\docs\environment.md` says the WSL lc0 build "does not include lc0's GPU backends" and that the BT3 checkpoint has "classical 112-plane inputs". Checkpoint at `C:\Users\HP\Desktop\LC0\models\source\BT3-768x15x24h-swa-2790000.pb.gz`, recorded sha256 `e3067757d1fc2dfc66947b21d15ace0cedf4c54254fc1de83d77c378a3e8b8e1`.

WSL (`wsl -l -v`): Ubuntu-22.04 (default) and Ubuntu, both Stopped, version 2.
Read-only probe of `/home/anjanrd/.local/share/lc0-int8` (scratchpad script `probe.sh`, PowerShell `wsl.exe -d Ubuntu-22.04 -- bash .../probe.sh`). A first attempt from Git Bash garbled the paths; that run's output was discarded.
```
lc0 bin: /home/anjanrd/.local/share/lc0-int8/build/lc0-tools/lc0
v0.33.0-rc0 built Oct 21 2026
Unhandled exception: Flag '--backend' must be one of the following values: eigen trivial random check roundrobin recordreplay multiplexing demux.
== syzygy
290
145      (*.rtbw)
145      (*.rtbz)
939M	/home/anjanrd/.local/share/lc0-int8/syzygy
     10 3     (files per piece count)
     60 4
    220 5
== venv
10.9.0.34 1.22.0 ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
== nsys/trtexec
(none found; no /usr/local/cuda*, no /opt/nvidia)
```
WSL: 16 CPUs, 15 GiB RAM.

Inventory result:
| Item | Found | Used |
|---|---|---|
| GPU / driver | RTX 4060 Laptop, 8188 MiB, 592.82, CUDA 13.1, WDDM | - |
| Python | 3.11.9 (Windows) | `.venv\` (3.11) |
| lc0 Windows | none | downloaded v0.33.0-rc0 onnx-trt to `tools\lc0\` |
| lc0 WSL | Anjan's, v0.33.0-rc0, eigen/CPU only, no onnx-trt | not used |
| TensorRT / trtexec | WSL Python wheel 10.9.0.34 only, no trtexec | downloaded TRT 10.12.0.36 zip, `tools\TensorRT-10.12.0.36\bin\trtexec.exe` |
| nsys | none | downloaded Nsight Systems 2025.1.3.140 to `tools\nsys\` |
| BT3 | Anjan's repo | copied to `leela-int8\nets\BT3.pb.gz` |
| Syzygy 3-4-5 WDL+DTZ | Anjan's WSL env, 290 files, 939M | copied to `syzygy\` |

## 23:22 BT3 copy

`cp C:/Users/HP/Desktop/LC0/models/source/BT3-768x15x24h-swa-2790000.pb.gz leela-int8/nets/BT3.pb.gz && sha256sum leela-int8/nets/BT3.pb.gz` exit 0:
```
e3067757d1fc2dfc66947b21d15ace0cedf4c54254fc1de83d77c378a3e8b8e1 */c/Users/HP/Desktop/LC0-B/leela-int8/nets/BT3.pb.gz
```
Matches Anjan's recorded digest.

## 23:22 Syzygy copy (PowerShell)

`wsl.exe -d Ubuntu-22.04 -- cp -r --preserve=timestamps /home/anjanrd/.local/share/lc0-int8/syzygy/. /mnt/c/Users/HP/Desktop/LC0-B/syzygy/` exit 0. Files counted afterwards: `290`, `938 MB`.

## 23:22 lc0 download

`curl -sSL -o tools/dl/lc0-v0.33.0-rc0-windows-onnx-trt.zip https://github.com/LeelaChessZero/lc0/releases/download/v0.33.0-rc0/lc0-v0.33.0-rc0-windows-onnx-trt.zip`, then unzip into `tools\lc0\`. Exit 0. The zip is 224570575 bytes, matching the GitHub release asset size. It bundles `onnxruntime.dll` and the ORT CUDA/TensorRT providers. The engine cache name below shows ORT 1.22.1.

## 23:22-23:30 CUDA / cuDNN / TensorRT DLLs (background task)

`install.cmd` stops at `pause` prompts and deletes the TensorRT zip, so its steps were run by hand with the same URLs. Base URL `https://developer.download.nvidia.com/compute/`:
```
cuda/redist/cuda_cudart/windows-x86_64/cuda_cudart-windows-x86_64-12.9.79-archive.zip
cuda/redist/libcublas/windows-x86_64/libcublas-windows-x86_64-12.9.1.4-archive.zip
cuda/redist/libcufft/windows-x86_64/libcufft-windows-x86_64-11.4.1.4-archive.zip
cudnn/redist/cudnn/windows-x86_64/cudnn-windows-x86_64-9.11.0.98_cuda12-archive.zip
machine-learning/tensorrt/10.12.0/zip/TensorRT-10.12.0.36.Windows.win10.cuda-12.9.zip
```
The same DLLs install.cmd extracts were put into `tools\lc0\` (cudart64_12, cublas64_12, cublasLt64_12, cufft64_11, cudnn64_9, cudnn_graph64_9, nvinfer_10, nvinfer_builder_resource_10, nvinfer_plugin_10, nvonnxparser_10). The full TensorRT zip was unpacked to `tools\TensorRT-10.12.0.36\`. Exit 0. Key output: `trtexec.exe` listed in `tools/TensorRT-10.12.0.36/bin`.

sha256 of the downloads (`tools\dl\`):
```
9dbe34b491aefb3ea5c46c5e4f672f1461c65af13a63668546c3c64fc05aab48  lc0-v0.33.0-rc0-windows-onnx-trt.zip
179e9c43b0735ffe67207b3da556eb5a0c50f3047961882b7657d3b822d34ef8  cuda_cudart-windows-x86_64-12.9.79-archive.zip
d534d98b0b453a98914dbf3adf47d7e84b55037abf02f87466439e1dcef581ed  libcublas-windows-x86_64-12.9.1.4-archive.zip
f26f80bb9abff3269c548e1559e8c2b4ba58ccb8acc6095bbc6404fc962d4b80  libcufft-windows-x86_64-11.4.1.4-archive.zip
947988b49209d0d22c81809f20f8e7a703e9347d519317e1468e11fd70bb195a  cudnn-windows-x86_64-9.11.0.98_cuda12-archive.zip
965d8d70c3954449131754669c3f8aadfc17b35bd94c91bd795effef5628d8c6  TensorRT-10.12.0.36.Windows.win10.cuda-12.9.zip
8d61f266a8a1bc1ababd44de3ee38f7b85c8cdfcdaebace14c8f065d7624d0b3  nsight_systems.zip
```

## 23:23-23:3x pip install

`py -3.11 -m venv .venv && .venv/Scripts/python -m pip install -q --upgrade pip && .venv/Scripts/python -m pip install -r leela-int8/requirements.txt`. The venv was created at 23:22 (pyvenv.cfg mtime). The `-q` install printed nothing for over 10 minutes. Trying to stop it was denied by the permission system. A second, non-quiet run (`pip install --progress-bar off -r leela-int8/requirements.txt`) finished at the same time. The background task for the first run then reported exit 0. Key output:
```
Successfully installed chess-1.11.2 contourpy-1.3.3 cycler-0.12.1 flatbuffers-25.12.19 fonttools-4.68.0 kiwisolver-1.5.1 matplotlib-3.11.2 ml_dtypes-0.6.0 numpy-2.4.6 nvidia-ml-py-13.615.71 onnx-1.23.2 onnxruntime-1.31.1 packaging-26.3 pillow-13.0.0 protobuf-7.36.2 pyparsing-3.3.3 python-chess-1.999 python-dateutil-3.0.0 six-1.17.0 typing_extensions-4.16.0 tzdata-2026.5
```
pip in the venv was upgraded to 26.2.2. Python's onnxruntime 1.31.1 is CPU-only and is used only by the ONNX-side tools. lc0 uses its own bundled ORT 1.22.1 (trap 3 concerns lc0's ORT).

## 23:38 Nsight Systems (background task)

`curl -sSL -o tools/dl/nsight_systems.zip https://developer.download.nvidia.com/compute/cuda/redist/nsight_systems/windows-x86_64/nsight_systems-windows-x86_64-2025.1.3.140-archive.zip`, unzipped to `tools\nsys\`. Exit 0. The URL comes from `cuda/redist/redistrib_12.9.1.json` (`nsight_systems 2025.1.3.140`, size 403084779). Output:
```
../nsys/nsight_systems-windows-x86_64-2025.1.3.140-archive/nsight-systems/2025.1.3/target-windows-x64/nsys.exe
```

## 23:38 config.json

Made from config.example.json with a short Python script. Diff (`python -m json.tool` of both files), plus the nsys path set after the Nsight download (23:38:50); `shutil.which` resolves it:
```
<     "lc0": "C:/lc0/lc0.exe",
<     "trtexec": "C:/TensorRT-10.12.0.36/bin/trtexec.exe",
<     "nsys": "nsys",
<     "syzygy": "D:/syzygy/3-4-5",
---
>     "lc0": "C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe",
>     "trtexec": "C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe",
>     "nsys": "C:/Users/HP/Desktop/LC0-B/tools/nsys/nsight_systems-windows-x86_64-2025.1.3.140-archive/nsight-systems/2025.1.3/target-windows-x64/nsys.exe",
>     "syzygy": "C:/Users/HP/Desktop/LC0-B/syzygy",
```
All other keys are as in config.example.json. ladder.py is run with `..\.venv\Scripts\python`.

## 23:36 Gate C1: tbset

From `leela-int8\`: `../.venv/Scripts/python ladder.py tbset 2>&1 | tail -40` (background). Pipeline exit 0. ladder.py did not print `step failed` and the output file exists. Underlying command (from `reports\logs\tbset.log`):
```
C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\tb\build_tbset.py --syzygy C:/Users/HP/Desktop/LC0-B/syzygy --out C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --per-class 400
```
Key output (28 classes, each `400 kept`; the full per-class table is in the log):
```
KPvKP    400 kept / 739 tried
...
KPPvK    400 kept / 3261 tried
...
wrote 11200 positions to C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl: {'calib': 1120, 'dev': 3360, 'test': 6720}; won 6803, drawn 4397
```
`wc -l data/tbset.jsonl` -> 11200. Produced: `leela-int8\data\tbset.jsonl` (6694891 bytes, 23:36:29), `leela-int8\reports\logs\tbset.log`.

## 23:44 onnx-trt smoke test

The first attempt (about 23:31) was denied by the permission system (not run). The user approved running `tools\lc0\lc0.exe`.

From `tools\lc0\`: `timeout 900 ./lc0.exe benchmark --weights=791556.pb.gz --backend=onnx-trt --backend-opts=optimize=6 --nodes=5000 --num-positions=2 2>&1 | grep -vE "^\s*$" | tail -30`. Pipeline exit 0 (lc0's own code not captured). lc0 printed its final summary:
```
Benchmark time 365 ms, 5001 nodes, 13853 nps, move e2a6
bestmove e2a6
===========================
Total time (ms) : 768
Nodes searched  : 10534
Nodes/second    : 13698
```
A second run (`--nodes=500 --num-positions=1`, grep for onnx/trt/fp32/fp16/provider/warn/error/cuda) printed only:
```
CUDA runtime version: 12.9.0
Latest version of CUDA supported by the driver: 13.1.0
```
No FP32 or other warnings. Produced: `tools\lc0\trt_cache\Lc0_ONNX_TRT_ORT_1.22.1_batch_-1_6_296cd0c45b33761b__15856772200426395709_0_fp16_sm89.engine` (+ `.profile`, `TensorrtExecutionProvider_cache_sm89.timing`), 23:44.
The net is the bundled T79 (791556.pb.gz), not BT3. BT3 has not been run on the GPU yet.

## 23:44 describenet BT3

`tools/lc0/lc0.exe describenet --weights=leela-int8/nets/BT3.pb.gz`. Exit 0 (checked on a rerun with absolute paths). Key output:
```
Weights file has multihead format, updating format flag
         Minimal Lc0 version: v0.30.0
                       Input: INPUT_CLASSICAL_112_PLANE
                     Network: NETWORK_ATTENTIONBODY_WITH_MULTIHEADFORMAT
             Input embedding: INPUT_EMBEDDING_PE_DENSE
                       Value: VALUE_WDL
                         MLH: MOVES_LEFT_V1
          Default activation: DEFAULT_ACTIVATION_MISH
              Training steps: 2790000
                    Encoders: 15
               Encoder heads: 24
              Embedding size: 768
                 Encoder DFF: 1024
                      Policy: Attention
```
BT3's input is classical (format 1), not V2 canonical as the README assumes. Traps 5 and 10 (nonzero halfmove clock hang/segfault on V2) therefore do not apply. Trap 1 (wrap.py copying formats) still does.

## 23:45 Gate C1: calib

From `leela-int8\`: `timeout 1800 ../.venv/Scripts/python ladder.py calib 2>&1 | tail -30`. Pipeline exit 0. ladder.py did not print `step failed` and both files exist. Output:
```
$ ...\.venv\Scripts\python.exe ...\quant\make_calib.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --weights nets/BT3.pb.gz --random-games 256 --tbset ...\data\tbset.jsonl --tb-split calib --n-tb 256 --out ...\data\calib.npz
wrote 512 positions (input format 1) to C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
$ ...\.venv\Scripts\python.exe ...\quant\make_calib.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --weights nets/BT3.pb.gz --tbset ...\data\tbset.jsonl --tb-split dev --n-tb 0 --out ...\data\dev.npz
wrote 3360 positions (input format 1) to C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz
```
Produced: `leela-int8\data\calib.npz` (235353 bytes, 23:45:01), `leela-int8\data\dev.npz` (670848 bytes, 23:45:04), `leela-int8\reports\logs\calib.log`.
Input format 1 matches BT3's INPUT_CLASSICAL_112_PLANE, which `check_npz_format` in day1 compares.

## Not done

- `ladder.py day1`: not run by the agent; the user is running it. `models\`, `results\` and `reports\` (apart from `reports\logs\`) are empty.

## 2026-10-28 00:14:11 +05:30 — C1-day1 approval and required reading
Commands (PowerShell; cwd C:\Users\HP\Desktop\LC0-B), both exit 0:
`Get-Content -LiteralPath .\leela-int8\STATUS.md; Get-Content -LiteralPath .\leela-int8\LOG.md`
`Get-Content -LiteralPath .\leela-int8\README.md; Get-Content -LiteralPath .\leela-int8\RUN_4060.md; Get-Content -LiteralPath .\leela-int8\day1.log; Get-Content -LiteralPath .\AGENTS.md`
Key output from prior STATUS.md:
~~~
| 1g day1 | todo | being run by the user, not by the agent |
| CHECKPOINT C1-day1 | todo | waits on day1 |
~~~
Bookkeeping command initially failed at PowerShell parsing, exit 1: "Missing ')' in method call." Cause: a Markdown backtick fence escaped a closing double quote. Nothing executed or changed. One permitted obvious-typo retry uses tilde fences.
User explicitly approved CHECKPOINT C1-day1. The day-1 summary block below is copied verbatim from day1.log (from its marker through EOF). The old "Not done" entry above is superseded.
Exact command for this bookkeeping step: read day1.log with [IO.File]::ReadAllText, take Substring from '=== day-1 summary ===', append it verbatim here; replace the day1 and checkpoint rows in STATUS.md. Exit 0.
Produced/updated: LOG.md, STATUS.md.

~~~text
=== day-1 summary ===
1. wrapped FP16 vs native lc0: KL 0.00e+00, top-1 1.000  -> OK
2. lc0 runs the INT8 file: OK (KL vs native 3.25e-02, top-1 0.760)
$ C:/Users/HP/Desktop/LC0-B/tools/nsys/nsight_systems-windows-x86_64-2025.1.3.140-archive/nsight-systems/2025.1.3/target-windows-x64/nsys.exe profile -o C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0 --force-overwrite true C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe benchmark --weights=C:\Users\HP\Desktop\LC0-B\leela-int8\models\s2.pb.gz --backend=onnx-trt --backend-opts=optimize=8 --nodes=20000 --num-positions=3
WARNING: CPU context switches trace requires administrative privileges, disabling.
WARNING: CPU sampling requires administrative privileges, disabling.
WARNING: Device-side CUDA Event completion trace is currently enabled.
         This may increase runtime overhead and the likelihood of false
         dependencies across CUDA Streams. If you wish to avoid this, please
         disable the feature with --cuda-event-trace=false.
Collecting data...
Generating 'C:\Users\HP\AppData\Local\Temp\nsys-report-acc1.qdstrm'

[1/1] [0%                          ] s2_lc0.nsys-rep
[1/1] [0%                          ] s2_lc0.nsys-rep
[1/1] [8%                          ] s2_lc0.nsys-rep
[1/1] [6%                          ] s2_lc0.nsys-rep
[1/1] [5%                          ] s2_lc0.nsys-rep
[1/1] [10%                         ] s2_lc0.nsys-rep
[1/1] [9%                          ] s2_lc0.nsys-rep
[1/1] [8%                          ] s2_lc0.nsys-rep
[1/1] [7%                          ] s2_lc0.nsys-rep
[1/1] [6%                          ] s2_lc0.nsys-rep
[1/1] [5%                          ] s2_lc0.nsys-rep
[1/1] [6%                          ] s2_lc0.nsys-rep
[1/1] [9%                          ] s2_lc0.nsys-rep
[1/1] [11%                         ] s2_lc0.nsys-rep
[1/1] [13%                         ] s2_lc0.nsys-rep
[1/1] [=16%                        ] s2_lc0.nsys-rep
[1/1] [==19%                       ] s2_lc0.nsys-rep
[1/1] [==21%                       ] s2_lc0.nsys-rep
[1/1] [===23%                      ] s2_lc0.nsys-rep
[1/1] [====26%                     ] s2_lc0.nsys-rep
[1/1] [====28%                     ] s2_lc0.nsys-rep
[1/1] [=====31%                    ] s2_lc0.nsys-rep
[1/1] [======33%                   ] s2_lc0.nsys-rep
[1/1] [======35%                   ] s2_lc0.nsys-rep
[1/1] [=======38%                  ] s2_lc0.nsys-rep
[1/1] [========40%                 ] s2_lc0.nsys-rep
[1/1] [=========43%                ] s2_lc0.nsys-rep
[1/1] [=========45%                ] s2_lc0.nsys-rep
[1/1] [==========48%               ] s2_lc0.nsys-rep
[1/1] [===========50%              ] s2_lc0.nsys-rep
[1/1] [===========53%              ] s2_lc0.nsys-rep
[1/1] [============55%             ] s2_lc0.nsys-rep
[1/1] [=============58%            ] s2_lc0.nsys-rep
[1/1] [==============61%           ] s2_lc0.nsys-rep
[1/1] [==============63%           ] s2_lc0.nsys-rep
[1/1] [==================75%       ] s2_lc0.nsys-rep
[1/1] [========================100%] s2_lc0.nsys-rep
[1/1] [========================100%] s2_lc0.nsys-rep
Generated:
	C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0.nsys-rep
$ C:/Users/HP/Desktop/LC0-B/tools/nsys/nsight_systems-windows-x86_64-2025.1.3.140-archive/nsight-systems/2025.1.3/target-windows-x64/nsys.exe stats --report cuda_gpu_kern_sum --format csv -o C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0 C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0.nsys-rep
Generating SQLite file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0.sqlite from C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0.nsys-rep
Processing [C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0.sqlite] with [C:\Users\HP\Desktop\LC0-B\tools\nsys\nsight_systems-windows-x86_64-2025.1.3.140-archive\nsight-systems\2025.1.3\host-windows-x64\reports\cuda_gpu_kern_sum.py] to [C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0_cuda_gpu_kern_sum.csv]... PROCESSED

$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\trt_layers.py kernels --csv C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0_cuda_gpu_kern_sum.csv
# GPU kernels in C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0_cuda_gpu_kern_sum.csv

all kernel time by tag: int8 50.5%, other 47.3%, fp32 1.2%, fp16 1.0%
GEMM-like kernel time by tag: int8 73.5%, other 24.1%, fp32 1.7%, fp16 0.7%
3. matmuls in INT8: see the 'GEMM-like kernel time by tag' line above (most should be int8)

~~~

## 2026-10-28 00:14:11 +05:30 — pre-flight and step-2 command inspection
Exact command (cwd leela-int8): Get-Content config.json; rg -n "pre.?flight|def (build|hw|study)|outlier|def kernels|other|bench" ladder.py hw/trt_layers.py hw/bench.py eval/run_study.py README.md RUN_4060.md; Get-Content ladder.py
Exit code: 0
Output:
~~~
{
 "lc0": "C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe",
 "trtexec": "C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe",
 "nsys": "C:/Users/HP/Desktop/LC0-B/tools/nsys/nsight_systems-windows-x86_64-2025.1.3.140-archive/nsight-systems/2025.1.3/target-windows-x64/nsys.exe",
 "bt3": "nets/BT3.pb.gz",
 "syzygy": "C:/Users/HP/Desktop/LC0-B/syzygy",
 "work": ".",
 "backend": "onnx-trt",
 "fp16_opts": "optimize=6",
 "int8_opts": "optimize=8",
 "native_backend": "onnx-trt",
 "native_opts": "optimize=6",
 "tbset": {
  "per_class": 400
 },
 "calib": {
  "random_games": 256,
  "n_tb": 256
 },
 "recipe": {
  "s3_method": "percentile",
  "s3_percentile": 99.99,
  "s4_alpha": 0.5
 },
 "best": "s4",
 "study": {
  "split": "test",
  "limit": 0,
  "budgets": "0,100,400,800,1600",
  "threads": 1,
  "minibatch": 256,
  "models": "fp16,s1,s2,s3,s4,s4aa"
 },
 "extras": {
  "s0_in_study_b": false,
  "swap": true,
  "s1sp": true
 },
 "studyc": {
  "movetimes": "200,800",
  "models": "fp16,BEST",
  "limit": 0
 },
 "match": {
  "tc": "10+0.1",
  "pairs": 250
 },
 "hw": {
  "batch_sizes": "32,64,128,256",
  "bench_movetime": 10000
 }
}
RUN_4060.md:5:close every other program (browser, games, Discord): they change the timings.
RUN_4060.md:20:Leave the laptop plugged in and untouched; close every other program. It runs, in order: day1 (a
RUN_4060.md:21:check that stops everything if the pipeline is wrong), FP16/INT8 benchmarks, a 50-position timing run
RUN_4060.md:37:python ladder.py hw --parts bench
ladder.py:17:  hw        bench + J/node, batch sweep, trtexec layer builds, roofline, peaks (GPU)
ladder.py:56:    "hw": {"batch_sizes": "32,64,128,256", "bench_movetime": 10000},
ladder.py:212:def study_cmd(cfg, name, budgets, split, limit, extra=()):
ladder.py:223:def build_model(cfg, name, log, force=False):
ladder.py:250:            cmd += ["--outlier-report", P(cfg, "reports", "outliers.txt")]
ladder.py:284:    bench = [cfg["lc0"], "benchmark", f"--weights={model_weights(cfg, 's2')}",
ladder.py:288:        run([nsys, "profile", "-o", rep, "--force-overwrite", "true", *bench], log, check=False)
ladder.py:298:              + " ".join(bench) + f"\n   nsys stats --report cuda_gpu_kern_sum --format csv -o {rep} {rep}.nsys-rep"
ladder.py:420:    parts = a.parts.split(",") if a.parts else ["bench", "sweep", "trt", "roofline"]
ladder.py:421:    if "bench" in parts:
ladder.py:425:            run([PY, script("hw", "bench.py"), "--lc0", cfg["lc0"], "--weights", model_weights(cfg, n),
ladder.py:427:                 "--movetime", h["bench_movetime"], "--out-dir", P(cfg, "reports", "bench")], log)
ladder.py:467:    ap.add_argument("--parts", default=None, help="hw: bench,sweep,trt,roofline")
hw/trt_layers.py:11:       nsys profile -o reports/trt/s4_lc0 --force-overwrite true lc0 benchmark --weights=models/s4.pb.gz --backend=onnx-trt --backend-opts=optimize=8 --nodes=20000 --num-positions=3
hw/trt_layers.py:209:        key = "+".join(sorted(tags)) or "other"
README.md:5:What has and hasn't been tested: every step ran end to end on CPU (lc0 v0.33.0-rc0 built for Linux, onnx-cpu backend) against two stand-in nets. One is the T79-era 15x192 SE-ResNet that ships in the Windows lc0 package (`791556.pb.gz`, a real trained net). The other is a tiny random-weight net with BT3's exact structure (attention body, smolgen, PE_DENSE embedding, canonical V2 input), made by `tests/make_toy_bt.py` so every BT3 graph path goes through `lc0 leela2onnx` as it will on the real net. Nothing has touched BT3, TensorRT or a GPU. Those runs are yours.
README.md:17:                         --act-act-matmul, outlier report
README.md:29:hw/bench.py              backendbench + benchmark with GPU (NVML) and CPU (RAPL) energy above idle
README.md:42:3. onnxruntime >= 1.27 with TensorRT 10 silently runs FP32 instead of FP16. The Windows v0.33.0-rc0 package bundles onnxruntime 1.22.1, so it's safe. `run_study.py` and `bench.py` shout if lc0 warns about FP32.
README.md:49:10. New today: `lc0 benchmark`'s built-in position 4 has a nonzero halfmove clock, and lc0 segfaults on it with a V2-canonical net (trap 5's cause again). BT3 is most likely V2, so `bench.py` and `batch_sweep.py` time UCI searches on their own halfmove-0 positions instead, and meter energy only around those searches. Don't use `lc0 benchmark` beyond `--num-positions=3` with BT3.
README.md:54:1. lc0: unzip `lc0-v0_33_0-rc0-windows-onnx-trt.zip`, run `install.cmd` (downloads the CUDA, cuDNN and TensorRT 10.12 DLLs), and check `lc0.exe benchmark --backend=onnx-trt` starts.
README.md:64:`python overnight.py` runs day1 (as a go/no-go gate), bench, a sizing run that sets `study.limit` and `studyc.limit` to fit `--study-hours`/`--studyc-hours`, Studies A+B, Study C, hw, the match (pairs sized to `--match-hours`), score, and zips everything into `send_back.zip`. It is resumable and never edits `config.json` (it writes `config.run.json`). Tested end to end on CPU only. The sections below describe each step.
README.md:78:3. The matmuls really run in INT8. With `nsys` on PATH it profiles an lc0 benchmark and prints the share of GEMM kernel time by precision. Most should be int8.
README.md:80:Then the outlier report and FP16 baselines:
README.md:83:python ladder.py build --only s4       # also writes reports/outliers.txt
README.md:84:python ladder.py hw --parts bench      # fp16, best and native: nps, J/node above idle, clocks
README.md:87:`outlier_ratio` is the worst input channel's |x|max over the median live channel's. Tens to hundreds on the LN outputs feeding QKV/FFN means SmoothQuant has work to do. Near 1-5 everywhere is risk row 3. Try `nvidia-smi -lgc <clock>` first (admin); if it refuses, the logged SM clock is your evidence.
README.md:122:python ladder.py hw                    # bench, batch sweep, trtexec builds (incl. sparse), peaks, roofline
README.md:128:- `reports/bench/<model>.json`: backendbench nps per batch, search nps over 10 fixed positions (10 s each), GPU J/node above idle, SM clock min/mean, max temperature.
README.md:146:What that showed, on stand-in nets (not results): wrapped FP32 matched native lc0 to KL 1e-8. On the trained T79 net, per-channel INT8 kept raw tablebase accuracy (0.993 vs 0.993) with policy KL 0.025; magnitude 2:4 dropped it to 0.972 and SparseGPT cut the value error versus magnitude by about 40% on the layers it could prune (T79's convs fall back to magnitude). On the toy transformer with planted outlier channels, SmoothQuant at alpha 0.5 cut policy KL about 3x versus percentile alone. SparseGPT's per-layer reconstruction error was about 30x below magnitude's, and it beat magnitude on held-out data in a synthetic check.
hw/bench.py:2:"""Throughput and energy for one model: `lc0 backendbench` (raw NN nps per
hw/bench.py:9:Trap 11: `lc0 benchmark`'s built-in positions include FENs with a nonzero
hw/bench.py:14:    python hw/bench.py --lc0 lc0 --weights models/fp16.pb.gz --backend-opts optimize=6 --name fp16
hw/bench.py:15:    python hw/bench.py --lc0 lc0 --weights nets/BT3.pb.gz --backend cuda-fp16 --name native_cuda
hw/bench.py:32:# Openings, middlegames and endgames (Stockfish bench positions), halfmove 0.
hw/bench.py:49:def search_bench(lc0, weights, backend, backend_opts, movetime, positions, idle=None,
hw/bench.py:50:                 threads=0, minibatch=0, log=None, name="bench"):
hw/bench.py:98:def parse_backendbench(txt):
hw/bench.py:108:def parse_benchmark(txt):
hw/bench.py:131:    ap.add_argument("--batches", type=int, default=200, help="backendbench batches per size")
hw/bench.py:140:    ap.add_argument("--skip-backendbench", action="store_true")
hw/bench.py:141:    ap.add_argument("--out-dir", default="reports/bench")
hw/bench.py:152:    w = subprocess.run([a.lc0, "backendbench", *lc0_args(a), "--batches=5",
hw/bench.py:165:    if not a.skip_backendbench:
hw/bench.py:166:        cmd = [a.lc0, "backendbench", *lc0_args(a), f"--batches={a.batches}",
hw/bench.py:170:        res["backendbench"] = {"rows": parse_backendbench(p.stdout + p.stderr), "energy": e}
hw/bench.py:171:        for r in res["backendbench"]["rows"]:
hw/bench.py:176:        b = search_bench(a.lc0, a.weights, a.backend, a.backend_opts, a.movetime, a.positions,
#!/usr/bin/env python3
"""One entry point for the whole pipeline. Works the same on Windows and Linux.

    python ladder.py <step> [--config config.json] [step options]

Steps, in order (each is resumable / skips work already done):
  tbset     build the Syzygy test set                              (CPU, once)
  calib     calibration + dev planes in lc0's exact encoding          (CPU, once)
  export    BT3 -> models/bt3_fp32.onnx -> models/fp16.pb.gz        (needs lc0)
  day1      gate C1 checks: wrapped FP16 == native lc0, INT8 loads, INT8 kernels
  select    dev-split grid for step 3 method and step 4 alpha       (ONNX Runtime)
  build     the ladder s1..s4 (+ s4aa, s0, s1sp, swaps), wrapped for lc0
  study     Studies A + B (overnight)                               (GPU)
  studyc    Study C fixed time per move                             (GPU)
  score     reports/scores_<split>.md (+ hard subset)
  match     time-parity match fp16 vs best                          (GPU, overnight)
  hw        bench + J/node, batch sweep, trtexec layer builds, roofline, peaks (GPU)

See README.md for the schedule and what each gate needs.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable

DEFAULT = {
    "lc0": "lc0",
    "lc0_py": None,
    "trtexec": "trtexec",
    "nsys": "nsys",
    "bt3": "nets/BT3.pb.gz",
    "syzygy": None,
    "work": ".",
    "backend": "onnx-trt",
    "fp16_opts": "optimize=6",
    "int8_opts": "optimize=8",
    "native_backend": "onnx-trt",
    "native_opts": "optimize=6",
    "tbset": {"per_class": 400, "classes": None},
    "calib": {"random_games": 256, "n_tb": 256},
    "recipe": {"s3_method": "percentile", "s3_percentile": 99.99, "s4_alpha": 0.5},
    "best": "s4",
    "study": {"split": "test", "limit": 0, "budgets": "0,100,400,800,1600",
              "threads": 1, "minibatch": 256,
              "models": "fp16,s1,s2,s3,s4,s4aa"},
    "extras": {"s0_in_study_b": False, "swap": True, "s1sp": True},
    "studyc": {"movetimes": "200,800", "models": "fp16,BEST", "limit": 0},
    "match": {"tc": "10+0.1", "pairs": 250},
    "hw": {"batch_sizes": "32,64,128,256", "bench_movetime": 10000},
}


# ------------------------------------------------------------------ config
def load_config(path):
    cfg = json.loads(json.dumps(DEFAULT))
    if path and Path(path).exists():
        user = json.loads(Path(path).read_text())
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    elif path:
        sys.exit(f"config {path} not found (copy config.example.json)")
    w = Path(cfg["work"]).resolve()
    cfg["_w"] = w
    for d in ("models", "data", "results", "reports", "reports/logs"):
        (w / d).mkdir(parents=True, exist_ok=True)
    return cfg


def P(cfg, *parts):
    return str(cfg["_w"].joinpath(*parts))


def run(cmd, log=None, check=True):
    cmd = [str(c) for c in cmd]
    print("$ " + " ".join(cmd), flush=True)
    t0 = time.time()
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"\n$ {' '.join(cmd)}\n")
            f.flush()
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                sys.stdout.write(line)
                f.write(line)
            p.wait()
            rc = p.returncode
    else:
        rc = subprocess.call(cmd)
    if check and rc != 0:
        sys.exit(f"step failed ({rc}) after {time.time() - t0:.0f}s: {' '.join(cmd)}")
    return rc


def script(*parts):
    return str(ROOT.joinpath(*parts))


# ------------------------------------------------------------------ models
def recipe_flags(cfg, name):
    r = cfg["recipe"]
    s3 = ["--granularity", "per-channel", "--method", r["s3_method"]]
    if r["s3_method"] == "percentile":
        s3 += ["--percentile", str(r["s3_percentile"])]
    s4 = s3 + ["--smoothquant", str(r["s4_alpha"])]
    table = {"s1": ["--granularity", "per-tensor", "--method", "minmax"],
             "s2": ["--granularity", "per-channel", "--method", "minmax"],
             "s3": s3, "s4": s4}
    if name in table:
        return table[name]
    best = table[cfg["best"]] if cfg["best"] in table else s4
    if name == "s4aa":
        return best + ["--act-act-matmul"]
    if name in ("s0", "s1sp"):
        return best
    raise KeyError(name)


def model_opts(cfg, name):
    return cfg["fp16_opts"] if name == "fp16" else cfg["int8_opts"]


def model_weights(cfg, name):
    if name == "native":
        return cfg["bt3"]
    return P(cfg, "models", f"{name}.pb.gz")


def resolve(cfg, names):
    out = []
    for n in names.split(","):
        n = n.strip()
        if n == "BEST":
            n = cfg["best"]
        if n and n not in out:
            out.append(n)
    return out


# ------------------------------------------------------------------ steps
def step_tbset(cfg, a):
    out = P(cfg, "data", "tbset.jsonl")
    if Path(out).exists() and not a.force:
        print(f"{out} exists (--force to rebuild)")
        return
    if not cfg["syzygy"]:
        sys.exit("set syzygy in the config")
    cmd = [PY, script("tb", "build_tbset.py"), "--syzygy", cfg["syzygy"], "--out", out,
           "--per-class", cfg["tbset"]["per_class"]]
    if cfg["tbset"]["classes"]:
        cmd += ["--classes", cfg["tbset"]["classes"]]
    run(cmd, P(cfg, "reports", "logs", "tbset.log"))


def step_calib(cfg, a):
    """Python port of lc0's encoder by default; lc0's bindings if lc0_py is set."""
    tb = P(cfg, "data", "tbset.jsonl")
    c = cfg["calib"]
    log = P(cfg, "reports", "logs", "calib.log")
    enc = ["--lc0-py", cfg["lc0_py"]] if cfg["lc0_py"] else ["--lc0", cfg["lc0"]]
    if not Path(P(cfg, "data", "calib.npz")).exists() or a.force:
        run([PY, script("quant", "make_calib.py"), *enc, "--weights", cfg["bt3"],
             "--random-games", c["random_games"], "--tbset", tb, "--tb-split", "calib",
             "--n-tb", c["n_tb"], "--out", P(cfg, "data", "calib.npz")], log)
    if not Path(P(cfg, "data", "dev.npz")).exists() or a.force:
        run([PY, script("quant", "make_calib.py"), *enc, "--weights", cfg["bt3"],
             "--tbset", tb, "--tb-split", "dev", "--n-tb", 0, "--out", P(cfg, "data", "dev.npz")], log)


def check_npz_format(cfg):
    import numpy as np
    import re
    r = subprocess.run([cfg["lc0"], "describenet", f"--weights={cfg['bt3']}"],
                       capture_output=True, text=True)
    m = re.search(r"Input:\s+(\S+)", r.stdout + r.stderr)
    names = {"INPUT_CLASSICAL_112_PLANE": 1, "INPUT_112_WITH_CASTLING_PLANE": 2,
             "INPUT_112_WITH_CANONICALIZATION": 3, "INPUT_112_WITH_CANONICALIZATION_HECTOPLIES": 4,
             "INPUT_112_WITH_CANONICALIZATION_HECTOPLIES_ARMAGEDDON": 132,
             "INPUT_112_WITH_CANONICALIZATION_V2": 5, "INPUT_112_WITH_CANONICALIZATION_V2_ARMAGEDDON": 133}
    want = names.get(m.group(1)) if m else None
    for f in ("calib.npz", "dev.npz"):
        p = Path(P(cfg, "data", f))
        if not p.exists():
            sys.exit(f"missing {p}: run `python ladder.py calib` first")
        got = int(np.load(p)["input_format"])
        if want is not None and got != want:
            sys.exit(f"{p} was made for input format {got}, BT3 uses {want} ({m.group(1)}). "
                     "Remake it with a net of BT3's input format.")
    print(f"calibration planes match BT3's input format ({m.group(1) if m else '?'})")


def step_export(cfg, a):
    onnx_path = P(cfg, "models", "bt3_fp32.onnx")
    log = P(cfg, "reports", "logs", "export.log")
    if not Path(onnx_path).exists() or a.force:
        run([cfg["lc0"], "describenet", f"--weights={cfg['bt3']}"], log)
        run([cfg["lc0"], "leela2onnx", f"--input={cfg['bt3']}", f"--output={onnx_path}"], log)
    if not Path(model_weights(cfg, "fp16")).exists() or a.force:
        run([PY, script("quant", "wrap.py"), "--lc0", cfg["lc0"], "--orig", cfg["bt3"],
             "--onnx", onnx_path, "--out", model_weights(cfg, "fp16")], log)


def study_cmd(cfg, name, budgets, split, limit, extra=()):
    s = cfg["study"]
    backend = cfg["native_backend"] if name == "native" else cfg["backend"]
    opts = cfg["native_opts"] if name == "native" else model_opts(cfg, name)
    return [PY, script("eval", "run_study.py"), "--lc0", cfg["lc0"], "--name", name,
            "--weights", model_weights(cfg, name), "--backend", backend, "--backend-opts", opts,
            "--tbset", P(cfg, "data", "tbset.jsonl"), "--split", split, "--limit", limit,
            "--budgets", budgets, "--threads", s["threads"], "--minibatch", s["minibatch"],
            "--out-dir", P(cfg, "results"), *extra]


def build_model(cfg, name, log, force=False):
    """Make models/<name>.onnx and models/<name>.pb.gz."""
    src = P(cfg, "models", "bt3_fp32.onnx")
    calib = P(cfg, "data", "calib.npz")
    onnx_out = P(cfg, "models", f"{name}.onnx")
    pb = model_weights(cfg, name)
    if Path(pb).exists() and not force:
        return
    if name in ("s0", "s1sp"):
        dense = P(cfg, "models", f"{name}_fp32.onnx")
        if not Path(dense).exists() or force:
            if name == "s0":
                run([PY, script("quant", "prune24.py"), "--onnx", src, "--out", dense], log)
            else:
                run([PY, script("quant", "sparsegpt24.py"), "--onnx", src, "--calib", calib,
                     "--out", dense], log)
        src = dense
    if name.startswith("swap_"):
        best = P(cfg, "models", f"{cfg['best']}.onnx")
        fp = P(cfg, "models", "bt3_fp32.onnx")
        pol, val = (best, fp) if name == "swap_pol8" else (fp, best)
        run([PY, script("quant", "stitch_swap.py"), "--policy", pol, "--value", val,
             "--out", onnx_out], log)
    else:
        cmd = [PY, script("quant", "quantize.py"), "--onnx", src, "--calib", calib,
               "--out", onnx_out, *recipe_flags(cfg, name)]
        if name == "s4":
            cmd += ["--outlier-report", P(cfg, "reports", "outliers.txt")]
        run(cmd, log)
    run([PY, script("quant", "wrap.py"), "--lc0", cfg["lc0"], "--orig", cfg["bt3"],
         "--onnx", onnx_out, "--out", pb], log)


def step_day1(cfg, a):
    """Gate C1 checks on a few hundred dev positions."""
    log = P(cfg, "reports", "logs", "day1.log")
    check_npz_format(cfg)
    step_export(cfg, a)
    build_model(cfg, "s2", log)
    n = a.limit or 200
    for name in ("native", "fp16", "s2"):
        run(study_cmd(cfg, name, "0", "dev", n), log)
    run([PY, script("eval", "score.py"), "--tbset", P(cfg, "data", "tbset.jsonl"),
         "--results", P(cfg, "results"), "--ref", "native", "--models", "native,fp16,s2",
         "--out", P(cfg, "reports", "day1"), "--split", "dev"], log)
    js = json.loads(Path(P(cfg, "reports", "day1", "scores_dev.json")).read_text())["models"]
    fp, s2 = js.get("fp16", {}).get("A", {}), js.get("s2", {}).get("A", {})
    print("\n=== day-1 summary ===")
    print(f"1. wrapped FP16 vs native lc0: KL {fp.get('kl', float('nan')):.2e}, top-1 "
          f"{fp.get('top1', float('nan')):.3f}  -> {'OK' if fp.get('top1', 0) > 0.97 else 'CHECK: wrapped path differs'}")
    print(f"2. lc0 runs the INT8 file: {'OK' if s2 else 'FAILED'} (KL vs native {s2.get('kl', float('nan')):.2e}, "
          f"top-1 {s2.get('top1', float('nan')):.3f})")
    for nm in ("native", "fp16", "s2"):
        mp = Path(P(cfg, "results", nm, "meta.json"))
        if mp.exists():
            w = json.loads(mp.read_text()).get("warnings", [])
            if w:
                print(f"   lc0 warnings for {nm}: {w[:3]}")
    nsys = shutil.which(cfg["nsys"])
    rep = P(cfg, "reports", "trt", "s2_lc0")
    Path(rep).parent.mkdir(parents=True, exist_ok=True)
    bench = [cfg["lc0"], "benchmark", f"--weights={model_weights(cfg, 's2')}",
             f"--backend={cfg['backend']}", f"--backend-opts={cfg['int8_opts']}",
             "--nodes=20000", "--num-positions=3"]
    if nsys:
        run([nsys, "profile", "-o", rep, "--force-overwrite", "true", *bench], log, check=False)
        run([nsys, "stats", "--report", "cuda_gpu_kern_sum", "--format", "csv", "-o", rep,
             rep + ".nsys-rep"], log, check=False)
        csvs = sorted(Path(rep).parent.glob(Path(rep).name + "*kern_sum*.csv"))
        if csvs:
            run([PY, script("hw", "trt_layers.py"), "kernels", "--csv", str(csvs[-1])], log, check=False)
            print("3. matmuls in INT8: see the 'GEMM-like kernel time by tag' line above "
                  "(most should be int8)")
    else:
        print("3. nsys not found. Run by hand:\n   nsys profile -o " + rep + " --force-overwrite true "
              + " ".join(bench) + f"\n   nsys stats --report cuda_gpu_kern_sum --format csv -o {rep} {rep}.nsys-rep"
              f"\n   python hw/trt_layers.py kernels --csv {rep}_cuda_gpu_kern_sum.csv")


def step_select(cfg, a):
    """Dev grid with ONNX Runtime: step 3 method and step 4 alpha."""
    log = P(cfg, "reports", "logs", "select.log")
    src = P(cfg, "models", "bt3_fp32.onnx")
    calib = P(cfg, "data", "calib.npz")
    d = Path(P(cfg, "models", "select"))
    d.mkdir(exist_ok=True)
    grid = {"s3_p999": ["--method", "percentile", "--percentile", "99.9"],
            "s3_p9999": ["--method", "percentile", "--percentile", "99.99"],
            "s3_p99999": ["--method", "percentile", "--percentile", "99.999"],
            "s3_entropy": ["--method", "entropy"]}
    for nm, fl in grid.items():
        if not (d / f"{nm}.onnx").exists():
            run([PY, script("quant", "quantize.py"), "--onnx", src, "--calib", calib,
                 "--out", str(d / f"{nm}.onnx"), "--granularity", "per-channel", *fl], log)
    run([PY, script("eval", "quick_compare.py"), "--ref", src, "--npz", P(cfg, "data", "dev.npz"),
         "--tbset", P(cfg, "data", "tbset.jsonl"), "--out", P(cfg, "reports", "select_s3_dev.txt"),
         *[str(d / f"{nm}.onnx") for nm in grid]], log)
    print("\nPick step 3 from the table above (lowest KL / highest tb_acc), set recipe.s3_method "
          "and s3_percentile in the config, then rerun `select --alpha` for step 4.")
    if a.alpha:
        r = cfg["recipe"]
        base = ["--granularity", "per-channel", "--method", r["s3_method"]]
        if r["s3_method"] == "percentile":
            base += ["--percentile", str(r["s3_percentile"])]
        files = []
        for al in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
            f = d / f"s4_a{al}.onnx"
            if not f.exists():
                run([PY, script("quant", "quantize.py"), "--onnx", src, "--calib", calib,
                     "--out", str(f), *base, "--smoothquant", str(al)], log)
            files.append(str(f))
        run([PY, script("eval", "quick_compare.py"), "--ref", src, "--npz", P(cfg, "data", "dev.npz"),
             "--tbset", P(cfg, "data", "tbset.jsonl"), "--out", P(cfg, "reports", "select_s4_dev.txt"),
             *files], log)
        print("\nSet recipe.s4_alpha in the config from the table above. If no alpha beats "
              "step 3, set best to s3.")


def step_build(cfg, a):
    log = P(cfg, "reports", "logs", "build.log")
    check_npz_format(cfg)
    step_export(cfg, a)
    names = ["s1", "s2", "s3", "s4", "s4aa", "s0"]
    if cfg["extras"]["s1sp"]:
        names.append("s1sp")
    if cfg["extras"]["swap"]:
        names += ["swap_pol8", "swap_val8"]
    if a.only:
        names = resolve(cfg, a.only)
    for n in names:
        build_model(cfg, n, log, force=a.force)
    onnxs = [P(cfg, "models", f"{n}.onnx") for n in names if not n.startswith("swap_")]
    run([PY, script("eval", "quick_compare.py"), "--ref", P(cfg, "models", "bt3_fp32.onnx"),
         "--npz", P(cfg, "data", "dev.npz"), "--tbset", P(cfg, "data", "tbset.jsonl"),
         "--out", P(cfg, "reports", "quick_compare_dev.txt"), *onnxs], log)


def step_study(cfg, a):
    s = cfg["study"]
    names = resolve(cfg, a.models or s["models"])
    log = P(cfg, "reports", "logs", "study.log")
    extras = []
    if cfg["extras"]["swap"] and not a.models:
        extras += ["swap_pol8", "swap_val8"]
    if cfg["extras"]["s1sp"] and not a.models:
        extras.append("s1sp")
    for n in names + extras:
        if n != "fp16" and not Path(model_weights(cfg, n)).exists():
            print(f"skipping {n}: {model_weights(cfg, n)} not built")
            continue
        run(study_cmd(cfg, n, s["budgets"], a.split or s["split"], a.limit if a.limit is not None else s["limit"]), log)
    # S0: Study A always; Study B only if switched on after looking at Study A
    if Path(model_weights(cfg, "s0")).exists() and not a.models:
        b = s["budgets"] if cfg["extras"]["s0_in_study_b"] else "0"
        run(study_cmd(cfg, "s0", b, a.split or s["split"], a.limit if a.limit is not None else s["limit"]), log)


def step_studyc(cfg, a):
    c = cfg["studyc"]
    log = P(cfg, "reports", "logs", "studyc.log")
    for n in resolve(cfg, a.models or c["models"]):
        cmd = study_cmd(cfg, n, "", a.split or cfg["study"]["split"],
                        a.limit if a.limit is not None else c["limit"])
        # Study C uses lc0's default Threads, not the fixed-node setting
        i = cmd.index("--threads")
        cmd[i + 1] = 0
        run(cmd + ["--movetimes", c["movetimes"]], log)


def step_score(cfg, a):
    names = resolve(cfg, a.models or ",".join(
        [cfg["study"]["models"], "s0", "s1sp", "swap_pol8", "swap_val8"]))
    names = [n for n in names if Path(P(cfg, "results", n)).exists()]
    run([PY, script("eval", "score.py"), "--tbset", P(cfg, "data", "tbset.jsonl"),
         "--results", P(cfg, "results"), "--ref", "fp16", "--models", ",".join(names),
         "--out", P(cfg, "reports"), "--split", a.split or cfg["study"]["split"]])


def step_match(cfg, a):
    m = cfg["match"]
    best = cfg["best"]
    cmd = [PY, script("eval", "match.py"), "--lc0", cfg["lc0"], "--name", f"fp16_vs_{best}",
           "--a", f"fp16={model_weights(cfg, 'fp16')}:{cfg['fp16_opts']}",
           "--b", f"{best}={model_weights(cfg, best)}:{cfg['int8_opts']}",
           "--backend", cfg["backend"], "--tc", m["tc"], "--pairs", m["pairs"],
           "--out-dir", P(cfg, "results")]
    if cfg["syzygy"]:
        cmd += ["--syzygy", cfg["syzygy"]]
    if a.estimate:
        cmd += ["--estimate", a.estimate]
    run(cmd, P(cfg, "reports", "logs", "match.log"))


def step_hw(cfg, a):
    h = cfg["hw"]
    log = P(cfg, "reports", "logs", "hw.log")
    best = cfg["best"]
    parts = a.parts.split(",") if a.parts else ["bench", "sweep", "trt", "roofline"]
    if "bench" in parts:
        for n in ("fp16", best, "native"):
            backend = cfg["native_backend"] if n == "native" else cfg["backend"]
            opts = cfg["native_opts"] if n == "native" else model_opts(cfg, n)
            run([PY, script("hw", "bench.py"), "--lc0", cfg["lc0"], "--weights", model_weights(cfg, n),
                 "--name", n, "--backend", backend, "--backend-opts", opts,
                 "--movetime", h["bench_movetime"], "--out-dir", P(cfg, "reports", "bench")], log)
    if "sweep" in parts:
        run([PY, script("hw", "batch_sweep.py"), "--lc0", cfg["lc0"], "--backend", cfg["backend"],
             "--sizes", h["batch_sizes"],
             "--model", f"fp16={model_weights(cfg, 'fp16')}:{cfg['fp16_opts']}",
             "--model", f"{best}={model_weights(cfg, best)}:{cfg['int8_opts']}",
             "--out", P(cfg, "reports", "batch_sweep")], log)
    trt = Path(P(cfg, "reports", "trt"))
    trt.mkdir(parents=True, exist_ok=True)
    builds = [("fp16", P(cfg, "models", "bt3_fp32.onnx"), [], ), (best, P(cfg, "models", f"{best}.onnx"), ["--int8"])]
    for sp in ("s0", "s1sp"):
        if Path(P(cfg, "models", f"{sp}.onnx")).exists():
            builds.append((f"{sp}_sparse", P(cfg, "models", f"{sp}.onnx"), ["--int8", "--sparsity"]))
            builds.append((f"{sp}_dense", P(cfg, "models", f"{sp}.onnx"), ["--int8"]))
    if "trt" in parts:
        for tag, onnx_path, fl in builds:
            run([PY, script("hw", "trt_layers.py"), "build", "--trtexec", cfg["trtexec"],
                 "--onnx", onnx_path, "--out", str(trt / tag), *fl], log, check=False)
        run([PY, script("hw", "roofline.py"), "peak", "--trtexec", cfg["trtexec"],
             "--out", str(trt / "peak.json")], log, check=False)
    if "roofline" in parts:
        for tag, onnx_path, _ in builds[:2]:
            if Path(f"{trt / tag}_layers.json").exists():
                run([PY, script("hw", "roofline.py"), "layers", "--onnx", onnx_path,
                     "--prefix", str(trt / tag), "--peaks", str(trt / "peak.json"),
                     "--out", P(cfg, "reports", "roofline", tag)], log, check=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["tbset", "calib", "export", "day1", "select", "build", "study",
                                     "studyc", "score", "match", "hw"])
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default=None, help="build: comma list of models")
    ap.add_argument("--models", default=None, help="study/studyc/score: comma list (BEST = config best)")
    ap.add_argument("--split", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--alpha", action="store_true", help="select: also run the step-4 alpha grid")
    ap.add_argument("--estimate", type=int, default=0, help="match: time N games and extrapolate")
    ap.add_argument("--parts", default=None, help="hw: bench,sweep,trt,roofline")
    a = ap.parse_args()
    cfg = load_config(a.config)
    os.chdir(cfg["_w"])
    globals()[f"step_{a.step}"](cfg, a)


if __name__ == "__main__":
    main()
~~~
Produced: LOG.md inspection entry only.

## 2026-10-28 00:14:23 +05:30 — GPU, power and pre-flight inspection
Exact command: nvidia-smi; Get-Content hw/trt_layers.py; Get-Content hw/bench.py; Get-Content eval/run_study.py; rg --files -g *AGENTS.md -g *preflight* -g *flight* -g *STATUS*; Get-ChildItem reports/trt/s2_lc0_cuda_gpu_kern_sum.csv; Get-CimInstance Win32_Battery | Select-Object BatteryStatus,EstimatedChargeRemaining; Get-PSDrive C
Exit code: 0
Output:
~~~
Wed Oct 28 00:14:22 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   42C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
#!/usr/bin/env python3
"""Do the matmuls really run in INT8 (and sparse)? Two independent checks.

1. build: run trtexec on an ONNX with lc0's settings (FP16 [+INT8], builder
   optimization level 5, the same dynamic batch profile lc0 uses), export
   per-layer info and a per-layer profile, and summarise which GEMM/conv
   layers run in which precision and how much of the time they take.
       python hw/trt_layers.py build --trtexec trtexec --onnx models/s4.onnx --int8 --out reports/trt/s4
       python hw/trt_layers.py build ... --sparsity     # S0/S1 speed ceiling
2. kernels: what lc0 actually ran, from an Nsight Systems capture:
       nsys profile -o reports/trt/s4_lc0 --force-overwrite true lc0 benchmark --weights=models/s4.pb.gz --backend=onnx-trt --backend-opts=optimize=8 --nodes=20000 --num-positions=3
       nsys stats --report cuda_gpu_kern_sum --format csv -o reports/trt/s4_lc0 reports/trt/s4_lc0.nsys-rep
       python hw/trt_layers.py kernels --csv reports/trt/s4_lc0_cuda_gpu_kern_sum.csv
   Kernel names are classified by the precision tokens TensorRT/cuBLAS put
   in them (i8/imma/int8, h/hmma/f16, bf16, sparse). Read the top names
   yourself too: the classifier is a heuristic.

lc0's onnx-trt maps optimize>=6 to fp16, >=7 to bf16 (only when lc0 was
built against onnxruntime >= 1.23), >=8 to int8 (trap 4). The Windows
v0.33.0-rc0 package bundles onnxruntime 1.22.1, so optimize=8 there means
FP16 + INT8, no BF16; `build` mirrors that unless --bf16.
"""
import argparse
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

INPUT = "/input/planes"
GEMM_TYPES = re.compile(r"gemm|matrix|matmul|conv|fully|cask", re.I)


def classify_text(s):
    """Primary precision of a kernel/tactic name (int8 > bf16 > fp16 > fp32,
    since e.g. `gemm_i8f16_i8i32` has int8 operands and an fp16 output),
    plus 'sparse' when the name says so."""
    s = s.lower()
    tags = set()
    if re.search(r"int8|i8|imma|s8|qgemm", s):
        tags.add("int8")
    elif re.search(r"bf16|bfloat", s):
        tags.add("bf16")
    elif re.search(r"fp16|f16|half|hmma|h16|_h_", s):
        tags.add("fp16")
    elif re.search(r"fp32|f32|float|sgemm|tf32", s):
        tags.add("fp32")
    if re.search(r"sparse|_sp_|sptensor|spmma", s):
        tags.add("sparse")
    return tags


def layer_precision(layer):
    """Precision of a layer from its I/O formats, else its tactic name."""
    fmts = []
    for io in layer.get("Inputs", []) + layer.get("Outputs", []):
        f = io.get("Format/Datatype") or io.get("Format") or io.get("Datatype") or ""
        fmts.append(f)
    ins = [(io.get("Format/Datatype") or "") for io in layer.get("Inputs", [])]
    if any(re.search(r"int8", f, re.I) for f in ins):
        p = "int8"
    elif any(re.search(r"bf16|bfloat", f, re.I) for f in ins):
        p = "bf16"
    elif any(re.search(r"half|fp16", f, re.I) for f in ins):
        p = "fp16"
    elif any(re.search(r"float|fp32", f, re.I) for f in ins):
        p = "fp32"
    else:
        t = classify_text(str(layer.get("TacticName", "")) + " " + str(layer.get("Name", "")))
        p = next((x for x in ("int8", "bf16", "fp16", "fp32") if x in t), "?")
    sparse = "sparse" in classify_text(str(layer.get("TacticName", "")))
    return p, sparse


def load_profile(path):
    if not path or not Path(path).exists():
        return {}
    d = json.loads(Path(path).read_text())
    out = {}
    for r in d:
        if isinstance(r, dict) and "name" in r:
            out[r["name"]] = float(r.get("averageMs", r.get("timeMs", 0)))
    return out


def summarize_layers(info_path, profile_path=None):
    info = json.loads(Path(info_path).read_text())
    layers = info.get("Layers", info if isinstance(info, list) else [])
    if layers and isinstance(layers[0], str):
        raise SystemExit("layer info has names only: rebuild with --profilingVerbosity=detailed")
    prof = load_profile(profile_path)
    tot = defaultdict(float)
    rows = []
    for L in layers:
        name = L.get("Name", "?")
        ltype = str(L.get("LayerType", L.get("ParameterType", "")))
        p, sp = layer_precision(L)
        ms = prof.get(name, 0.0)
        is_gemm = bool(GEMM_TYPES.search(ltype)) or "ForeignNode" in name
        rows.append({"name": name, "type": ltype, "precision": p, "sparse": sp,
                     "ms": ms, "gemm": is_gemm, "tactic": L.get("TacticName", "")})
        tot["all"] += ms
        if is_gemm:
            tot["gemm"] += ms
            tot[f"gemm_{p}"] += ms
            if sp:
                tot["gemm_sparse"] += ms
    return rows, dict(tot)


def report_layers(rows, tot, out):
    g = [r for r in rows if r["gemm"]]
    cnt = defaultdict(int)
    for r in g:
        cnt[r["precision"] + ("+sparse" if r["sparse"] else "")] += 1
    lines = ["# TensorRT layer precision", "",
             f"GEMM/conv-like layers: {len(g)} of {len(rows)} engine layers",
             "count by precision: " + ", ".join(f"{k}={v}" for k, v in sorted(cnt.items()))]
    if tot.get("all"):
        lines.append(f"time: all {tot['all']:.3f} ms, gemm-like {tot.get('gemm', 0):.3f} ms; "
                     + ", ".join(f"{k[5:]} {100 * v / max(tot.get('gemm', 1e-9), 1e-9):.1f}%"
                                 for k, v in sorted(tot.items()) if k.startswith("gemm_")))
    foreign = [r for r in rows if "ForeignNode" in r["name"]]
    if foreign:
        lines.append(f"\n{len(foreign)} Myelin ForeignNode layer(s): fused regions whose "
                     "per-op precision is not visible here; use `kernels` on an nsys capture.")
    lines += ["", "| ms | precision | sparse | type | layer |", "|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: -r["ms"])[:60]:
        nm = r["name"] if len(r["name"]) < 110 else r["name"][:107] + "..."
        lines.append(f"| {r['ms']:.4f} | {r['precision']} | {'y' if r['sparse'] else ''} | "
                     f"{r['type']} | `{nm}` |")
    Path(out).write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:6]))


def cmd_build(a):
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shp = lambda b: f"{INPUT}:{b}x112x8x8"  # noqa: E731
    args = [a.trtexec, f"--onnx={a.onnx}", "--fp16",
            f"--builderOptimizationLevel={a.opt_level}",
            f"--minShapes={shp(a.min_batch)}", f"--optShapes={shp(a.opt_batch)}",
            f"--maxShapes={shp(a.max_batch)}", f"--shapes={shp(a.batch)}",
            "--profilingVerbosity=detailed",
            f"--exportLayerInfo={out}_layers.json", f"--exportProfile={out}_profile.json",
            f"--exportTimes={out}_times.json", "--separateProfileRun",
            f"--saveEngine={out}.engine", f"--timingCacheFile={out.parent / 'timing.cache'}",
            "--useCudaGraph", "--noDataTransfers"]
    if a.int8:
        args.append("--int8")
    if a.bf16:
        args.append("--bf16")
    if a.sparsity:
        args.append("--sparsity=enable")
    if a.layer_norm_fp32:
        # lc0 sets trt_layer_norm_fp32_fallback=1; trtexec has no direct switch.
        args.append("--layerPrecisions=*/ln*:fp32")
        args.append("--precisionConstraints=prefer")
    print(" ".join(args), file=sys.stderr)
    log = Path(f"{out}_trtexec.log")
    with open(log, "w") as f:
        r = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT)
    txt = log.read_text(errors="replace")
    m = re.search(r"Throughput:\s*([\d.]+)\s*qps", txt)
    lat = re.search(r"GPU Compute Time: min = [\d.]+ ms, max = [\d.]+ ms, mean = ([\d.]+) ms", txt)
    summ = {"onnx": a.onnx, "int8": a.int8, "sparsity": a.sparsity, "batch": a.batch,
            "returncode": r.returncode,
            "qps": float(m.group(1)) if m else None,
            "gpu_ms_mean": float(lat.group(1)) if lat else None}
    if summ["qps"]:
        summ["positions_per_s"] = summ["qps"] * a.batch
    if a.sparsity:
        summ["sparse_layers_reported"] = len(re.findall(r"[Ss]parsity.*?(?:eligible|enabled)", txt))
    Path(f"{out}_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ), file=sys.stderr)
    if r.returncode != 0:
        sys.exit(f"trtexec failed; see {log}")
    rows, tot = summarize_layers(f"{out}_layers.json", f"{out}_profile.json")
    report_layers(rows, tot, f"{out}_layers.md")


def cmd_layers(a):
    rows, tot = summarize_layers(a.info, a.profile)
    report_layers(rows, tot, a.out)


def cmd_kernels(a):
    rows = []
    with open(a.csv, newline="", encoding="utf-8", errors="replace") as f:
        txt = f.read()
    # nsys stats may print a header before the CSV
    i = txt.find('"Time')
    i = i if i >= 0 else txt.find("Time")
    rd = csv.DictReader(txt[i:].splitlines())
    for r in rd:
        name = r.get("Name") or r.get("Kernel Name") or ""
        t = r.get("Total Time (ns)") or r.get("Total Time") or "0"
        try:
            ns = float(str(t).replace(",", ""))
        except ValueError:
            continue
        rows.append((ns, name, classify_text(name), int(float(str(r.get("Instances", "0")).replace(",", "") or 0))))
    tot = sum(r[0] for r in rows) or 1
    by = defaultdict(float)
    gemm_by = defaultdict(float)
    for ns, name, tags, _ in rows:
        key = "+".join(sorted(tags)) or "other"
        by[key] += ns
        if re.search(r"gemm|mma|conv|xmma|cutlass|matmul", name, re.I):
            gemm_by[key] += ns
    gt = sum(gemm_by.values()) or 1
    lines = [f"# GPU kernels in {a.csv}", "",
             "all kernel time by tag: " + ", ".join(f"{k} {100 * v / tot:.1f}%" for k, v in sorted(by.items(), key=lambda kv: -kv[1])),
             "GEMM-like kernel time by tag: " + ", ".join(f"{k} {100 * v / gt:.1f}%" for k, v in sorted(gemm_by.items(), key=lambda kv: -kv[1])),
             "", "| % time | instances | tags | kernel |", "|---|---|---|---|"]
    for ns, name, tags, n in sorted(rows, reverse=True)[:40]:
        nm = name if len(name) < 120 else name[:117] + "..."
        lines.append(f"| {100 * ns / tot:.2f} | {n} | {'+'.join(sorted(tags))} | `{nm}` |")
    out = a.out or str(Path(a.csv).with_suffix(".md"))
    Path(out).write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:4]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--trtexec", default="trtexec")
    b.add_argument("--onnx", required=True)
    b.add_argument("--out", required=True, help="path prefix for outputs")
    b.add_argument("--int8", action="store_true")
    b.add_argument("--bf16", action="store_true")
    b.add_argument("--sparsity", action="store_true")
    b.add_argument("--layer-norm-fp32", action="store_true",
                   help="try to mimic lc0's trt_layer_norm_fp32_fallback (layer-name glob "
                        "support in --layerPrecisions varies by TensorRT version)")
    b.add_argument("--opt-level", type=int, default=5)
    b.add_argument("--batch", type=int, default=256)
    b.add_argument("--min-batch", type=int, default=4)
    b.add_argument("--opt-batch", type=int, default=256, help="lc0 uses max_batch/4 = 256")
    b.add_argument("--max-batch", type=int, default=1024)
    l = sub.add_parser("layers", help="summarise existing trtexec exports")
    l.add_argument("--info", required=True)
    l.add_argument("--profile", default=None)
    l.add_argument("--out", required=True)
    k = sub.add_parser("kernels")
    k.add_argument("--csv", required=True)
    k.add_argument("--out", default=None)
    a = ap.parse_args()
    {"build": cmd_build, "layers": cmd_layers, "kernels": cmd_kernels}[a.cmd](a)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Throughput and energy for one model: `lc0 backendbench` (raw NN nps per
batch size) and timed UCI searches (search nps), with GPU energy from NVML
(CPU energy from RAPL on Linux) above idle, and clocks/temperature logged.

J/node = energy above idle during the searches ÷ nodes searched. Only the
searches are metered (engine load and TensorRT engine build are not).

Trap 11: `lc0 benchmark`'s built-in positions include FENs with a nonzero
halfmove clock, which crash lc0 v0.33 with V2 canonical nets (segfault on
position 4; same root cause as trap 5). So search speed is measured here
over UCI on SEARCH_FENS, a fixed list with halfmove clock 0.

    python hw/bench.py --lc0 lc0 --weights models/fp16.pb.gz --backend-opts optimize=6 --name fp16
    python hw/bench.py --lc0 lc0 --weights nets/BT3.pb.gz --backend cuda-fp16 --name native_cuda

Lock clocks first if you can (`nvidia-smi -lgc 1500,1500`, admin); laptops
and some desktop drivers refuse, so the SM clock is always logged instead.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
from energy import Meter, describe_env, idle_power, run_metered  # noqa: E402

# Openings, middlegames and endgames (Stockfish bench positions), halfmove 0.
SEARCH_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 11",
    "4rrk1/pp1n3p/3q2pQ/2p1pb2/2PP4/2P3N1/P2B2PP/4RRK1 b - - 0 19",
    "rq3rk1/ppp2ppp/1bnpb3/3N2B1/3NP3/7P/PPPQ1PP1/2KR3R w - - 0 14",
    "r1bq1r1k/1pp1n1pp/1p1p4/4p2Q/4Pp2/1BNP4/PPP2PPP/3R1RK1 w - - 0 14",
    "r3r1k1/2p2ppp/p1p1bn2/8/1q2P3/2NPQN2/PPP3PP/R4RK1 b - - 0 15",
    "r1bbk1nr/pp3p1p/2n5/1N4p1/2Np1B2/8/PPP2PPP/2KR1B1R w kq - 0 13",
    "r1bq1rk1/ppp1nppp/4n3/3p3Q/3P4/1BP1B3/PP1N2PP/R4RK1 w - - 0 16",
    "4r1k1/r1q2ppp/ppp2n2/4P3/5Rb1/1N1BQ3/PPP3PP/R5K1 w - - 0 17",
    "2rqkb1r/ppp2p2/2npb1p1/1N1Nn2p/2P1PP2/8/PP2B1PP/R1BQK2R b KQ - 0 11",
    "r1bq1r1k/b1p1npp1/p2p3p/1p6/3PP3/1B2NN2/PP3PPP/R2Q1RK1 w - - 0 16",
]


def search_bench(lc0, weights, backend, backend_opts, movetime, positions, idle=None,
                 threads=0, minibatch=0, log=None, name="bench"):
    """Timed `go movetime` searches over SEARCH_FENS[:positions]; energy is
    metered around the searches only. Returns a dict."""
    from lc0uci import Lc0
    opts = {"MoveOverheadMs": 20}
    if threads:
        opts["Threads"] = threads
    if minibatch:
        opts["MinibatchSize"] = minibatch
    e = Lc0(lc0, weights, backend=backend, backend_opts=backend_opts, options=opts,
            log=log, name=name)
    fens = SEARCH_FENS[:positions] if positions <= len(SEARCH_FENS) else \
        [SEARCH_FENS[i % len(SEARCH_FENS)] for i in range(positions)]
    try:
        e.go(fen=fens[0], movetime=min(movetime, 2000))  # warm-up, clocks up
        nodes, lc0_ms = 0, 0
        with Meter() as m:
            for f in fens:
                e.newgame()
                r = e.go(fen=f, movetime=movetime)
                nodes += r.get("nodes") or 0
                lc0_ms += r.get("time_ms") or 0
    finally:
        e.quit()
    en = dict(m.result)
    if idle:
        if "gpu_j" in en and "gpu_w" in idle:
            en["gpu_j_above_idle"] = en["gpu_j"] - idle["gpu_w"] * en["seconds"]
        if "cpu_j" in en and "cpu_w" in idle:
            en["cpu_j_above_idle"] = en["cpu_j"] - idle["cpu_w"] * en["seconds"]
    out = {"nodes": nodes, "time_ms": lc0_ms, "positions": len(fens), "movetime": movetime,
           "nps": round(1000 * nodes / lc0_ms) if lc0_ms else None, "energy": en,
           "warnings": e.warnings}
    if nodes and "gpu_j_above_idle" in en:
        out["gpu_j_per_node"] = en["gpu_j_above_idle"] / nodes
        out["gpu_j_per_node_total"] = en["gpu_j"] / nodes
    if nodes and "cpu_j_above_idle" in en:
        out["cpu_j_per_node"] = en["cpu_j_above_idle"] / nodes
    return out


def lc0_args(a):
    args = [f"--weights={a.weights}", f"--backend={a.backend}"]
    if a.backend_opts:
        args.append(f"--backend-opts={a.backend_opts}")
    return args


def parse_backendbench(txt):
    rows = []
    for line in txt.splitlines():
        m = re.match(r"\s*(\d+),\s*([\d.]+),\s*([\d.]+),", line)
        if m:
            rows.append({"batch": int(m.group(1)), "nps": float(m.group(2)),
                         "ms": float(m.group(3))})
    return rows


def parse_benchmark(txt):
    out = {}
    for key, pat in (("time_ms", r"Total time \(ms\)\s*:\s*(\d+)"),
                     ("nodes", r"Nodes searched\s*:\s*(\d+)"),
                     ("nps", r"Nodes/second\s*:\s*(\d+)")):
        m = re.search(pat, txt)
        if m:
            out[key] = int(m.group(1))
    return out


def warn_lines(txt):
    return [l for l in txt.splitlines() if re.search(r"warn|fp32|fall ?back", l, re.I)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lc0", default="lc0")
    ap.add_argument("--weights", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--backend", default="onnx-trt")
    ap.add_argument("--backend-opts", default="")
    ap.add_argument("--idle-seconds", type=float, default=10)
    ap.add_argument("--batches", type=int, default=200, help="backendbench batches per size")
    ap.add_argument("--start-batch", type=int, default=32)
    ap.add_argument("--max-batch", type=int, default=512)
    ap.add_argument("--batch-step", type=int, default=32)
    ap.add_argument("--movetime", type=int, default=10000, help="search ms per position")
    ap.add_argument("--positions", type=int, default=10)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--minibatch", type=int, default=0)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--skip-backendbench", action="store_true")
    ap.add_argument("--out-dir", default="reports/bench")
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    res = {"name": a.name, "weights": a.weights, "backend": a.backend,
           "backend_opts": a.backend_opts, "env": describe_env(),
           "time": time.strftime("%Y-%m-%d %H:%M:%S")}

    # Warm-up: builds / loads the TensorRT engine so it is not timed.
    print(f"[{a.name}] warm-up (TensorRT engine build on first use can take minutes)",
          file=sys.stderr)
    w = subprocess.run([a.lc0, "backendbench", *lc0_args(a), "--batches=5",
                        "--start-batch-size=64", "--max-batch-size=64"],
                       capture_output=True, text=True)
    res["warnings"] = warn_lines(w.stdout + w.stderr)
    for l in res["warnings"]:
        print(f"[{a.name}] {l}", file=sys.stderr)
    if w.returncode != 0:
        sys.exit(f"lc0 failed:\n{w.stdout[-3000:]}\n{w.stderr[-3000:]}")

    time.sleep(3)
    res["idle"] = idle_power(a.idle_seconds)
    print(f"[{a.name}] idle {res['idle']}", file=sys.stderr)

    if not a.skip_backendbench:
        cmd = [a.lc0, "backendbench", *lc0_args(a), f"--batches={a.batches}",
               f"--start-batch-size={a.start_batch}", f"--max-batch-size={a.max_batch}",
               f"--batch-step={a.batch_step}"]
        p, e = run_metered(cmd, res["idle"])
        res["backendbench"] = {"rows": parse_backendbench(p.stdout + p.stderr), "energy": e}
        for r in res["backendbench"]["rows"]:
            print(f"  batch {r['batch']:5d}  {r['nps']:10.0f} nps", file=sys.stderr)

    runs = []
    for k in range(a.repeat):
        b = search_bench(a.lc0, a.weights, a.backend, a.backend_opts, a.movetime, a.positions,
                         res["idle"], a.threads, a.minibatch,
                         log=str(out / f"{a.name}.lc0.log"), name=a.name)
        e = b["energy"]
        runs.append(b)
        print(f"  search run {k + 1}: {b.get('nps')} nps, {b.get('nodes')} nodes, "
              f"GPU {b.get('gpu_j_per_node', float('nan')) * 1e3:.3f} mJ/node above idle, "
              f"SM {e.get('sm_mhz_mean', 0):.0f} MHz (min {e.get('sm_mhz_min', 0)}), "
              f"{e.get('temp_c_max', 0)} C max", file=sys.stderr)
    res["search"] = runs
    path = out / f"{a.name}.json"
    path.write_text(json.dumps(res, indent=1))
    print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Studies A, B and C on the tablebase set, through stock lc0 over UCI.

  A  (budget 0)       raw network: `go nodes 1`, PolicyTemperature=1, P of
                      every legal move + raw V/WL/D of the root.
  B  (--budgets)      fixed node budgets, SmartPruningFactor=0 so the search
                      really spends the budget. Actual nodes are recorded
                      (trap 6: `go nodes N` overshoots by up to a minibatch).
  C  (--movetimes)    fixed time per move with the engine's normal settings
                      (smart pruning on). A fresh engine per movetime so NN
                      cache entries from one pass cannot speed up the next.

Resumable: each (position, budget) is one jsonl line, finished ones are
skipped. --shard i/n splits the positions for parallel machines.

    python eval/run_study.py --name fp16 --weights models/fp16.pb.gz --backend-opts optimize=6 \
        --tbset data/tbset.jsonl --split test --budgets 0,100,400,800,1600
    python eval/run_study.py --name s4 --weights models/s4.pb.gz --backend-opts optimize=8 \
        --tbset data/tbset.jsonl --split test --movetimes 200,800 --threads 0
"""
import argparse
import json
import platform
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import append_jsonl, read_jsonl, write_json  # noqa: E402
from lc0uci import Lc0  # noqa: E402


def positions(a):
    recs = [r for r in read_jsonl(a.tbset) if r["split"] == a.split]
    recs.sort(key=lambda r: r["id"])
    if a.classes:
        keep = set(a.classes.split(","))
        recs = [r for r in recs if r["cls"] in keep]
    if a.ids:
        keep = {int(x) for x in Path(a.ids).read_text().split()}
        recs = [r for r in recs if r["id"] in keep]
    if a.limit:
        # spread the limit over classes instead of taking the first classes
        by = {}
        for r in recs:
            by.setdefault(r["cls"], []).append(r)
        out, i = [], 0
        while len(out) < a.limit and any(by.values()):
            for c in list(by):
                if by[c]:
                    out.append(by[c].pop(0))
                    if len(out) >= a.limit:
                        break
            i += 1
        recs = sorted(out, key=lambda r: r["id"])
    if a.shard:
        i, n = (int(x) for x in a.shard.split("/"))
        recs = [r for k, r in enumerate(recs) if k % n == i]
    return recs


def make_engine(a, log_dir, tag, study):
    opts = {"VerboseMoveStats": True, "MinibatchSize": a.minibatch}
    if a.nncache is not None:
        opts["NNCacheSize"] = a.nncache
    if study in ("A", "B"):
        opts["Threads"] = a.threads if a.threads else 1
    elif a.threads:
        opts["Threads"] = a.threads
    if study == "A":
        opts["PolicyTemperature"] = 1.0
    if study == "B":
        opts["SmartPruningFactor"] = 0
    if study == "C":
        # Trap 8: lc0 subtracts MoveOverheadMs (default 200 ms) from every
        # movetime, so `go movetime 200` would search for ~0 ms.
        opts["MoveOverheadMs"] = a.move_overhead
    for kv in a.option or []:
        k, v = kv.split("=", 1)
        opts[k] = v
    return Lc0(a.lc0, a.weights, backend=a.backend, backend_opts=a.backend_opts,
               options=opts, log=str(log_dir / f"{tag}.lc0.log"), name=f"{a.name}:{tag}")


class Progress:
    def __init__(self, total, label):
        self.total, self.label, self.t0, self.n = total, label, time.time(), 0

    def tick(self):
        self.n += 1
        if self.n % 25 == 0 or self.n == self.total:
            el = time.time() - self.t0
            eta = el / self.n * (self.total - self.n)
            print(f"  [{self.label}] {self.n}/{self.total}  {el / self.n:.2f}s/item  "
                  f"eta {eta / 60:.1f} min", file=sys.stderr, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lc0", default="lc0")
    ap.add_argument("--weights", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--backend", default="onnx-trt")
    ap.add_argument("--backend-opts", default="")
    ap.add_argument("--threads", type=int, default=0,
                    help="0: 1 for studies A/B, lc0's default for C")
    ap.add_argument("--minibatch", type=int, default=256)
    ap.add_argument("--nncache", type=int, default=None)
    ap.add_argument("--option", action="append", help="extra UCI option Name=Value")
    ap.add_argument("--tbset", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--classes", default=None)
    ap.add_argument("--ids", default=None, help="file of position ids to run")
    ap.add_argument("--shard", default=None, help="i/n")
    ap.add_argument("--budgets", default="", help="e.g. 0,100,400,800,1600 (0 = Study A)")
    ap.add_argument("--movetimes", default="", help="ms per move, e.g. 200,800 (Study C)")
    ap.add_argument("--move-overhead", type=int, default=20,
                    help="MoveOverheadMs for Study C (lc0 default 200 eats short movetimes)")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args()

    out = Path(a.out_dir) / a.name
    out.mkdir(parents=True, exist_ok=True)
    recs = positions(a)
    budgets = [int(x) for x in a.budgets.split(",") if x != ""]
    movetimes = [int(x) for x in a.movetimes.split(",") if x != ""]
    meta = {"name": a.name, "weights": a.weights, "backend": a.backend,
            "backend_opts": a.backend_opts, "threads": a.threads, "minibatch": a.minibatch,
            "split": a.split, "n_positions": len(recs), "move_overhead": a.move_overhead, "host": platform.node(),
            "started": time.strftime("%Y-%m-%d %H:%M:%S"), "warnings": []}
    print(f"{a.name}: {len(recs)} positions, budgets {budgets}, movetimes {movetimes}",
          file=sys.stderr)

    def done_keys(path, key):
        return {(r["id"], r[key]) for r in read_jsonl(path)}

    # ---------------- Study A
    if 0 in budgets:
        path = out / "study_a.jsonl"
        done = done_keys(path, "budget")
        todo = [r for r in recs if (r["id"], 0) not in done]
        if todo:
            e = make_engine(a, out, "A", "A")
            meta["warnings"] += e.warnings
            pr = Progress(len(todo), f"{a.name} A")
            for r in todo:
                e.newgame()
                res = e.go(fen=r["fen"], nodes=1)
                append_jsonl(path, {"id": r["id"], "budget": 0, "best": res["bestmove"],
                                    "p": {m: round(v["p"], 6) for m, v in res["moves"].items()},
                                    "wl": res.get("wl"), "d": res.get("d"), "v": res.get("v"),
                                    "m": res.get("m"), "nodes": res["nodes"]})
                pr.tick()
            e.quit()

    # ---------------- Study B
    bb = sorted(b for b in budgets if b > 0)
    if bb:
        path = out / "study_b.jsonl"
        done = done_keys(path, "budget")
        todo = [r for r in recs if any((r["id"], b) not in done for b in bb)]
        if todo:
            e = make_engine(a, out, "B", "B")
            meta["warnings"] += e.warnings
            pr = Progress(len(todo), f"{a.name} B")
            for r in todo:
                for b in bb:  # ascending; same-position cache reuse only saves time
                    if (r["id"], b) in done:
                        continue
                    e.newgame()
                    res = e.go(fen=r["fen"], nodes=b)
                    append_jsonl(path, {"id": r["id"], "budget": b, "best": res["bestmove"],
                                        "nodes": res["nodes"], "time_ms": res["time_ms"],
                                        "wall": round(res["wall"], 4),
                                        "score_cp": res["score_cp"], "depth": res["depth"]})
                pr.tick()
            e.quit()

    # ---------------- Study C
    if movetimes:
        path = out / "study_c.jsonl"
        done = done_keys(path, "movetime")
        for mt in movetimes:
            todo = [r for r in recs if (r["id"], mt) not in done]
            if not todo:
                continue
            e = make_engine(a, out, f"C{mt}", "C")
            meta["warnings"] += e.warnings
            e.go(fen=todo[0]["fen"], movetime=mt)  # warm-up, not recorded
            pr = Progress(len(todo), f"{a.name} C{mt}")
            for r in todo:
                e.newgame()
                res = e.go(fen=r["fen"], movetime=mt)
                append_jsonl(path, {"id": r["id"], "movetime": mt, "best": res["bestmove"],
                                    "nodes": res["nodes"], "time_ms": res["time_ms"],
                                    "wall": round(res["wall"], 4), "depth": res["depth"]})
                pr.tick()
            e.quit()

    meta["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    hist = out / "meta.jsonl"
    append_jsonl(hist, meta)
    write_json(out / "meta.json", meta)
    if any("fp32" in w.lower() for w in meta["warnings"]):
        print("!!! lc0 warned about FP32 (trap 3): this run is not a valid FP16/INT8 "
              "measurement. Check the onnxruntime version.", file=sys.stderr)


if __name__ == "__main__":
    main()
STATUS.md
C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_lc0_cuda_gpu_kern_sum.csv

C
~~~
Produced: LOG.md entry only.

## 2026-10-28 00:14:50 +05:30 — pre-flight artifact verification and other-kernel review
Exact command: following Python via here-string piped to ..\.venv\Scripts\python.exe - (cwd leela-int8)
~~~python
import csv, json, sys, hashlib
from pathlib import Path
from hw.trt_layers import classify_text
cfg=json.loads(Path('config.json').read_text())
print('Python:', sys.version)
for k in ['lc0','trtexec','nsys','bt3','syzygy']:
    p=Path(cfg[k]); print(k, str(p.resolve()), 'exists=',p.exists())
    assert p.exists(), f'missing {k}: {p}'
sy=list(Path(cfg['syzygy']).glob('*.rtb*'))
print('Syzygy files:',len(sy),'WDL:',sum(p.suffix=='.rtbw' for p in sy),'DTZ:',sum(p.suffix=='.rtbz' for p in sy))
for p in ['data/tbset.jsonl','data/calib.npz','data/dev.npz','models/bt3_fp32.onnx','models/fp16.pb.gz','models/s2.pb.gz']:
    q=Path(p); print(p, 'bytes=',q.stat().st_size)
print('Existing s4:',Path('models/s4.pb.gz').exists(),'outlier report:',Path('reports/outliers.txt').exists())
day=Path('day1.log').read_text(); summary=day[day.index('=== day-1 summary ==='):]
print('Verbatim day-1 summary present in LOG.md:',summary in Path('LOG.md').read_text())
assert summary in Path('LOG.md').read_text()
p=Path('reports/trt/s2_lc0_cuda_gpu_kern_sum.csv')
txt=p.read_text(); i=txt.find('"Time'); i=i if i>=0 else txt.find('Time')
rows=list(csv.DictReader(txt[i:].splitlines()))
ns=lambda r:float(r.get('Total Time (ns)','0').replace(',',''))
total=sum(ns(r) for r in rows)
other=sorted([r for r in rows if not classify_text(r['Name'])], key=ns,reverse=True)
print('All kernel time (ns):',int(total),'Other kernel rows:',len(other))
lines=['# Top 15 kernels tagged other','', 'Shares are of ALL captured GPU kernel time; labels are name-based inference, not measured operand precision.','', '| Rank | Total ns | Share | Looks like | Kernel |','|---|---|---|---|---|']
for j,r in enumerate(other[:15],1):
    name=r['Name']; low=name.lower()
    if 'i168' in low or 'i8816' in low or 'i8832' in low:
        label='INT8 (inferred integer MMA naming)'
    elif 'h168' in low or 'h884' in low or 'hgemm' in low or 'h16816' in low:
        label='FP16 (inferred half MMA/GEMM naming)'
    elif any(s in low for s in ['gemm','mma','matmul']):
        label='matmul, precision unresolved from name'
    else:
        label='non-matmul (name-based)'
    lines.append(f'| {j} | {int(ns(r))} | {100*ns(r)/total:.4f}% | {label} | `{name}` |')
report='\n'.join(lines)+'\n'
p=Path('reports/trt/s2_other_top15_review.md'); p.write_text(report)
print(report);print('Produced:',p.resolve())
~~~
Exit code: 0
Output:
~~~
Python: 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
lc0 C:\Users\HP\Desktop\LC0-B\tools\lc0\lc0.exe exists= True
trtexec C:\Users\HP\Desktop\LC0-B\tools\TensorRT-10.12.0.36\bin\trtexec.exe exists= True
nsys C:\Users\HP\Desktop\LC0-B\tools\nsys\nsight_systems-windows-x86_64-2025.1.3.140-archive\nsight-systems\2025.1.3\target-windows-x64\nsys.exe exists= True
bt3 C:\Users\HP\Desktop\LC0-B\leela-int8\nets\BT3.pb.gz exists= True
syzygy C:\Users\HP\Desktop\LC0-B\syzygy exists= True
Syzygy files: 290 WDL: 145 DTZ: 145
data/tbset.jsonl bytes= 6694891
data/calib.npz bytes= 235353
data/dev.npz bytes= 670848
models/bt3_fp32.onnx bytes= 410354293
models/fp16.pb.gz bytes= 294605128
models/s2.pb.gz bytes= 95037093
Existing s4: False outlier report: False
Verbatim day-1 summary present in LOG.md: True
All kernel time (ns): 7191070160 Other kernel rows: 57
# Top 15 kernels tagged other

Shares are of ALL captured GPU kernel time; labels are name-based inference, not measured operand precision.

| Rank | Total ns | Share | Looks like | Kernel |
|---|---|---|---|---|
| 1 | 447450214 | 6.2223% | non-matmul (name-based) | `__myl_CastMul_0x9698266d4f8a2c42b3ee5030474f1e88_com_vec` |
| 2 | 376231329 | 5.2319% | non-matmul (name-based) | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce7fb8c_com_vec` |
| 3 | 319075746 | 4.4371% | non-matmul (name-based) | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_com_vec` |
| 4 | 302974486 | 4.2132% | non-matmul (name-based) | `__myl_CastMulAddReshTranReshMove_0x0340c5e5be98d9cff14028d435e46a87_com_vec` |
| 5 | 169936666 | 2.3632% | matmul, precision unresolved from name | `_gemm_mha_v2_0x5670ba801b2de8a2907d63de1165fdb4` |
| 6 | 154229791 | 2.1447% | non-matmul (name-based) | `__myl_CastMulAddReshTranReshMove_0x132535db0b518e0a175a5158bc1b1139_com_vec` |
| 7 | 133882345 | 1.8618% | non-matmul (name-based) | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce7fb8c_vec` |
| 8 | 103491656 | 1.4392% | non-matmul (name-based) | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_vec` |
| 9 | 88060935 | 1.2246% | non-matmul (name-based) | `__myl_MoveReshTran_0x7bfad93cb08ea2697ad4d01ea85ce2ff_com_vec` |
| 10 | 84982118 | 1.1818% | matmul, precision unresolved from name | `_gemm_mha_v2_0x1fe1cc1fc70208fa1b2cf8ace9d12c4f` |
| 11 | 84982039 | 1.1818% | matmul, precision unresolved from name | `_gemm_mha_v2_0x7f1aba88ddd93d06bfd656f26231a9bf` |
| 12 | 84979997 | 1.1817% | matmul, precision unresolved from name | `_gemm_mha_v2_0xa3cb0d93fdf10f031368b0c1d43bf756` |
| 13 | 84970010 | 1.1816% | matmul, precision unresolved from name | `_gemm_mha_v2_0x4362f572a7cf6cb4ad2c8c19dbcd894e` |
| 14 | 84967008 | 1.1816% | matmul, precision unresolved from name | `_gemm_mha_v2_0x188def927c4090eca727b3bc88fcb84c` |
| 15 | 84964450 | 1.1815% | matmul, precision unresolved from name | `_gemm_mha_v2_0x8e523ab71e8f56bda53303a6b0159433` |

Produced: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\trt\s2_other_top15_review.md
~~~

## 2026-10-28 00:14:50 +05:30 — dependency pre-flight
Exact command: ..\.venv\Scripts\python.exe -m pip check
Exit code: 0
Output:
~~~
No broken requirements found.
~~~
Produced: LOG.md only.

## 2026-10-28 00:15:29 +05:30 — kernel interpretation
Exact command: Python via here-string piped to ..\.venv\Scripts\python.exe -
~~~python
from pathlib import Path
p=Path('reports/trt/s2_other_top15_review.md')
s=p.read_text().replace('matmul, precision unresolved from name','likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved)')
s += '\nInterpretation: day1.log records s2 as 164 weight nodes + 0 act-act. ladder.py builds s2 with per-channel minmax without --act-act-matmul. The bundled ORT and optimize=8 permit FP16 fallback (README trap 4). Thus the _gemm_mha_v2 entries look like FP16 attention matmuls; this is a contextual inference, not a measured precision. Cast/Mul/Mean/Sqrt/Div/Mish-like, transpose and move kernels are non-matmul even when operating on mixed precision tensors. No classifier or pipeline code changed.\n'
p.write_text(s)
print(s)
~~~
Exit code: 0
Output:
~~~
# Top 15 kernels tagged other

Shares are of ALL captured GPU kernel time; labels are name-based inference, not measured operand precision.

| Rank | Total ns | Share | Looks like | Kernel |
|---|---|---|---|---|
| 1 | 447450214 | 6.2223% | non-matmul (name-based) | `__myl_CastMul_0x9698266d4f8a2c42b3ee5030474f1e88_com_vec` |
| 2 | 376231329 | 5.2319% | non-matmul (name-based) | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce7fb8c_com_vec` |
| 3 | 319075746 | 4.4371% | non-matmul (name-based) | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_com_vec` |
| 4 | 302974486 | 4.2132% | non-matmul (name-based) | `__myl_CastMulAddReshTranReshMove_0x0340c5e5be98d9cff14028d435e46a87_com_vec` |
| 5 | 169936666 | 2.3632% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x5670ba801b2de8a2907d63de1165fdb4` |
| 6 | 154229791 | 2.1447% | non-matmul (name-based) | `__myl_CastMulAddReshTranReshMove_0x132535db0b518e0a175a5158bc1b1139_com_vec` |
| 7 | 133882345 | 1.8618% | non-matmul (name-based) | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce7fb8c_vec` |
| 8 | 103491656 | 1.4392% | non-matmul (name-based) | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_vec` |
| 9 | 88060935 | 1.2246% | non-matmul (name-based) | `__myl_MoveReshTran_0x7bfad93cb08ea2697ad4d01ea85ce2ff_com_vec` |
| 10 | 84982118 | 1.1818% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x1fe1cc1fc70208fa1b2cf8ace9d12c4f` |
| 11 | 84982039 | 1.1818% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x7f1aba88ddd93d06bfd656f26231a9bf` |
| 12 | 84979997 | 1.1817% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0xa3cb0d93fdf10f031368b0c1d43bf756` |
| 13 | 84970010 | 1.1816% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x4362f572a7cf6cb4ad2c8c19dbcd894e` |
| 14 | 84967008 | 1.1816% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x188def927c4090eca727b3bc88fcb84c` |
| 15 | 84964450 | 1.1815% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x8e523ab71e8f56bda53303a6b0159433` |

Interpretation: day1.log records s2 as 164 weight nodes + 0 act-act. ladder.py builds s2 with per-channel minmax without --act-act-matmul. The bundled ORT and optimize=8 permit FP16 fallback (README trap 4). Thus the _gemm_mha_v2 entries look like FP16 attention matmuls; this is a contextual inference, not a measured precision. Cast/Mul/Mean/Sqrt/Div/Mish-like, transpose and move kernels are non-matmul even when operating on mixed precision tensors. No classifier or pipeline code changed.

~~~
Produced: reports/trt/s2_other_top15_review.md. No pipeline/config code edits.

## 2026-10-28 00:15:29 +05:30 — before s4 build
Exact command: nvidia-smi
Exit code: 0
~~~
Wed Oct 28 00:15:29 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   41C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
~~~

## 2026-10-28 00:15:30 +05:30 — s4 build started
Exact command (cwd leela-int8): ..\.venv\Scripts\python.exe -u ladder.py build --only s4
Output capture: 2>&1 | Tee-Object reports/logs/C1-build.log
Exit code: running; completion recorded below.
Resume command: ..\.venv\Scripts\python.exe -u ladder.py build --only s4

## 2026-10-28 00:16:49 +05:30 — outlier report inspection (build still running)
Exact command: Get-Content reports/outliers.txt
Exit code: 0
Output:
~~~
# outlier_ratio = worst input channel |x|max / median channel |x|max
# tens-to-hundreds on attention/FFN inputs: SmoothQuant has work to do
    ratio        max     median  tensor -> consumers
 665019.9      52.76  7.933e-05  /encoder14/ln2 -> /policy/dense1/matmul,/value/embed/matmul,/mlh/embed/matmul
  27631.9      42.34   0.001532  /mlh/dense1/mish -> /mlh/dense2/matmul
    489.0         57     0.1166  /attn_body/rehape -> /attn_body/ffn/dense1/w
     91.9      28.37     0.3088  /value/dense1/mish -> /value/dense2/matmul
     69.0      50.65     0.7338  /encoder0/ln1 -> /encoder0/ffn/dense1/w
     53.8      5.782     0.1075  /policy/dense1/mish -> /policy/Q/matmul,/policy/K/matmul
     51.9      50.74     0.9774  /encoder1/ln1 -> /encoder1/ffn/dense1/w
     48.9      54.65      1.119  /encoder2/ln1 -> /encoder2/ffn/dense1/w
     44.4      54.92      1.236  /encoder3/ln1 -> /encoder3/ffn/dense1/w
     40.4      50.52      1.252  /encoder4/ln1 -> /encoder4/ffn/dense1/w
     40.2      23.15     0.5763  /value/reshape -> /value/dense1/matmul
     36.6      49.09       1.34  /encoder5/ln1 -> /encoder5/ffn/dense1/w
     33.8      45.88      1.356  /encoder8/ln1 -> /encoder8/ffn/dense1/w
     33.7      47.34      1.403  /encoder6/ln1 -> /encoder6/ffn/dense1/w
     32.8      45.54      1.389  /encoder7/ln1 -> /encoder7/ffn/dense1/w
     32.7      44.58      1.364  /encoder9/ln1 -> /encoder9/ffn/dense1/w
     30.1      41.16      1.369  /encoder10/ln1 -> /encoder10/ffn/dense1/w
     28.3      36.72      1.298  /encoder11/ln1 -> /encoder11/ffn/dense1/w
     26.1       31.1       1.19  /encoder13/ln1 -> /encoder13/ffn/dense1/w
     21.9      26.97      1.231  /encoder12/ln1 -> /encoder12/ffn/dense1/w
     20.4      4.901     0.2399  /attn_body/ln2 -> /encoder0/mha/Q/w,/encoder0/mha/K/w,/encoder0/mha/V/w,/encoder0/smolgen/compress
     20.0      16.62     0.8291  /encoder14/ln1 -> /encoder14/ffn/dense1/w
     11.6      6.917     0.5944  policy/promotion/slice -> /policy/promotion/matmul
     11.3      7.739     0.6846  /encoder13/ln2 -> /encoder14/mha/Q/w,/encoder14/mha/K/w,/encoder14/mha/V/w,/encoder14/smolgen/compress
     10.8         20      1.846  /attn_body/embedding/out/reshape -> /attn_body/matmul
      8.9      8.587     0.9613  /encoder14/smolgen/gen_from/reshape -> /encoder14/smolgen/smol_weight_gen
      8.6      4.054      0.472  /encoder0/ln2 -> /encoder1/mha/Q/w,/encoder1/mha/K/w,/encoder1/mha/V/w,/encoder1/smolgen/compress
      8.5      5.549     0.6521  /encoder12/ln2 -> /encoder13/mha/Q/w,/encoder13/mha/K/w,/encoder13/mha/V/w,/encoder13/smolgen/compress
      8.1      8.289      1.022  /encoder8/smolgen/gen_from/reshape -> /encoder8/smolgen/smol_weight_gen
      8.0      4.035      0.506  /encoder1/ln2 -> /encoder2/mha/Q/w,/encoder2/mha/K/w,/encoder2/mha/V/w,/encoder2/smolgen/compress
      7.5      16.16      2.159  /encoder0/smolgen/gen_from/reshape -> /encoder0/smolgen/smol_weight_gen
      7.1       7.84      1.097  /encoder5/smolgen/gen_from/reshape -> /encoder5/smolgen/smol_weight_gen
      6.9      7.824      1.126  /encoder10/smolgen/gen_from/reshape -> /encoder10/smolgen/smol_weight_gen
      6.7       10.7        1.6  /encoder14/mha/out/reshape -> /encoder14/mha/out/dense/w
      6.6      8.311      1.259  /encoder13/smolgen/gen_from/reshape -> /encoder13/smolgen/smol_weight_gen
      6.5      3.941     0.6098  /encoder11/ln2 -> /encoder12/mha/Q/w,/encoder12/mha/K/w,/encoder12/mha/V/w,/encoder12/smolgen/compress
      6.4      7.131       1.11  /encoder11/smolgen/gen_from/reshape -> /encoder11/smolgen/smol_weight_gen
      6.4      7.966      1.241  /encoder2/smolgen/gen_from/reshape -> /encoder2/smolgen/smol_weight_gen
      6.2      3.462     0.5543  /encoder2/ln2 -> /encoder3/mha/Q/w,/encoder3/mha/K/w,/encoder3/mha/V/w,/encoder3/smolgen/compress
      6.2      6.698      1.073  /encoder12/smolgen/gen_from/reshape -> /encoder12/smolgen/smol_weight_gen
      5.9      3.371     0.5744  /encoder9/ln2 -> /encoder10/mha/Q/w,/encoder10/mha/K/w,/encoder10/mha/V/w,/encoder10/smolgen/compress
      5.9      7.565       1.29  /encoder6/smolgen/gen_from/reshape -> /encoder6/smolgen/smol_weight_gen
      5.8      3.415     0.5872  /encoder10/ln2 -> /encoder11/mha/Q/w,/encoder11/mha/K/w,/encoder11/mha/V/w,/encoder11/smolgen/compress
      5.8      6.444      1.113  /encoder9/smolgen/gen_from/reshape -> /encoder9/smolgen/smol_weight_gen
      5.7       3.49     0.6131  /encoder8/ln2 -> /encoder9/mha/Q/w,/encoder9/mha/K/w,/encoder9/mha/V/w,/encoder9/smolgen/compress
      5.6      3.103     0.5586  /encoder3/ln2 -> /encoder4/mha/Q/w,/encoder4/mha/K/w,/encoder4/mha/V/w,/encoder4/smolgen/compress
      5.5      17.09       3.13  /encoder14/ffn/dense1/mish -> /encoder14/ffn/dense2/w
      5.4      14.94      2.744  /encoder3/smolgen/ln1 -> /encoder3/smolgen/dense2/w
      5.2      3.257     0.6274  /encoder4/ln2 -> /encoder5/mha/Q/w,/encoder5/mha/K/w,/encoder5/mha/V/w,/encoder5/smolgen/compress
      5.1      8.107      1.587  /encoder1/smolgen/gen_from/reshape -> /encoder1/smolgen/smol_weight_gen
      5.1      14.88      2.935  /encoder14/smolgen/compress/reshape -> /encoder14/smolgen/dense1/w
      5.0      14.39      2.863  /encoder4/smolgen/ln1 -> /encoder4/smolgen/dense2/w
      4.9      3.135     0.6407  /encoder7/ln2 -> /encoder8/mha/Q/w,/encoder8/mha/K/w,/encoder8/mha/V/w,/encoder8/smolgen/compress
      4.8      3.084     0.6377  /encoder6/ln2 -> /encoder7/mha/Q/w,/encoder7/mha/K/w,/encoder7/mha/V/w,/encoder7/smolgen/compress
      4.6      11.52      2.496  /encoder11/ffn/dense1/mish -> /encoder11/ffn/dense2/w
      4.6      4.884      1.065  /encoder3/smolgen/gen_from/reshape -> /encoder3/smolgen/smol_weight_gen
      4.6       3.03     0.6638  /encoder5/ln2 -> /encoder6/mha/Q/w,/encoder6/mha/K/w,/encoder6/mha/V/w,/encoder6/smolgen/compress
      4.2      4.262      1.012  /encoder4/smolgen/gen_from/reshape -> /encoder4/smolgen/smol_weight_gen
      4.2      39.26      9.411  /mlh/reshape -> /mlh/dense1/matmul
      4.0      4.327      1.081  /encoder7/smolgen/gen_from/reshape -> /encoder7/smolgen/smol_weight_gen
      3.9      10.61      2.718  /encoder13/ffn/dense1/mish -> /encoder13/ffn/dense2/w
      3.9      9.883      2.547  /encoder12/ffn/dense1/mish -> /encoder12/ffn/dense2/w
      3.8      11.16      2.921  /encoder5/ffn/dense1/mish -> /encoder5/ffn/dense2/w
      3.7      5.191      1.412  /encoder1/mha/out/reshape -> /encoder1/mha/out/dense/w
      3.6      10.36      2.862  /encoder7/smolgen/ln1 -> /encoder7/smolgen/dense2/w
      3.6      14.35      4.031  /encoder1/ffn/dense1/mish -> /encoder1/ffn/dense2/w
      3.5      3.311     0.9415  /encoder12/mha/out/reshape -> /encoder12/mha/out/dense/w
      3.3      11.46      3.433  /encoder3/ffn/dense1/mish -> /encoder3/ffn/dense2/w
      3.3      9.328      2.832  /encoder12/smolgen/compress/reshape -> /encoder12/smolgen/dense1/w
      3.3      9.224      2.833  /encoder6/ffn/dense1/mish -> /encoder6/ffn/dense2/w
      3.3      3.044      0.936  /encoder5/mha/out/reshape -> /encoder5/mha/out/dense/w
      3.2      8.944      2.773  /encoder7/ffn/dense1/mish -> /encoder7/ffn/dense2/w
      3.2      10.37      3.239  /encoder4/ffn/dense1/mish -> /encoder4/ffn/dense2/w
      3.2      2.839     0.8885  /encoder6/mha/out/reshape -> /encoder6/mha/out/dense/w
      3.1      2.453     0.7874  /encoder10/mha/out/reshape -> /encoder10/mha/out/dense/w
      3.1      7.971      2.566  /encoder9/ffn/dense1/mish -> /encoder9/ffn/dense2/w
      3.1      16.15      5.259  /attn_body/ffn/dense1/mish -> /attn_body/ffn/dense2/w
      3.1      2.428     0.7924  /encoder7/mha/out/reshape -> /encoder7/mha/out/dense/w
      3.0      2.722     0.9138  /encoder9/mha/out/reshape -> /encoder9/mha/out/dense/w
      2.9      8.756      2.983  /encoder5/smolgen/ln1 -> /encoder5/smolgen/dense2/w
      2.9      10.49      3.615  /encoder2/ffn/dense1/mish -> /encoder2/ffn/dense2/w
      2.9      2.935      1.019  /encoder3/mha/out/reshape -> /encoder3/mha/out/dense/w
      2.9      8.529       2.98  /encoder6/smolgen/ln1 -> /encoder6/smolgen/dense2/w
      2.9       8.29      2.902  /encoder11/smolgen/ln1 -> /encoder11/smolgen/dense2/w
      2.8      7.593      2.665  /encoder10/ffn/dense1/mish -> /encoder10/ffn/dense2/w
      2.8      8.939      3.145  /encoder9/smolgen/compress/reshape -> /encoder9/smolgen/dense1/w
      2.8      2.529     0.8958  /encoder11/mha/out/reshape -> /encoder11/mha/out/dense/w
      2.8      8.812      3.137  /encoder6/smolgen/compress/reshape -> /encoder6/smolgen/dense1/w
      2.8      3.254      1.162  /encoder13/mha/out/reshape -> /encoder13/mha/out/dense/w
      2.8      7.888      2.868  /encoder7/smolgen/compress/reshape -> /encoder7/smolgen/dense1/w
      2.7      7.495      2.727  /encoder8/ffn/dense1/mish -> /encoder8/ffn/dense2/w
      2.7      2.453     0.8948  /encoder8/mha/out/reshape -> /encoder8/mha/out/dense/w
      2.7       8.38      3.069  /encoder2/smolgen/compress/reshape -> /encoder2/smolgen/dense1/w
      2.7      3.573      1.316  /encoder2/mha/out/reshape -> /encoder2/mha/out/dense/w
      2.7      8.037      2.981  /encoder1/smolgen/compress/reshape -> /encoder1/smolgen/dense1/w
      2.7      8.976      3.382  /encoder0/smolgen/compress/reshape -> /encoder0/smolgen/dense1/w
      2.6      7.785      2.973  /encoder0/smolgen/ln1 -> /encoder0/smolgen/dense2/w
      2.6      8.108      3.111  /encoder5/smolgen/compress/reshape -> /encoder5/smolgen/dense1/w
      2.6      2.563     0.9834  /encoder4/mha/out/reshape -> /encoder4/mha/out/dense/w
      2.6      7.567      2.954  /encoder2/smolgen/ln1 -> /encoder2/smolgen/dense2/w
      2.5      7.022      2.788  /encoder10/smolgen/compress/reshape -> /encoder10/smolgen/dense1/w
      2.5      7.473      2.967  /encoder8/smolgen/ln1 -> /encoder8/smolgen/dense2/w
      2.5      7.692      3.063  /encoder12/smolgen/ln1 -> /encoder12/smolgen/dense2/w
      2.5      7.667      3.066  /encoder10/smolgen/ln1 -> /encoder10/smolgen/dense2/w
      2.5        7.9      3.166  /encoder13/smolgen/compress/reshape -> /encoder13/smolgen/dense1/w
      2.5       10.4      4.205  /encoder0/ffn/dense1/mish -> /encoder0/ffn/dense2/w
      2.5      7.489      3.046  /encoder9/smolgen/ln1 -> /encoder9/smolgen/dense2/w
      2.4      3.662        1.5  /encoder0/mha/out/reshape -> /encoder0/mha/out/dense/w
      2.4      6.538      2.747  /encoder8/smolgen/compress/reshape -> /encoder8/smolgen/dense1/w
      2.2      5.498       2.51  /encoder11/smolgen/compress/reshape -> /encoder11/smolgen/dense1/w
      2.2      6.427      2.949  /encoder1/smolgen/ln1 -> /encoder1/smolgen/dense2/w
      2.2      6.483      3.006  /encoder4/smolgen/compress/reshape -> /encoder4/smolgen/dense1/w
      2.1      6.419      3.086  /encoder13/smolgen/ln1 -> /encoder13/smolgen/dense2/w
      2.1       6.06      2.938  /encoder14/smolgen/ln1 -> /encoder14/smolgen/dense2/w
      1.8      5.273      2.889  /encoder3/smolgen/compress/reshape -> /encoder3/smolgen/dense1/w
      1.0          1          1  /attn_body/embedding/reshape -> /attn_body/embedding/preprocess/matmul

# after SmoothQuant (per group)
 665019.9 -> 124666.6  /encoder14/ln2
  27631.9 -> 59476.0  /mlh/dense1/mish
    489.0 ->    17.3  /attn_body/rehape
     91.9 ->    49.3  /value/dense1/mish
     69.0 ->     4.7  /encoder0/ln1
     53.8 ->    30.4  /policy/dense1/mish
     51.9 ->     5.2  /encoder1/ln1
     48.9 ->     4.7  /encoder2/ln1
     44.4 ->     4.6  /encoder3/ln1
     40.4 ->     4.2  /encoder4/ln1
     40.2 ->    16.4  /value/reshape
     36.6 ->     4.1  /encoder5/ln1
     33.8 ->     4.4  /encoder8/ln1
     33.7 ->     4.1  /encoder6/ln1
     32.8 ->     3.6  /encoder7/ln1
     32.7 ->     3.7  /encoder9/ln1
     30.1 ->     4.1  /encoder10/ln1
     28.3 ->     3.6  /encoder11/ln1
     26.1 ->     3.2  /encoder13/ln1
     21.9 ->     4.3  /encoder12/ln1
     20.4 ->     4.4  /attn_body/ln2
     20.0 ->     3.6  /encoder14/ln1
     11.6 ->     6.8  policy/promotion/slice
     11.3 ->     3.5  /encoder13/ln2
     10.9 ->     2.3  /attn_body/embedding/out/reshape
      8.6 ->     4.3  /encoder0/ln2
      8.5 ->     3.5  /encoder12/ln2
      8.0 ->     4.0  /encoder1/ln2
      6.7 ->     3.1  /encoder14/mha/out/reshape
      6.5 ->     3.6  /encoder11/ln2
      6.2 ->     4.2  /encoder2/ln2
      5.9 ->     3.8  /encoder9/ln2
      5.8 ->     3.6  /encoder10/ln2
      5.7 ->     4.1  /encoder8/ln2
      5.6 ->     4.2  /encoder3/ln2
      5.5 ->     3.5  /encoder14/ffn/dense1/mish
      5.4 ->     5.2  /encoder3/smolgen/ln1
      5.2 ->     3.9  /encoder4/ln2
      5.1 ->     2.4  /encoder14/smolgen/compress/reshape
      5.0 ->     4.5  /encoder4/smolgen/ln1
      4.9 ->     3.8  /encoder7/ln2
      4.8 ->     4.4  /encoder6/ln2
      4.6 ->     6.6  /encoder11/ffn/dense1/mish
      4.6 ->     3.8  /encoder5/ln2
      4.2 ->     2.4  /mlh/reshape
      3.9 ->     3.0  /encoder13/ffn/dense1/mish
      3.9 ->     3.5  /encoder12/ffn/dense1/mish
      3.8 ->     2.9  /encoder5/ffn/dense1/mish
      3.7 ->     2.4  /encoder1/mha/out/reshape
      3.6 ->     3.7  /encoder7/smolgen/ln1
      3.6 ->     3.2  /encoder1/ffn/dense1/mish
      3.5 ->     4.7  /encoder12/mha/out/reshape
      3.3 ->     2.5  /encoder3/ffn/dense1/mish
      3.3 ->     1.8  /encoder12/smolgen/compress/reshape
      3.3 ->     4.0  /encoder6/ffn/dense1/mish
      3.3 ->     2.7  /encoder5/mha/out/reshape
      3.2 ->     3.4  /encoder7/ffn/dense1/mish
      3.2 ->     3.2  /encoder4/ffn/dense1/mish
      3.2 ->     2.6  /encoder6/mha/out/reshape
      3.1 ->     3.1  /encoder10/mha/out/reshape
      3.1 ->     3.9  /encoder9/ffn/dense1/mish
      3.1 ->     2.1  /attn_body/ffn/dense1/mish
      3.1 ->     2.8  /encoder7/mha/out/reshape
      3.0 ->     2.6  /encoder9/mha/out/reshape
      2.9 ->     2.9  /encoder5/smolgen/ln1
      2.9 ->     2.6  /encoder2/ffn/dense1/mish
      2.9 ->     2.7  /encoder3/mha/out/reshape
      2.9 ->     2.9  /encoder6/smolgen/ln1
      2.9 ->     2.9  /encoder11/smolgen/ln1
      2.8 ->     5.3  /encoder10/ffn/dense1/mish
      2.8 ->     1.9  /encoder9/smolgen/compress/reshape
      2.8 ->     2.9  /encoder11/mha/out/reshape
      2.8 ->     1.8  /encoder6/smolgen/compress/reshape
      2.8 ->     2.8  /encoder13/mha/out/reshape
      2.8 ->     1.7  /encoder7/smolgen/compress/reshape
      2.7 ->     3.2  /encoder8/ffn/dense1/mish
      2.7 ->     2.5  /encoder8/mha/out/reshape
      2.7 ->     1.8  /encoder2/smolgen/compress/reshape
      2.7 ->     2.7  /encoder2/mha/out/reshape
      2.7 ->     2.0  /encoder1/smolgen/compress/reshape
      2.7 ->     1.9  /encoder0/smolgen/compress/reshape
      2.6 ->     2.5  /encoder0/smolgen/ln1
      2.6 ->     1.7  /encoder5/smolgen/compress/reshape
      2.6 ->     2.7  /encoder4/mha/out/reshape
      2.6 ->     2.7  /encoder2/smolgen/ln1
      2.5 ->     1.7  /encoder10/smolgen/compress/reshape
      2.5 ->     2.9  /encoder8/smolgen/ln1
      2.5 ->     2.6  /encoder12/smolgen/ln1
      2.5 ->     2.7  /encoder10/smolgen/ln1
      2.5 ->     1.7  /encoder13/smolgen/compress/reshape
      2.5 ->     2.8  /encoder0/ffn/dense1/mish
      2.5 ->     2.6  /encoder9/smolgen/ln1
      2.4 ->     2.8  /encoder0/mha/out/reshape
      2.4 ->     1.8  /encoder8/smolgen/compress/reshape
      2.2 ->     1.7  /encoder11/smolgen/compress/reshape
      2.2 ->     2.4  /encoder1/smolgen/ln1
      2.2 ->     1.6  /encoder4/smolgen/compress/reshape
      2.1 ->     2.3  /encoder13/smolgen/ln1
      2.1 ->     2.3  /encoder14/smolgen/ln1
      1.8 ->     1.5  /encoder3/smolgen/compress/reshape
      1.0 ->     1.4  /attn_body/embedding/reshape
~~~
Read existing build output: reports/outliers.txt; produced LOG.md entry only.

## 2026-10-28 00:18:26 +05:30 — build progress inspection
Exact command: Get-CimInstance Win32_Process | Where-Object { $_.Name -match "python|lc0" } | Select-Object ProcessId,ParentProcessId,Name,CommandLine; Get-ChildItem models/s4*; Get-Content reports/logs/C1-build.log -Tail 8
Exit code: 0
~~~

ProcessId       : 10592
ParentProcessId : 31524
Name            : python.exe
CommandLine     : "C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe" -u ladder.py build --only s4

ProcessId       : 23336
ParentProcessId : 10592
Name            : python.exe
CommandLine     : "C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" -u ladder.py build --only s4

ProcessId       : 24348
ParentProcessId : 23336
Name            : python.exe
CommandLine     : C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib 
                  C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --granularity per-channel --method percentile --percentile 99.99 --smoothquant 0.5 --outlier-report 
                  C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt

ProcessId       : 11472
ParentProcessId : 24348
Name            : python.exe
CommandLine     : "C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib 
                  C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --granularity per-channel --method percentile --percentile 99.99 --smoothquant 0.5 --outlier-report 
                  C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt

calibration planes match BT3's input format (INPUT_CLASSICAL_112_PLANE)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --granularity per-channel --method percentile --percentile 99.99 --smoothquant 0.5 --outlier-report C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.5: 101 groups smoothed
outlier report -> C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 

~~~
Produced: LOG.md entry only.

## 2026-10-28 00:19:14 +05:30 — LN outlier ratio extraction
Exact command: Python via here-string piped to ..\.venv\Scripts\python.exe -
~~~python
from pathlib import Path
import re
s=Path('reports/outliers.txt').read_text()
rows=[]
for line in s.split('# after SmoothQuant (per group)')[1].splitlines():
    m=re.match(r'\s*([\d.]+)\s*->\s*([\d.]+)\s+(\S+)',line)
    if m and re.search(r'/ln[12]$',m[3]): rows.append((m[3],float(m[1]),float(m[2])))
lines=['# LN output outlier ratios','','Worst input-channel absolute maximum / median live-channel maximum. Before and after SmoothQuant at alpha 0.5, as printed in reports/outliers.txt.','','| LN output | Before | After |','|---|---|---|']
for n,b,a in sorted(rows): lines.append(f'| `{n}` | {b:.1f} | {a:.1f} |')
for label,sel in [
    ('FFN input encoder ln1',lambda n:re.fullmatch(r'/encoder\d+/ln1',n)),
    ('QKV inputs (attn_body/ln2 and encoder0..13/ln2)',lambda n:n=='/attn_body/ln2' or bool(re.fullmatch(r'/encoder(?:[0-9]|1[0-3])/ln2',n))),
    ('Smolgen ln1',lambda n:'/smolgen/ln1' in n)]:
    group=[r for r in rows if sel(r[0])]
    lines+=['',f'{label}: before {min(r[1] for r in group):.1f}..{max(r[1] for r in group):.1f}; after {min(r[2] for r in group):.1f}..{max(r[2] for r in group):.1f}.']
text='\n'.join(lines)+'\n';p=Path('reports/C1_LN_outliers.md');p.write_text(text);print(text);print('Produced:',p.resolve())
~~~
Exit code: 0
Output:
~~~
# LN output outlier ratios

Worst input-channel absolute maximum / median live-channel maximum. Before and after SmoothQuant at alpha 0.5, as printed in reports/outliers.txt.

| LN output | Before | After |
|---|---|---|
| `/attn_body/ln2` | 20.4 | 4.4 |
| `/encoder0/ln1` | 69.0 | 4.7 |
| `/encoder0/ln2` | 8.6 | 4.3 |
| `/encoder0/smolgen/ln1` | 2.6 | 2.5 |
| `/encoder1/ln1` | 51.9 | 5.2 |
| `/encoder1/ln2` | 8.0 | 4.0 |
| `/encoder1/smolgen/ln1` | 2.2 | 2.4 |
| `/encoder10/ln1` | 30.1 | 4.1 |
| `/encoder10/ln2` | 5.8 | 3.6 |
| `/encoder10/smolgen/ln1` | 2.5 | 2.7 |
| `/encoder11/ln1` | 28.3 | 3.6 |
| `/encoder11/ln2` | 6.5 | 3.6 |
| `/encoder11/smolgen/ln1` | 2.9 | 2.9 |
| `/encoder12/ln1` | 21.9 | 4.3 |
| `/encoder12/ln2` | 8.5 | 3.5 |
| `/encoder12/smolgen/ln1` | 2.5 | 2.6 |
| `/encoder13/ln1` | 26.1 | 3.2 |
| `/encoder13/ln2` | 11.3 | 3.5 |
| `/encoder13/smolgen/ln1` | 2.1 | 2.3 |
| `/encoder14/ln1` | 20.0 | 3.6 |
| `/encoder14/ln2` | 665019.9 | 124666.6 |
| `/encoder14/smolgen/ln1` | 2.1 | 2.3 |
| `/encoder2/ln1` | 48.9 | 4.7 |
| `/encoder2/ln2` | 6.2 | 4.2 |
| `/encoder2/smolgen/ln1` | 2.6 | 2.7 |
| `/encoder3/ln1` | 44.4 | 4.6 |
| `/encoder3/ln2` | 5.6 | 4.2 |
| `/encoder3/smolgen/ln1` | 5.4 | 5.2 |
| `/encoder4/ln1` | 40.4 | 4.2 |
| `/encoder4/ln2` | 5.2 | 3.9 |
| `/encoder4/smolgen/ln1` | 5.0 | 4.5 |
| `/encoder5/ln1` | 36.6 | 4.1 |
| `/encoder5/ln2` | 4.6 | 3.8 |
| `/encoder5/smolgen/ln1` | 2.9 | 2.9 |
| `/encoder6/ln1` | 33.7 | 4.1 |
| `/encoder6/ln2` | 4.8 | 4.4 |
| `/encoder6/smolgen/ln1` | 2.9 | 2.9 |
| `/encoder7/ln1` | 32.8 | 3.6 |
| `/encoder7/ln2` | 4.9 | 3.8 |
| `/encoder7/smolgen/ln1` | 3.6 | 3.7 |
| `/encoder8/ln1` | 33.8 | 4.4 |
| `/encoder8/ln2` | 5.7 | 4.1 |
| `/encoder8/smolgen/ln1` | 2.5 | 2.9 |
| `/encoder9/ln1` | 32.7 | 3.7 |
| `/encoder9/ln2` | 5.9 | 3.8 |
| `/encoder9/smolgen/ln1` | 2.5 | 2.6 |

FFN input encoder ln1: before 20.0..69.0; after 3.2..5.2.

QKV inputs (attn_body/ln2 and encoder0..13/ln2): before 4.6..20.4; after 3.5..4.4.

Smolgen ln1: before 2.1..5.4; after 2.3..5.2.

Produced: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\C1_LN_outliers.md
~~~
Produced: reports/C1_LN_outliers.md

## 2026-10-28 00:20:57 +05:30 — dev comparison progress inspection
Exact command: Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,CPU,WorkingSet64; Get-Content reports/logs/C1-build.log -Tail 3
Exit code: 0
~~~

   Id    CPU WorkingSet64
   --    --- ------------
10592   0.00      4509696
23320 591.66    888037376
23336   0.16     30908416
32184   0.00      4399104

$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\quick_compare_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx

~~~
Produced: LOG.md entry only.

## 2026-10-28 00:22:03 +05:30 — s4 build completion
Exact command: ..\.venv\Scripts\python.exe -u ladder.py build --only s4
Exit code: 0
Key output:
~~~
calibration planes match BT3's input format (INPUT_CLASSICAL_112_PLANE)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --granularity per-channel --method percentile --percentile 99.99 --smoothquant 0.5 --outlier-report C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.5: 101 groups smoothed
outlier report -> C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.703, min 0.321 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (245s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\quick_compare_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx
3360 positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz (ORT, not TensorRT)
model                               KL   top1    |dV|  tb_acc
ref bt3_fp32.onnx             0.00e+00  1.000  0.0000   0.998
s4.onnx                       1.15e-02  0.889  0.0102   0.998
~~~
Output log: reports/logs/C1-build.log; reports/logs/C1-build.exitcode. Produced paths listed in output.

## 2026-10-28 00:22:30 +05:30 — before hardware benchmark
Exact command: nvidia-smi
Exit code: 0
~~~
Wed Oct 28 00:22:30 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   42C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
~~~

## 2026-10-28 00:22:30 +05:30 — hardware benchmark started
Exact command (cwd leela-int8): ..\.venv\Scripts\python.exe -u ladder.py hw --parts bench
Background exec session; output: 2>&1 | Tee-Object reports/logs/C1-hw-bench.log
Exit code: running; completion recorded below.
Resume command: ..\.venv\Scripts\python.exe -u ladder.py hw --parts bench
Note: hw bench reruns its benchmark sequence; it does not skip existing JSON. No clock lock requested (optional in RUN_4060.md); measured clocks are captured by bench.py.

## 2026-10-28 00:23:01 +05:30 — STATUS table normalization
Exact command: Python via here-string piped to ..\.venv\Scripts\python.exe -
~~~python
from pathlib import Path
p=Path('STATUS.md');s=p.read_text()
rows=[x for x in s.splitlines() if x.startswith('|')]
rows=[x for x in rows if x!='| 2-5 | todo | |']
rows += ['| 2c study --models fp16 --limit 50 | todo | Queued after hw bench |',
'| CHECKPOINT C1-done | todo | Pending completed bench and sizing results |',
'| 3-5 | todo | Await checkpoint approval |']
notes=[x[2:] for x in s.splitlines() if x.startswith('- ')]
for i,n in enumerate(notes,1): rows.append(f'| Prior-session review note {i} | done | {n.replace(chr(124),chr(47))} |')
p.write_text('# STATUS\n\nMachine: RTX 4060 Laptop (HP), Windows 11. Updated 2026-10-28. Commands and evidence: LOG.md.\n\n'+'\n'.join(rows)+'\n')
print(p.read_text())
~~~
Exit code: 0
Output:
~~~
# STATUS

Machine: RTX 4060 Laptop (HP), Windows 11. Updated 2026-10-28. Commands and evidence: LOG.md.

| Gate / step | State | Result |
|---|---|---|
| 0 Inventory | done | RTX 4060 Laptop 8188 MiB, driver 592.82 (CUDA 13.1); Python 3.11.9; Windows lc0 v0.33.0-rc0 onnx-trt (new download, `..\tools\lc0`); trtexec TRT 10.12.0.36; nsys 2025.1.3; BT3 sha256 matches Anjan's; Syzygy 3-4-5 290 files |
| 1a config.json | done | from config.example.json; lc0, trtexec, nsys, syzygy paths changed (diff in LOG.md) |
| 1b pip install -r requirements.txt | done | into `..\.venv` (Python 3.11.9); onnxruntime 1.31.1 (CPU), onnx 1.23.2, numpy 2.4.6 |
| 1c onnx-trt smoke test | done | `lc0 benchmark` on bundled 791556.pb.gz, optimize=6: 10534 nodes, 13698 nps, no FP32 warning |
| 1d describenet BT3 | done | INPUT_CLASSICAL_112_PLANE (traps 5/10 do not apply); 15 enc, 24 heads, 768, DFF 1024; exit 0 |
| 1e tbset | done | 11200 positions: calib 1120 / dev 3360 / test 6720; won 6803, drawn 4397 |
| 1f calib | done | calib.npz 512 positions, dev.npz 3360 positions, both input format 1 |
| 1g day1 | done | day1.log: wrapped/native KL 0.00e+00, top-1 1.000; INT8 runs; GEMM-like INT8 73.5% |
| CHECKPOINT C1-day1 | done | passed — explicitly approved by user on 2026-10-28; verbatim summary in LOG.md |
| Bookkeeping typo retry | done | Initial command BLOCKED at parsing: Missing closing parenthesis; one obvious-typo retry succeeded, no pipeline commands had run |
| Pre-flight C1 step 2 | done | Prior inventory/install/tbset/calib/day1 verified; paths exist, pip check passed, GPU idle, BatteryStatus 2; optional clock lock omitted, measured clocks will be recorded |
| Other-kernel review | done | reports/trt/s2_other_top15_review.md; labels inferred from names; pipeline code unchanged |
| 2a build --only s4 | done | Exit 0; reports/outliers.txt, models/s4.onnx, models/s4.pb.gz, reports/quick_compare_dev.txt |
| 2b hw --parts bench | running | One GPU job; background output reports/logs/C1-hw-bench.log; rerun same command to resume |
| 2c study --models fp16 --limit 50 | todo | Queued after hw bench |
| CHECKPOINT C1-done | todo | Pending completed bench and sizing results |
| 3-5 | todo | Await checkpoint approval |
| Prior-session review note 1 | done | `..\.venv`, `..\tools`, `..\syzygy` were created by the agent in this session (23:22-23:38), not earlier by someone else as AGENTS.md says. |
| Prior-session review note 2 | done | lc0, the CUDA/cuDNN/TRT DLLs, trtexec and nsys were downloaded: no Windows GPU lc0, trtexec or nsys existed on the machine, and Anjan's WSL lc0 is CPU-only (eigen). |
| Prior-session review note 3 | done | Syzygy was copied from Anjan's WSL env into `..\syzygy` rather than used by path. |
| Prior-session review note 4 | done | Exit codes for tbset, the smoke test and calib were not captured separately (output was piped to `tail`); see LOG.md. |

~~~
Updated: STATUS.md (existing prior-session review notes preserved as rows).

## 2026-10-28 00:29:18 +05:30 — FP16 benchmark artifact
Exact command: Get-Content reports/bench/fp16.json
Exit code: 0
Output:
~~~
{
 "name": "fp16",
 "weights": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\fp16.pb.gz",
 "backend": "onnx-trt",
 "backend_opts": "optimize=6",
 "env": {
  "nvml": true,
  "nvml_energy_counter": true,
  "gpu": "NVIDIA GeForce RTX 4060 Laptop GPU",
  "rapl": false,
  "platform": "win32",
  "pid": 24504
 },
 "time": "2026-10-28 00:22:30",
 "warnings": [],
 "idle": {
  "seconds": 10.015618085861206,
  "gpu_w": 2.5965446942023487,
  "sm_mhz_mean": 218.29145728643215,
  "temp_c_mean": 42.66834170854271
 },
 "backendbench": {
  "rows": [
   {
    "batch": 32,
    "nps": 3648.0,
    "ms": 8.773
   },
   {
    "batch": 64,
    "nps": 3727.0,
    "ms": 17.17
   },
   {
    "batch": 96,
    "nps": 3611.0,
    "ms": 26.59
   },
   {
    "batch": 128,
    "nps": 3581.0,
    "ms": 35.74
   },
   {
    "batch": 160,
    "nps": 3436.0,
    "ms": 46.57
   },
   {
    "batch": 192,
    "nps": 3282.0,
    "ms": 58.5
   },
   {
    "batch": 224,
    "nps": 3179.0,
    "ms": 70.47
   },
   {
    "batch": 256,
    "nps": 3176.0,
    "ms": 80.61
   },
   {
    "batch": 288,
    "nps": 2987.0,
    "ms": 96.41
   },
   {
    "batch": 320,
    "nps": 3104.0,
    "ms": 103.1
   },
   {
    "batch": 352,
    "nps": 3050.0,
    "ms": 115.4
   },
   {
    "batch": 384,
    "nps": 3019.0,
    "ms": 127.2
   },
   {
    "batch": 416,
    "nps": 3015.0,
    "ms": 138.0
   },
   {
    "batch": 448,
    "nps": 2971.0,
    "ms": 150.8
   },
   {
    "batch": 480,
    "nps": 2999.0,
    "ms": 160.1
   },
   {
    "batch": 512,
    "nps": 2955.0,
    "ms": 173.3
   }
  ],
  "energy": {
   "seconds": 288.8546416759491,
   "gpu_j": 24658.015,
   "gpu_j_source": "nvml_counter",
   "power_w_mean": 85.24212077378971,
   "power_w_min": 1.655,
   "power_w_max": 104.901,
   "sm_mhz_mean": 2182.4607877309168,
   "sm_mhz_min": 210,
   "sm_mhz_max": 2520,
   "mem_mhz_mean": 7925.543046357616,
   "mem_mhz_min": 405,
   "mem_mhz_max": 8001,
   "temp_c_mean": 81.98745207389334,
   "temp_c_min": 42,
   "temp_c_max": 87,
   "util_mean": 97.19205298013244,
   "util_min": 0,
   "util_max": 100,
   "gpu": "NVIDIA GeForce RTX 4060 Laptop GPU",
   "gpu_j_above_idle": 23907.991012760594
  }
 },
 "search": [
  {
   "nodes": 250628,
   "time_ms": 57626,
   "positions": 10,
   "movetime": 10000,
   "nps": 4349,
   "energy": {
    "seconds": 58.4552001953125,
    "gpu_j": 4849.223,
    "gpu_j_source": "nvml_counter",
    "power_w_mean": 83.07477241379326,
    "power_w_min": 78.36,
    "power_w_max": 93.709,
    "sm_mhz_mean": 2175.426724137931,
    "sm_mhz_min": 1875,
    "sm_mhz_max": 2505,
    "mem_mhz_mean": 8001.0,
    "mem_mhz_min": 8001,
    "mem_mhz_max": 8001,
    "temp_c_mean": 83.94310344827586,
    "temp_c_min": 81,
    "temp_c_max": 87,
    "util_mean": 99.29655172413793,
    "util_min": 89,
    "util_max": 100,
    "gpu": "NVIDIA GeForce RTX 4060 Laptop GPU",
    "gpu_j_above_idle": 4697.441460084326
   },
   "warnings": [],
   "gpu_j_per_node": 0.018742684217582736,
   "gpu_j_per_node_total": 0.01934828909778636
  }
 ]
}
~~~
Read: reports/bench/fp16.json. Produced: LOG.md entry.

## 2026-10-28 00:42:27 +05:30 — hardware benchmark completion
Exact command: ..\.venv\Scripts\python.exe -u ladder.py hw --parts bench
Exit code: 0
Key output:
~~~
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\bench.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\fp16.pb.gz --name fp16 --backend onnx-trt --backend-opts optimize=6 --movetime 10000 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\reports\bench
[fp16] warm-up (TensorRT engine build on first use can take minutes)
[fp16] idle {'seconds': 10.015618085861206, 'gpu_w': 2.5965446942023487, 'sm_mhz_mean': 218.29145728643215, 'temp_c_mean': 42.66834170854271}
  batch    32        3648 nps
  batch    64        3727 nps
  batch    96        3611 nps
  batch   128        3581 nps
  batch   160        3436 nps
  batch   192        3282 nps
  batch   224        3179 nps
  batch   256        3176 nps
  batch   288        2987 nps
  batch   320        3104 nps
  batch   352        3050 nps
  batch   384        3019 nps
  batch   416        3015 nps
  batch   448        2971 nps
  batch   480        2999 nps
  batch   512        2955 nps
  search run 1: 4349 nps, 250628 nodes, GPU 18.743 mJ/node above idle, SM 2175 MHz (min 1875), 87 C max
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\reports\bench\fp16.json
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\bench.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz --name s4 --backend onnx-trt --backend-opts optimize=8 --movetime 10000 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\reports\bench
[s4] warm-up (TensorRT engine build on first use can take minutes)
[s4] idle {'seconds': 10.020487308502197, 'gpu_w': 5.044165861785335, 'sm_mhz_mean': 210.0, 'temp_c_mean': 44.768844221105525}
  batch    32        4718 nps
  batch    64        4993 nps
  batch    96        4845 nps
  batch   128        4677 nps
  batch   160        4541 nps
  batch   192        4397 nps
  batch   224        4264 nps
  batch   256        4239 nps
  batch   288        4002 nps
  batch   320        4046 nps
  batch   352        3927 nps
  batch   384        3905 nps
  batch   416        3861 nps
  batch   448        3860 nps
  batch   480        3793 nps
  batch   512        3805 nps
  search run 1: 5685 nps, 312670 nodes, GPU 14.190 mJ/node above idle, SM 2269 MHz (min 1965), 87 C max
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\reports\bench\s4.json
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\bench.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --weights nets/BT3.pb.gz --name native --backend onnx-trt --backend-opts optimize=6 --movetime 10000 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\reports\bench
[native] warm-up (TensorRT engine build on first use can take minutes)
[native] idle {'seconds': 10.014123678207397, 'gpu_w': 3.1098078075239677, 'sm_mhz_mean': 212.26130653266333, 'temp_c_mean': 53.62311557788945}
  batch    32        3425 nps
  batch    64        3496 nps
  batch    96        3203 nps
  batch   128        3198 nps
  batch   160        3177 nps
  batch   192        3034 nps
  batch   224        2985 nps
  batch   256        3067 nps
  batch   288        2979 nps
  batch   320        2945 nps
  batch   352        2993 nps
  batch   384        2874 nps
  batch   416        2968 nps
  batch   448        2994 nps
  batch   480        3017 nps
  batch   512        2959 nps
  search run 1: 4358 nps, 253843 nodes, GPU 18.491 mJ/node above idle, SM 2159 MHz (min 1725), 87 C max
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\reports\bench\native.json
~~~
Outputs: reports/logs/C1-hw-bench.log, reports/logs/C1-hw-bench.exitcode; reports/logs/hw.log; reports/bench/ per output above.

## 2026-10-28 00:42:56 +05:30 — benchmark result validation
Exact command: Python via here-string piped to ..\.venv\Scripts\python.exe -
~~~python
from pathlib import Path
import json
for n in ['fp16','s4','native']:
    d=json.loads(Path(f'reports/bench/{n}.json').read_text())
    warnings=d['warnings']+sum([r.get('warnings',[]) for r in d['search']],[])
    print(n,'warnings:',warnings)
    assert not any('fp32' in w.lower() for w in warnings), f'{n}: FP32 warning'
    assert d['backendbench']['rows'] and d['search'],f'{n}: missing benchmark rows'
    b=next(r for r in d['backendbench']['rows'] if r['batch']==256)
    for r in d['search']:
        assert r['nps'] and r['nodes'],f'{n}: empty search'
        print(n,'raw batch256 nps:',b['nps'],'search nps:',r['nps'],'mean SM MHz:',r['energy']['sm_mhz_mean'],'min SM MHz:',r['energy']['sm_mhz_min'],'max temperature C:',r['energy']['temp_c_max'])
print('Saved benchmark result checks passed.')
~~~
Exit code: 0
Output:
~~~
fp16 warnings: []
fp16 raw batch256 nps: 3176.0 search nps: 4349 mean SM MHz: 2175.426724137931 min SM MHz: 1875 max temperature C: 87
s4 warnings: []
s4 raw batch256 nps: 4239.0 search nps: 5685 mean SM MHz: 2268.6787330316743 min SM MHz: 1965 max temperature C: 87
native warnings: []
native raw batch256 nps: 3067.0 search nps: 4358 mean SM MHz: 2159.2741935483873 min SM MHz: 1725 max temperature C: 87
Saved benchmark result checks passed.
~~~
Read: reports/bench/fp16.json, s4.json, native.json; produced LOG.md entry.

## 2026-10-28 00:42:56 +05:30 — before Study B sizing
Exact command: nvidia-smi
Exit code: 0
~~~
Wed Oct 28 00:42:56 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   49C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
~~~

## 2026-10-28 00:42:56 +05:30 — FP16 study sizing started
Exact command (cwd leela-int8): ..\.venv\Scripts\python.exe -u ladder.py study --models fp16 --limit 50
Background exec session; output: 2>&1 | Tee-Object reports/logs/C1-study-fp16-50.log
Exit code: running; completion recorded below.
Resume command: ..\.venv\Scripts\python.exe -u ladder.py study --models fp16 --limit 50
Timing interpretation from eval/run_study.py: its Study B progress ticks once after all budgets for a position. The 1600-node-only measurement will be extracted from study_b.jsonl without changing code.

## 2026-10-28 00:43:51 +05:30 — FP16 study sizing completion
Exact command: ..\.venv\Scripts\python.exe -u ladder.py study --models fp16 --limit 50
Exit code: 0
Key output:
~~~
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name fp16 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\fp16.pb.gz --backend onnx-trt --backend-opts optimize=6 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --limit 50 --budgets 0,100,400,800,1600 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results
fp16: 50 positions, budgets [0, 100, 400, 800, 1600], movetimes []
  [fp16 A] 25/50  0.24s/item  eta 0.1 min
  [fp16 A] 50/50  0.12s/item  eta 0.0 min
  [fp16 B] 25/50  1.01s/item  eta 0.4 min
  [fp16 B] 50/50  0.94s/item  eta 0.0 min
~~~
Outputs: reports/logs/C1-study-fp16-50.log, reports/logs/C1-study-fp16-50.exitcode, reports/logs/study.log, results/fp16/study_a.jsonl, study_b.jsonl, A.lc0.log, B.lc0.log, meta.json and meta.jsonl.

## 2026-10-28 00:44:39 +05:30 — C1-done result extraction and final validation
Exact command: Python via here-string piped to ..\.venv\Scripts\python.exe -
~~~python
from pathlib import Path
from argparse import Namespace
import json, re, statistics
from eval.run_study import positions
args=Namespace(tbset='data/tbset.jsonl',split='test',limit=50,classes=None,ids=None,shard=None)
ids={r['id'] for r in positions(args)}
records=[json.loads(x) for x in Path('results/fp16/study_b.jsonl').read_text().splitlines() if x.strip()]
records=[r for r in records if r['id'] in ids]
for budget in [100,400,800,1600]:
    group=[r for r in records if r['budget']==budget]
    print('Study B budget',budget,'records:',len(group),'distinct positions:',len({r['id'] for r in group}))
    assert len(group)==50 and len({r['id'] for r in group})==50, f'incomplete or duplicated budget {budget}'
meta=json.loads(Path('results/fp16/meta.json').read_text())
print('Study meta:',json.dumps(meta))
assert meta['n_positions']==50 and meta['split']=='test'
assert not meta['warnings'], 'Study warnings require review'
progress=[x for x in Path('reports/logs/C1-study-fp16-50.log').read_text().splitlines() if '[fp16 B]' in x][-1]
b=[r for r in records if r['budget']==1600]
meanwall=statistics.mean(r['wall'] for r in b)
meanlc0=statistics.mean(r['time_ms'] for r in b)/1000
meannodes=statistics.mean(r['nodes'] for r in b)
print('Study B final progress:',progress)
print(f'1600-node budget: mean wall s/position={meanwall:.6f}; mean lc0 s/position={meanlc0:.6f}; positions={len(b)}')
print(f'1600-node budget actual nodes: min={min(r["nodes"] for r in b)}; mean={meannodes:.2f}; max={max(r["nodes"] for r in b)}')
exitcodes={s:Path(f'reports/logs/{s}.exitcode').read_text().strip() for s in ['C1-build','C1-hw-bench','C1-study-fp16-50']}
print('Step exit codes:',json.dumps(exitcodes))
assert all(v=='0' for v in exitcodes.values())
day=Path('day1.log').read_text();summary=day[day.index('=== day-1 summary ==='):]
assert summary in Path('LOG.md').read_text(), 'Day-1 summary not verbatim in LOG.md'
print('Day-1 summary verbatim check: passed')
for f in ['reports/outliers.txt','models/s4.onnx','models/s4.pb.gz','reports/quick_compare_dev.txt','reports/C1_LN_outliers.md','reports/trt/s2_other_top15_review.md']:
    p=Path(f);assert p.is_file() and p.stat().st_size>0,f'missing/empty {f}'
lines=['# C1-done review','','C1-day1 explicitly approved by user; day-1 summary copied verbatim into LOG.md. Pre-flight dependencies and configured paths verified. No pipeline code/config edited in this turn.','',
'build --only s4, hw --parts bench, and study --models fp16 --limit 50 all exited 0.','',
'| Model | Search nps | Raw batch-256 nps | Search SM mean MHz | Search SM min MHz | Search max C |','|---|---|---|---|---|---|']
for n in ['fp16','native','s4']:
    d=json.loads(Path(f'reports/bench/{n}.json').read_text());r=d['search'][0];e=r['energy'];raw=next(x['nps'] for x in d['backendbench']['rows'] if x['batch']==256)
    lines.append(f'| {n} | {r["nps"]} | {raw:.0f} | {e["sm_mhz_mean"]:.2f} | {e["sm_mhz_min"]} | {e["temp_c_max"]} |')
lines += ['', 'Clock locking was optional and was not attempted. Recorded clocks are shown above. All saved bench and study warning lists were empty.','',
'## Study B sizing','',f'Final progress: `{progress.strip()}`','',
'This progress measures all budgets 100, 400, 800, 1600 together per position. It is not the 1600-node-only cost.',
f'At the 1600-node budget: mean wall **{meanwall:.6f} s/position**; mean lc0-reported time **{meanlc0:.6f} s/position**, over {len(b)} positions.',
f'Actual nodes: min {min(r["nodes"] for r in b)}, mean {meannodes:.2f}, max {max(r["nodes"] for r in b)}. Threads=1, MinibatchSize=256, SmartPruningFactor=0; test split.',
'', 'No overnight study size selected and no timing extrapolation made.','',
'## LN outputs','',
'FFN input encoder ln1: 20.0..69.0 before -> 3.2..5.2 after SmoothQuant.',
'QKV input LN outputs: 4.6..20.4 before -> 3.5..4.4 after.',
'Smolgen ln1: 2.1..5.4 before -> 2.3..5.2 after.',
'Head-feeding /encoder14/ln2: 665019.9 -> 124666.6 (max 52.76, median 7.933e-05 before smoothing).',
'Full per-output ratios: reports/C1_LN_outliers.md. Original: reports/outliers.txt.','',
'## Resume commands (from leela-int8)','',
'`..\\.venv\\Scripts\\python.exe -u ladder.py hw --parts bench` reruns the bench sequence; existing benchmark JSON is not a skip condition.',
'`..\\.venv\\Scripts\\python.exe -u ladder.py study --models fp16 --limit 50` skips completed position/budget records.',
'',Path('reports/trt/s2_other_top15_review.md').read_text()]
report='\n'.join(lines)+'\n';p=Path('reports/C1-done.md');p.write_text(report)
print(report);print('Produced:',p.resolve())
~~~
Exit code: 0
Output:
~~~
Study B budget 100 records: 50 distinct positions: 50
Study B budget 400 records: 50 distinct positions: 50
Study B budget 800 records: 50 distinct positions: 50
Study B budget 1600 records: 50 distinct positions: 50
Study meta: {"name": "fp16", "weights": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\fp16.pb.gz", "backend": "onnx-trt", "backend_opts": "optimize=6", "threads": 1, "minibatch": 256, "split": "test", "n_positions": 50, "move_overhead": 20, "host": "Anjans-Omen", "started": "2026-10-28 00:42:57", "warnings": [], "finished": "2026-10-28 00:43:51"}
Study B final progress:   [fp16 B] 50/50  0.94s/item  eta 0.0 min
1600-node budget: mean wall s/position=0.341638; mean lc0 s/position=0.340760; positions=50
1600-node budget actual nodes: min=1601; mean=1811.38; max=2200
Step exit codes: {"C1-build": "0", "C1-hw-bench": "0", "C1-study-fp16-50": "0"}
Day-1 summary verbatim check: passed
# C1-done review

C1-day1 explicitly approved by user; day-1 summary copied verbatim into LOG.md. Pre-flight dependencies and configured paths verified. No pipeline code/config edited in this turn.

build --only s4, hw --parts bench, and study --models fp16 --limit 50 all exited 0.

| Model | Search nps | Raw batch-256 nps | Search SM mean MHz | Search SM min MHz | Search max C |
|---|---|---|---|---|---|
| fp16 | 4349 | 3176 | 2175.43 | 1875 | 87 |
| native | 4358 | 3067 | 2159.27 | 1725 | 87 |
| s4 | 5685 | 4239 | 2268.68 | 1965 | 87 |

Clock locking was optional and was not attempted. Recorded clocks are shown above. All saved bench and study warning lists were empty.

## Study B sizing

Final progress: `[fp16 B] 50/50  0.94s/item  eta 0.0 min`

This progress measures all budgets 100, 400, 800, 1600 together per position. It is not the 1600-node-only cost.
At the 1600-node budget: mean wall **0.341638 s/position**; mean lc0-reported time **0.340760 s/position**, over 50 positions.
Actual nodes: min 1601, mean 1811.38, max 2200. Threads=1, MinibatchSize=256, SmartPruningFactor=0; test split.

No overnight study size selected and no timing extrapolation made.

## LN outputs

FFN input encoder ln1: 20.0..69.0 before -> 3.2..5.2 after SmoothQuant.
QKV input LN outputs: 4.6..20.4 before -> 3.5..4.4 after.
Smolgen ln1: 2.1..5.4 before -> 2.3..5.2 after.
Head-feeding /encoder14/ln2: 665019.9 -> 124666.6 (max 52.76, median 7.933e-05 before smoothing).
Full per-output ratios: reports/C1_LN_outliers.md. Original: reports/outliers.txt.

## Resume commands (from leela-int8)

`..\.venv\Scripts\python.exe -u ladder.py hw --parts bench` reruns the bench sequence; existing benchmark JSON is not a skip condition.
`..\.venv\Scripts\python.exe -u ladder.py study --models fp16 --limit 50` skips completed position/budget records.

# Top 15 kernels tagged other

Shares are of ALL captured GPU kernel time; labels are name-based inference, not measured operand precision.

| Rank | Total ns | Share | Looks like | Kernel |
|---|---|---|---|---|
| 1 | 447450214 | 6.2223% | non-matmul (name-based) | `__myl_CastMul_0x9698266d4f8a2c42b3ee5030474f1e88_com_vec` |
| 2 | 376231329 | 5.2319% | non-matmul (name-based) | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce7fb8c_com_vec` |
| 3 | 319075746 | 4.4371% | non-matmul (name-based) | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_com_vec` |
| 4 | 302974486 | 4.2132% | non-matmul (name-based) | `__myl_CastMulAddReshTranReshMove_0x0340c5e5be98d9cff14028d435e46a87_com_vec` |
| 5 | 169936666 | 2.3632% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x5670ba801b2de8a2907d63de1165fdb4` |
| 6 | 154229791 | 2.1447% | non-matmul (name-based) | `__myl_CastMulAddReshTranReshMove_0x132535db0b518e0a175a5158bc1b1139_com_vec` |
| 7 | 133882345 | 1.8618% | non-matmul (name-based) | `__myl_CastMulCastMulAddMulAddCastMeanSubMulMeanAddSqrtDivMulCastMulAddMulMinMaxRounCast_0x7d9dc8b2a4e3ffac3b84e7a66ce7fb8c_vec` |
| 8 | 103491656 | 1.4392% | non-matmul (name-based) | `__myl_CastMulAddExpAddLogLteSeleTanhMulMulMinMaxRounCast_0xa9ff92d6c7fc01b18f5015381215a0db_vec` |
| 9 | 88060935 | 1.2246% | non-matmul (name-based) | `__myl_MoveReshTran_0x7bfad93cb08ea2697ad4d01ea85ce2ff_com_vec` |
| 10 | 84982118 | 1.1818% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x1fe1cc1fc70208fa1b2cf8ace9d12c4f` |
| 11 | 84982039 | 1.1818% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x7f1aba88ddd93d06bfd656f26231a9bf` |
| 12 | 84979997 | 1.1817% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0xa3cb0d93fdf10f031368b0c1d43bf756` |
| 13 | 84970010 | 1.1816% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x4362f572a7cf6cb4ad2c8c19dbcd894e` |
| 14 | 84967008 | 1.1816% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x188def927c4090eca727b3bc88fcb84c` |
| 15 | 84964450 | 1.1815% | likely FP16 attention GEMM (s2 has no act-act quantization; name alone unresolved) | `_gemm_mha_v2_0x8e523ab71e8f56bda53303a6b0159433` |

Interpretation: day1.log records s2 as 164 weight nodes + 0 act-act. ladder.py builds s2 with per-channel minmax without --act-act-matmul. The bundled ORT and optimize=8 permit FP16 fallback (README trap 4). Thus the _gemm_mha_v2 entries look like FP16 attention matmuls; this is a contextual inference, not a measured precision. Cast/Mul/Mean/Sqrt/Div/Mish-like, transpose and move kernels are non-matmul even when operating on mixed precision tensors. No classifier or pipeline code changed.


Produced: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\C1-done.md
~~~
Produced: reports/C1-done.md. Read/validated outputs listed above.

## 2026-10-28 00:44:39 +05:30 — checkpoint bookkeeping, stop
Exact PowerShell commands: [IO.File]::ReadAllText(STATUS.md); replace completed hw result, recorded-clock wording, and pending C1-done row with the rows pasted below; [IO.File]::WriteAllText(STATUS.md, status); Write-Output status.
Exit code: 0
Output:
~~~
# STATUS

Machine: RTX 4060 Laptop (HP), Windows 11. Updated 2026-10-28. Commands and evidence: LOG.md.

| Gate / step | State | Result |
|---|---|---|
| 0 Inventory | done | RTX 4060 Laptop 8188 MiB, driver 592.82 (CUDA 13.1); Python 3.11.9; Windows lc0 v0.33.0-rc0 onnx-trt (new download, `..\tools\lc0`); trtexec TRT 10.12.0.36; nsys 2025.1.3; BT3 sha256 matches Anjan's; Syzygy 3-4-5 290 files |
| 1a config.json | done | from config.example.json; lc0, trtexec, nsys, syzygy paths changed (diff in LOG.md) |
| 1b pip install -r requirements.txt | done | into `..\.venv` (Python 3.11.9); onnxruntime 1.31.1 (CPU), onnx 1.23.2, numpy 2.4.6 |
| 1c onnx-trt smoke test | done | `lc0 benchmark` on bundled 791556.pb.gz, optimize=6: 10534 nodes, 13698 nps, no FP32 warning |
| 1d describenet BT3 | done | INPUT_CLASSICAL_112_PLANE (traps 5/10 do not apply); 15 enc, 24 heads, 768, DFF 1024; exit 0 |
| 1e tbset | done | 11200 positions: calib 1120 / dev 3360 / test 6720; won 6803, drawn 4397 |
| 1f calib | done | calib.npz 512 positions, dev.npz 3360 positions, both input format 1 |
| 1g day1 | done | day1.log: wrapped/native KL 0.00e+00, top-1 1.000; INT8 runs; GEMM-like INT8 73.5% |
| CHECKPOINT C1-day1 | done | passed — explicitly approved by user on 2026-10-28; verbatim summary in LOG.md |
| Bookkeeping typo retry | done | Initial command BLOCKED at parsing: Missing closing parenthesis; one obvious-typo retry succeeded, no pipeline commands had run |
| Pre-flight C1 step 2 | done | Prior inventory/install/tbset/calib/day1 verified; paths exist, pip check passed, GPU idle, BatteryStatus 2; optional clock lock omitted, measured clocks recorded in reports/bench/*.json |
| Other-kernel review | done | reports/trt/s2_other_top15_review.md; labels inferred from names; pipeline code unchanged |
| 2a build --only s4 | done | Exit 0; reports/outliers.txt, models/s4.onnx, models/s4.pb.gz, reports/quick_compare_dev.txt |
| 2b hw --parts bench | done | Exit 0; search nps fp16 4349, native 4358, s4 5685; reports/bench/*.json; warnings empty |
| 2c study --models fp16 --limit 50 | done | Exit 0; results/fp16/study_b.jsonl; see reports/logs/C1-study-fp16-50.log for progress timing |
| CHECKPOINT C1-done | done | CHECKPOINT C1-done: ready for review; reports/C1-done.md; stopped awaiting user |
| 3-5 | todo | Await checkpoint approval |
| Prior-session review note 1 | done | `..\.venv`, `..\tools`, `..\syzygy` were created by the agent in this session (23:22-23:38), not earlier by someone else as AGENTS.md says. |
| Prior-session review note 2 | done | lc0, the CUDA/cuDNN/TRT DLLs, trtexec and nsys were downloaded: no Windows GPU lc0, trtexec or nsys existed on the machine, and Anjan's WSL lc0 is CPU-only (eigen). |
| Prior-session review note 3 | done | Syzygy was copied from Anjan's WSL env into `..\syzygy` rather than used by path. |
| Prior-session review note 4 | done | Exit codes for tbset, the smoke test and calib were not captured separately (output was piped to `tail`); see LOG.md. |

~~~
Updated: STATUS.md, LOG.md. CHECKPOINT C1-done: ready for review. No further pipeline steps run.

## 2026-10-28 01:37:45 +05:30 — C2 initial inspection / sidecar filename typo
Exact command (cwd leela-int8): Get-Content STATUS.md; Get-Content LOG.md -Tail 180; Get-Content config.json; rg --files -g AGENTS.md; rg -n 'outlier|channel|maxima|one-shot|sequential|stage|providers|smooth|s4_alpha|def step_select|def step_build|def step_study|def recipe_flags|exists|force' quant/quantize.py quant/sparsegpt24.py eval/quick_compare.py ladder.py; Get-ChildItem models/s4*; Get-Content models/s4.onnx.json -ErrorAction SilentlyContinue
Exit code: 1
Key output:
~~~
| CHECKPOINT C1-done | done | CHECKPOINT C1-done: ready for review; reports/C1-done.md; stopped awaiting user |
s4.json 50144 bytes; s4.onnx 105829506 bytes; s4.pb.gz 92783432 bytes.
~~~
Error: final read used models/s4.onnx.json; actual sidecar listed by Get-ChildItem is models/s4.json. Error was suppressed by -ErrorAction SilentlyContinue; no pipeline ran. The AGENTS.md filename search had no matches below leela-int8 (root AGENTS.md is already read). One permitted obvious filename-typo retry follows. Produced: LOG.md and BLOCKED status row.

## 2026-10-28 01:37:45 +05:30 — one permitted sidecar typo retry
Exact command: Get-Content models/s4.json -Raw | ConvertFrom-Json | Select-Object granularity,method,percentile,smoothquant,act_act_matmul,n_quantize_linear
Exit code: 0
Output:
~~~

granularity       : per-channel
method            : percentile
percentile        : 99.99
smoothquant       : 0.5
act_act_matmul    : False
n_quantize_linear : 280


~~~
Produced: LOG.md entry only.

## 2026-10-28 01:37:45 +05:30 — CPU inspection and selection implementation
Exact command: Get-Content quant/quantize.py; Get-Content eval/quick_compare.py; Get-Content quant/sparsegpt24.py; Get-Content common.py; Get-Content AGENTS.md files beneath workspace root, if present
Exit code: 0
Output:
~~~
#!/usr/bin/env python3
"""W8A8 QDQ ONNX for TensorRT explicit quantization.

Ladder knobs: --granularity per-tensor|per-channel (weights), --method
minmax|percentile|entropy (activations), --smoothquant ALPHA, and
--act-act-matmul (also quantize Q·Kᵀ and attn·V, which have no weights).

Only weight-carrying MatMul/Gemm/Conv are quantized by default; everything
else stays in the engine's float precision. All Q/DQ are symmetric int8
(zero point 0), which is what TensorRT accepts.

Trap 2: ONNX Runtime's entropy calibration is unusable here (defaults leave
one candidate threshold, i.e. max calibration; more bins make its first
candidate a no-merge slice and it clips everything to 1/8 of max). So ORT
always calibrates minmax (it places Q/DQ and sets weight scales), and
percentile / entropy activation thresholds are computed here from |x|
histograms (TensorRT's legacy entropy method, 2048 bins, zero bin excluded)
and written into the activation scale initializers.

SmoothQuant: for each group of weight matmuls reading the same activation X,
s_j = max|X_j|^a / max|W_j|^(1-a); W rows are multiplied by s and an explicit
Mul(X, 1/s) is inserted on the branch feeding that group. Folding 1/s into the
preceding LayerNorm is not possible in lc0's graphs: the LN output also feeds
the residual skip. Groups whose weight initializer is shared with matmuls
outside the group (smolgen's global weight) are left alone.

    python quant/quantize.py --onnx models/bt3_fp32.onnx --calib data/calib.npz \
        --out models/s4.onnx --granularity per-channel --method percentile \
        --percentile 99.99 --smoothquant 0.5 --outlier-report reports/outliers.txt
"""
import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import onnx
from onnx import helper, numpy_helper

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (INPUT, act_act_matmuls, consumers, initializers,  # noqa: E402
                    load_onnx, ort_session, save_onnx, weight_input, weight_nodes)

BATCH = 32


# ------------------------------------------------------------------ data
def load_planes(npz, n=0):
    d = np.load(npz)
    x = d["planes"].astype(np.float32)
    if n:
        x = x[:n]
    return x


def batches(x, bs=BATCH):
    for i in range(0, len(x), bs):
        yield x[i:i + bs]


def with_outputs(model, names):
    m = onnx.ModelProto()
    m.CopyFrom(model)
    have = {o.name for o in m.graph.output}
    for n in names:
        if n not in have:
            m.graph.output.append(helper.make_tensor_value_info(n, onnx.TensorProto.FLOAT, None))
    return m


def run_collect(model, planes, names, fn, cpu=True):
    """Run `model` over planes, calling fn(name, array) per batch."""
    names = list(dict.fromkeys(names))
    chunk = 64  # cap extra outputs per session to bound memory
    for c in range(0, len(names), chunk):
        sub = names[c:c + chunk]
        s = _session(with_outputs(model, sub), cpu)
        for xb in batches(planes):
            outs = s.run(sub, {INPUT: xb})
            for n, o in zip(sub, outs):
                fn(n, o)


def _session(model, cpu):
    if model.ByteSize() < 1.8e9:
        return ort_session(model, cpu=cpu)
    tmp = Path(tempfile.mkdtemp()) / "m.onnx"
    save_onnx(model, tmp)
    return ort_session(tmp, cpu=cpu)


# ------------------------------------------------------------------ stats
def channel_amax(model, planes, tensors, axis_of):
    amax = {}

    def fn(n, o):
        ax = axis_of[n] % o.ndim
        red = tuple(i for i in range(o.ndim) if i != ax)
        v = np.abs(o).max(axis=red)
        amax[n] = v if n not in amax else np.maximum(amax[n], v)

    run_collect(model, planes, tensors, fn)
    return amax


def abs_histograms(model, planes, tensors, bins=2048):
    amax = {}
    run_collect(model, planes, tensors,
                lambda n, o: amax.__setitem__(n, max(amax.get(n, 0.0), float(np.abs(o).max()))))
    hist = {t: np.zeros(bins, dtype=np.float64) for t in tensors}

    def fn(n, o):
        if amax[n] > 0:
            h, _ = np.histogram(np.abs(o), bins=bins, range=(0, amax[n]))
            hist[n] += h

    run_collect(model, planes, tensors, fn)
    return amax, hist


def percentile_amax(hist, amax, pct):
    c = np.cumsum(hist)
    if c[-1] == 0:
        return amax
    i = int(np.searchsorted(c, c[-1] * pct / 100.0))
    return min(amax, (i + 1) * amax / len(hist))


def entropy_amax(hist, amax, nq=128, start=128):
    """TensorRT's legacy entropy calibration, matching pytorch-quantization's
    _compute_amax_entropy for a symmetric int8 tensor (|x| histogram, 128
    levels, stride 1), including its zero-spike suppression (bin 0 set to
    bin 1: ReLU/mish outputs pile up at zero, which is exact in int8)."""
    h = hist.astype(np.float64).copy()
    if len(h) > 1:
        h[0] = h[1]
    nb = len(h)
    if h.sum() == 0:
        return amax
    best_kl, best_i = np.inf, nb
    for i in range(start, nb + 1):
        hb = h[:i]
        nz = hb != 0
        g = (np.arange(i) * nq) // i                 # = digitize(range(i), linspace(0,i,nq+1)) - 1
        qb = np.bincount(g, weights=hb, minlength=nq)
        cnt = np.bincount(g, weights=nz.astype(np.float64), minlength=nq)
        per = np.divide(qb, cnt, out=np.zeros_like(qb), where=cnt > 0)
        q = per[g] * nz
        p = hb.copy()
        p[-1] += h[i:].sum()
        ps, qs = p / p.sum(), q / q.sum()
        mask = ps > 0
        if (qs[mask] == 0).any():
            continue                                 # KL = inf
        kl = float(np.sum(ps[mask] * np.log(ps[mask] / qs[mask])))
        if kl < best_kl:
            best_kl, best_i = kl, i
    return best_i * amax / nb


# ------------------------------------------------------------------ smoothquant
def smoothquant(model, planes, alpha, targets):
    """Returns (new_model, report). targets: weight-matmul nodes eligible."""
    inits = initializers(model)
    cons = consumers(model)
    by_input = {}
    for n in targets:
        if n.op_type not in ("MatMul", "Gemm") or weight_input(n, inits) != 1:
            continue
        if n.op_type == "Gemm":
            attrs = {a.name: helper.get_attribute_value(a) for a in n.attribute}
            if attrs.get("transA", 0) or attrs.get("transB", 0):
                continue
        by_input.setdefault(n.input[0], []).append(n)
    w_users = {}
    for n in model.graph.node:
        for i in n.input:
            if i in inits:
                w_users.setdefault(i, set()).add(n.name)
    groups = {}
    for x, nodes in by_input.items():
        names = {n.name for n in nodes}
        if any(w_users[n.input[1]] - names for n in nodes):
            continue
        if len({n.input[1] for n in nodes}) != len(nodes):
            continue
        groups[x] = nodes
    if not groups:
        return model, {}
    amax = channel_amax(model, planes, list(groups), {x: -1 for x in groups})
    m = onnx.ModelProto()
    m.CopyFrom(model)
    inits = initializers(m)
    node_by_name = {n.name: n for n in m.graph.node}
    report = {}
    new_nodes = []
    for x, nodes in groups.items():
        ax = amax[x].astype(np.float64)
        ws = [numpy_helper.to_array(inits[n.input[1]]).astype(np.float64) for n in nodes]
        if any(w.ndim != 2 or w.shape[0] != len(ax) for w in ws):
            continue
        wmax = np.max(np.stack([np.abs(w).max(axis=1) for w in ws]), axis=0)
        s = np.where((ax > 0) & (wmax > 0),
                     np.power(np.maximum(ax, 1e-8), alpha) /
                     np.power(np.maximum(wmax, 1e-8), 1 - alpha), 1.0)
        s = np.clip(s, 1e-4, 1e4)
        for n, w in zip(nodes, ws):
            init = inits[n.input[1]]
            init.CopyFrom(numpy_helper.from_array((w * s[:, None]).astype(np.float32), init.name))
        sname = f"{x}/smooth_inv"
        m.graph.initializer.append(numpy_helper.from_array((1.0 / s).astype(np.float32), sname))
        out = f"{x}/smoothed"
        new_nodes.append((x, helper.make_node("Mul", [x, sname], [out], name=f"{x}/smooth")))
        for n in nodes:
            nn = node_by_name[n.name]
            nn.input[0] = out
        before = ax.max() / max(np.median(ax), 1e-12)
        after_ch = ax / s
        report[x] = {"consumers": [n.name for n in nodes], "outlier_before": float(before),
                     "outlier_after": float(after_ch.max() / max(np.median(after_ch), 1e-12))}
    # Insert each Mul right after its producer to keep the graph sorted.
    prod_pos = {o: i for i, n in enumerate(m.graph.node) for o in n.output}
    nodes = list(m.graph.node)
    for x, node in sorted(new_nodes, key=lambda t: -prod_pos.get(t[0], -1)):
        nodes.insert(prod_pos.get(x, -1) + 1, node)
    del m.graph.node[:]
    m.graph.node.extend(nodes)
    onnx.checker.check_model(m) if m.ByteSize() < 1.8e9 else None
    return m, report


# ------------------------------------------------------------------ outliers
def outlier_report(model, planes, nodes, path, smooth_rep=None):
    inits = initializers(model)
    xs = {}
    for n in nodes:
        if n.op_type in ("MatMul", "Gemm") and weight_input(n, inits) == 1:
            xs.setdefault(n.input[0], []).append(n.name)
        elif n.op_type == "Conv":
            xs.setdefault(n.input[0], []).append(n.name)
    axis = {x: (1 if any(nn.op_type == "Conv" for nn in nodes if nn.input[0] == x) else -1)
            for x in xs}
    amax = channel_amax(model, planes, list(xs), axis)
    rows = []
    for x, a in amax.items():
        # Median over live channels: binary input planes have many all-zero
        # channels, which would make the ratio meaningless.
        live = a[a > 0]
        med = float(np.median(live)) if len(live) else 0.0
        rows.append((float(a.max()) / max(med, 1e-12), x, float(a.max()), med, xs[x]))
    rows.sort(reverse=True)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("# outlier_ratio = worst input channel |x|max / median channel |x|max\n")
        f.write("# tens-to-hundreds on attention/FFN inputs: SmoothQuant has work to do\n")
        f.write(f"{'ratio':>9} {'max':>10} {'median':>10}  tensor -> consumers\n")
        for r, x, mx, med, c in rows:
            f.write(f"{r:9.1f} {mx:10.4g} {med:10.4g}  {x} -> {','.join(c)}\n")
        if smooth_rep:
            f.write("\n# after SmoothQuant (per group)\n")
            for x, v in sorted(smooth_rep.items(), key=lambda kv: -kv[1]["outlier_before"]):
                f.write(f"{v['outlier_before']:9.1f} -> {v['outlier_after']:7.1f}  {x}\n")
    return rows


# ------------------------------------------------------------------ quantize
class Reader:
    def __init__(self, planes):
        self.it = iter(list(batches(planes)))

    def get_next(self):
        b = next(self.it, None)
        return None if b is None else {INPUT: b}

    def rewind(self):
        pass


def ort_quantize(model, planes, nodes, per_channel, tmpdir):
    from onnxruntime.quantization import (CalibrationDataReader, CalibrationMethod,
                                          QuantFormat, QuantType, quantize_static)

    class R(CalibrationDataReader, Reader):
        def __init__(self, p):
            Reader.__init__(self, p)

        def get_next(self):
            return Reader.get_next(self)

    src = Path(tmpdir) / "src.onnx"
    dst = Path(tmpdir) / "q.onnx"
    save_onnx(model, src)
    quantize_static(
        str(src), str(dst), R(planes),
        quant_format=QuantFormat.QDQ,
        activation_type=QuantType.QInt8, weight_type=QuantType.QInt8,
        per_channel=per_channel,
        calibrate_method=CalibrationMethod.MinMax,
        op_types_to_quantize=["MatMul", "Gemm", "Conv"],
        nodes_to_quantize=[n.name for n in nodes],
        use_external_data_format=model.ByteSize() > 1.8e9,
        extra_options={"ActivationSymmetric": True, "WeightSymmetric": True,
                       "QDQOpTypePerChannelSupportToAxis": {"MatMul": 1},
                       "CalibMovingAverage": False})
    return onnx.load(str(dst), load_external_data=True)


def activation_scales(qmodel):
    """activation tensor -> scale initializer name, for scalar activation Q."""
    inits = initializers(qmodel)
    out = {}
    for n in qmodel.graph.node:
        if n.op_type == "QuantizeLinear" and n.input[0] not in inits \
                and n.input[1] in inits \
                and numpy_helper.to_array(inits[n.input[1]]).size == 1:
            out.setdefault(n.input[0], n.input[1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--onnx", required=True)
    ap.add_argument("--calib", required=True)
    ap.add_argument("--calib-n", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--granularity", choices=["per-tensor", "per-channel"], default="per-channel")
    ap.add_argument("--method", choices=["minmax", "percentile", "entropy"], default="minmax")
    ap.add_argument("--percentile", type=float, default=99.99)
    ap.add_argument("--smoothquant", type=float, default=None, metavar="ALPHA")
    ap.add_argument("--act-act-matmul", action="store_true",
                    help="also quantize Q·Kᵀ / attn·V / policy Q·Kᵀ")
    ap.add_argument("--exclude", default=None, help="regex on node names to keep float")
    ap.add_argument("--outlier-report", default=None)
    a = ap.parse_args()
    t0 = time.time()

    model = load_onnx(a.onnx)
    planes = load_planes(a.calib, a.calib_n)
    print(f"{len(planes)} calibration positions from {a.calib}", file=sys.stderr)
    targets = weight_nodes(model)
    if a.exclude:
        targets = [n for n in targets if not re.search(a.exclude, n.name)]

    smooth_rep = {}
    if a.smoothquant is not None:
        model, smooth_rep = smoothquant(model, planes, a.smoothquant, targets)
        print(f"SmoothQuant alpha={a.smoothquant}: {len(smooth_rep)} groups smoothed",
              file=sys.stderr)
        names = {n.name for n in targets}
        targets = [n for n in model.graph.node if n.name in names]
    if a.outlier_report:
        # Outliers are a property of the original net; report on it, plus the
        # post-smoothing ratios if SmoothQuant ran.
        orig = load_onnx(a.onnx)
        on = {n.name for n in targets}
        outlier_report(orig, planes, [n for n in orig.graph.node if n.name in on],
                       a.outlier_report, smooth_rep)
        print(f"outlier report -> {a.outlier_report}", file=sys.stderr)

    qnodes = list(targets)
    aa = []
    if a.act_act_matmul:
        aa = [n for n in act_act_matmuls(model)
              if not (a.exclude and re.search(a.exclude, n.name))]
        qnodes += aa
    with tempfile.TemporaryDirectory() as td:
        q = ort_quantize(model, planes, qnodes, a.granularity == "per-channel", td)

    scales = activation_scales(q)
    clip = {}
    if a.method != "minmax":
        # The input planes are binary (plus a few scalars): minmax is exact
        # for them and clipping them only destroys information.
        tensors = sorted(t for t in scales if t in {o for n in model.graph.node for o in n.output})
        amax, hist = abs_histograms(model, planes, tensors)
        inits = initializers(q)
        for t in tensors:
            if amax[t] == 0:
                continue
            thr = (percentile_amax(hist[t], amax[t], a.percentile) if a.method == "percentile"
                   else entropy_amax(hist[t], amax[t]))
            init = inits[scales[t]]
            old = numpy_helper.to_array(init)
            init.CopyFrom(numpy_helper.from_array((old * (thr / amax[t])).astype(old.dtype), init.name))
            h = hist[t]
            above = h[int(np.floor(thr / amax[t] * len(h))):].sum() / max(h.sum(), 1)
            clip[t] = {"ratio": float(thr / amax[t]), "clipped_frac": float(above)}
        r = np.array([v["ratio"] for v in clip.values()]) if clip else np.array([1.0])
        print(f"{a.method}: median range ratio {np.median(r):.3f}, min {r.min():.3f} "
              f"over {len(clip)} activations", file=sys.stderr)

    save_onnx(q, a.out)
    n_q = sum(1 for n in q.graph.node if n.op_type == "QuantizeLinear")
    side = {"source": str(a.onnx), "calib": str(a.calib), "n_calib": int(len(planes)),
            "granularity": a.granularity, "method": a.method,
            "percentile": a.percentile if a.method == "percentile" else None,
            "smoothquant": a.smoothquant, "act_act_matmul": a.act_act_matmul,
            "exclude": a.exclude, "n_weight_nodes": len(targets), "n_act_act": len(aa),
            "n_quantize_linear": n_q, "smoothed_groups": smooth_rep,
            "activation_clip": clip, "seconds": round(time.time() - t0, 1)}
    with open(Path(a.out).with_suffix(".json"), "w") as f:
        json.dump(side, f, indent=1)
    print(f"wrote {a.out}: {len(targets)} weight nodes + {len(aa)} act-act, "
          f"{n_q} QuantizeLinear ({time.time() - t0:.0f}s)", file=sys.stderr)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Seconds-fast ONNX Runtime comparison of models against a reference on an
.npz of planes (from make_calib.py). For choosing ladder knobs on the dev
split; NOT a reported result (ORT's int8 kernels are not TensorRT's).

Reports policy KL(ref||model) over legal moves, top-1 agreement, mean |ΔV|
(V = W - L), and, for tablebase positions, raw-policy tablebase accuracy.

    python eval/quick_compare.py --ref models/fp32.onnx --npz data/dev.npz \
        --tbset data/tbset.jsonl models/s1.onnx models/s2.onnx ...
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import INPUT, OUT_POLICY, OUT_WDL, ort_session, read_jsonl  # noqa: E402


def run(path, planes, cpu, bs=64):
    s = ort_session(path, cpu=cpu)
    pol, wdl = [], []
    for i in range(0, len(planes), bs):
        p, w = s.run([OUT_POLICY, OUT_WDL], {INPUT: planes[i:i + bs]})[:2]
        pol.append(p)
        wdl.append(w)
    return np.concatenate(pol), np.concatenate(wdl)


def legal_softmax(pol, legal):
    out = []
    for p, idx in zip(pol, legal):
        idx = idx[idx >= 0]
        lg = p[idx].astype(np.float64)
        e = np.exp(lg - lg.max())
        out.append(e / e.sum())
    return out


def compare(ref, mod, wref, wmod, ucis, tb, tb_ids):
    kl, agree, dv, acc, n_tb = [], 0, [], 0, 0
    for i, (p, q) in enumerate(zip(ref, mod)):
        kl.append(float(np.sum(p * (np.log(np.maximum(p, 1e-12)) - np.log(np.maximum(q, 1e-12))))))
        agree += int(np.argmax(p) == np.argmax(q))
        dv.append(abs((wref[i][0] - wref[i][2]) - (wmod[i][0] - wmod[i][2])))
        if tb is not None and tb_ids[i] in tb:
            n_tb += 1
            acc += int(ucis[i][int(np.argmax(q))] in tb[tb_ids[i]])
    return {"kl": float(np.mean(kl)), "top1": agree / len(ref), "dv": float(np.mean(dv)),
            "tb_acc": acc / n_tb if n_tb else float("nan"), "n_tb": n_tb}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--npz", required=True)
    ap.add_argument("--tbset", default=None)
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--out", default=None, help="also write the table here")
    ap.add_argument("models", nargs="+")
    a = ap.parse_args()
    d = np.load(a.npz)
    planes = d["planes"].astype(np.float32)
    legal = d["legal_idx"]
    ucis = [str(u).split() for u in d["legal_uci"]]
    tb = None
    if a.tbset:
        tb = {r["id"]: set(r["correct"]) for r in read_jsonl(a.tbset)}
    tb_ids = d["tb_id"]
    rp, rw = run(a.ref, planes, a.cpu)
    ref = legal_softmax(rp, legal)
    rows = [("ref " + Path(a.ref).name, compare(ref, ref, rw, rw, ucis, tb, tb_ids))]
    for m in a.models:
        mp, mw = run(m, planes, a.cpu)
        rows.append((Path(m).name, compare(ref, legal_softmax(mp, legal), rw, mw, ucis, tb, tb_ids)))
    lines = [f"{len(planes)} positions from {a.npz} (ORT, not TensorRT)",
             f"{'model':28s} {'KL':>9s} {'top1':>6s} {'|dV|':>7s} {'tb_acc':>7s}"]
    for name, r in rows:
        lines.append(f"{name:28s} {r['kl']:9.2e} {r['top1']:6.3f} {r['dv']:7.4f} {r['tb_acc']:7.3f}")
    print("\n".join(lines))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""S1: SparseGPT 2:4 (Frantar & Alistarh, 2023) on every weight-carrying
MatMul/Gemm, no fine-tuning. Output is an FP32 ONNX with the same 2:4
pattern as S0, so speed is identical; only accuracy differs.

Per layer, with H = Xᵀ X from that layer's calibration inputs, columns are
processed left to right in blocks; in each group of 4 input channels the 2
weights with the smallest w² / [H⁻¹]_jj² are zeroed and the OBS update
spreads their error over the not-yet-processed columns.

Sequential (default): layers are pruned in dependency stages and each stage's
inputs are captured from the model with all earlier stages already pruned,
as in the paper. --one-shot captures everything from the dense model in one
pass (faster, slightly worse). Weights shared by several matmuls (smolgen's
global weight) get one H summed over all their consumers, from the dense
model, in the first stage. Conv weights (none in BT3) fall back to magnitude.

    python quant/sparsegpt24.py --onnx models/bt3_fp32.onnx --calib data/calib.npz \
        --out models/s1sp_fp32.onnx
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from onnx import numpy_helper

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import initializers, load_onnx, save_onnx  # noqa: E402
from quantize import load_planes, run_collect  # noqa: E402
from sparse_common import check_24, from_kn, magnitude_mask, targets, to_kn  # noqa: E402


def sparsegpt_24(w_kn, H, blocksize=128, percdamp=0.01):
    """w_kn: [K, N] (y = x @ W). Returns pruned [K, N]."""
    W = w_kn.T.astype(np.float64).copy()          # rows = outputs, cols = inputs
    K = W.shape[1]
    H = H.astype(np.float64).copy()
    dead = np.diag(H) == 0
    H[dead, dead] = 1
    W[:, dead] = 0
    H[np.diag_indices(K)] += percdamp * np.mean(np.diag(H))
    Hinv = np.linalg.cholesky(np.linalg.inv(H)).T  # upper Cholesky of H^-1
    bs = max(4, blocksize - blocksize % 4)
    for i1 in range(0, K, bs):
        i2 = min(i1 + bs, K)
        W1 = W[:, i1:i2].copy()
        Q1 = np.zeros_like(W1)
        E1 = np.zeros_like(W1)
        Hi1 = Hinv[i1:i2, i1:i2]
        dg = np.diag(Hi1)
        mask1 = np.zeros(W1.shape, dtype=bool)
        for i in range(i2 - i1):
            if i % 4 == 0:
                tmp = W1[:, i:i + 4] ** 2 / (dg[i:i + 4][None, :] ** 2)
                idx = np.argsort(tmp, axis=1)[:, :2]
                sub = mask1[:, i:i + 4]
                np.put_along_axis(sub, idx, True, axis=1)
            w = W1[:, i]
            q = w.copy()
            q[mask1[:, i]] = 0
            Q1[:, i] = q
            err = (w - q) / Hi1[i, i]
            W1[:, i:] -= np.outer(err, Hi1[i, i:])
            E1[:, i] = err
        W[:, i1:i2] = Q1
        W[:, i2:] -= E1 @ Hinv[i1:i2, i2:]
    return W.T.astype(np.float32)


def recon_err(w, wp, H):
    d = (w - wp).astype(np.float64)
    num = np.einsum("kn,kj,jn->", d, H, d)
    den = np.einsum("kn,kj,jn->", w.astype(np.float64), H, w.astype(np.float64))
    return float(num / max(den, 1e-30))


def upstream_targets(model, tmap):
    """tensor -> set of target initializers that influence it."""
    node_w = {}
    for w, nodes in tmap.items():
        for n in nodes:
            node_w[n.name] = w
    up = {}
    for n in model.graph.node:  # ONNX graphs are topologically sorted
        s = set()
        for i in n.input:
            s |= up.get(i, set())
        if n.name in node_w:
            s = s | {node_w[n.name]}
        for o in n.output:
            up[o] = s
    return up


def hessians(model, planes, need):
    """need: {weight: [input tensor names]} -> {weight: (H, rows)}"""
    tensors = sorted({t for ts in need.values() for t in ts})
    acc = {t: None for t in tensors}
    rows = {t: 0 for t in tensors}

    def fn(n, o):
        x = o.reshape(-1, o.shape[-1]).astype(np.float64)
        h = x.T @ x
        acc[n] = h if acc[n] is None else acc[n] + h
        rows[n] += x.shape[0]

    run_collect(model, planes, tensors, fn)
    out = {}
    for w, ts in need.items():
        H = sum(acc[t] for t in ts)
        r = sum(rows[t] for t in ts)
        out[w] = (2 * H / max(r, 1), r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--onnx", required=True)
    ap.add_argument("--calib", required=True)
    ap.add_argument("--calib-n", type=int, default=0,
                    help="0 = all; smolgen's dense1 gets ONE row per position, so it needs many")
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip", default=None)
    ap.add_argument("--one-shot", action="store_true")
    ap.add_argument("--blocksize", type=int, default=128)
    ap.add_argument("--damp", type=float, default=0.01)
    a = ap.parse_args()
    t0 = time.time()
    m = load_onnx(a.onnx)
    planes = load_planes(a.calib, a.calib_n)
    tmap = targets(m, a.skip)
    inits = initializers(m)
    rep = {}

    def prune(w, H, rows):
        nodes = tmap[w]
        op = nodes[0].op_type
        W = numpy_helper.to_array(inits[w]).astype(np.float32)
        kn = to_kn(W, op)
        mag = np.where(magnitude_mask(kn), kn, 0).astype(np.float32)
        if op == "Conv" or H is None:
            p = mag
            meth = "magnitude"
        else:
            if rows < 2 * kn.shape[0]:
                print(f"  warning: {w}: {rows} calibration rows for K={kn.shape[0]} inputs; "
                      "H is poorly conditioned, so SparseGPT may overfit this layer "
                      "(more calibration positions help)", file=sys.stderr)
            p = sparsegpt_24(kn, H, a.blocksize, a.damp)
            meth = "sparsegpt"
        assert check_24(p), w
        inits[w].CopyFrom(numpy_helper.from_array(from_kn(p, op, W.shape).astype(np.float32), w))
        r = {"nodes": [n.name for n in nodes], "method": meth, "rows": rows}
        if H is not None:
            r["recon_err"] = recon_err(kn, p, H)
            r["recon_err_magnitude"] = recon_err(kn, mag, H)
        rep[w] = r

    mm = {w: ns for w, ns in tmap.items() if ns[0].op_type != "Conv"}
    for w in set(tmap) - set(mm):
        prune(w, None, 0)
    shared = [w for w, ns in mm.items() if len(ns) > 1]
    single = [w for w, ns in mm.items() if len(ns) == 1]
    need = {w: [n.input[0] for n in mm[w]] for w in mm}

    if a.one_shot:
        Hs = hessians(m, planes, need)
        for w in mm:
            prune(w, *Hs[w])
        stages = 1
    else:
        done = set(tmap) - set(mm)   # convs were pruned (magnitude) above
        stages = 0
        if shared:
            Hs = hessians(m, planes, {w: need[w] for w in shared})
            for w in shared:
                prune(w, *Hs[w])
            done |= set(shared)
            stages += 1
        pending = list(single)
        while pending:
            up = upstream_targets(m, tmap)
            ready = [w for w in pending
                     if all(up.get(t, set()) <= done for t in need[w])]
            if not ready:
                raise RuntimeError("dependency cycle among targets: " + ", ".join(pending[:5]))
            Hs = hessians(m, planes, {w: need[w] for w in ready})
            for w in ready:
                prune(w, *Hs[w])
            done |= set(ready)
            pending = [w for w in pending if w not in done]
            stages += 1
            print(f"  stage {stages}: {len(ready)} layers, {len(pending)} left "
                  f"({time.time() - t0:.0f}s)", file=sys.stderr)
    save_onnx(m, a.out)
    errs = [(v["recon_err"], v["recon_err_magnitude"]) for v in rep.values() if "recon_err" in v]
    side = {"method": "sparsegpt 2:4", "one_shot": a.one_shot, "stages": stages,
            "n_calib": int(len(planes)), "blocksize": a.blocksize, "damp": a.damp,
            "skip": a.skip, "layers": rep, "seconds": round(time.time() - t0, 1)}
    with open(Path(a.out).with_suffix(".json"), "w") as f:
        json.dump(side, f, indent=1)
    if errs:
        e = np.array(errs)
        print(f"pruned {len(rep)} weights in {stages} stages; median layer reconstruction "
              f"error {np.median(e[:, 0]):.4f} (magnitude would be {np.median(e[:, 1]):.4f}) "
              f"-> {a.out} ({time.time() - t0:.0f}s)", file=sys.stderr)


if __name__ == "__main__":
    main()
"""Shared helpers: ONNX I/O, lc0 tensor names, jsonl, small stats."""
import json
import math
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Tensor names produced by `lc0 leela2onnx` (checked against v0.33).
INPUT = "/input/planes"
OUT_POLICY = "/output/policy"
OUT_WDL = "/output/wdl"
OUT_MLH = "/output/mlh"

WEIGHT_OPS = ("MatMul", "Gemm", "Conv")


# ------------------------------------------------------------------ jsonl
def read_jsonl(path):
    out = []
    p = Path(path)
    if not p.exists():
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # A run killed mid-write leaves a torn last line; skip it.
                continue
    return out


def append_jsonl(path, rec):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
        f.flush()
        os.fsync(f.fileno())


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


# ------------------------------------------------------------------ onnx
def load_onnx(path, load_data=True):
    import onnx
    return onnx.load(str(path), load_external_data=load_data)


def save_onnx(model, path):
    """Save, switching to external data above ~1.8 GB (protobuf's 2 GB cap).
    Saves a copy so the caller's in-memory model keeps inline tensors."""
    import onnx
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    size = model.ByteSize()
    if size < 1.8e9:
        onnx.save(model, str(path))
        return
    m = onnx.ModelProto()
    m.CopyFrom(model)
    data = path.name + ".data"
    if (path.parent / data).exists():
        (path.parent / data).unlink()
    onnx.save(m, str(path), save_as_external_data=True,
              all_tensors_to_one_file=True, location=data, size_threshold=1024)


def initializers(model):
    return {i.name: i for i in model.graph.initializer}


def producers(model):
    return {o: n for n in model.graph.node for o in n.output}


def consumers(model):
    c = {}
    for n in model.graph.node:
        for i in n.input:
            c.setdefault(i, []).append(n)
    return c


def weight_input(node, inits):
    """Index of the constant weight input of a MatMul/Gemm/Conv, or None.
    Follows nothing: leela2onnx feeds weights straight from initializers
    (possibly through a Cast for fp16 graphs, which we do not quantize)."""
    if node.op_type not in WEIGHT_OPS:
        return None
    if node.op_type in ("Conv",):
        return 1 if len(node.input) > 1 and node.input[1] in inits else None
    if node.op_type == "Gemm":
        return 1 if node.input[1] in inits else None
    # MatMul: weight is normally the second input.
    if node.input[1] in inits:
        return 1
    if node.input[0] in inits:
        return 0
    return None


def weight_nodes(model):
    inits = initializers(model)
    return [n for n in model.graph.node if weight_input(n, inits) is not None]


def act_act_matmuls(model):
    inits = initializers(model)
    return [n for n in model.graph.node
            if n.op_type == "MatMul" and n.input[0] not in inits
            and n.input[1] not in inits]


def ort_session(model_or_path, cpu=False, threads=0):
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    if threads:
        so.intra_op_num_threads = threads
    so.log_severity_level = 3
    provs = ["CPUExecutionProvider"]
    if not cpu:
        avail = ort.get_available_providers()
        if "CUDAExecutionProvider" in avail:
            provs = ["CUDAExecutionProvider"] + provs
    src = model_or_path
    if not isinstance(src, (str, Path)):
        if src.ByteSize() > 1.8e9:
            raise RuntimeError("model >1.8GB: save to disk and pass the path")
        src = src.SerializeToString()
    else:
        src = str(src)
    return ort.InferenceSession(src, so, providers=provs)


# ------------------------------------------------------------------ stats
def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def bootstrap_ci(values, stat=None, iters=2000, seed=0, alpha=0.05):
    import numpy as np
    v = np.asarray(values, dtype=float)
    if len(v) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(iters, len(v)))
    s = v[idx].mean(axis=1) if stat is None else np.array([stat(v[i]) for i in idx])
    return (float(np.quantile(s, alpha / 2)), float(np.quantile(s, 1 - alpha / 2)))


def die(msg):
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)


def seeded(seed):
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
C:\Users\HP\Desktop\LC0-B\AGENTS.md
# Rules for this folder (Leela INT8 pipeline, Person B work)

Read README.md and RUN_4060.md first. The README's "Traps" list is binding: do not work around it.

Scope
- Write only inside this folder. C:\Users\HP\Desktop\LC0 and the WSL env under /home/anjanrd/.local/share/lc0-int8 are Anjan's frozen run: read-only. Reuse his installs (lc0 build, TensorRT, checkpoint, Syzygy) by path; don't re-download if one works.
- No git commit or push. No config or code change to quant/, eval/ or tb/ logic without logging the diff in LOG.md.
- One GPU job at a time. Run nvidia-smi first; if the GPU is busy, wait.

Evidence
- Never state a number you did not see printed by a command. No estimates, no "should be".
- Append to LOG.md after every step: time, exact command, exit code, the key output lines (paste them), and the path of any file produced.
- Keep STATUS.md as a table: gate/step, state (todo / running / done / BLOCKED), one-line result.

Stop rules
- On the first failure: write BLOCKED plus the error to STATUS.md and stop. Do not try alternative fixes beyond one retry of an obvious typo.
- After each checkpoint below, write "CHECKPOINT <name>: ready for review" in STATUS.md and stop. Wait for me.
- Long jobs (study, studyc, match, hw) run in the background with output to a log file. They are resumable; say which command resumes them.

Order
0. Inventory: nvidia-smi + driver, python, lc0 (Windows and/or WSL, onnx-trt works?), trtexec, nsys, BT3 checkpoint, Syzygy 3-4-5 path. Write it to STATUS.md.
1. config.json, pip install -r requirements.txt, then tbset, calib, day1.  CHECKPOINT C1-day1
2. build --only s4 (outlier report), hw --parts bench, study --models fp16 --limit 50 (size Study B).  CHECKPOINT C1-done
3. select, select --alpha, set recipe in config.json from the reports.  CHECKPOINT C2-select
4. build, then study (overnight), then score.  CHECKPOINT C2-done
5. studyc, match --estimate 2, match, hw.  CHECKPOINT C3
Layout: ladder.py, README.md, RUN_4060.md, quant\, eval\, hw\, tb\ are in .\leela-int8\ - run ladder.py from there. Keep LOG.md and STATUS.md in .\leela-int8\.
The .venv\, tools\ and syzygy\ folders here were set up earlier by someone else. Inventory them in step 0 before reusing them; do not assume they are complete or correct.

~~~
Updated: LOG.md, STATUS.md. No source edits.

## 2026-10-28 01:38:39 +05:30 — C2 graph topology, CPU providers, study arithmetic
Exact command: following Python via here-string piped to ..\.venv\Scripts\python.exe -
~~~python
import json
from pathlib import Path
from decimal import Decimal, ROUND_FLOOR
import onnx, onnxruntime as ort
from onnx import TensorProto
m=onnx.load('models/s4.onnx')
prod={o:n for n in m.graph.node for o in n.output}
cons={}
for n in m.graph.node:
    for i in n.input: cons.setdefault(i,[]).append(n)
inits={i.name:i for i in m.graph.initializer}
x='/encoder14/ln2'
print('Available ORT providers:',ort.get_available_providers())
assert 'CUDAExecutionProvider' not in ort.get_available_providers(), 'Unexpected CUDA provider: stop before CPU-only ladder commands'
print('Direct consumers of',x)
for n in cons.get(x,[]): print(json.dumps({'name':n.name,'op':n.op_type,'inputs':list(n.input),'outputs':list(n.output)}))
print('Transparent branch traversal to terminal consumers:')
queue=[(x,[])];seen=set()
while queue:
    t,path=queue.pop(0)
    for n in cons.get(t,[]):
        if n.name in seen: continue
        seen.add(n.name)
        p=path+[n.name]
        print(json.dumps({'path':p,'op':n.op_type,'inputs':list(n.input),'outputs':list(n.output)}))
        if n.op_type in ['Mul','QuantizeLinear','DequantizeLinear','Identity','Reshape','Transpose']:
            queue.extend((o,p) for o in n.output)
        elif n.op_type in ['MatMul','Gemm','Conv']:
            desc=[]
            for i in n.input:
                q=prod.get(i)
                d={'input':i,'producer':q.name if q else None,'op':q.op_type if q else None}
                if q is not None and q.op_type=='DequantizeLinear':
                    zp=inits.get(q.input[2]) if len(q.input)>2 else None
                    d['zero_point_type']=TensorProto.DataType.Name(zp.data_type) if zp is not None else 'not explicit'
                desc.append(d)
            print('MATMUL QUANTIZATION EVIDENCE',n.name,json.dumps(desc))
print('Original graph direct consumers:')
o=onnx.load('models/bt3_fp32.onnx')
for n in o.graph.node:
    if x in n.input: print(json.dumps({'name':n.name,'op':n.op_type,'inputs':list(n.input),'outputs':list(n.output)}))
print('Stored s4 smoothing group:',json.dumps(json.loads(Path('models/s4.json').read_text())['smoothed_groups'][x]))
cfg=json.loads(Path('config.json').read_text())
names=[]
for n in cfg['study']['models'].split(','):
    n=n.strip(); n=cfg['best'] if n=='BEST' else n
    if n and n not in names: names.append(n)
if cfg['extras']['swap']: names+=['swap_pol8','swap_val8']
if cfg['extras']['s1sp']: names+=['s1sp']
if cfg['extras']['s0_in_study_b'] and 's0' not in names: names+=['s0']
weights={n:(2 if n.startswith('swap_') else 1) for n in names}
weighted=sum(weights.values());seconds=Decimal('0.94');target=Decimal(7*60*60)
limit=int((target/(weighted*seconds)).to_integral_value(rounding=ROUND_FLOOR))
maxpositions=sum(json.loads(l)['split']==cfg['study']['split'] for l in Path('data/tbset.jsonl').read_text().splitlines())
limit=min(limit,maxpositions)
print('Study B models and weights:',json.dumps(weights))
print('Study B model count:',len(names),'weighted model count:',weighted)
print(f'Target: 7 * 60 * 60 = {target} seconds')
print(f'Cost per selected position across models: {weighted} * {seconds} = {weighted*seconds} seconds')
print(f'study.limit = floor({target} / ({weighted} * {seconds})) = {limit}; available split positions = {maxpositions}')
print(f'Formula total: {limit} * {weighted} * {seconds} = {limit*weighted*seconds} seconds = {limit*weighted*seconds/Decimal(3600)} hours')
print('Planning formula supplied by user; actual runtime is not measured by this calculation.')
Path('reports/C2-study-sizing.json').write_text(json.dumps({'models':weights,'weighted_models':weighted,'seconds_per_position_all_budgets':str(seconds),'target_seconds':str(target),'study_limit':limit,'formula_seconds':str(limit*weighted*seconds)},indent=2)+'\n')
~~~
Exit code: 0
Output:
~~~
Available ORT providers: ['AzureExecutionProvider', 'CPUExecutionProvider']
Direct consumers of /encoder14/ln2
{"name": "/encoder14/ln2/smooth", "op": "Mul", "inputs": ["/encoder14/ln2", "/encoder14/ln2/smooth_inv"], "outputs": ["/encoder14/ln2/smoothed"]}
Transparent branch traversal to terminal consumers:
{"path": ["/encoder14/ln2/smooth"], "op": "Mul", "inputs": ["/encoder14/ln2", "/encoder14/ln2/smooth_inv"], "outputs": ["/encoder14/ln2/smoothed"]}
{"path": ["/encoder14/ln2/smooth", "/encoder14/ln2/smoothed_QuantizeLinear"], "op": "QuantizeLinear", "inputs": ["/encoder14/ln2/smoothed", "/encoder14/ln2/smoothed_scale", "/encoder14/ln2/smoothed_zero_point"], "outputs": ["/encoder14/ln2/smoothed_QuantizeLinear_Output"]}
{"path": ["/encoder14/ln2/smooth", "/encoder14/ln2/smoothed_QuantizeLinear", "/encoder14/ln2/smoothed_DequantizeLinear"], "op": "DequantizeLinear", "inputs": ["/encoder14/ln2/smoothed_QuantizeLinear_Output", "/encoder14/ln2/smoothed_scale", "/encoder14/ln2/smoothed_zero_point"], "outputs": ["/encoder14/ln2/smoothed_DequantizeLinear_Output"]}
{"path": ["/encoder14/ln2/smooth", "/encoder14/ln2/smoothed_QuantizeLinear", "/encoder14/ln2/smoothed_DequantizeLinear", "/policy/dense1/matmul"], "op": "MatMul", "inputs": ["/encoder14/ln2/smoothed_DequantizeLinear_Output", "/policy/dense1/matmul/w_DequantizeLinear_Output"], "outputs": ["/policy/dense1/matmul"]}
MATMUL QUANTIZATION EVIDENCE /policy/dense1/matmul [{"input": "/encoder14/ln2/smoothed_DequantizeLinear_Output", "producer": "/encoder14/ln2/smoothed_DequantizeLinear", "op": "DequantizeLinear", "zero_point_type": "INT8"}, {"input": "/policy/dense1/matmul/w_DequantizeLinear_Output", "producer": "/policy/dense1/matmul/w_DequantizeLinear", "op": "DequantizeLinear", "zero_point_type": "INT8"}]
{"path": ["/encoder14/ln2/smooth", "/encoder14/ln2/smoothed_QuantizeLinear", "/encoder14/ln2/smoothed_DequantizeLinear", "/value/embed/matmul"], "op": "MatMul", "inputs": ["/encoder14/ln2/smoothed_DequantizeLinear_Output", "/value/embed/matmul/w_DequantizeLinear_Output"], "outputs": ["/value/embed/matmul"]}
MATMUL QUANTIZATION EVIDENCE /value/embed/matmul [{"input": "/encoder14/ln2/smoothed_DequantizeLinear_Output", "producer": "/encoder14/ln2/smoothed_DequantizeLinear", "op": "DequantizeLinear", "zero_point_type": "INT8"}, {"input": "/value/embed/matmul/w_DequantizeLinear_Output", "producer": "/value/embed/matmul/w_DequantizeLinear", "op": "DequantizeLinear", "zero_point_type": "INT8"}]
{"path": ["/encoder14/ln2/smooth", "/encoder14/ln2/smoothed_QuantizeLinear", "/encoder14/ln2/smoothed_DequantizeLinear", "/mlh/embed/matmul"], "op": "MatMul", "inputs": ["/encoder14/ln2/smoothed_DequantizeLinear_Output", "/mlh/embed/matmul/w_DequantizeLinear_Output"], "outputs": ["/mlh/embed/matmul"]}
MATMUL QUANTIZATION EVIDENCE /mlh/embed/matmul [{"input": "/encoder14/ln2/smoothed_DequantizeLinear_Output", "producer": "/encoder14/ln2/smoothed_DequantizeLinear", "op": "DequantizeLinear", "zero_point_type": "INT8"}, {"input": "/mlh/embed/matmul/w_DequantizeLinear_Output", "producer": "/mlh/embed/matmul/w_DequantizeLinear", "op": "DequantizeLinear", "zero_point_type": "INT8"}]
Original graph direct consumers:
{"name": "/policy/dense1/matmul", "op": "MatMul", "inputs": ["/encoder14/ln2", "/policy/dense1/matmul/w"], "outputs": ["/policy/dense1/matmul"]}
{"name": "/value/embed/matmul", "op": "MatMul", "inputs": ["/encoder14/ln2", "/value/embed/matmul/w"], "outputs": ["/value/embed/matmul"]}
{"name": "/mlh/embed/matmul", "op": "MatMul", "inputs": ["/encoder14/ln2", "/mlh/embed/matmul/w"], "outputs": ["/mlh/embed/matmul"]}
Stored s4 smoothing group: {"consumers": ["/policy/dense1/matmul", "/value/embed/matmul", "/mlh/embed/matmul"], "outlier_before": 665019.877284822, "outlier_after": 124666.55689666144}
Study B models and weights: {"fp16": 1, "s1": 1, "s2": 1, "s3": 1, "s4": 1, "s4aa": 1, "swap_pol8": 2, "swap_val8": 2, "s1sp": 1}
Study B model count: 9 weighted model count: 11
Target: 7 * 60 * 60 = 25200 seconds
Cost per selected position across models: 11 * 0.94 = 10.34 seconds
study.limit = floor(25200 / (11 * 0.94)) = 2437; available split positions = 6720
Formula total: 2437 * 11 * 0.94 = 25198.58 seconds = 6.999605555555555555555555556 hours
Planning formula supplied by user; actual runtime is not measured by this calculation.
~~~
Produced: reports/C2-study-sizing.json; LOG.md entry. Graphs inspected read-only.

## 2026-10-28 01:39:17 +05:30 — set study limit and read-only channel collection
Exact command: following Python via here-string piped to ..\.venv\Scripts\python.exe -u -; output Tee-Object reports/logs/C2-ln2-probe.log
~~~python
from pathlib import Path
import json, difflib, hashlib, time
import numpy as np
import onnx
from quant.quantize import channel_amax, load_planes
p=Path('config.json');before=p.read_text();cfg=json.loads(before)
sizing=json.loads(Path('reports/C2-study-sizing.json').read_text())
Path('reports/config.C2-before-sizing.json').write_text(before)
cfg['study']['limit']=sizing['study_limit'];after=json.dumps(cfg,indent=1)+'\n'
p.write_text(after)
print('Config diff:');print(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='config.json before',tofile='config.json after')))
print('Set study.limit:',cfg['study']['limit'])
paths=['models/s4.onnx','models/bt3_fp32.onnx']
hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
planes=load_planes('data/calib.npz')
print('Channel maxima calibration positions:',len(planes),flush=True)
x='/encoder14/ln2';sm=x+'/smoothed'
report=['# C2 final LN inspection','',
'Graphs inspected read-only. Calibration input: data/calib.npz. Channel axis is last; |x|max spans all calibration positions and tokens. Median uses channels with nonzero maximum.','',
'| Consumer in s4 | Op | Quantized? |','|---|---|---|',
'| `/encoder14/ln2/smooth` (only direct consumer) | Mul | Float smoothing; no integer Q/DQ inputs |',
'| `/encoder14/ln2/smoothed_QuantizeLinear` | QuantizeLinear | Converts smoothed activation to INT8 |',
'| `/encoder14/ln2/smoothed_DequantizeLinear` | DequantizeLinear | Decodes shared INT8 activation |',
'| `/policy/dense1/matmul` | MatMul | Yes: INT8 activation Q/DQ and INT8 weight DQ |',
'| `/value/embed/matmul` | MatMul | Yes: INT8 activation Q/DQ and INT8 weight DQ |',
'| `/mlh/embed/matmul` | MatMul | Yes: INT8 activation Q/DQ and INT8 weight DQ |','']
arrays={}
for label,path,names in [('s4','models/s4.onnx',[x,sm]),('original','models/bt3_fp32.onnx',[x])]:
    t=time.perf_counter();m=onnx.load(path)
    am=channel_amax(m,planes,names,{n:-1 for n in names})
    print(label,'channel collection seconds:',round(time.perf_counter()-t,3),flush=True)
    for name,a in am.items():
        key=label+('_smoothed' if name==sm else '_raw');arrays[key]=a
        live=a[a>0];med=float(np.median(live));top=np.argsort(-a)[:5]
        print(label,name,'channels:',len(a),'live:',len(live),'median live:',format(med,'.12g'),flush=True)
        report += [f'## {label}: `{name}`','',f'Live channels: {len(live)} / {len(a)}. Median live |x|max: {med:.12g}.','',
                   '| Channel (zero-based) | Maximum absolute activation | Ratio to median live |','|---|---|---|']
        for i in top:
            line=f'| {int(i)} | {float(a[i]):.12g} | {float(a[i])/med:.6f} |'
            report.append(line);print(line,flush=True)
        report.append('')
for p,h in hashes.items():
    now=hashlib.sha256(Path(p).read_bytes()).hexdigest();assert now==h, f'graph changed: {p}'
    print('Graph unchanged SHA256:',p,h,flush=True)
np.savez('reports/C2-ln2-channel-maxima.npz',**arrays)
Path('reports/C2-ln2-consumers-and-channels.md').write_text('\n'.join(report)+'\n')
print('Produced: reports/C2-ln2-consumers-and-channels.md; reports/C2-ln2-channel-maxima.npz; reports/config.C2-before-sizing.json',flush=True)
~~~
Exit code: running; recorded on completion below.

## 2026-10-28 01:39:41 +05:30 — channel inspection completion
Exact command: inline Python recorded above
Exit code: 0
Output:
~~~
Config diff:
--- config.json before
+++ config.json after
@@ -25,7 +25,7 @@
  "best": "s4",
  "study": {
   "split": "test",
-  "limit": 0,
+  "limit": 2437,
   "budgets": "0,100,400,800,1600",
   "threads": 1,
   "minibatch": 256,
@@ -49,4 +49,4 @@
   "batch_sizes": "32,64,128,256",
   "bench_movetime": 10000
  }
-}+}

Set study.limit: 2437
Channel maxima calibration positions: 512
s4 channel collection seconds: 10.239
s4 /encoder14/ln2 channels: 768 live: 768 median live: 8.13330552774e-05
| 420 | 56.0252571106 | 688837.483352 |
| 644 | 32.8431091309 | 403810.099336 |
| 401 | 29.0968647003 | 357749.559525 |
| 383 | 25.4995193481 | 313519.752347 |
| 238 | 25.0413208008 | 307886.144390 |
s4 /encoder14/ln2/smoothed channels: 768 live: 768 median live: 3.2066131098e-05
| 420 | 4.06870698929 | 126884.873540 |
| 401 | 3.48657655716 | 108730.814656 |
| 468 | 2.92885684967 | 91338.017696 |
| 565 | 2.83453202248 | 88396.445889 |
| 682 | 2.20494794846 | 68762.518987 |
original channel collection seconds: 12.688
original /encoder14/ln2 channels: 768 live: 768 median live: 7.93288418208e-05
| 420 | 52.7552566528 | 665019.877285 |
| 644 | 31.9671916962 | 402970.608954 |
| 401 | 29.1855373383 | 367905.753675 |
| 240 | 25.877363205 | 326203.718736 |
| 572 | 24.6206893921 | 310362.395656 |
Graph unchanged SHA256: models/s4.onnx 574f555e5aa2d6b49e319e268a2d572c640d802399246767f1ac58c7161893ec
Graph unchanged SHA256: models/bt3_fp32.onnx 937d5ac3d1ce9daafc7858f54166787924680c0c9c4aaab94d438402430db2b9
Produced: reports/C2-ln2-consumers-and-channels.md; reports/C2-ln2-channel-maxima.npz; reports/config.C2-before-sizing.json
~~~
Produced: reports/logs/C2-ln2-probe.log, reports/C2-ln2-consumers-and-channels.md, reports/C2-ln2-channel-maxima.npz, reports/config.C2-before-sizing.json. Updated config.json study.limit; exact diff above.

## 2026-10-28 01:40:02 +05:30 — select started (CPU only)
Exact command (cwd leela-int8): ..\.venv\Scripts\python.exe -u ladder.py select
Process-local environment: CUDA_VISIBLE_DEVICES=-1; TEMP=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\tmp; TMP=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\tmp. ORT available providers printed above exclude CUDA; common.ort_session selects CPU.
Background exec session output: 2>&1 | Tee-Object reports/logs/C2-select.log
Exit code: running; completion recorded below.
Resume command: ..\.venv\Scripts\python.exe -u ladder.py select (reuses completed candidate ONNX; reruns comparison).

## 2026-10-28 01:44:40 +05:30 — C2 checkpoint scope recorded
Exact PowerShell: read STATUS.md with [IO.File]::ReadAllText; replace row '| 3-5 | todo | Await checkpoint approval |' with the rows below; write with [IO.File]::WriteAllText; Write-Output new rows.
Exit code: 0
Output:
~~~
| 3b select --alpha | todo | Run after s3 recipe is set from the dev report; CPU only |
| 3c freeze recipe | todo | Select s3 method/percentile and SmoothQuant alpha from dev reports |
| CHECKPOINT C2-select | todo | Stop after selection and recipe update, before build |
| 4 build | todo | After C2-select review; ensure existing s4 recipe is refreshed if changed; assess SparseGPT one-shot condition |
| CHECKPOINT C2-done | todo | User-requested stop after build; study not started |
| Study and later GPU steps | todo | Await review; user requested CPU only until study |
~~~
Updated: STATUS.md, LOG.md. User requests stopping at C2-select and again after build. No build, SparseGPT, or study is run before C2-select review. ladder.py skips an existing model .pb.gz; when the selected s4 recipe changes, the subsequent approved build must refresh the existing C1 s4 rather than silently reusing it. No code changes made.

## 2026-10-28 01:58:27 +05:30 — select dev comparison progress inspection
Exact command: Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "python.exe" -and $_.CommandLine -like "*quick_compare.py*" } | Select-Object ProcessId,CommandLine; Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,CPU,WorkingSet64
Exit code: 0
Output:
~~~

ProcessId   : 16068
CommandLine : C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz 
              C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\select_s3_dev.txt 
              C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p9999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p99999.onnx 
              C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_entropy.onnx

ProcessId   : 29912
CommandLine : "C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz 
              C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\select_s3_dev.txt 
              C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p9999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p99999.onnx 
              C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_entropy.onnx


   Id     CPU WorkingSet64
   --     --- ------------
16068    0.00      4505600
21896    0.02      4542464
28440    0.08     16687104
29912 2544.47    691290112


~~~
Produced: LOG.md entry only; no source/config changes.

## 2026-10-28 02:00:09 +05:30 — select completion
Exact command: ..\.venv\Scripts\python.exe -u ladder.py select
Exit code: 0
Key output:
~~~
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p999.onnx --granularity per-channel --method percentile --percentile 99.9
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.501, min 0.107 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p999.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (188s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p9999.onnx --granularity per-channel --method percentile --percentile 99.99
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.690, min 0.321 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p9999.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (187s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p99999.onnx --granularity per-channel --method percentile --percentile 99.999
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.829, min 0.478 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p99999.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (186s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_entropy.onnx --granularity per-channel --method entropy
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py:154: RuntimeWarning: invalid value encountered in divide
  ps, qs = p / p.sum(), q / q.sum()
entropy: median range ratio 0.730, min 0.062 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_entropy.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (219s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\select_s3_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p9999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p99999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_entropy.onnx
3360 positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz (ORT, not TensorRT)
model                               KL   top1    |dV|  tb_acc
ref bt3_fp32.onnx             0.00e+00  1.000  0.0000   0.998
s3_p999.onnx                  2.16e-01  0.707  0.1532   0.984
s3_p9999.onnx                 4.03e-02  0.839  0.0217   0.996
s3_p99999.onnx                2.20e-02  0.844  0.0128   0.997
s3_entropy.onnx               1.01e+00  0.214  0.5925   0.552

Pick step 3 from the table above (lowest KL / highest tb_acc), set recipe.s3_method and s3_percentile in the config, then rerun `select --alpha` for step 4.
~~~
Outputs: reports/logs/C2-select.log, reports/logs/C2-select.exitcode, reports/logs/select.log; models/select/*.onnx and *.json; reports/select_s3_dev.txt if completed.

## 2026-10-28 02:00:51 +05:30 — selection validation and s3 config update
Exact command: following Python via here-string piped to ..\.venv\Scripts\python.exe -
~~~python
from pathlib import Path
import json, math, difflib
import onnx, numpy as np
from onnx import numpy_helper
report=Path('reports/select_s3_dev.txt').read_text();print(report)
names=['s3_p999','s3_p9999','s3_p99999','s3_entropy']
for name in names:
    m=onnx.load(f'models/select/{name}.onnx');inits={x.name:x for x in m.graph.initializer}
    scale_names={n.input[1] for n in m.graph.node if n.op_type in ['QuantizeLinear','DequantizeLinear']}
    arrays=[numpy_helper.to_array(inits[x]) for x in scale_names]
    assert all(np.isfinite(a).all() and (a>0).all() for a in arrays),f'{name}: invalid quantization scale'
    side=json.loads(Path(f'models/select/{name}.json').read_text())
    clips=side['activation_clip']
    assert all(math.isfinite(v['ratio']) and 0<v['ratio']<=1 and math.isfinite(v['clipped_frac']) and 0<=v['clipped_frac']<=1 for v in clips.values()),f'{name}: invalid clip metadata'
    print(name,'positive finite Q/DQ scale tensors:',len(scale_names),'finite clip entries:',len(clips))
rows=[]
for line in report.splitlines():
    v=line.split()
    if v and v[0].endswith('.onnx'):
        assert len(v)==5,line
        rows.append(dict(name=v[0],kl=float(v[1]),top1=float(v[2]),dv=float(v[3]),tb_acc=float(v[4])))
assert len(rows)==4
best=min(rows,key=lambda r:(r['kl'],-r['tb_acc'],-r['top1'],r['dv']))
assert best['tb_acc']==max(r['tb_acc'] for r in rows),'KL and TB winner differ: review before choosing'
print('Chosen s3:',json.dumps(best))
settings={'s3_p999.onnx':('percentile',99.9),'s3_p9999.onnx':('percentile',99.99),'s3_p99999.onnx':('percentile',99.999),'s3_entropy.onnx':('entropy',None)}
method,pct=settings[best['name']]
p=Path('config.json');before=p.read_text();cfg=json.loads(before)
Path('reports/config.C2-before-s3-selection.json').write_text(before)
cfg['recipe']['s3_method']=method
if pct is not None: cfg['recipe']['s3_percentile']=pct
p.write_text(json.dumps(cfg,indent=1)+'\n')
print('Config diff:');print(''.join(difflib.unified_diff(before.splitlines(True),p.read_text().splitlines(True),fromfile='config.json before',tofile='config.json after')))
Path('reports/C2-s3-choice.json').write_text(json.dumps({'chosen':best,'all':rows,'decision':'Lowest reported KL and highest candidate tb_acc; scales positive and finite; clip metadata finite','entropy_warning':'NumPy invalid divide warning during threshold scan; command exited 0; emitted entropy scales and clip metadata passed finite checks'},indent=2)+'\n')
print('Entropy warning retained; all saved scales and clip ratios passed validation. No calibration code change.')
print('Produced: reports/C2-s3-choice.json, reports/config.C2-before-s3-selection.json; updated config.json')
~~~
Exit code: 0
Output:
~~~
3360 positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz (ORT, not TensorRT)
model                               KL   top1    |dV|  tb_acc
ref bt3_fp32.onnx             0.00e+00  1.000  0.0000   0.998
s3_p999.onnx                  2.16e-01  0.707  0.1532   0.984
s3_p9999.onnx                 4.03e-02  0.839  0.0217   0.996
s3_p99999.onnx                2.20e-02  0.844  0.0128   0.997
s3_entropy.onnx               1.01e+00  0.214  0.5925   0.552

s3_p999 positive finite Q/DQ scale tensors: 430 finite clip entries: 280
s3_p9999 positive finite Q/DQ scale tensors: 430 finite clip entries: 280
s3_p99999 positive finite Q/DQ scale tensors: 430 finite clip entries: 280
s3_entropy positive finite Q/DQ scale tensors: 430 finite clip entries: 280
Chosen s3: {"name": "s3_p99999.onnx", "kl": 0.022, "top1": 0.844, "dv": 0.0128, "tb_acc": 0.997}
Config diff:
--- config.json before
+++ config.json after
@@ -19,7 +19,7 @@
  },
  "recipe": {
   "s3_method": "percentile",
-  "s3_percentile": 99.99,
+  "s3_percentile": 99.999,
   "s4_alpha": 0.5
  },
  "best": "s4",

Entropy warning retained; all saved scales and clip ratios passed validation. No calibration code change.
Produced: reports/C2-s3-choice.json, reports/config.C2-before-s3-selection.json; updated config.json
~~~
Produced: reports/C2-s3-choice.json, reports/config.C2-before-s3-selection.json. Updated config.json with exact diff above.

## 2026-10-28 02:00:52 +05:30 — alpha selection started (CPU only)
Exact command (cwd leela-int8): ..\.venv\Scripts\python.exe -u ladder.py select --alpha
Process-local environment: CUDA_VISIBLE_DEVICES=-1; TEMP=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\tmp; TMP=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\tmp. CPU-only ORT install unchanged.
Background exec session output: 2>&1 | Tee-Object reports/logs/C2-select-alpha.log
Exit code: running; completion recorded below.
Resume command: ..\.venv\Scripts\python.exe -u ladder.py select --alpha (reuses completed candidates; reruns comparisons).
This command first repeats the s3 dev comparison, then builds alpha candidates on the selected s3 recipe and compares them.

## 2026-10-28 02:06:40 +05:30 — user C2 stop-rule and selection override
Exact action: replace prior pending C2 checkpoint/build/study rows in STATUS.md using [IO.File]::ReadAllText/.Replace/[IO.File]::WriteAllText.
Exit code: 0
New authorized rules: continue at C2-select and after build; stop at first failure except one nonfatal study retry, or at C2-done after score. s3: lowest finite dev KL, tie higher top-1. Alpha: lowest finite dev KL among alphas whose top-1 is at least chosen s3; otherwise best=s3; ties favor simpler recipe. No quantization/scoring code changes. Back up models/s4.* under reports/c1-s4-backup then remove originals. Build all nine variants and validate sidecar recipes/files. SparseGPT projected total over 90 minutes permits restarting that one model with --one-shot. Background study must write reports/logs/study.log, with GPU idle first; score after completion. C2-done must include recipe/reason, study.limit, per-model accuracy/node-equivalents, warnings, and resume command.
Updated: STATUS.md, LOG.md.

## 2026-10-28 02:06:40 +05:30 — build sidecar and score schema inspection
Exact command: Get-Content quant/stitch_swap.py; Get-Content quant/prune24.py; Get-Content eval/score.py; Get-Content ladder.py | Select-Object -Skip 100 -First 30
Exit code: 0
Output:
~~~
#!/usr/bin/env python3
"""Policy/value swap models for stock lc0: one ONNX that takes its policy
output from model P and its value (WDL) + MLH outputs from model V.

lc0 cannot mix two nets, but it runs any ONNX. This prefixes every name in
each graph, shares the input, keeps only the nodes each kept output needs
(so P's value head and V's policy head are dropped) and renames the outputs
back to lc0's names. Both bodies run, so the result is ~2× slower: use it
for accuracy studies (A/B) only, never for timing.

    python quant/stitch_swap.py --policy models/s4.onnx --value models/bt3_fp32.onnx \
        --out models/swap_int8pol.onnx
    python quant/wrap.py --orig nets/BT3.pb.gz --onnx models/swap_int8pol.onnx --out models/swap_int8pol.pb.gz
"""
import argparse
import sys
from pathlib import Path

import onnx
from onnx import helper

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import INPUT, OUT_MLH, OUT_POLICY, OUT_WDL, load_onnx, save_onnx  # noqa: E402


def needed_nodes(graph, outputs):
    prod = {o: n for n in graph.node for o in n.output}
    keep, stack, seen = [], list(outputs), set()
    while stack:
        t = stack.pop()
        if t in seen:
            continue
        seen.add(t)
        n = prod.get(t)
        if n is None:
            continue
        if id(n) not in {id(k) for k in keep}:
            keep.append(n)
        stack.extend(n.input)
        # subgraph-free ops only in lc0 graphs
    order = {id(n): i for i, n in enumerate(graph.node)}
    keep.sort(key=lambda n: order[id(n)])
    return keep


def prefixed(model, pfx, outputs):
    g = model.graph
    keep = needed_nodes(g, outputs)
    used = {i for n in keep for i in n.input}

    def ren(x):
        return x if x in ("", INPUT) else pfx + x

    nodes = []
    for n in keep:
        nn = onnx.NodeProto()
        nn.CopyFrom(n)
        nn.name = pfx + n.name
        del nn.input[:]
        nn.input.extend(ren(i) for i in n.input)
        del nn.output[:]
        nn.output.extend(ren(o) for o in n.output)
        nodes.append(nn)
    inits = []
    for t in g.initializer:
        if t.name in used:
            tt = onnx.TensorProto()
            tt.CopyFrom(t)
            tt.name = pfx + t.name
            inits.append(tt)
    vis = []
    for v in g.value_info:
        if v.name in used:
            vv = onnx.ValueInfoProto()
            vv.CopyFrom(v)
            vv.name = pfx + v.name
            vis.append(vv)
    return nodes, inits, vis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True, help="ONNX whose policy head is used")
    ap.add_argument("--value", required=True, help="ONNX whose WDL (and MLH) heads are used")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    P = load_onnx(a.policy)
    V = load_onnx(a.value)
    v_outs = [OUT_WDL] + ([OUT_MLH] if any(o.name == OUT_MLH for o in V.graph.output) else [])
    pn, pi, pv = prefixed(P, "P", [OUT_POLICY])
    vn, vi, vv = prefixed(V, "V", v_outs)
    # Rename the kept outputs back to lc0's names with Identity nodes.
    ident = [helper.make_node("Identity", ["P" + OUT_POLICY], [OUT_POLICY], name="/swap/policy")]
    ident += [helper.make_node("Identity", ["V" + o], [o], name=f"/swap{o}") for o in v_outs]
    outs = [o for o in P.graph.output if o.name == OUT_POLICY] + \
           [o for o in V.graph.output if o.name in v_outs]
    g = helper.make_graph(pn + vn + ident, "swap", list(P.graph.input), outs,
                          initializer=pi + vi, value_info=pv + vv)
    opsets = {}
    for m in (P, V):
        for o in m.opset_import:
            opsets[o.domain] = max(opsets.get(o.domain, 0), o.version)
    m = helper.make_model(g, opset_imports=[helper.make_opsetid(d, v) for d, v in opsets.items()],
                          producer_name="leela-int8 stitch_swap")
    m.ir_version = max(P.ir_version, V.ir_version)
    if m.ByteSize() < 1.8e9:
        onnx.checker.check_model(m)
    save_onnx(m, a.out)
    print(f"policy from {a.policy}, value from {a.value} -> {a.out} "
          f"({len(pn)} + {len(vn)} nodes)", file=sys.stderr)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""S0: one-shot magnitude 2:4 pruning of every weight-carrying MatMul/Conv
(no fine-tuning). Output is an FP32 ONNX; the ladder then quantizes it with
the frozen PTQ recipe (zeros stay zeros under symmetric int8).

    python quant/prune24.py --onnx models/bt3_fp32.onnx --out models/s0_fp32.onnx
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from onnx import numpy_helper

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import initializers, load_onnx, save_onnx  # noqa: E402
from sparse_common import check_24, from_kn, magnitude_mask, targets, to_kn  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--onnx", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip", default=None, help="regex of node names to leave dense")
    a = ap.parse_args()
    m = load_onnx(a.onnx)
    inits = initializers(m)
    rep = {}
    for name, nodes in targets(m, a.skip).items():
        op = nodes[0].op_type
        w = numpy_helper.to_array(inits[name]).astype(np.float32)
        kn = to_kn(w, op)
        mask = magnitude_mask(kn)
        p = np.where(mask, kn, 0).astype(np.float32)
        assert check_24(p)
        inits[name].CopyFrom(numpy_helper.from_array(from_kn(p, op, w.shape), name))
        rep[name] = {"nodes": [n.name for n in nodes],
                     "rel_err": float(np.linalg.norm(kn - p) / max(np.linalg.norm(kn), 1e-12))}
    save_onnx(m, a.out)
    with open(Path(a.out).with_suffix(".json"), "w") as f:
        json.dump({"method": "magnitude 2:4", "skip": a.skip, "layers": rep}, f, indent=1)
    errs = [v["rel_err"] for v in rep.values()]
    print(f"pruned {len(rep)} weights 2:4 (magnitude); median rel. weight error "
          f"{np.median(errs):.3f} -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Score Studies A/B/C against the tablebase labels.

Per model:
  Study A  raw tablebase accuracy (+95% Wilson CI), DTZ-optimal rate,
           KL(ref || model) over legal moves, top-1 agreement, mean |ΔV|.
           KL is approximate below ~1e-4 (trap 7: lc0 prints P to 0.01%).
  Study B  accuracy at each node budget with paired counts vs the reference
           (−worse / +better) and an exact McNemar p, mean actual nodes,
           and node-equivalents: FP16 nodes needed to reach the model's
           accuracy ÷ the model's nodes (1.00 = matches FP16; 0 = below
           FP16's raw net; inf = above FP16's largest budget).
  Study C  accuracy at each movetime, paired vs reference, mean nodes and
           the nodes ratio vs the reference (the realised speed-up).

Rows are scored on positions that the model AND the reference finished at
every budget (the `n` column); the header warns when rows differ in n.
The hard subset (reference's raw top move wrong, or under 80% raw policy
mass on correct moves) is scored the same way into <out>/hard/.

    python eval/score.py --tbset data/tbset.jsonl --results results --ref fp16 \
        --models fp16,s1,s2,s3,s4 --out reports
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import read_jsonl, wilson  # noqa: E402


def load(results, name):
    d = Path(results) / name
    A = {r["id"]: r for r in read_jsonl(d / "study_a.jsonl")}
    B, C = {}, {}
    for r in read_jsonl(d / "study_b.jsonl"):
        B.setdefault(r["budget"], {})[r["id"]] = r
    for r in read_jsonl(d / "study_c.jsonl"):
        C.setdefault(r["movetime"], {})[r["id"]] = r
    return A, B, C


def mcnemar_p(worse, better):
    n = worse + better
    if n == 0:
        return 1.0
    k = min(worse, better)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def kl(p, q):
    keys = sorted(set(p) | set(q))
    a = np.array([max(p.get(k, 0.0), 1e-6) for k in keys])
    b = np.array([max(q.get(k, 0.0), 1e-6) for k in keys])
    a /= a.sum()
    b /= b.sum()
    return float(np.sum(a * np.log(a / b)))


def ne_curve(ref_points):
    """ref_points: [(mean_nodes, acc)] incl. raw (1 node). Monotone envelope."""
    pts = sorted(ref_points)
    xs = [math.log(max(n, 1)) for n, _ in pts]
    ys, best = [], -1
    for _, acc in pts:
        best = max(best, acc)
        ys.append(best)
    return xs, ys


def nodes_for(acc, xs, ys, hint):
    """FP16 nodes needed to reach `acc` on the envelope (xs = log nodes).
    Where the envelope is flat at `acc` the inverse is an interval; take the
    point of it nearest the model's own node count (`hint`), so a model that
    matches a saturated FP16 gets 1.00, not an artefact of the flat stretch."""
    eps = 1e-12
    if acc < ys[0] - eps:
        return 0.0
    if acc > ys[-1] + eps:
        return float("inf")

    def interp(j, target):
        if ys[j] == ys[j - 1]:
            return xs[j - 1]
        t = (target - ys[j - 1]) / (ys[j] - ys[j - 1])
        return xs[j - 1] + t * (xs[j] - xs[j - 1])

    j = next(k for k in range(len(ys)) if ys[k] >= acc - eps)
    lo = xs[0] if j == 0 else interp(j, acc)
    j2 = next((k for k in range(len(ys)) if ys[k] > acc + eps), None)
    hi = float("inf") if j2 is None else (xs[0] if j2 == 0 else interp(j2, acc))
    x = min(max(math.log(max(hint, 1)), lo), hi)
    return math.exp(x)


def fmt_ci(k, n):
    lo, hi = wilson(k, n)
    return f"{k / n:.4f} [{lo:.3f},{hi:.3f}]" if n else "n/a"


def score(tb, data, ref, models, ids_filter=None):
    """Returns (markdown lines, json dict)."""
    rA, rB, rC = data[ref]
    budgets = sorted(rB)
    movetimes = sorted(rC)
    out = {"ref": ref, "models": {}}
    L = []

    # ---------------- Study A
    L.append("## Study A: raw network (budget 0)\n")
    L.append("| model | n | tb accuracy [95% CI] | DTZ-optimal | KL vs ref | top-1 agree | mean abs dV |")
    L.append("|---|---|---|---|---|---|---|")
    ns = set()
    for m in models:
        A = data[m][0]
        ids = [i for i in A if i in rA and i in tb and (ids_filter is None or i in ids_filter)]
        n = len(ids)
        if not n:
            continue
        ns.add(n)
        acc = sum(A[i]["best"] in tb[i]["correct"] for i in ids)
        dtz = sum(A[i]["best"] in tb[i]["dtz_opt"] for i in ids)
        kls = [kl(rA[i]["p"], A[i]["p"]) for i in ids]
        t1 = sum(max(A[i]["p"], key=A[i]["p"].get) == max(rA[i]["p"], key=rA[i]["p"].get) for i in ids)
        dv = [abs((A[i]["v"] or 0) - (rA[i]["v"] or 0)) for i in ids
              if A[i].get("v") is not None and rA[i].get("v") is not None]
        L.append(f"| {m} | {n} | {fmt_ci(acc, n)} | {dtz / n:.4f} | {np.mean(kls):.2e} | "
                 f"{t1 / n:.4f} | {np.mean(dv) if dv else float('nan'):.4f} |")
        out["models"].setdefault(m, {})["A"] = {"n": n, "acc": acc / n, "dtz_opt": dtz / n,
                                               "kl": float(np.mean(kls)), "top1": t1 / n,
                                               "dv": float(np.mean(dv)) if dv else None}
    if len(ns) > 1:
        L.insert(1, f"> WARNING: rows have different n {sorted(ns)} (interrupted run?)\n")

    # ---------------- Study B
    if budgets:
        L.append("\n## Study B: fixed node budgets\n")
        L.append("Accuracy (paired vs ref: −worse/+better, McNemar p), mean actual nodes.\n")
        L.append("| model | n | raw | " + " | ".join(f"{b} nodes" for b in budgets) + " |")
        L.append("|---|---|---|" + "---|" * len(budgets))
        ref_ids = None
        ne_rows = []
        for m in models:
            A, B, _ = data[m]
            ids = set(i for i in rA if i in tb and (ids_filter is None or i in ids_filter))
            ids &= set(A)
            for b in budgets:
                ids &= set(B.get(b, {})) & set(rB[b])
            ids = sorted(ids)
            if not ids:
                continue
            if m == ref:
                ref_ids = ids
            cells, mres = [], {}
            raw = sum(A[i]["best"] in tb[i]["correct"] for i in ids) / len(ids)
            pts = []
            for b in budgets:
                ok = [B[b][i]["best"] in tb[i]["correct"] for i in ids]
                rok = [rB[b][i]["best"] in tb[i]["correct"] for i in ids]
                worse = sum(r and not o for o, r in zip(ok, rok))
                better = sum(o and not r for o, r in zip(ok, rok))
                nodes = float(np.mean([B[b][i]["nodes"] or b for i in ids]))
                acc = sum(ok) / len(ids)
                pts.append((nodes, acc))
                s = f"{acc:.4f}"
                if m != ref:
                    s += f" (−{worse}/+{better}, p={mcnemar_p(worse, better):.2g})"
                s += f" @{nodes:.0f}"
                cells.append(s)
                mres[b] = {"acc": acc, "worse": worse, "better": better,
                           "p": mcnemar_p(worse, better), "nodes": nodes}
            L.append(f"| {m} | {len(ids)} | {raw:.4f} | " + " | ".join(cells) + " |")
            out["models"].setdefault(m, {})["B"] = {"n": len(ids), "raw": raw, "budgets": mres}
            ne_rows.append((m, ids, raw, pts))
        # node-equivalents, each against FP16 on the same ids
        L.append("\n### Node-equivalents (FP16 nodes needed ÷ model nodes)\n")
        L.append("| model | " + " | ".join(f"{b}" for b in budgets) + " |")
        L.append("|---|" + "---|" * len(budgets))
        for m, ids, raw, pts in ne_rows:
            rraw = sum(rA[i]["best"] in tb[i]["correct"] for i in ids) / len(ids)
            rpts = [(1.0, rraw)]
            for b in budgets:
                rpts.append((float(np.mean([rB[b][i]["nodes"] or b for i in ids])),
                             sum(rB[b][i]["best"] in tb[i]["correct"] for i in ids) / len(ids)))
            xs, ys = ne_curve(rpts)
            cells = []
            for (nodes, acc) in pts:
                need = nodes_for(acc, xs, ys, nodes)
                cells.append("inf" if need == float("inf") else f"{need / nodes:.2f}")
            L.append(f"| {m} | " + " | ".join(cells) + " |")
            out["models"][m].setdefault("B", {})["node_equiv"] = cells

    # ---------------- Study C
    if movetimes:
        L.append("\n## Study C: fixed time per move\n")
        L.append("| model | " + " | ".join(f"{t} ms" for t in movetimes) + " |")
        L.append("|---|" + "---|" * len(movetimes))
        for m in models:
            C = data[m][2]
            cells, res = [], {}
            for t in movetimes:
                ids = sorted(i for i in C.get(t, {}) if i in rC[t] and i in tb
                             and (ids_filter is None or i in ids_filter))
                if not ids:
                    cells.append("–")
                    continue
                ok = [C[t][i]["best"] in tb[i]["correct"] for i in ids]
                rok = [rC[t][i]["best"] in tb[i]["correct"] for i in ids]
                worse = sum(r and not o for o, r in zip(ok, rok))
                better = sum(o and not r for o, r in zip(ok, rok))
                nodes = float(np.mean([C[t][i]["nodes"] or 0 for i in ids]))
                rnodes = float(np.mean([rC[t][i]["nodes"] or 0 for i in ids]))
                acc = sum(ok) / len(ids)
                s = f"{acc:.4f} n={len(ids)}"
                if m != ref:
                    s += f" (−{worse}/+{better}, p={mcnemar_p(worse, better):.2g})"
                s += f" @{nodes:.0f} nodes (×{nodes / max(rnodes, 1e-9):.2f})"
                cells.append(s)
                res[t] = {"n": len(ids), "acc": acc, "worse": worse, "better": better,
                          "nodes": nodes, "nodes_ratio": nodes / max(rnodes, 1e-9)}
            L.append(f"| {m} | " + " | ".join(cells) + " |")
            out["models"].setdefault(m, {})["C"] = res
    return L, out


def by_class(tb, data, ref, models, keep):
    rA = {i: v for i, v in data[ref][0].items() if i in keep}
    classes = sorted({tb[i]["cls"] for i in rA if i in tb})
    L = ["\n## Raw accuracy by material class\n",
         "| class | n | " + " | ".join(models) + " |", "|---|---|" + "---|" * len(models)]
    for c in classes:
        ids = [i for i in rA if i in tb and tb[i]["cls"] == c]
        row = [f"{sum(data[m][0][i]['best'] in tb[i]['correct'] for i in ids if i in data[m][0]) / max(1, sum(i in data[m][0] for i in ids)):.3f}"
               for m in models]
        L.append(f"| {c} | {len(ids)} | " + " | ".join(row) + " |")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tbset", required=True)
    ap.add_argument("--results", default="results")
    ap.add_argument("--ref", default="fp16")
    ap.add_argument("--models", required=True, help="comma list; ref included or not")
    ap.add_argument("--out", default="reports")
    ap.add_argument("--split", default="test",
                    help="score only positions of this tbset split (results files may hold several)")
    ap.add_argument("--tag", default=None, help="report name suffix (default: the split)")
    ap.add_argument("--hard-mass", type=float, default=0.8)
    a = ap.parse_args()
    a.tag = a.tag or a.split
    recs = read_jsonl(a.tbset)
    tb = {r["id"]: {"correct": set(r["correct"]), "dtz_opt": set(r["dtz_opt"]), "cls": r["cls"]}
          for r in recs}
    split_ids = {r["id"] for r in recs if r["split"] == a.split}
    models = [m for m in a.models.split(",") if m]
    if a.ref not in models:
        models = [a.ref] + models
    data = {m: load(a.results, m) for m in models}
    if not data[a.ref][0]:
        sys.exit(f"no Study A results for the reference {a.ref}")
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    L, js = score(tb, data, a.ref, models, ids_filter=split_ids)
    L = [f"# Scores ({a.tag}), reference = {a.ref}\n"] + L + by_class(tb, data, a.ref, models, split_ids)
    (out_dir / f"scores_{a.tag}.md").write_text("\n".join(L) + "\n")
    (out_dir / f"scores_{a.tag}.json").write_text(json.dumps(js, indent=1))

    rA = data[a.ref][0]
    hard = set()
    for i, r in rA.items():
        if i not in tb or i not in split_ids:
            continue
        mass = sum(p for mv, p in r["p"].items() if mv in tb[i]["correct"])
        if r["best"] not in tb[i]["correct"] or mass < a.hard_mass:
            hard.add(i)
    hd = out_dir / "hard"
    hd.mkdir(exist_ok=True)
    (hd / "ids.txt").write_text("\n".join(str(i) for i in sorted(hard)) + "\n")
    L2, js2 = score(tb, data, a.ref, models, ids_filter=hard)
    L2 = [f"# Hard subset ({a.tag}): {len(hard)} positions where {a.ref}'s raw top move is "
          f"wrong or <{a.hard_mass:.0%} raw policy mass is on correct moves\n"] + L2
    (hd / f"scores_{a.tag}.md").write_text("\n".join(L2) + "\n")
    (hd / f"scores_{a.tag}.json").write_text(json.dumps(js2, indent=1))
    print("\n".join(L))
    print(f"\nwrote {out_dir}/scores_{a.tag}.md and hard/ ({len(hard)} hard positions)")


if __name__ == "__main__":
    main()
    return rc


def script(*parts):
    return str(ROOT.joinpath(*parts))


# ------------------------------------------------------------------ models
def recipe_flags(cfg, name):
    r = cfg["recipe"]
    s3 = ["--granularity", "per-channel", "--method", r["s3_method"]]
    if r["s3_method"] == "percentile":
        s3 += ["--percentile", str(r["s3_percentile"])]
    s4 = s3 + ["--smoothquant", str(r["s4_alpha"])]
    table = {"s1": ["--granularity", "per-tensor", "--method", "minmax"],
             "s2": ["--granularity", "per-channel", "--method", "minmax"],
             "s3": s3, "s4": s4}
    if name in table:
        return table[name]
    best = table[cfg["best"]] if cfg["best"] in table else s4
    if name == "s4aa":
        return best + ["--act-act-matmul"]
    if name in ("s0", "s1sp"):
        return best
    raise KeyError(name)


def model_opts(cfg, name):
    return cfg["fp16_opts"] if name == "fp16" else cfg["int8_opts"]


~~~
Produced: LOG.md inspection entry only. No source edits.

## 2026-10-28 02:14:38 +05:30 — C2 continuation runner syntax check
Exact command: ..\.venv\Scripts\python.exe -m py_compile reports/c2_continue.py
Exit code: 0
Produced: reports/__pycache__/c2_continue*.pyc. Runner added at reports/c2_continue.py using apply_patch; it orchestrates existing CLIs and metadata only, with no edits to quant/, eval/, tb/, common.py or ladder.py.

## 2026-10-28 02:14:39 +05:30 — C2 continuation dry plan
Exact command: ..\.venv\Scripts\python.exe reports/c2_continue.py --plan
Exit code: 0
Output:
~~~
Wait for current select --alpha exit file; mechanical finite selection; back up/remove C1 s4; CPU main build; SparseGPT sequential with 5400s stage projection switch; CPU remaining build; sidecar/file verification; idle GPU; background study with one nonfatal retry; score; C2-done; stop.
~~~
Runner SHA256: A5A9A2CD87A2158F55F25C0E3BD6469E70818A81F8F43E2A7D81E4032AF1A8FB. Source artifact: reports/c2_continue.py. No model/config mutation in --plan. The swap builder emits no JSON; runner creates provenance JSON output sidecars for swaps without changing stitch_swap.py. Model recipe validation uses ladder.recipe_flags so fixed minmax s1/s2 baselines retain their specified ablation recipes.

## 2026-10-28 02:14:39 +05:30 — detached C2 continuation launched
Exact command: Start-Process -FilePath C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -ArgumentList @('-u','reports/c2_continue.py') -WorkingDirectory C:\Users\HP\Desktop\LC0-B\leela-int8 -RedirectStandardOutput reports/logs/C2-controller.stdout.log -RedirectStandardError reports/logs/C2-controller.stderr.log -WindowStyle Hidden -PassThru
Exit code: 0 (launch); controller running, completion tracked in reports/C2-controller-state.json.
Printed PID: 16964
Produced: reports/logs/C2-controller.pid, C2-controller.stdout.log, C2-controller.stderr.log; reports/C2-controller-state.json and C2-source-hashes.json will record progress. The runner waits for the already-running alpha command; it does not start another selection job.

## 2026-10-28T02:14:39+05:30 — process-local awake request
Exact API call: SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED), result=-2147483648. Reversible process/thread lifetime request; no persistent power settings changed.

## 2026-10-28T02:14:39+05:30 — C2 continuation started
Exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u reports/c2_continue.py
PID: 18308
Awaiting existing command completion marker: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-select-alpha.exitcode
No second selection job is started. Source hash manifest: reports/C2-source-hashes.json. Controller source: reports/c2_continue.py (orchestration only).

## 2026-10-28 02:14:54 +05:30 — detached controller startup verification
Exact command: Get-Content reports/C2-controller-state.json; Get-Content reports/logs/C2-controller.stdout.log -Tail 12; Get-Content reports/logs/C2-controller.stderr.log (state existence checked before read)
Exit code: 0
Output:
~~~
{
  "state": "running",
  "phase": "waiting for already-running select --alpha",
  "pid": 18308,
  "updated": "2026-10-28T02:14:39+05:30"
}
2026-10-28T02:14:39+05:30 process-local awake request
2026-10-28T02:14:39+05:30 PHASE waiting for already-running select --alpha
2026-10-28T02:14:39+05:30 C2 continuation started

~~~
Read-only progress verification; LOG.md entry produced.

## 2026-10-28 02:17:41 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:17:41 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.5: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:18:32 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:18:32 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.5: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:19:22 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:19:22 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.5: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:20:13 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:20:13 +05:30
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.6.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.6
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.6: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:21:04 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:21:04 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.6: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:21:55 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:21:55 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.6: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:22:45 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:22:45 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.6: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:23:36 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:23:36 +05:30
percentile: median range ratio 0.840, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.6.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (229s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.7.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.7
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
~~~


## 2026-10-28 02:24:26 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:24:26 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.7: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:25:17 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:25:17 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.7: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:26:08 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:26:08 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.7: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:26:59 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:26:59 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.7: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:27:49 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:27:49 +05:30
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.8
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.8: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:28:40 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:28:40 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.8: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:29:31 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:29:31 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.8: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:30:21 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:30:21 +05:30
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.8: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
~~~


## 2026-10-28 02:31:12 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:31:12 +05:30
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\select_s4_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.3.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.4.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.5.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.6.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.7.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx
~~~


## 2026-10-28 02:32:03 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:32:03 +05:30
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\select_s4_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.3.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.4.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.5.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.6.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.7.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx
~~~


## 2026-10-28 02:32:54 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:32:54 +05:30
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\select_s4_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.3.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.4.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.5.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.6.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.7.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx
~~~


## 2026-10-28 02:33:44 +05:30 — background progress observation
Exact command: read reports/C2-controller-state.json; read last four alpha-log lines while waiting, otherwise last five controller stdout lines. Exit code: 0. No pipeline mutation.
~~~
C2_STATE_JSON {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"}
Observed 2026-10-28 02:33:44 +05:30
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\select_s4_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.3.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.4.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.5.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.6.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.7.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx
~~~


## 2026-10-28 02:34:04 +05:30 — compact background progress observation
Exact command: read reports/C2-controller-state.json and last 35 active log lines; omit repeated command/preprocessing warnings; print final two meaningful lines. Exit code: 0. Full logs preserved; no pipeline mutation.
~~~
C2_STATE {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"} Observed 2026-10-28 02:34:04 +05:30
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
~~~

## 2026-10-28 02:34:55 +05:30 — compact background progress observation
Exact command: read reports/C2-controller-state.json and last 35 active log lines; omit repeated command/preprocessing warnings; print final two meaningful lines. Exit code: 0. Full logs preserved; no pipeline mutation.
~~~
C2_STATE {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"} Observed 2026-10-28 02:34:55 +05:30
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
~~~

## 2026-10-28 02:35:45 +05:30 — compact background progress observation
Exact command: read reports/C2-controller-state.json and last 35 active log lines; omit repeated command/preprocessing warnings; print final two meaningful lines. Exit code: 0. Full logs preserved; no pipeline mutation.
~~~
C2_STATE {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"} Observed 2026-10-28 02:35:45 +05:30
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
~~~

## 2026-10-28 02:36:36 +05:30 — compact background progress observation
Exact command: read reports/C2-controller-state.json and last 35 active log lines; omit repeated command/preprocessing warnings; print final two meaningful lines. Exit code: 0. Full logs preserved; no pipeline mutation.
~~~
C2_STATE {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"} Observed 2026-10-28 02:36:36 +05:30
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
~~~

## 2026-10-28 02:37:27 +05:30 — compact background progress observation
Exact command: read reports/C2-controller-state.json and last 35 active log lines; omit repeated command/preprocessing warnings; print final two meaningful lines. Exit code: 0. Full logs preserved; no pipeline mutation.
~~~
C2_STATE {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"} Observed 2026-10-28 02:37:27 +05:30
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
~~~

## 2026-10-28 02:38:18 +05:30 — compact background progress observation
Exact command: read reports/C2-controller-state.json and last 35 active log lines; omit repeated command/preprocessing warnings; print final two meaningful lines. Exit code: 0. Full logs preserved; no pipeline mutation.
~~~
C2_STATE {"state":"running","phase":"waiting for already-running select --alpha","pid":18308,"updated":"2026-10-28T02:14:39+05:30"} Observed 2026-10-28 02:38:18 +05:30
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
~~~

## 2026-10-28 02:38:52 +05:30 — alpha selection completion
Exact command: ..\.venv\Scripts\python.exe -u ladder.py select --alpha
Exit code: 0
Key output:
~~~
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\select_s3_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p9999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_p99999.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s3_entropy.onnx
3360 positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz (ORT, not TensorRT)
model                               KL   top1    |dV|  tb_acc
ref bt3_fp32.onnx             0.00e+00  1.000  0.0000   0.998
s3_p999.onnx                  2.16e-01  0.707  0.1532   0.984
s3_p9999.onnx                 4.03e-02  0.839  0.0217   0.996
s3_p99999.onnx                2.20e-02  0.844  0.0128   0.997
s3_entropy.onnx               1.01e+00  0.214  0.5925   0.552

Pick step 3 from the table above (lowest KL / highest tb_acc), set recipe.s3_method and s3_percentile in the config, then rerun `select --alpha` for step 4.
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.3.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.3
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.3: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.825, min 0.476 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.3.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (233s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.4.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.4
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.4: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.829, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.4.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (231s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.5.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.5
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.5: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.835, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.5.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (232s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.6.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.6
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.6: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.840, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.6.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (229s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.7.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.7
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.7: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.846, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.7.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (225s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.8
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.8: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md 
percentile: median range ratio 0.849, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (228s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\select_s4_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.3.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.4.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.5.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.6.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.7.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\select\s4_a0.8.onnx
3360 positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz (ORT, not TensorRT)
model                               KL   top1    |dV|  tb_acc
ref bt3_fp32.onnx             0.00e+00  1.000  0.0000   0.998
s4_a0.3.onnx                  5.25e-03  0.871  0.0061   0.998
s4_a0.4.onnx                  4.83e-03  0.884  0.0049   0.998
s4_a0.5.onnx                  4.50e-03  0.900  0.0050   0.998
s4_a0.6.onnx                  4.45e-03  0.891  0.0051   0.999
s4_a0.7.onnx                  4.13e-03  0.891  0.0045   0.997
s4_a0.8.onnx                  4.14e-03  0.894  0.0066   0.998

Set recipe.s4_alpha in the config from the table above. If no alpha beats step 3, set best to s3.
~~~
Outputs: reports/logs/C2-select-alpha.log, reports/logs/C2-select-alpha.exitcode, reports/logs/select.log; models/select/s4_a*.onnx and *.json; reports/select_s3_dev.txt and reports/select_s4_dev.txt if completed.

## 2026-10-28T02:39:01+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s3_p999.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:01+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s3_p9999.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:02+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s3_p99999.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:02+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s3_entropy.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:02+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s4_a0.3.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:02+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s4_a0.4.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:02+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s4_a0.5.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:02+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s4_a0.6.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:02+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s4_a0.7.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:02+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\select\\s4_a0.8.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T02:39:02+05:30 — C2 mechanical recipe frozen
s3 s3_p99999.onnx: lowest finite dev KL 2.20e-02, top-1 0.844; s3 ties use higher top-1. Alpha 0.7: lowest eligible dev KL 4.13e-03, top-1 0.891 >= s3 0.844. best=s4. KL ties favor unsmoothed s3; equal alpha rows use smaller alpha deterministically.
All candidate rows:
{
  "s3": [
    {
      "name": "s3_p999.onnx",
      "kl": 0.216,
      "top1": 0.707,
      "dv": 0.1532,
      "tb_acc": 0.984
    },
    {
      "name": "s3_p9999.onnx",
      "kl": 0.0403,
      "top1": 0.839,
      "dv": 0.0217,
      "tb_acc": 0.996
    },
    {
      "name": "s3_p99999.onnx",
      "kl": 0.022,
      "top1": 0.844,
      "dv": 0.0128,
      "tb_acc": 0.997
    },
    {
      "name": "s3_entropy.onnx",
      "kl": 1.01,
      "top1": 0.214,
      "dv": 0.5925,
      "tb_acc": 0.552
    }
  ],
  "alpha": [
    {
      "name": "s4_a0.3.onnx",
      "kl": 0.00525,
      "top1": 0.871,
      "dv": 0.0061,
      "tb_acc": 0.998,
      "alpha": 0.3,
      "qualifies": true
    },
    {
      "name": "s4_a0.4.onnx",
      "kl": 0.00483,
      "top1": 0.884,
      "dv": 0.0049,
      "tb_acc": 0.998,
      "alpha": 0.4,
      "qualifies": true
    },
    {
      "name": "s4_a0.5.onnx",
      "kl": 0.0045,
      "top1": 0.9,
      "dv": 0.005,
      "tb_acc": 0.998,
      "alpha": 0.5,
      "qualifies": true
    },
    {
      "name": "s4_a0.6.onnx",
      "kl": 0.00445,
      "top1": 0.891,
      "dv": 0.0051,
      "tb_acc": 0.999,
      "alpha": 0.6,
      "qualifies": true
    },
    {
      "name": "s4_a0.7.onnx",
      "kl": 0.00413,
      "top1": 0.891,
      "dv": 0.0045,
      "tb_acc": 0.997,
      "alpha": 0.7,
      "qualifies": true
    },
    {
      "name": "s4_a0.8.onnx",
      "kl": 0.00414,
      "top1": 0.894,
      "dv": 0.0066,
      "tb_acc": 0.998,
      "alpha": 0.8,
      "qualifies": true
    }
  ]
}
Config diff:
~~~diff
--- config before
+++ config after
@@ -20,7 +20,7 @@
  "recipe": {
   "s3_method": "percentile",
   "s3_percentile": 99.999,
-  "s4_alpha": 0.5
+  "s4_alpha": 0.7
  },
  "best": "s4",
  "study": {

~~~
Produced: reports/C2-recipe-choice.json; reports/config.C2-before-alpha-choice.json; config.json.

## 2026-10-28T02:39:03+05:30 — C1 s4 backup verified before removal
Exact operation: shutil.copy2 for each explicitly listed source/destination, followed by SHA256 comparison.
Exit code: 0
[
  {
    "source": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.json",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\c1-s4-backup\\s4.json",
    "bytes": 50144,
    "sha256": "6f5552bc6cbc0c400448620e09b5fadc324fa9d1044c4ec31d8293e14933a07f"
  },
  {
    "source": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.onnx",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\c1-s4-backup\\s4.onnx",
    "bytes": 105829506,
    "sha256": "574f555e5aa2d6b49e319e268a2d572c640d802399246767f1ac58c7161893ec"
  },
  {
    "source": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.pb.gz",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\c1-s4-backup\\s4.pb.gz",
    "bytes": 92783432,
    "sha256": "717c520bc29431f4f791fd447ae7eb98c60688681998b5992a9d7a3525366820"
  }
]

## 2026-10-28T02:39:03+05:30 — C1 s4 originals removed
Exact operation: Path.unlink for the source paths in the verified manifest above; all are within C:\Users\HP\Desktop\LC0-B\leela-int8
Exit code: 0
Produced: reports/c1-s4-backup/manifest.json and backed-up s4.*. Originals removed to force s4 rebuild.

## 2026-10-28T02:39:03+05:30 — command start
Phase: build main variants
Cwd: C:\Users\HP\Desktop\LC0-B\leela-int8
Exact command: `C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py build --only s1,s2,s3,s4,s4aa,s0`
CPU-only environment: True; TEMP/TMP=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\tmp
Output: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-build-main.log
Exit code: running.

## 2026-10-28 02:39:09 +05:30 — compact background progress observation
Exact command: read reports/C2-controller-state.json and last 35 active log lines; omit repeated command/preprocessing warnings; print final two meaningful lines. Exit code: 0. Full logs preserved; no pipeline mutation.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:39:09 +05:30
2026-10-28T02:39:04+05:30 calibration planes match BT3's input format (INPUT_CLASSICAL_112_PLANE)
2026-10-28T02:39:05+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
~~~

## 2026-10-28 02:39:59 +05:30 — compact background progress observation
Exact command: read reports/C2-controller-state.json and last 35 active log lines; omit repeated command/preprocessing warnings; print final two meaningful lines. Exit code: 0. Full logs preserved; no pipeline mutation.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:39:59 +05:30
2026-10-28T02:39:32+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
2026-10-28T02:39:32+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
~~~

## 2026-10-28 02:40:16 +05:30 — selection and C1 backup read-back
Exact command: Get-Content reports/C2-recipe-choice.json; Get-Content reports/select_s4_dev.txt; Get-Content reports/c1-s4-backup/manifest.json; Get-Content config.json; Get-Content reports/logs/C2-controller.stdout.log -Tail 12; Get-Content reports/C2-controller-state.json
Exit code: 0
Output:
~~~
{
  "s3": {
    "name": "s3_p99999.onnx",
    "kl": 0.022,
    "top1": 0.844,
    "dv": 0.0128,
    "tb_acc": 0.997
  },
  "alpha": {
    "name": "s4_a0.7.onnx",
    "kl": 0.00413,
    "top1": 0.891,
    "dv": 0.0045,
    "tb_acc": 0.997,
    "alpha": 0.7,
    "qualifies": true
  },
  "alpha_rows": [
    {
      "name": "s4_a0.3.onnx",
      "kl": 0.00525,
      "top1": 0.871,
      "dv": 0.0061,
      "tb_acc": 0.998,
      "alpha": 0.3,
      "qualifies": true
    },
    {
      "name": "s4_a0.4.onnx",
      "kl": 0.00483,
      "top1": 0.884,
      "dv": 0.0049,
      "tb_acc": 0.998,
      "alpha": 0.4,
      "qualifies": true
    },
    {
      "name": "s4_a0.5.onnx",
      "kl": 0.0045,
      "top1": 0.9,
      "dv": 0.005,
      "tb_acc": 0.998,
      "alpha": 0.5,
      "qualifies": true
    },
    {
      "name": "s4_a0.6.onnx",
      "kl": 0.00445,
      "top1": 0.891,
      "dv": 0.0051,
      "tb_acc": 0.999,
      "alpha": 0.6,
      "qualifies": true
    },
    {
      "name": "s4_a0.7.onnx",
      "kl": 0.00413,
      "top1": 0.891,
      "dv": 0.0045,
      "tb_acc": 0.997,
      "alpha": 0.7,
      "qualifies": true
    },
    {
      "name": "s4_a0.8.onnx",
      "kl": 0.00414,
      "top1": 0.894,
      "dv": 0.0066,
      "tb_acc": 0.998,
      "alpha": 0.8,
      "qualifies": true
    }
  ],
  "recipe": {
    "s3_method": "percentile",
    "s3_percentile": 99.999,
    "s4_alpha": 0.7
  },
  "best": "s4",
  "reason": "s3 s3_p99999.onnx: lowest finite dev KL 2.20e-02, top-1 0.844; s3 ties use higher top-1. Alpha 0.7: lowest eligible dev KL 4.13e-03, top-1 0.891 >= s3 0.844. best=s4. KL ties favor unsmoothed s3; equal alpha rows use smaller alpha deterministically."
}
3360 positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz (ORT, not TensorRT)
model                               KL   top1    |dV|  tb_acc
ref bt3_fp32.onnx             0.00e+00  1.000  0.0000   0.998
s4_a0.3.onnx                  5.25e-03  0.871  0.0061   0.998
s4_a0.4.onnx                  4.83e-03  0.884  0.0049   0.998
s4_a0.5.onnx                  4.50e-03  0.900  0.0050   0.998
s4_a0.6.onnx                  4.45e-03  0.891  0.0051   0.999
s4_a0.7.onnx                  4.13e-03  0.891  0.0045   0.997
s4_a0.8.onnx                  4.14e-03  0.894  0.0066   0.998
[
  {
    "source": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.json",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\c1-s4-backup\\s4.json",
    "bytes": 50144,
    "sha256": "6f5552bc6cbc0c400448620e09b5fadc324fa9d1044c4ec31d8293e14933a07f"
  },
  {
    "source": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.onnx",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\c1-s4-backup\\s4.onnx",
    "bytes": 105829506,
    "sha256": "574f555e5aa2d6b49e319e268a2d572c640d802399246767f1ac58c7161893ec"
  },
  {
    "source": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.pb.gz",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\c1-s4-backup\\s4.pb.gz",
    "bytes": 92783432,
    "sha256": "717c520bc29431f4f791fd447ae7eb98c60688681998b5992a9d7a3525366820"
  }
]
{
 "lc0": "C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe",
 "trtexec": "C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe",
 "nsys": "C:/Users/HP/Desktop/LC0-B/tools/nsys/nsight_systems-windows-x86_64-2025.1.3.140-archive/nsight-systems/2025.1.3/target-windows-x64/nsys.exe",
 "bt3": "nets/BT3.pb.gz",
 "syzygy": "C:/Users/HP/Desktop/LC0-B/syzygy",
 "work": ".",
 "backend": "onnx-trt",
 "fp16_opts": "optimize=6",
 "int8_opts": "optimize=8",
 "native_backend": "onnx-trt",
 "native_opts": "optimize=6",
 "tbset": {
  "per_class": 400
 },
 "calib": {
  "random_games": 256,
  "n_tb": 256
 },
 "recipe": {
  "s3_method": "percentile",
  "s3_percentile": 99.999,
  "s4_alpha": 0.7
 },
 "best": "s4",
 "study": {
  "split": "test",
  "limit": 2437,
  "budgets": "0,100,400,800,1600",
  "threads": 1,
  "minibatch": 256,
  "models": "fp16,s1,s2,s3,s4,s4aa"
 },
 "extras": {
  "s0_in_study_b": false,
  "swap": true,
  "s1sp": true
 },
 "studyc": {
  "movetimes": "200,800",
  "models": "fp16,BEST",
  "limit": 0
 },
 "match": {
  "tc": "10+0.1",
  "pairs": 250
 },
 "hw": {
  "batch_sizes": "32,64,128,256",
  "bench_movetime": 10000
 }
}
2026-10-28T02:39:04+05:30 calibration planes match BT3's input format (INPUT_CLASSICAL_112_PLANE)
2026-10-28T02:39:04+05:30 $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx --granularity per-tensor --method minmax
2026-10-28T02:39:05+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:39:07+05:30 WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
2026-10-28T02:39:25+05:30 WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
2026-10-28T02:39:26+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (21s)
2026-10-28T02:39:26+05:30 $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz
2026-10-28T02:39:32+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
2026-10-28T02:39:32+05:30 $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.onnx --granularity per-channel --method percentile --percentile 99.999
2026-10-28T02:39:32+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:39:35+05:30 WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
2026-10-28T02:39:59+05:30 WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
{
  "state": "running",
  "phase": "build main variants",
  "pid": 18308,
  "updated": "2026-10-28T02:39:03+05:30"
}

~~~
No pipeline interruption: only the read-only polling observer was restarted to inspect this evidence. Detached controller continues.

## 2026-10-28 02:40:50 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:40:50 +05:30
2026-10-28T02:39:32+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
2026-10-28T02:39:32+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
~~~

## 2026-10-28 02:41:41 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:41:41 +05:30
2026-10-28T02:39:32+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
2026-10-28T02:39:32+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
~~~

## 2026-10-28 02:42:31 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:42:31 +05:30
2026-10-28T02:39:32+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
2026-10-28T02:39:32+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
~~~

## 2026-10-28 02:43:22 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:43:22 +05:30
2026-10-28T02:42:53+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:43:21+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
~~~

## 2026-10-28 02:44:13 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:44:13 +05:30
2026-10-28T02:43:21+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
2026-10-28T02:43:49+05:30 outlier report -> C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
~~~

## 2026-10-28 02:45:03 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:45:03 +05:30
2026-10-28T02:43:21+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
2026-10-28T02:43:49+05:30 outlier report -> C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
~~~

## 2026-10-28 02:45:54 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:45:54 +05:30
2026-10-28T02:43:21+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
2026-10-28T02:43:49+05:30 outlier report -> C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
~~~

## 2026-10-28 02:46:45 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:46:45 +05:30
2026-10-28T02:43:21+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
2026-10-28T02:43:49+05:30 outlier report -> C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
~~~

## 2026-10-28 02:47:35 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:47:35 +05:30
2026-10-28T02:47:15+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
2026-10-28T02:47:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
~~~

## 2026-10-28 02:48:26 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:48:26 +05:30
2026-10-28T02:47:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:47:44+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
~~~

## 2026-10-28 02:49:17 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:49:17 +05:30
2026-10-28T02:47:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:47:44+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
~~~

## 2026-10-28 02:50:07 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:50:07 +05:30
2026-10-28T02:47:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:47:44+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
~~~

## 2026-10-28 02:50:58 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:50:58 +05:30
2026-10-28T02:47:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:47:44+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
~~~

## 2026-10-28 02:51:49 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:51:49 +05:30
2026-10-28T02:51:46+05:30 percentile: median range ratio 0.814, min 0.345 over 373 activations
2026-10-28T02:51:47+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.onnx: 164 weight nodes + 31 act-act, 373 QuantizeLinear (271s)
~~~

## 2026-10-28 02:52:39 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:52:39 +05:30
2026-10-28T02:51:57+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:52:26+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
~~~

## 2026-10-28 02:53:30 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:53:30 +05:30
2026-10-28T02:51:57+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:52:26+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
~~~

## 2026-10-28 02:54:21 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:54:21 +05:30
2026-10-28T02:51:57+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:52:26+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
~~~

## 2026-10-28 02:55:12 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:55:12 +05:30
2026-10-28T02:51:57+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T02:52:26+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
~~~

## 2026-10-28 02:56:02 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:56:02 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28 02:56:53 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:56:53 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28 02:57:44 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:57:44 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28 02:58:35 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:58:35 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28 02:59:26 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 02:59:26 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28 03:00:17 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 03:00:17 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28 03:01:08 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 03:01:08 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28 03:01:59 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 03:01:59 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28 03:02:50 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 03:02:50 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28 03:03:41 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build main variants","pid":18308,"updated":"2026-10-28T02:39:03+05:30"} Observed 2026-10-28 03:03:41 +05:30
2026-10-28T02:55:40+05:30 wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
2026-10-28T02:55:53+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
~~~

## 2026-10-28T03:04:08+05:30 — command completion
Exact command: `C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py build --only s1,s2,s3,s4,s4aa,s0`
Exit code: 0
Elapsed command seconds: 1505.312
Authorized timing switch: False
Output file: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-build-main.log
Key output:
~~~
calibration planes match BT3's input format (INPUT_CLASSICAL_112_PLANE)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx --granularity per-tensor --method minmax
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (21s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.onnx --granularity per-channel --method percentile --percentile 99.999
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
percentile: median range ratio 0.829, min 0.478 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (195s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.7 --outlier-report C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.7: 101 groups smoothed
outlier report -> C:\Users\HP\Desktop\LC0-B\leela-int8\reports\outliers.txt
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
percentile: median range ratio 0.846, min 0.479 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (257s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.7 --act-act-matmul
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.7: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
percentile: median range ratio 0.814, min 0.345 over 373 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.onnx: 164 weight nodes + 31 act-act, 373 QuantizeLinear (271s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\prune24.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0_fp32.onnx
pruned 150 weights 2:4 (magnitude); median rel. weight error 0.362 -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0_fp32.onnx
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.7
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.7: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
percentile: median range ratio 0.878, min 0.612 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (224s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\quick_compare_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s2.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.onnx
3360 positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz (ORT, not TensorRT)
model                               KL   top1    |dV|  tb_acc
ref bt3_fp32.onnx             0.00e+00  1.000  0.0000   0.998
s1.onnx                       3.08e-02  0.827  0.0129   0.997
s2.onnx                       2.90e-02  0.827  0.0124   0.997
s3.onnx                       2.20e-02  0.844  0.0128   0.997
s4.onnx                       4.13e-03  0.891  0.0045   0.997
s4aa.onnx                     4.68e-03  0.884  0.0043   0.997
s0.onnx                       7.81e-01  0.455  1.4277   0.799
~~~

## 2026-10-28T03:04:08+05:30 — SparseGPT dependency stage inventory
Exact operation: read-only target/dependency traversal using existing targets/upstream_targets helpers.
Exit code: 0
Printed total stages: 98; pruning targets: 150.

## 2026-10-28T03:04:08+05:30 — command start
Phase: SparseGPT sequential with timing gate
Cwd: C:\Users\HP\Desktop\LC0-B\leela-int8
Exact command: `C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u quant/sparsegpt24.py --onnx models/bt3_fp32.onnx --calib data/calib.npz --out models/s1sp_fp32.onnx`
CPU-only environment: True; TEMP/TMP=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\tmp
Output: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-sparsegpt-sequential.log
Exit code: running.

## 2026-10-28 03:04:31 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:04:31 +05:30
2026-10-28T03:04:08+05:30 SparseGPT dependency stage inventory
2026-10-28T03:04:08+05:30 command start
~~~

## 2026-10-28T03:04:55+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=46.0s, completed stages=2, total stages=98; 46.0/2*98=2254.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:05:08+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=59.0s, completed stages=3, total stages=98; 59.0/3*98=1927.3s, threshold=5400s (90 minutes).

## 2026-10-28 03:05:22 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:05:22 +05:30
2026-10-28T03:05:08+05:30   stage 3: 1 layers, 147 left (59s)
2026-10-28T03:05:08+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=59.0s, completed stages=3, total stages=98; 59.0/3*98=1927.3s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:05:24+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=75.0s, completed stages=4, total stages=98; 75.0/4*98=1837.5s, threshold=5400s (90 minutes).

## 2026-10-28T03:05:40+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=91.0s, completed stages=5, total stages=98; 91.0/5*98=1783.6s, threshold=5400s (90 minutes).

## 2026-10-28T03:05:59+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=110.0s, completed stages=6, total stages=98; 110.0/6*98=1796.7s, threshold=5400s (90 minutes).

## 2026-10-28 03:06:13 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:06:13 +05:30
2026-10-28T03:05:59+05:30 SparseGPT stage projection
2026-10-28T03:06:13+05:30   warning: /encoder0/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
SparseGPT timing: elapsed=110.0s, completed stages=6, total stages=98; 110.0/6*98=1796.7s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:06:17+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=128.0s, completed stages=7, total stages=98; 128.0/7*98=1792.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:06:31+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=143.0s, completed stages=8, total stages=98; 143.0/8*98=1751.8s, threshold=5400s (90 minutes).

## 2026-10-28T03:06:46+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=158.0s, completed stages=9, total stages=98; 158.0/9*98=1720.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:07:02+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=173.0s, completed stages=10, total stages=98; 173.0/10*98=1695.4s, threshold=5400s (90 minutes).

## 2026-10-28 03:07:03 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:07:03 +05:30
2026-10-28T03:07:02+05:30   stage 10: 1 layers, 137 left (173s)
2026-10-28T03:07:02+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=173.0s, completed stages=10, total stages=98; 173.0/10*98=1695.4s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:07:18+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=189.0s, completed stages=11, total stages=98; 189.0/11*98=1683.8s, threshold=5400s (90 minutes).

## 2026-10-28T03:07:37+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=208.0s, completed stages=12, total stages=98; 208.0/12*98=1698.7s, threshold=5400s (90 minutes).

## 2026-10-28 03:07:54 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:07:54 +05:30
2026-10-28T03:07:37+05:30 SparseGPT stage projection
2026-10-28T03:07:50+05:30   warning: /encoder1/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
SparseGPT timing: elapsed=208.0s, completed stages=12, total stages=98; 208.0/12*98=1698.7s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:07:54+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=226.0s, completed stages=13, total stages=98; 226.0/13*98=1703.7s, threshold=5400s (90 minutes).

## 2026-10-28T03:08:09+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=240.0s, completed stages=14, total stages=98; 240.0/14*98=1680.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:08:24+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=255.0s, completed stages=15, total stages=98; 255.0/15*98=1666.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:08:40+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=271.0s, completed stages=16, total stages=98; 271.0/16*98=1659.9s, threshold=5400s (90 minutes).

## 2026-10-28 03:08:45 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:08:45 +05:30
2026-10-28T03:08:40+05:30   stage 16: 1 layers, 128 left (271s)
2026-10-28T03:08:40+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=271.0s, completed stages=16, total stages=98; 271.0/16*98=1659.9s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:08:56+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=287.0s, completed stages=17, total stages=98; 287.0/17*98=1654.5s, threshold=5400s (90 minutes).

## 2026-10-28T03:09:15+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=306.0s, completed stages=18, total stages=98; 306.0/18*98=1666.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:09:32+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=324.0s, completed stages=19, total stages=98; 324.0/19*98=1671.2s, threshold=5400s (90 minutes).

## 2026-10-28 03:09:36 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:09:36 +05:30
2026-10-28T03:09:32+05:30   stage 19: 1 layers, 122 left (324s)
2026-10-28T03:09:32+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=324.0s, completed stages=19, total stages=98; 324.0/19*98=1671.2s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:09:47+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=338.0s, completed stages=20, total stages=98; 338.0/20*98=1656.2s, threshold=5400s (90 minutes).

## 2026-10-28T03:10:02+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=353.0s, completed stages=21, total stages=98; 353.0/21*98=1647.3s, threshold=5400s (90 minutes).

## 2026-10-28T03:10:17+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=369.0s, completed stages=22, total stages=98; 369.0/22*98=1643.7s, threshold=5400s (90 minutes).

## 2026-10-28 03:10:26 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:10:26 +05:30
2026-10-28T03:10:17+05:30   stage 22: 1 layers, 119 left (369s)
2026-10-28T03:10:17+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=369.0s, completed stages=22, total stages=98; 369.0/22*98=1643.7s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:10:34+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=385.0s, completed stages=23, total stages=98; 385.0/23*98=1640.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:10:53+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=404.0s, completed stages=24, total stages=98; 404.0/24*98=1649.7s, threshold=5400s (90 minutes).

## 2026-10-28T03:11:10+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=422.0s, completed stages=25, total stages=98; 422.0/25*98=1654.2s, threshold=5400s (90 minutes).

## 2026-10-28 03:11:17 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:11:17 +05:30
2026-10-28T03:11:10+05:30   stage 25: 1 layers, 113 left (422s)
2026-10-28T03:11:10+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=422.0s, completed stages=25, total stages=98; 422.0/25*98=1654.2s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:11:25+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=437.0s, completed stages=26, total stages=98; 437.0/26*98=1647.2s, threshold=5400s (90 minutes).

## 2026-10-28T03:11:40+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=452.0s, completed stages=27, total stages=98; 452.0/27*98=1640.6s, threshold=5400s (90 minutes).

## 2026-10-28T03:11:56+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=467.0s, completed stages=28, total stages=98; 467.0/28*98=1634.5s, threshold=5400s (90 minutes).

## 2026-10-28 03:12:08 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:12:08 +05:30
2026-10-28T03:11:56+05:30   stage 28: 1 layers, 110 left (467s)
2026-10-28T03:11:56+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=467.0s, completed stages=28, total stages=98; 467.0/28*98=1634.5s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:12:12+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=484.0s, completed stages=29, total stages=98; 484.0/29*98=1635.6s, threshold=5400s (90 minutes).

## 2026-10-28T03:12:31+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=502.0s, completed stages=30, total stages=98; 502.0/30*98=1639.9s, threshold=5400s (90 minutes).

## 2026-10-28T03:12:49+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=520.0s, completed stages=31, total stages=98; 520.0/31*98=1643.9s, threshold=5400s (90 minutes).

## 2026-10-28 03:12:59 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:12:59 +05:30
2026-10-28T03:12:49+05:30   stage 31: 1 layers, 104 left (520s)
2026-10-28T03:12:49+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=520.0s, completed stages=31, total stages=98; 520.0/31*98=1643.9s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:13:03+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=535.0s, completed stages=32, total stages=98; 535.0/32*98=1638.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:13:18+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=549.0s, completed stages=33, total stages=98; 549.0/33*98=1630.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:13:34+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=565.0s, completed stages=34, total stages=98; 565.0/34*98=1628.5s, threshold=5400s (90 minutes).

## 2026-10-28 03:13:49 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:13:49 +05:30
2026-10-28T03:13:34+05:30   stage 34: 1 layers, 101 left (565s)
2026-10-28T03:13:34+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=565.0s, completed stages=34, total stages=98; 565.0/34*98=1628.5s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:13:50+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=581.0s, completed stages=35, total stages=98; 581.0/35*98=1626.8s, threshold=5400s (90 minutes).

## 2026-10-28T03:14:08+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=600.0s, completed stages=36, total stages=98; 600.0/36*98=1633.3s, threshold=5400s (90 minutes).

## 2026-10-28T03:14:26+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=617.0s, completed stages=37, total stages=98; 617.0/37*98=1634.2s, threshold=5400s (90 minutes).

## 2026-10-28 03:14:40 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:14:40 +05:30
2026-10-28T03:14:26+05:30   stage 37: 1 layers, 95 left (617s)
2026-10-28T03:14:26+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=617.0s, completed stages=37, total stages=98; 617.0/37*98=1634.2s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:14:41+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=632.0s, completed stages=38, total stages=98; 632.0/38*98=1629.9s, threshold=5400s (90 minutes).

## 2026-10-28T03:14:55+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=646.0s, completed stages=39, total stages=98; 646.0/39*98=1623.3s, threshold=5400s (90 minutes).

## 2026-10-28T03:15:11+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=662.0s, completed stages=40, total stages=98; 662.0/40*98=1621.9s, threshold=5400s (90 minutes).

## 2026-10-28T03:15:27+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=678.0s, completed stages=41, total stages=98; 678.0/41*98=1620.6s, threshold=5400s (90 minutes).

## 2026-10-28 03:15:31 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:15:31 +05:30
2026-10-28T03:15:27+05:30   stage 41: 1 layers, 91 left (678s)
2026-10-28T03:15:27+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=678.0s, completed stages=41, total stages=98; 678.0/41*98=1620.6s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:15:45+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=696.0s, completed stages=42, total stages=98; 696.0/42*98=1624.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:16:03+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=714.0s, completed stages=43, total stages=98; 714.0/43*98=1627.3s, threshold=5400s (90 minutes).

## 2026-10-28T03:16:17+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=729.0s, completed stages=44, total stages=98; 729.0/44*98=1623.7s, threshold=5400s (90 minutes).

## 2026-10-28 03:16:22 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:16:21 +05:30
2026-10-28T03:16:17+05:30   stage 44: 1 layers, 85 left (729s)
2026-10-28T03:16:17+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=729.0s, completed stages=44, total stages=98; 729.0/44*98=1623.7s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:16:33+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=744.0s, completed stages=45, total stages=98; 744.0/45*98=1620.3s, threshold=5400s (90 minutes).

## 2026-10-28T03:16:49+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=760.0s, completed stages=46, total stages=98; 760.0/46*98=1619.1s, threshold=5400s (90 minutes).

## 2026-10-28T03:17:05+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=777.0s, completed stages=47, total stages=98; 777.0/47*98=1620.1s, threshold=5400s (90 minutes).

## 2026-10-28 03:17:12 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:17:12 +05:30
2026-10-28T03:17:05+05:30   stage 47: 1 layers, 82 left (777s)
2026-10-28T03:17:05+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=777.0s, completed stages=47, total stages=98; 777.0/47*98=1620.1s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:17:24+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=795.0s, completed stages=48, total stages=98; 795.0/48*98=1623.1s, threshold=5400s (90 minutes).

## 2026-10-28T03:17:41+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=813.0s, completed stages=49, total stages=98; 813.0/49*98=1626.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:17:56+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=827.0s, completed stages=50, total stages=98; 827.0/50*98=1620.9s, threshold=5400s (90 minutes).

## 2026-10-28 03:18:03 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:18:03 +05:30
2026-10-28T03:17:56+05:30   stage 50: 1 layers, 76 left (827s)
2026-10-28T03:17:56+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=827.0s, completed stages=50, total stages=98; 827.0/50*98=1620.9s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:18:11+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=842.0s, completed stages=51, total stages=98; 842.0/51*98=1618.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:18:26+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=858.0s, completed stages=52, total stages=98; 858.0/52*98=1617.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:18:42+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=874.0s, completed stages=53, total stages=98; 874.0/53*98=1616.1s, threshold=5400s (90 minutes).

## 2026-10-28 03:18:54 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:18:54 +05:30
2026-10-28T03:18:42+05:30   stage 53: 1 layers, 73 left (874s)
2026-10-28T03:18:42+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=874.0s, completed stages=53, total stages=98; 874.0/53*98=1616.1s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:19:01+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=892.0s, completed stages=54, total stages=98; 892.0/54*98=1618.8s, threshold=5400s (90 minutes).

## 2026-10-28T03:19:18+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=910.0s, completed stages=55, total stages=98; 910.0/55*98=1621.5s, threshold=5400s (90 minutes).

## 2026-10-28T03:19:33+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=924.0s, completed stages=56, total stages=98; 924.0/56*98=1617.0s, threshold=5400s (90 minutes).

## 2026-10-28 03:19:45 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:19:45 +05:30
2026-10-28T03:19:33+05:30   stage 56: 1 layers, 67 left (924s)
2026-10-28T03:19:33+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=924.0s, completed stages=56, total stages=98; 924.0/56*98=1617.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:19:48+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=939.0s, completed stages=57, total stages=98; 939.0/57*98=1614.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:20:03+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=955.0s, completed stages=58, total stages=98; 955.0/58*98=1613.6s, threshold=5400s (90 minutes).

## 2026-10-28T03:20:19+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=971.0s, completed stages=59, total stages=98; 971.0/59*98=1612.8s, threshold=5400s (90 minutes).

## 2026-10-28 03:20:35 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:20:35 +05:30
2026-10-28T03:20:19+05:30   stage 59: 1 layers, 64 left (971s)
2026-10-28T03:20:19+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=971.0s, completed stages=59, total stages=98; 971.0/59*98=1612.8s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:20:38+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=989.0s, completed stages=60, total stages=98; 989.0/60*98=1615.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:20:56+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1007.0s, completed stages=61, total stages=98; 1007.0/61*98=1617.8s, threshold=5400s (90 minutes).

## 2026-10-28T03:21:10+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1021.0s, completed stages=62, total stages=98; 1021.0/62*98=1613.8s, threshold=5400s (90 minutes).

## 2026-10-28T03:21:25+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1036.0s, completed stages=63, total stages=98; 1036.0/63*98=1611.6s, threshold=5400s (90 minutes).

## 2026-10-28 03:21:26 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:21:26 +05:30
2026-10-28T03:21:25+05:30   stage 63: 1 layers, 57 left (1036s)
2026-10-28T03:21:25+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1036.0s, completed stages=63, total stages=98; 1036.0/63*98=1611.6s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:21:41+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1052.0s, completed stages=64, total stages=98; 1052.0/64*98=1610.9s, threshold=5400s (90 minutes).

## 2026-10-28T03:21:57+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1068.0s, completed stages=65, total stages=98; 1068.0/65*98=1610.2s, threshold=5400s (90 minutes).

## 2026-10-28T03:22:15+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1087.0s, completed stages=66, total stages=98; 1087.0/66*98=1614.0s, threshold=5400s (90 minutes).

## 2026-10-28 03:22:16 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:22:16 +05:30
2026-10-28T03:22:15+05:30   stage 66: 4 layers, 51 left (1087s)
2026-10-28T03:22:15+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1087.0s, completed stages=66, total stages=98; 1087.0/66*98=1614.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:22:33+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1104.0s, completed stages=67, total stages=98; 1104.0/67*98=1614.8s, threshold=5400s (90 minutes).

## 2026-10-28T03:22:47+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1119.0s, completed stages=68, total stages=98; 1119.0/68*98=1612.7s, threshold=5400s (90 minutes).

## 2026-10-28T03:23:02+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1134.0s, completed stages=69, total stages=98; 1134.0/69*98=1610.6s, threshold=5400s (90 minutes).

## 2026-10-28 03:23:07 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:23:07 +05:30
2026-10-28T03:23:02+05:30   stage 69: 1 layers, 48 left (1134s)
2026-10-28T03:23:02+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1134.0s, completed stages=69, total stages=98; 1134.0/69*98=1610.6s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:23:18+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1149.0s, completed stages=70, total stages=98; 1149.0/70*98=1608.6s, threshold=5400s (90 minutes).

## 2026-10-28T03:23:35+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1166.0s, completed stages=71, total stages=98; 1166.0/71*98=1609.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:23:53+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1184.0s, completed stages=72, total stages=98; 1184.0/72*98=1611.6s, threshold=5400s (90 minutes).

## 2026-10-28 03:23:58 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:23:58 +05:30
2026-10-28T03:23:53+05:30   stage 72: 4 layers, 42 left (1184s)
2026-10-28T03:23:53+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1184.0s, completed stages=72, total stages=98; 1184.0/72*98=1611.6s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:24:12+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1204.0s, completed stages=73, total stages=98; 1204.0/73*98=1616.3s, threshold=5400s (90 minutes).

## 2026-10-28T03:24:28+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1219.0s, completed stages=74, total stages=98; 1219.0/74*98=1614.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:24:44+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1235.0s, completed stages=75, total stages=98; 1235.0/75*98=1613.7s, threshold=5400s (90 minutes).

## 2026-10-28 03:24:49 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:24:49 +05:30
2026-10-28T03:24:44+05:30   stage 75: 1 layers, 39 left (1235s)
2026-10-28T03:24:44+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1235.0s, completed stages=75, total stages=98; 1235.0/75*98=1613.7s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:25:01+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1252.0s, completed stages=76, total stages=98; 1252.0/76*98=1614.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:25:18+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1270.0s, completed stages=77, total stages=98; 1270.0/77*98=1616.4s, threshold=5400s (90 minutes).

## 2026-10-28T03:25:38+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1289.0s, completed stages=78, total stages=98; 1289.0/78*98=1619.5s, threshold=5400s (90 minutes).

## 2026-10-28 03:25:40 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:25:40 +05:30
2026-10-28T03:25:38+05:30   stage 78: 4 layers, 33 left (1289s)
2026-10-28T03:25:38+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1289.0s, completed stages=78, total stages=98; 1289.0/78*98=1619.5s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:25:57+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1308.0s, completed stages=79, total stages=98; 1308.0/79*98=1622.6s, threshold=5400s (90 minutes).

## 2026-10-28T03:26:13+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1324.0s, completed stages=80, total stages=98; 1324.0/80*98=1621.9s, threshold=5400s (90 minutes).

## 2026-10-28T03:26:29+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1340.0s, completed stages=81, total stages=98; 1340.0/81*98=1621.2s, threshold=5400s (90 minutes).

## 2026-10-28 03:26:30 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:26:30 +05:30
2026-10-28T03:26:29+05:30   stage 81: 1 layers, 30 left (1340s)
2026-10-28T03:26:29+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1340.0s, completed stages=81, total stages=98; 1340.0/81*98=1621.2s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:26:46+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1357.0s, completed stages=82, total stages=98; 1357.0/82*98=1621.8s, threshold=5400s (90 minutes).

## 2026-10-28T03:27:03+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1375.0s, completed stages=83, total stages=98; 1375.0/83*98=1623.5s, threshold=5400s (90 minutes).

## 2026-10-28 03:27:21 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:27:21 +05:30
2026-10-28T03:27:03+05:30   stage 83: 1 layers, 28 left (1375s)
2026-10-28T03:27:03+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1375.0s, completed stages=83, total stages=98; 1375.0/83*98=1623.5s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:27:23+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1395.0s, completed stages=84, total stages=98; 1395.0/84*98=1627.5s, threshold=5400s (90 minutes).

## 2026-10-28T03:27:42+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1414.0s, completed stages=85, total stages=98; 1414.0/85*98=1630.3s, threshold=5400s (90 minutes).

## 2026-10-28T03:27:58+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1430.0s, completed stages=86, total stages=98; 1430.0/86*98=1629.5s, threshold=5400s (90 minutes).

## 2026-10-28 03:28:12 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:28:12 +05:30
2026-10-28T03:27:58+05:30   stage 86: 1 layers, 22 left (1430s)
2026-10-28T03:27:58+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1430.0s, completed stages=86, total stages=98; 1430.0/86*98=1629.5s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:28:14+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1445.0s, completed stages=87, total stages=98; 1445.0/87*98=1627.7s, threshold=5400s (90 minutes).

## 2026-10-28T03:28:29+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1461.0s, completed stages=88, total stages=98; 1461.0/88*98=1627.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:28:45+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1477.0s, completed stages=89, total stages=98; 1477.0/89*98=1626.4s, threshold=5400s (90 minutes).

## 2026-10-28 03:29:02 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:29:02 +05:30
2026-10-28T03:28:45+05:30   stage 89: 1 layers, 19 left (1477s)
2026-10-28T03:28:45+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1477.0s, completed stages=89, total stages=98; 1477.0/89*98=1626.4s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:29:04+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1496.0s, completed stages=90, total stages=98; 1496.0/90*98=1629.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:29:22+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1514.0s, completed stages=91, total stages=98; 1514.0/91*98=1630.5s, threshold=5400s (90 minutes).

## 2026-10-28T03:29:37+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1528.0s, completed stages=92, total stages=98; 1528.0/92*98=1627.7s, threshold=5400s (90 minutes).

## 2026-10-28T03:29:52+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1543.0s, completed stages=93, total stages=98; 1543.0/93*98=1626.0s, threshold=5400s (90 minutes).

## 2026-10-28 03:29:53 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:29:53 +05:30
2026-10-28T03:29:52+05:30   stage 93: 1 layers, 12 left (1543s)
2026-10-28T03:29:52+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1543.0s, completed stages=93, total stages=98; 1543.0/93*98=1626.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:30:08+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1559.0s, completed stages=94, total stages=98; 1559.0/94*98=1625.3s, threshold=5400s (90 minutes).

## 2026-10-28T03:30:24+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1575.0s, completed stages=95, total stages=98; 1575.0/95*98=1624.7s, threshold=5400s (90 minutes).

## 2026-10-28T03:30:39+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1590.0s, completed stages=96, total stages=98; 1590.0/96*98=1623.1s, threshold=5400s (90 minutes).

## 2026-10-28 03:30:44 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"SparseGPT sequential with timing gate","pid":18308,"updated":"2026-10-28T03:04:08+05:30"} Observed 2026-10-28 03:30:44 +05:30
2026-10-28T03:30:39+05:30   stage 96: 3 layers, 7 left (1590s)
2026-10-28T03:30:39+05:30 SparseGPT stage projection
SparseGPT timing: elapsed=1590.0s, completed stages=96, total stages=98; 1590.0/96*98=1623.1s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:30:59+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1611.0s, completed stages=97, total stages=98; 1611.0/97*98=1627.6s, threshold=5400s (90 minutes).

## 2026-10-28T03:31:13+05:30 — SparseGPT stage projection
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).

## 2026-10-28T03:31:13+05:30 — command completion
Exact command: `C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u quant/sparsegpt24.py --onnx models/bt3_fp32.onnx --calib data/calib.npz --out models/s1sp_fp32.onnx`
Exit code: 0
Elapsed command seconds: 1625.046
Authorized timing switch: False
Output file: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-sparsegpt-sequential.log
Key output:
~~~
  stage 32: 1 layers, 103 left (535s)
  stage 33: 1 layers, 102 left (549s)
  stage 34: 1 layers, 101 left (565s)
  stage 35: 1 layers, 100 left (581s)
  stage 36: 4 layers, 96 left (600s)
  warning: /encoder5/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 37: 1 layers, 95 left (617s)
  stage 38: 1 layers, 94 left (632s)
  stage 39: 1 layers, 93 left (646s)
  stage 40: 1 layers, 92 left (662s)
  stage 41: 1 layers, 91 left (678s)
  stage 42: 4 layers, 87 left (696s)
  warning: /encoder6/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 43: 1 layers, 86 left (714s)
  stage 44: 1 layers, 85 left (729s)
  stage 45: 1 layers, 84 left (744s)
  stage 46: 1 layers, 83 left (760s)
  stage 47: 1 layers, 82 left (777s)
  stage 48: 4 layers, 78 left (795s)
  warning: /encoder7/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 49: 1 layers, 77 left (813s)
  stage 50: 1 layers, 76 left (827s)
  stage 51: 1 layers, 75 left (842s)
  stage 52: 1 layers, 74 left (858s)
  stage 53: 1 layers, 73 left (874s)
  stage 54: 4 layers, 69 left (892s)
  warning: /encoder8/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 55: 1 layers, 68 left (910s)
  stage 56: 1 layers, 67 left (924s)
  stage 57: 1 layers, 66 left (939s)
  stage 58: 1 layers, 65 left (955s)
  stage 59: 1 layers, 64 left (971s)
  stage 60: 4 layers, 60 left (989s)
  warning: /encoder9/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 61: 1 layers, 59 left (1007s)
  stage 62: 1 layers, 58 left (1021s)
  stage 63: 1 layers, 57 left (1036s)
  stage 64: 1 layers, 56 left (1052s)
  stage 65: 1 layers, 55 left (1068s)
  stage 66: 4 layers, 51 left (1087s)
  warning: /encoder10/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 67: 1 layers, 50 left (1104s)
  stage 68: 1 layers, 49 left (1119s)
  stage 69: 1 layers, 48 left (1134s)
  stage 70: 1 layers, 47 left (1149s)
  stage 71: 1 layers, 46 left (1166s)
  stage 72: 4 layers, 42 left (1184s)
  warning: /encoder11/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 73: 1 layers, 41 left (1204s)
  stage 74: 1 layers, 40 left (1219s)
  stage 75: 1 layers, 39 left (1235s)
  stage 76: 1 layers, 38 left (1252s)
  stage 77: 1 layers, 37 left (1270s)
  stage 78: 4 layers, 33 left (1289s)
  warning: /encoder12/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 79: 1 layers, 32 left (1308s)
  stage 80: 1 layers, 31 left (1324s)
  stage 81: 1 layers, 30 left (1340s)
  stage 82: 1 layers, 29 left (1357s)
  stage 83: 1 layers, 28 left (1375s)
  stage 84: 4 layers, 24 left (1395s)
  warning: /encoder13/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 85: 1 layers, 23 left (1414s)
  stage 86: 1 layers, 22 left (1430s)
  stage 87: 1 layers, 21 left (1445s)
  stage 88: 1 layers, 20 left (1461s)
  stage 89: 1 layers, 19 left (1477s)
  stage 90: 4 layers, 15 left (1496s)
  warning: /encoder14/smolgen/dense1/w/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 91: 1 layers, 14 left (1514s)
  stage 92: 1 layers, 13 left (1528s)
  stage 93: 1 layers, 12 left (1543s)
  stage 94: 1 layers, 11 left (1559s)
  stage 95: 1 layers, 10 left (1575s)
  stage 96: 3 layers, 7 left (1590s)
  warning: /value/dense1/matmul/w: 512 calibration rows for K=2048 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  warning: /mlh/dense1/matmul/w: 512 calibration rows for K=512 inputs; H is poorly conditioned, so SparseGPT may overfit this layer (more calibration positions help)
  stage 97: 4 layers, 3 left (1611s)
  stage 98: 3 layers, 0 left (1624s)
pruned 150 weights in 98 stages; median layer reconstruction error 0.0069 (magnitude would be 0.0895) -> models/s1sp_fp32.onnx (1625s)
~~~

## 2026-10-28T03:31:13+05:30 — command start
Phase: build SparseGPT quantization and swaps
Cwd: C:\Users\HP\Desktop\LC0-B\leela-int8
Exact command: `C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py build --only s1sp,swap_pol8,swap_val8`
CPU-only environment: True; TEMP/TMP=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\tmp
Output: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-build-extras.log
Exit code: running.

## 2026-10-28 03:31:35 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build SparseGPT quantization and swaps","pid":18308,"updated":"2026-10-28T03:31:13+05:30"} Observed 2026-10-28 03:31:35 +05:30
2026-10-28T03:31:15+05:30 calibration planes match BT3's input format (INPUT_CLASSICAL_112_PLANE)
2026-10-28T03:31:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28 03:32:25 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build SparseGPT quantization and swaps","pid":18308,"updated":"2026-10-28T03:31:13+05:30"} Observed 2026-10-28 03:32:25 +05:30
2026-10-28T03:31:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T03:31:45+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28 03:33:16 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build SparseGPT quantization and swaps","pid":18308,"updated":"2026-10-28T03:31:13+05:30"} Observed 2026-10-28 03:33:16 +05:30
2026-10-28T03:31:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T03:31:45+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28 03:34:07 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build SparseGPT quantization and swaps","pid":18308,"updated":"2026-10-28T03:31:13+05:30"} Observed 2026-10-28 03:34:07 +05:30
2026-10-28T03:31:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T03:31:45+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28 03:34:58 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build SparseGPT quantization and swaps","pid":18308,"updated":"2026-10-28T03:31:13+05:30"} Observed 2026-10-28 03:34:58 +05:30
2026-10-28T03:31:15+05:30 512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
2026-10-28T03:31:45+05:30 SmoothQuant alpha=0.7: 101 groups smoothed
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28 03:35:48 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build SparseGPT quantization and swaps","pid":18308,"updated":"2026-10-28T03:31:13+05:30"} Observed 2026-10-28 03:35:48 +05:30
2026-10-28T03:35:37+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_pol8.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_pol8.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
2026-10-28T03:35:40+05:30 policy from C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx, value from C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx (734 + 1525 nodes)
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28 03:36:39 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build SparseGPT quantization and swaps","pid":18308,"updated":"2026-10-28T03:31:13+05:30"} Observed 2026-10-28 03:36:39 +05:30
2026-10-28T03:35:40+05:30 policy from C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx, value from C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx (734 + 1525 nodes)
2026-10-28T03:36:01+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28 03:37:30 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build SparseGPT quantization and swaps","pid":18308,"updated":"2026-10-28T03:31:13+05:30"} Observed 2026-10-28 03:37:30 +05:30
2026-10-28T03:35:40+05:30 policy from C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx, value from C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx (734 + 1525 nodes)
2026-10-28T03:36:01+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28 03:38:21 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"build SparseGPT quantization and swaps","pid":18308,"updated":"2026-10-28T03:31:13+05:30"} Observed 2026-10-28 03:38:21 +05:30
2026-10-28T03:35:40+05:30 policy from C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx, value from C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx (734 + 1525 nodes)
2026-10-28T03:36:01+05:30 wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
SparseGPT timing: elapsed=1624.0s, completed stages=98, total stages=98; 1624.0/98*98=1624.0s, threshold=5400s (90 minutes).
~~~

## 2026-10-28T03:38:25+05:30 — command completion
Exact command: `C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py build --only s1sp,swap_pol8,swap_val8`
Exit code: 0
Elapsed command seconds: 431.454
Authorized timing switch: False
Output file: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-build-extras.log
Key output:
~~~
calibration planes match BT3's input format (INPUT_CLASSICAL_112_PLANE)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\quantize.py --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1sp_fp32.onnx --calib C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1sp.onnx --granularity per-channel --method percentile --percentile 99.999 --smoothquant 0.7
512 calibration positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\calib.npz
SmoothQuant alpha=0.7: 101 groups smoothed
WARNING:root:Please consider to run pre-processing before quantization. Refer to example: https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
WARNING:root:Please consider pre-processing before quantization. See https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md
percentile: median range ratio 0.852, min 0.473 over 280 activations
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1sp.onnx: 164 weight nodes + 0 act-act, 280 QuantizeLinear (226s)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1sp.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1sp.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1sp.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1sp.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\stitch_swap.py --policy C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --value C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_pol8.onnx
policy from C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx, value from C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_pol8.onnx (1515 + 732 nodes)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_pol8.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_pol8.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_pol8.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_pol8.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\stitch_swap.py --policy C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --value C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx
policy from C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx, value from C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx (734 + 1525 nodes)
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\quant\wrap.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --orig nets/BT3.pb.gz --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.pb.gz
wrapped C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.onnx -> C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.pb.gz  Input=INPUT_CLASSICAL_112_PLANE Policy=POLICY_ATTENTION Value=VALUE_WDL MLH=MOVES_LEFT_V1
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\quick_compare.py --ref C:\Users\HP\Desktop\LC0-B\leela-int8\models\bt3_fp32.onnx --npz C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\quick_compare_dev.txt C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1sp.onnx
3360 positions from C:\Users\HP\Desktop\LC0-B\leela-int8\data\dev.npz (ORT, not TensorRT)
model                               KL   top1    |dV|  tb_acc
ref bt3_fp32.onnx             0.00e+00  1.000  0.0000   0.998
s1sp.onnx                     7.31e-02  0.799  0.0324   0.991
~~~

## 2026-10-28T03:38:25+05:30 — swap provenance sidecar
{
  "kind": "policy/value swap",
  "recipe_applies_to": "quantized component; other component is FP32 ONNX for FP16 engine fallback",
  "method": "percentile",
  "percentile": 99.999,
  "smoothquant": 0.7,
  "policy": {
    "model": "s4",
    "onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.onnx",
    "sha256": "24fd9a11bbc755962b98fab08dd49f9a721c797097dfb607183e27b7e76e1904"
  },
  "value_mlh": {
    "model": "fp16",
    "onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\bt3_fp32.onnx",
    "sha256": "937d5ac3d1ce9daafc7858f54166787924680c0c9c4aaab94d438402430db2b9"
  },
  "generated_by": "reports/c2_continue.py provenance only; stitch_swap.py emits no native JSON"
}
P Q nodes=270; V Q nodes=0
Produced: models/swap_pol8.json; no graph/code changes.

## 2026-10-28T03:38:26+05:30 — swap provenance sidecar
{
  "kind": "policy/value swap",
  "recipe_applies_to": "quantized component; other component is FP32 ONNX for FP16 engine fallback",
  "method": "percentile",
  "percentile": 99.999,
  "smoothquant": 0.7,
  "policy": {
    "model": "fp16",
    "onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\bt3_fp32.onnx",
    "sha256": "937d5ac3d1ce9daafc7858f54166787924680c0c9c4aaab94d438402430db2b9"
  },
  "value_mlh": {
    "model": "s4",
    "onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.onnx",
    "sha256": "24fd9a11bbc755962b98fab08dd49f9a721c797097dfb607183e27b7e76e1904"
  },
  "generated_by": "reports/c2_continue.py provenance only; stitch_swap.py emits no native JSON"
}
P Q nodes=0; V Q nodes=274
Produced: models/swap_val8.json; no graph/code changes.

## 2026-10-28T03:38:26+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s1.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 0}

## 2026-10-28T03:38:26+05:30 — model recipe verified
s1: {"granularity": "per-tensor", "method": "minmax", "percentile": null, "smoothquant": null, "act_act_matmul": false}
Expected from ladder.recipe_flags(config, 's1'): {"granularity": "per-tensor", "method": "minmax", "percentile": null, "smoothquant": null, "act_act_matmul": false}

## 2026-10-28T03:38:26+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s2.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 0}

## 2026-10-28T03:38:26+05:30 — model recipe verified
s2: {"granularity": "per-channel", "method": "minmax", "percentile": null, "smoothquant": null, "act_act_matmul": false}
Expected from ladder.recipe_flags(config, 's2'): {"granularity": "per-channel", "method": "minmax", "percentile": null, "smoothquant": null, "act_act_matmul": false}

## 2026-10-28T03:38:27+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s3.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T03:38:27+05:30 — model recipe verified
s3: {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": null, "act_act_matmul": false}
Expected from ladder.recipe_flags(config, 's3'): {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": null, "act_act_matmul": false}

## 2026-10-28T03:38:27+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T03:38:27+05:30 — model recipe verified
s4: {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": 0.7, "act_act_matmul": false}
Expected from ladder.recipe_flags(config, 's4'): {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": 0.7, "act_act_matmul": false}

## 2026-10-28T03:38:27+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4aa.onnx", "valid": true, "scale_tensors": 523, "clip_entries": 373}

## 2026-10-28T03:38:27+05:30 — model recipe verified
s4aa: {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": 0.7, "act_act_matmul": true}
Expected from ladder.recipe_flags(config, 's4aa'): {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": 0.7, "act_act_matmul": true}

## 2026-10-28T03:38:27+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s0.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T03:38:27+05:30 — model recipe verified
s0: {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": 0.7, "act_act_matmul": false}
Expected from ladder.recipe_flags(config, 's0'): {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": 0.7, "act_act_matmul": false}

## 2026-10-28T03:38:28+05:30 — scale/clip validation
{"file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s1sp.onnx", "valid": true, "scale_tensors": 430, "clip_entries": 280}

## 2026-10-28T03:38:28+05:30 — model recipe verified
s1sp: {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": 0.7, "act_act_matmul": false}
Expected from ladder.recipe_flags(config, 's1sp'): {"granularity": "per-channel", "method": "percentile", "percentile": 99.999, "smoothquant": 0.7, "act_act_matmul": false}

## 2026-10-28T03:38:29+05:30 — all build artifacts verified
[
  {
    "model": "s1",
    "recipe": {
      "method": "minmax",
      "percentile": null,
      "smoothquant": null
    },
    "files": [
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s1.onnx",
        "bytes": 104487495,
        "sha256": "3fb946f7df05d6079e9c5225fa17a358900a2debce462753f6d421796d25578a"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s1.pb.gz",
        "bytes": 71716055,
        "sha256": "9d714319f799ae8a19b0809d6380f3ec819e02704af52587dbbdc1fdc3e08b1f"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s1.json",
        "bytes": 458,
        "sha256": "ce22366ecf146039190c098494fb0ed42bbe33ad6bac1872bff9103aa61f1900"
      }
    ]
  },
  {
    "model": "s2",
    "recipe": {
      "method": "minmax",
      "percentile": null,
      "smoothquant": null
    },
    "files": [
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s2.onnx",
        "bytes": 105424621,
        "sha256": "02c5ac09362f62b80ab0f18a279a38f1e2d2c60db778b936fbda34ab753f1b54"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s2.pb.gz",
        "bytes": 95037093,
        "sha256": "b99af74303433a86d15ae39b6a805a2b8f156e2c59edf906bed70e7ad6bc97ab"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s2.json",
        "bytes": 459,
        "sha256": "953c354802798befc954ac27e4bf26bd6bf2236554ef1bb0f4cdc2d2939ef57e"
      }
    ]
  },
  {
    "model": "s3",
    "recipe": {
      "method": "percentile",
      "percentile": 99.999,
      "smoothquant": null
    },
    "files": [
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s3.onnx",
        "bytes": 105424621,
        "sha256": "60c283e77f04ace1b71873c6ecbddd601d6d22a1ad01b5156dbd2677b3fb70ff"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s3.pb.gz",
        "bytes": 95037368,
        "sha256": "d43dba92a9ac11da200b823ac8eb8ba9fb9ce3ecb31ada99d5561b100bd78364"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s3.json",
        "bytes": 30062,
        "sha256": "029176200387abe1cbbd99b87ce6ba6ebee9461824411cee367d81acbe11b54d"
      }
    ]
  },
  {
    "model": "s4",
    "recipe": {
      "method": "percentile",
      "percentile": 99.999,
      "smoothquant": 0.7
    },
    "files": [
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.onnx",
        "bytes": 105829506,
        "sha256": "24fd9a11bbc755962b98fab08dd49f9a721c797097dfb607183e27b7e76e1904"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.pb.gz",
        "bytes": 90915493,
        "sha256": "b556b45cab302ecf893c4afcd932c3df51358004a14f6e1ec9ef99fb21f75abb"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.json",
        "bytes": 50028,
        "sha256": "b75628f2384aa6e576d26190907fae6b6fde44e0a9b5aaa8b4209b1924249e9d"
      }
    ]
  },
  {
    "model": "s4aa",
    "recipe": {
      "method": "percentile",
      "percentile": 99.999,
      "smoothquant": 0.7
    },
    "files": [
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4aa.onnx",
        "bytes": 105880615,
        "sha256": "f7992eba5dda26b64d1a5ebd57d756aec8c053bc0e08f95de5a78a54e98f7b82"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4aa.pb.gz",
        "bytes": 90921041,
        "sha256": "6445a8bdf4fde85121c2c1dcef3babd9e62b23858444be3ac9c9d6b36b9bb284"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4aa.json",
        "bytes": 60010,
        "sha256": "ef5d36ce1d2d25406b381ca196d9b17f6c7c64de72dba90191ececd5d1faa937"
      }
    ]
  },
  {
    "model": "s0",
    "recipe": {
      "method": "percentile",
      "percentile": 99.999,
      "smoothquant": 0.7
    },
    "files": [
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s0.onnx",
        "bytes": 105829506,
        "sha256": "8871c0bd6cb9101b02271643dd06bd3b3b78ce0b9372103d9e2e7b2e1b4d5170"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s0.pb.gz",
        "bytes": 69978207,
        "sha256": "01976840b4de5de2a9299ecfda97fc9c56c626eb7e6a79c48f64aaf526d3afd4"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s0.json",
        "bytes": 50083,
        "sha256": "f80ca884cfde80a33b804fbc20ba3e8f15b414251567ad1409e5b75a290c70c7"
      }
    ]
  },
  {
    "model": "s1sp",
    "recipe": {
      "method": "percentile",
      "percentile": 99.999,
      "smoothquant": 0.7
    },
    "files": [
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s1sp.onnx",
        "bytes": 105829506,
        "sha256": "6cee555e1c6199bf2960e6862ffe24c45d346fe88ad4321277a6da055dce348a"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s1sp.pb.gz",
        "bytes": 69089577,
        "sha256": "b3a020e0fda20925744f35b2540872f54deeec31dcb9f7229c67db80399d5ec9"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s1sp.json",
        "bytes": 49979,
        "sha256": "686060e0bce1604e3d8cf4f4a54b2ab2b04a4d64426cfc008d8770e342d6e64e"
      }
    ]
  },
  {
    "model": "swap_pol8",
    "recipe": {
      "method": "percentile",
      "percentile": 99.999,
      "smoothquant": 0.7
    },
    "files": [
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\swap_pol8.onnx",
        "bytes": 508700407,
        "sha256": "92da35c3df1ef37d66aac0909f2337b1a91685d289d10797d777e8fb16d94c51"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\swap_pol8.pb.gz",
        "bytes": 381896136,
        "sha256": "82d2f082d33c41fd3bd06280d99a6f35850e94f3fd4dc314d7fe234c60c24319"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\swap_pol8.json",
        "bytes": 719,
        "sha256": "3b4d75ef7cb031f1b16e5c4d291898926db8f6558ca9765c0e222c61a399baed"
      }
    ]
  },
  {
    "model": "swap_val8",
    "recipe": {
      "method": "percentile",
      "percentile": 99.999,
      "smoothquant": 0.7
    },
    "files": [
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\swap_val8.onnx",
        "bytes": 512938981,
        "sha256": "40bd6f0aae177df4225ce4048302ba76f267dc5a16f001593ba31227f266b56d"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\swap_val8.pb.gz",
        "bytes": 384327326,
        "sha256": "f59515059aa106615ba0cfc188cff8317a7ca6b1e6eebbfa2a2367a41f210fe5"
      },
      {
        "path": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\swap_val8.json",
        "bytes": 719,
        "sha256": "714be9d4e3178423bc0931dc3a4111961d1e73c1d3cb8a2d4b4574d19a98bf0b"
      }
    ]
  }
]
Baseline exception is intentional: s1/s2 are fixed minmax ablations; selected recipes apply according to ladder.recipe_flags. Swaps mix the best recipe with the FP32 source.
Produced: reports/C2-build-manifest.json.

## 2026-10-28T03:38:29+05:30 — GPU pre-flight
Exact command: nvidia-smi
Exit code: 0
~~~
Wed Oct 28 03:38:29 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   46C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

~~~

## 2026-10-28T03:38:30+05:30 — GPU utilization check
Exact command: nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits
Exit code: 0
~~~
0, 0

~~~

## 2026-10-28T03:38:30+05:30 — study logging and resume
Exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py study
ladder.py itself appends commands/output to reports/logs/study.log. Controller separately captures console to reports/logs/C2-study-console.log to avoid duplicate writes to the canonical log.
Resume from leela-int8: ..\.venv\Scripts\python.exe -u ladder.py study

## 2026-10-28T03:38:30+05:30 — command start
Phase: study
Cwd: C:\Users\HP\Desktop\LC0-B\leela-int8
Exact command: `C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py study`
CPU-only environment: False; TEMP/TMP=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\tmp
Output: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-study-console.log
Exit code: running.

## 2026-10-28 03:39:11 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"study","pid":18308,"updated":"2026-10-28T03:38:30+05:30"} Observed 2026-10-28 03:39:11 +05:30
2026-10-28T03:38:49+05:30   [fp16 A] 2375/2387  0.01s/item  eta 0.0 min
2026-10-28T03:38:50+05:30   [fp16 A] 2387/2387  0.01s/item  eta 0.0 min
~~~

## 2026-10-28 03:40:02 +05:30 — C2 background observation
Exact command: read C2-controller-state.json and last 35 controller stdout lines, print last two meaningful lines; during SparseGPT also print latest timing projection from LOG.md tail. Exit code: 0. Observer only; no pipeline interruption.
~~~
C2_STATE {"state":"running","phase":"study","pid":18308,"updated":"2026-10-28T03:38:30+05:30"} Observed 2026-10-28 03:40:02 +05:30
2026-10-28T03:39:34+05:30   [fp16 B] 50/2387  0.87s/item  eta 34.1 min
2026-10-28T03:39:55+05:30   [fp16 B] 75/2387  0.87s/item  eta 33.4 min
~~~

## 2026-10-28 03:40:28 +05:30 — build and GPU pre-flight evidence read-back
Exact command: following Python via here-string piped to ..\.venv\Scripts\python.exe -
~~~python
from pathlib import Path
import json
m=json.loads(Path('reports/C2-build-manifest.json').read_text())
print('Verified build manifest:')
for r in m:
    print(r['model'],json.dumps(r['recipe']), 'files:',[(Path(f['path']).name,f['bytes']) for f in r['files']])
p=json.loads(Path('models/s1sp_fp32.json').read_text())
print('SparseGPT:',json.dumps({k:p[k] for k in ['method','one_shot','stages','n_calib','seconds']}))
log=Path('LOG.md').read_text()
for name in ['GPU pre-flight','GPU utilization check']:
    i=log.rfind('— '+name+'\n')
    j=log.find('\n## ',i+1)
    print(log[i:j if j>=0 else None])
print('Current state:',Path('reports/C2-controller-state.json').read_text())
print('Latest study output:')
print('\n'.join(Path('reports/logs/C2-study-console.log').read_text().splitlines()[-8:]))
print('Canonical study.log exists:',Path('reports/logs/study.log').exists())
~~~
Exit code: 1
Output:
~~~
Verified build manifest:
s1 {"method": "minmax", "percentile": null, "smoothquant": null} files: [('s1.onnx', 104487495), ('s1.pb.gz', 71716055), ('s1.json', 458)]
s2 {"method": "minmax", "percentile": null, "smoothquant": null} files: [('s2.onnx', 105424621), ('s2.pb.gz', 95037093), ('s2.json', 459)]
s3 {"method": "percentile", "percentile": 99.999, "smoothquant": null} files: [('s3.onnx', 105424621), ('s3.pb.gz', 95037368), ('s3.json', 30062)]
s4 {"method": "percentile", "percentile": 99.999, "smoothquant": 0.7} files: [('s4.onnx', 105829506), ('s4.pb.gz', 90915493), ('s4.json', 50028)]
s4aa {"method": "percentile", "percentile": 99.999, "smoothquant": 0.7} files: [('s4aa.onnx', 105880615), ('s4aa.pb.gz', 90921041), ('s4aa.json', 60010)]
s0 {"method": "percentile", "percentile": 99.999, "smoothquant": 0.7} files: [('s0.onnx', 105829506), ('s0.pb.gz', 69978207), ('s0.json', 50083)]
Traceback (most recent call last):
s1sp {"method": "percentile", "percentile": 99.999, "smoothquant": 0.7} files: [('s1sp.onnx', 105829506), ('s1sp.pb.gz', 69089577), ('s1sp.json', 49979)]
  File "<stdin>", line 9, in <module>
swap_pol8 {"method": "percentile", "percentile": 99.999, "smoothquant": 0.7} files: [('swap_pol8.onnx', 508700407), ('swap_pol8.pb.gz', 381896136), ('swap_pol8.json', 719)]
swap_val8 {"method": "percentile", "percentile": 99.999, "smoothquant": 0.7} files: [('swap_val8.onnx', 512938981), ('swap_val8.pb.gz', 384327326), ('swap_val8.json', 719)]
SparseGPT: {"method": "sparsegpt 2:4", "one_shot": false, "stages": 98, "n_calib": 512, "seconds": 1624.6}
  File "C:\Users\HP\AppData\Local\Programs\Python\Python311\Lib\pathlib.py", line 1059, in read_text
    return f.read()
           ^^^^^^^^
  File "C:\Users\HP\AppData\Local\Programs\Python\Python311\Lib\encodings\cp1252.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position 179126: character maps to <undefined>
~~~
Read-only reporting; detached study/controller continue. Produced LOG.md entry only.

## 2026-10-28 03:43:21 +05:30 — BLOCKED and stop after reporting read-back failure
Error: Reporting read-back failed: UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position 179126; LOG.md was read with Windows cp1252 instead of UTF-8. Read-back command exit 1.
The pipeline build itself had completed and the study was running; this failure was in the agent's read-only reporting command, not in quantization or the study engine. No alternative fix or additional pipeline command attempted.
Exact cleanup commands: Get-CimInstance Win32_Process -Filter ProcessId=18308; verify CommandLine contains c2_continue.py; taskkill /PID 18308 /T /F. Exit code: 0
Output:
~~~
SUCCESS: The process with PID 29996 (child process of PID 16044) has been terminated.
SUCCESS: The process with PID 16044 (child process of PID 15064) has been terminated.
SUCCESS: The process with PID 15064 (child process of PID 2252) has been terminated.
SUCCESS: The process with PID 2252 (child process of PID 300) has been terminated.
SUCCESS: The process with PID 300 (child process of PID 18308) has been terminated.
SUCCESS: The process with PID 18308 (child process of PID 16964) has been terminated.
~~~
Updated STATUS.md C2 continuation/study to BLOCKED; score and C2-done remain todo. Updated reports/C2-controller-state.json to BLOCKED. Produced reports/logs/C2-stopped-after-readback-error.log. All completed models, backups, and JSONL study records retained. Resume command from leela-int8 (for a subsequent authorized continuation): ..\.venv\Scripts\python.exe -u ladder.py study; then ..\.venv\Scripts\python.exe -u ladder.py score. No scoring/quantization code was changed.

## 2026-10-28 03:43:21 +05:30 — post-stop GPU verification
Exact command: nvidia-smi
Exit code: 0
Output:
~~~
Wed Oct 28 03:43:21 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   85C    P0             81W /  120W |       0MiB /   8188MiB |     91%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
~~~
No further pipeline work. BLOCKED awaiting user.

## 2026-10-28 05:34:16 +05:30 — user-authorized C2 resume and encoding policy
Initial read command (exit 0): Get-Content README.md -Encoding utf8; Get-Content RUN_4060.md -Encoding utf8; Get-Content STATUS.md -Encoding utf8; Get-Content config.json -Encoding utf8; Get-Content reports/c2_continue.py -Encoding utf8; Get-Content ladder.py -Encoding utf8; Get-Content eval/run_study.py -Encoding utf8; Get-Content eval/score.py -Encoding utf8.
LOG read, reporting only: [Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes(LOG.md)); print final 90 lines in try/catch. Replacement decoding, never on pipeline critical path. Existing LOG.md is not rewritten.
Future LOG.md writes append with Add-Content -Encoding utf8; STATUS.md writes use Set-Content -Encoding utf8. No quantization/scoring source or recipe changes authorized/needed.
Fresh GPU check exact command: nvidia-smi; exit code 0.
~~~
Wed Oct 28 05:34:16 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   40C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
~~~
Process check: Get-CimInstance Win32_Process filtered to owned C2/study Python/lc0 commands; exit 0.
~~~

~~~
Recipe: {"s3_method":"percentile","s3_percentile":99.999,"s4_alpha":0.7}; best=s4; study.limit=2437.
User authorizes one study resume after backup/tail JSON checks, one-minute continuation verification, then score and C2-done. Prior read-back encoding error is not a pipeline failure.

## 2026-10-28 05:37:03 +05:30 — resume orchestration encoding fix
Added reports/c2_resume.py (orchestration/reporting only) with tools.apply_patch. Existing LOG.md never rewritten. All future LOG.md/STATUS.md output goes through PowerShell Add-Content/Set-Content -Encoding utf8. No LOG.md read on pipeline critical path; optional reads use bytes and replacement decoding.
Exact syntax-check command: ..\.venv\Scripts\python.exe -m py_compile reports/c2_resume.py
Exit code: 0
Process-local PYTHONUTF8=1; PYTHONIOENCODING=utf-8 for consistent file/console encoding. No quantization or scoring source changed. No recipe/config/model changes. Produced reports/c2_resume.py and reports/__pycache__/c2_resume*.pyc.

## 2026-10-28T05:37:03+05:30 — study JSONL backups verified
Exact operation: shutil.copy2 for all results/**/study*.jsonl into C:\Users\HP\Desktop\LC0-B\leela-int8\reports\study-backup\2026-10-28T053703_0530; byte comparison before any edit. Exit code: 0.
[
  {
    "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\fp16\\study_a.jsonl",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\study-backup\\2026-10-28T053703_0530\\fp16\\study_a.jsonl",
    "before_bytes": 919000,
    "backup_sha256": "a2a77665c40506f86a911cc2f26904bab7f3e739496838b0b3d5cf16ed08e353",
    "tail_action": "not checked"
  },
  {
    "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\fp16\\study_b.jsonl",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\study-backup\\2026-10-28T053703_0530\\fp16\\study_b.jsonl",
    "before_bytes": 185157,
    "backup_sha256": "39114b10282f257ad330a4bf4b26acf2523277c248cf07f1fd6548ff230279f9",
    "tail_action": "not checked"
  },
  {
    "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\native\\study_a.jsonl",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\study-backup\\2026-10-28T053703_0530\\native\\study_a.jsonl",
    "before_bytes": 71373,
    "backup_sha256": "e3f44b9efecb1f5670cf8fa36b31af7c932453734b584ee8e36dc8aa32aa6ffe",
    "tail_action": "not checked"
  },
  {
    "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\s2\\study_a.jsonl",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\study-backup\\2026-10-28T053703_0530\\s2\\study_a.jsonl",
    "before_bytes": 70919,
    "backup_sha256": "3bfc8361402ab1c8ec9b33d7603cc0ec12641139e50c3e601a38009b48713ba8",
    "tail_action": "not checked"
  }
]


## 2026-10-28T05:37:04+05:30 — study tails checked and resume baseline recorded
[
  {
    "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\fp16\\study_a.jsonl",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\study-backup\\2026-10-28T053703_0530\\fp16\\study_a.jsonl",
    "before_bytes": 919000,
    "backup_sha256": "a2a77665c40506f86a911cc2f26904bab7f3e739496838b0b3d5cf16ed08e353",
    "tail_action": "last nonempty line parses as JSON; unchanged",
    "after_bytes": 919000,
    "after_sha256": "a2a77665c40506f86a911cc2f26904bab7f3e739496838b0b3d5cf16ed08e353"
  },
  {
    "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\fp16\\study_b.jsonl",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\study-backup\\2026-10-28T053703_0530\\fp16\\study_b.jsonl",
    "before_bytes": 185157,
    "backup_sha256": "39114b10282f257ad330a4bf4b26acf2523277c248cf07f1fd6548ff230279f9",
    "tail_action": "last nonempty line parses as JSON; unchanged",
    "after_bytes": 185157,
    "after_sha256": "39114b10282f257ad330a4bf4b26acf2523277c248cf07f1fd6548ff230279f9"
  },
  {
    "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\native\\study_a.jsonl",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\study-backup\\2026-10-28T053703_0530\\native\\study_a.jsonl",
    "before_bytes": 71373,
    "backup_sha256": "e3f44b9efecb1f5670cf8fa36b31af7c932453734b584ee8e36dc8aa32aa6ffe",
    "tail_action": "last nonempty line parses as JSON; unchanged",
    "after_bytes": 71373,
    "after_sha256": "e3f44b9efecb1f5670cf8fa36b31af7c932453734b584ee8e36dc8aa32aa6ffe"
  },
  {
    "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\s2\\study_a.jsonl",
    "backup": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\study-backup\\2026-10-28T053703_0530\\s2\\study_a.jsonl",
    "before_bytes": 70919,
    "backup_sha256": "3bfc8361402ab1c8ec9b33d7603cc0ec12641139e50c3e601a38009b48713ba8",
    "tail_action": "last nonempty line parses as JSON; unchanged",
    "after_bytes": 70919,
    "after_sha256": "3bfc8361402ab1c8ec9b33d7603cc0ec12641139e50c3e601a38009b48713ba8"
  }
]
| model | selected Study A done | selected Study B complete at all budgets | B done by budget |
|---|---|---|---|
| fp16 | 2437 | 383 | {"100": 384, "400": 384, "800": 384, "1600": 383} |
| s1 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s2 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s3 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s4 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s4aa | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| swap_pol8 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| swap_val8 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s1sp | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s0 | 0 | not required (S0 raw only) | {"100": 0, "400": 0, "800": 0, "1600": 0} |
Exit code: 0. Produced: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\study-backup\2026-10-28T053703_0530\manifest.json, C:\Users\HP\Desktop\LC0-B\leela-int8\reports\C2-resume-baseline.json, C:\Users\HP\Desktop\LC0-B\leela-int8\reports\C2-resume-prepared.json


## 2026-10-28 05:37:05 +05:30 — prepare command completion
Exact command: ..\.venv\Scripts\python.exe -u reports/c2_resume.py --prepare
Exit code: 0
Output captured in reports/logs/C2-resume-prepare.log; backup/tail/count details appended above with UTF-8. No LOG history rewrite.

## 2026-10-28 05:38:14 +05:30 — authorized background study continuation launched
Exact launch command: Start-Process -FilePath C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -ArgumentList @('-u','reports/c2_resume.py','--run') -WorkingDirectory C:\Users\HP\Desktop\LC0-B\leela-int8 -RedirectStandardOutput reports/logs/C2-resume.stdout.log -RedirectStandardError reports/logs/C2-resume.stderr.log -WindowStyle Hidden -PassThru
Exit code: 0 (launch). Printed launcher PID: 28740.
Exact pipeline resume command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py study
Cwd: C:\Users\HP\Desktop\LC0-B\leela-int8. Process-local PYTHONUTF8=1 and PYTHONIOENCODING=utf-8. ladder.py appends to reports/logs/study.log; outer console separately appends to reports/logs/C2-resume-study-console.log. A fresh nvidia-smi/idle check precedes launch. One-minute JSONL-prefix and per-model completed-position verification is scheduled in the runner. This is the one authorized resume; no automatic second launch. On success, score and C2-done follow automatically.
Produced: reports/logs/C2-resume.pid, C2-resume.stdout.log, C2-resume.stderr.log. LOG append uses -Encoding utf8; existing LOG never rewritten.

## 2026-10-28T05:38:15+05:30 — GPU pre-flight
Exact command: nvidia-smi
Exit code: 0
~~~
Wed Oct 28 05:38:14 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   40C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

~~~


## 2026-10-28T05:38:15+05:30 — GPU utilization check
Exact command: nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits
Exit code: 0
~~~
0, 0

~~~


## 2026-10-28T05:38:16+05:30 — authorized study resume start
Exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py study
Cwd: C:\Users\HP\Desktop\LC0-B\leela-int8
Process-local PYTHONUTF8=1 and PYTHONIOENCODING=utf-8, no algorithm/code/config changes. ladder.py appends its own reports/logs/study.log. Outer console is separately appended to C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-resume-study-console.log
Exit code: running. One resume only; no automatic second launch.


## 2026-10-28T05:39:17+05:30 — one-minute resume verification
{
  "checked": "2026-10-28T05:39:17+05:30",
  "elapsed_seconds": 60.39,
  "retained_file_prefixes": [
    {
      "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\fp16\\study_a.jsonl",
      "retained_prefix_bytes": 919000,
      "unchanged": true
    },
    {
      "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\fp16\\study_b.jsonl",
      "retained_prefix_bytes": 185157,
      "unchanged": true
    },
    {
      "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\native\\study_a.jsonl",
      "retained_prefix_bytes": 71373,
      "unchanged": true
    },
    {
      "file": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\results\\s2\\study_a.jsonl",
      "retained_prefix_bytes": 70919,
      "unchanged": true
    }
  ],
  "before": {
    "fp16": {
      "A": 2437,
      "B_all_budgets": 383,
      "B_by_budget": {
        "100": 384,
        "400": 384,
        "800": 384,
        "1600": 383
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 2637,
        "b": 1535
      },
      "B_required": true
    },
    "s1": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s2": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 200,
        "b": 0
      },
      "B_required": true
    },
    "s3": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s4": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s4aa": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "swap_pol8": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "swap_val8": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s1sp": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s0": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": false
    }
  },
  "after": {
    "fp16": {
      "A": 2437,
      "B_all_budgets": 447,
      "B_by_budget": {
        "100": 448,
        "400": 448,
        "800": 448,
        "1600": 447
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 2637,
        "b": 1791
      },
      "B_required": true
    },
    "s1": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s2": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 200,
        "b": 0
      },
      "B_required": true
    },
    "s3": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s4": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s4aa": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "swap_pol8": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "swap_val8": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s1sp": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": true
    },
    "s0": {
      "A": 0,
      "B_all_budgets": 0,
      "B_by_budget": {
        "100": 0,
        "400": 0,
        "800": 0,
        "1600": 0
      },
      "duplicate_selected_keys": 0,
      "total_rows_including_other_splits": {
        "a": 0,
        "b": 0
      },
      "B_required": false
    }
  },
  "progress_lines": [
    "  [fp16 B] 25/2054  1.15s/item  eta 39.0 min",
    "  [fp16 B] 50/2054  0.95s/item  eta 31.8 min"
  ],
  "verdict": "resuming: prior bytes and completed keys retained; no new duplicate keys"
}
Positions already done BEFORE resume:
| model | selected Study A done | selected Study B complete at all budgets | B done by budget |
|---|---|---|---|
| fp16 | 2437 | 383 | {"100": 384, "400": 384, "800": 384, "1600": 383} |
| s1 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s2 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s3 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s4 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s4aa | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| swap_pol8 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| swap_val8 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s1sp | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s0 | 0 | not required (S0 raw only) | {"100": 0, "400": 0, "800": 0, "1600": 0} |
Positions done AFTER one minute:
| model | selected Study A done | selected Study B complete at all budgets | B done by budget |
|---|---|---|---|
| fp16 | 2437 | 447 | {"100": 448, "400": 448, "800": 448, "1600": 447} |
| s1 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s2 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s3 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s4 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s4aa | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| swap_pol8 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| swap_val8 | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s1sp | 0 | 0 | {"100": 0, "400": 0, "800": 0, "1600": 0} |
| s0 | 0 | not required (S0 raw only) | {"100": 0, "400": 0, "800": 0, "1600": 0} |
Exit code: 0. Produced: reports/C2-resume-one-minute.json. No LOG.md reads used.


## 2026-10-28 05:39:32 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:39:32 +05:30
2026-10-28T05:39:17+05:30 | C2 one-minute resume check | done | resuming: prior bytes and completed keys retained; no new duplicate keys; reports/C2-resume-one-minute.json |
2026-10-28T05:39:26+05:30   [fp16 B] 75/2054  0.93s/item  eta 30.5 min
~~~

## 2026-10-28 05:40:22 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:40:22 +05:30
2026-10-28T05:39:49+05:30   [fp16 B] 100/2054  0.92s/item  eta 30.0 min
2026-10-28T05:40:14+05:30   [fp16 B] 125/2054  0.94s/item  eta 30.1 min
~~~

## 2026-10-28 05:41:13 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:41:13 +05:30
2026-10-28T05:40:39+05:30   [fp16 B] 150/2054  0.95s/item  eta 30.1 min
2026-10-28T05:41:04+05:30   [fp16 B] 175/2054  0.96s/item  eta 30.0 min
~~~

## 2026-10-28 05:42:03 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:42:03 +05:30
2026-10-28T05:41:28+05:30   [fp16 B] 200/2054  0.96s/item  eta 29.6 min
2026-10-28T05:41:52+05:30   [fp16 B] 225/2054  0.96s/item  eta 29.2 min
~~~

## 2026-10-28 05:42:54 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:42:54 +05:30
2026-10-28T05:42:16+05:30   [fp16 B] 250/2054  0.96s/item  eta 28.8 min
2026-10-28T05:42:39+05:30   [fp16 B] 275/2054  0.95s/item  eta 28.3 min
~~~

## 2026-10-28 05:43:44 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:43:44 +05:30
2026-10-28T05:43:01+05:30   [fp16 B] 300/2054  0.95s/item  eta 27.7 min
2026-10-28T05:43:25+05:30   [fp16 B] 325/2054  0.95s/item  eta 27.4 min
~~~

## 2026-10-28 05:44:35 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:44:35 +05:30
2026-10-28T05:44:12+05:30   [fp16 B] 375/2054  0.95s/item  eta 26.5 min
2026-10-28T05:44:34+05:30   [fp16 B] 400/2054  0.94s/item  eta 26.0 min
~~~

## 2026-10-28 05:45:25 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:45:25 +05:30
2026-10-28T05:44:56+05:30   [fp16 B] 425/2054  0.94s/item  eta 25.5 min
2026-10-28T05:45:18+05:30   [fp16 B] 450/2054  0.94s/item  eta 25.1 min
~~~

## 2026-10-28 05:46:15 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:46:15 +05:30
2026-10-28T05:45:41+05:30   [fp16 B] 475/2054  0.94s/item  eta 24.6 min
2026-10-28T05:46:05+05:30   [fp16 B] 500/2054  0.94s/item  eta 24.3 min
~~~

## 2026-10-28 05:47:06 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:47:06 +05:30
2026-10-28T05:46:27+05:30   [fp16 B] 525/2054  0.93s/item  eta 23.8 min
2026-10-28T05:46:48+05:30   [fp16 B] 550/2054  0.93s/item  eta 23.3 min
~~~

## 2026-10-28 05:47:56 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:47:56 +05:30
2026-10-28T05:47:32+05:30   [fp16 B] 600/2054  0.93s/item  eta 22.4 min
2026-10-28T05:47:53+05:30   [fp16 B] 625/2054  0.92s/item  eta 22.0 min
~~~

## 2026-10-28 05:48:47 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:48:47 +05:30
2026-10-28T05:48:15+05:30   [fp16 B] 650/2054  0.92s/item  eta 21.5 min
2026-10-28T05:48:38+05:30   [fp16 B] 675/2054  0.92s/item  eta 21.2 min
~~~

## 2026-10-28 05:49:37 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:49:37 +05:30
2026-10-28T05:49:16+05:30   [fp16 B] 725/2054  0.91s/item  eta 20.1 min
2026-10-28T05:49:36+05:30   [fp16 B] 750/2054  0.91s/item  eta 19.7 min
~~~

## 2026-10-28 05:50:27 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:50:27 +05:30
2026-10-28T05:49:54+05:30   [fp16 B] 775/2054  0.90s/item  eta 19.2 min
2026-10-28T05:50:15+05:30   [fp16 B] 800/2054  0.90s/item  eta 18.8 min
~~~

## 2026-10-28 05:51:18 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:51:18 +05:30
2026-10-28T05:50:51+05:30   [fp16 B] 850/2054  0.89s/item  eta 17.8 min
2026-10-28T05:51:10+05:30   [fp16 B] 875/2054  0.88s/item  eta 17.4 min
~~~

## 2026-10-28 05:52:08 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:52:08 +05:30
2026-10-28T05:51:46+05:30   [fp16 B] 925/2054  0.88s/item  eta 16.5 min
2026-10-28T05:52:03+05:30   [fp16 B] 950/2054  0.87s/item  eta 16.0 min
~~~

## 2026-10-28 05:52:59 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:52:59 +05:30
2026-10-28T05:52:23+05:30   [fp16 B] 975/2054  0.87s/item  eta 15.6 min
2026-10-28T05:52:45+05:30   [fp16 B] 1000/2054  0.87s/item  eta 15.2 min
~~~

## 2026-10-28 05:53:49 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:53:49 +05:30
2026-10-28T05:53:06+05:30   [fp16 B] 1025/2054  0.87s/item  eta 14.9 min
2026-10-28T05:53:30+05:30   [fp16 B] 1050/2054  0.87s/item  eta 14.6 min
~~~

## 2026-10-28 05:54:40 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:54:40 +05:30
2026-10-28T05:53:54+05:30   [fp16 B] 1075/2054  0.87s/item  eta 14.2 min
2026-10-28T05:54:21+05:30   [fp16 B] 1100/2054  0.88s/item  eta 13.9 min
~~~

## 2026-10-28 05:55:30 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:55:30 +05:30
2026-10-28T05:54:46+05:30   [fp16 B] 1125/2054  0.88s/item  eta 13.6 min
2026-10-28T05:55:12+05:30   [fp16 B] 1150/2054  0.88s/item  eta 13.3 min
~~~

## 2026-10-28 05:56:20 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:56:20 +05:30
2026-10-28T05:55:37+05:30   [fp16 B] 1175/2054  0.89s/item  eta 13.0 min
2026-10-28T05:56:02+05:30   [fp16 B] 1200/2054  0.89s/item  eta 12.6 min
~~~

## 2026-10-28 05:57:11 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:57:11 +05:30
2026-10-28T05:56:26+05:30   [fp16 B] 1225/2054  0.89s/item  eta 12.3 min
2026-10-28T05:56:51+05:30   [fp16 B] 1250/2054  0.89s/item  eta 11.9 min
~~~

## 2026-10-28 05:58:01 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:58:01 +05:30
2026-10-28T05:57:17+05:30   [fp16 B] 1275/2054  0.89s/item  eta 11.6 min
2026-10-28T05:57:41+05:30   [fp16 B] 1300/2054  0.90s/item  eta 11.3 min
~~~

## 2026-10-28 05:58:52 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:58:52 +05:30
2026-10-28T05:58:07+05:30   [fp16 B] 1325/2054  0.90s/item  eta 10.9 min
2026-10-28T05:58:32+05:30   [fp16 B] 1350/2054  0.90s/item  eta 10.6 min
~~~

## 2026-10-28 05:59:42 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 05:59:42 +05:30
2026-10-28T05:58:56+05:30   [fp16 B] 1375/2054  0.90s/item  eta 10.2 min
2026-10-28T05:59:21+05:30   [fp16 B] 1400/2054  0.90s/item  eta 9.8 min
~~~

## 2026-10-28 06:00:32 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:00:32 +05:30
2026-10-28T05:59:48+05:30   [fp16 B] 1425/2054  0.91s/item  eta 9.5 min
2026-10-28T06:00:14+05:30   [fp16 B] 1450/2054  0.91s/item  eta 9.1 min
~~~

## 2026-10-28 06:01:23 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:01:23 +05:30
2026-10-28T06:00:36+05:30   [fp16 B] 1475/2054  0.91s/item  eta 8.8 min
2026-10-28T06:00:59+05:30   [fp16 B] 1500/2054  0.91s/item  eta 8.4 min
~~~

## 2026-10-28 06:02:13 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:02:13 +05:30
2026-10-28T06:01:25+05:30   [fp16 B] 1525/2054  0.91s/item  eta 8.0 min
2026-10-28T06:01:49+05:30   [fp16 B] 1550/2054  0.91s/item  eta 7.7 min
~~~

## 2026-10-28 06:03:04 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:03:04 +05:30
2026-10-28T06:02:15+05:30   [fp16 B] 1575/2054  0.91s/item  eta 7.3 min
2026-10-28T06:02:40+05:30   [fp16 B] 1600/2054  0.91s/item  eta 6.9 min
~~~

## 2026-10-28 06:03:54 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:03:54 +05:30
2026-10-28T06:03:05+05:30   [fp16 B] 1625/2054  0.92s/item  eta 6.5 min
2026-10-28T06:03:31+05:30   [fp16 B] 1650/2054  0.92s/item  eta 6.2 min
~~~

## 2026-10-28 06:04:45 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:04:45 +05:30
2026-10-28T06:03:56+05:30   [fp16 B] 1675/2054  0.92s/item  eta 5.8 min
2026-10-28T06:04:24+05:30   [fp16 B] 1700/2054  0.92s/item  eta 5.4 min
~~~

## 2026-10-28 06:05:35 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:05:35 +05:30
2026-10-28T06:05:10+05:30   [fp16 B] 1750/2054  0.92s/item  eta 4.7 min
2026-10-28T06:05:33+05:30   [fp16 B] 1775/2054  0.92s/item  eta 4.3 min
~~~

## 2026-10-28 06:06:25 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:06:25 +05:30
2026-10-28T06:05:56+05:30   [fp16 B] 1800/2054  0.92s/item  eta 3.9 min
2026-10-28T06:06:24+05:30   [fp16 B] 1825/2054  0.92s/item  eta 3.5 min
~~~

## 2026-10-28 06:07:16 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:07:16 +05:30
2026-10-28T06:06:24+05:30   [fp16 B] 1825/2054  0.92s/item  eta 3.5 min
2026-10-28T06:06:51+05:30   [fp16 B] 1850/2054  0.93s/item  eta 3.2 min
~~~

## 2026-10-28 06:08:06 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:08:06 +05:30
2026-10-28T06:07:20+05:30   [fp16 B] 1875/2054  0.93s/item  eta 2.8 min
2026-10-28T06:07:46+05:30   [fp16 B] 1900/2054  0.93s/item  eta 2.4 min
~~~

## 2026-10-28 06:08:57 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:08:57 +05:30
2026-10-28T06:08:15+05:30   [fp16 B] 1925/2054  0.93s/item  eta 2.0 min
2026-10-28T06:08:44+05:30   [fp16 B] 1950/2054  0.94s/item  eta 1.6 min
~~~

## 2026-10-28 06:09:47 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:09:47 +05:30
2026-10-28T06:09:10+05:30   [fp16 B] 1975/2054  0.94s/item  eta 1.2 min
2026-10-28T06:09:36+05:30   [fp16 B] 2000/2054  0.94s/item  eta 0.8 min
~~~

## 2026-10-28 06:10:38 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:10:38 +05:30
2026-10-28T06:10:31+05:30   [fp16 B] 2054/2054  0.94s/item  eta 0.0 min
2026-10-28T06:10:32+05:30 s1: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 06:11:28 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:11:28 +05:30
2026-10-28T06:10:31+05:30   [fp16 B] 2054/2054  0.94s/item  eta 0.0 min
2026-10-28T06:10:32+05:30 s1: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 06:12:18 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:12:18 +05:30
2026-10-28T06:10:31+05:30   [fp16 B] 2054/2054  0.94s/item  eta 0.0 min
2026-10-28T06:10:32+05:30 s1: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 06:13:09 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:13:09 +05:30
2026-10-28T06:10:31+05:30   [fp16 B] 2054/2054  0.94s/item  eta 0.0 min
2026-10-28T06:10:32+05:30 s1: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 06:13:59 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:13:59 +05:30
2026-10-28T06:10:31+05:30   [fp16 B] 2054/2054  0.94s/item  eta 0.0 min
2026-10-28T06:10:32+05:30 s1: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 06:14:50 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:14:50 +05:30
2026-10-28T06:10:31+05:30   [fp16 B] 2054/2054  0.94s/item  eta 0.0 min
2026-10-28T06:10:32+05:30 s1: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 06:15:40 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:15:40 +05:30
2026-10-28T06:10:31+05:30   [fp16 B] 2054/2054  0.94s/item  eta 0.0 min
2026-10-28T06:10:32+05:30 s1: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 06:16:30 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:16:30 +05:30
2026-10-28T06:16:07+05:30   [s1 A] 2437/2437  0.14s/item  eta 0.0 min
2026-10-28T06:16:29+05:30   [s1 B] 25/2437  0.68s/item  eta 27.5 min
~~~

## 2026-10-28 06:17:21 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:17:21 +05:30
2026-10-28T06:16:57+05:30   [s1 B] 75/2437  0.60s/item  eta 23.6 min
2026-10-28T06:17:12+05:30   [s1 B] 100/2437  0.60s/item  eta 23.2 min
~~~

## 2026-10-28 06:18:11 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:18:11 +05:30
2026-10-28T06:17:51+05:30   [s1 B] 175/2437  0.57s/item  eta 21.3 min
2026-10-28T06:18:04+05:30   [s1 B] 200/2437  0.56s/item  eta 20.8 min
~~~

## 2026-10-28 06:19:02 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:19:02 +05:30
2026-10-28T06:18:42+05:30   [s1 B] 275/2437  0.55s/item  eta 19.7 min
2026-10-28T06:18:58+05:30   [s1 B] 300/2437  0.55s/item  eta 19.7 min
~~~

## 2026-10-28 06:19:52 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:19:52 +05:30
2026-10-28T06:19:29+05:30   [s1 B] 350/2437  0.56s/item  eta 19.6 min
2026-10-28T06:19:45+05:30   [s1 B] 375/2437  0.57s/item  eta 19.5 min
~~~

## 2026-10-28 06:20:42 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:20:42 +05:30
2026-10-28T06:20:17+05:30   [s1 B] 425/2437  0.58s/item  eta 19.3 min
2026-10-28T06:20:35+05:30   [s1 B] 450/2437  0.58s/item  eta 19.3 min
~~~

## 2026-10-28 06:21:33 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:21:33 +05:30
2026-10-28T06:21:11+05:30   [s1 B] 500/2437  0.60s/item  eta 19.3 min
2026-10-28T06:21:30+05:30   [s1 B] 525/2437  0.60s/item  eta 19.3 min
~~~

## 2026-10-28 06:22:23 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:22:23 +05:30
2026-10-28T06:22:05+05:30   [s1 B] 575/2437  0.61s/item  eta 19.0 min
2026-10-28T06:22:22+05:30   [s1 B] 600/2437  0.62s/item  eta 18.9 min
~~~

## 2026-10-28 06:23:14 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:23:14 +05:30
2026-10-28T06:22:55+05:30   [s1 B] 650/2437  0.62s/item  eta 18.5 min
2026-10-28T06:23:13+05:30   [s1 B] 675/2437  0.62s/item  eta 18.3 min
~~~

## 2026-10-28 06:24:04 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:24:04 +05:30
2026-10-28T06:23:47+05:30   [s1 B] 725/2437  0.63s/item  eta 17.9 min
2026-10-28T06:24:03+05:30   [s1 B] 750/2437  0.63s/item  eta 17.7 min
~~~

## 2026-10-28 06:24:55 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:24:55 +05:30
2026-10-28T06:24:36+05:30   [s1 B] 800/2437  0.63s/item  eta 17.2 min
2026-10-28T06:24:52+05:30   [s1 B] 825/2437  0.63s/item  eta 16.9 min
~~~

## 2026-10-28 06:25:45 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:25:45 +05:30
2026-10-28T06:25:25+05:30   [s1 B] 875/2437  0.63s/item  eta 16.4 min
2026-10-28T06:25:40+05:30   [s1 B] 900/2437  0.63s/item  eta 16.2 min
~~~

## 2026-10-28 06:26:35 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:26:35 +05:30
2026-10-28T06:26:12+05:30   [s1 B] 950/2437  0.63s/item  eta 15.6 min
2026-10-28T06:26:28+05:30   [s1 B] 975/2437  0.63s/item  eta 15.4 min
~~~

## 2026-10-28 06:27:26 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:27:26 +05:30
2026-10-28T06:27:00+05:30   [s1 B] 1025/2437  0.63s/item  eta 14.9 min
2026-10-28T06:27:15+05:30   [s1 B] 1050/2437  0.63s/item  eta 14.6 min
~~~

## 2026-10-28 06:28:16 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:28:16 +05:30
2026-10-28T06:27:55+05:30   [s1 B] 1125/2437  0.62s/item  eta 13.7 min
2026-10-28T06:28:09+05:30   [s1 B] 1150/2437  0.62s/item  eta 13.4 min
~~~

## 2026-10-28 06:29:07 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:29:07 +05:30
2026-10-28T06:28:48+05:30   [s1 B] 1225/2437  0.62s/item  eta 12.5 min
2026-10-28T06:29:01+05:30   [s1 B] 1250/2437  0.62s/item  eta 12.2 min
~~~

## 2026-10-28 06:29:57 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:29:57 +05:30
2026-10-28T06:29:38+05:30   [s1 B] 1325/2437  0.61s/item  eta 11.3 min
2026-10-28T06:29:53+05:30   [s1 B] 1350/2437  0.61s/item  eta 11.0 min
~~~

## 2026-10-28 06:30:47 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:30:47 +05:30
2026-10-28T06:30:24+05:30   [s1 B] 1400/2437  0.61s/item  eta 10.5 min
2026-10-28T06:30:43+05:30   [s1 B] 1425/2437  0.61s/item  eta 10.3 min
~~~

## 2026-10-28 06:31:38 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:31:38 +05:30
2026-10-28T06:31:20+05:30   [s1 B] 1475/2437  0.62s/item  eta 9.9 min
2026-10-28T06:31:38+05:30   [s1 B] 1500/2437  0.62s/item  eta 9.6 min
~~~

## 2026-10-28 06:32:28 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:32:28 +05:30
2026-10-28T06:31:56+05:30   [s1 B] 1525/2437  0.62s/item  eta 9.4 min
2026-10-28T06:32:15+05:30   [s1 B] 1550/2437  0.62s/item  eta 9.2 min
~~~

## 2026-10-28 06:33:19 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:33:19 +05:30
2026-10-28T06:32:51+05:30   [s1 B] 1600/2437  0.62s/item  eta 8.7 min
2026-10-28T06:33:10+05:30   [s1 B] 1625/2437  0.63s/item  eta 8.5 min
~~~

## 2026-10-28 06:34:09 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:34:09 +05:30
2026-10-28T06:33:45+05:30   [s1 B] 1675/2437  0.63s/item  eta 8.0 min
2026-10-28T06:34:03+05:30   [s1 B] 1700/2437  0.63s/item  eta 7.7 min
~~~

## 2026-10-28 06:34:59 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:34:59 +05:30
2026-10-28T06:34:38+05:30   [s1 B] 1750/2437  0.63s/item  eta 7.2 min
2026-10-28T06:34:57+05:30   [s1 B] 1775/2437  0.63s/item  eta 7.0 min
~~~

## 2026-10-28 06:35:50 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:35:50 +05:30
2026-10-28T06:35:33+05:30   [s1 B] 1825/2437  0.64s/item  eta 6.5 min
2026-10-28T06:35:49+05:30   [s1 B] 1850/2437  0.64s/item  eta 6.2 min
~~~

## 2026-10-28 06:36:40 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:36:40 +05:30
2026-10-28T06:36:06+05:30   [s1 B] 1875/2437  0.64s/item  eta 6.0 min
2026-10-28T06:36:24+05:30   [s1 B] 1900/2437  0.64s/item  eta 5.7 min
~~~

## 2026-10-28 06:37:31 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:37:31 +05:30
2026-10-28T06:36:59+05:30   [s1 B] 1950/2437  0.64s/item  eta 5.2 min
2026-10-28T06:37:17+05:30   [s1 B] 1975/2437  0.64s/item  eta 4.9 min
~~~

## 2026-10-28 06:38:21 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:38:21 +05:30
2026-10-28T06:37:52+05:30   [s1 B] 2025/2437  0.64s/item  eta 4.4 min
2026-10-28T06:38:09+05:30   [s1 B] 2050/2437  0.64s/item  eta 4.1 min
~~~

## 2026-10-28 06:39:12 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:39:12 +05:30
2026-10-28T06:38:46+05:30   [s1 B] 2100/2437  0.64s/item  eta 3.6 min
2026-10-28T06:39:01+05:30   [s1 B] 2125/2437  0.64s/item  eta 3.4 min
~~~

## 2026-10-28 06:40:02 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:40:02 +05:30
2026-10-28T06:39:32+05:30   [s1 B] 2175/2437  0.64s/item  eta 2.8 min
2026-10-28T06:39:51+05:30   [s1 B] 2200/2437  0.64s/item  eta 2.5 min
~~~

## 2026-10-28 06:40:52 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:40:52 +05:30
2026-10-28T06:40:30+05:30   [s1 B] 2250/2437  0.65s/item  eta 2.0 min
2026-10-28T06:40:48+05:30   [s1 B] 2275/2437  0.65s/item  eta 1.8 min
~~~

## 2026-10-28 06:41:43 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:41:43 +05:30
2026-10-28T06:41:08+05:30   [s1 B] 2300/2437  0.65s/item  eta 1.5 min
2026-10-28T06:41:28+05:30   [s1 B] 2325/2437  0.65s/item  eta 1.2 min
~~~

## 2026-10-28 06:42:33 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:42:33 +05:30
2026-10-28T06:42:05+05:30   [s1 B] 2375/2437  0.65s/item  eta 0.7 min
2026-10-28T06:42:23+05:30   [s1 B] 2400/2437  0.65s/item  eta 0.4 min
~~~

## 2026-10-28 06:43:24 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:43:24 +05:30
2026-10-28T06:43:09+05:30   [s2 A] 2425/2437  0.01s/item  eta 0.0 min
2026-10-28T06:43:09+05:30   [s2 A] 2437/2437  0.01s/item  eta 0.0 min
~~~

## 2026-10-28 06:44:14 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:44:14 +05:30
2026-10-28T06:43:57+05:30   [s2 B] 75/2437  0.63s/item  eta 24.8 min
2026-10-28T06:44:12+05:30   [s2 B] 100/2437  0.62s/item  eta 24.3 min
~~~

## 2026-10-28 06:45:05 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:45:05 +05:30
2026-10-28T06:44:38+05:30   [s2 B] 150/2437  0.59s/item  eta 22.5 min
2026-10-28T06:44:53+05:30   [s2 B] 175/2437  0.59s/item  eta 22.2 min
~~~

## 2026-10-28 06:45:55 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:45:55 +05:30
2026-10-28T06:45:30+05:30   [s2 B] 250/2437  0.56s/item  eta 20.4 min
2026-10-28T06:45:44+05:30   [s2 B] 275/2437  0.56s/item  eta 20.3 min
~~~

## 2026-10-28 06:46:45 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:46:45 +05:30
2026-10-28T06:46:15+05:30   [s2 B] 325/2437  0.57s/item  eta 20.1 min
2026-10-28T06:46:31+05:30   [s2 B] 350/2437  0.57s/item  eta 20.0 min
~~~

## 2026-10-28 06:47:36 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:47:36 +05:30
2026-10-28T06:47:18+05:30   [s2 B] 425/2437  0.58s/item  eta 19.6 min
2026-10-28T06:47:35+05:30   [s2 B] 450/2437  0.59s/item  eta 19.5 min
~~~

## 2026-10-28 06:48:26 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:48:26 +05:30
2026-10-28T06:47:53+05:30   [s2 B] 475/2437  0.60s/item  eta 19.5 min
2026-10-28T06:48:11+05:30   [s2 B] 500/2437  0.60s/item  eta 19.5 min
~~~

## 2026-10-28 06:49:17 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:49:17 +05:30
2026-10-28T06:48:46+05:30   [s2 B] 550/2437  0.61s/item  eta 19.3 min
2026-10-28T06:49:04+05:30   [s2 B] 575/2437  0.62s/item  eta 19.1 min
~~~

## 2026-10-28 06:50:07 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:50:07 +05:30
2026-10-28T06:49:36+05:30   [s2 B] 625/2437  0.62s/item  eta 18.7 min
2026-10-28T06:49:52+05:30   [s2 B] 650/2437  0.62s/item  eta 18.5 min
~~~

## 2026-10-28 06:50:57 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:50:57 +05:30
2026-10-28T06:50:26+05:30   [s2 B] 700/2437  0.62s/item  eta 18.0 min
2026-10-28T06:50:42+05:30   [s2 B] 725/2437  0.62s/item  eta 17.8 min
~~~

## 2026-10-28 06:51:48 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:51:48 +05:30
2026-10-28T06:51:29+05:30   [s2 B] 800/2437  0.62s/item  eta 17.0 min
2026-10-28T06:51:44+05:30   [s2 B] 825/2437  0.62s/item  eta 16.8 min
~~~

## 2026-10-28 06:52:38 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:52:38 +05:30
2026-10-28T06:52:15+05:30   [s2 B] 875/2437  0.62s/item  eta 16.2 min
2026-10-28T06:52:30+05:30   [s2 B] 900/2437  0.62s/item  eta 16.0 min
~~~

## 2026-10-28 06:53:29 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:53:29 +05:30
2026-10-28T06:53:01+05:30   [s2 B] 950/2437  0.62s/item  eta 15.4 min
2026-10-28T06:53:16+05:30   [s2 B] 975/2437  0.62s/item  eta 15.2 min
~~~

## 2026-10-28 06:54:19 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:54:19 +05:30
2026-10-28T06:54:02+05:30   [s2 B] 1050/2437  0.62s/item  eta 14.4 min
2026-10-28T06:54:16+05:30   [s2 B] 1075/2437  0.62s/item  eta 14.1 min
~~~

## 2026-10-28 06:55:10 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:55:10 +05:30
2026-10-28T06:54:54+05:30   [s2 B] 1150/2437  0.61s/item  eta 13.1 min
2026-10-28T06:55:08+05:30   [s2 B] 1175/2437  0.61s/item  eta 12.9 min
~~~

## 2026-10-28 06:56:00 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:56:00 +05:30
2026-10-28T06:55:45+05:30   [s2 B] 1250/2437  0.60s/item  eta 12.0 min
2026-10-28T06:55:58+05:30   [s2 B] 1275/2437  0.60s/item  eta 11.7 min
~~~

## 2026-10-28 06:56:50 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:56:50 +05:30
2026-10-28T06:56:21+05:30   [s2 B] 1325/2437  0.60s/item  eta 11.1 min
2026-10-28T06:56:36+05:30   [s2 B] 1350/2437  0.60s/item  eta 10.8 min
~~~

## 2026-10-28 06:57:41 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:57:41 +05:30
2026-10-28T06:57:07+05:30   [s2 B] 1400/2437  0.60s/item  eta 10.3 min
2026-10-28T06:57:25+05:30   [s2 B] 1425/2437  0.60s/item  eta 10.1 min
~~~

## 2026-10-28 06:58:31 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:58:31 +05:30
2026-10-28T06:58:00+05:30   [s2 B] 1475/2437  0.60s/item  eta 9.7 min
2026-10-28T06:58:18+05:30   [s2 B] 1500/2437  0.61s/item  eta 9.5 min
~~~

## 2026-10-28 06:59:22 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 06:59:22 +05:30
2026-10-28T06:58:53+05:30   [s2 B] 1550/2437  0.61s/item  eta 9.0 min
2026-10-28T06:59:10+05:30   [s2 B] 1575/2437  0.61s/item  eta 8.8 min
~~~

## 2026-10-28 07:00:12 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:00:12 +05:30
2026-10-28T06:59:45+05:30   [s2 B] 1625/2437  0.61s/item  eta 8.3 min
2026-10-28T07:00:02+05:30   [s2 B] 1650/2437  0.61s/item  eta 8.0 min
~~~

## 2026-10-28 07:01:02 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:01:02 +05:30
2026-10-28T07:00:36+05:30   [s2 B] 1700/2437  0.62s/item  eta 7.6 min
2026-10-28T07:00:53+05:30   [s2 B] 1725/2437  0.62s/item  eta 7.3 min
~~~

## 2026-10-28 07:01:53 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:01:53 +05:30
2026-10-28T07:01:27+05:30   [s2 B] 1775/2437  0.62s/item  eta 6.8 min
2026-10-28T07:01:44+05:30   [s2 B] 1800/2437  0.62s/item  eta 6.6 min
~~~

## 2026-10-28 07:02:43 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:02:43 +05:30
2026-10-28T07:02:17+05:30   [s2 B] 1850/2437  0.62s/item  eta 6.1 min
2026-10-28T07:02:33+05:30   [s2 B] 1875/2437  0.62s/item  eta 5.8 min
~~~

## 2026-10-28 07:03:34 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:03:34 +05:30
2026-10-28T07:03:07+05:30   [s2 B] 1925/2437  0.62s/item  eta 5.3 min
2026-10-28T07:03:24+05:30   [s2 B] 1950/2437  0.62s/item  eta 5.1 min
~~~

## 2026-10-28 07:04:24 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:04:24 +05:30
2026-10-28T07:03:58+05:30   [s2 B] 2000/2437  0.62s/item  eta 4.5 min
2026-10-28T07:04:16+05:30   [s2 B] 2025/2437  0.63s/item  eta 4.3 min
~~~

## 2026-10-28 07:05:15 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:05:15 +05:30
2026-10-28T07:04:52+05:30   [s2 B] 2075/2437  0.63s/item  eta 3.8 min
2026-10-28T07:05:09+05:30   [s2 B] 2100/2437  0.63s/item  eta 3.5 min
~~~

## 2026-10-28 07:06:05 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:06:05 +05:30
2026-10-28T07:05:39+05:30   [s2 B] 2150/2437  0.63s/item  eta 3.0 min
2026-10-28T07:05:54+05:30   [s2 B] 2175/2437  0.63s/item  eta 2.7 min
~~~

## 2026-10-28 07:06:55 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:06:55 +05:30
2026-10-28T07:06:31+05:30   [s2 B] 2225/2437  0.63s/item  eta 2.2 min
2026-10-28T07:06:49+05:30   [s2 B] 2250/2437  0.63s/item  eta 2.0 min
~~~

## 2026-10-28 07:07:46 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:07:46 +05:30
2026-10-28T07:07:26+05:30   [s2 B] 2300/2437  0.63s/item  eta 1.4 min
2026-10-28T07:07:45+05:30   [s2 B] 2325/2437  0.63s/item  eta 1.2 min
~~~

## 2026-10-28 07:08:36 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:08:36 +05:30
2026-10-28T07:08:04+05:30   [s2 B] 2350/2437  0.64s/item  eta 0.9 min
2026-10-28T07:08:20+05:30   [s2 B] 2375/2437  0.64s/item  eta 0.7 min
~~~

## 2026-10-28 07:09:27 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:09:27 +05:30
2026-10-28T07:09:02+05:30   [s2 B] 2437/2437  0.64s/item  eta 0.0 min
2026-10-28T07:09:04+05:30 s3: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 07:10:17 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:10:17 +05:30
2026-10-28T07:09:02+05:30   [s2 B] 2437/2437  0.64s/item  eta 0.0 min
2026-10-28T07:09:04+05:30 s3: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 07:11:07 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:11:07 +05:30
2026-10-28T07:09:02+05:30   [s2 B] 2437/2437  0.64s/item  eta 0.0 min
2026-10-28T07:09:04+05:30 s3: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 07:11:58 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:11:58 +05:30
2026-10-28T07:11:24+05:30   [s3 A] 2437/2437  0.06s/item  eta 0.0 min
2026-10-28T07:11:46+05:30   [s3 B] 25/2437  0.69s/item  eta 27.7 min
~~~

## 2026-10-28 07:12:48 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:12:48 +05:30
2026-10-28T07:12:28+05:30   [s3 B] 100/2437  0.59s/item  eta 23.2 min
2026-10-28T07:12:41+05:30   [s3 B] 125/2437  0.58s/item  eta 22.3 min
~~~

## 2026-10-28 07:13:39 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:13:39 +05:30
2026-10-28T07:13:20+05:30   [s3 B] 200/2437  0.56s/item  eta 20.8 min
2026-10-28T07:13:30+05:30   [s3 B] 225/2437  0.54s/item  eta 19.9 min
~~~

## 2026-10-28 07:14:29 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:14:29 +05:30
2026-10-28T07:13:59+05:30   [s3 B] 275/2437  0.55s/item  eta 19.7 min
2026-10-28T07:14:14+05:30   [s3 B] 300/2437  0.55s/item  eta 19.7 min
~~~

## 2026-10-28 07:15:20 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:15:20 +05:30
2026-10-28T07:15:02+05:30   [s3 B] 375/2437  0.57s/item  eta 19.5 min
2026-10-28T07:15:17+05:30   [s3 B] 400/2437  0.57s/item  eta 19.4 min
~~~

## 2026-10-28 07:16:10 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:16:10 +05:30
2026-10-28T07:15:50+05:30   [s3 B] 450/2437  0.58s/item  eta 19.3 min
2026-10-28T07:16:08+05:30   [s3 B] 475/2437  0.59s/item  eta 19.3 min
~~~

## 2026-10-28 07:17:00 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:17:00 +05:30
2026-10-28T07:16:26+05:30   [s3 B] 500/2437  0.60s/item  eta 19.2 min
2026-10-28T07:16:44+05:30   [s3 B] 525/2437  0.60s/item  eta 19.2 min
~~~

## 2026-10-28 07:17:51 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:17:51 +05:30
2026-10-28T07:17:20+05:30   [s3 B] 575/2437  0.61s/item  eta 19.0 min
2026-10-28T07:17:37+05:30   [s3 B] 600/2437  0.61s/item  eta 18.8 min
~~~

## 2026-10-28 07:18:41 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:18:41 +05:30
2026-10-28T07:18:09+05:30   [s3 B] 650/2437  0.62s/item  eta 18.4 min
2026-10-28T07:18:27+05:30   [s3 B] 675/2437  0.62s/item  eta 18.2 min
~~~

## 2026-10-28 07:19:32 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:19:32 +05:30
2026-10-28T07:19:00+05:30   [s3 B] 725/2437  0.62s/item  eta 17.8 min
2026-10-28T07:19:16+05:30   [s3 B] 750/2437  0.62s/item  eta 17.5 min
~~~

## 2026-10-28 07:20:22 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:20:22 +05:30
2026-10-28T07:20:03+05:30   [s3 B] 825/2437  0.62s/item  eta 16.8 min
2026-10-28T07:20:20+05:30   [s3 B] 850/2437  0.63s/item  eta 16.5 min
~~~

## 2026-10-28 07:21:12 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:21:12 +05:30
2026-10-28T07:20:51+05:30   [s3 B] 900/2437  0.62s/item  eta 16.0 min
2026-10-28T07:21:07+05:30   [s3 B] 925/2437  0.63s/item  eta 15.8 min
~~~

## 2026-10-28 07:22:03 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:22:03 +05:30
2026-10-28T07:21:37+05:30   [s3 B] 975/2437  0.62s/item  eta 15.2 min
2026-10-28T07:21:53+05:30   [s3 B] 1000/2437  0.62s/item  eta 15.0 min
~~~

## 2026-10-28 07:22:53 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:22:53 +05:30
2026-10-28T07:22:37+05:30   [s3 B] 1075/2437  0.62s/item  eta 14.1 min
2026-10-28T07:22:49+05:30   [s3 B] 1100/2437  0.62s/item  eta 13.8 min
~~~

## 2026-10-28 07:23:44 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:23:44 +05:30
2026-10-28T07:23:30+05:30   [s3 B] 1175/2437  0.61s/item  eta 12.9 min
2026-10-28T07:23:41+05:30   [s3 B] 1200/2437  0.61s/item  eta 12.6 min
~~~

## 2026-10-28 07:24:34 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:24:34 +05:30
2026-10-28T07:24:20+05:30   [s3 B] 1275/2437  0.61s/item  eta 11.7 min
2026-10-28T07:24:33+05:30   [s3 B] 1300/2437  0.60s/item  eta 11.4 min
~~~

## 2026-10-28 07:25:25 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:25:25 +05:30
2026-10-28T07:24:58+05:30   [s3 B] 1350/2437  0.60s/item  eta 10.9 min
2026-10-28T07:25:13+05:30   [s3 B] 1375/2437  0.60s/item  eta 10.6 min
~~~

## 2026-10-28 07:26:15 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:26:15 +05:30
2026-10-28T07:25:48+05:30   [s3 B] 1425/2437  0.60s/item  eta 10.2 min
2026-10-28T07:26:05+05:30   [s3 B] 1450/2437  0.60s/item  eta 9.9 min
~~~

## 2026-10-28 07:27:05 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:27:05 +05:30
2026-10-28T07:26:41+05:30   [s3 B] 1500/2437  0.61s/item  eta 9.5 min
2026-10-28T07:26:59+05:30   [s3 B] 1525/2437  0.61s/item  eta 9.3 min
~~~

## 2026-10-28 07:27:56 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:27:56 +05:30
2026-10-28T07:27:34+05:30   [s3 B] 1575/2437  0.61s/item  eta 8.8 min
2026-10-28T07:27:51+05:30   [s3 B] 1600/2437  0.61s/item  eta 8.6 min
~~~

## 2026-10-28 07:28:46 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:28:46 +05:30
2026-10-28T07:28:27+05:30   [s3 B] 1650/2437  0.62s/item  eta 8.1 min
2026-10-28T07:28:43+05:30   [s3 B] 1675/2437  0.62s/item  eta 7.8 min
~~~

## 2026-10-28 07:29:37 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:29:37 +05:30
2026-10-28T07:29:19+05:30   [s3 B] 1725/2437  0.62s/item  eta 7.4 min
2026-10-28T07:29:35+05:30   [s3 B] 1750/2437  0.62s/item  eta 7.1 min
~~~

## 2026-10-28 07:30:27 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:30:27 +05:30
2026-10-28T07:29:53+05:30   [s3 B] 1775/2437  0.62s/item  eta 6.9 min
2026-10-28T07:30:10+05:30   [s3 B] 1800/2437  0.62s/item  eta 6.6 min
~~~

## 2026-10-28 07:31:18 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:31:17 +05:30
2026-10-28T07:30:43+05:30   [s3 B] 1850/2437  0.62s/item  eta 6.1 min
2026-10-28T07:31:00+05:30   [s3 B] 1875/2437  0.62s/item  eta 5.9 min
~~~

## 2026-10-28 07:32:08 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:32:08 +05:30
2026-10-28T07:31:35+05:30   [s3 B] 1925/2437  0.63s/item  eta 5.3 min
2026-10-28T07:31:52+05:30   [s3 B] 1950/2437  0.63s/item  eta 5.1 min
~~~

## 2026-10-28 07:32:58 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:32:58 +05:30
2026-10-28T07:32:27+05:30   [s3 B] 2000/2437  0.63s/item  eta 4.6 min
2026-10-28T07:32:45+05:30   [s3 B] 2025/2437  0.63s/item  eta 4.3 min
~~~

## 2026-10-28 07:33:49 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:33:49 +05:30
2026-10-28T07:33:22+05:30   [s3 B] 2075/2437  0.63s/item  eta 3.8 min
2026-10-28T07:33:40+05:30   [s3 B] 2100/2437  0.63s/item  eta 3.6 min
~~~

## 2026-10-28 07:34:39 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:34:39 +05:30
2026-10-28T07:34:10+05:30   [s3 B] 2150/2437  0.63s/item  eta 3.0 min
2026-10-28T07:34:25+05:30   [s3 B] 2175/2437  0.63s/item  eta 2.8 min
~~~

## 2026-10-28 07:35:30 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:35:30 +05:30
2026-10-28T07:35:02+05:30   [s3 B] 2225/2437  0.64s/item  eta 2.2 min
2026-10-28T07:35:22+05:30   [s3 B] 2250/2437  0.64s/item  eta 2.0 min
~~~

## 2026-10-28 07:36:20 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:36:20 +05:30
2026-10-28T07:35:59+05:30   [s3 B] 2300/2437  0.64s/item  eta 1.5 min
2026-10-28T07:36:19+05:30   [s3 B] 2325/2437  0.64s/item  eta 1.2 min
~~~

## 2026-10-28 07:37:10 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:37:10 +05:30
2026-10-28T07:36:38+05:30   [s3 B] 2350/2437  0.64s/item  eta 0.9 min
2026-10-28T07:36:55+05:30   [s3 B] 2375/2437  0.64s/item  eta 0.7 min
~~~

## 2026-10-28 07:38:01 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:38:01 +05:30
2026-10-28T07:37:37+05:30   [s3 B] 2437/2437  0.64s/item  eta 0.0 min
2026-10-28T07:37:39+05:30 s4: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 07:38:51 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:38:51 +05:30
2026-10-28T07:37:37+05:30   [s3 B] 2437/2437  0.64s/item  eta 0.0 min
2026-10-28T07:37:39+05:30 s4: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 07:39:42 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:39:42 +05:30
2026-10-28T07:39:37+05:30   [s4 A] 2425/2437  0.05s/item  eta 0.0 min
2026-10-28T07:39:37+05:30   [s4 A] 2437/2437  0.05s/item  eta 0.0 min
~~~

## 2026-10-28 07:40:32 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:40:32 +05:30
2026-10-28T07:40:15+05:30   [s4 B] 50/2437  0.67s/item  eta 26.5 min
2026-10-28T07:40:31+05:30   [s4 B] 75/2437  0.66s/item  eta 25.9 min
~~~

## 2026-10-28 07:41:23 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:41:23 +05:30
2026-10-28T07:41:01+05:30   [s4 B] 125/2437  0.64s/item  eta 24.6 min
2026-10-28T07:41:15+05:30   [s4 B] 150/2437  0.62s/item  eta 23.7 min
~~~

## 2026-10-28 07:42:13 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:42:13 +05:30
2026-10-28T07:41:54+05:30   [s4 B] 225/2437  0.59s/item  eta 21.8 min
2026-10-28T07:42:10+05:30   [s4 B] 250/2437  0.59s/item  eta 21.7 min
~~~

## 2026-10-28 07:43:03 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:43:03 +05:30
2026-10-28T07:42:42+05:30   [s4 B] 300/2437  0.60s/item  eta 21.4 min
2026-10-28T07:42:58+05:30   [s4 B] 325/2437  0.61s/item  eta 21.3 min
~~~

## 2026-10-28 07:43:54 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:43:54 +05:30
2026-10-28T07:43:33+05:30   [s4 B] 375/2437  0.62s/item  eta 21.2 min
2026-10-28T07:43:50+05:30   [s4 B] 400/2437  0.62s/item  eta 21.1 min
~~~

## 2026-10-28 07:44:44 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:44:44 +05:30
2026-10-28T07:44:07+05:30   [s4 B] 425/2437  0.63s/item  eta 21.0 min
2026-10-28T07:44:26+05:30   [s4 B] 450/2437  0.63s/item  eta 20.9 min
~~~

## 2026-10-28 07:45:35 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:45:35 +05:30
2026-10-28T07:45:04+05:30   [s4 B] 500/2437  0.64s/item  eta 20.8 min
2026-10-28T07:45:23+05:30   [s4 B] 525/2437  0.65s/item  eta 20.7 min
~~~

## 2026-10-28 07:46:25 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:46:25 +05:30
2026-10-28T07:46:00+05:30   [s4 B] 575/2437  0.66s/item  eta 20.4 min
2026-10-28T07:46:18+05:30   [s4 B] 600/2437  0.66s/item  eta 20.2 min
~~~

## 2026-10-28 07:47:15 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:47:15 +05:30
2026-10-28T07:46:52+05:30   [s4 B] 650/2437  0.66s/item  eta 19.7 min
2026-10-28T07:47:11+05:30   [s4 B] 675/2437  0.67s/item  eta 19.5 min
~~~

## 2026-10-28 07:48:06 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:48:06 +05:30
2026-10-28T07:47:46+05:30   [s4 B] 725/2437  0.67s/item  eta 19.1 min
2026-10-28T07:48:03+05:30   [s4 B] 750/2437  0.67s/item  eta 18.8 min
~~~

## 2026-10-28 07:48:56 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:48:56 +05:30
2026-10-28T07:48:36+05:30   [s4 B] 800/2437  0.67s/item  eta 18.2 min
2026-10-28T07:48:53+05:30   [s4 B] 825/2437  0.67s/item  eta 18.0 min
~~~

## 2026-10-28 07:49:47 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:49:47 +05:30
2026-10-28T07:49:27+05:30   [s4 B] 875/2437  0.67s/item  eta 17.4 min
2026-10-28T07:49:43+05:30   [s4 B] 900/2437  0.67s/item  eta 17.1 min
~~~

## 2026-10-28 07:50:37 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:50:37 +05:30
2026-10-28T07:50:17+05:30   [s4 B] 950/2437  0.67s/item  eta 16.6 min
2026-10-28T07:50:33+05:30   [s4 B] 975/2437  0.67s/item  eta 16.3 min
~~~

## 2026-10-28 07:51:28 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:51:28 +05:30
2026-10-28T07:51:06+05:30   [s4 B] 1025/2437  0.67s/item  eta 15.7 min
2026-10-28T07:51:22+05:30   [s4 B] 1050/2437  0.67s/item  eta 15.4 min
~~~

## 2026-10-28 07:52:18 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:52:18 +05:30
2026-10-28T07:52:03+05:30   [s4 B] 1125/2437  0.66s/item  eta 14.4 min
2026-10-28T07:52:18+05:30   [s4 B] 1150/2437  0.66s/item  eta 14.1 min
~~~

## 2026-10-28 07:53:08 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:53:08 +05:30
2026-10-28T07:52:45+05:30   [s4 B] 1200/2437  0.65s/item  eta 13.5 min
2026-10-28T07:53:00+05:30   [s4 B] 1225/2437  0.65s/item  eta 13.2 min
~~~

## 2026-10-28 07:53:59 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:53:59 +05:30
2026-10-28T07:53:42+05:30   [s4 B] 1300/2437  0.65s/item  eta 12.3 min
2026-10-28T07:53:55+05:30   [s4 B] 1325/2437  0.64s/item  eta 11.9 min
~~~

## 2026-10-28 07:54:49 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:54:49 +05:30
2026-10-28T07:54:27+05:30   [s4 B] 1375/2437  0.64s/item  eta 11.4 min
2026-10-28T07:54:45+05:30   [s4 B] 1400/2437  0.65s/item  eta 11.2 min
~~~

## 2026-10-28 07:55:40 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:55:40 +05:30
2026-10-28T07:55:04+05:30   [s4 B] 1425/2437  0.65s/item  eta 10.9 min
2026-10-28T07:55:22+05:30   [s4 B] 1450/2437  0.65s/item  eta 10.7 min
~~~

## 2026-10-28 07:56:30 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:56:30 +05:30
2026-10-28T07:56:00+05:30   [s4 B] 1500/2437  0.65s/item  eta 10.2 min
2026-10-28T07:56:19+05:30   [s4 B] 1525/2437  0.65s/item  eta 9.9 min
~~~

## 2026-10-28 07:57:21 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:57:21 +05:30
2026-10-28T07:56:57+05:30   [s4 B] 1575/2437  0.66s/item  eta 9.4 min
2026-10-28T07:57:15+05:30   [s4 B] 1600/2437  0.66s/item  eta 9.2 min
~~~

## 2026-10-28 07:58:11 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:58:11 +05:30
2026-10-28T07:57:52+05:30   [s4 B] 1650/2437  0.66s/item  eta 8.7 min
2026-10-28T07:58:10+05:30   [s4 B] 1675/2437  0.66s/item  eta 8.4 min
~~~

## 2026-10-28 07:59:01 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:59:01 +05:30
2026-10-28T07:58:28+05:30   [s4 B] 1700/2437  0.66s/item  eta 8.1 min
2026-10-28T07:58:47+05:30   [s4 B] 1725/2437  0.66s/item  eta 7.9 min
~~~

## 2026-10-28 07:59:52 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 07:59:52 +05:30
2026-10-28T07:59:23+05:30   [s4 B] 1775/2437  0.67s/item  eta 7.3 min
2026-10-28T07:59:42+05:30   [s4 B] 1800/2437  0.67s/item  eta 7.1 min
~~~

## 2026-10-28 08:00:42 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:00:42 +05:30
2026-10-28T08:00:17+05:30   [s4 B] 1850/2437  0.67s/item  eta 6.5 min
2026-10-28T08:00:34+05:30   [s4 B] 1875/2437  0.67s/item  eta 6.3 min
~~~

## 2026-10-28 08:01:33 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:01:33 +05:30
2026-10-28T08:01:11+05:30   [s4 B] 1925/2437  0.67s/item  eta 5.7 min
2026-10-28T08:01:30+05:30   [s4 B] 1950/2437  0.67s/item  eta 5.4 min
~~~

## 2026-10-28 08:02:23 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:02:23 +05:30
2026-10-28T08:01:48+05:30   [s4 B] 1975/2437  0.67s/item  eta 5.2 min
2026-10-28T08:02:06+05:30   [s4 B] 2000/2437  0.67s/item  eta 4.9 min
~~~

## 2026-10-28 08:03:13 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:03:13 +05:30
2026-10-28T08:02:44+05:30   [s4 B] 2050/2437  0.67s/item  eta 4.3 min
2026-10-28T08:03:04+05:30   [s4 B] 2075/2437  0.68s/item  eta 4.1 min
~~~

## 2026-10-28 08:04:04 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:04:04 +05:30
2026-10-28T08:03:38+05:30   [s4 B] 2125/2437  0.68s/item  eta 3.5 min
2026-10-28T08:03:54+05:30   [s4 B] 2150/2437  0.68s/item  eta 3.2 min
~~~

## 2026-10-28 08:04:54 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:04:54 +05:30
2026-10-28T08:04:30+05:30   [s4 B] 2200/2437  0.68s/item  eta 2.7 min
2026-10-28T08:04:50+05:30   [s4 B] 2225/2437  0.68s/item  eta 2.4 min
~~~

## 2026-10-28 08:05:45 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:05:45 +05:30
2026-10-28T08:05:10+05:30   [s4 B] 2250/2437  0.68s/item  eta 2.1 min
2026-10-28T08:05:29+05:30   [s4 B] 2275/2437  0.68s/item  eta 1.8 min
~~~

## 2026-10-28 08:06:35 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:06:35 +05:30
2026-10-28T08:06:10+05:30   [s4 B] 2325/2437  0.68s/item  eta 1.3 min
2026-10-28T08:06:30+05:30   [s4 B] 2350/2437  0.68s/item  eta 1.0 min
~~~

## 2026-10-28 08:07:26 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:07:26 +05:30
2026-10-28T08:07:06+05:30   [s4 B] 2400/2437  0.69s/item  eta 0.4 min
2026-10-28T08:07:24+05:30   [s4 B] 2425/2437  0.69s/item  eta 0.1 min
~~~

## 2026-10-28 08:08:16 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:08:16 +05:30
2026-10-28T08:07:33+05:30   [s4 B] 2437/2437  0.69s/item  eta 0.0 min
2026-10-28T08:07:34+05:30 s4aa: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:09:06 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:09:06 +05:30
2026-10-28T08:07:33+05:30   [s4 B] 2437/2437  0.69s/item  eta 0.0 min
2026-10-28T08:07:34+05:30 s4aa: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:09:57 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:09:57 +05:30
2026-10-28T08:09:57+05:30   [s4aa A] 975/2437  0.15s/item  eta 3.6 min
2026-10-28T08:09:57+05:30   [s4aa A] 1000/2437  0.14s/item  eta 3.4 min
~~~

## 2026-10-28 08:10:47 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:10:47 +05:30
2026-10-28T08:10:30+05:30   [s4aa B] 25/2437  0.75s/item  eta 30.2 min
2026-10-28T08:10:45+05:30   [s4aa B] 50/2437  0.68s/item  eta 26.9 min
~~~

## 2026-10-28 08:11:38 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:11:38 +05:30
2026-10-28T08:11:17+05:30   [s4aa B] 100/2437  0.67s/item  eta 25.9 min
2026-10-28T08:11:32+05:30   [s4aa B] 125/2437  0.65s/item  eta 25.1 min
~~~

## 2026-10-28 08:12:28 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:12:28 +05:30
2026-10-28T08:12:17+05:30   [s4aa B] 200/2437  0.63s/item  eta 23.4 min
2026-10-28T08:12:28+05:30   [s4aa B] 225/2437  0.61s/item  eta 22.5 min
~~~

## 2026-10-28 08:13:19 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:13:19 +05:30
2026-10-28T08:13:00+05:30   [s4aa B] 275/2437  0.62s/item  eta 22.2 min
2026-10-28T08:13:18+05:30   [s4aa B] 300/2437  0.62s/item  eta 22.2 min
~~~

## 2026-10-28 08:14:09 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:14:09 +05:30
2026-10-28T08:13:36+05:30   [s4aa B] 325/2437  0.63s/item  eta 22.2 min
2026-10-28T08:13:54+05:30   [s4aa B] 350/2437  0.64s/item  eta 22.1 min
~~~

## 2026-10-28 08:14:59 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:14:59 +05:30
2026-10-28T08:14:30+05:30   [s4aa B] 400/2437  0.65s/item  eta 21.9 min
2026-10-28T08:14:47+05:30   [s4aa B] 425/2437  0.65s/item  eta 21.8 min
~~~

## 2026-10-28 08:15:50 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:15:50 +05:30
2026-10-28T08:15:27+05:30   [s4aa B] 475/2437  0.67s/item  eta 21.8 min
2026-10-28T08:15:48+05:30   [s4aa B] 500/2437  0.67s/item  eta 21.7 min
~~~

## 2026-10-28 08:16:40 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:16:40 +05:30
2026-10-28T08:16:08+05:30   [s4aa B] 525/2437  0.68s/item  eta 21.6 min
2026-10-28T08:16:27+05:30   [s4aa B] 550/2437  0.68s/item  eta 21.5 min
~~~

## 2026-10-28 08:17:31 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:17:31 +05:30
2026-10-28T08:17:06+05:30   [s4aa B] 600/2437  0.69s/item  eta 21.2 min
2026-10-28T08:17:24+05:30   [s4aa B] 625/2437  0.69s/item  eta 20.9 min
~~~

## 2026-10-28 08:18:21 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:18:21 +05:30
2026-10-28T08:18:02+05:30   [s4aa B] 675/2437  0.70s/item  eta 20.5 min
2026-10-28T08:18:21+05:30   [s4aa B] 700/2437  0.70s/item  eta 20.2 min
~~~

## 2026-10-28 08:19:12 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:19:12 +05:30
2026-10-28T08:18:39+05:30   [s4aa B] 725/2437  0.70s/item  eta 20.0 min
2026-10-28T08:18:57+05:30   [s4aa B] 750/2437  0.70s/item  eta 19.7 min
~~~

## 2026-10-28 08:20:02 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:20:02 +05:30
2026-10-28T08:19:33+05:30   [s4aa B] 800/2437  0.70s/item  eta 19.2 min
2026-10-28T08:19:50+05:30   [s4aa B] 825/2437  0.70s/item  eta 18.9 min
~~~

## 2026-10-28 08:20:52 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:20:52 +05:30
2026-10-28T08:20:26+05:30   [s4aa B] 875/2437  0.70s/item  eta 18.3 min
2026-10-28T08:20:43+05:30   [s4aa B] 900/2437  0.70s/item  eta 18.0 min
~~~

## 2026-10-28 08:21:43 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:21:43 +05:30
2026-10-28T08:21:19+05:30   [s4aa B] 950/2437  0.70s/item  eta 17.4 min
2026-10-28T08:21:35+05:30   [s4aa B] 975/2437  0.70s/item  eta 17.1 min
~~~

## 2026-10-28 08:22:33 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:22:33 +05:30
2026-10-28T08:22:11+05:30   [s4aa B] 1025/2437  0.70s/item  eta 16.5 min
2026-10-28T08:22:28+05:30   [s4aa B] 1050/2437  0.70s/item  eta 16.2 min
~~~

## 2026-10-28 08:23:24 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:23:24 +05:30
2026-10-28T08:22:58+05:30   [s4aa B] 1100/2437  0.70s/item  eta 15.5 min
2026-10-28T08:23:12+05:30   [s4aa B] 1125/2437  0.69s/item  eta 15.2 min
~~~

## 2026-10-28 08:24:14 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:24:14 +05:30
2026-10-28T08:23:57+05:30   [s4aa B] 1200/2437  0.69s/item  eta 14.2 min
2026-10-28T08:24:12+05:30   [s4aa B] 1225/2437  0.69s/item  eta 13.9 min
~~~

## 2026-10-28 08:25:04 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:25:04 +05:30
2026-10-28T08:24:43+05:30   [s4aa B] 1275/2437  0.68s/item  eta 13.2 min
2026-10-28T08:24:58+05:30   [s4aa B] 1300/2437  0.68s/item  eta 12.9 min
~~~

## 2026-10-28 08:25:55 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:25:55 +05:30
2026-10-28T08:25:27+05:30   [s4aa B] 1350/2437  0.68s/item  eta 12.3 min
2026-10-28T08:25:45+05:30   [s4aa B] 1375/2437  0.68s/item  eta 12.0 min
~~~

## 2026-10-28 08:26:45 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:26:45 +05:30
2026-10-28T08:26:23+05:30   [s4aa B] 1425/2437  0.68s/item  eta 11.5 min
2026-10-28T08:26:43+05:30   [s4aa B] 1450/2437  0.68s/item  eta 11.3 min
~~~

## 2026-10-28 08:27:36 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:27:36 +05:30
2026-10-28T08:27:03+05:30   [s4aa B] 1475/2437  0.69s/item  eta 11.0 min
2026-10-28T08:27:24+05:30   [s4aa B] 1500/2437  0.69s/item  eta 10.8 min
~~~

## 2026-10-28 08:28:26 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:28:26 +05:30
2026-10-28T08:28:04+05:30   [s4aa B] 1550/2437  0.69s/item  eta 10.2 min
2026-10-28T08:28:24+05:30   [s4aa B] 1575/2437  0.69s/item  eta 10.0 min
~~~

## 2026-10-28 08:29:17 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:29:17 +05:30
2026-10-28T08:28:44+05:30   [s4aa B] 1600/2437  0.70s/item  eta 9.7 min
2026-10-28T08:29:04+05:30   [s4aa B] 1625/2437  0.70s/item  eta 9.4 min
~~~

## 2026-10-28 08:30:07 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:30:07 +05:30
2026-10-28T08:29:43+05:30   [s4aa B] 1675/2437  0.70s/item  eta 8.9 min
2026-10-28T08:30:03+05:30   [s4aa B] 1700/2437  0.70s/item  eta 8.6 min
~~~

## 2026-10-28 08:30:57 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:30:57 +05:30
2026-10-28T08:30:23+05:30   [s4aa B] 1725/2437  0.70s/item  eta 8.3 min
2026-10-28T08:30:42+05:30   [s4aa B] 1750/2437  0.70s/item  eta 8.1 min
~~~

## 2026-10-28 08:31:48 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:31:48 +05:30
2026-10-28T08:31:22+05:30   [s4aa B] 1800/2437  0.71s/item  eta 7.5 min
2026-10-28T08:31:43+05:30   [s4aa B] 1825/2437  0.71s/item  eta 7.2 min
~~~

## 2026-10-28 08:32:38 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:32:38 +05:30
2026-10-28T08:32:01+05:30   [s4aa B] 1850/2437  0.71s/item  eta 6.9 min
2026-10-28T08:32:19+05:30   [s4aa B] 1875/2437  0.71s/item  eta 6.6 min
~~~

## 2026-10-28 08:33:29 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:33:29 +05:30
2026-10-28T08:32:58+05:30   [s4aa B] 1925/2437  0.71s/item  eta 6.1 min
2026-10-28T08:33:18+05:30   [s4aa B] 1950/2437  0.71s/item  eta 5.8 min
~~~

## 2026-10-28 08:34:19 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:34:19 +05:30
2026-10-28T08:33:57+05:30   [s4aa B] 2000/2437  0.71s/item  eta 5.2 min
2026-10-28T08:34:17+05:30   [s4aa B] 2025/2437  0.71s/item  eta 4.9 min
~~~

## 2026-10-28 08:35:10 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:35:10 +05:30
2026-10-28T08:34:37+05:30   [s4aa B] 2050/2437  0.72s/item  eta 4.6 min
2026-10-28T08:34:58+05:30   [s4aa B] 2075/2437  0.72s/item  eta 4.3 min
~~~

## 2026-10-28 08:36:00 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:36:00 +05:30
2026-10-28T08:35:35+05:30   [s4aa B] 2125/2437  0.72s/item  eta 3.7 min
2026-10-28T08:35:53+05:30   [s4aa B] 2150/2437  0.72s/item  eta 3.4 min
~~~

## 2026-10-28 08:36:50 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:36:50 +05:30
2026-10-28T08:36:11+05:30   [s4aa B] 2175/2437  0.72s/item  eta 3.1 min
2026-10-28T08:36:32+05:30   [s4aa B] 2200/2437  0.72s/item  eta 2.8 min
~~~

## 2026-10-28 08:37:41 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:37:41 +05:30
2026-10-28T08:37:14+05:30   [s4aa B] 2250/2437  0.72s/item  eta 2.2 min
2026-10-28T08:37:35+05:30   [s4aa B] 2275/2437  0.72s/item  eta 2.0 min
~~~

## 2026-10-28 08:38:31 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:38:31 +05:30
2026-10-28T08:37:56+05:30   [s4aa B] 2300/2437  0.72s/item  eta 1.7 min
2026-10-28T08:38:17+05:30   [s4aa B] 2325/2437  0.73s/item  eta 1.4 min
~~~

## 2026-10-28 08:39:22 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:39:22 +05:30
2026-10-28T08:38:58+05:30   [s4aa B] 2375/2437  0.73s/item  eta 0.8 min
2026-10-28T08:39:18+05:30   [s4aa B] 2400/2437  0.73s/item  eta 0.4 min
~~~

## 2026-10-28 08:40:12 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:40:12 +05:30
2026-10-28T08:39:47+05:30   [s4aa B] 2437/2437  0.73s/item  eta 0.0 min
2026-10-28T08:39:48+05:30 swap_pol8: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:41:03 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:41:03 +05:30
2026-10-28T08:39:47+05:30   [s4aa B] 2437/2437  0.73s/item  eta 0.0 min
2026-10-28T08:39:48+05:30 swap_pol8: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:41:53 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:41:53 +05:30
2026-10-28T08:39:47+05:30   [s4aa B] 2437/2437  0.73s/item  eta 0.0 min
2026-10-28T08:39:48+05:30 swap_pol8: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:42:43 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:42:43 +05:30
2026-10-28T08:39:47+05:30   [s4aa B] 2437/2437  0.73s/item  eta 0.0 min
2026-10-28T08:39:48+05:30 swap_pol8: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:43:34 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:43:34 +05:30
2026-10-28T08:39:47+05:30   [s4aa B] 2437/2437  0.73s/item  eta 0.0 min
2026-10-28T08:39:48+05:30 swap_pol8: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:44:24 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:44:24 +05:30
2026-10-28T08:39:47+05:30   [s4aa B] 2437/2437  0.73s/item  eta 0.0 min
2026-10-28T08:39:48+05:30 swap_pol8: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:45:15 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:45:15 +05:30
2026-10-28T08:39:47+05:30   [s4aa B] 2437/2437  0.73s/item  eta 0.0 min
2026-10-28T08:39:48+05:30 swap_pol8: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:46:05 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:46:05 +05:30
2026-10-28T08:39:47+05:30   [s4aa B] 2437/2437  0.73s/item  eta 0.0 min
2026-10-28T08:39:48+05:30 swap_pol8: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:46:55 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:46:55 +05:30
2026-10-28T08:39:47+05:30   [s4aa B] 2437/2437  0.73s/item  eta 0.0 min
2026-10-28T08:39:48+05:30 swap_pol8: 2437 positions, budgets [0, 100, 400, 800, 1600], movetimes []
~~~

## 2026-10-28 08:47:46 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:47:46 +05:30
2026-10-28T08:47:45+05:30   [swap_pol8 A] 900/2437  0.53s/item  eta 13.6 min
2026-10-28T08:47:46+05:30   [swap_pol8 A] 925/2437  0.52s/item  eta 13.0 min
~~~

## 2026-10-28 08:48:36 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:48:36 +05:30
2026-10-28T08:48:03+05:30   [swap_pol8 A] 2425/2437  0.20s/item  eta 0.0 min
2026-10-28T08:48:03+05:30   [swap_pol8 A] 2437/2437  0.20s/item  eta 0.0 min
~~~

## 2026-10-28 08:49:27 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines. Exit code: 0. Observation only; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:49:27 +05:30
2026-10-28T08:48:51+05:30   [swap_pol8 B] 25/2437  1.59s/item  eta 63.9 min
2026-10-28T08:49:23+05:30   [swap_pol8 B] 50/2437  1.45s/item  eta 57.5 min
~~~

## 2026-10-28 08:50:19 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines, omitting ETA from display only. Exit code: 0. Observation only; full pipeline logs unchanged; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:50:19 +05:30
2026-10-28T08:49:23+05:30   [swap_pol8 B] 50/2437  1.45s/item
2026-10-28T08:50:01+05:30   [swap_pol8 B] 75/2437  1.46s/item
~~~

## 2026-10-28 08:51:09 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines, omitting ETA from display only. Exit code: 0. Observation only; full pipeline logs unchanged; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:51:09 +05:30
2026-10-28T08:50:01+05:30   [swap_pol8 B] 75/2437  1.46s/item
2026-10-28T08:50:38+05:30   [swap_pol8 B] 100/2437  1.47s/item
~~~

## 2026-10-28 08:51:59 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines, omitting ETA from display only. Exit code: 0. Observation only; full pipeline logs unchanged; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:51:59 +05:30
2026-10-28T08:51:10+05:30   [swap_pol8 B] 125/2437  1.43s/item
2026-10-28T08:51:41+05:30   [swap_pol8 B] 150/2437  1.40s/item
~~~

## 2026-10-28 08:52:50 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines, omitting ETA from display only. Exit code: 0. Observation only; full pipeline logs unchanged; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:52:50 +05:30
2026-10-28T08:52:15+05:30   [swap_pol8 B] 175/2437  1.39s/item
2026-10-28T08:52:45+05:30   [swap_pol8 B] 200/2437  1.37s/item
~~~

## 2026-10-28 08:53:40 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines, omitting ETA from display only. Exit code: 0. Observation only; full pipeline logs unchanged; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:53:40 +05:30
2026-10-28T08:52:45+05:30   [swap_pol8 B] 200/2437  1.37s/item
2026-10-28T08:53:08+05:30   [swap_pol8 B] 225/2437  1.32s/item
~~~

## 2026-10-28 08:54:31 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines, omitting ETA from display only. Exit code: 0. Observation only; full pipeline logs unchanged; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:54:31 +05:30
2026-10-28T08:53:42+05:30   [swap_pol8 B] 250/2437  1.33s/item
2026-10-28T08:54:17+05:30   [swap_pol8 B] 275/2437  1.33s/item
~~~

## 2026-10-28 08:55:21 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines, omitting ETA from display only. Exit code: 0. Observation only; full pipeline logs unchanged; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:55:21 +05:30
2026-10-28T08:54:17+05:30   [swap_pol8 B] 275/2437  1.33s/item
2026-10-28T08:54:54+05:30   [swap_pol8 B] 300/2437  1.34s/item
~~~

## 2026-10-28 08:56:12 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines, omitting ETA from display only. Exit code: 0. Observation only; full pipeline logs unchanged; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 08:56:12 +05:30
2026-10-28T08:55:31+05:30   [swap_pol8 B] 325/2437  1.35s/item
2026-10-28T08:56:09+05:30   [swap_pol8 B] 350/2437  1.36s/item
~~~

## 2026-10-28 10:46:28 +05:30 — noncritical C2 resume observation
Exact command: read C2-controller-state.json and C2-resume.stdout.log with -Encoding utf8; print final two meaningful lines, omitting ETA from display only. Exit code: 0. Observation only; full pipeline logs unchanged; no LOG.md read.
~~~
C2_STATE {"state":"running","phase":"study authorized resume 1 of 1","pid":9316,"updated":"2026-10-28T05:38:15+05:30"} Observed 2026-10-28 10:46:28 +05:30
2026-10-28T10:45:13+05:30   [swap_val8 B] 2075/2437  1.48s/item
2026-10-28T10:45:53+05:30   [swap_val8 B] 2100/2437  1.48s/item
~~~

## 2026-10-28 10:47:01 +05:30 — CPU-only prep: active GPU job inventory
First command: nvidia-smi
Exit code: 0
Output:
~~~
Wed Oct 28 10:47:00 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   87C    P0             76W /  120W |    1505MiB /   8188MiB |    100%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A           21956      C   ...sktop\LC0-B\tools\lc0\lc0.exe      N/A      |
+-----------------------------------------------------------------------------------------+
~~~
Read-only process command: Get-CimInstance Win32_Process | Where-Object Name -eq lc0.exe | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine
Exit code: 0
~~~

ProcessId       : 21956
ParentProcessId : 27616
ExecutablePath  : C:\Users\HP\Desktop\LC0-B\tools\lc0\lc0.exe
CommandLine     : C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --weights=C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.pb.gz --backend=onnx-trt --backend-opts=optimize=8


~~~
Running lc0 job is identified by its weights argument above. No GPU job started, stopped, resumed, restarted, or benchmarked. Only the chat's read-only progress observer was ended; the background study and its controller remain untouched. All prep writes use UTF-8; existing LOG history is append-only.

## 2026-10-28 10:54:03 +05:30 — CPU prep source/config/log inspection
Exact command: Get-Content STATUS.md -Encoding utf8; Get-Content config.json -Encoding utf8; rg -n "ids|classes|limit|def positions|def step_hw|for n in|bench_movetime|--name|--weights" eval/run_study.py ladder.py hw/bench.py; Get-Content eval/run_study.py -Encoding utf8 | Select-Object -First 145; Get-Content ladder.py -Encoding utf8 | Select-Object -Skip 415 -First 25; Get-Content reports/logs/study.log -Tail 22 -Encoding utf8; Get-Content reports/hard/ids.txt -Encoding utf8
Exit code: 0
Key output/read evidence:
~~~
# STATUS

Machine: RTX 4060 Laptop (HP), Windows 11. Updated 2026-10-28. Commands and evidence: LOG.md.

| Gate / step | State | Result |
|---|---|---|
| 0 Inventory | done | RTX 4060 Laptop 8188 MiB, driver 592.82 (CUDA 13.1); Python 3.11.9; Windows lc0 v0.33.0-rc0 onnx-trt (new download, `..\tools\lc0`); trtexec TRT 10.12.0.36; nsys 2025.1.3; BT3 sha256 matches Anjan's; Syzygy 3-4-5 290 files |
| 1a config.json | done | from config.example.json; lc0, trtexec, nsys, syzygy paths changed (diff in LOG.md) |
| 1b pip install -r requirements.txt | done | into `..\.venv` (Python 3.11.9); onnxruntime 1.31.1 (CPU), onnx 1.23.2, numpy 2.4.6 |
| 1c onnx-trt smoke test | done | `lc0 benchmark` on bundled 791556.pb.gz, optimize=6: 10534 nodes, 13698 nps, no FP32 warning |
| 1d describenet BT3 | done | INPUT_CLASSICAL_112_PLANE (traps 5/10 do not apply); 15 enc, 24 heads, 768, DFF 1024; exit 0 |
| 1e tbset | done | 11200 positions: calib 1120 / dev 3360 / test 6720; won 6803, drawn 4397 |
| 1f calib | done | calib.npz 512 positions, dev.npz 3360 positions, both input format 1 |
| 1g day1 | done | day1.log: wrapped/native KL 0.00e+00, top-1 1.000; INT8 runs; GEMM-like INT8 73.5% |
| CHECKPOINT C1-day1 | done | passed — explicitly approved by user on 2026-10-28; verbatim summary in LOG.md |
| Bookkeeping typo retry | done | Initial command BLOCKED at parsing: Missing closing parenthesis; one obvious-typo retry succeeded, no pipeline commands had run |
| Pre-flight C1 step 2 | done | Prior inventory/install/tbset/calib/day1 verified; paths exist, pip check passed, GPU idle, BatteryStatus 2; optional clock lock omitted, measured clocks recorded in reports/bench/*.json |
| Other-kernel review | done | reports/trt/s2_other_top15_review.md; labels inferred from names; pipeline code unchanged |
| 2a build --only s4 | done | Exit 0; reports/outliers.txt, models/s4.onnx, models/s4.pb.gz, reports/quick_compare_dev.txt |
| 2b hw --parts bench | done | Exit 0; search nps fp16 4349, native 4358, s4 5685; reports/bench/*.json; warnings empty |
| 2c study --models fp16 --limit 50 | done | Exit 0; results/fp16/study_b.jsonl; see reports/logs/C1-study-fp16-50.log for progress timing |
| CHECKPOINT C1-done | done | passed — user authorized step 3 on 2026-10-28; reports/C1-done.md |
| 3b select --alpha | done | Exit 0; reports/select_s4_dev.txt; CPU-only alpha grid and comparison |
| 3c freeze recipe | done | s3 s3_p99999.onnx: lowest finite dev KL 2.20e-02, top-1 0.844; s3 ties use higher top-1. Alpha 0.7: lowest eligible dev KL 4.13e-03, top-1 0.891 >= s3 0.844. best=s4. KL ties favor unsmoothed s3; equal alpha rows use smaller alpha deterministically. |
| CHECKPOINT C2-select | done | CHECKPOINT C2-select: ready for review; user override: continuing through build, study and score |
| 4 build | done | All nine ONNX/pb.gz/JSON sets exist; recipes verified against ladder/config; reports/C2-build-manifest.json; continuing to study |
| CHECKPOINT C2-done | todo | Not reached; study incomplete and score not run; reporting failure is BLOCKED above |
| 4 study | running | Authorized resume 1 of 1; canonical reports/logs/study.log appended by ladder.py; console C2-resume-study-console.log |
| 4 score | todo | Not run; stopped at first-failure rule before score |
| 5 C3 | todo | Not authorized in this C2 continuation |
| Prior-session review note 1 | done | `..\.venv`, `..\tools`, `..\syzygy` were created by the agent in this session (23:22-23:38), not earlier by someone else as AGENTS.md says. |
| Prior-session review note 2 | done | lc0, the CUDA/cuDNN/TRT DLLs, trtexec and nsys were downloaded: no Windows GPU lc0, trtexec or nsys existed on the machine, and Anjan's WSL lc0 is CPU-only (eigen). |
| Prior-session review note 3 | done | Syzygy was copied from Anjan's WSL env into `..\syzygy` rather than used by path. |
| Prior-session review note 4 | done | Exit codes for tbset, the smoke test and calib were not captured separately (output was piped to `tail`); see LOG.md. |
| C2 sidecar inspection | done | Filename typo models/s4.onnx.json corrected once to models/s4.json; retry exit 0; no pipeline failure |
| C2 LN consumers/channels | done | reports/C2-ln2-consumers-and-channels.md; graph hashes unchanged; CPU calibration diagnostics |
| C2 study.limit | done | 9 models, 11 weighted; floor(25200/(11*0.94))=2437; exact config diff in LOG.md |
| 3a select | done | Exit 0; reports/select_s3_dev.txt; CPU-only candidates and comparison |
| C2 continuation | running | Existing built artifacts reused; study resume -> score -> C2-done; no checkpoint pauses |
| C2 evidence read-back | done | Prior report decoding error resolved by byte/replacement reads outside critical path; LOG history preserved |
| C2 study backup/tails | done | All study JSONL backed up and tail checked; manifest reports\study-backup\2026-10-28T053703_0530/manifest.json |


| C2 resume command | running | C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py study; cwd C:\Users\HP\Desktop\LC0-B\leela-int8; PYTHONUTF8=1; no second automatic resume |




| C2 one-minute resume check | done | resuming: prior bytes and completed keys retained; no new duplicate keys; reports/C2-resume-one-minute.json |

{
 "lc0": "C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe",
 "trtexec": "C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe",
 "nsys": "C:/Users/HP/Desktop/LC0-B/tools/nsys/nsight_systems-windows-x86_64-2025.1.3.140-archive/nsight-systems/2025.1.3/target-windows-x64/nsys.exe",
 "bt3": "nets/BT3.pb.gz",
 "syzygy": "C:/Users/HP/Desktop/LC0-B/syzygy",
 "work": ".",
 "backend": "onnx-trt",
 "fp16_opts": "optimize=6",
 "int8_opts": "optimize=8",
 "native_backend": "onnx-trt",
 "native_opts": "optimize=6",
 "tbset": {
  "per_class": 400
 },
 "calib": {
  "random_games": 256,
  "n_tb": 256
 },
 "recipe": {
  "s3_method": "percentile",
  "s3_percentile": 99.999,
  "s4_alpha": 0.7
 },
 "best": "s4",
 "study": {
  "split": "test",
  "limit": 2437,
  "budgets": "0,100,400,800,1600",
  "threads": 1,
  "minibatch": 256,
  "models": "fp16,s1,s2,s3,s4,s4aa"
 },
 "extras": {
  "s0_in_study_b": false,
  "swap": true,
  "s1sp": true
 },
 "studyc": {
  "movetimes": "200,800",
  "models": "fp16,BEST",
  "limit": 0
 },
 "match": {
  "tc": "10+0.1",
  "pairs": 250
 },
 "hw": {
  "batch_sizes": "32,64,128,256",
  "bench_movetime": 10000
 }
}
ladder.py:46:    "tbset": {"per_class": 400, "classes": None},
ladder.py:50:    "study": {"split": "test", "limit": 0, "budgets": "0,100,400,800,1600",
ladder.py:54:    "studyc": {"movetimes": "200,800", "models": "fp16,BEST", "limit": 0},
ladder.py:56:    "hw": {"batch_sizes": "32,64,128,256", "bench_movetime": 10000},
ladder.py:140:    for n in names.split(","):
ladder.py:159:    if cfg["tbset"]["classes"]:
ladder.py:160:        cmd += ["--classes", cfg["tbset"]["classes"]]
ladder.py:171:        run([PY, script("quant", "make_calib.py"), *enc, "--weights", cfg["bt3"],
ladder.py:175:        run([PY, script("quant", "make_calib.py"), *enc, "--weights", cfg["bt3"],
ladder.py:182:    r = subprocess.run([cfg["lc0"], "describenet", f"--weights={cfg['bt3']}"],
ladder.py:205:        run([cfg["lc0"], "describenet", f"--weights={cfg['bt3']}"], log)
ladder.py:212:def study_cmd(cfg, name, budgets, split, limit, extra=()):
ladder.py:216:    return [PY, script("eval", "run_study.py"), "--lc0", cfg["lc0"], "--name", name,
ladder.py:217:            "--weights", model_weights(cfg, name), "--backend", backend, "--backend-opts", opts,
ladder.py:218:            "--tbset", P(cfg, "data", "tbset.jsonl"), "--split", split, "--limit", limit,
ladder.py:262:    n = a.limit or 200
ladder.py:284:    bench = [cfg["lc0"], "benchmark", f"--weights={model_weights(cfg, 's2')}",
ladder.py:352:    for n in names:
ladder.py:354:    onnxs = [P(cfg, "models", f"{n}.onnx") for n in names if not n.startswith("swap_")]
ladder.py:369:    for n in names + extras:
ladder.py:373:        run(study_cmd(cfg, n, s["budgets"], a.split or s["split"], a.limit if a.limit is not None else s["limit"]), log)
ladder.py:377:        run(study_cmd(cfg, "s0", b, a.split or s["split"], a.limit if a.limit is not None else s["limit"]), log)
ladder.py:383:    for n in resolve(cfg, a.models or c["models"]):
ladder.py:385:                        a.limit if a.limit is not None else c["limit"])
ladder.py:395:    names = [n for n in names if Path(P(cfg, "results", n)).exists()]
ladder.py:404:    cmd = [PY, script("eval", "match.py"), "--lc0", cfg["lc0"], "--name", f"fp16_vs_{best}",
ladder.py:416:def step_hw(cfg, a):
ladder.py:422:        for n in ("fp16", best, "native"):
ladder.py:425:            run([PY, script("hw", "bench.py"), "--lc0", cfg["lc0"], "--weights", model_weights(cfg, n),
ladder.py:426:                 "--name", n, "--backend", backend, "--backend-opts", opts,
ladder.py:427:                 "--movetime", h["bench_movetime"], "--out-dir", P(cfg, "reports", "bench")], log)
ladder.py:464:    ap.add_argument("--limit", type=int, default=None)
eval/run_study.py:16:    python eval/run_study.py --name fp16 --weights models/fp16.pb.gz --backend-opts optimize=6 \
eval/run_study.py:18:    python eval/run_study.py --name s4 --weights models/s4.pb.gz --backend-opts optimize=8 \
eval/run_study.py:34:def positions(a):
eval/run_study.py:37:    if a.classes:
eval/run_study.py:38:        keep = set(a.classes.split(","))
eval/run_study.py:40:    if a.ids:
eval/run_study.py:41:        keep = {int(x) for x in Path(a.ids).read_text().split()}
eval/run_study.py:43:    if a.limit:
eval/run_study.py:44:        # spread the limit over classes instead of taking the first classes
eval/run_study.py:49:        while len(out) < a.limit and any(by.values()):
eval/run_study.py:53:                    if len(out) >= a.limit:
eval/run_study.py:102:    ap.add_argument("--weights", required=True)
eval/run_study.py:103:    ap.add_argument("--name", required=True)
eval/run_study.py:113:    ap.add_argument("--limit", type=int, default=0)
eval/run_study.py:114:    ap.add_argument("--classes", default=None)
eval/run_study.py:115:    ap.add_argument("--ids", default=None, help="file of position ids to run")
hw/bench.py:14:    python hw/bench.py --lc0 lc0 --weights models/fp16.pb.gz --backend-opts optimize=6 --name fp16
hw/bench.py:15:    python hw/bench.py --lc0 lc0 --weights nets/BT3.pb.gz --backend cuda-fp16 --name native_cuda
hw/bench.py:92:    args = [f"--weights={a.weights}", f"--backend={a.backend}"]
hw/bench.py:126:    ap.add_argument("--weights", required=True)
hw/bench.py:127:    ap.add_argument("--name", required=True)
#!/usr/bin/env python3
"""Studies A, B and C on the tablebase set, through stock lc0 over UCI.

  A  (budget 0)       raw network: `go nodes 1`, PolicyTemperature=1, P of
                      every legal move + raw V/WL/D of the root.
  B  (--budgets)      fixed node budgets, SmartPruningFactor=0 so the search
                      really spends the budget. Actual nodes are recorded
                      (trap 6: `go nodes N` overshoots by up to a minibatch).
  C  (--movetimes)    fixed time per move with the engine's normal settings
                      (smart pruning on). A fresh engine per movetime so NN
                      cache entries from one pass cannot speed up the next.

Resumable: each (position, budget) is one jsonl line, finished ones are
skipped. --shard i/n splits the positions for parallel machines.

    python eval/run_study.py --name fp16 --weights models/fp16.pb.gz --backend-opts optimize=6 \
        --tbset data/tbset.jsonl --split test --budgets 0,100,400,800,1600
    python eval/run_study.py --name s4 --weights models/s4.pb.gz --backend-opts optimize=8 \
        --tbset data/tbset.jsonl --split test --movetimes 200,800 --threads 0
"""
import argparse
import json
import platform
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import append_jsonl, read_jsonl, write_json  # noqa: E402
from lc0uci import Lc0  # noqa: E402


def positions(a):
    recs = [r for r in read_jsonl(a.tbset) if r["split"] == a.split]
    recs.sort(key=lambda r: r["id"])
    if a.classes:
        keep = set(a.classes.split(","))
        recs = [r for r in recs if r["cls"] in keep]
    if a.ids:
        keep = {int(x) for x in Path(a.ids).read_text().split()}
        recs = [r for r in recs if r["id"] in keep]
    if a.limit:
        # spread the limit over classes instead of taking the first classes
        by = {}
        for r in recs:
            by.setdefault(r["cls"], []).append(r)
        out, i = [], 0
        while len(out) < a.limit and any(by.values()):
            for c in list(by):
                if by[c]:
                    out.append(by[c].pop(0))
                    if len(out) >= a.limit:
                        break
            i += 1
        recs = sorted(out, key=lambda r: r["id"])
    if a.shard:
        i, n = (int(x) for x in a.shard.split("/"))
        recs = [r for k, r in enumerate(recs) if k % n == i]
    return recs


def make_engine(a, log_dir, tag, study):
    opts = {"VerboseMoveStats": True, "MinibatchSize": a.minibatch}
    if a.nncache is not None:
        opts["NNCacheSize"] = a.nncache
    if study in ("A", "B"):
        opts["Threads"] = a.threads if a.threads else 1
    elif a.threads:
        opts["Threads"] = a.threads
    if study == "A":
        opts["PolicyTemperature"] = 1.0
    if study == "B":
        opts["SmartPruningFactor"] = 0
    if study == "C":
        # Trap 8: lc0 subtracts MoveOverheadMs (default 200 ms) from every
        # movetime, so `go movetime 200` would search for ~0 ms.
        opts["MoveOverheadMs"] = a.move_overhead
    for kv in a.option or []:
        k, v = kv.split("=", 1)
        opts[k] = v
    return Lc0(a.lc0, a.weights, backend=a.backend, backend_opts=a.backend_opts,
               options=opts, log=str(log_dir / f"{tag}.lc0.log"), name=f"{a.name}:{tag}")


class Progress:
    def __init__(self, total, label):
        self.total, self.label, self.t0, self.n = total, label, time.time(), 0

    def tick(self):
        self.n += 1
        if self.n % 25 == 0 or self.n == self.total:
            el = time.time() - self.t0
            eta = el / self.n * (self.total - self.n)
            print(f"  [{self.label}] {self.n}/{self.total}  {el / self.n:.2f}s/item  "
                  f"eta {eta / 60:.1f} min", file=sys.stderr, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lc0", default="lc0")
    ap.add_argument("--weights", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--backend", default="onnx-trt")
    ap.add_argument("--backend-opts", default="")
    ap.add_argument("--threads", type=int, default=0,
                    help="0: 1 for studies A/B, lc0's default for C")
    ap.add_argument("--minibatch", type=int, default=256)
    ap.add_argument("--nncache", type=int, default=None)
    ap.add_argument("--option", action="append", help="extra UCI option Name=Value")
    ap.add_argument("--tbset", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--classes", default=None)
    ap.add_argument("--ids", default=None, help="file of position ids to run")
    ap.add_argument("--shard", default=None, help="i/n")
    ap.add_argument("--budgets", default="", help="e.g. 0,100,400,800,1600 (0 = Study A)")
    ap.add_argument("--movetimes", default="", help="ms per move, e.g. 200,800 (Study C)")
    ap.add_argument("--move-overhead", type=int, default=20,
                    help="MoveOverheadMs for Study C (lc0 default 200 eats short movetimes)")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args()

    out = Path(a.out_dir) / a.name
    out.mkdir(parents=True, exist_ok=True)
    recs = positions(a)
    budgets = [int(x) for x in a.budgets.split(",") if x != ""]
    movetimes = [int(x) for x in a.movetimes.split(",") if x != ""]
    meta = {"name": a.name, "weights": a.weights, "backend": a.backend,
            "backend_opts": a.backend_opts, "threads": a.threads, "minibatch": a.minibatch,
            "split": a.split, "n_positions": len(recs), "move_overhead": a.move_overhead, "host": platform.node(),
            "started": time.strftime("%Y-%m-%d %H:%M:%S"), "warnings": []}
    print(f"{a.name}: {len(recs)} positions, budgets {budgets}, movetimes {movetimes}",
          file=sys.stderr)

    def done_keys(path, key):
        return {(r["id"], r[key]) for r in read_jsonl(path)}

    # ---------------- Study A
    if 0 in budgets:
        path = out / "study_a.jsonl"
        done = done_keys(path, "budget")
        todo = [r for r in recs if (r["id"], 0) not in done]
        if todo:
            e = make_engine(a, out, "A", "A")
def step_hw(cfg, a):
    h = cfg["hw"]
    log = P(cfg, "reports", "logs", "hw.log")
    best = cfg["best"]
    parts = a.parts.split(",") if a.parts else ["bench", "sweep", "trt", "roofline"]
    if "bench" in parts:
        for n in ("fp16", best, "native"):
            backend = cfg["native_backend"] if n == "native" else cfg["backend"]
            opts = cfg["native_opts"] if n == "native" else model_opts(cfg, n)
            run([PY, script("hw", "bench.py"), "--lc0", cfg["lc0"], "--weights", model_weights(cfg, n),
                 "--name", n, "--backend", backend, "--backend-opts", opts,
                 "--movetime", h["bench_movetime"], "--out-dir", P(cfg, "reports", "bench")], log)
    if "sweep" in parts:
        run([PY, script("hw", "batch_sweep.py"), "--lc0", cfg["lc0"], "--backend", cfg["backend"],
             "--sizes", h["batch_sizes"],
             "--model", f"fp16={model_weights(cfg, 'fp16')}:{cfg['fp16_opts']}",
             "--model", f"{best}={model_weights(cfg, best)}:{cfg['int8_opts']}",
             "--out", P(cfg, "reports", "batch_sweep")], log)
    trt = Path(P(cfg, "reports", "trt"))
    trt.mkdir(parents=True, exist_ok=True)
    builds = [("fp16", P(cfg, "models", "bt3_fp32.onnx"), [], ), (best, P(cfg, "models", f"{best}.onnx"), ["--int8"])]
    for sp in ("s0", "s1sp"):
        if Path(P(cfg, "models", f"{sp}.onnx")).exists():
            builds.append((f"{sp}_sparse", P(cfg, "models", f"{sp}.onnx"), ["--int8", "--sparsity"]))
            builds.append((f"{sp}_dense", P(cfg, "models", f"{sp}.onnx"), ["--int8"]))
  [swap_pol8 B] 1975/2437  1.48s/item  eta 11.4 min
  [swap_pol8 B] 2000/2437  1.48s/item  eta 10.8 min
  [swap_pol8 B] 2025/2437  1.48s/item  eta 10.2 min
  [swap_pol8 B] 2050/2437  1.48s/item  eta 9.6 min
  [swap_pol8 B] 2075/2437  1.49s/item  eta 9.0 min
  [swap_pol8 B] 2100/2437  1.49s/item  eta 8.4 min
  [swap_pol8 B] 2125/2437  1.49s/item  eta 7.7 min
  [swap_pol8 B] 2150/2437  1.49s/item  eta 7.1 min
  [swap_pol8 B] 2175/2437  1.48s/item  eta 6.5 min
  [swap_pol8 B] 2200/2437  1.49s/item  eta 5.9 min
  [swap_pol8 B] 2225/2437  1.49s/item  eta 5.3 min
  [swap_pol8 B] 2250/2437  1.49s/item  eta 4.7 min
  [swap_pol8 B] 2275/2437  1.50s/item  eta 4.0 min
  [swap_pol8 B] 2300/2437  1.50s/item  eta 3.4 min
  [swap_pol8 B] 2325/2437  1.50s/item  eta 2.8 min
  [swap_pol8 B] 2350/2437  1.51s/item  eta 2.2 min
  [swap_pol8 B] 2375/2437  1.51s/item  eta 1.6 min
  [swap_pol8 B] 2400/2437  1.51s/item  eta 0.9 min
  [swap_pol8 B] 2425/2437  1.51s/item  eta 0.3 min
  [swap_pol8 B] 2437/2437  1.51s/item  eta 0.0 min

$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name swap_val8 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\swap_val8.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --limit 2437 --budgets 0,100,400,800,1600 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results
2962
2966
2980
3043
3437
3787
4182
4215
4569
6568
6583
6606
6630
6969
6979
6991
7005
7027
7377
7383
7412
7414
7425
7763
7772
7792
7837
8166
8201
8205
8207
8229
8232
8570
8638
8640
9031
9766
9799
9827
10644
11004
11022

~~~
Sources inspected read-only. No GPU command or benchmark invoked. Existing LOG/STATUS history not rewritten.

[2026-10-28 10:56:03 +05:30] CPU-only inspection; exit 0. Commands: Get-Content README.md/RUN_4060.md -Encoding utf8; rg -n ID/CLI/bench selectors in eval/run_study.py, eval/score.py, ladder.py, hw/bench.py; Get-Content config.json and source excerpts; read reports/logs/study.log tail/final progress. Key output: eval/run_study.py:115 already supports --ids (file of position ids to run); positions() filters IDs before limit/shard. ladder.py:422 selects bench models with for n in (fp16, best, native); best=s4, no config bench-model list. No source/config changes required or made. swap_val8 B completed: [swap_val8 B] 2437/2437  1.50s/item  eta 0.0 min. Next logged command is --name s1sp. Existing background job untouched. No output artifact from inspection.

[2026-10-28 10:57:04 +05:30] CPU-only prep; files written: reports/cpu_prep_audit.py (analysis/helper only); no pipeline source edits. Prior hard-ID check command: Python stdin read reports/hard/ids.txt; exit 0; hard_ids_count=43 unique=43. Running exact command: ..\.venv\Scripts\python.exe reports\cpu_prep_audit.py. GPU launches forbidden by audit subprocess/engine guards.
[2026-10-28 10:57:04 +05:30] Command exit=0; key output and artifacts:
DRY RUN: default selection=2437; --ids reports/hard/ids.txt --limit 0 selection=43; exact ID match; subprocess and engine creation disabled
Full selected test set | fp16 | 2431/2437 | 0.997538 | 2431 | 0 | 0 | 1 |
Full selected test set | s1 | 2424/2437 | 0.994666 | 2431 | 7 | 0 | 0.015625 |
Full selected test set | s2 | 2427/2437 | 0.995897 | 2431 | 6 | 2 | 0.2890625 |
Full selected test set | s3 | 2431/2437 | 0.997538 | 2431 | 1 | 1 | 1 |
Full selected test set | s4 | 2431/2437 | 0.997538 | 2431 | 1 | 1 | 1 |
Full selected test set | s4aa | 2431/2437 | 0.997538 | 2431 | 1 | 1 | 1 |
Full selected test set | swap_pol8 | 2431/2437 | 0.997538 | 2431 | 1 | 1 | 1 |
Full selected test set | swap_val8 | 2431/2437 | 0.997538 | 2431 | 0 | 0 | 1 |
Existing hard IDs | fp16 | 37/43 | 0.860465 | 37 | 0 | 0 | 1 |
Existing hard IDs | s1 | 32/43 | 0.744186 | 37 | 5 | 0 | 0.0625 |
Existing hard IDs | s2 | 34/43 | 0.790698 | 37 | 5 | 2 | 0.453125 |
Existing hard IDs | s3 | 37/43 | 0.860465 | 37 | 1 | 1 | 1 |
Existing hard IDs | s4 | 37/43 | 0.860465 | 37 | 1 | 1 | 1 |
Existing hard IDs | s4aa | 37/43 | 0.860465 | 37 | 1 | 1 | 1 |
Existing hard IDs | swap_pol8 | 37/43 | 0.860465 | 37 | 1 | 1 | 1 |
Existing hard IDs | swap_val8 | 37/43 | 0.860465 | 37 | 0 | 0 | 1 |
RUNTIME {"model": "fp16", "A": 2437, "B_positions": 2437, "A_final": null, "B_final": {"count": 2054, "total": 2054, "seconds": "0.94", "line": "[fp16 B] 2054/2054  0.94s/item  eta 0.0 min"}, "latest_B": {"count": 2054, "total": 2054, "seconds": "0.94", "line": "[fp16 B] 2054/2054  0.94s/item  eta 0.0 min"}}
RUNTIME {"model": "s1", "A": 2437, "B_positions": 2437, "A_final": {"count": 2437, "total": 2437, "seconds": "0.14", "line": "[s1 A] 2437/2437  0.14s/item  eta 0.0 min"}, "B_final": {"count": 2437, "total": 2437, "seconds": "0.66", "line": "[s1 B] 2437/2437  0.66s/item  eta 0.0 min"}, "latest_B": {"count": 2437, "total": 2437, "seconds": "0.66", "line": "[s1 B] 2437/2437  0.66s/item  eta 0.0 min"}}
RUNTIME {"model": "s2", "A": 2437, "B_positions": 2437, "A_final": {"count": 2437, "total": 2437, "seconds": "0.01", "line": "[s2 A] 2437/2437  0.01s/item  eta 0.0 min"}, "B_final": {"count": 2437, "total": 2437, "seconds": "0.64", "line": "[s2 B] 2437/2437  0.64s/item  eta 0.0 min"}, "latest_B": {"count": 2437, "total": 2437, "seconds": "0.64", "line": "[s2 B] 2437/2437  0.64s/item  eta 0.0 min"}}
RUNTIME {"model": "s3", "A": 2437, "B_positions": 2437, "A_final": {"count": 2437, "total": 2437, "seconds": "0.06", "line": "[s3 A] 2437/2437  0.06s/item  eta 0.0 min"}, "B_final": {"count": 2437, "total": 2437, "seconds": "0.64", "line": "[s3 B] 2437/2437  0.64s/item  eta 0.0 min"}, "latest_B": {"count": 2437, "total": 2437, "seconds": "0.64", "line": "[s3 B] 2437/2437  0.64s/item  eta 0.0 min"}}
RUNTIME {"model": "s4", "A": 2437, "B_positions": 2437, "A_final": {"count": 2437, "total": 2437, "seconds": "0.05", "line": "[s4 A] 2437/2437  0.05s/item  eta 0.0 min"}, "B_final": {"count": 2437, "total": 2437, "seconds": "0.69", "line": "[s4 B] 2437/2437  0.69s/item  eta 0.0 min"}, "latest_B": {"count": 2437, "total": 2437, "seconds": "0.69", "line": "[s4 B] 2437/2437  0.69s/item  eta 0.0 min"}}
RUNTIME {"model": "s4aa", "A": 2437, "B_positions": 2437, "A_final": {"count": 2437, "total": 2437, "seconds": "0.06", "line": "[s4aa A] 2437/2437  0.06s/item  eta 0.0 min"}, "B_final": {"count": 2437, "total": 2437, "seconds": "0.73", "line": "[s4aa B] 2437/2437  0.73s/item  eta 0.0 min"}, "latest_B": {"count": 2437, "total": 2437, "seconds": "0.73", "line": "[s4aa B] 2437/2437  0.73s/item  eta 0.0 min"}}
RUNTIME {"model": "swap_pol8", "A": 2437, "B_positions": 2437, "A_final": {"count": 2437, "total": 2437, "seconds": "0.20", "line": "[swap_pol8 A] 2437/2437  0.20s/item  eta 0.0 min"}, "B_final": {"count": 2437, "total": 2437, "seconds": "1.51", "line": "[swap_pol8 B] 2437/2437  1.51s/item  eta 0.0 min"}, "latest_B": {"count": 2437, "total": 2437, "seconds": "1.51", "line": "[swap_pol8 B] 2437/2437  1.51s/item  eta 0.0 min"}}
RUNTIME {"model": "swap_val8", "A": 2437, "B_positions": 2437, "A_final": {"count": 2437, "total": 2437, "seconds": "0.11", "line": "[swap_val8 A] 2437/2437  0.11s/item  eta 0.0 min"}, "B_final": {"count": 2437, "total": 2437, "seconds": "1.50", "line": "[swap_val8 B] 2437/2437  1.50s/item  eta 0.0 min"}, "latest_B": {"count": 2437, "total": 2437, "seconds": "1.50", "line": "[swap_val8 B] 2437/2437  1.50s/item  eta 0.0 min"}}
RUNTIME {"model": "s1sp", "A": 1215, "B_positions": 0, "A_final": null, "B_final": null, "latest_B": null}
RUNTIME {"model": "s0", "A": 0, "B_positions": 0, "A_final": null, "B_final": null, "latest_B": null}
RUNTIME {"model": "native", "A": 0, "B_positions": 0, "A_final": null, "B_final": null, "latest_B": null}
UNCHANGED: eval/run_study.py eval/score.py hw/bench.py ladder.py config.json (SHA256 verified)
PRODUCED: reports/study_a_mcnemar.md; reports/cpu_prep_audit.json; reports/prepared_gpu_commands.md; reports/prepared_{hard_lowbudget,studyc,hw}.ps1 (NOT RUN)

[2026-10-28 10:57:37 +05:30] Append-only status update; command: PowerShell ConvertFrom-Json reports/cpu_prep_audit.json, construct snapshot/runtime/todo rows, Add-Content STATUS.md -Encoding utf8; exit 0. Produced STATUS.md appended rows. Key lines:

| gate/step | state | one-line result |
|---|---|---|
| CPU-only snapshot 10/28/2026 10:57:04 | done | Existing background study untouched; snapshot results and timings below; reports/cpu_prep_audit.json |
| CPU-only GPU observation | done | First nvidia-smi: 2026-10-28 10:47:00 IST, lc0 PID 21956, weights swap_val8.pb.gz, onnx-trt optimize=8; study.log subsequently completed swap_val8 and advanced to s1sp |
| Snapshot fp16 | done | A=2437/2437 (not printed in matching study.log completion); B=2437/2437 positions at all configured budgets (0.94 s/item) |
| Snapshot s1 | done | A=2437/2437 (0.14 s/item); B=2437/2437 positions at all configured budgets (0.66 s/item) |
| Snapshot s2 | done | A=2437/2437 (0.01 s/item); B=2437/2437 positions at all configured budgets (0.64 s/item) |
| Snapshot s3 | done | A=2437/2437 (0.06 s/item); B=2437/2437 positions at all configured budgets (0.64 s/item) |
| Snapshot s4 | done | A=2437/2437 (0.05 s/item); B=2437/2437 positions at all configured budgets (0.69 s/item) |
| Snapshot s4aa | done | A=2437/2437 (0.06 s/item); B=2437/2437 positions at all configured budgets (0.73 s/item) |
| Snapshot swap_pol8 | done | A=2437/2437 (0.20 s/item); B=2437/2437 positions at all configured budgets (1.51 s/item) |
| Snapshot swap_val8 | done | A=2437/2437 (0.11 s/item); B=2437/2437 positions at all configured budgets (1.50 s/item) |
| Snapshot s1sp | running | A=1215/2437 (not printed in matching study.log completion); B=0/2437 positions at all configured budgets (not finished) |
| Snapshot s0 | todo | A=0/2437 (not printed in matching study.log completion); B=0/2437 positions at all configured budgets (not finished) |
| Runtime interpretation | done | Study B s/item covers a position across 100,400,800,1600; fp16 final 2054/2054 is remaining work after resume, results confirm full 2437/2437 |
| Raw McNemar | done | Full n=2437 and existing hard n=43; 8 complete raw models; reports/study_a_mcnemar.md; incomplete s1sp/s0 excluded, native only historical dev results |
| ID filter dry run | done | Existing eval/run_study.py --ids supported; default 2437, hard 43 exact ID match; engine/subprocess launches disabled; no source change |
| Bench model selection | done | hw/bench.py accepts one model; ladder.py:422 hardcodes fp16,best,native = fp16,s4,native; adding s4aa requires code, so unchanged |
| Low-budget settings | done | Prepared commands retain Threads=1 and MinibatchSize=256 for all models; README trap 6 allows overshoot, use recorded actual nodes |
| Prepared hard-lowbudget fp16 | todo | NOT RUN: & 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 'fp16' '--weights' 'models/fp16.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=6' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'; cwd C:\Users\HP\Desktop\LC0-B\leela-int8; background launchers in reports/prepared_gpu_commands.md |
| Prepared hard-lowbudget s1 | todo | NOT RUN: & 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's1' '--weights' 'models/s1.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'; cwd C:\Users\HP\Desktop\LC0-B\leela-int8; background launchers in reports/prepared_gpu_commands.md |
| Prepared hard-lowbudget s2 | todo | NOT RUN: & 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's2' '--weights' 'models/s2.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'; cwd C:\Users\HP\Desktop\LC0-B\leela-int8; background launchers in reports/prepared_gpu_commands.md |
| Prepared hard-lowbudget s3 | todo | NOT RUN: & 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's3' '--weights' 'models/s3.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'; cwd C:\Users\HP\Desktop\LC0-B\leela-int8; background launchers in reports/prepared_gpu_commands.md |
| Prepared hard-lowbudget s4 | todo | NOT RUN: & 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's4' '--weights' 'models/s4.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'; cwd C:\Users\HP\Desktop\LC0-B\leela-int8; background launchers in reports/prepared_gpu_commands.md |
| Prepared hard-lowbudget s4aa | todo | NOT RUN: & 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'eval/run_study.py' '--lc0' 'C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe' '--name' 's4aa' '--weights' 'models/s4aa.pb.gz' '--backend' 'onnx-trt' '--backend-opts' 'optimize=8' '--tbset' 'data/tbset.jsonl' '--split' 'test' '--ids' 'reports/hard/ids.txt' '--limit' '0' '--budgets' '10,25,50,100,200' '--threads' '1' '--minibatch' '256' '--out-dir' 'results/hard_lowbudget'; cwd C:\Users\HP\Desktop\LC0-B\leela-int8; background launchers in reports/prepared_gpu_commands.md |
| Prepared studyc | todo | NOT RUN: & 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'ladder.py' 'studyc'; cwd C:\Users\HP\Desktop\LC0-B\leela-int8; background launchers in reports/prepared_gpu_commands.md |
| Prepared hw | todo | NOT RUN: & 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' '-u' 'ladder.py' 'hw'; cwd C:\Users\HP\Desktop\LC0-B\leela-int8; background launchers in reports/prepared_gpu_commands.md |
| CPU-only prep | done | Stopped after preparation; no GPU work started, stopped, resumed or restarted; no lc0/benchmark run; do not run prepared commands until existing pipeline finishes and GPU is idle |
[2026-10-28 10:57:37 +05:30] Verification command: PowerShell Language.Parser.ParseFile on three prepared scripts (parse only); exit 0; syntax_errors=0; scripts NOT EXECUTED. Artifacts: reports/prepared_gpu_commands.md, reports/prepared_hard_lowbudget.ps1, reports/prepared_studyc.ps1, reports/prepared_hw.ps1, reports/study_a_mcnemar.md, reports/cpu_prep_audit.json, reports/logs/cpu_prep_audit.log. All earlier LOG/STATUS entries preserved.

## 2026-10-28T11:26:29+05:30 — study resume completion
Exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py study
Exit code: 0
Key output:
~~~
  [s0 A] 725/2437  0.13s/item  eta 3.8 min
  [s0 A] 750/2437  0.13s/item  eta 3.6 min
  [s0 A] 775/2437  0.13s/item  eta 3.5 min
  [s0 A] 800/2437  0.12s/item  eta 3.3 min
  [s0 A] 825/2437  0.12s/item  eta 3.2 min
  [s0 A] 850/2437  0.11s/item  eta 3.0 min
  [s0 A] 875/2437  0.11s/item  eta 2.9 min
  [s0 A] 900/2437  0.11s/item  eta 2.8 min
  [s0 A] 925/2437  0.11s/item  eta 2.7 min
  [s0 A] 950/2437  0.10s/item  eta 2.6 min
  [s0 A] 975/2437  0.10s/item  eta 2.5 min
  [s0 A] 1000/2437  0.10s/item  eta 2.4 min
  [s0 A] 1025/2437  0.10s/item  eta 2.3 min
  [s0 A] 1050/2437  0.09s/item  eta 2.2 min
  [s0 A] 1075/2437  0.09s/item  eta 2.1 min
  [s0 A] 1100/2437  0.09s/item  eta 2.0 min
  [s0 A] 1125/2437  0.09s/item  eta 1.9 min
  [s0 A] 1150/2437  0.09s/item  eta 1.9 min
  [s0 A] 1175/2437  0.08s/item  eta 1.8 min
  [s0 A] 1200/2437  0.08s/item  eta 1.7 min
  [s0 A] 1225/2437  0.08s/item  eta 1.6 min
  [s0 A] 1250/2437  0.08s/item  eta 1.6 min
  [s0 A] 1275/2437  0.08s/item  eta 1.5 min
  [s0 A] 1300/2437  0.08s/item  eta 1.5 min
  [s0 A] 1325/2437  0.08s/item  eta 1.4 min
  [s0 A] 1350/2437  0.07s/item  eta 1.4 min
  [s0 A] 1375/2437  0.07s/item  eta 1.3 min
  [s0 A] 1400/2437  0.07s/item  eta 1.2 min
  [s0 A] 1425/2437  0.07s/item  eta 1.2 min
  [s0 A] 1450/2437  0.07s/item  eta 1.1 min
  [s0 A] 1475/2437  0.07s/item  eta 1.1 min
  [s0 A] 1500/2437  0.07s/item  eta 1.1 min
  [s0 A] 1525/2437  0.07s/item  eta 1.0 min
  [s0 A] 1550/2437  0.07s/item  eta 1.0 min
  [s0 A] 1575/2437  0.06s/item  eta 0.9 min
  [s0 A] 1600/2437  0.06s/item  eta 0.9 min
  [s0 A] 1625/2437  0.06s/item  eta 0.9 min
  [s0 A] 1650/2437  0.06s/item  eta 0.8 min
  [s0 A] 1675/2437  0.06s/item  eta 0.8 min
  [s0 A] 1700/2437  0.06s/item  eta 0.7 min
  [s0 A] 1725/2437  0.06s/item  eta 0.7 min
  [s0 A] 1750/2437  0.06s/item  eta 0.7 min
  [s0 A] 1775/2437  0.06s/item  eta 0.6 min
  [s0 A] 1800/2437  0.06s/item  eta 0.6 min
  [s0 A] 1825/2437  0.06s/item  eta 0.6 min
  [s0 A] 1850/2437  0.06s/item  eta 0.5 min
  [s0 A] 1875/2437  0.06s/item  eta 0.5 min
  [s0 A] 1900/2437  0.05s/item  eta 0.5 min
  [s0 A] 1925/2437  0.05s/item  eta 0.5 min
  [s0 A] 1950/2437  0.05s/item  eta 0.4 min
  [s0 A] 1975/2437  0.05s/item  eta 0.4 min
  [s0 A] 2000/2437  0.05s/item  eta 0.4 min
  [s0 A] 2025/2437  0.05s/item  eta 0.4 min
  [s0 A] 2050/2437  0.05s/item  eta 0.3 min
  [s0 A] 2075/2437  0.05s/item  eta 0.3 min
  [s0 A] 2100/2437  0.05s/item  eta 0.3 min
  [s0 A] 2125/2437  0.05s/item  eta 0.3 min
  [s0 A] 2150/2437  0.05s/item  eta 0.2 min
  [s0 A] 2175/2437  0.05s/item  eta 0.2 min
  [s0 A] 2200/2437  0.05s/item  eta 0.2 min
  [s0 A] 2225/2437  0.05s/item  eta 0.2 min
  [s0 A] 2250/2437  0.05s/item  eta 0.1 min
  [s0 A] 2275/2437  0.05s/item  eta 0.1 min
  [s0 A] 2300/2437  0.05s/item  eta 0.1 min
  [s0 A] 2325/2437  0.05s/item  eta 0.1 min
  [s0 A] 2350/2437  0.05s/item  eta 0.1 min
  [s0 A] 2375/2437  0.05s/item  eta 0.0 min
  [s0 A] 2400/2437  0.04s/item  eta 0.0 min
  [s0 A] 2425/2437  0.04s/item  eta 0.0 min
  [s0 A] 2437/2437  0.04s/item  eta 0.0 min
~~~
Outputs: reports/logs/study.log; C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-resume-study-console.log; results/*/study_*.jsonl and meta.json/meta.jsonl; reports/logs/C2-resume-study-result.json


## 2026-10-28T11:26:29+05:30 — command start
Phase: score
Cwd: C:\Users\HP\Desktop\LC0-B\leela-int8
Exact command: `C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py score`
CPU-only environment: True; TEMP/TMP=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\tmp
Output: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-score.log
Exit code: running.


## 2026-10-28T11:26:31+05:30 — command completion
Exact command: `C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u ladder.py score`
Exit code: 0
Elapsed command seconds: 1.563
Authorized timing switch: False
Output file: C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\C2-score.log
Key output:
~~~

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

wrote C:\Users\HP\Desktop\LC0-B\leela-int8\reports/scores_test.md and hard/ (43 hard positions)
~~~


## 2026-10-28T11:26:32+05:30 — printed model score
fp16: A accuracy=0.9975379565038982, n=2437; B100 acc=0.9996 node-equivalent=1.00; B400 acc=1.0000 node-equivalent=1.00; B800 acc=1.0000 node-equivalent=1.00; B1600 acc=1.0000 node-equivalent=1.00; B n=2437


## 2026-10-28T11:26:33+05:30 — printed model score
s1: A accuracy=0.9946655724251129, n=2437; B100 acc=0.9992 node-equivalent=0.35; B400 acc=1.0000 node-equivalent=1.04; B800 acc=1.0000 node-equivalent=1.00; B1600 acc=1.0000 node-equivalent=1.00; B n=2437


## 2026-10-28T11:26:33+05:30 — printed model score
s2: A accuracy=0.9958965941731637, n=2437; B100 acc=0.9996 node-equivalent=0.99; B400 acc=1.0000 node-equivalent=1.03; B800 acc=1.0000 node-equivalent=1.00; B1600 acc=1.0000 node-equivalent=1.00; B n=2437


## 2026-10-28T11:26:34+05:30 — printed model score
s3: A accuracy=0.9975379565038982, n=2437; B100 acc=0.9996 node-equivalent=0.98; B400 acc=0.9996 node-equivalent=0.35; B800 acc=1.0000 node-equivalent=1.00; B1600 acc=1.0000 node-equivalent=1.00; B n=2437


## 2026-10-28T11:26:34+05:30 — printed model score
s4: A accuracy=0.9975379565038982, n=2437; B100 acc=0.9996 node-equivalent=0.97; B400 acc=1.0000 node-equivalent=1.02; B800 acc=1.0000 node-equivalent=1.00; B1600 acc=1.0000 node-equivalent=1.00; B n=2437


## 2026-10-28T11:26:35+05:30 — printed model score
s4aa: A accuracy=0.9975379565038982, n=2437; B100 acc=0.9996 node-equivalent=0.97; B400 acc=1.0000 node-equivalent=1.02; B800 acc=1.0000 node-equivalent=1.00; B1600 acc=1.0000 node-equivalent=1.00; B n=2437


## 2026-10-28T11:26:35+05:30 — printed model score
swap_pol8: A accuracy=0.9975379565038982, n=2437; B100 acc=0.9996 node-equivalent=1.07; B400 acc=1.0000 node-equivalent=1.04; B800 acc=1.0000 node-equivalent=1.00; B1600 acc=1.0000 node-equivalent=1.00; B n=2437


## 2026-10-28T11:26:36+05:30 — printed model score
swap_val8: A accuracy=0.9975379565038982, n=2437; B100 acc=0.9996 node-equivalent=1.07; B400 acc=1.0000 node-equivalent=1.04; B800 acc=1.0000 node-equivalent=1.00; B1600 acc=1.0000 node-equivalent=1.00; B n=2437


## 2026-10-28T11:26:36+05:30 — printed model score
s1sp: A accuracy=0.9909725071809602, n=2437; B100 acc=0.9938 node-equivalent=0.00; B400 acc=0.9930 node-equivalent=0.00; B800 acc=0.9943 node-equivalent=0.00; B1600 acc=0.9943 node-equivalent=0.00; B n=2437


## 2026-10-28T11:26:37+05:30 — printed model score
s0: A accuracy=0.8034468608945424, n=2437; Study A only (runbook S0)


## 2026-10-28T11:26:37+05:30 — C2 final evidence
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

Produced: reports/C2-done.md, reports/scores_test.md, reports/scores_test.json, reports/hard/; source hashes unchanged. Exit code: 0.


[2026-10-28 12:48:10 +05:30] C3-part1 start; commands: Get-Content README.md/RUN_4060.md/STATUS.md/LOG.md -Encoding utf8 and nvidia-smi; exit 0. GPU idle: 41C, 0%, 0MiB, no running processes. CPU inspection: ladder.py config/path/study/hw routing, quant/stitch_swap.py, swap sidecars, tbset example, run_study arguments, s0 study.log launch; exit 0. Existing --ids supported, --ids-file absent. Bench list hardcoded fp16,best,native; adding s4aa requires code and is not authorized by conditional, leave unchanged. No score or match.

[2026-10-28 12:49:03 +05:30] Exact command: ..\.venv\Scripts\python.exe reports/c3_cpu_errors.py; exit=0; key output:
| 2173 | KQvKQ | `1k6/5K2/8/8/1q6/8/5Q2/8 w - - 0 1` | f7f6 | -1 | +0 | f2a2, f2c2, f2e2, f2e3, f2f1, f2f3, f2f5, f2f6, f2g1, f2g2, f2g3, f2h2, f7e6, f7e8, f7g6, f7g7, f7g8 | f2g3 | yes |
| 6609 | KRPvKR | `4k1r1/7p/8/8/8/3K4/R7/8 w - - 0 1` | d3d2 | -1 | +0 | a2a1, a2a4, a2a5, a2a6, a2a7, a2a8, a2b2, a2c2, a2d2, a2e2, a2f2, a2h2, d3c3, d3c4, d3d4, d3e3, d3e4 | a2a8 | yes |
| 7369 | KQPvKQ | `1k6/7p/2Q5/4K3/8/8/q7/8 w - - 0 1` | e5e4 | -1 | +0 | c6b5, c6b6, c6c1, c6c3, c6c5, c6d5, c6d6, c6d7, c6e4, c6e6, c6e8, c6f3, c6f6, c6h1, c6h6, e5d4, e5d6, e5f4, e5f5, e5f6 | c6d6 | yes |
| 7383 | KQPvKQ | `2K5/8/4k3/8/8/6p1/2Q5/5q2 b - - 0 1` | g3g2 | +0 | +1 | f1f5, f1f8 | f1f5 | yes |
| 7394 | KQPvKQ | `2k5/8/1q6/8/1p6/4K3/Q7/8 w - - 0 1` | e3d2 | -1 | +0 | e3d3, e3e2, e3e4 | e3e2 | yes |
| 7411 | KQPvKQ | `4K3/8/3p4/3Q4/7k/8/7q/8 w - - 0 1` | d5d3 | -1 | +0 | d5c4, d5c6, d5d1, d5d4, d5e4, d5e6, d5f3, d5f7, e8d7, e8d8, e8e7, e8f7 | e8d7 | yes |
| 7442 | KQPvKQ | `6k1/3q4/6KQ/5P2/8/8/8/8 w - - 0 1` | h6h2 | -1 | +0 | f5f6, g6f6, g6g5, g6h5, h6c1, h6e3, h6f4, h6g5, h6h3, h6h4 | h6g5 | yes |
| 8232 | KBPvKN | `8/1N6/7p/8/3K4/8/7b/5k2 w - - 0 1` | b7d8 | -1 | +0 | d4e3, d4e4 | d4e4 | yes |
| 8631 | KPPvKP | `8/1k5p/3P4/8/K7/3P4/8/8 w - - 0 1` | d6d7 | -1 | +0 | a4b3, a4b4, a4b5 | a4b5 | yes |
| 9021 | KQvKRP | `6QK/8/2k5/1p3r2/8/8/8/8 b - - 0 1` | f5d5 | +0 | +1 | f5h5 | f5h5 | yes |
| 9780 | KQRvKQ | `1q6/6r1/7Q/k4K2/8/8/8/8 b - - 0 1` | g7g8 | +0 | +1 | b8a7, b8b1, b8b2, b8b5, b8b7, b8c7, b8c8, b8f8, b8g3, b8g8, g7a7, g7b7, g7c7, g7d7, g7e7, g7f7, g7g1, g7g2, g7g3, g7h7 | g7f7 | yes |
| 9817 | KQRvKQ | `3k4/K7/2Q5/8/7q/8/8/3r4 b - - 0 1` | d1h1 | +0 | +1 | d1a1, d1d2, d1d3, d1d4, d1d7, d1e1, d8e7, h4b4, h4d4, h4e1, h4e7, h4f2, h4f4, h4g3, h4g4, h4g5, h4h1, h4h2, h4h3, h4h5, h4h7 | h4e7 | yes |
| 9827 | KQRvKQ | `4Q3/2q5/8/8/8/6k1/4R3/5K2 b - - 0 1` | c7f4 | -1 | +0 | c7c1 | c7c1 | yes |
| 11004 | KPPvKN | `5K2/8/6p1/1p1k4/8/8/5N2/8 b - - 0 1` | b5b4 | +0 | +1 | d5e6 | d5e6 | yes |
| 188 | KQvK | `4K1k1/8/8/8/8/2q5/8/8 b - - 0 1` | c3c7 | +0 | +1 | c3a1, c3a3, c3a5, c3b2, c3b3, c3b4, c3c1, c3c2, c3c4, c3c5, c3c6, c3c8, c3d2, c3d3, c3d4, c3e1, c3e3, c3e5, c3f3, c3f6, c3g3, c3g7, c3h3, c3h8, g8g7, g8h7, g8h8 | c3c6 | yes |
| 216 | KQvK | `7k/8/1K6/3Q4/8/8/8/8 w - - 0 1` | d5f7 | +0 | +1 | b6a5, b6a6, b6a7, b6b5, b6b7, b6c5, b6c6, b6c7, d5a2, d5a5, d5a8, d5b3, d5b5, d5b7, d5c4, d5c5, d5c6, d5d1, d5d2, d5d3, d5d4, d5d6, d5d7, d5d8, d5e4, d5e5, d5e6, d5f3, d5f5, d5g2, d5g5, d5h1, d5h5 | d5g5 | yes |
| 218 | KQvK | `7k/8/8/8/8/8/6K1/5Q2 w - - 0 1` | f1f7 | +0 | +1 | f1a1, f1a6, f1b1, f1b5, f1c1, f1c4, f1d1, f1d3, f1e1, f1e2, f1f2, f1f3, f1f4, f1f5, f1f6, f1f8, f1g1, f1h1, g2f2, g2f3, g2g1, g2g3, g2h1, g2h2, g2h3 | g2f3 | yes |
| 229 | KQvK | `8/1q6/8/8/5k2/8/8/K7 b - - 0 1` | b7b3 | +0 | +1 | b7a6, b7a7, b7a8, b7b4, b7b5, b7b6, b7b8, b7c6, b7c7, b7c8, b7d5, b7d7, b7e4, b7e7, b7f3, b7f7, b7g2, b7g7, b7h1, b7h7, f4e3, f4e4, f4e5, f4f3, f4f5, f4g3, f4g4, f4g5 | f4e3 | yes |
| 234 | KQvK | `8/2K5/8/8/8/4Q3/8/7k w - - 0 1` | e3f2 | +0 | +1 | c7b6, c7b7, c7b8, c7c6, c7c8, c7d6, c7d7, c7d8, e3a3, e3a7, e3b3, e3b6, e3c1, e3c3, e3c5, e3d2, e3d3, e3d4, e3e1, e3e2, e3e4, e3e5, e3e6, e3e7, e3e8, e3f3, e3f4, e3g5, e3h3, e3h6 | c7d6 | yes |
| 235 | KQvK | `8/2K5/8/8/8/8/1Q6/7k w - - 0 1` | b2f2 | +0 | +1 | b2a1, b2a2, b2a3, b2b1, b2b3, b2b4, b2b5, b2b6, b2b7, b2b8, b2c1, b2c2, b2c3, b2d2, b2d4, b2e2, b2e5, b2f6, b2g7, b2h8, c7b6, c7b7, c7b8, c7c6, c7c8, c7d6, c7d7, c7d8 | c7d6 | yes |
swap_pol8 {"pb_gz_sha256": "82d2f082d33c41fd3bd06280d99a6f35850e94f3fd4dc314d7fe234c60c24319", "onnx_sha256": "92da35c3df1ef37d66aac0909f2337b1a91685d289d10797d777e8fb16d94c51", "policy": {"model": "s4", "onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.onnx", "sha256": "24fd9a11bbc755962b98fab08dd49f9a721c797097dfb607183e27b7e76e1904", "verified_sha256": "24fd9a11bbc755962b98fab08dd49f9a721c797097dfb607183e27b7e76e1904"}, "value_mlh": {"model": "fp16", "onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\bt3_fp32.onnx", "sha256": "937d5ac3d1ce9daafc7858f54166787924680c0c9c4aaab94d438402430db2b9", "verified_sha256": "937d5ac3d1ce9daafc7858f54166787924680c0c9c4aaab94d438402430db2b9"}, "shared_graph_inputs": ["/input/planes"], "quantize_nodes_by_branch": {"P": 270, "V": 0}, "output_routes": {"/swap/policy": ["P/output/policy"], "/swap/output/wdl": ["V/output/wdl"], "/swap/output/mlh": ["V/output/mlh"]}}
swap_val8 {"pb_gz_sha256": "f59515059aa106615ba0cfc188cff8317a7ca6b1e6eebbfa2a2367a41f210fe5", "onnx_sha256": "40bd6f0aae177df4225ce4048302ba76f267dc5a16f001593ba31227f266b56d", "policy": {"model": "fp16", "onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\bt3_fp32.onnx", "sha256": "937d5ac3d1ce9daafc7858f54166787924680c0c9c4aaab94d438402430db2b9", "verified_sha256": "937d5ac3d1ce9daafc7858f54166787924680c0c9c4aaab94d438402430db2b9"}, "value_mlh": {"model": "s4", "onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\models\\s4.onnx", "sha256": "24fd9a11bbc755962b98fab08dd49f9a721c797097dfb607183e27b7e76e1904", "verified_sha256": "24fd9a11bbc755962b98fab08dd49f9a721c797097dfb607183e27b7e76e1904"}, "shared_graph_inputs": ["/input/planes"], "quantize_nodes_by_branch": {"P": 0, "V": 274}, "output_routes": {"/swap/policy": ["P/output/policy"], "/swap/output/wdl": ["V/output/wdl"], "/swap/output/mlh": ["V/output/mlh"]}}
CONFIRMED: 14 s1sp B1600 errors; 6 s1sp KQvK raw errors; swap weights differ; policy/value source files are reversed, hashes verified, quantized P/V branches reversed. Both intentionally share the board-plane input.
PRODUCED reports/s1sp_errors.md reports/c3_swap_provenance.json
Files: reports/s1sp_errors.md, reports/c3_swap_provenance.json, reports/logs/c3_cpu_errors.log. CPU-only, no pipeline code changes. Inspection hw/ladder sources exit 0: hw uses check=False for TRT/roofline child failures; enforce stop rules in launch supervisor.

[2026-10-28 12:49:27 +05:30] Exact command: Python stdin CPU argparse/positions dry run (captured reports/logs/c3_ids_dryrun.log); exit=0. Authorized one-line eval/run_study.py diff:
-    ap.add_argument("--ids", default=None, help="file of position ids to run")
+    ap.add_argument("--ids", "--ids-file", dest="ids", default=None, help="file of position ids to run")
No quantization/scoring logic changed. Key output:
Parsed option=['--ids-file', 'reports/hard/ids.txt'] selected=43 IDs; ids=reports/hard/ids.txt
Parsed option=['--ids', 'reports/hard/ids.txt'] selected=43 IDs; ids=reports/hard/ids.txt
Parsed option=['--split', 'test'] selected=6720 IDs; ids=None
PASS: alias and existing option select 43; default-off selects all 6720 test positions; zero lc0 calls

[2026-10-28 12:49:55 +05:30] Exact preparation: PowerShell New-Item directories/junctions and UTF-8 no-BOM JSON snapshots from config.json, with only work and absolute bt3 changed; exit 0. File outputs: reports/c3-part1/config.studyc.json, config.hw.json; models/data junctions point at existing project artifacts; results/studyc and reports/c3_hw are isolated outputs; stage logs route to reports/logs. Main config unchanged. Bench s4aa addition requires code, so not added.

[2026-10-28 12:50:39 +05:30] Exact command: ..\.venv\Scripts\python.exe -m py_compile reports/c3_cpu_errors.py reports/c3_hw_guard.py reports/c3_part1_run.py; exit=0. Created report-only helpers, no pipeline changes beyond logged --ids-file alias. Background controller strictly sequences a0 -> six hard models -> studyc -> hw; no score/match/retry. HW wrapper imports unchanged ladder and forces run(check=True), because native hw passes check=False for TRT/roofline; first failing child will stop instead of continuing. Exact underlying hw arguments: ladder.py hw --config reports/c3-part1/config.hw.json. Main config unchanged; stage config only work/absolute BT3 paths. All helper/temp/log/result paths stay in project. Prepared commands/result paths in controller and STATUS; no jobs launched by compile.

[2026-10-28 12:51:00 +05:30] Exact background launch: Start-Process -FilePath 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' -ArgumentList @('-u','reports/c3_part1_run.py') -WorkingDirectory 'C:\Users\HP\Desktop\LC0-B\leela-int8' -WindowStyle Hidden -RedirectStandardOutput reports/logs/c3_controller.stdout.log -RedirectStandardError reports/logs/c3_controller.stderr.log -PassThru; launch exit 0; controller PID=11376. No overlaps; stop on first failure. State reports/c3-part1/state.json. Each command/result/log recorded by supervisor.

[2026-10-28 12:51:00 +0530] a0 GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 12:51:00 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   40C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 40, 210, 0, 0
compute processes: none

[2026-10-28 12:51:01 +0530] Launching a0_s0 in background controller, exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s0 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --limit 2437 --budgets 100,400 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\s0_search; cwd=C:\Users\HP\Desktop\LC0-B\leela-int8; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a0_s0.log; result=results/s0_search/s0; resume command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s0 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --limit 2437 --budgets 100,400 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\s0_search; no automatic resume

[2026-10-28 12:57:45 +0530] Finished a0_s0; exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s0 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s0.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --limit 2437 --budgets 100,400 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\s0_search; exit=0; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a0_s0.log; result=results/s0_search/s0; key output:
  [s0 B] 2025/2437  0.16s/item  eta 1.1 min
  [s0 B] 2050/2437  0.16s/item  eta 1.0 min
  [s0 B] 2075/2437  0.16s/item  eta 1.0 min
  [s0 B] 2100/2437  0.16s/item  eta 0.9 min
  [s0 B] 2125/2437  0.16s/item  eta 0.8 min
  [s0 B] 2150/2437  0.16s/item  eta 0.8 min
  [s0 B] 2175/2437  0.16s/item  eta 0.7 min
  [s0 B] 2200/2437  0.16s/item  eta 0.6 min
  [s0 B] 2225/2437  0.16s/item  eta 0.6 min
  [s0 B] 2250/2437  0.16s/item  eta 0.5 min
  [s0 B] 2275/2437  0.16s/item  eta 0.4 min
  [s0 B] 2300/2437  0.16s/item  eta 0.4 min
  [s0 B] 2325/2437  0.16s/item  eta 0.3 min
  [s0 B] 2350/2437  0.16s/item  eta 0.2 min
  [s0 B] 2375/2437  0.16s/item  eta 0.2 min
  [s0 B] 2400/2437  0.17s/item  eta 0.1 min
  [s0 B] 2425/2437  0.17s/item  eta 0.0 min
  [s0 B] 2437/2437  0.17s/item  eta 0.0 min

[2026-10-28 12:57:45 +0530] a_fp16 GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 12:57:45 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   67C    P0             37W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 67, 2520, 0, 0
compute processes: none

[2026-10-28 12:57:46 +0530] Launching a_fp16 in background controller, exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name fp16 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\fp16.pb.gz --backend onnx-trt --backend-opts optimize=6 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; cwd=C:\Users\HP\Desktop\LC0-B\leela-int8; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_fp16.log; result=results/hard_lowbudget/fp16; resume command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name fp16 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\fp16.pb.gz --backend onnx-trt --backend-opts optimize=6 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; no automatic resume

[2026-10-28 12:58:07 +0530] Finished a_fp16; exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name fp16 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\fp16.pb.gz --backend onnx-trt --backend-opts optimize=6 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; exit=0; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_fp16.log; result=results/hard_lowbudget/fp16; key output:

[2026-10-28 12:57:46 +0530] $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name fp16 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\fp16.pb.gz --backend onnx-trt --backend-opts optimize=6 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget
fp16: 43 positions, budgets [10, 25, 50, 100, 200], movetimes []
  [fp16 B] 25/43  0.56s/item  eta 0.2 min
  [fp16 B] 43/43  0.45s/item  eta 0.0 min

[2026-10-28 12:58:07 +0530] a_s1 GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 12:58:07 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   65C    P0             27W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 65, 2520, 0, 0
compute processes: none

[2026-10-28 12:58:07 +0530] Launching a_s1 in background controller, exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s1 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; cwd=C:\Users\HP\Desktop\LC0-B\leela-int8; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s1.log; result=results/hard_lowbudget/s1; resume command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s1 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; no automatic resume

[2026-10-28 12:58:25 +0530] Finished a_s1; exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s1 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; exit=0; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s1.log; result=results/hard_lowbudget/s1; key output:

[2026-10-28 12:58:08 +0530] $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s1 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s1.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget
s1: 43 positions, budgets [10, 25, 50, 100, 200], movetimes []
  [s1 B] 25/43  0.43s/item  eta 0.1 min
  [s1 B] 43/43  0.36s/item  eta 0.0 min

[2026-10-28 12:58:25 +0530] a_s2 GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 12:58:25 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   62C    P0             28W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 62, 2520, 0, 0
compute processes: none

[2026-10-28 12:58:26 +0530] Launching a_s2 in background controller, exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s2 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s2.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; cwd=C:\Users\HP\Desktop\LC0-B\leela-int8; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s2.log; result=results/hard_lowbudget/s2; resume command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s2 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s2.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; no automatic resume

[2026-10-28 12:58:43 +0530] Finished a_s2; exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s2 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s2.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; exit=0; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s2.log; result=results/hard_lowbudget/s2; key output:

[2026-10-28 12:58:26 +0530] $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s2 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s2.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget
s2: 43 positions, budgets [10, 25, 50, 100, 200], movetimes []
  [s2 B] 25/43  0.43s/item  eta 0.1 min
  [s2 B] 43/43  0.36s/item  eta 0.0 min

[2026-10-28 12:58:43 +0530] a_s3 GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 12:58:43 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   62C    P0             34W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 61, 2520, 0, 0
compute processes: none

[2026-10-28 12:58:44 +0530] Launching a_s3 in background controller, exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s3 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; cwd=C:\Users\HP\Desktop\LC0-B\leela-int8; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s3.log; result=results/hard_lowbudget/s3; resume command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s3 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; no automatic resume

[2026-10-28 12:59:01 +0530] Finished a_s3; exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s3 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; exit=0; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s3.log; result=results/hard_lowbudget/s3; key output:

[2026-10-28 12:58:44 +0530] $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s3 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s3.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget
s3: 43 positions, budgets [10, 25, 50, 100, 200], movetimes []
  [s3 B] 25/43  0.43s/item  eta 0.1 min
  [s3 B] 43/43  0.36s/item  eta 0.0 min

[2026-10-28 12:59:01 +0530] a_s4 GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 12:59:01 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   62C    P0             26W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 62, 2520, 0, 0
compute processes: none

[2026-10-28 12:59:01 +0530] Launching a_s4 in background controller, exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s4 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; cwd=C:\Users\HP\Desktop\LC0-B\leela-int8; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s4.log; result=results/hard_lowbudget/s4; resume command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s4 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; no automatic resume

[2026-10-28 12:59:19 +0530] Finished a_s4; exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s4 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; exit=0; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s4.log; result=results/hard_lowbudget/s4; key output:

[2026-10-28 12:59:02 +0530] $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s4 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget
s4: 43 positions, budgets [10, 25, 50, 100, 200], movetimes []
  [s4 B] 25/43  0.45s/item  eta 0.1 min
  [s4 B] 43/43  0.37s/item  eta 0.0 min

[2026-10-28 12:59:20 +0530] a_s4aa GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 12:59:20 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   61C    P0             28W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 61, 2520, 0, 0
compute processes: none

[2026-10-28 12:59:20 +0530] Launching a_s4aa in background controller, exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s4aa --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; cwd=C:\Users\HP\Desktop\LC0-B\leela-int8; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s4aa.log; result=results/hard_lowbudget/s4aa; resume command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s4aa --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; no automatic resume

[2026-10-28 12:59:39 +0530] Finished a_s4aa; exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s4aa --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget; exit=0; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_a_s4aa.log; result=results/hard_lowbudget/s4aa; key output:

[2026-10-28 12:59:21 +0530] $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name s4aa --weights C:\Users\HP\Desktop\LC0-B\leela-int8\models\s4aa.pb.gz --backend onnx-trt --backend-opts optimize=8 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\data\tbset.jsonl --split test --ids-file C:\Users\HP\Desktop\LC0-B\leela-int8\reports\hard\ids.txt --limit 0 --budgets 10,25,50,100,200 --threads 1 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\results\hard_lowbudget
s4aa: 43 positions, budgets [10, 25, 50, 100, 200], movetimes []
  [s4aa B] 25/43  0.48s/item  eta 0.1 min
  [s4aa B] 43/43  0.40s/item  eta 0.0 min

[2026-10-28 12:59:40 +0530] b_studyc GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 12:59:39 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   61C    P0             21W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 61, 2520, 0, 0
compute processes: none

[2026-10-28 13:00:10 +0530] b_studyc GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 13:00:10 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   48C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 48, 210, 0, 0
compute processes: none

[2026-10-28 13:00:10 +0530] Optional clock lock: nvidia-smi -lgc 1500,1500; exit=4; The current user does not have permission to change clocks for GPU 00000000:01:00.0.
Terminating early due to previous errors.
; if unavailable/admin-required, skipped per explicit user instruction; no escalation

[2026-10-28 13:00:11 +0530] b_studyc after optional clock-lock attempt GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 13:00:11 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   48C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 48, 210, 0, 0
compute processes: none

[2026-10-28 13:00:11 +0530] Launching b_studyc in background controller, exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\ladder.py studyc --config C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\config.studyc.json; cwd=C:\Users\HP\Desktop\LC0-B\leela-int8; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_b_studyc.log; result=results/studyc; reports/c3_studyc; resume command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\ladder.py studyc --config C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\config.studyc.json; no automatic resume

[2026-10-28 13:00:23 +05:30] Exact verification: Python stdin JSONL count/unique-key checks for results/s0_search and results/hard_lowbudget (no engine/scorer); exit=0; key output:
results\s0_search\s0\study_b.jsonl: rows=4874, distinct keys=4874, positions=2437, budgets=[100, 400]; PASS
results\hard_lowbudget\fp16\study_b.jsonl: rows=215, distinct keys=215, positions=43, budgets=[10, 25, 50, 100, 200]; PASS
results\hard_lowbudget\s1\study_b.jsonl: rows=215, distinct keys=215, positions=43, budgets=[10, 25, 50, 100, 200]; PASS
results\hard_lowbudget\s2\study_b.jsonl: rows=215, distinct keys=215, positions=43, budgets=[10, 25, 50, 100, 200]; PASS
results\hard_lowbudget\s3\study_b.jsonl: rows=215, distinct keys=215, positions=43, budgets=[10, 25, 50, 100, 200]; PASS
results\hard_lowbudget\s4\study_b.jsonl: rows=215, distinct keys=215, positions=43, budgets=[10, 25, 50, 100, 200]; PASS
results\hard_lowbudget\s4aa\study_b.jsonl: rows=215, distinct keys=215, positions=43, budgets=[10, 25, 50, 100, 200]; PASS

[2026-10-28 13:58:45 +05:30] User-authorized Study C resize. Read ladder.py step_studyc and launch log; exit 0: limit comes from --limit if given, otherwise config.studyc.limit. Actual ladder command uses --config reports/c3-part1/config.studyc.json with no CLI --limit; its studyc.limit=0 produced --limit 0 and 6720 positions. No pipeline code change needed. Will set active snapshot and main config studyc.limit=2437, preserving the same launch command. Selecting 2437 uses the same class-balanced positions() logic as Studies A/B, not a simple numeric-ID prefix.

[2026-10-28 13:59:45 +05:30] Authorized interruption: Stop-Process -Id 23996 (CPU supervisor only) and 5596 (CPU per-minute observer only), so queued hw cannot start and polling ends. Exact clean engine-stop command: ..\.venv\Scripts\python.exe reports/studyc_quit_pipe.py; exit=1; key output:
Worker 31924: writable pipe handle=188 access=0x120196
Worker 31924: writable pipe handle=192 access=0x120196
Worker 31924: writable pipe handle=488 access=0x120196
Worker 31924: writable pipe handle=492 access=0x120196
Worker 31924: writable pipe handle=712 access=0x120196
Traceback (most recent call last):
  File "C:\Users\HP\Desktop\LC0-B\leela-int8\reports\studyc_quit_pipe.py", line 50, in <module>
    assert len(handles) == 1, f'Expected sole engine stdin writer, found {len(handles)}; no writes performed'
           ^^^^^^^^^^^^^^^^^
AssertionError: Expected sole engine stdin writer, found 5; no writes performed
File: reports/logs/studyc_resize_stop.log. Source inspection eval/lc0uci.py showed stdin UCI pipe, no console; helper duplicates only the worker's sole writable pipe and sends stop/quit. Expected worker EOF after user-authorized cancellation is not a pipeline failure.

[2026-10-28 14:06:26 +05:30] User manually stopped Study C tree with taskkill /PID 22808 /T /F (reported child 8124 also ended). Read-only preflight command: nvidia-smi and Win32_Process inventory; exit 0: 48C, GPU 0%, memory 0MiB, no GPU processes and no python/lc0/trtexec jobs. Prior stop-helper BLOCKED superseded by explicit user continuation. Exact preparation command: ..\.venv\Scripts\python.exe reports/studyc_resize_prep.py; exit=0; key output:
BACKUP {"file": "fp16\\C200.lc0.log", "size": 21785955, "sha256": "e3085bdb81e7fe6aaa3571fe9c29541fdb566ba0998c9fba285d00fa4c32005c"}
BACKUP {"file": "fp16\\C800.lc0.log", "size": 9872869, "sha256": "49708498a3ab979a93be33a6900aa8651850ba3219818078efb5101f6ff19bd9"}
BACKUP {"file": "fp16\\study_c.jsonl", "size": 992829, "sha256": "e9e13cae30cb04b37415761979ee1d0f77f916ef61ec0bcca4f4fe0a807bc5f1"}
Diagnostic log backed up, not a JSONL results file: fp16\C200.lc0.log
Diagnostic log backed up, not a JSONL results file: fp16\C800.lc0.log
VALID FINAL JSON fp16\study_c.jsonl rows= 9429 ; no trimming
CONFIG ONLY: reports/c3-part1/config.studyc.json studyc.limit 0 -> 2437; main config.json unchanged; no pipeline source edits
BASELINE fp16 200ms: selected existing=2437/2437; all stored=6720; remaining=0
BASELINE fp16 800ms: selected existing=1027/2437; all stored=2709; remaining=1410
BASELINE s4 200ms: selected existing=0/2437; all stored=0; remaining=2437
BASELINE s4 800ms: selected existing=0/2437; all stored=0; remaining=2437
SELECTED: 2437 positions, exact match to Studies A/B class-balanced IDs; existing out-of-selection rows preserved
RESUME COMMAND: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\ladder.py studyc --config C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\config.studyc.json
PRODUCED reports\studyc-backup\2026-10-28T140625_+0530 reports/c3-part1/resize-baseline.json
File: reports/logs/studyc_resize_prep.log. Diagnostic lc0 logs backed up unchanged; only JSONL result tails validated as JSON.

[2026-10-28 14:08:00 +05:30] Helper syntax command: ..\.venv\Scripts\python.exe -m py_compile reports/studyc_resize_prep.py reports/studyc_resize_resume.py; exit 0. Exact background launch: Start-Process -FilePath 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' -ArgumentList @('-u','reports/studyc_resize_resume.py') -WorkingDirectory 'C:\Users\HP\Desktop\LC0-B\leela-int8' -WindowStyle Hidden -RedirectStandardOutput reports/logs/studyc_resize_controller.stdout.log -RedirectStandardError reports/logs/studyc_resize_controller.stderr.log -PassThru; launch exit 0, launcher PID=32040. Single authorized resume, no automatic retry; initial verification at 55 seconds, then no active-job polling in supervisor (waits for exits); hw follows only after Study C completion and cool/idle nvidia-smi preflight. Main chat checks at most each 20 minutes or on completion/failure; no per-minute observer. No pipeline code changes; reuse original controller definitions without executing its old main or rerunning a0/a.

[2026-10-28 14:08:00 +0530] resized b_studyc GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 14:08:00 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   42C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 42, 210, 0, 0
compute processes: none

[2026-10-28 14:08:00 +0530] User-authorized Study C resume after manual stop; same exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\ladder.py studyc --config C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\config.studyc.json; log appended=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_b_studyc.log; no automatic retry; hw remains queued. Backup and pre-existing counts: reports/c3-part1/resize-baseline.json

[2026-10-28 14:08:56 +0530] First-minute resume verification PASS; original byte prefixes retained, no duplicated keys, new rows restricted to the Studies A/B IDs; completed fp16 200ms skipped.
fp16 200ms: already done before resume=2437/2437; at check=2437/2437; remaining=0
fp16 800ms: already done before resume=1027/2437; at check=1093/2437; remaining=1344
s4 200ms: already done before resume=0/2437; at check=0/2437; remaining=2437
s4 800ms: already done before resume=0/2437; at check=0/2437; remaining=2437
Evidence reports/c3-part1/resize-one-minute.json
Startup/resume key output:

[2026-10-28 14:08:01 +0530] $ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\ladder.py studyc --config C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\config.studyc.json
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\eval\run_study.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --name fp16 --weights C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\studyc-work\models\fp16.pb.gz --backend onnx-trt --backend-opts optimize=6 --tbset C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\studyc-work\data\tbset.jsonl --split test --limit 2437 --budgets  --threads 0 --minibatch 256 --out-dir C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\studyc-work\results --movetimes 200,800
fp16: 2437 positions, budgets [], movetimes [200, 800]
  [fp16 C800] 25/1410  0.65s/item  eta 15.1 min
  [fp16 C800] 50/1410  0.71s/item  eta 16.1 min

[2026-10-28 15:01:32 +0530] Study C resized command finished; exit=0; command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\ladder.py studyc --config C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\config.studyc.json; output=results/studyc; reports/c3_studyc; key lines:
  [s4 C800] 2025/2437  0.66s/item  eta 4.5 min
  [s4 C800] 2050/2437  0.66s/item  eta 4.3 min
  [s4 C800] 2075/2437  0.66s/item  eta 4.0 min
  [s4 C800] 2100/2437  0.66s/item  eta 3.7 min
  [s4 C800] 2125/2437  0.65s/item  eta 3.4 min
  [s4 C800] 2150/2437  0.65s/item  eta 3.1 min
  [s4 C800] 2175/2437  0.65s/item  eta 2.8 min
  [s4 C800] 2200/2437  0.65s/item  eta 2.6 min
  [s4 C800] 2225/2437  0.65s/item  eta 2.3 min
  [s4 C800] 2250/2437  0.65s/item  eta 2.0 min
  [s4 C800] 2275/2437  0.65s/item  eta 1.8 min
  [s4 C800] 2300/2437  0.65s/item  eta 1.5 min
  [s4 C800] 2325/2437  0.66s/item  eta 1.2 min
  [s4 C800] 2350/2437  0.66s/item  eta 1.0 min
  [s4 C800] 2375/2437  0.66s/item  eta 0.7 min
  [s4 C800] 2400/2437  0.66s/item  eta 0.4 min
  [s4 C800] 2425/2437  0.66s/item  eta 0.1 min
  [s4 C800] 2437/2437  0.66s/item  eta 0.0 min

[2026-10-28 15:01:32 +0530] Study C completion count fp16 200ms: 2437/2437 selected positions; prior extra rows preserved

[2026-10-28 15:01:32 +0530] Study C completion count fp16 800ms: 2437/2437 selected positions; prior extra rows preserved

[2026-10-28 15:01:33 +0530] Study C completion count s4 200ms: 2437/2437 selected positions; prior extra rows preserved

[2026-10-28 15:01:33 +0530] Study C completion count s4 800ms: 2437/2437 selected positions; prior extra rows preserved

[2026-10-28 15:01:34 +0530] c_hw GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 15:01:33 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   68C    P4             23W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 68, 2520, 0, 0
compute processes: none

[2026-10-28 15:02:04 +0530] c_hw GPU preflight: nvidia-smi exit=0; nvidia-smi --query-gpu=temperature.gpu,clocks.sm,utilization.gpu,memory.used --format=csv,noheader,nounits exit=0; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader exit=0
Wed Oct 28 15:02:04 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 592.82                 Driver Version: 592.82         CUDA Version: 13.1     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   52C    P8              1W /  120W |       0MiB /   8188MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+

temperature C, SM clock MHz, utilization %, memory MiB: 52, 210, 0, 0
compute processes: none

[2026-10-28 15:02:04 +0530] Launching c_hw in background controller, exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3_hw_guard.py --config C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\config.hw.json; cwd=C:\Users\HP\Desktop\LC0-B\leela-int8; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_c_hw.log; result=reports/c3_hw; resume command=C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3_hw_guard.py --config C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\config.hw.json; no automatic resume

[2026-10-28 15:24:56 +0530] Finished c_hw; exact command: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe -u C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3_hw_guard.py --config C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\config.hw.json; exit=1; output=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\logs\c3_c_hw.log; result=reports/c3_hw; key output:
  batch   512        3138 nps
  search run 1: 4620 nps, 265902 nodes, GPU 18.194 mJ/node above idle, SM 2189 MHz (min 1905), 88 C max
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\bench\native.json
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\batch_sweep.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --backend onnx-trt --sizes 32,64,128,256 --model fp16=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\fp16.pb.gz:optimize=6 --model s4=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\s4.pb.gz:optimize=8 --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\batch_sweep
fp16       minibatch    32: 5449 nps, 15.148 mJ/node
fp16       minibatch    64: 5577 nps, 14.650 mJ/node
fp16       minibatch   128: 5417 nps, 15.323 mJ/node
fp16       minibatch   256: 5140 nps, 17.008 mJ/node
s4         minibatch    32: 7241 nps, 11.227 mJ/node
s4         minibatch    64: 7820 nps, 10.651 mJ/node
s4         minibatch   128: 7283 nps, 11.801 mJ/node
s4         minibatch   256: 6757 nps, 13.069 mJ/node
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\batch_sweep/sweep.csv
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\trt_layers.py build --trtexec C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\bt3_fp32.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16
C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe --onnx=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\bt3_fp32.onnx --fp16 --builderOptimizationLevel=5 --minShapes=/input/planes:4x112x8x8 --optShapes=/input/planes:256x112x8x8 --maxShapes=/input/planes:1024x112x8x8 --shapes=/input/planes:256x112x8x8 --profilingVerbosity=detailed --exportLayerInfo=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16_layers.json --exportProfile=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16_profile.json --exportTimes=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16_times.json --separateProfileRun --saveEngine=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16.engine --timingCacheFile=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\timing.cache --useCudaGraph --noDataTransfers
{"onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\c3-part1\\hw-work\\models\\bt3_fp32.onnx", "int8": false, "sparsity": false, "batch": 256, "returncode": 1, "qps": null, "gpu_ms_mean": null}
trtexec failed; see C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16_trtexec.log
step failed (1) after 0s: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\trt_layers.py build --trtexec C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\bt3_fp32.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16

[2026-10-28 15:24:57 +0530] BLOCKED; stopped on first failure; RuntimeError: c_hw exit 1:   batch   512        3138 nps
  search run 1: 4620 nps, 265902 nodes, GPU 18.194 mJ/node above idle, SM 2189 MHz (min 1905), 88 C max
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\bench\native.json
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\batch_sweep.py --lc0 C:/Users/HP/Desktop/LC0-B/tools/lc0/lc0.exe --backend onnx-trt --sizes 32,64,128,256 --model fp16=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\fp16.pb.gz:optimize=6 --model s4=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\s4.pb.gz:optimize=8 --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\batch_sweep
fp16       minibatch    32: 5449 nps, 15.148 mJ/node
fp16       minibatch    64: 5577 nps, 14.650 mJ/node
fp16       minibatch   128: 5417 nps, 15.323 mJ/node
fp16       minibatch   256: 5140 nps, 17.008 mJ/node
s4         minibatch    32: 7241 nps, 11.227 mJ/node
s4         minibatch    64: 7820 nps, 10.651 mJ/node
s4         minibatch   128: 7283 nps, 11.801 mJ/node
s4         minibatch   256: 6757 nps, 13.069 mJ/node
wrote C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\batch_sweep/sweep.csv
$ C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\trt_layers.py build --trtexec C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\bt3_fp32.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16
C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe --onnx=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\bt3_fp32.onnx --fp16 --builderOptimizationLevel=5 --minShapes=/input/planes:4x112x8x8 --optShapes=/input/planes:256x112x8x8 --maxShapes=/input/planes:1024x112x8x8 --shapes=/input/planes:256x112x8x8 --profilingVerbosity=detailed --exportLayerInfo=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16_layers.json --exportProfile=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16_profile.json --exportTimes=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16_times.json --separateProfileRun --saveEngine=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16.engine --timingCacheFile=C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\timing.cache --useCudaGraph --noDataTransfers
{"onnx": "C:\\Users\\HP\\Desktop\\LC0-B\\leela-int8\\reports\\c3-part1\\hw-work\\models\\bt3_fp32.onnx", "int8": false, "sparsity": false, "batch": 256, "returncode": 1, "qps": null, "gpu_ms_mean": null}
trtexec failed; see C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16_trtexec.log
step failed (1) after 0s: C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe C:\Users\HP\Desktop\LC0-B\leela-int8\hw\trt_layers.py build --trtexec C:/Users/HP/Desktop/LC0-B/tools/TensorRT-10.12.0.36/bin/trtexec.exe --onnx C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\models\bt3_fp32.onnx --out C:\Users\HP\Desktop\LC0-B\leela-int8\reports\c3-part1\hw-work\reports\trt\fp16

[2026-10-28 15:33:00 +05:30] Completion/failure review only (no retry/fix/job launch): read background-controller state and c3_c_hw.log after permitted 20-minute wait; controller exited 1 at 2026-10-28 15:24:57 +0530 and wrote BLOCKED. Resized Study C completed all 2437 selected positions for fp16/s4 at 200/800 ms. Hardware bench and batch sweep completed; first TRT fp16 build returned 1. Exact diagnostic commands: Get-Content reports/c3_hw/trt/fp16_trtexec.log -Encoding utf8 | Select-String Error/error/Unknown/failed; read controller completion/cool-down lines; list bench/sweep files; exit 0. No score or match; no C3-part1 checkpoint written because hw failed.
[2026-10-28 15:33:15 +05:30] Failure root cause, exact key line from reports/c3_hw/trt/fp16_trtexec.log: [10/28/2026-15:24:56] [E] Uncaught exception detected: Unable to open library: nvinfer_plugin_10.dll. TRT child exit=1; supervisor stopped at first failed child (no retries/alternative fixes). Completed: Study C fp16/s4 at 200/800ms each 2437/2437 selected positions (same A/B IDs); hardware bench fp16/s4/native and fp16/s4 batch sweep. Before hw, nvidia-smi at 15:01:34 printed 68C, 2520 MHz, utilization 0%, memory 0MiB; waited, then at 15:02:04 printed 52C, 210 MHz, utilization 0%, memory 0MiB and no compute processes before starting. Clock locking previously skipped for permission denial. Study C backup reports/studyc-backup/2026-10-28T140625_+0530; last JSONL line valid, zero lines removed. First-minute evidence reports/c3-part1/resize-one-minute.json: fp16 C200 before/after=2437/2437, fp16 C800 1027 -> 1093, s4 C200/C800 0 -> 0, all old prefixes retained, zero duplicate keys, 66 new selected keys. Current command only appends this evidence and concise STATUS rows, exit 0. No score, match, or C3-part1 completion checkpoint.


## 2026-10-29 — Shared-repository consolidation (user-authorized)

Authorization: adopt Person B conventions/pipeline/trimmed plan; create updated_plan.md and consolidation_context.md; consolidate both trees. No commit/push, teammate message, new chess inference, model rebuild, GPU benchmark or profiler retry.

Operations: retained the existing Git root/history; relocated original A directories/PDFs to archive/person-a-week1; promoted former LC0-B/leela-int8 contents to root; moved tools/tables to .runtime and the local environment to .venv; retained original edited B files under archive/person-b-import. Original activation/console scripts and pyvenv.cfg were copied to .runtime/imported-environment-scripts before launcher refresh. Per-file source/destination/bytes/SHA256: maintenance/consolidation-manifest.json. The independent Desktop/LC0-B checkout and external WSL runtime were untouched. No original file was deleted.

Code changes: ladder.load_config anchors relative paths to the config/work location and accepts UTF-8 BOM; default config is repository-relative. overnight config/work location follows the same root. Quantization, encoder, scorer, pruning, UCI and hardware numerical logic were unchanged. Exact entry-point diff: maintenance/consolidation-code.patch. Shared recipe matches the frozen run; Study C limit is 2437, matching the actually completed resized run rather than the stale base-config zero.

Documentation/metadata: current README/RUN_4060/AGENTS/STATUS, retained technical traps under docs/runtime_notes.md, updated plan with all retained deliverables and explicit F8/F10 omissions, consolidation guide, output-directory notes, observed Windows preparation lock, Git ignore/line-ending rules. Large artifacts stay local; maintenance/artifacts.py supports verified pack/restore and refuses different-file overwrite. artifacts/manifest.json inventories transferable research trees; no full artifact ZIP was created or uploaded.

Verification commands/results (all exit 0):
- .venv/Scripts/python.exe -B -m unittest discover -s tests -p test_repository.py -v: 6 tests passed (path portability/frozen recipe and artifact round-trip, conflict, traversal, tamper checks).
- .venv/Scripts/python.exe -B -m pip check: No broken requirements found.
- .venv/Scripts/python.exe -B ladder.py --help; overnight.py --dry-run: passed, no experiment launched.
- AST parse of 28 active Python files; config local path existence; activation/entry-point checks: passed.
- eval/score.py --tbset data/tbset.jsonl --results results --ref fp16 --models fp16,s1,s2,s3,s4,s4aa,s0,s1sp,swap_pol8,swap_val8 --out <OS TemporaryDirectory> --split test: exact main/hard JSON+Markdown and hard IDs (five outputs), no inference; maintenance/scoring-verification.json.
- Full SHA256 preservation audit: 10722 original files, 23406412244 bytes, zero final failures. Initial seven missing cache destinations were resolved by relocating reports/__pycache__; originals retained.
- maintenance/artifacts.py inventory plus verification: 328 artifacts, 8588237031 bytes, zero failures.
- Git-layout audit: all 217 original tracked A files other than revised root .gitignore have Git-visible archive counterparts; only two already-tracked historical arrays exceed 50 MB; no new model/tool binaries exposed.

Final verification: maintenance/consolidation-verification.json. Scientific state remains: main dense/sparse/swap accuracy complete; detailed profiler BLOCKED at nvinfer_plugin_10.dll loading; matches, final comparative/repeated hardware evidence, matched timed/hard reporting and final deliverables pending per updated_plan.md.


## 2026-10-29 — Publication authorization and preflight

User explicitly requested add/commit with message `consolidation 1 29th Oct`, push to GitHub, and initialize remote `anjan` and `ritwik` at the same version as `main`. A concise message is to be drafted, not sent.

Preflight commands (exit 0): `git fetch origin --prune`, `git branch -a -vv`, `git ls-remote --heads origin main anjan ritwik`. Remote main and both local branches started at 671d72e1ec6ff0eb1183335b874caef67a7d30fa; neither requested remote branch existed. No remote-main changes needed integration. Updated the current consolidation guide to record the authorized publication and teammate branch workflow. Existing scientific evidence and ignored local artifacts remain unchanged.

Publication target: one consolidation commit on main, fast-forward local anjan to it, create ritwik there, then a normal atomic push of main/anjan/ritwik. Git commit history and the remote branch refs provide the final publication evidence; this is the pre-commit authorization/preflight record.


## 2026-10-29 — Person A Run 1 A1

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A1`. Exit 0; verified. Output: {"roots": 11200, "cohort": 2437, "hard": 43, "cross_split_groups": 7, "affected_test_ids": [611, 627, 965]}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A2

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A2`. Exit 0; verified. Output: {"models": 10, "score_A_exact_match": true, "figure": "F1-ablation"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A3

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A3`. Exit 0; BLOCKED. Output: {"error": "fp16"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A3

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A3`. Exit 0; verified. Output: {"main_score_B_exact_match": true, "search_rows": 38, "hard_rows": 30, "figures": ["F2-nodes", "F3-node-equivalents", "S1-hard-lowbudget"]}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A4

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A4`. Exit 0; verified. Output: {"source_hashes_verified": true, "comparison_rows": 20, "figure": "F4-swaps"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A5

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A5`. Exit 0; BLOCKED. Output: {"error": ""}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 stopped at A5 verification gate

A1 verified 11200 roots, 2437 primary IDs and 43 hard IDs; seven cross-split symmetry groups affect measured IDs 611,627,965. A2 exactly reproduced all ten saved Study A rows; A3 exactly reproduced Study B after one permitted JSON budget-key representation typo retry (int keys normalized to strings), producing 38 main/supplemental search rows and 30 hard conditions. A4 verified saved swap/source hashes and exported 20 comparison rows. F1/F2/F3/F4 and the hard supplement were generated; final visual QA remains pending.

Command `.venv/Scripts/python.exe -B analysis/person_a/run1.py A5` exited 1. The check `np.all(inv>0) and np.allclose(s4_raw * smooth_inverse, s4_smoothed, rtol=1e-5, atol=1e-12)` failed using frozen `reports/C2-ln2-channel-maxima.npz` and current `models/s4.onnx`. No cause is asserted; the sequence stopped without investigating, altering raw statistics, relaxing tolerance or collecting activations. Detailed failure and frozen identities: analysis/person_a/run1/blocker-A5.json. A6–A10 were not executed.

All research artifacts matched the frozen manifest at run start (328 files). No engine inference, training, search, GPU benchmark, commit, push or teammate message was performed. Quantization/evaluation/tablebase logic and imported evidence remain unchanged. Root STATUS.md and the new run tracker record BLOCKED. The current AGENTS.md failure rule requires authorization before investigating/fixing this new consistency failure.


## 2026-10-29 — User-authorized A5 deferral and A6 resume

User explicitly deferred A5 to the end, requested a reminder before autonomous Run 2, and authorized the remaining independent Run 1 work from A6. Original A5 failure record remains unchanged; status is deferred, not resolved. Added analysis/person_a/BEFORE_RUN_2.md and a persistent tracker/status reminder. The runner allows only the explicit A5→A6 bypass; all later prerequisites remain verified gates. No model/scorer/protocol change.


## 2026-10-29 — Person A Run 1 A6

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A6`. Exit 0; verified. Output: {"mask_models": 2, "unique_matrices_each": 150, "reconstruction_rows": 150, "error_case_rows": 2706, "hardware": "WAIT R1/R2"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A7

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A7`. Exit 0; verified. Output: {"operations": 195, "fixed_weight_operations": 164, "dynamic_operations": 31, "macs_per_position": 4539245056, "arithmetic_ops_per_position": 9078490112, "active_graph_sha256": "937d5ac3d1ce9daafc7858f54166787924680c0c9c4aaab94d438402430db2b9", "geometry_source_sha256": "2dc17ea66e3db343532292a5f8f37d9daae6f387a510de8114cc3304d18e22d8", "geometry_proof": "all operator protobufs and integer shape constants identical; matrix dimensions checked", "graph_io": {"input": [{"name": "/input/planes", "shape": ["batch", 112, 8, 8]}], "output": [{"name": "/output/policy", "shape": ["batch", 1858]}, {"name": "/output/wdl", "shape": ["batch", 3]}, {"name": "/output/mlh", "shape": ["batch", 1]}]}, "s4_graph_targets": 164, "s4aa_graph_targets": 195, "executed_precision_and_measured_roofline": "WAIT R1; no peak/timing supplied"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A8

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A8`. Exit 0; verified. Output: {"timed_rows": 4, "timed_positions": 9748, "frontier_quality_rows": 8, "legal_openings": 50, "waiting": ["R1", "R2", "R4", "R5"], "R3": "final alignment only"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A9

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A9`. Exit 0; verified. Output: {"report": "deliverables/report/person_a_sections.md", "claim_rows": 9, "verified_primary_references": 7, "A5": "deferred; no activation claim", "final_shared_report": "WAIT systems evidence and final integration"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A10

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A10`. Exit 0; run1_complete_waiting_Ritwik. Output: {"checklist_rows": 25, "slides": "prepared outline", "demo": "prepared recording plan", "reproduction": "prepared FP16 + s4 + sparse-path procedure; not executed", "before_run2": "Address deferred A5 first; then validate Ritwik inputs", "final_delivery": "WAIT A5 handling and R1\u2013R5 integration"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A9

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A9`. Exit 0; verified. Output: {"report": "deliverables/report/person_a_sections.md", "claim_rows": 9, "verified_primary_references": 7, "A5": "deferred; no activation claim", "final_shared_report": "WAIT systems evidence and final integration"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 independent block closure

User-authorized A6–A10 continuation on anjan completed. A5 remains explicitly deferred; analysis/person_a/BEFORE_RUN_2.md, readiness.py, STATUS.md and AGENTS.md require a reminder before Run 2. A6 verified both 2:4 sources (150 matrices each), 150 reconstruction rows and 2706 saved sparse error-case rows. A7 verified all 195 matrix operations (164 fixed, 31 dynamic), graph/shape identities and 4539245056 MACs/position; actual precision/timings/peaks remain R1. A8 exported four matched timed summaries, 9748 position-condition records, eight frontier quality rows and 50 legal existing openings. A9 wrote the evidence-linked report and seven checked primary-reference entries (Haque exact historical counts excluded pending source-table verification). A10 prepared 25 retained/omitted checklist rows, slide/demo and FP16+s4+sparse reproduction plans.

Verification commands/results: `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_person_a_run1.py -v` exited 0: 7 tests passed, including actual frozen-score regression and deferral/readiness guards. Visual view_image review passed F1/F2/F3/F4/hard supplement; PNG/PDF/SVG exports checked. Frozen-source SHA256 audit passed all 350 files with zero mismatches; row counts and finite numerical values checked. `.venv/Scripts/python.exe -B analysis/person_a/readiness.py` exited 0, printing the A5 reminder and not-ready state. See analysis/person_a/run1/verification.json, visual_review.json and progress.json.

No new engine inference, training, search, GPU benchmark, protocol/model/scorer change, commit, push or teammate message. A5 failure history and all original research evidence remain preserved. Full project completion, final systems findings, fresh experimental reproduction, final deck and recording are not claimed.


## 2026-10-29 — User-authorized A5 resolution plan and provenance diagnosis

User requested a plan and implementation for A5 on anjan. Plan: analysis/person_a/A5_resolution_plan.md. Read-only inspection and `.venv/Scripts/python.exe -B analysis/person_a/smoothquant_diagnostic.py diagnose` exited 0. Original NPZ belongs to C1 model SHA574f555e… (alpha0.5, percentile99.99), verified against collection LOG and backup manifest; all 768 channels exactly match its multiplier. Current model SHA24fd9a11… uses alpha0.7/percentile99.999; wrong pairing fails all 768 channels. Original data/model/failure evidence preserved. No scientific protocol or quantization/scorer changes.

Explicit bounded diagnostic collection uses the unchanged selected model and 512 unchanged calibration inputs on CPU, batch32, with new outputs under analysis/person_a/a5/. `.venv/Scripts/python.exe -B analysis/person_a/smoothquant_diagnostic.py collect` first exited1 at the new analysis shape assertion, before saving statistics; BLOCKED record retained at a5/collect-failure.json. The new collector assumed [batch,64,768], whereas read-only ONNX value_info confirms this export uses flattened [batch*64,768]. One obvious shape-assertion/reduction correction, matching the imported collector's reduction over every non-channel axis, is applied for the permitted single retry. This is an analysis implementation correction, not a model/protocol variant.


## 2026-10-29 — Person A Run 1 A5

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A5`. Exit 0; verified. Output: {"groups": 101, "groups_improved": 100, "groups_not_improved": 1, "channels": 768, "groups_not_improved_details": [{"tensor": "/attn_body/embedding/reshape", "ratio_before": 1.0, "ratio_after": 1.2492252983716854, "after_over_before": 1.2492252983716854, "improved": false, "consumers": "/attn_body/embedding/preprocess/matmul"}], "saved_mul_pair_agrees_with_graph": true, "selected_recipe": {"smoothquant": 0.7, "percentile": 99.999, "method": "percentile", "granularity": "per-channel", "n_calib": 512}, "measured_example": {"s4_raw": {"max": 53.507041931152344, "median": 7.907499093562365e-05, "max_over_median": 676662.0052440269, "live_channels": 768}, "s4_smoothed": {"max": 2.270639419555664, "median": 0.0020073330961167812, "max_over_median": 1131.1722124983905, "live_channels": 768}}, "pair_check": {"agrees": true, "channels": 768, "failed_channels": 0, "max_absolute_error": 0.0, "max_relative_error": 0.0, "rtol": 1e-05, "atol": 1e-12}, "provenance": "analysis/person_a/a5/provenance.json", "collection": "analysis/person_a/a5/collection.json", "diagnosis": "Historical alpha-0.5 arrays were paired with the selected alpha-0.7 graph; historical pair verifies exactly against its preserved graph. New selected-model measurements now verify independently.", "ratio_definitions": {"groups": "original-build amax / max(median(all channel amax),1e-12); after derived from smoothing", "saved_example": "selected s4 alpha=0.7, CPU, 512 calibration inputs; channel amax over positions/tokens before/after one Mul; median over all 768 channels"}, "collection_elapsed_seconds": 8.22917010000674, "quantized_upstream_differs_from_original": true, "new_chess_search_or_gpu_performance_measurements": false}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A9

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A9`. Exit 0; verified. Output: {"report": "deliverables/report/person_a_sections.md", "claim_rows": 9, "verified_primary_references": 7, "A5": "verified selected-model F12", "final_shared_report": "WAIT systems evidence and final integration"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — Person A Run 1 A10

Authorization: full sequential Run 1 on anjan. Command: `.venv/Scripts/python.exe -B analysis/person_a/run1.py A10`. Exit 0; run1_complete_waiting_Ritwik. Output: {"checklist_rows": 25, "slides": "prepared outline", "demo": "prepared recording plan", "reproduction": "prepared FP16 + s4 + sparse-path procedure; not executed", "before_run2": "A5 verified; validate Ritwik inputs", "final_delivery": "WAIT R1\u2013R5 integration"}. Original evidence preserved; no engine inference/training/search or GPU benchmarking.


## 2026-10-29 — A5 resolved and F12 verified on anjan

The permitted corrected `.venv/Scripts/python.exe -B analysis/person_a/smoothquant_diagnostic.py collect` retry exited0: CPUExecutionProvider only, ORT1.31.1, batch32, 512 unchanged calibration inputs; collection loop8.2291701s (not a latency benchmark). Both sides of /encoder14/ln2/smooth were fetched in each pass. All 768 maxima pass original rtol1e-5/atol1e-12; per-batch and maxima absolute differences are zero. All source hashes checked before/after collection. New arrays/metadata: analysis/person_a/a5/current-channel-maxima.npz and collection.json. A later identical collect command exited0 and reused verified evidence without inference; resume guard verified. The first failed shape assertion remains preserved in collect-failure.json.

`.venv/Scripts/python.exe -B analysis/person_a/run1.py A5` exited0, verified, using the new final-model arrays. Analysis diff: pair saved statistics with their correct source model; require source/output identities and exact multiplier agreement; retain tolerance; separate original-build derived statistics from measured final-model activations. No quantization/evaluation/tablebase code, model, calibration, selected recipe or scientific protocol change. Across101 groups100 ratios improve,1 worsens (embedding/reshape1->1.2492253). Final measured LN ratio676662.0052->1131.1722. These are activation range statistics, not WDL, accuracy, speed or strength measurements. CSVs, findings and F12 PNG/PDF/SVG exported; final visual view_image inspection passed, labels/captions legible without clipping/overlap.

A9 and A10 commands were rerun solely to refresh linked report/delivery preparation after A5 closure, each exit0; no other experiment step was rerun. Readiness command `.venv/Scripts/python.exe -B analysis/person_a/readiness.py` exited0: A5 verified, reminder false, Run2 readiness false due to R1-R5 handoff review (R3 final alignment). Updated roadmap2.2, execution handoff, report/claim register, checklist, slides/demo/reproduction preparation, STATUS/README/context and agent preflight. Prior failure and original Run1 verification/visual/document/output manifests remain unchanged as historical evidence.

Verification: `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_person_a_run1.py -v` exited0,11 tests passed, including actual original-score regression and new wrong-model/exact-multiplier guards. The read-only Python closure audit exited0: all350 frozen inputs (8588424153bytes) unchanged, original failure/prior verification files unchanged in Git, past LOG content is an unchanged prefix, five analysis/test files parse,36 local document links resolve,101 group/768 channel CSV rows agree, final PNG/PDF/SVG exports pass structural checks and five prior figure hashes remain unchanged. `git diff --check` exited0. See analysis/person_a/a5/closure.json, visual_review.json, document_verification.json and current output_manifest.json; original run1/verification.json describes the earlier deferred checkpoint.

A5/F12 is complete. No model rebuilding/recalibration, chess/search/GPU performance experiment, Run2 execution, commit, push or teammate message. Ritwik-dependent final systems/results/delivery/reproduction remain pending.


## 2026-10-30 — New normal autonomous Run 1: takeover preparation

Authorization: user accepted five additional runs covering remaining A+B work and explicitly started only the new normal Run1. Work remained on anjan at unchanged HEAD7f9bacc. Prior uncommitted A5 work was preserved. No new commit/push or teammate message. The new five-run sequence replaces the external Ritwik wait; the old A final-integration readiness remains a different gate. See docs/takeover_runs.md, updated_plan.md2.3 and reports/takeover/progress.json.

Preservation/CPU preflight commands exited0: Python source snapshot/check verified all350 original files (8588424153bytes), recorded eight prior A5/config/manifest identities and starting Git status; read-only volume/memory/power/file-version observations; `.venv/Scripts/python.exe -B -m execution.prepare` verified actual x64 PE metadata and child PATH membership without loading an engine/DLL. TensorRT lib and lc0 dependency directories are added only to a future child environment. Original SDK plugin is present; actual GPU loader validation remains pending. Observed RAM33595191296bytes, approximately507GiB disk free, normal-run power scheme Balanced; null native file-version fields retained, not inferred. No power/PATH setting changed.

Added execution/ wrappers and execution/protocol.json. Imported ladder/common/quant/eval/hw code, model bytes, calibration, scorer and cohorts are unchanged. Procedural diff: docs/takeover_protocol_note.md. New guards reject incomplete benchmark/energy data and incompatible or corrupt match resumes; imported Game.play/clocks/adjudication stay in use. Atomic game+PGN envelopes rebuild interrupted aggregate exports. Imported summary remains traceable; degenerate/clipped intervals are not reported as reliable. Sequential attempts preserve raw logs/engines/trace identities, resource observations and failures. Only the exact known initial plugin-open failure may defer standalone profiling while independent lc0 work continues; required retained profiling deliverables stay pending.

Offline review tightened raw-artifact hashing and launch/monitor exception recording, then added the explicit safe --plan alias. The initial CPU preparation draft is preserved under run1/initial-cpu-draft; final run2_jobs.json preparation revision2 is the current freeze. This occurred before any GPU execution. Final `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_*.py -v` exited0:40 tests passed (17 existing +23 takeover safeguards, no skips), including original score regression, fake-command fail/skip/resume/launch-error tests, atomic game recovery/settings/PGN/CI checks, original clock behavior, synthetic external-resource flags, actual CPU-only Windows counters and PE header reads. Toy failures were expected isolated unit fixtures in OS temporary directories, not GPU/pipeline attempts.

`.venv/Scripts/python.exe -B -m execution.run_jobs --plan` exited0:45 planned jobs,0 GPU workloads started. Final manifest has69 verified execution/tool/model source identities,6 model profile jobs,1 probe,1 three-microbenchmark ceiling job,8 lc0 captures,28 benchmark trials and1 two-game pilot. Five headline trials each for FP16/s4; three each for the other six models. Common search minibatch64, imported benchmark positions/default threads, four NN batches and explicit warmup/idle/condition rules are recorded in protocol.json. Production matches are not in new Run2.

Final CPU closure audit exited0: original350 source files and eight prior records unchanged; all69 execution inputs verify;9 Python files parse;34 local documentation links resolve; command DAG/counts validate; no reports/takeover/run2 experiment directory exists; exclusive template remains all-false; HEAD/branch unchanged; prior LOG prefix preserved; git diff --check exited0. See reports/takeover/run1/verification.json, runtime_preflight.json, runtime_versions.json and current output_manifest.json. Existing A5/source manifests remain historical verification records.

New Run1 is complete as preparation only. No GPU engine/profiler/benchmark/match/model inference, app termination, global PATH/power change, training/recalibration or source scientific protocol alteration ran. New exclusive Run2 awaits explicit start after save/AC/quiet/power/cooling preparation. Provisional estimate3–7hours; reserve up to8hours for cold build uncertainty. Repeat the preparation reminder and update the duration before every future exclusive run.
