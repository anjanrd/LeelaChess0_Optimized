# BT3 INT8 in lc0 — shared project

This repository is the unified workspace for Person A (model/analysis) and Person B (systems/experiments). The active pipeline is the former LC0-B application. Completed model/data/results are retained; earlier A-side Week 1 work is archived.

Start with [updated_plan.md](updated_plan.md) for scope, ownership and deliverables, [STATUS.md](STATUS.md) for the current checkpoint, and [consolidation_context.md](consolidation_context.md) for lineage, paths and safe continuation. Agent instructions are in [AGENTS.md](AGENTS.md); retained technical traps are in [runtime notes](docs/runtime_notes.md).

Person A's independent Run 1 analysis is ready: [execution handoff](person_a_execution_plan.md) and [report draft](deliverables/report/person_a_sections.md). **A5/F12 is resolved and verified**; [resolution evidence](analysis/person_a/a5/closure.json). Final systems-dependent outputs remain pending; review [Run 2 prerequisites](analysis/person_a/BEFORE_RUN_2.md).

Anjan is now completing the remaining B-side work too. The [five-run takeover](docs/takeover_runs.md) includes the former A-side Run 2. Runs 1 and 2 are complete: 35 original verified jobs plus ten verified jobs under `reports/takeover/run2/codex-continuation-v2/`, covering all 28 benchmark trials and the two-game pilot. The approved continuation records background-interference flags without stopping; other validation remains. The manual launcher was abandoned after a preserved pre-GPU PID-gate failure. Next is normal Run 3 analysis/reproduction preparation; the laptop is usable. See [current progress](reports/takeover/progress.json) and [policy note](docs/takeover_protocol_note.md).

## Current position

The dense INT8 ladder, SmoothQuant, attention extension, magnitude/SparseGPT pruning, policy/value swaps and main network/fixed-node evaluations are complete. Fixed-time FP16/s4 raw runs and the reduced batch sweep exist. The TensorRT loader is fixed; detailed profiles, ceilings, lc0 traces, all-model repeated benchmarks and runtime pilot are collected and verified. Their final interpretation, production matches, writing and fresh reproduction remain. No research experiment was run merely to consolidate the repository.

## Layout

| Location | Contents |
|---|---|
| `ladder.py`, `quant/`, `eval/`, `tb/`, `hw/` | Active pipeline and experiment code |
| `data/`, `models/`, `nets/` | Active inputs, model recipes and local binaries |
| `results/`, `reports/`, `LOG.md` | Imported raw results and evidence |
| `analysis/`, `deliverables/` | Final figure/table/report/presentation destinations |
| `archive/person-a-week1/` | Original A code, datasets, models, results and proposal/plan |
| `archive/person-b-import/` | Original B files that were edited during consolidation |
| `maintenance/`, `artifacts/` | Preservation audit and artifact-transfer tooling/inventory |
| `.runtime/`, `.venv/`, `config.json` | Local installations/environment/config, ignored by Git |

## Setup and checks

Use Python 3.11 or newer. This machine already has `.venv`, compatible local tools and `config.json`. Use the unified checkout rather than the separate Desktop/LC0-B copy.

For a fresh Windows checkout:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.json config.json
```

Edit only local tool/table paths in `config.json`. Paths resolve relative to the configuration file; `bt3` resolves relative to `work`. Bare executable names can use PATH. The shared template carries the actual selected recipe (percentile 99.999, SmoothQuant 0.7) and the completed 2,437-position cohort. A same-platform observed package lock is in `requirements/windows-prep.lock.txt`.

Install/provide lc0 v0.33.0-rc0 with its onnx-trt runtime, TensorRT 10.12/trtexec, Nsight and Syzygy 3–5-piece tables as required. Python's preparation ORT package and lc0's bundled GPU ORT are separate installations. See [RUN_4060.md](RUN_4060.md).

Large model binaries, engine caches, traces and raw log files are local artifacts, not committed source. A fresh clone also needs the research artifact bundle. On the source machine:

```powershell
.\.venv\Scripts\python.exe -B maintenance/artifacts.py verify
.\.venv\Scripts\python.exe -B maintenance/artifacts.py pack ../lc0-artifacts.zip
```

On the receiving checkout, restore with `maintenance/artifacts.py restore <bundle>` and verify. The pack command requires an output outside the checkout and refuses to overwrite an existing bundle. Runtime installations and virtual environments are excluded; create/install those locally. Consolidation did not upload or create the full-size bundle.

CPU-only repository checks:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_repository.py -v
.\.venv\Scripts\python.exe -B ladder.py --help
.\.venv\Scripts\python.exe -B overnight.py --dry-run
```

These are infrastructure checks, not fresh inference or the final experimental reproduction.

## Continuing experiments

Read the current status first. Do not replay setup, regenerate datasets/models or run the full overnight sequence to resume the current profiling stage. Historical controller scripts/configs in `reports/` contain old absolute paths; consult the relocation notes before using them. Main `ladder.py score` does not automatically consolidate nested Study C/hard-lowbudget results.

Use one GPU workload at a time, preserve imported evidence, agree scientific changes before running them, and append verified commands/results to `LOG.md`. Omitted outputs and the remaining deliverable checklist are explicit in `updated_plan.md`.
