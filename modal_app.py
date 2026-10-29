"""Run the accuracy studies (A and B) on Modal GPUs, in parallel shards, so
the RTX 4060 stays free for timing. NOT TESTED (no Modal account where this
was written): treat the first run as a smoke test with --limit.

Only fixed-node accuracy belongs here. Every speed, energy, Study C and
match number must come from the 4060, or the numbers are not comparable.
Use an Ada GPU (L4, sm_89, same architecture as the 4060) so TensorRT's
INT8 kernels are the same family; tiny numeric differences remain, so run
FP16 and every INT8 model on Modal, never mix machines within one table.

One-time:
    pip install modal && modal setup
    modal volume create leela-int8
    modal volume put leela-int8 data/tbset.jsonl /data/tbset.jsonl
    modal volume put leela-int8 models/fp16.pb.gz /models/fp16.pb.gz     # and s1..s4, s4aa, s0, s1sp, swap_*
Run (8 shards per model, all models in parallel):
    modal run modal_app.py --models fp16,s1,s2,s3,s4,s4aa --budgets 0,100,400,800,1600 --shards 8
    modal run modal_app.py --models fp16 --limit 50 --shards 1          # smoke test first
Fetch:
    modal volume get leela-int8 /results ./results_modal
then score with: python eval/score.py --results results_modal/results --ref fp16 --models ...
Each shard writes results/<model>/shard<i>/study_*.jsonl; merge_shards() below
(called at the end of `modal run`) concatenates them into results/<model>/.
"""
from pathlib import Path

import modal

ORT = "1.22.0"            # same minor as the Windows package's 1.22.1 (trap 3: <= 1.26)
TRT = "10.12.0.36"        # same TensorRT as the Windows package
GPU = "L4"

app = modal.App("leela-int8")
vol = modal.Volume.from_name("leela-int8", create_if_missing=True)
REPO = Path(__file__).resolve().parent

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04", add_python="3.11")
    .apt_install("git", "ninja-build", "pkg-config", "zlib1g-dev", "wget", "g++")
    .pip_install("meson==1.5.2", "numpy", "onnx", "python-chess", f"tensorrt-cu12-libs=={TRT}")
    .run_commands(
        f"wget -q https://github.com/microsoft/onnxruntime/releases/download/v{ORT}/"
        f"onnxruntime-linux-x64-gpu-{ORT}.tgz -O /tmp/ort.tgz",
        "mkdir -p /opt && tar xzf /tmp/ort.tgz -C /opt && mv /opt/onnxruntime-linux-x64-gpu-* /opt/ort",
        "git clone --depth 1 --branch v0.33.0-rc0 https://github.com/LeelaChessZero/lc0.git /opt/lc0-src",
        "cd /opt/lc0-src && meson setup build --buildtype=release -Dgtest=false -Dblas=false "
        "-Dopenblas=false -Donnx_libdir=/opt/ort/lib -Donnx_include=/opt/ort/include "
        "&& ninja -C build lc0",
        "mkdir -p /opt/lc0 && cp /opt/lc0-src/build/lc0 /opt/lc0/",
    )
    .env({"LD_LIBRARY_PATH": "/opt/ort/lib:/usr/local/lib/python3.11/site-packages/tensorrt_libs:"
                             "/usr/local/cuda/lib64"})
    .add_local_dir(str(REPO), "/root/leela-int8", ignore=["models", "results", "reports", "data", "*.zip"])
)

FP16_OPTS, INT8_OPTS = "optimize=6", "optimize=8"


@app.function(image=image, gpu=GPU, volumes={"/vol": vol}, timeout=24 * 3600)
def study_shard(model: str, budgets: str, split: str, limit: int, shard: int, nshards: int,
                threads: int = 1, minibatch: int = 256):
    import subprocess
    import sys
    weights = f"/vol/models/{model}.pb.gz"
    out = f"/vol/results/{model}/shard{shard}"
    opts = FP16_OPTS if model == "fp16" else INT8_OPTS
    cmd = [sys.executable, "/root/leela-int8/eval/run_study.py", "--lc0", "/opt/lc0/lc0",
           "--name", ".", "--weights", weights, "--backend", "onnx-trt", "--backend-opts", opts,
           "--tbset", "/vol/data/tbset.jsonl", "--split", split, "--limit", str(limit),
           "--budgets", budgets, "--threads", str(threads), "--minibatch", str(minibatch),
           "--shard", f"{shard}/{nshards}", "--out-dir", out]
    print(" ".join(cmd), flush=True)
    # Commit partial results every so often so a preempted shard resumes.
    p = subprocess.Popen(cmd)
    import time
    while p.poll() is None:
        time.sleep(300)
        vol.commit()
    vol.commit()
    if p.returncode:
        raise RuntimeError(f"{model} shard {shard} failed ({p.returncode})")
    return f"{model} shard {shard} done"


@app.function(image=image, volumes={"/vol": vol}, timeout=3600)
def merge_shards(model: str):
    from pathlib import Path as P
    vol.reload()
    base = P(f"/vol/results/{model}")
    for study in ("study_a.jsonl", "study_b.jsonl"):
        lines = []
        for f in sorted(base.glob(f"shard*/{study}")):
            lines += [ln for ln in f.read_text().splitlines() if ln.strip()]
        if lines:
            (base / study).write_text("\n".join(lines) + "\n")
    vol.commit()
    return model


@app.local_entrypoint()
def main(models: str = "fp16,s1,s2,s3,s4,s4aa", budgets: str = "0,100,400,800,1600",
         split: str = "test", limit: int = 0, shards: int = 8):
    jobs = [(m, budgets, split, limit, i, shards) for m in models.split(",") for i in range(shards)]
    for r in study_shard.starmap(jobs, return_exceptions=True):
        print(r)
    for m in merge_shards.map(models.split(",")):
        print("merged", m)
