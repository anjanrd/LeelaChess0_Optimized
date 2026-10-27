"""Preserved TensorRT baseline: build once, reload, inspect, and verify.

TensorRT performs all model math. PyTorch only owns CUDA buffers/streams and
copies arrays; it does not implement any of the network layers in this runner.
Large engines, traces, and diagnostic arrays live outside the project in WSL.
"""

import argparse
import gc
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

import export_step5 as common

PROJECT = common.PROJECT
RUNTIME = common.RUNTIME
WORK = RUNTIME / "step5-preserved"
ENGINE_RECORD = PROJECT / "environment/step5-engine.json"


def progress(step, status, **evidence):
    path = PROJECT / "environment/step5-progress.json"
    record = json.loads(path.read_text())
    record["updated_at_utc"] = common.now()
    record["steps"][step] = {"status": status, **evidence}
    common.save(path, record)


def prerequisites(step):
    stages = json.loads((PROJECT / "environment/step5-progress.json").read_text())["steps"]
    for name in [f"5{x}" for x in "ABCDEFG"[:"ABCDEFG".index(step[-1])]]:
        if stages[name]["status"] != "passed":
            raise RuntimeError(f"Cannot begin {step} before {name} passes")


def build(accumulation="native", replace_candidate=False):
    prerequisites("5C")
    import torch
    import tensorrt as trt

    checkpoint = common.identities()
    graphs = common.graphs()
    assert trt.__version__ == "10.9.0.34"
    assert torch.cuda.is_available()
    WORK.mkdir(parents=True, exist_ok=True)
    torch.cuda.init()
    settings = {"workspace_bytes": 536870912, "tf32": False, "fp16": True,
                "obey_precision_constraints": accumulation == "native", "matrix_precision": "float16",
                "accumulation_request": accumulation, "strongly_typed": accumulation == "fp32",
                "normalization_compute_precision": "float32",
                "min_shape": [1, 112, 8, 8], "opt_shape": [4, 112, 8, 8],
                "max_shape": [8, 112, 8, 8], "builder_optimization_level": 3,
                "max_aux_streams": 0, "profiling_verbosity": "DETAILED"}
    if ENGINE_RECORD.exists():
        old = json.loads(ENGINE_RECORD.read_text())
        previous_settings = dict(old["settings"])
        # The first preserved candidate predates the explicit accumulator
        # fields. Its original settings/record remain immutable provenance.
        previous_settings.setdefault("accumulation_request", "native")
        previous_settings.setdefault("strongly_typed", False)
        if previous_settings != settings or old["graph_sha256"] != graphs["graphs"]["f16"]["sha256"]:
            if not replace_candidate:
                raise RuntimeError("Existing engine configuration differs; explicitly version a new candidate")
            history = PROJECT / "environment/step5-history" / old["engine_sha256"][:16] / "step5-engine.json"
            assert history.exists() and common.sha256(history) == common.sha256(ENGINE_RECORD)
            progress("5C", "pending", reason="Explicitly declared global FP32-accumulation candidate; previous engine/evidence preserved")
            progress("5D", "pending", reason="Changed engine must be traced again")
            progress("5E", "pending", reason="Changed engine must be checked on all prior development data")
            progress("5F", "pending", reason="Previous confirmation retained as failed; new candidate needs fresh confirmation")
        else:
            assert common.sha256(old["engine_path"]) == old["engine_sha256"]
            print("Reusing preserved engine:", old["engine_path"], flush=True)
            return
    logger = trt.Logger(trt.Logger.WARNING)
    builder = trt.Builder(logger)
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.STRONGLY_TYPED)
                                     if accumulation == "fp32" else 0)
    parser = trt.OnnxParser(network, logger)
    model_path = PROJECT / graphs["graphs"]["f16"]["relative_path"]
    if not parser.parse_from_file(str(model_path)):
        raise RuntimeError("\n".join(str(parser.get_error(i)) for i in range(parser.num_errors)))
    constrained, norms, layer_types = [], [], Counter()
    original_layers = [network.get_layer(i) for i in range(network.num_layers)]
    for layer in original_layers:
        layer_types[str(layer.type)] += 1
        if layer.type == trt.LayerType.MATRIX_MULTIPLY:
            if accumulation == "native":
                layer.precision = trt.float16
                layer.set_output_type(0, trt.float16)
            else:
                # Documented TensorRT cast-around-GEMM idiom: compiler may
                # fuse FP16 inputs with FP32 accumulation. Hardware trace
                # must independently confirm FP16 multiplication afterwards.
                output = layer.get_output(0)
                original_name = output.name
                users = [(consumer, i) for consumer in original_layers
                         for i in range(consumer.num_inputs) if consumer.get_input(i) == output]
                for i in [0, 1]:
                    cast = network.add_cast(layer.get_input(i), trt.float32)
                    cast.name = layer.name + f"/accumulate_fp32/input{i}"
                    layer.set_input(i, cast.get_output(0))
                cast_back = network.add_cast(output, trt.float16)
                cast_back.name = layer.name + "/accumulate_fp32/output_half"
                output.name = original_name + "/accumulated_float"
                cast_back.get_output(0).name = original_name
                for consumer, i in users:
                    consumer.set_input(i, cast_back.get_output(0))
                if output.is_network_output:
                    network.unmark_output(output)
                    network.mark_output(cast_back.get_output(0))
            constrained.append(layer.name)
        elif layer.type == trt.LayerType.NORMALIZATION:
            # get_layer returns the base ILayer wrapper in TRT's Python API.
            layer.__class__ = trt.INormalizationLayer
            layer.compute_precision = trt.float32
            norms.append(layer.name)
    assert len(constrained) == 195, len(constrained)
    config = builder.create_builder_config()
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, settings["workspace_bytes"])
    if accumulation == "native":
        config.set_flag(trt.BuilderFlag.FP16)
        config.set_flag(trt.BuilderFlag.OBEY_PRECISION_CONSTRAINTS)
    config.clear_flag(trt.BuilderFlag.TF32)
    config.profiling_verbosity = trt.ProfilingVerbosity.DETAILED
    config.builder_optimization_level = settings["builder_optimization_level"]
    config.max_aux_streams = 0
    profile = builder.create_optimization_profile()
    profile.set_shape("/input/planes", settings["min_shape"], settings["opt_shape"], settings["max_shape"])
    assert profile
    assert [list(shape) for shape in profile.get_shape("/input/planes")] == [
        settings["min_shape"], settings["opt_shape"], settings["max_shape"]]
    assert config.add_optimization_profile(profile) >= 0
    config.set_timing_cache(config.create_timing_cache(b""), ignore_mismatch=False)
    print(f"Building preserved engine: {len(constrained)} matrix layers; accumulation={accumulation}; TF32 off", flush=True)
    started = time.perf_counter()
    serialized = builder.build_serialized_network(network, config)
    if serialized is None:
        raise RuntimeError("TensorRT engine build failed")
    payload = bytes(serialized)
    import hashlib
    digest = hashlib.sha256(payload).hexdigest()
    engine_path = WORK / ("bt3-f16-" + digest[:16] + ".plan")
    engine_path.write_bytes(payload)
    assert common.sha256(engine_path) == digest
    timing_path = WORK / ("build-" + digest[:16] + ".timing")
    timing_path.write_bytes(bytes(config.get_timing_cache().serialize()))
    record = {"built_at_utc": common.now(), "build_seconds": time.perf_counter() - started,
              "baseline": "F16_TRT", "engine_path": str(engine_path), "engine_sha256": digest,
              "engine_bytes": len(payload), "settings": settings,
              "graph_sha256": graphs["graphs"]["f16"]["sha256"],
              "checkpoint_sha256": checkpoint["sha256_compressed"], "lc0_commit": common.COMMIT,
              "tensorrt": trt.__version__, "torch_for_buffers": torch.__version__,
              "cuda_runtime_for_buffers": torch.version.cuda,
              "gpu": torch.cuda.get_device_name(0), "compute_capability": list(torch.cuda.get_device_capability(0)),
              "driver": subprocess.check_output(["/usr/lib/wsl/lib/nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], text=True).strip(),
              "matrix_precision_constraints": constrained, "normalization_fp32_compute": norms,
              "parsed_layer_types": dict(layer_types), "timing_cache_path": str(timing_path),
              "timing_cache_sha256": common.sha256(timing_path), "build_script_sha256": common.sha256(Path(__file__)),
              "runtime": "TensorRT Runtime API; PyTorch only allocates/copies GPU buffers and owns the CUDA stream",
              "cache_resolution": "Controlled ORT cache failure reproduced separately; direct serialization bypasses filename ambiguity and permits explicit build precision control"}
    common.save(ENGINE_RECORD, record)
    print(f"Engine saved and fingerprinted: {engine_path} ({len(payload):,} bytes)", flush=True)


class Engine:
    def __init__(self):
        import torch
        import tensorrt as trt
        self.torch, self.trt = torch, trt
        self.record = json.loads(ENGINE_RECORD.read_text())
        assert common.sha256(self.record["engine_path"]) == self.record["engine_sha256"]
        assert trt.__version__ == self.record["tensorrt"]
        assert torch.cuda.get_device_name(0) == self.record["gpu"]
        self.logger = trt.Logger(trt.Logger.WARNING)
        torch.cuda.init()
        self.runtime = trt.Runtime(self.logger)
        self.engine = self.runtime.deserialize_cuda_engine(Path(self.record["engine_path"]).read_bytes())
        if self.engine is None:
            raise RuntimeError("Cannot deserialize preserved engine")
        self.context = self.engine.create_execution_context()
        self.stream = torch.cuda.Stream()
        assert self.engine.num_io_tensors == 4
        names = [self.engine.get_tensor_name(i) for i in range(self.engine.num_io_tensors)]
        assert set(names) == {"/input/planes", *common.OUTPUTS}
        assert all(self.engine.get_tensor_dtype(name) == trt.float16 for name in names)
        self.buffers = {}

    def prepare(self, batch):
        if batch not in self.buffers:
            assert self.context.set_input_shape("/input/planes", (batch, 112, 8, 8))
            missing = self.context.infer_shapes()
            assert not missing, missing
            tensors = {}
            for i in range(self.engine.num_io_tensors):
                name = self.engine.get_tensor_name(i)
                shape = tuple(self.context.get_tensor_shape(name))
                assert all(d > 0 for d in shape), (name, shape)
                tensors[name] = self.torch.empty(shape, dtype=self.torch.float16, device="cuda")
            self.buffers[batch] = tensors
        assert self.context.set_input_shape("/input/planes", (batch, 112, 8, 8))
        for name, tensor in self.buffers[batch].items():
            assert self.context.set_tensor_address(name, tensor.data_ptr())
        return self.buffers[batch]

    def run(self, planes):
        assert 1 <= len(planes) <= 8
        buffers = self.prepare(len(planes))
        array = np.ascontiguousarray(planes, dtype=np.float16)
        with self.torch.cuda.stream(self.stream):
            buffers["/input/planes"].copy_(self.torch.from_numpy(array), non_blocking=False)
            if not self.context.execute_async_v3(self.stream.cuda_stream):
                raise RuntimeError("TensorRT execute_async_v3 failed")
        self.stream.synchronize()
        result = [buffers[name].cpu().numpy().astype(np.float32) for name in common.OUTPUTS]
        for array, width in zip(result, [1858, 3, 1]):
            assert array.shape == (len(planes), width) and np.isfinite(array).all()
        return result

    def close(self):
        self.stream.synchronize()
        del self.context, self.engine, self.runtime
        self.buffers.clear()
        gc.collect()
        self.torch.cuda.empty_cache()


def reload_check(tag):
    prerequisites("5C")
    import torch
    WORK.mkdir(parents=True, exist_ok=True)
    with np.load(PROJECT / "data/pilot/inputs.npz", allow_pickle=False) as data:
        indices = [0, 8, 16, 24, 31, 32, 48, 56]
        planes, ids = data["planes"][indices], data["ids"][indices]
    runner = Engine()
    result = {"ids": ids}
    for batch in [1, 8]:
        first = [[], [], []]
        for start in range(0, len(planes), batch):
            a = runner.run(planes[start:start + batch])
            b = runner.run(planes[start:start + batch])
            assert all(np.array_equal(x, y) for x, y in zip(a, b)), "Same-engine repeat differed"
            for i in range(3): first[i].append(a[i])
        for name, parts in zip(["policy", "wdl", "mlh"], first):
            result[f"b{batch}_{name}"] = np.concatenate(parts)
    # Native TensorRT output retains the expected public semantics.
    for batch in [1, 8]:
        wdl = result[f"b{batch}_wdl"]
        assert np.min(wdl) >= 0 and np.max(wdl) <= 1
        assert np.max(abs(wdl.sum(axis=1) - 1)) <= 0.001
        assert np.min(result[f"b{batch}_mlh"]) >= 0
    record = runner.record
    runner.close()
    path = WORK / f"reload-{record['engine_sha256'][:16]}-{tag}.npz"
    np.savez_compressed(path, **result)
    common.save(PROJECT / f"environment/step5-reload-{tag}.json", {
        "verified_at_utc": common.now(), "pid": os.getpid(), "status": "passed",
        "engine_sha256": record["engine_sha256"], "engine_path": record["engine_path"],
        "arrays_path": str(path), "arrays_sha256": common.sha256(path),
        "batch_sizes": [1, 8], "same_process_repeats": "bit-identical",
        "finite_shapes_and_wdl_semantics": "passed", "builder_invoked": False})
    print(f"Reload {tag}: both batches and same-process repeats passed, PID={os.getpid()}", flush=True)


def finish_reload():
    prerequisites("5C")
    records = [json.loads((PROJECT / f"environment/step5-reload-{tag}.json").read_text()) for tag in ["first", "second"]]
    assert records[0]["pid"] != records[1]["pid"]
    assert records[0]["engine_sha256"] == records[1]["engine_sha256"]
    for record in records:
        assert common.sha256(record["arrays_path"]) == record["arrays_sha256"]
    with np.load(records[0]["arrays_path"], allow_pickle=False) as first, np.load(records[1]["arrays_path"], allow_pickle=False) as second:
        assert first.files == second.files
        assert all(np.array_equal(first[name], second[name]) for name in first.files), "Cross-process reload differed"
    progress("5C", "passed", evidence="environment/step5-engine.json",
             engine_sha256=records[0]["engine_sha256"],
             verification="Direct serialized engine hash checked; two fresh-process deserializations with no builder; bit-identical same-input results at each tested batch; original cache failure independently reproduced and explained")
    print("5C verified: preserved engine reloads identically in two fresh processes.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["build", "reload-check", "finish-reload"])
    parser.add_argument("--tag", choices=["first", "second"], default="first")
    parser.add_argument("--accumulation", choices=["native", "fp32"], default="native")
    parser.add_argument("--replace-candidate", action="store_true")
    args = parser.parse_args()
    {"build": lambda: build(args.accumulation, args.replace_candidate),
     "reload-check": lambda: reload_check(args.tag), "finish-reload": finish_reload}[args.stage]()
