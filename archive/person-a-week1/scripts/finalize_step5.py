"""Record the human acceptance decision, verify, time, and freeze Step 5.

The raw numerical reports retain their failed status. Acceptance is a separate,
engine-specific human decision, never a change to the original tolerances.
"""

import argparse
import gc
import json
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np

import export_step5 as common
from lc0_inputs import dense_planes, native_encode
from step5_engine import ENGINE_RECORD, PROJECT, WORK, Engine, prerequisites, progress

ACCEPTED = "4271981b85fb44dd1171a8b49cd999626cd9662f184d3f347a8f7bc4b08b8363"
LIMITS = "9f1f32f4d4865c822850a94d20371a83b0d8f7b2d702d684f90f2266f1d04866"
HISTORY = PROJECT / "environment/step5-history" / ACCEPTED[:16]
DECISION = PROJECT / "environment/step5-acceptance.json"


def read(path):
    return json.loads(Path(path).read_text())


def accept():
    common.identities()
    common.graphs()
    assert common.sha256(PROJECT / "environment/step5-tolerances.json") == LIMITS
    first = read(HISTORY / "step5-engine.json")
    assert first["engine_sha256"] == ACCEPTED == common.sha256(first["engine_path"])
    confirmation = read(HISTORY / "step5-confirmation.json")
    assert confirmation["engine_sha256"] == ACCEPTED and confirmation["status"] == "failed"
    assert len(confirmation["gate_failures"]) == 4
    for group in confirmation["gate_failures"]:
        assert group["baseline"] == "F16_TRT" and len(group["failures"]) == 1
        failure = group["failures"][0]
        assert failure["id"] == "export-confirm-073" and failure["metric"] == "wdl_max_abs"
        assert failure["limit"] == 0.015 and 0.01959 <= failure["observed"] < 0.01960
    if DECISION.exists():
        decision = read(DECISION)
        assert decision["engine_sha256"] == ACCEPTED and decision["decision"] == "accepted_with_documented_drift"
        print("Existing explicit acceptance retained.", flush=True)
        return
    current = read(ENGINE_RECORD)
    if current["engine_sha256"] != ACCEPTED:
        rejected = PROJECT / "environment/step5-history" / current["engine_sha256"][:16]
        rejected.mkdir(parents=True, exist_ok=False)
        for name in ["step5-engine.json", "step5-precision.json", "step5-diagnosis.json",
                     "step5-reload-first.json", "step5-reload-second.json", "step5-progress.json",
                     "step5-resume-summary.json"]:
            shutil.copy2(PROJECT / "environment" / name, rejected / name)
    for name in ["step5-engine.json", "step5-precision.json", "step5-diagnosis.json",
                 "step5-confirmation.json", "step5-reload-first.json", "step5-reload-second.json"]:
        shutil.copy2(HISTORY / name, PROJECT / "environment" / name)
    decision = {"recorded_at_utc": common.now(), "decision": "accepted_with_documented_drift",
        "authority": "Direct human reply in this conversation",
        "user_reply": "Accept first engine with documented drift (Recommended)",
        "engine_sha256": ACCEPTED, "engine_path": first["engine_path"],
        "baseline": "F16_TRT", "original_tolerances_sha256": LIMITS,
        "raw_confirmation_status": "failed", "confirmation_report_sha256": common.sha256(HISTORY / "step5-confirmation.json"),
        "accepted_exception": {"position": "export-confirm-073", "metric": "wdl_max_abs",
            "original_limit": 0.015, "observed_vs_native": 0.019593477249145508,
            "observed_vs_R32_CUDA_max": 0.019594907760620117, "confirmation_positions": 128,
            "note": "One position, duplicated across batch/reference checks; raw failure remains recorded"},
        "scope": "Accept this exact engine and its measured drift; no blanket relaxation for future engines/models/positions",
        "unchanged": ["two baseline definitions", "checkpoint and ONNX hashes", "original numerical limits"],
        "scientific_limit": "Prediction agreement only; no tablebase accuracy or chess-strength conclusion"}
    common.save(DECISION, decision)
    progress("5C", "passed", engine_sha256=ACCEPTED, evidence="environment/step5-engine.json",
             verification="User-selected first engine restored; prior two fresh-process reload checks retained")
    progress("5D", "passed", engine_sha256=ACCEPTED, evidence="environment/step5-precision.json",
             verification="Restored first-engine precision evidence: executed FP32 SGEMMs and FP16 Tensor Core GEMMs")
    progress("5E", "passed", evidence="environment/step5-diagnosis.json", raw_numerical_status="passed",
             verification="Selected first engine passed original limits on all 86 development positions")
    progress("5F", "passed", acceptance="accepted_with_documented_drift", raw_numerical_status="failed",
             evidence="environment/step5-acceptance.json",
             verification="Explicit user acceptance of the exact preserved engine with the known 1/128 WDL exception; raw failure and original limits retained")
    print("User acceptance recorded; first engine restored; raw numerical failure preserved.", flush=True)


def verify(live=True):
    prerequisites("5G")
    common.identities()
    graphs = common.graphs()
    decision = read(DECISION)
    assert decision["decision"] == "accepted_with_documented_drift" and decision["engine_sha256"] == ACCEPTED
    assert common.sha256(PROJECT / "environment/step5-tolerances.json") == LIMITS
    assert read(ENGINE_RECORD)["engine_sha256"] == ACCEPTED
    assert read(ENGINE_RECORD)["graph_sha256"] == graphs["graphs"]["f16"]["sha256"]
    assert read(PROJECT / "environment/step5-precision.json")["F16_TRT"]["engine_sha256"] == ACCEPTED
    confirmation = read(PROJECT / "environment/step5-confirmation.json")
    assert confirmation["status"] == "failed"
    assert common.sha256(PROJECT / "environment/step5-confirmation.json") == decision["confirmation_report_sha256"]
    assert common.sha256(confirmation["outputs_path"]) == confirmation["outputs_sha256"]
    diagnosis = read(PROJECT / "environment/step5-diagnosis.json")
    assert diagnosis["status"] == "passed" and diagnosis["engine_sha256"] == ACCEPTED
    assert common.sha256(diagnosis["outputs_path"]) == diagnosis["outputs_sha256"]
    for artifact in read(PROJECT / "environment/step5-precision.json")["artifacts"]:
        assert common.sha256(artifact["path"]) == artifact["sha256"]
    engine_record = read(ENGINE_RECORD)
    assert common.sha256(engine_record["engine_path"]) == ACCEPTED
    snapshot = WORK / "history" / ACCEPTED[:16] / "step5_engine.py"
    assert common.sha256(snapshot) == engine_record["build_script_sha256"]
    cache_path = Path(engine_record["timing_cache_path"])
    timing_cache_matches = cache_path.exists() and common.sha256(cache_path) == engine_record["timing_cache_sha256"]
    if live:
        runner = Engine()
        reload_record = read(HISTORY / "step5-reload-first.json")
        assert common.sha256(reload_record["arrays_path"]) == reload_record["arrays_sha256"]
        with np.load(PROJECT / "data/pilot/inputs.npz", allow_pickle=False) as inputs, np.load(reload_record["arrays_path"], allow_pickle=False) as expected:
            indices = [inputs["ids"].tolist().index(key) for key in expected["ids"]]
            planes = inputs["planes"][indices]
            for batch in [1, 8]:
                outputs = [[], [], []]
                for start in range(0, len(planes), batch):
                    result = runner.run(planes[start:start + batch])
                    for i in range(3): outputs[i].append(result[i])
                for key, parts in zip(["policy", "wdl", "mlh"], outputs):
                    assert np.array_equal(np.concatenate(parts), expected[f"b{batch}_{key}"]), "Restored-engine output changed"
        rows = [json.loads(line) for line in (PROJECT / "data/export-confirmation/positions.jsonl").read_text().splitlines()]
        row = next(row for row in rows if row["id"] == "export-confirm-073")
        planes = dense_planes(native_encode([row])[0])[None]
        outputs = runner.run(planes)
        with np.load(PROJECT / "data/export-confirmation/outputs.npz", allow_pickle=False) as expected:
            index = expected["ids"].tolist().index(row["id"])
            for key, output in zip(["logits", "wdl", "moves_left"], outputs):
                assert np.array_equal(output[0], expected["F16_TRT_b1_" + key][index])
        runner.close()
    record = {"verified_at_utc": common.now(), "status": "passed", "engine_sha256": ACCEPTED,
              "original_limits_unchanged": True, "raw_failure_preserved": True,
              "acceptance_sha256": common.sha256(DECISION),
              "restored_engine_outputs": "bit-identical to archived outputs, including accepted outlier" if live else "live check not requested",
              "original_build_source_snapshot_sha256": common.sha256(snapshot),
              "original_timing_cache_matches": bool(timing_cache_matches),
              "reproducibility": "Reuse exact serialized engine. Original shared timing-cache file was overwritten by the rejected build; it is not a valid first-engine rebuild cache. Future builds use hash-specific cache filenames. A fresh rebuild is not promised bit-identical."}
    if live:
        common.save(PROJECT / "environment/step5-final-integrity.json", record)
    print("Accepted-engine identity, evidence hashes and exception scope verified" +
          ("; restored outputs are bit-identical." if live else "; prior live-check record retained."), flush=True)
    return record


def telemetry():
    result = subprocess.run(["/usr/lib/wsl/lib/nvidia-smi", "--query-gpu=name,driver_version,pstate,temperature.gpu,clocks.sm,clocks.mem,power.draw,memory.used", "--format=csv"], capture_output=True, text=True)
    return {"recorded_at_utc": common.now(), "returncode": result.returncode,
            "output": result.stdout.strip(), "error": result.stderr.strip()}


def statistics(values):
    return {"median_ms": float(np.median(values)), "p95_ms": float(np.percentile(values, 95)),
            "minimum_ms": float(np.min(values)), "samples_ms": values}


def timing():
    verify(live=False)
    import torch
    import onnxruntime as ort
    ort.preload_dlls()
    engine = Engine()
    stream = engine.stream
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.log_severity_level = 3
    session = ort.InferenceSession(str(PROJECT / "models/onnx/bt3-r32.onnx"), sess_options=options,
        providers=[("CUDAExecutionProvider", {"use_tf32": "0", "user_compute_stream": str(stream.cuda_stream),
                                               "cudnn_conv_use_max_workspace": "0"}), "CPUExecutionProvider"])
    session.disable_fallback()
    assert session.get_provider_options()["CUDAExecutionProvider"]["use_tf32"] == "0"
    with np.load(PROJECT / "data/pilot/inputs.npz", allow_pickle=False) as data:
        indices = [0, 8, 16, 24, 31, 32, 48, 56]
        inputs, ids = data["planes"][indices].copy(), data["ids"][indices].tolist()
    report = {"started_at_utc": common.now(), "engine_sha256": ACCEPTED, "positions": ids,
              "warmup_resident": 10, "resident_repetitions": 30, "warmup_host": 5, "host_repetitions": 15,
              "ordering": "Alternate which baseline runs first on each repetition; one workload at a time",
              "before": telemetry(), "batches": {}, "ORT_provider_options": session.get_provider_options(),
              "power_policy": "Windows Balanced observed at setup; clocks/power not locked or tuned for this sanity measurement",
              "scope": "Small timing sanity check, not the final controlled benchmark; runtime and precision both differ; no MCTS/strength claim"}
    for batch in [1, 8]:
        planes = np.ascontiguousarray(inputs[:batch], dtype=np.float32)
        half_planes = np.ascontiguousarray(planes, dtype=np.float16)
        binding = session.io_binding()
        input_tensor = torch.from_numpy(planes).to("cuda")
        output_tensors = [torch.empty((batch, width), device="cuda", dtype=torch.float32) for width in [1858, 3, 1]]
        binding.bind_input("/input/planes", "cuda", 0, np.float32, tuple(input_tensor.shape), input_tensor.data_ptr())
        for name, tensor in zip(common.OUTPUTS, output_tensors):
            binding.bind_output(name, "cuda", 0, np.float32, tuple(tensor.shape), tensor.data_ptr())
        torch.cuda.synchronize()
        buffers = engine.prepare(batch)
        with torch.cuda.stream(stream):
            buffers["/input/planes"].copy_(torch.from_numpy(half_planes), non_blocking=False)
        stream.synchronize()

        def r32_resident():
            session.run_with_iobinding(binding)

        def f16_resident():
            assert engine.context.execute_async_v3(stream.cuda_stream)

        functions = {"R32_CUDA": r32_resident, "F16_TRT": f16_resident}
        for _ in range(10):
            for function in functions.values():
                function()
                stream.synchronize()
        wall = {name: [] for name in functions}
        device = {name: [] for name in functions}
        for iteration in range(30):
            order = list(functions) if iteration % 2 == 0 else list(reversed(functions))
            for name in order:
                begin, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                started = time.perf_counter()
                begin.record(stream)
                functions[name]()
                end.record(stream)
                end.synchronize()
                wall[name].append((time.perf_counter() - started) * 1000)
                device[name].append(float(begin.elapsed_time(end)))
        r32_resident_outputs = [tensor.cpu().numpy().copy() for tensor in output_tensors]
        f16_resident_outputs = [buffers[name].cpu().numpy().astype(np.float32) for name in common.OUTPUTS]
        r32_host = session.run(common.OUTPUTS, {"/input/planes": planes})
        f16_host = engine.run(half_planes)
        for gpu, cpu in zip(r32_resident_outputs, r32_host):
            np.testing.assert_allclose(gpu, cpu, atol=1e-5, rtol=1e-5)
        for gpu, cpu in zip(f16_resident_outputs, f16_host):
            assert np.array_equal(gpu, cpu), "TensorRT resident/host pipeline mismatch"
        host_functions = {"R32_CUDA": lambda: session.run(common.OUTPUTS, {"/input/planes": planes}),
                          "F16_TRT": lambda: engine.run(half_planes)}
        for _ in range(5):
            for function in host_functions.values(): function()
        host = {name: [] for name in functions}
        for iteration in range(15):
            order = list(functions) if iteration % 2 == 0 else list(reversed(functions))
            for name in order:
                started = time.perf_counter()
                host_functions[name]()
                host[name].append((time.perf_counter() - started) * 1000)
        results = {name: {"resident_host_wall": statistics(wall[name]), "resident_cuda_event": statistics(device[name]),
                          "host_arrays_to_float32_host_outputs": statistics(host[name]),
                          "resident_positions_per_second": batch * 1000 / float(np.median(wall[name]))}
                   for name in functions}
        results["resident_pipeline_speedup_F16_over_R32"] = results["R32_CUDA"]["resident_host_wall"]["median_ms"] / results["F16_TRT"]["resident_host_wall"]["median_ms"]
        report["batches"][str(batch)] = results
        print("Timing batch", batch, json.dumps({name: value["resident_host_wall"]["median_ms"] for name, value in results.items() if isinstance(value, dict)}), flush=True)
        del binding, input_tensor, output_tensors
    report.update({"completed_at_utc": common.now(), "status": "passed", "after": telemetry(),
        "boundaries": {"resident_host_wall": "Host wall clock around API enqueue and completion, preallocated GPU input/output; excludes H2D/D2H and build/load/warmup",
                       "resident_cuda_event": "CUDA stream interval surrounding enqueue; includes device waits for host submissions, not a sum of kernel durations",
                       "host_arrays_to_float32_host_outputs": "Host wall clock including input/output transfers and API/copy/conversion overhead; FP16 outputs returned as float32 for common evaluation"},
        "script_sha256": common.sha256(__file__)})
    report["clock_comparison"] = {
        "cuda_event_over_host_wall": {batch: {name:
            values[name]["resident_cuda_event"]["median_ms"] / values[name]["resident_host_wall"]["median_ms"]
            for name in functions} for batch, values in report["batches"].items()},
        "interpretation": "Record both clocks independently. An approximately 8% disagreement was observed in the initial pilot; cause is not established. Host wall is the stated pipeline metric, and CUDA events are diagnostic. Resolve clock disagreement before final absolute timing claims."}
    engine.close()
    del session
    gc.collect()
    common.save(PROJECT / "environment/step5-timing.json", report)


def freeze():
    integrity = verify(live=False)
    saved_integrity = read(PROJECT / "environment/step5-final-integrity.json")
    assert saved_integrity["status"] == "passed" and saved_integrity["engine_sha256"] == ACCEPTED
    assert saved_integrity["acceptance_sha256"] == common.sha256(DECISION)
    timing_report = read(PROJECT / "environment/step5-timing.json")
    assert timing_report["status"] == "passed" and timing_report["engine_sha256"] == ACCEPTED
    paths = ["environment/step5-baselines.json", "environment/step5-acceptance.json",
             "environment/step5-engine.json", "environment/step5-precision.json",
             "environment/step5-diagnosis.json", "environment/step5-confirmation.json",
             "environment/step5-final-integrity.json", "environment/step5-timing.json",
             "environment/step5-tolerances.json", "models/onnx/manifest.json",
             "data/pilot/exclusions.json", "data/export-confirmation/exclusions.json",
             "data/export-confirmation/protocol.json", "scripts/export_step5.py",
             "scripts/step5_engine.py", "scripts/step5_precision.py", "scripts/step5_numerics.py",
             "scripts/finalize_step5.py", "scripts/lc0_inputs.py",
             "docs/experiment-contract.md", "docs/onnx-validation.md", "docs/environment.md"]
    manifest = {"frozen_at_utc": common.now(), "status": "complete_with_documented_drift",
        "engine_sha256": ACCEPTED, "engine_path": read(ENGINE_RECORD)["engine_path"],
        "baseline_ids": ["R32_CUDA", "F16_TRT"], "two_baseline_definition": "unchanged",
        "raw_confirmation_status": "failed", "acceptance": "Explicit human acceptance, engine-specific; original bounds unchanged",
        "artifacts": [{"relative_path": path, "sha256": common.sha256(PROJECT / path)} for path in paths],
        "runtime_assets": read(PROJECT / "environment/step5-precision.json")["artifacts"],
        "build_source_snapshot": str(WORK / "history" / ACCEPTED[:16] / "step5_engine.py"),
        "timing_cache_matches_original_build": integrity["original_timing_cache_matches"],
        "reproduce": "Reuse exact engine; python scripts/finalize_step5.py verify. Rebuilding can choose different tactics and invalidates this engine-specific acceptance.",
        "later_final_test_exclusions": ["data/pilot/exclusions.json", "data/export-confirmation/exclusions.json"],
        "limitations": ["Pilot timing only; host/CUDA clock disagreement needs resolution before final absolute timing claims",
                        "No Syzygy accuracy, INT8, or MCTS results", "Step 6 not started"]}
    common.save(PROJECT / "environment/step5-final-manifest.json", manifest)
    progress("5G", "passed", evidence="environment/step5-final-manifest.json",
             verification="Accepted first-engine identity and outputs reverified; matched-boundary pilot timings recorded; final artifact hashes frozen",
             acceptance="complete_with_documented_drift", reason="Explicit acceptance recorded; timing, integrity checks and baseline freeze completed")
    summary = read(PROJECT / "environment/step5-resume-summary.json")
    summary.update({"updated_at_utc": common.now(), "status": "complete_with_documented_drift",
                    "accepted_engine_sha256": ACCEPTED, "5G_started": True, "5G_completed": True,
                    "step6_started": False, "remaining": [], "acceptance_record": "environment/step5-acceptance.json",
                    "final_manifest": "environment/step5-final-manifest.json"})
    for candidate in summary["candidates"]:
        selected = candidate["engine_sha256"] == ACCEPTED
        candidate["selection"] = "accepted_with_documented_drift" if selected else "rejected"
        candidate["recommendation"] = ("Selected by explicit human acceptance; raw confirmation failure retained" if selected
                                       else "Do not adopt; development numerical checks failed")
    for item in ["5E selected-engine development checks",
                 "5F explicit human acceptance of documented confirmation drift",
                 "5G live restored-output integrity, pilot timings and final freeze"]:
        if item not in summary["verified_work"]:
            summary["verified_work"].append(item)
    common.save(PROJECT / "environment/step5-resume-summary.json", summary)
    print("5G complete: Step 5 frozen with the explicitly accepted drift; Step 6 remains unstarted.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["accept", "verify", "timing", "freeze"])
    stage = parser.parse_args().stage
    {"accept": accept, "verify": verify, "timing": timing, "freeze": freeze}[stage]()
