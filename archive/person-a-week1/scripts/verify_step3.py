"""Verify the installed tools with synthetic GPU work, without exporting BT3."""

import gc
import hashlib
import importlib.metadata
import inspect
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "lc0-int8"
BUILD = RUNTIME / "build/lc0-tools"
COMMIT = "9f45ea446baf9ce55e299250cde3053b7e93a035"


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def ort_gpu_check(model, inputs, expected, provider, scratch):
    import numpy as np
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.enable_profiling = True
    options.profile_file_prefix = str(scratch / provider)
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
    options.log_severity_level = 3
    providers = [provider, "CPUExecutionProvider"]
    if provider == "TensorrtExecutionProvider":
        providers = [(provider, {"trt_max_workspace_size": 64 * 1024 * 1024,
                                  "trt_min_subgraph_size": 1}),
                     "CUDAExecutionProvider", "CPUExecutionProvider"]
    session = ort.InferenceSession(model.SerializeToString(), sess_options=options, providers=providers)
    if provider not in session.get_providers():
        raise RuntimeError(f"Requested provider failed to initialize: {provider}")
    output = session.run(None, {"x": inputs})[0]
    np.testing.assert_allclose(output, expected, atol=1e-4, rtol=1e-4)
    profile_path = Path(session.end_profiling())
    events = json.loads(profile_path.read_text())
    executed = sorted({e.get("args", {}).get("provider") for e in events
                       if e.get("args", {}).get("provider")})
    if provider not in executed:
        raise RuntimeError(f"No evidence of execution on {provider}: {executed}")
    result = {"requested_provider": provider, "executed_providers": executed,
              "max_abs_error": float(np.max(np.abs(output - expected)))}
    del session
    gc.collect()
    return result


def main():
    import numpy as np
    import torch
    import onnx
    import onnxruntime as ort
    import tensorrt as trt
    from onnx import TensorProto, helper, numpy_helper
    import modelopt.onnx.quantization as moq

    versions = {name: importlib.metadata.version(name) for name in [
        "pip", "meson", "numpy", "torch", "onnx", "onnxruntime-gpu", "tensorrt-cu12",
        "nvidia-modelopt", "matplotlib", "python-chess", "cupy-cuda12x", "onnx-graphsurgeon"]}
    print("Imported pinned packages", json.dumps(versions), flush=True)
    assert ort.__version__ == "1.22.0"
    assert trt.__version__.startswith("10.9.")
    assert callable(moq.quantize)
    assert torch.cuda.is_available(), "PyTorch cannot access CUDA"
    values = torch.arange(16, dtype=torch.float32, device="cuda").reshape(4, 4)
    np.testing.assert_allclose((values @ values.T).cpu().numpy(),
                               np.arange(16, dtype=np.float32).reshape(4, 4) @
                               np.arange(16, dtype=np.float32).reshape(4, 4).T)
    print("PyTorch CUDA calculation passed", flush=True)
    ort.preload_dlls()
    inputs = np.linspace(-1, 1, 16, dtype=np.float32).reshape(1, 16)
    weights = np.arange(256, dtype=np.float32).reshape(16, 16) / 256
    graph = helper.make_graph(
        [helper.make_node("MatMul", ["x", "w"], ["y"])], "step3_toolchain_smoke",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 16])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 16])],
        [numpy_helper.from_array(weights, name="w")])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 10
    onnx.checker.check_model(model)
    with tempfile.TemporaryDirectory(prefix="lc0-step3-verify-") as directory:
        scratch = Path(directory)
        gpu_checks = [ort_gpu_check(model, inputs, inputs @ weights, provider, scratch)
                      for provider in ["CUDAExecutionProvider", "TensorrtExecutionProvider"]]
    print("ONNX Runtime CUDA and TensorRT execution passed", flush=True)
    checkpoint = json.loads((PROJECT / "models/source/checkpoint.json").read_text())
    weights_path = PROJECT / checkpoint["relative_path"]
    digest = hashlib.sha256()
    with weights_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    assert digest.hexdigest() == checkpoint["sha256_compressed"]
    commit = run("git", "-C", str(RUNTIME / "source/lc0"), "rev-parse", "HEAD")
    assert commit == COMMIT
    metadata = run(str(BUILD / "lc0"), "describenet", "--weights=" + str(weights_path))
    print(metadata, flush=True)
    metadata_sections = {}
    current_section = None
    for line in metadata.splitlines():
        if line in {"General", "Format", "Training Parameters", "Weights"}:
            current_section = line
            metadata_sections[current_section] = {}
        elif current_section and ":" in line:
            key, value = line.split(":", 1)
            metadata_sections[current_section][key.strip()] = value.strip()
    assert metadata_sections["Format"]["Input"] == "INPUT_CLASSICAL_112_PLANE"
    assert metadata_sections["Format"]["Value"] == "VALUE_WDL"
    for field, value in {"Encoders": "15", "Encoder heads": "24", "Embedding size": "768"}.items():
        assert metadata_sections["Weights"][field] == value
    export_help = run(str(BUILD / "lc0"), "leela2onnx", "--help")
    for flag in ["onnx2pytorch", "onnx-data-type", "onnx-opset"]:
        assert flag in export_help, f"Missing exporter capability: {flag}"
    wrapper_help = run(str(BUILD / "lc0"), "onnx2leela", "--help")
    assert "input-format" in wrapper_help
    sys.path.insert(0, str(BUILD))
    import backends
    binding_names = sorted(name for name in dir(backends) if not name.startswith("_"))
    assert "Weights" in binding_names, "Missing lc0 Weights binding"
    result = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "python": platform.python_version(),
        "python_executable": sys.executable, "runtime_root": str(RUNTIME),
        "versions": versions, "torch_cuda_runtime": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
        "nvidia_smi": run("/usr/lib/wsl/lib/nvidia-smi",
                           "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"),
        "pytorch_cuda_calculation": "passed",
        "onnxruntime_gpu_checks": gpu_checks,
        "synthetic_graph": {"operator": "MatMul", "opset": 17, "ir_version": 10,
                            "input_shape": [1, 16], "weights_shape": [16, 16]},
        "modelopt_quantize_signature": str(inspect.signature(moq.quantize)),
        "checkpoint_sha256_rechecked": digest.hexdigest(),
        "lc0_commit": commit,
        "lc0_version_banner": subprocess.run([str(BUILD / "lc0"), "describenet", "--help"],
                                            check=True, capture_output=True, text=True).stderr.strip(),
        "lc0_build_scope": "Eigen CPU reference + export/metadata tools + Python bindings; no GPU engine backend",
        "checkpoint_metadata": metadata_sections, "checkpoint_metadata_text": metadata,
        "lc0_python_bindings": binding_names,
        "pip_check": run(sys.executable, "-m", "pip", "check"),
        "system_packages": run("dpkg-query", "-W", "-f=${Package}\t${Version}\n",
                               "build-essential", "python3-dev", "python3-venv", "cmake", "ninja-build",
                               "pkg-config", "zlib1g-dev", "libabsl-dev", "libeigen3-dev"),
        "scope_limit": "Synthetic toolchain checks only; BT3 export and numerical parity remain later steps",
    }
    output = PROJECT / "environment/step3-verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    lock = run(sys.executable, "-m", "pip", "freeze", "--all")
    (PROJECT / "requirements/step3.lock").write_text(lock + "\n")
    print(f"Verified report: {output}", flush=True)


if __name__ == "__main__":
    main()
