"""Shared provenance/progress helpers for the autonomous Person A Week 1 run."""
import json
import re
from pathlib import Path

import export_step5 as base

PROJECT = base.PROJECT
RUNTIME = base.RUNTIME / "week1"
STATE = PROJECT / "environment/week1-progress.json"


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    base.save(Path(path), value)


def frozen():
    for name in ["step5-final-manifest.json", "step6-verification.json"]:
        for item in read(PROJECT / "environment" / name)["artifacts"]:
            path = PROJECT / item["relative_path"]
            assert base.sha256(path) == item["sha256"], path
    record = read(PROJECT / "environment/step5-engine.json")
    assert base.sha256(record["engine_path"]) == record["engine_sha256"]
    return record


def progress(task, status, evidence=None, detail=None):
    state = read(STATE) if STATE.exists() else {"authority": "User authorized autonomous completion of remaining Person A Week 1 tasks, verifying each before progression, on 2026-10-26", "tasks": {}}
    state["updated_at_utc"] = base.now()
    state["tasks"][task] = {"status": status, "evidence": evidence, "detail": detail}
    save(STATE, state)
    path = PROJECT / "docs/project-roadmap.md"
    text = path.read_text()
    pattern = rf"(### {re.escape(task)} -[^\n]*\n\n- \*\*Owner / priority / status:\*\* [^\n]* / )([^/\n]+)(\.)"
    text = re.sub(pattern, lambda m: m[1] + status + m[3], text, count=1)
    marker = "\n### Autonomous execution checkpoints\n"
    if marker not in text:
        text += marker + "\nThe user authorized autonomous progression through all remaining A-side Week 1 tasks on 2026-10-26. Routine scope decisions within the approved review are delegated; essential experimental acceptance decisions and required manual intervention still stop progression.\n\n"
    row = f"- **{task}: {status}**"
    entry = row + (f" - [{evidence}]({evidence.removeprefix('docs/') if evidence.startswith('docs/') else '../' + evidence})" if evidence else "") + (f". {detail}" if detail else "")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(row.split(":")[0] + ":"):
            lines[i] = entry
            break
    else:
        lines.append(entry)
    path.write_text("\n".join(lines) + "\n")


def artifact(path):
    return {"path": str(path), "sha256": base.sha256(path)}


def baseline_review_open():
    """A raw drift report stays immutable; only a matching human addendum closes it."""
    report = PROJECT / 'environment/week1-baseline-drift-review.json'
    acceptance = PROJECT / 'environment/week1-baseline-drift-acceptance.json'
    if not report.exists(): return False
    if not acceptance.exists(): return True
    record = read(acceptance)
    return not (record.get('status') == 'ACCEPTED_WITH_DRIFT'
                and record.get('explicit_user_acceptance') is True
                and record.get('review_report_sha256') == base.sha256(report)
                and record.get('engine_sha256') == read(report)['engine_identity'])


class TensorRunner:
    """Explicit saved-engine runner; PyTorch owns buffers, never network math."""
    def __init__(self, record_path):
        import torch
        import tensorrt as trt
        self.record = read(record_path)
        assert base.sha256(self.record["engine_path"]) == self.record["engine_sha256"]
        self.torch, self.trt = torch, trt
        self.logger = trt.Logger(trt.Logger.WARNING)
        self.runtime = trt.Runtime(self.logger)
        self.engine = self.runtime.deserialize_cuda_engine(Path(self.record["engine_path"]).read_bytes())
        assert self.engine is not None
        self.context = self.engine.create_execution_context()
        self.stream = torch.cuda.Stream()
        self.buffers = {}

    def prepare(self, batch):
        torch, trt = self.torch, self.trt
        assert self.context.set_input_shape("/input/planes", (batch, 112, 8, 8))
        if batch not in self.buffers:
            values = {}
            for i in range(self.engine.num_io_tensors):
                name = self.engine.get_tensor_name(i)
                dtype = torch.float16 if self.engine.get_tensor_dtype(name) == trt.float16 else torch.float32
                values[name] = torch.empty(tuple(self.context.get_tensor_shape(name)), dtype=dtype, device="cuda")
            self.buffers[batch] = values
        for name, tensor in self.buffers[batch].items():
            assert self.context.set_tensor_address(name, tensor.data_ptr())
        return self.buffers[batch]

    def run(self, planes):
        import numpy as np
        buffers = self.prepare(len(planes))
        with self.torch.cuda.stream(self.stream):
            buffers["/input/planes"].copy_(self.torch.from_numpy(np.ascontiguousarray(planes)), non_blocking=False)
            assert self.context.execute_async_v3(self.stream.cuda_stream)
        self.stream.synchronize()
        return [buffers[name].cpu().numpy().astype(np.float32) for name in base.OUTPUTS]

    def close(self):
        self.stream.synchronize()
        self.buffers.clear()
        del self.context, self.engine, self.runtime
        self.torch.cuda.empty_cache()


if __name__ == "__main__":
    RUNTIME.mkdir(parents=True, exist_ok=True)
    frozen()
    progress("W1-A06P", "IN_PROGRESS", detail="Autonomous authorization recorded; checking accepted-engine layer timings without rebuilding it.")
