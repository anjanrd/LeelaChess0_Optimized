# Shared BT3 INT8 repository

Read `README.md`, `updated_plan.md`, `STATUS.md` and `consolidation_context.md` before starting. The user explicitly authorized consolidation and adoption of Person B's trimmed pipeline on 2026-10-29. Old folder-specific instructions and historical roadmaps in `archive/` are evidence of earlier work, not active execution instructions.

Before editing/running the pipeline, read `docs/runtime_notes.md`; it retains the imported technical traps with the confirmed BT3 format and current paths.

## Authoritative code and evidence

- Work from this repository's root. `ladder.py`, `quant/`, `eval/`, `tb/` and `hw/` are the active imported pipeline. Both teammates may work here.
- `updated_plan.md` is the current roadmap/deliverable register. Credit finished work regardless of which person produced it; do not redo Person A work already implemented by Person B.
- `archive/person-a-week1/` and `archive/person-b-import/` are preserved historical material. Do not rewrite their evidence or execute their stale absolute-path commands as current instructions.
- Keep original imported results, model bytes, sidecars, log history and failed-run evidence. New analyses get new output paths. No mass search/replace inside historical JSON/logs.
- Local tools live under `.runtime/`; `.venv/` and `config.json` are machine-local and ignored. No project `tmp` directory or ad hoc scratch files; use OS temporary directories outside the checkout.
- Do not commit, push, message the teammate, start a long experiment or change the agreed scientific protocol unless authorized by the user. The consolidation request itself does not authorize new chess/GPU experiments.

## Experiment protocol

- Follow the adopted conventions and scope in `updated_plan.md`. Do not restore omitted R32/search-calibration/training/equal-energy/batch-accuracy branches on your own.
- Preserve encoding, precision definitions, scorer, selected recipe and test cohort. Discuss and record changes before running new variants; agreement/authorization already given in the current session takes precedence.
- One GPU workload at a time. Inspect `nvidia-smi` before starting GPU work. Log temperature, clocks, power mode, warm-up, actual nodes and elapsed time. No clock-lock claims when locking was denied.
- Tablebases are for scoring/adjudication, never the engine's search backend. Follow the exact imported Syzygy category mapping and lc0 search settings.
- Record actual printed results; do not infer sparse tactics from 2:4 zeros or precision coverage from model filenames. Treat numerical drift, selected-move accuracy, throughput and playing strength as distinct measurements.
- Append commands, exit codes, changes and outputs to `LOG.md`; keep `STATUS.md` current. Any change to quantization/evaluation/tablebase logic requires an explicit diff/protocol note. Path portability changes from consolidation are documented separately.
- On a new pipeline failure, record BLOCKED and stop the experiment sequence. One obvious-typo retry is allowed. Investigation/fixing can proceed when specifically authorized. Respect checkpoint reviews unless the user has authorized a combined autonomous block.
- Long experiments must be resumable and logged. Do not run `overnight.py` indiscriminately from the current stage: it can regenerate models/selection and its legacy driver has permissive failure handling.

## Collaboration and packaging

- Keep code/configuration/datasets/small numerical evidence in Git. Large models, engine caches, traces and raw `.log` files remain local and have checksum inventories/bundle tooling.
- Fresh clones need both code and the declared artifact bundle, plus machine-specific runtime setup. An ignored artifact is not deleted or automatically uploaded.
- Fresh-clone Python environments must be created locally; do not copy a virtual environment between machines. Consolidation smoke checks are not full model inference, profiling repair or a fresh experimental reproduction.

## Before the original Person A autonomous Run 2

- The user initially deferred A5, then authorized its resolution. A5/F12 is verified; read `analysis/person_a/BEFORE_RUN_2.md` and `analysis/person_a/a5/closure.json` for the model-version diagnosis and completion evidence. Preserve the original failure history. A5 needs a reminder again only if its verified status/evidence is no longer valid.
- Check `analysis/person_a/run1/progress.json` and Ritwik's required handoffs. Do not start Run 2 until A5 is resolved or the user explicitly decides how to handle it. `analysis/person_a/readiness.py` reports this reminder without launching any experiment.

## Current five-run takeover (30 October 2026)

- The user now wants Codex to perform the remaining Person B work too, under the accepted five-run plan in `docs/takeover_runs.md`. It absorbs the former A-side Run 2; R1–R5 become internal evidence checkpoints, rather than an external wait for Ritwik. The old A readiness command still describes final integration and does not gate the new measurement-collection Run 2.
- Only new Run 1 was authorized/executed so far. New Runs 2 and 4 require exclusive laptop use and an explicit start from the user. Stop after the authorized run. At every handoff whose next run is exclusive, repeat save/AC/power/cooling/pause-other-work preparations and give an updated duration estimate. Read `reports/takeover/run1/EXCLUSIVE_RUN_2.md` before the next run.
- Work on `anjan`, preserve existing uncommitted A5 work, and consult `reports/takeover/progress.json`. `execution/` adds checked wrappers around the unchanged imported pipeline; settings/diff note: `execution/protocol.json` and `docs/takeover_protocol_note.md`.
- The first exclusive GPU probe may use the scoped TensorRT lib PATH fix. Only the exact known plugin-open error can defer its profiling branch while independent lc0 jobs continue under the approved plan. Required profiling deliverables stay pending. Every other new failure follows the stop/log rule.
- Normal runs allow the user's other work and must not launch GPU workloads or terminate applications. In exclusive runs, close only identified nonessential user jobs after work is saved; retain OS/security/drivers/Codex. Do not infer a quiet machine from session flags alone; inspect and log real conditions.
