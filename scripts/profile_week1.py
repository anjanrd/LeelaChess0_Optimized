"""Profile the exact accepted floating engines before selecting INT8 coverage."""
import gc
import json
import re
import subprocess
import time
from collections import Counter, defaultdict

import numpy as np

from week1_common import PROJECT, RUNTIME, artifact, base, frozen, progress, read, save
from step5_engine import Engine


def telemetry():
    r = subprocess.run(["/usr/lib/wsl/lib/nvidia-smi", "--query-gpu=name,pstate,temperature.gpu,clocks.sm,clocks.mem,power.draw,memory.used", "--format=csv"], capture_output=True, text=True)
    return {"utc": base.now(), "output": r.stdout.strip(), "error": r.stderr.strip()}


def stats(values):
    return {"median_ms": float(np.median(values)), "p95_ms": float(np.percentile(values, 95)), "samples_ms": values}


def time_calls(fn, stream, torch, count=40):
    wall, cuda = [], []
    for _ in range(count):
        start, stop = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        t = time.perf_counter()
        start.record(stream)
        fn()
        stop.record(stream)
        stop.synchronize()
        wall.append((time.perf_counter() - t) * 1000)
        cuda.append(float(start.elapsed_time(stop)))
    return {"wall": stats(wall), "cuda_event": stats(cuda), "cuda_over_wall": float(np.median(cuda) / np.median(wall))}


def main():
    frozen()
    import torch
    import tensorrt as trt
    import onnxruntime as ort
    ort.preload_dlls()
    work = RUNTIME / "profile"
    work.mkdir(parents=True, exist_ok=True)
    protocol = {"registered_at_utc": base.now(), "engine_sha256": read(PROJECT / "environment/step5-engine.json")["engine_sha256"],
        "batches": [1, 4, 8], "warmups": 30, "resident_repeats": 40, "host_repeats": 20, "profile_repeats": 20,
        "scope_candidates": ["v1: 127 weighted MatMuls", "expanded: all fixed-weight MatMuls with K/N >=16 (160), leaving four tiny output matrices floating"],
        "probe_budget": "At most these two full naive INT8 candidates; do not select layers using numerical/test accuracy",
        "trigger": "If excluded-weight associated gemm layers exceed 10% of profiled F16 layer time at batch 1, expanded candidate requires a bounded pilot comparison. Otherwise review memory/storage benefit explicitly.",
        "criterion": "Prefer broader actual INT8 weight coverage if its warmed host-pipeline median is not more than 10% slower at batch 1 and 8; report all numerical drift without fitting scope to predictions. Invalid/nonfinite output, unsupported actual INT8 or major degeneration requires investigation.",
        "limits": "Layer times are instrumented; unfused MAC/weight-byte estimates are not measured DRAM traffic. No memory counter permissions assumed."}
    save(PROJECT / "environment/week1-profile-protocol.json", protocol)
    record = {"started_at_utc": base.now(), "before": telemetry(), "protocol": protocol, "F16_TRT": {}, "R32_CUDA": {}}
    with np.load(PROJECT / "data/pilot/inputs.npz", allow_pickle=False) as d:
        planes = d["planes"][[0, 8, 16, 24, 31, 32, 48, 56]].copy()
    inventory = read(PROJECT / "environment/step6-inventory.json")["matrix_operations"]
    categories = {r["name"]: "selected_weighted" if r["selected"] else "excluded_weighted" if r["weight"] else "dynamic_products" for r in inventory}
    runner = Engine()
    baseline_outputs = {}
    for batch in [1, 4, 8]:
        expected = runner.run(planes[:batch])
        buffers = runner.prepare(batch)
        fn = lambda: runner.context.execute_async_v3(runner.stream.cuda_stream)
        for _ in range(30): fn()
        runner.stream.synchronize()
        resident = time_calls(fn, runner.stream, torch)
        host = []
        for _ in range(20):
            t = time.perf_counter()
            output = runner.run(planes[:batch])
            host.append((time.perf_counter() - t) * 1000)
        assert all(np.array_equal(a, b) for a, b in zip(expected, output))
        baseline_outputs[batch] = expected
        record["F16_TRT"][str(batch)] = {"resident": resident, "host_pipeline": stats(host)}
    class Collector(trt.IProfiler):
        def __init__(self):
            trt.IProfiler.__init__(self)
            self.rows = defaultdict(list)
        def report_layer_time(self, name, milliseconds):
            self.rows[name].append(float(milliseconds))
    collector = Collector()
    runner.context.profiler = collector
    runner.context.enqueue_emits_profile = False
    for batch in [1, 4, 8]:
        runner.run(planes[:batch])
        runner.context.report_to_profiler()
        collector.rows.clear()
        inspector = runner.engine.create_engine_inspector()
        inspector.execution_context = runner.context
        info = json.loads(inspector.get_engine_information(trt.LayerInformationFormat.JSON))
        path = work / f"inspector-b{batch}.json"
        save(path, info)
        by_name = {r["Name"]: r for r in info["Layers"]}
        measured = []
        for _ in range(20):
            t = time.perf_counter()
            output = runner.run(planes[:batch])
            assert runner.context.report_to_profiler()
            measured.append((time.perf_counter() - t) * 1000)
        assert all(np.array_equal(a, b) for a, b in zip(baseline_outputs[batch], output))
        mapped, totals = [], defaultdict(float)
        for name, values in collector.rows.items():
            item = by_name.get(name, {})
            origins = re.findall(r"\[ONNX Layer: ([^\]]+)\]", item.get("Metadata", ""))
            matrix_names = sorted(set(origins) & categories.keys())
            cats = {categories[n] for n in matrix_names}
            # kgen metadata can include a MatMul whose reshape/cast it helps;
            # only gemm layers are assigned exclusively to matrix groups.
            category = next(iter(cats)) if len(cats) == 1 and item.get("LayerType") == "gemm" else "mixed_fused" if matrix_names else "other_or_unattributed"
            ms = float(np.mean(values))
            totals[category] += ms
            mapped.append({"layer": name, "type": item.get("LayerType"), "mean_ms": ms, "samples": len(values),
                "category": category, "matrix_origins": matrix_names, "tactic": item.get("TacticName", "")})
        assert mapped and all(r["samples"] == 20 for r in mapped)
        total = sum(totals.values())
        assert total > 0 and totals["excluded_weighted"] > 0
        record["F16_TRT"][str(batch)].update({"profiled_host": stats(measured), "sum_mean_layer_ms": total,
            "exclusive_layer_groups_ms": dict(totals), "excluded_weighted_layer_fraction": totals["excluded_weighted"] / total,
            "layers": mapped, "inspector": artifact(path)})
        print("F16 profile", batch, round(total, 3), "ms; excluded weighted", round(100 * totals["excluded_weighted"] / total, 2), "%", flush=True)
    runner.close()
    del runner, collector
    gc.collect()
    torch.cuda.empty_cache()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.log_severity_level = 3
    options.enable_profiling = True
    options.profile_file_prefix = str(work / "r32-provider")
    stream = torch.cuda.Stream()
    session = ort.InferenceSession(str(PROJECT / "models/onnx/bt3-r32.onnx"), sess_options=options,
        providers=[("CUDAExecutionProvider", {"use_tf32": "0", "user_compute_stream": str(stream.cuda_stream), "cudnn_conv_use_max_workspace": "0"}), "CPUExecutionProvider"])
    for batch in [1, 4, 8]:
        tensor = torch.from_numpy(planes[:batch]).to("cuda")
        outputs = [torch.empty((batch, w), dtype=torch.float32, device="cuda") for w in [1858, 3, 1]]
        binding = session.io_binding()
        binding.bind_input("/input/planes", "cuda", 0, np.float32, tuple(tensor.shape), tensor.data_ptr())
        for name, value in zip(base.OUTPUTS, outputs): binding.bind_output(name, "cuda", 0, np.float32, tuple(value.shape), value.data_ptr())
        torch.cuda.synchronize()
        fn = lambda: session.run_with_iobinding(binding)
        for _ in range(30): fn()
        stream.synchronize()
        resident = time_calls(fn, stream, torch)
        host = []
        for _ in range(20):
            t = time.perf_counter()
            result = session.run(base.OUTPUTS, {"/input/planes": planes[:batch]})
            host.append((time.perf_counter() - t) * 1000)
        for gpu, cpu in zip(outputs, result): np.testing.assert_allclose(gpu.cpu().numpy(), cpu, atol=1e-5, rtol=1e-5)
        record["R32_CUDA"][str(batch)] = {"resident": resident, "host_pipeline": stats(host)}
    provider_path = session.end_profiling()
    record["R32_CUDA_provider_profile"] = artifact(provider_path)
    record.update({"completed_at_utc": base.now(), "status": "passed", "after": telemetry(),
        "memory_counters": "Not collected; no bandwidth-bound claim from timing/MAC counts alone",
        "fp16_outputs": "Identical before/after instrumentation", "baseline_artifacts_unchanged": True,
        "script_sha256": base.sha256(__file__)})
    frozen()
    save(PROJECT / "environment/week1-baseline-profile.json", record)
    progress("W1-A06P", "DONE", "environment/week1-baseline-profile.json",
        "Accepted engine profiled without rebuild at batches 1/4/8; actual excluded-weight layer contribution recorded; precision/shape evidence preserved.")


if __name__ == "__main__": main()
