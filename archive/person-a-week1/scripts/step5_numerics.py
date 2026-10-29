"""Numerical diagnosis and predeclared fresh confirmation for Step 5."""

import argparse
import json
import random
import tempfile
from collections import Counter
from pathlib import Path

import chess
import numpy as np

import export_step5 as common
from lc0_inputs import BRIDGE, classical_planes, dense_planes, native_encode
from prepare_pilot import FAMILIES, group_id, sample_board
from step5_engine import Engine, PROJECT, WORK, prerequisites, progress


def checked_identities():
    common.identities()
    common.graphs()
    bridge = json.loads((PROJECT / "environment/step4-bridge.json").read_text())
    assert common.sha256(BRIDGE) == bridge["binary_sha256"]
    assert common.sha256(PROJECT / "src/native/encoder_bridge.cc") == bridge["adapter_source_sha256"]
    precision = json.loads((PROJECT / "environment/step5-precision.json").read_text())
    engine = json.loads((PROJECT / "environment/step5-engine.json").read_text())
    assert engine["engine_sha256"] == precision["F16_TRT"]["engine_sha256"]
    assert common.sha256(engine["engine_path"]) == engine["engine_sha256"]
    return engine


def evaluate(records, planes, native, label, output_path):
    gates_path = PROJECT / "environment/step5-tolerances.json"
    gates = json.loads(gates_path.read_text())["gates"]
    report = {"started_at_utc": common.now(), "positions": len(records),
              "tolerances_sha256": common.sha256(gates_path), "results": {}}
    arrays = {"ids": np.array([row["id"] for row in records])}
    for name, value in zip(["logits", "wdl", "moves_left"], native):
        arrays["native_" + name] = value
    with tempfile.TemporaryDirectory(prefix="lc0-step5-numerics-") as directory:
        f32, evidence = common.infer("f32", planes, [1, 8], Path(directory))
    r32 = {"b1_vs_native": common.compare(records, native, f32[1], gates["f32"], enforce=False),
           "b8_vs_native": common.compare(records, native, f32[8], gates["f32"], enforce=False),
           "batch_consistency": common.batch_check(records, f32[1], f32[8], gates["f32"], enforce=False),
           "runtime": evidence}
    report["results"]["R32_CUDA"] = r32
    for batch, outputs in f32.items():
        for name, value in zip(["logits", "wdl", "moves_left"], outputs):
            arrays[f"R32_CUDA_b{batch}_" + name] = value
    runner = Engine()
    f16 = {}
    for batch in [1, 8]:
        chunks = []
        for start in range(0, len(planes), batch):
            feed = planes[start:start + batch]
            first, repeated = runner.run(feed), runner.run(feed)
            assert all(np.array_equal(a, b) for a, b in zip(first, repeated)), "Saved engine repeat changed"
            chunks.append(first)
        f16[batch] = [np.concatenate([item[i] for item in chunks]) for i in range(3)]
        print(f"{label}: preserved TensorRT FP16 batch {batch} checked, including exact repeats", flush=True)
    engine_identity = runner.record["engine_sha256"]
    runner.close()
    f16_report = {"b1_vs_native": common.compare(records, native, f16[1], gates["f16"], enforce=False),
                  "b8_vs_native": common.compare(records, native, f16[8], gates["f16"], enforce=False),
                  "batch_consistency": common.batch_check(records, f16[1], f16[8], gates["f16"], enforce=False),
                  "b1_vs_R32_CUDA": common.compare(records, f32[1], f16[1], gates["f16"], enforce=False),
                  "b8_vs_R32_CUDA": common.compare(records, f32[8], f16[8], gates["f16"], enforce=False),
                  "engine_sha256": engine_identity, "same_engine_repeats": "bit-identical"}
    report["results"]["F16_TRT"] = f16_report
    for batch, outputs in f16.items():
        for name, value in zip(["logits", "wdl", "moves_left"], outputs):
            arrays[f"F16_TRT_b{batch}_" + name] = value
    failures = []
    for baseline, result in report["results"].items():
        for check, values in result.items():
            if isinstance(values, dict) and values.get("gate_failures"):
                failures.append({"baseline": baseline, "check": check, "failures": values["gate_failures"]})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, **arrays)
    report.update({"completed_at_utc": common.now(), "status": "passed" if not failures else "failed",
                   "gate_failures": failures, "outputs_path": str(output_path),
                   "outputs_sha256": common.sha256(output_path), "engine_sha256": engine_identity,
                   "script_sha256": common.sha256(__file__),
                   "scope": "Numerical conversion/precision checks only; no Syzygy accuracy or MCTS result"})
    return report


def diagnose():
    prerequisites("5E")
    engine = checked_identities()
    pilot = [json.loads(line) for line in (PROJECT / "data/pilot/positions.jsonl").read_text().splitlines()]
    fixtures = [json.loads(line) for line in (PROJECT / "data/pilot/fixtures.jsonl").read_text().splitlines()]
    old_report = json.loads((PROJECT / "environment/step5-verification.json").read_text())
    path = PROJECT / "data/pilot/onnx_reference.npz"
    assert common.sha256(path) == old_report["outputs_sha256"]
    with np.load(path, allow_pickle=False) as saved:
        assert saved["ids"].tolist() == [row["id"] for row in pilot]
        old_native = [saved["native_" + key].copy() for key in ["logits", "wdl", "moves_left"]]
    with np.load(PROJECT / "data/pilot/inputs.npz", allow_pickle=False) as saved:
        pilot_planes = saved["planes"].copy()
    fixture_planes, fixture_native = common.native_reference(fixtures)
    native = [np.concatenate([a, b]) for a, b in zip(old_native, fixture_native)]
    records, planes = pilot + fixtures, np.concatenate([pilot_planes, fixture_planes])
    if engine["settings"].get("accumulation_request") == "fp32":
        previous = PROJECT / "data/export-confirmation"
        protocol = json.loads((previous / "protocol.json").read_text())
        archived = PROJECT / "environment/step5-history" / protocol["engine_sha256"][:16] / "step5-confirmation.json"
        old_confirmation = json.loads(archived.read_text())
        assert common.sha256(previous / "outputs.npz") == old_confirmation["outputs_sha256"]
        assert common.sha256(previous / "positions.jsonl") == protocol["positions_sha256"]
        prior_rows = [json.loads(line) for line in (previous / "positions.jsonl").read_text().splitlines()]
        prior_planes = np.stack([dense_planes(item) for item in native_encode(prior_rows)])
        with np.load(previous / "outputs.npz", allow_pickle=False) as saved:
            prior_native = [saved["native_" + key].copy() for key in ["logits", "wdl", "moves_left"]]
        records += prior_rows
        planes = np.concatenate([planes, prior_planes])
        native = [np.concatenate([a, b]) for a, b in zip(native, prior_native)]
    report = evaluate(records, planes, native, "development",
                      PROJECT / f"data/pilot/step5-preserved-outputs-{engine['engine_sha256'][:16]}.npz")
    report["interpretation"] = {
        "preservation": "Same saved-engine execution and fresh-process reload are stable; this is separate from agreement with FP32",
        "remaining_precision_drift": "Differences against native/FP32 are recorded per position; no tablebase labels and no chess-strength claim",
        "historical_build_comparison": "Original weights/ONNX graph unchanged. Explicit FP16 constraints, TF32 control, runtime build configuration and selected tactics differ from the historical EP builds. Better agreement does not isolate which change caused it.",
        "accumulation": engine["settings"].get("accumulation_request", "native"),
        "candidate_selection": "Original constrained build, then at most one predeclared global FP32-accumulation revision; no selection of individual layers to fit confirmation results"}
    common.save(PROJECT / "environment/step5-diagnosis.json", report)
    if report["status"] != "passed":
        progress("5E", "needs_decision", evidence="environment/step5-diagnosis.json",
                 reason="Selected baseline still exceeds unchanged numerical bounds; no automatic relaxation")
        print(json.dumps(report["gate_failures"], indent=2), flush=True)
        raise SystemExit(1)
    progress("5E", "passed", evidence="environment/step5-diagnosis.json",
             verification=f"All {len(records)} development positions, both selected baselines, batches 1/8, exact saved-engine repeats, native parity limits and batch-consistency gates passed without changing limits")
    print("5E passed:", json.dumps({b: r["b1_vs_native"]["summary"] for b, r in report["results"].items()}), flush=True)


def prepare_confirmation(round_number=1):
    prerequisites("5F")
    engine = checked_identities()
    destination = PROJECT / ("data/export-confirmation" if round_number == 1 else f"data/export-confirmation-r{round_number}")
    protocol_path = destination / "protocol.json"
    if protocol_path.exists():
        raise RuntimeError("Confirmation already declared; do not redefine after seeing outputs")
    seed = 20261024 + round_number
    rng = random.Random(seed)
    excluded = set(json.loads((PROJECT / "data/pilot/exclusions.json").read_text())["symmetry_groups"])
    for prior_round in range(1, round_number):
        directory = PROJECT / ("data/export-confirmation" if prior_round == 1 else f"data/export-confirmation-r{prior_round}")
        excluded.update(json.loads((directory / "exclusions.json").read_text())["symmetry_groups"])
    groups, rows = set(), []
    for family, pieces in FAMILIES.items():
        for side in [chess.WHITE, chess.BLACK]:
            count = 0
            while count < 16:
                board = sample_board(rng, pieces, side)
                group = group_id(board)
                if group in excluded or group in groups:
                    continue
                groups.add(group)
                rows.append({"id": f"export-confirm-r{round_number}-{len(rows):03d}", "family": family,
                             "side_to_move": "white" if side else "black", "fen": board.fen(en_passant="fen"),
                             "moves": [], "symmetry_group": group, "tablebase_label": None,
                             "role": "step5_numerical_confirmation_only"})
                count += 1
    assert len(rows) == len(groups) == 128 and not groups.intersection(excluded)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / "positions.jsonl"
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    exclusion_path = destination / "exclusions.json"
    common.save(exclusion_path, {"symmetry_groups": sorted(groups),
                "required_use": "Final test must reject these groups in addition to data/pilot/exclusions.json"})
    common.save(protocol_path, {"declared_before_inference_utc": common.now(), "seed": seed,
        "positions": 128, "material_side_counts": dict(Counter(r["family"] + ":" + r["side_to_move"] for r in rows)),
        "positions_sha256": common.sha256(path), "exclusions_sha256": common.sha256(exclusion_path),
        "engine_sha256": engine["engine_sha256"],
        "tolerances_sha256": common.sha256(PROJECT / "environment/step5-tolerances.json"),
        "graph_manifest_sha256": common.sha256(PROJECT / "models/onnx/manifest.json"),
        "batches": [1, 8], "final_test": False,
        "scope": "Fresh numerical confirmation of the frozen build, not statistical strength evidence; never tune on confirmation results"})
    print(f"5F confirmation round {round_number} declared before inference: 128 disjoint symmetry groups, seed {seed}.", flush=True)


def confirm(round_number=1):
    prerequisites("5F")
    engine = checked_identities()
    directory = PROJECT / ("data/export-confirmation" if round_number == 1 else f"data/export-confirmation-r{round_number}")
    protocol = json.loads((directory / "protocol.json").read_text())
    assert common.sha256(directory / "positions.jsonl") == protocol["positions_sha256"]
    assert common.sha256(directory / "exclusions.json") == protocol["exclusions_sha256"]
    assert common.sha256(PROJECT / "environment/step5-tolerances.json") == protocol["tolerances_sha256"]
    assert common.sha256(PROJECT / "models/onnx/manifest.json") == protocol["graph_manifest_sha256"]
    assert engine["engine_sha256"] == protocol["engine_sha256"]
    records = [json.loads(line) for line in (directory / "positions.jsonl").read_text().splitlines()]
    encoded = native_encode(records)
    planes = np.stack([dense_planes(item) for item in encoded])
    assert np.array_equal(planes, np.stack([classical_planes(row) for row in records]))
    same_planes, native = common.native_reference(records)
    assert np.array_equal(planes, same_planes)
    report = evaluate(records, planes, native, "confirmation", directory / "outputs.npz")
    report["confirmation_protocol_sha256"] = common.sha256(directory / "protocol.json")
    common.save(PROJECT / "environment/step5-confirmation.json", report)
    if report["status"] != "passed":
        progress("5F", "needs_decision", evidence="environment/step5-confirmation.json",
                 reason="Fresh confirmation failed unchanged limits; frozen candidate not retuned")
        print(json.dumps(report["gate_failures"], indent=2), flush=True)
        raise SystemExit(1)
    progress("5F", "passed", evidence="environment/step5-confirmation.json",
             verification="Predeclared 128 fresh symmetry-disjoint positions passed original numerical and batch gates with unchanged engine and thresholds")
    print("5F passed:", json.dumps({b: r["b1_vs_native"]["summary"] for b, r in report["results"].items()}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["diagnose", "prepare-confirmation", "confirm"])
    parser.add_argument("--round", type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    {"diagnose": diagnose, "prepare-confirmation": lambda: prepare_confirmation(args.round),
     "confirm": lambda: confirm(args.round)}[args.stage]()
