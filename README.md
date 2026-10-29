# BT3 INT8 in lc0 — shared project

This repository is the unified workspace for Person A (model/analysis) and Person B (systems/experiments). The active pipeline is the former LC0-B application. Completed model/data/results are retained; earlier A-side Week 1 work is archived.

Start with [updated_plan.md](updated_plan.md) for scope, ownership and deliverables, [STATUS.md](STATUS.md) for the current checkpoint, and [consolidation_context.md](consolidation_context.md) for lineage, paths and safe continuation. Agent instructions are in [AGENTS.md](AGENTS.md); retained technical traps are in [runtime notes](docs/runtime_notes.md).

## Current position

The dense INT8 ladder, SmoothQuant, attention extension, magnitude/SparseGPT pruning, policy/value swaps and main network/fixed-node evaluations are complete. Fixed-time FP16/s4 raw runs and the reduced speed/energy batch sweep also exist. Detailed profiling is blocked by the saved TensorRT plugin-loading error; matches, final analyses, writing and reproduction remain. No new research experiment was run to consolidate the repository.

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
