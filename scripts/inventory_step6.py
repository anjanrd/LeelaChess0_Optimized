"""Inventory and freeze INT8 placement without quantizing or building an engine.

Run in the pinned WSL environment: inventory_step6.py inventory, then verify.
Only small, intended inventory/scope/report artifacts are written to the project.
The accepted Step 5 graphs, engines, documentation and evidence stay unchanged.
"""

import argparse
import gc
import importlib
import importlib.metadata
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import onnx

import export_step5 as common

PROJECT = common.PROJECT
INVENTORY = PROJECT / "environment/step6-inventory.json"
SCOPE = PROJECT / "environment/step6-scope.json"
VERIFICATION = PROJECT / "environment/step6-verification.json"
REPORT = PROJECT / "docs/quantization-scope.md"
BATCHES = list(range(1, 9))
MIN_DIM = 16
SOURCES = {
    "modelopt/onnx/quantization/int8.py": "https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/quantization/int8.py",
    "modelopt/onnx/quantization/graph_utils.py": "https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/quantization/graph_utils.py",
    "modelopt/onnx/quantization/ort_utils.py": "https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/quantization/ort_utils.py",
    "modelopt/onnx/quantization/ort_patching.py": "https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/quantization/ort_patching.py",
    "modelopt/onnx/autocast/convert.py": "https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/autocast/convert.py",
    "onnxruntime/quantization/operators/matmul.py": "https://github.com/microsoft/onnxruntime/blob/v1.22.0/onnxruntime/python/tools/quantization/operators/matmul.py",
}


def read(path):
    import json
    return json.loads(Path(path).read_text())


def prerequisites():
    manifest_path = PROJECT / "environment/step5-final-manifest.json"
    manifest = read(manifest_path)
    assert manifest["status"] == "complete_with_documented_drift"
    for item in manifest["artifacts"]:
        assert common.sha256(PROJECT / item["relative_path"]) == item["sha256"], item["relative_path"]
    ledger = read(PROJECT / "environment/step5-progress.json")
    assert all(ledger["steps"]["5" + stage]["status"] == "passed" for stage in "ABCDEFG")
    assert read(PROJECT / "environment/step5-confirmation.json")["status"] == "failed"
    graph_manifest = read(PROJECT / "models/onnx/manifest.json")
    for graph in graph_manifest["graphs"].values():
        assert common.sha256(PROJECT / graph["relative_path"]) == graph["sha256"]
    return common.sha256(manifest_path), graph_manifest


def structure(model):
    return {
        "nodes": [(n.name, n.op_type, n.domain, list(n.input), list(n.output),
                   [a.SerializeToString().hex() for a in n.attribute]) for n in model.graph.node],
        "initializers": [(i.name, list(i.dims)) for i in model.graph.initializer],
        "opsets": [(o.domain, o.version) for o in model.opset_import],
    }


def shape_map(model):
    result = {}
    for value in list(model.graph.input) + list(model.graph.value_info) + list(model.graph.output):
        result[value.name] = [d.dim_value if d.HasField("dim_value") else d.dim_param or "?"
                              for d in value.type.tensor_type.shape.dim]
    result.update({i.name: list(i.dims) for i in model.graph.initializer})
    return result


def geometry(a, b, output):
    assert len(a) >= 2 and len(b) >= 2
    assert all(isinstance(d, int) and d > 0 for d in a + b + output), (a, b, output)
    m, k, n = a[-2], a[-1], b[-1]
    assert k == b[-2]
    # Independently derive broadcast dimensions and check ONNX's output shape.
    prefix = []
    for x, y in zip(reversed(a[:-2]), reversed(b[:-2])):
        assert x == y or x == 1 or y == 1
        prefix.append(max(x, y))
    longest = a[:-2] if len(a) >= len(b) else b[:-2]
    prefix = list(longest[:len(longest) - len(prefix)]) + list(reversed(prefix))
    assert output == prefix + [m, n], (a, b, output)
    macs = math.prod(output) * k
    assert macs == math.prod(prefix) * m * k * n
    return {"a": a, "b": b, "output": output, "M": m, "K": k, "N": n,
            "macs": macs, "geometry_excluded": m == 1 or n == 1 or k < MIN_DIM or n < MIN_DIM}


def region(name):
    match = re.match(r"/encoder(\d+)/", name)
    if match:
        return "encoder" + match[1]
    return name.split("/")[1]


def scan(model):
    names = [n.name for n in model.graph.node]
    assert len(names) == len(set(names)) and all(names)
    counts = Counter(n.op_type for n in model.graph.node)
    assert counts["MatMul"] == 195 and counts["Gemm"] == 0 and len(names) == 762
    assert counts["QuantizeLinear"] == counts["DequantizeLinear"] == 0
    initializers = {i.name: i for i in model.graph.initializer}
    consumers = defaultdict(list)
    for node in model.graph.node:
        for index, name in enumerate(node.input):
            consumers[name].append({"node": node.name, "input_index": index, "op_type": node.op_type})
    matrices = [n for n in model.graph.node if n.op_type == "MatMul"]
    rows = []
    for index, node in enumerate(matrices):
        assert len(node.input) == 2 and node.input[0] not in initializers
        weight = initializers.get(node.input[1])
        if weight is not None:
            assert len(weight.dims) == 2
        rows.append({"index": index, "name": node.name, "op_type": node.op_type,
            "region": region(node.name), "inputs": list(node.input), "output": node.output[0],
            "kind": "activation_times_weight" if weight is not None else "activation_times_activation",
            "weight": None if weight is None else {
                "name": weight.name, "shape": list(weight.dims), "parameters": math.prod(weight.dims),
                "dtype": onnx.TensorProto.DataType.Name(weight.data_type), "output_channel_axis": 1,
                "consumers": consumers[weight.name]},
            "activation_consumers": consumers[node.input[0]], "shapes_by_batch": {}})
    for batch in BATCHES:
        model.graph.input[0].type.tensor_type.shape.dim[0].dim_value = batch
        inferred = onnx.shape_inference.infer_shapes(model, strict_mode=True, data_prop=True)
        shapes = shape_map(inferred)
        for row in rows:
            row["shapes_by_batch"][str(batch)] = geometry(
                shapes[row["inputs"][0]], shapes[row["inputs"][1]], shapes[row["output"]])
        del inferred
    for row in rows:
        vector_batches = [b for b in BATCHES if row["shapes_by_batch"][str(b)]["M"] == 1
                          or row["shapes_by_batch"][str(b)]["N"] == 1]
        small_batches = [b for b in BATCHES if row["shapes_by_batch"][str(b)]["K"] < MIN_DIM
                         or row["shapes_by_batch"][str(b)]["N"] < MIN_DIM]
        row["exclusion_reasons"] = []
        if row["weight"] is None:
            row["exclusion_reasons"].append("dynamic_operands_outside_common_weight_quantization_scope")
        if vector_batches:
            row["exclusion_reasons"].append("vector_at_one_or_more_supported_batches")
        if small_batches:
            row["exclusion_reasons"].append("K_or_N_below_ModelOpt_16_dimension_heuristic")
        row["selected"] = not row["exclusion_reasons"]
        assert all(row["shapes_by_batch"][str(b)]["macs"] == b * row["shapes_by_batch"]["1"]["macs"] for b in BATCHES)
    return rows, dict(counts), consumers


def tool_evidence():
    assert importlib.metadata.version("nvidia-modelopt") == "0.47.0"
    assert importlib.metadata.version("onnxruntime-gpu") == "1.22.0"
    root = Path(importlib.util.find_spec("modelopt").origin).parent.parent
    evidence = [{"path": str(root / path), "sha256": common.sha256(root / path), "url": url}
                for path, url in SOURCES.items()]
    int8_source = (root / "modelopt/onnx/quantization/int8.py").read_text()
    assert "per_channel=True" in int8_source
    assert "per_channel=False" in (root / "modelopt/onnx/quantization/ort_patching.py").read_text()
    assert "_MIN_MATMUL_DIM = 16" in (root / "modelopt/onnx/quantization/graph_utils.py").read_text()
    assert "base_min_opset = 22 if low_precision_type == \"bf16\" else 19" in (root / "modelopt/onnx/autocast/convert.py").read_text()
    schemas = {}
    for version in [17, 19]:
        schema = onnx.defs.get_schema("QuantizeLinear", version)
        schemas[str(version)] = {"schema_since_version": schema.since_version,
            "input_types": next(list(t.allowed_type_strs) for t in schema.type_constraints if t.type_param_str == "T1")}
    assert "tensor(float16)" not in schemas["17"]["input_types"]
    assert "tensor(float16)" in schemas["19"]["input_types"]
    return evidence, schemas


def inventory():
    assert not INVENTORY.exists() and not SCOPE.exists(), "Existing scope is frozen: version an explicit amendment"
    previous_hash, graphs = prerequisites()
    original = onnx.load(PROJECT / graphs["graphs"]["f16"]["relative_path"])
    onnx.checker.check_model(original, full_check=True)
    reference_structure = structure(original)
    rows, counts, consumers = scan(original)
    del original
    gc.collect()
    fp32 = onnx.load(PROJECT / graphs["graphs"]["f32"]["relative_path"])
    assert structure(fp32) == reference_structure, "Floating graphs have different operator structure"
    del fp32, reference_structure
    gc.collect()
    sources, schemas = tool_evidence()
    # Cross-check against the installed tool's own shape-based selection, without
    # calibration, quantization, inference or an engine build.
    from modelopt.onnx.quantization.graph_utils import find_nodes_from_matmul_to_exclude
    comparisons = {}
    for batch in [1, 4, 8]:
        actual = sorted(find_nodes_from_matmul_to_exclude(
            str(PROJECT / graphs["graphs"]["f16"]["relative_path"]),
            calibration_shapes={"/input/planes": [batch, 112, 8, 8]}))
        expected = sorted(r["name"] for r in rows if r["shapes_by_batch"][str(batch)]["geometry_excluded"])
        assert actual == expected, (batch, actual, expected)
        comparisons[str(batch)] = {"status": "passed", "excluded_nodes": actual}
    selected = [r for r in rows if r["selected"]]
    excluded = [r for r in rows if not r["selected"]]
    assert len(selected) == 127 and len(excluded) == 68
    total_macs = sum(r["shapes_by_batch"]["1"]["macs"] for r in rows)
    selected_macs = sum(r["shapes_by_batch"]["1"]["macs"] for r in selected)
    weights = {r["weight"]["name"]: r["weight"] for r in selected}
    coverage = {"selected_matrices": len(selected), "total_matrices": len(rows),
        "dynamic_matrices_excluded": sum(r["weight"] is None for r in excluded),
        "weighted_matrices_excluded": sum(r["weight"] is not None for r in excluded),
        "unique_selected_weight_tensors": len(weights),
        "unique_selected_weight_parameters": sum(w["parameters"] for w in weights.values()),
        "matrix_macs_per_position": total_macs, "selected_matrix_macs_per_position": selected_macs,
        "selected_matrix_mac_fraction": selected_macs / total_macs,
        "interpretation": "Unfused ONNX arithmetic estimate, excludes nonmatrix work; not measured INT8 coverage, runtime share or speedup"}
    payload = {"generated_at_utc": common.now(), "status": "inventory_complete",
        "step5_manifest_sha256": previous_hash, "graphs": graphs["graphs"], "operator_counts": counts,
        "shape_batches_checked": BATCHES, "floating_graph_structure_equal": True,
        "modelopt_geometry_crosscheck": comparisons, "tool_sources": sources,
        "quantize_linear_schemas": schemas, "coverage": coverage, "matrix_operations": rows}
    # Keep inventory small: export command logs already belong to the frozen Step 5 manifest.
    payload["graphs"] = {k: {key: graph[key] for key in ["relative_path", "sha256", "opset", "ir_version"]}
                         for k, graph in graphs["graphs"].items()}
    scope = {"version": "1.0", "recorded_at_utc": common.now(), "status": "frozen_intended_placement",
        "authority": "User authorized Codex to complete Step 6; architecture/tool rules selected before INT8 results",
        "inventory_sha256": None, "source_graph_sha256": graphs["graphs"]["f16"]["sha256"],
        "profile": {"min_batch": 1, "opt_batch": 4, "max_batch": 8},
        "selection_rule": "MatMul with a fixed rank-2 RHS weight, M/N > 1 and K/N >= 16 at every batch 1..8",
        "rationale": "Common weight-based ladder; follow pinned ModelOpt geometry heuristics conservatively across the entire profile, independent of calibration batch or numerical/chess results",
        "geometry_warning": "A tool performance heuristic is not a statement that excluded dimensions are physically unsupported",
        "selected_nodes": [r["name"] for r in selected],
        "excluded_matrix_nodes": [{"name": r["name"], "reasons": r["exclusion_reasons"]} for r in excluded],
        "modelopt_exact_name_patterns": ["^" + re.escape(r["name"]) + "$" for r in selected],
        "op_types_to_quantize": ["MatMul"],
        "nonmatrix_policy": "No explicit INT8 placement on biases, residual Adds, normalization, softmax, Mish or layout/index operations. Floating graph semantics retained; internal fusion/precision must be disclosed in Step 7.",
        "weight_scaling": {"I1": "per-tensor signed symmetric INT8", "I2_and_later": "per-output-channel signed symmetric INT8, RHS axis 1"},
        "activation_scaling": "Per-tensor signed symmetric INT8; never per-channel activation scales for this TensorRT recipe",
        "I1_calibration": "Max-absolute ranges from legal pilot positions; provisional pilot, later datasets and manifests separate",
        "tool_adapter": "ModelOpt 0.47.0 int8.quantize hardcodes per_channel=True. Step 7 must explicitly use its lower-level quantize_static path or a recorded process-local adapter with per_channel=False for I1; never edit site-packages or silently call I2 the naive I1.",
        "opset_bridge": {"original": 17, "required_for_fp16_qdq": 19,
            "action_in_step7": "Create and validate an unquantized opset-19 bridge from the same FP16 weights before Q/DQ insertion. Preserve node mapping, tensors, metadata and reference outputs; full checker and numerical bridge checks are mandatory. Apply changes consistently to derived compared graphs; never silently replace/rebuild the accepted Step 5 engine.",
            "failure_rule": "Unexpected graph, baseline execution or numerical changes require investigation and a versioned decision before comparative claims"},
        "shared_tensor_rule": "Shared activation consumers and tied weights must retain equivalent floating computation before quantization; compensate every affected consumer or explicitly clone a branch/weight. Never smooth a shared tensor in place while leaving other consumers uncompensated.",
        "change_control": "Same named matrix targets across the dense ladder. Any backend-required coverage amendment is versioned before variant comparisons; no silent fallback, per-batch placement changes or accuracy-driven layer exclusions.",
        "coverage": coverage, "actual_INT8_execution": "not yet verified; Step 7",
        "step7_requirements": ["Validate the opset bridge and output conventions", "Audit exact Q/DQ placement, scalar I1 weight scales, zero points and floating exclusions",
            "Verify selected matrix multiplication really uses INT8 Tensor Core execution, recording fused/layer coverage and fallbacks",
            "Preserve engine identity/reload results and disclose calibration inputs, batch/profile, conversion overhead and numerical differences"],
        "step7_started": False}
    common.save(INVENTORY, payload)
    scope["inventory_sha256"] = common.sha256(INVENTORY)
    common.save(SCOPE, scope)
    assert prerequisites()[0] == previous_hash
    print(f"Inventory complete: {len(selected)}/195 selected; {100 * selected_macs / total_macs:.4f}% of matrix MACs. Run verify before progression.", flush=True)


def report_text(inventory, scope):
    coverage = scope["coverage"]
    all_weights = {r["weight"]["name"]: r["weight"]["parameters"]
                   for r in inventory["matrix_operations"] if r["weight"]}
    total_weight_parameters = sum(all_weights.values())
    groups = defaultdict(lambda: [0, 0, 0])
    for row in inventory["matrix_operations"]:
        group = "15 encoder blocks" if row["region"].startswith("encoder") else row["region"]
        groups[group][0] += 1
        groups[group][1] += int(row["selected"])
        groups[group][2] += row["shapes_by_batch"]["1"]["macs"] if row["selected"] else 0
    lines = ["# Step 6: intended INT8 scope", "", "Status: **Step 6 complete and verified. Step 7 has not started.**", "",
        "## Objective and intuition", "",
        "Choose exactly which calculations the dense INT8 variants will change. Keep that placement fixed so differences between techniques can be interpreted. This step inventories the graph; actual INT8 execution is a Step 7 gate.", "",
        "## Frozen placement v1.0", "",
        f"Select **127 of 195 MatMul operations**, representing **{100 * coverage['selected_matrix_mac_fraction']:.4f}% of estimated matrix MACs**. There are no Gemm nodes. Shapes were resolved for every batch from 1 through 8. FP32 and FP16 exports have identical node connectivity, attributes and initializer dimensions.", "",
        "Select an operation only when its second input is a fixed rank-2 learned weight, M/N exceed 1, and K/N are at least 16 throughout the batch profile. The geometry rule follows the pinned ModelOpt heuristic. It is a performance choice, not a universal hardware-support restriction. Exclude the union across batches, rather than letting the calibration batch change coverage.", "",
        "| Region | Matrix operations | INT8 targets | Target MACs per position |", "| --- | ---: | ---: | ---: |"]
    lines += [f"| {name} | {values[0]} | {values[1]} | {values[2]:,} |" for name, values in groups.items()]
    lines += ["", "The 68 excluded matrix operations comprise 31 activation-by-activation attention/policy products and 37 weighted operations that fail the profile-wide vector/small-dimension rule. The larger fixed-weight scope includes Q/K/V and output projections, FFNs, smolgen compression/shared weight generation, and eligible embedding/policy/value projections.", "",
        f"The graph has {coverage['matrix_macs_per_position']:,} matrix multiply-accumulates per position, of which {coverage['selected_matrix_macs_per_position']:,} are targeted. These are unfused arithmetic counts, excluding elementwise/layout work. They do not establish runtime coverage or a speedup.", "",
        "Normalization, softmax, Mish, biases, residual additions and indexing/layout operations receive no explicit INT8 placement. Retain their floating graph semantics. TensorRT may fuse work; report actual execution and floating precision exceptions later.", "",
        "## Controlled variants and shared tensors", "",
        "I1 uses symmetric signed INT8 weights with one scale per weight tensor, per-tensor activation scales and max calibration. I2 changes only weight granularity to per-output-channel scaling, RHS axis 1. Subsequent dense variants retain these named targets unless a versioned coverage amendment is made before comparisons.", "",
        f"There are {coverage['unique_selected_weight_tensors']} unique selected weight tensors with {coverage['unique_selected_weight_parameters']:,} parameters, out of {len(all_weights)} unique matrix-weight tensors with {total_weight_parameters:,} parameters ({100 * coverage['unique_selected_weight_parameters'] / total_weight_parameters:.2f}% of matrix-weight elements). Several excluded vector operations have large weight matrices. The 97% arithmetic coverage therefore does not imply that 97% of weights, storage, memory traffic or runtime become INT8. Engine storage is a separate measurement.", "",
        "In particular, `/const/smolgen_w` is shared by all 15 encoder blocks. The inventory records every selected activation/weight consumer. SmoothQuant or any algebraic transformation must compensate all affected consumers, or explicitly clone a branch/weight; an uncompensated shared residual/attention consumer would change the floating model before quantization.", "",
        "## Tool constraints to handle in Step 7", "",
        "1. ModelOpt 0.47.0's INT8 entry point hardcodes per-channel weights. Use its lower-level static quantizer or a recorded process-local adapter to request per-tensor I1 weights, then audit scale shapes. Leave installed packages unchanged. [Pinned INT8 source](https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/quantization/int8.py#L274).", "",
        "2. ONNX opset 17 QuantizeLinear does not accept FP16 input/scales; opset 19 does. ModelOpt's FP16 converter enforces at least 19. Validate an unquantized bridge from the same FP16 weights before inserting Q/DQ, preserving node mapping and output semantics. Keep the accepted Step 5 engine and evidence intact. Changes in execution/numerics are a gate, not permission to accept a different baseline silently. [ONNX schema](https://onnx.ai/onnx/operators/onnx__QuantizeLinear.html#quantizelinear-19), [pinned converter](https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/autocast/convert.py#L253).", "",
        "3. Check the exact named targets after preprocessing and Q/DQ insertion. Confirm scalar I1 weight scales, signed zero points, per-tensor activations and unchanged floating exclusions. Explicit selection bypasses some defaults, but the tool can still apply exclusions. [Pinned geometry/selection source](https://github.com/NVIDIA/Model-Optimizer/blob/0.47.0/modelopt/onnx/quantization/graph_utils.py#L1094).", "",
        "4. A Q/DQ graph is not hardware proof. Build/reload and inspect/profile the INT8 engine in Step 7. Record actual INT8 Tensor Core matrix execution, compiler fusion, conversion boundaries and any fallback. A backend-required placement change needs an explicit scope version before comparisons.", "",
        "## Verification and reproduction", "",
        "The installed ModelOpt geometry exclusion helper was executed without calibration/inference at batches 1, 4 and 8 and matched the independent inventory exactly: 37 exclusions at batch 1, four at batches 4/8. Broadcast/M/K/N arithmetic, full matrix coverage, exact-name patterns, tied weights, source hashes and the unchanged Step 5 frozen artifacts were checked. No chess positions or INT8 results informed selection.", "",
        "Machine-readable artifacts: `environment/step6-inventory.json`, `environment/step6-scope.json`, and `environment/step6-verification.json`. The verification record hashes this report, the script, the scope and the inventory. No graph conversion, quantization, calibration or engine build was performed.", "",
        "In the activated pinned WSL environment, run:", "", "```bash",
        "OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 python scripts/inventory_step6.py verify", "```", "",
        "The initial `inventory` command refuses to overwrite an existing frozen scope. Version changes deliberately instead of silently regenerating placement.", ""]
    return "\n".join(lines)


def verify():
    prior_hash, graphs = prerequisites()
    inventory_record, scope = read(INVENTORY), read(SCOPE)
    assert scope["inventory_sha256"] == common.sha256(INVENTORY)
    assert inventory_record["step5_manifest_sha256"] == prior_hash
    assert scope["source_graph_sha256"] == graphs["graphs"]["f16"]["sha256"]
    for source in inventory_record["tool_sources"]:
        assert common.sha256(source["path"]) == source["sha256"]
    model = onnx.load(PROJECT / graphs["graphs"]["f16"]["relative_path"])
    matrices = {n.name: n for n in model.graph.node if n.op_type in {"MatMul", "Gemm"}}
    rows = inventory_record["matrix_operations"]
    assert set(matrices) == {r["name"] for r in rows} and len(rows) == 195
    assert dict(Counter(n.op_type for n in model.graph.node)) == inventory_record["operator_counts"]
    inits = {i.name: i for i in model.graph.initializer}
    selected = set(scope["selected_nodes"])
    excluded = {r["name"] for r in scope["excluded_matrix_nodes"]}
    assert len(selected) == 127 and len(excluded) == 68
    assert not selected & excluded and selected | excluded == set(matrices)
    assert scope["coverage"] == inventory_record["coverage"]
    all_macs = sum(r["shapes_by_batch"]["1"]["macs"] for r in rows)
    target_macs = sum(r["shapes_by_batch"]["1"]["macs"] for r in rows if r["name"] in selected)
    assert scope["coverage"]["matrix_macs_per_position"] == all_macs
    assert scope["coverage"]["selected_matrix_macs_per_position"] == target_macs
    assert scope["coverage"]["selected_matrix_mac_fraction"] == target_macs / all_macs
    patterns = scope["modelopt_exact_name_patterns"]
    assert len(patterns) == len(selected)
    assert {name for name in (n.name for n in model.graph.node) if any(re.match(p, name) for p in patterns)} == selected
    for row in rows:
        node = matrices[row["name"]]
        assert row["inputs"] == list(node.input) and row["output"] == node.output[0]
        assert row["selected"] == (row["name"] in selected)
        assert row["selected"] == (row["weight"] is not None and all(
            not geometry(**{"a": s["a"], "b": s["b"], "output": s["output"]})["geometry_excluded"]
            for s in row["shapes_by_batch"].values()))
        if row["weight"]:
            assert row["weight"]["shape"] == list(inits[node.input[1]].dims)
        for batch, entry in row["shapes_by_batch"].items():
            assert entry == geometry(entry["a"], entry["b"], entry["output"])
            assert entry["macs"] == int(batch) * row["shapes_by_batch"]["1"]["macs"]
    # Re-infer both endpoints from the untouched graph, rather than trusting
    # recorded shape rows or count-only comparisons.
    for batch in [1, 8]:
        model.graph.input[0].type.tensor_type.shape.dim[0].dim_value = batch
        inferred = onnx.shape_inference.infer_shapes(model, strict_mode=True, data_prop=True)
        shapes = shape_map(inferred)
        for row in rows:
            actual = geometry(shapes[row["inputs"][0]], shapes[row["inputs"][1]], shapes[row["output"]])
            assert actual == row["shapes_by_batch"][str(batch)]
        del inferred
    for encoder in range(15):
        block = [r for r in rows if r["region"] == f"encoder{encoder}"]
        assert len(block) == 12 and sum(r["selected"] for r in block) == 8
    tied = [r for r in rows if r["weight"] and r["weight"]["name"] == "/const/smolgen_w"]
    assert len(tied) == 15 and all(r["selected"] and len(r["weight"]["consumers"]) == 15 for r in tied)
    assert all(c["status"] == "passed" for c in inventory_record["modelopt_geometry_crosscheck"].values())
    assert not scope["step7_started"]
    common_text = report_text(inventory_record, scope)
    REPORT.write_text(common_text)
    assert prerequisites()[0] == prior_hash
    artifacts = [INVENTORY, SCOPE, REPORT, Path(__file__).resolve()]
    record = {"verified_at_utc": common.now(), "status": "passed", "scope_version": scope["version"],
        "step5_frozen_manifest_sha256": prior_hash, "step5_artifacts_unchanged": True,
        "checks": ["All 195 named matrix operations accounted for; no missing or duplicate targets",
            "Both original floating graphs match structurally; model hashes unchanged",
            "Exact shapes for all batches 1..8; endpoints independently re-inferred",
            "Broadcast/output and two independent MAC formulas agree",
            "Installed ModelOpt geometry exclusions match at batches 1/4/8",
            "127 selected nodes and 68 explicit exclusions partition the matrix graph",
            "Anchored quantizer patterns select exactly the intended names",
            "15 encoder blocks have consistent placement; shared smolgen weights accounted for",
            "Pinned tool source hashes and FP16 Q/DQ schema constraints verified"],
        "coverage": scope["coverage"], "artifacts": [{"relative_path": str(p.relative_to(PROJECT)),
            "sha256": common.sha256(p)} for p in artifacts],
        "execution_limit": "Intended placement only; no actual INT8 execution or accuracy/performance claim",
        "step7_started": False}
    common.save(VERIFICATION, record)
    print("Step 6 verified and frozen. Step 7 has not started.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["inventory", "verify"])
    args = parser.parse_args()
    {"inventory": inventory, "verify": verify}[args.stage]()
