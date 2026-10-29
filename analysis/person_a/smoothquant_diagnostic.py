"""Version-matched A5 diagnostics; CPU collection is a separate explicit command.

Never edits a model/calibration artifact. Small new outputs live in a5/.
The historical pair remains evidence for C1, not for the selected C2 model.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import onnx
from onnx import numpy_helper

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "analysis/person_a/a5"
TENSOR = "/encoder14/ln2"
RTOL, ATOL = 1e-5, 1e-12
CURRENT = "models/s4.onnx"
HISTORICAL = "reports/c1-s4-backup/s4.onnx"
SAVED = "reports/C2-ln2-channel-maxima.npz"
COLLECTED = "analysis/person_a/a5/current-channel-maxima.npz"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def write(path, obj):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def identity(path):
    p = ROOT / path
    with p.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    return {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": digest}


def inverse(path):
    model = onnx.load(ROOT / path)
    nodes = [n for n in model.graph.node if n.name == TENSOR + "/smooth"]
    assert len(nodes) == 1 and nodes[0].op_type == "Mul"
    assert list(nodes[0].input) == [TENSOR, TENSOR + "/smooth_inv"]
    assert list(nodes[0].output) == [TENSOR + "/smoothed"]
    return numpy_helper.to_array(next(t for t in model.graph.initializer
                                     if t.name == TENSOR + "/smooth_inv")).copy()


def pair_check(before, after, inv):
    """Check actual matched channel maxima, without changing the failed tolerance."""
    before, after, inv = map(np.asarray, (before, after, inv))
    assert before.shape == after.shape == inv.shape == (768,), "Expected 768 channels"
    assert all(np.isfinite(v).all() for v in (before, after, inv)), "Nonfinite channels"
    assert (before >= 0).all() and (after >= 0).all() and (inv > 0).all(), "Invalid ranges/scales"
    expected = before * inv
    error = np.abs(expected.astype(np.float64) - after.astype(np.float64))
    tolerance = ATOL + RTOL * np.abs(after.astype(np.float64))
    return {"agrees": bool(np.all(error <= tolerance)), "channels": len(before),
            "failed_channels": int(np.count_nonzero(error > tolerance)),
            "max_absolute_error": float(error.max()),
            "max_relative_error": float((error / np.maximum(np.abs(after), ATOL)).max()),
            "rtol": RTOL, "atol": ATOL}


def load_arrays(path):
    with np.load(ROOT / path, allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}


def diagnose():
    saved = load_arrays(SAVED)
    old_id, current_id = identity(HISTORICAL), identity(CURRENT)
    manifest = read("reports/c1-s4-backup/manifest.json")
    assert any(r["sha256"] == old_id["sha256"] and r["bytes"] == old_id["bytes"] for r in manifest)
    witness = "Graph unchanged SHA256: models/s4.onnx " + old_id["sha256"]
    assert witness in (ROOT / "LOG.md").read_text(encoding="utf-8-sig")
    historical = pair_check(saved["s4_raw"], saved["s4_smoothed"], inverse(HISTORICAL))
    current = pair_check(saved["s4_raw"], saved["s4_smoothed"], inverse(CURRENT))
    assert historical["agrees"] and not current["agrees"], "Diagnosis changed; investigate provenance"
    keys = ("smoothquant", "percentile", "method", "granularity", "n_calib")
    old_side = read("reports/c1-s4-backup/s4.json")
    side = read("models/s4.json")
    result = {"status": "verified provenance mismatch", "saved_statistics": identity(SAVED),
              "historical_model": old_id, "selected_model": current_id,
              "historical_recipe": {k: old_side[k] for k in keys},
              "selected_recipe": {k: side[k] for k in keys},
              "collection_log_witness": witness,
              "backup_manifest": identity("reports/c1-s4-backup/manifest.json"),
              "historical_pair_check": historical, "wrong_current_pair_check": current,
              "resolution": "Preserve historical pair; collect selected model on the same frozen calibration inputs."}
    write(OUT / "provenance.json", result)
    return result


def validate_current():
    record = read(OUT / "collection.json")
    assert record["status"] == "verified"
    assert record["providers"] == ["CPUExecutionProvider"]
    assert record["calibration_positions"] == 512 and record["batch_size"] == 32
    for item in record["sources"] + [record["output"]]:
        assert identity(item["path"]) == item, "Diagnostic source/output identity changed: " + item["path"]
    a = load_arrays(COLLECTED)
    assert set(a) == {"s4_raw", "s4_smoothed", "smooth_inverse"}
    inv = inverse(CURRENT)
    assert np.array_equal(a["smooth_inverse"], inv), "Saved statistics use another model's multiplier"
    checked = pair_check(a["s4_raw"], a["s4_smoothed"], inv)
    assert checked["agrees"], "Current matched pair failed original tolerance"
    assert checked == record["pair_check"]
    return a, record


def collect_current():
    if (ROOT / COLLECTED).exists() or (OUT / "collection.json").exists():
        _, record = validate_current()
        print("Reusing verified selected-model diagnostic; no inference repeated.", flush=True)
        return record
    from common import INPUT, ort_session
    from quant.quantize import BATCH, batches, load_planes, with_outputs
    import onnxruntime as ort

    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() == "anjan"
    sources = [identity(p) for p in (CURRENT, "models/s4.json", "data/calib.npz",
                                    "quant/quantize.py", "common.py", "analysis/person_a/smoothquant_diagnostic.py")]
    planes = load_planes(ROOT / "data/calib.npz")
    assert planes.shape == (512, 112, 8, 8) and np.isfinite(planes).all()
    assert BATCH == 32
    names = [TENSOR, TENSOR + "/smoothed"]
    model = onnx.load(ROOT / CURRENT)
    inv = inverse(CURRENT)
    session = ort_session(with_outputs(model, names), cpu=True)
    assert session.get_providers() == ["CPUExecutionProvider"]
    maxima = {}
    start = time.perf_counter()
    batch_pair_max_error = 0.0
    for i, xb in enumerate(batches(planes)):
        before, after = session.run(names, {INPUT: xb})
        # This export flattens batch and square axes: [batch * 64, 768].
        # Reduce every non-channel axis, as the imported collector does.
        assert before.shape == after.shape and before.shape[-1] == 768
        assert before.size == len(xb) * 64 * 768
        assert np.isfinite(before).all() and np.isfinite(after).all()
        assert np.allclose(before * inv, after, rtol=RTOL, atol=ATOL), "Per-batch Mul mismatch"
        batch_pair_max_error = max(batch_pair_max_error, float(np.abs(before * inv - after).max()))
        for name, value in zip(("s4_raw", "s4_smoothed"), (before, after)):
            a = np.abs(value).max(axis=tuple(range(value.ndim - 1)))
            maxima[name] = np.maximum(maxima[name], a) if name in maxima else a
        if (i + 1) % 4 == 0:
            print(f"CPU diagnostic: {(i + 1) * BATCH}/512 inputs collected", flush=True)
    elapsed = time.perf_counter() - start
    assert all(identity(item["path"]) == item for item in sources), "Source changed during collection"
    checked = pair_check(maxima["s4_raw"], maxima["s4_smoothed"], inv)
    assert checked["agrees"]
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(ROOT / COLLECTED, **maxima, smooth_inverse=inv)
    record = {"status": "verified", "sources": sources, "output": identity(COLLECTED),
              "providers": session.get_providers(), "onnxruntime": ort.__version__,
              "onnx": onnx.__version__, "numpy": np.__version__,
              "calibration_positions": len(planes), "batch_size": BATCH,
              "tensors": names, "observed_last_batch_tensor_shape": list(before.shape),
              "channel_axis": -1, "reduce_axes": ["positions", "tokens"],
              "collection_elapsed_seconds": elapsed, "batch_pair_max_absolute_error": batch_pair_max_error,
              "pair_check": checked, "model_modified": False, "gpu_workload": False,
              "scope": "CPU activation diagnostic, not GPU runtime precision, latency, search or accuracy measurement"}
    write(OUT / "collection.json", record)
    validate_current()
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["diagnose", "collect", "verify"])
    action = ap.parse_args().action
    try:
        if action == "diagnose":
            result = diagnose()
        elif action == "collect":
            result = collect_current()
        else:
            _, result = validate_current()
    except Exception as exc:
        write(OUT / (action + "-failure.json"), {"status": "BLOCKED", "error": repr(exc)})
        raise
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
