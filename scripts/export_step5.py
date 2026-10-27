"""Export pinned BT3 graphs; establish development gates, then verify the pilot.

Run stages in order: export, develop, verify. Build/profile scratch stays in /tmp.
The develop stage never evaluates pilot positions. Verify cannot change gates.
"""

import argparse
import gc
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from lc0_inputs import (RUNTIME, dense_planes, input_object, legal_move_indices,
                        legal_policy, native_encode, replay, wdl_from_qd)

PROJECT = Path(__file__).resolve().parents[1]
COMMIT = "9f45ea446baf9ce55e299250cde3053b7e93a035"
DESTINATION = PROJECT / "models/onnx"
MODEL_NAMES = {"f32": "bt3-r32.onnx", "f16": "bt3-f16.onnx"}
OUTPUTS = ["/output/policy", "/output/wdl", "/output/mlh"]
# Initial gates are recorded before any development inference. Raw logits are
# diagnostic: their additive offset has no effect on legal move probabilities.
INITIAL_GATES = {
    "f32": {"legal_probability_max_abs": 0.0002, "legal_kl_max": 0.00001,
            "wdl_max_abs": 0.0005, "q_max_abs": 0.001,
            "moves_left_atol": 0.02, "moves_left_rtol": 0.0002,
            "batch_probability_max_abs": 0.0002},
    "f16": {"legal_probability_max_abs": 0.015, "legal_kl_max": 0.003,
            "wdl_max_abs": 0.015, "q_max_abs": 0.03,
            "moves_left_atol": 0.5, "moves_left_rtol": 0.01,
            "batch_probability_max_abs": 0.005},
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def identities():
    source = RUNTIME / "source/lc0"
    assert subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip() == COMMIT
    assert not subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True).strip()
    checkpoint = json.loads((PROJECT / "models/source/checkpoint.json").read_text())
    assert sha256(PROJECT / checkpoint["relative_path"]) == checkpoint["sha256_compressed"]
    pilot = json.loads((PROJECT / "data/pilot/manifest.json").read_text())
    for name, digest in pilot["files_sha256"].items():
        assert sha256(PROJECT / "data/pilot" / name) == digest, name
    return checkpoint


def export():
    import onnx
    checkpoint = identities()
    DESTINATION.mkdir(parents=True, exist_ok=True)
    manifest = {"exported_at_utc": now(), "lc0_commit": COMMIT,
                "checkpoint_sha256": checkpoint["sha256_compressed"],
                "policy_head": "vanilla", "value_head": "winner",
                "history_fill": "no (input preparation)", "graphs": {}}
    with tempfile.TemporaryDirectory(prefix="lc0-step5-export-") as directory:
        for precision, filename in MODEL_NAMES.items():
            temporary = Path(directory) / filename
            command = [str(RUNTIME / "build/lc0-tools/lc0"), "leela2onnx",
                       "--input=" + str(PROJECT / checkpoint["relative_path"]),
                       "--output=" + str(temporary), "--onnx-data-type=" + precision,
                       "--onnx-opset=17", "--onnx-batch-size=-1", "--onnx-ir=9",
                       "--policy-head=vanilla", "--value-head=winner"]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            model = onnx.load(str(temporary))
            onnx.checker.check_model(model, full_check=True)
            dtype = onnx.TensorProto.FLOAT if precision == "f32" else onnx.TensorProto.FLOAT16
            inputs, outputs = model.graph.input, model.graph.output
            assert len(inputs) == 1 and inputs[0].name == "/input/planes"
            assert [v.name for v in outputs] == OUTPUTS
            assert [d.dim_value for d in inputs[0].type.tensor_type.shape.dim[1:]] == [112, 8, 8]
            assert [v.type.tensor_type.shape.dim[1].dim_value for v in outputs] == [1858, 3, 1]
            assert all(v.type.tensor_type.elem_type == dtype for v in [*inputs, *outputs])
            assert all(v.type.tensor_type.shape.dim[0].dim_value <= 0 for v in [*inputs, *outputs])
            assert model.ir_version == 9 and model.opset_import[0].version == 17
            # Every floating initializer must use the requested export dtype.
            floats = Counter(t.data_type for t in model.graph.initializer if t.data_type in {1, 10, 11, 16})
            assert set(floats) == {dtype}, floats
            assert not any(n.op_type in {"QuantizeLinear", "DequantizeLinear"} for n in model.graph.node)
            target = DESTINATION / filename
            digest = sha256(temporary)
            if target.exists() and sha256(target) != digest:
                raise RuntimeError(f"Existing graph differs: {target}; version changes explicitly")
            if not target.exists():
                import shutil
                shutil.copyfile(temporary, target)
            manifest["graphs"][precision] = {
                "relative_path": str(target.relative_to(PROJECT)), "sha256": digest,
                "bytes": target.stat().st_size, "ir_version": model.ir_version,
                "opset": 17, "input": {"name": inputs[0].name, "shape": ["B", 112, 8, 8],
                                        "dtype": onnx.TensorProto.DataType.Name(dtype)},
                "outputs": [{"name": v.name, "shape": ["B", v.type.tensor_type.shape.dim[1].dim_value],
                             "dtype": onnx.TensorProto.DataType.Name(dtype)} for v in outputs],
                "nodes": len(model.graph.node), "floating_initializers": dict(floats),
                "operator_counts": dict(Counter(n.op_type for n in model.graph.node)),
                "command": command, "exporter_stdout": result.stdout,
                "onnx_full_check": "passed"}
            del model
            gc.collect()
            print(f"Export/check passed: {precision} ({target.stat().st_size:,} bytes)", flush=True)
    save(DESTINATION / "manifest.json", manifest)


def graphs():
    manifest = json.loads((DESTINATION / "manifest.json").read_text())
    for graph in manifest["graphs"].values():
        assert sha256(PROJECT / graph["relative_path"]) == graph["sha256"]
    return manifest


def native_reference(records):
    sys.path.insert(0, str(RUNTIME / "build/lc0-tools"))
    import backends
    checkpoint = json.loads((PROJECT / "models/source/checkpoint.json").read_text())
    encoded = native_encode(records)
    planes = np.stack([dense_planes(item) for item in encoded])
    weights = backends.Weights(str(PROJECT / checkpoint["relative_path"]))
    backend = backends.Backend(weights=weights, backend="eigen", options="batch_size=1,threads=2")
    logits, wdl, mlh = [], [], []
    for record, item in zip(records, encoded):
        output, = backend.evaluate(input_object(backends, item))
        logits.append(output.p_raw(*range(1858)))
        wdl.append(wdl_from_qd(output.q(), output.d()))
        mlh.append([output.m()])
    result = [np.asarray(item, dtype=np.float32) for item in [logits, wdl, mlh]]
    del backend, weights
    gc.collect()
    print(f"Native Eigen reference ready: {len(records)} positions", flush=True)
    return planes, result


def infer(precision, planes, batch_sizes, scratch, provider="cuda"):
    import onnxruntime as ort
    if provider == "trt":
        import tensorrt  # Load wheel-provided TensorRT shared libraries first.
    # Load bundled CUDA/cuDNN libraries. CUDA EP must execute real compute;
    # provider registration alone is not accepted as execution evidence.
    ort.preload_dlls()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.enable_profiling = True
    options.profile_file_prefix = str(scratch / precision)
    options.log_severity_level = 3
    providers = [("CUDAExecutionProvider", {"use_tf32": "0", "cudnn_conv_use_max_workspace": "0"}),
                 "CPUExecutionProvider"]
    if provider == "trt":
        cache = RUNTIME / "step5-diagnostics/trt-cache"
        cache.mkdir(parents=True, exist_ok=True)
        providers.insert(0, ("TensorrtExecutionProvider", {
            "trt_fp16_enable": True, "trt_max_workspace_size": 536870912,
            "trt_engine_cache_enable": True, "trt_engine_cache_path": str(cache),
            "trt_profile_min_shapes": "/input/planes:1x112x8x8",
            "trt_profile_opt_shapes": "/input/planes:4x112x8x8",
            "trt_profile_max_shapes": "/input/planes:8x112x8x8",
            "trt_layer_norm_fp32_fallback": True}))
    session = ort.InferenceSession(str(DESTINATION / MODEL_NAMES[precision]),
                                   sess_options=options, providers=providers)
    session.disable_fallback()
    assert "CUDAExecutionProvider" in session.get_providers()
    if provider == "trt":
        assert "TensorrtExecutionProvider" in session.get_providers()
    assert session.get_provider_options()["CUDAExecutionProvider"]["use_tf32"] == "0"
    dtype = np.float32 if precision == "f32" else np.float16
    assert session.get_inputs()[0].type == ("tensor(float)" if precision == "f32" else "tensor(float16)")
    runs = {}
    for batch in batch_sizes:
        collected = []
        for start in range(0, len(planes), batch):
            feed = np.ascontiguousarray(planes[start:start + batch], dtype=dtype)
            outputs = session.run(OUTPUTS, {"/input/planes": feed})
            for output, width in zip(outputs, [1858, 3, 1]):
                assert output.shape == (len(feed), width) and output.dtype == dtype
                assert np.isfinite(output).all(), f"Nonfinite {precision} output at {start}"
            collected.append(outputs)
        runs[batch] = [np.concatenate([item[i] for item in collected]).astype(np.float32) for i in range(3)]
        print(f"{provider} {precision}: {len(planes)} positions, batch {batch}", flush=True)
    events = json.loads(Path(session.end_profiling()).read_text())
    kernels = [e for e in events if e.get("args", {}).get("provider")]
    execution = Counter((e["args"]["provider"], e["args"].get("op_name")) for e in kernels)
    if provider == "trt":
        assert any(ep == "TensorrtExecutionProvider" for ep, op in execution), execution
    else:
        assert any(ep == "CUDAExecutionProvider" and op in {"MatMul", "Gemm", "FusedMatMul"}
                   for ep, op in execution), execution
    cpu_compute = {op for provider, op in execution if provider == "CPUExecutionProvider"
                   and op not in {"Shape", "Gather", "Concat", "Unsqueeze", "Squeeze", "Slice", "Cast", "Reshape"}}
    assert not cpu_compute, f"Unexpected CPU computation: {cpu_compute}"
    evidence = {"onnxruntime_version": ort.__version__, "providers": session.get_providers(),
                "provider_options": session.get_provider_options(),
                "executed_kernels": [{"provider": provider, "operator": op, "events": count}
                                     for (provider, op), count in sorted(execution.items())],
                "batches": batch_sizes, "cuda_ep_tf32": False,
                "tensorrt_tf32": "not established by CUDA EP settings" if provider == "trt" else "not applicable",
                "note": "Numerical validation only; provider evidence does not prove every internal kernel's precision or benchmark performance"}
    del session
    gc.collect()
    return runs, evidence


def log_probabilities(logits, indices):
    values = np.asarray(logits[indices], dtype=np.float64)
    centered = values - values.max()
    return centered - np.log(np.exp(centered).sum())


def compare(records, reference, candidate, gates, enforce=True):
    rp, rw, rm = reference
    cp, cw, cm = candidate
    assert np.isfinite(cp).all() and np.isfinite(cw).all() and np.isfinite(cm).all()
    assert np.min(cw) >= 0 and np.max(cw) <= 1 and np.max(abs(cw.sum(axis=1) - 1)) <= 0.001
    assert np.min(cm) >= 0
    rows, failures = [], []
    for i, record in enumerate(records):
        board, _ = replay(record)
        row = {"id": record["id"], "raw_logit_max_abs": float(np.max(abs(cp[i] - rp[i]))),
               "wdl_max_abs": float(np.max(abs(cw[i] - rw[i]))),
               "q_abs": float(abs((cw[i, 0] - cw[i, 2]) - (rw[i, 0] - rw[i, 2]))),
               "moves_left_abs": float(abs(cm[i, 0] - rm[i, 0]))}
        for metric, limit in [("wdl_max_abs", gates["wdl_max_abs"]),
                              ("q_abs", gates["q_max_abs"]),
                              ("moves_left_abs", gates["moves_left_atol"] + gates["moves_left_rtol"] * abs(rm[i, 0]))]:
            if row[metric] > limit:
                failures.append({"id": record["id"], "metric": metric,
                                 "observed": row[metric], "limit": float(limit)})
        if board.legal_moves.count():
            moves, probs, best = legal_policy(rp[i], board)
            _, other, new_best = legal_policy(cp[i], board)
            indices = [legal_move_indices(board)[move] for move in moves]
            logp, logq = log_probabilities(rp[i], indices), log_probabilities(cp[i], indices)
            kl = max(0.0, float(np.sum(np.exp(logp) * (logp - logq))))
            margin = float(np.sort(probs)[-1] - np.sort(probs)[-2]) if len(probs) > 1 else 1.0
            row.update({"legal_probability_max_abs": float(np.max(abs(probs - other))),
                        "legal_kl": kl, "reference_best": best, "candidate_best": new_best,
                        "top_agrees": best == new_best, "reference_top_margin": margin})
            for metric, limit in [("legal_probability_max_abs", gates["legal_probability_max_abs"]),
                                  ("legal_kl", gates["legal_kl_max"])]:
                if row[metric] > limit:
                    failures.append({"id": record["id"], "metric": metric,
                                     "observed": row[metric], "limit": limit})
            # Small numerical changes can flip genuine near-ties. A move change
            # with a reference margin larger than the declared bound is a failure.
            if best != new_best and margin > 2 * gates["legal_probability_max_abs"]:
                failures.append({"id": record["id"], "metric": "top_move_flip_outside_tie_bound",
                                 "observed": margin, "limit": 2 * gates["legal_probability_max_abs"]})
        rows.append(row)
    legal = [r for r in rows if "legal_kl" in r]
    summary = {"positions": len(rows), "nonterminal_positions": len(legal),
               "raw_logit_max_abs": max(r["raw_logit_max_abs"] for r in rows),
               "legal_probability_max_abs": max(r["legal_probability_max_abs"] for r in legal),
               "legal_kl_max": max(r["legal_kl"] for r in legal),
               "legal_kl_mean": float(np.mean([r["legal_kl"] for r in legal])),
               "top_move_agreement": float(np.mean([r["top_agrees"] for r in legal])),
               "wdl_max_abs": max(r["wdl_max_abs"] for r in rows),
               "q_max_abs": max(r["q_abs"] for r in rows),
               "moves_left_max_abs": max(r["moves_left_abs"] for r in rows)}
    if enforce and failures:
        raise AssertionError(failures)
    return {"summary": summary, "per_position": rows, "gate_failures": failures}


def batch_check(records, singleton, batched, gates, enforce=True):
    maximum = 0.0
    for i, record in enumerate(records):
        board, _ = replay(record)
        if board.legal_moves.count():
            a = legal_policy(singleton[0][i], board)[1]
            b = legal_policy(batched[0][i], board)[1]
            maximum = max(maximum, float(np.max(abs(a - b))))
    checks = {"policy": maximum <= gates["batch_probability_max_abs"],
              "wdl": np.max(abs(singleton[1] - batched[1])) <= gates["wdl_max_abs"],
              "moves_left": np.all(abs(singleton[2] - batched[2]) <= gates["moves_left_atol"] + gates["moves_left_rtol"] * abs(singleton[2]))}
    failures = [name for name, passed in checks.items() if not passed]
    if enforce and failures:
        raise AssertionError(f"Batch consistency failed: {failures}")
    return {"gate_failures": failures, "legal_probability_max_abs": maximum,
            "wdl_max_abs": float(np.max(abs(singleton[1] - batched[1]))),
            "moves_left_max_abs": float(np.max(abs(singleton[2] - batched[2])))}


def develop():
    identities()
    manifest = graphs()
    gate_path = PROJECT / "environment/step5-tolerances.json"
    if gate_path.exists():
        raise RuntimeError("Gates already frozen; use verify, or explicitly version a gate change")
    protocol = {"recorded_before_development_inference_utc": now(),
                "development": "all 22 data/pilot/fixtures.jsonl; no pilot inference in develop",
                "confirmation": "all 64 data/pilot/positions.jsonl; never final experiment test data",
                "gates": INITIAL_GATES,
                "interpretation": "Per-position bounds; raw logit errors diagnostic; top flips only within 2x probability bound",
                "selection": "Conservative precision-specific starting bounds, confirmed on independent native development outputs; no tuning on pilot"}
    save(PROJECT / "environment/step5-development-protocol.json", protocol)
    records = [json.loads(line) for line in (PROJECT / "data/pilot/fixtures.jsonl").read_text().splitlines()]
    planes, native = native_reference(records)
    report = {"development_started_after_protocol_utc": now(), "results": {}}
    with tempfile.TemporaryDirectory(prefix="lc0-step5-dev-") as directory:
        for precision in MODEL_NAMES:
            runs, evidence = infer(precision, planes, [1, 4], Path(directory))
            result = compare(records, native, runs[1], INITIAL_GATES[precision])
            result["batched_vs_native"] = compare(records, native, runs[4], INITIAL_GATES[precision])
            result["batch_consistency"] = batch_check(records, runs[1], runs[4], INITIAL_GATES[precision])
            result["runtime"] = evidence
            report["results"][precision] = result
            print(precision, json.dumps(result["summary"]), flush=True)
    report["completed_at_utc"] = now()
    save(PROJECT / "environment/step5-development.json", report)
    protocol.update({"frozen_at_utc": now(), "development_passed": True,
                     "development_report_sha256": sha256(PROJECT / "environment/step5-development.json"),
                     "graphs_sha256": {p: g["sha256"] for p, g in manifest["graphs"].items()},
                     "fixtures_sha256": sha256(PROJECT / "data/pilot/fixtures.jsonl")})
    save(gate_path, protocol)
    print("Development passed; numerical gates frozen before pilot inference.", flush=True)


def selected_baseline_status(results):
    """A diagnostic failure cannot veto a different selected runtime baseline."""
    selected = {"f32": "R32_CUDA", "trt_f16": "F16_TRT"}
    statuses = {}
    for key, baseline in selected.items():
        result = results.get(key)
        statuses[baseline] = bool(result is not None and not (
            result["gate_failures"] or result["batched_vs_native"]["gate_failures"]
            or result["batch_consistency"]["gate_failures"]))
    return statuses


def verify():
    checkpoint = identities()
    manifest = graphs()
    gate_path = PROJECT / "environment/step5-tolerances.json"
    protocol = json.loads(gate_path.read_text())
    assert protocol["development_passed"]
    assert sha256(PROJECT / "environment/step5-development.json") == protocol["development_report_sha256"]
    assert sha256(PROJECT / "data/pilot/fixtures.jsonl") == protocol["fixtures_sha256"]
    assert {p: g["sha256"] for p, g in manifest["graphs"].items()} == protocol["graphs_sha256"]
    records = [json.loads(line) for line in (PROJECT / "data/pilot/positions.jsonl").read_text().splitlines()]
    planes, native = native_reference(records)
    with np.load(PROJECT / "data/pilot/inputs.npz", allow_pickle=False) as saved:
        assert np.array_equal(planes, saved["planes"])
        assert saved["ids"].tolist() == [r["id"] for r in records]
    with np.load(PROJECT / "data/pilot/native_reference.npz", allow_pickle=False) as saved:
        indices = [[r["id"] for r in records].index(key) for key in saved["ids"]]
        for key, values in zip(["logits", "wdl", "moves_left"], native):
            expected = saved[key].reshape(values[indices].shape)
            np.testing.assert_allclose(values[indices], expected, atol=1e-6, rtol=1e-6)
    report = {"pilot_started_after_tolerances_frozen_utc": now(),
              "tolerances_sha256": sha256(gate_path), "results": {}}
    output_arrays = {"ids": np.array([r["id"] for r in records])}
    for key, array in zip(["logits", "wdl", "moves_left"], native):
        output_arrays["native_" + key] = array
    with tempfile.TemporaryDirectory(prefix="lc0-step5-pilot-") as directory:
        for variant, precision, provider in [("f32", "f32", "cuda"), ("f16", "f16", "cuda"),
                                              ("trt_f16", "f16", "trt")]:
            runs, evidence = infer(precision, planes, [1, 8], Path(directory), provider=provider)
            gates = protocol["gates"][precision]
            result = compare(records, native, runs[1], gates, enforce=False)
            result["batched_vs_native"] = compare(records, native, runs[8], gates, enforce=False)
            result["batch_consistency"] = batch_check(records, runs[1], runs[8], gates, enforce=False)
            result["runtime"] = evidence
            report["results"][variant] = result
            for key, array in zip(["logits", "wdl", "moves_left"], runs[1]):
                output_arrays[variant + "_" + key] = array
            print(variant, json.dumps(result["summary"]), flush=True)
    # Also report the direct precision difference used as context for later INT8.
    report["f16_vs_f32"] = compare(records,
        [output_arrays["f32_" + key] for key in ["logits", "wdl", "moves_left"]],
        [output_arrays["f16_" + key] for key in ["logits", "wdl", "moves_left"]], protocol["gates"]["f16"], enforce=False)
    # Preserve the original 2026-10-21 evidence and its hash linkage.
    outputs_path = PROJECT / "data/pilot/step5-current-outputs.npz"
    np.savez_compressed(outputs_path, **output_arrays)
    statuses = selected_baseline_status(report["results"])
    passed = all(statuses.values())
    report["selected_baseline_numerical_status"] = statuses
    report["diagnostics_only"] = ["f16"]
    report["engine_identity_and_kernel_precision"] = "Separate 5C/5D checks required; EP registration is insufficient"
    report.update({"verified_at_utc": now(), "status": "passed" if passed else "failed", "lc0_commit": COMMIT,
                   "checkpoint_sha256": checkpoint["sha256_compressed"],
                   "export_manifest_sha256": sha256(DESTINATION / "manifest.json"),
                   "pilot_manifest_sha256": sha256(PROJECT / "data/pilot/manifest.json"),
                   "outputs_sha256": sha256(outputs_path), "script_sha256": sha256(Path(__file__)),
                   "scope": "FP32 conversion and FP16 CUDA/TensorRT numerical validation only; no INT8, tablebase or strength results; no benchmark timing or per-kernel precision audit"})
    save(PROJECT / "environment/step5-current-verification.json", report)
    print(f"Step 5 {'passed' if passed else 'FAILED'}; graphs, per-position outputs and evidence saved.", flush=True)
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["export", "develop", "verify"])
    args = parser.parse_args()
    {"export": export, "develop": develop, "verify": verify}[args.stage]()
