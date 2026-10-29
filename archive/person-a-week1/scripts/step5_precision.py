"""Inspect and trace actual CUDA/TensorRT kernels for the two baselines."""

import gc
import json
from collections import Counter

import numpy as np

import export_step5 as common
from step5_engine import Engine, PROJECT, WORK, prerequisites, progress


def kernel_summary(path):
    trace = json.loads(path.read_text())
    return Counter(e["name"] for e in trace["traceEvents"] if e.get("cat") == "kernel")


def main():
    prerequisites("5D")
    import torch
    import onnxruntime as ort
    ort.preload_dlls()
    assert ort.__version__ == "1.22.0"
    definitions = json.loads((PROJECT / "environment/step5-baselines.json").read_text())
    engine_record = json.loads((PROJECT / "environment/step5-engine.json").read_text())
    key = engine_record["engine_sha256"][:16]
    indices = [0, 8, 16, 24, 31, 32, 48, 56]
    with np.load(PROJECT / "data/pilot/inputs.npz", allow_pickle=False) as data:
        planes = data["planes"][indices]
    rows = [json.loads(line) for line in (PROJECT / "data/pilot/positions.jsonl").read_text().splitlines()]
    records = [rows[i] for i in indices]
    old = json.loads((PROJECT / "environment/step5-verification.json").read_text())
    reference_path = PROJECT / "data/pilot/onnx_reference.npz"
    assert common.sha256(reference_path) == old["outputs_sha256"]
    with np.load(reference_path, allow_pickle=False) as saved:
        native = [saved["native_" + name][indices] for name in ["logits", "wdl", "moves_left"]]
    gates = json.loads((PROJECT / "environment/step5-tolerances.json").read_text())["gates"]
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.log_severity_level = 3
    options.enable_profiling = True
    options.profile_file_prefix = str(WORK / ("r32-ort-provider-" + key))
    session = ort.InferenceSession(str(PROJECT / definitions["baselines"]["R32_CUDA"]["graph"]),
        sess_options=options, providers=[("CUDAExecutionProvider", {"use_tf32": "0",
            "cudnn_conv_use_max_workspace": "0"}), "CPUExecutionProvider"])
    session.disable_fallback()
    provider_options = session.get_provider_options()
    assert provider_options["CUDAExecutionProvider"]["use_tf32"] == "0"
    session.run(common.OUTPUTS, {"/input/planes": planes})
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
                                             torch.profiler.ProfilerActivity.CUDA]) as profiler:
        with torch.profiler.record_function("R32_CUDA_tf32_disabled"):
            r32 = session.run(common.OUTPUTS, {"/input/planes": planes})
    r32_trace = WORK / f"r32-kernels-{key}.json"
    profiler.export_chrome_trace(str(r32_trace))
    r32_kernels = kernel_summary(r32_trace)
    sgemm = {name: count for name, count in r32_kernels.items() if "sgemm" in name.lower()}
    assert sgemm, "No executed FP32 SGEMM kernels captured"
    assert not any("xmma" in name.lower() or "tf32" in name.lower() for name in r32_kernels), "Unexpected tensor-matrix kernels in strict FP32 trace"
    f32_check = common.compare(records, native, r32, gates["f32"])
    provider_profile = __import__("pathlib").Path(session.end_profiling())
    provider_events = json.loads(provider_profile.read_text())
    providers = Counter(e.get("args", {}).get("provider") for e in provider_events if e.get("args", {}).get("provider"))
    assert providers["CUDAExecutionProvider"] > 0
    cpu_ops = {e.get("args", {}).get("op_name") for e in provider_events
               if e.get("args", {}).get("provider") == "CPUExecutionProvider"}
    assert cpu_ops <= {"Shape", "Gather", "Slice", "Concat", "Reshape", "Cast", "Unsqueeze", "Squeeze"}, cpu_ops
    del session
    gc.collect()
    torch.cuda.empty_cache()
    print("R32_CUDA: executed SGEMM kernels, TF32 off, native numerical parity passed", flush=True)

    engine = Engine()
    engine.run(planes[:1])
    engine.run(planes)
    inspector = engine.engine.create_engine_inspector()
    inspector.execution_context = engine.context
    inspector_path = WORK / f"engine-inspector-{key}.json"
    inspector_path.write_text(inspector.get_engine_information(engine.trt.LayerInformationFormat.JSON))
    layers = json.loads(inspector_path.read_text())["Layers"]
    gemm_layers = [layer for layer in layers if layer.get("LayerType") == "gemm"]
    assert gemm_layers
    for layer in gemm_layers:
        types = [tensor.get("Format/Datatype", "").lower() for tensor in layer.get("Inputs", [])]
        # A cast-around-GEMM can expose FP32 interfaces while the fused tactic
        # still multiplies FP16 operands. Require typed FP16 tactic evidence
        # whenever the visible interface alone does not establish this.
        assert all("half" in dtype or "fp16" in dtype for dtype in types) or "f16f16" in layer.get("TacticName", ""), layer
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
                                             torch.profiler.ProfilerActivity.CUDA]) as profiler:
        with torch.profiler.record_function("F16_TRT_preserved_engine"):
            engine.run(planes[:1])
            engine.run(planes)
    f16_trace = WORK / f"f16-kernels-{key}.json"
    profiler.export_chrome_trace(str(f16_trace))
    f16_kernels = kernel_summary(f16_trace)
    tensor_kernels = {name: count for name, count in f16_kernels.items()
                      if "xmma_gemm_f16f16" in name and "tensor16x8x16" in name}
    assert tensor_kernels, "No executed FP16 Tensor Core GEMM kernels captured"
    assert not any("sgemm" in name.lower() or "tf32" in name.lower() for name in f16_kernels)
    settings = engine.record["settings"]
    assert not settings["tf32"] and settings["matrix_precision"] == "float16"
    assert settings["obey_precision_constraints"] or settings.get("strongly_typed")
    record = {"verified_at_utc": common.now(), "status": "passed",
              "R32_CUDA": {"graph_sha256": definitions["baselines"]["R32_CUDA"]["graph_sha256"],
                           "provider_options": provider_options, "tf32": False,
                           "executed_sgemm_kernels": sgemm, "all_kernel_counts": dict(r32_kernels),
                           "native_parity_summary": f32_check["summary"],
                           "provider_events": dict(providers), "cpu_ops": sorted(cpu_ops)},
              "F16_TRT": {"engine_sha256": engine.record["engine_sha256"], "tf32": False,
                          "constrained_matrix_layers": len(engine.record["matrix_precision_constraints"]),
                          "inspected_gemm_layers": len(gemm_layers),
                          "gemm_input_types": dict(Counter(t.get("Format/Datatype", "") for l in gemm_layers for t in l.get("Inputs", []))),
                          "gemm_output_types": dict(Counter(t.get("Format/Datatype", "") for l in gemm_layers for t in l.get("Outputs", []))),
                          "executed_fp16_tensor_core_kernels": tensor_kernels,
                          "all_kernel_counts": dict(f16_kernels),
                          "inspector_layer_types": dict(Counter(layer["LayerType"] for layer in layers)),
                          "normalization_fp32_compute_layers": len(engine.record["normalization_fp32_compute"]),
                          "provider_fallback": "none: direct TensorRT runtime has no CUDA/CPU provider fallback",
                          "accumulation_request": settings.get("accumulation_request", "native"),
                          "accumulation": "Global cast-around-GEMM request for FP32 accumulation, with actual FP16 input Tensor Core tactics traced" if settings.get("strongly_typed") else "Observed tactics include FP16 accumulation; FP32 accumulation is allowed but was not forced or claimed",
                          "coverage_limit": "Dynamic trace proves executed named FP16 tensor16x8x16 GEMMs; not a hardware-counter utilization measurement or a mapping of every fused operation to machine instructions"},
              "artifacts": [{"path": str(path), "sha256": common.sha256(path)} for path in
                            [r32_trace, f16_trace, inspector_path, provider_profile]],
              "profiling": "PyTorch/CUPTI CUDA activity traces; TensorRT/ORT execute model math. No GPU performance counter permissions or new profiling installation required.",
              "script_sha256": common.sha256(__file__)}
    engine.close()
    common.save(PROJECT / "environment/step5-precision.json", record)
    progress("5D", "passed", evidence="environment/step5-precision.json",
             verification="Actual FP32 SGEMM traced with TF32 disabled; actual FP16 tensor16x8x16 GEMM kernels traced from the preserved engine; inspected half GEMM interfaces, FP16 constraints, and explicit normalization compute policy")
    print(f"5D verified: {len(tensor_kernels)} distinct executed FP16 Tensor Core GEMM kernels; precision evidence saved.", flush=True)


if __name__ == "__main__":
    main()
