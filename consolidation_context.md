# Consolidation context and handoff

29 October 2026. Shared repository: `C:\Users\HP\Desktop\LC0`.

Read this document together with [updated_plan.md](updated_plan.md), [README.md](README.md), [STATUS.md](STATUS.md) and [AGENTS.md](AGENTS.md). The plan is authoritative for scientific scope and responsibilities; this file explains repository structure, lineage and safe continuation.

Current continuation (30 October): new Runs1–3 are complete; see [Run3 analysis](analysis/person_a/run3_findings.md) and [exclusive Run4 handoff](reports/takeover/run3/EXCLUSIVE_RUN_4.md). The clean reproduction clone/environment/artifact subset lives outside the checkout in `%LOCALAPPDATA%/LC0-BT3-Reproduction/run4-eb9e8cf`. Same-host GPU reproduction and production matches remain pending. Historical consolidation and Run2 records below retain their original checkpoint meaning.

## 1. What was authorized and what changed

The user accepted Person B's conventions, pipeline, rules and trimmed plan as the basis for all future work, then authorized consolidating both workspaces and creating a revised plan/deliverable register. The consolidation preserves completed work instead of replaying Week 1 or rebuilding models.

The existing Git repository and history were retained. The former `LC0-B/leela-int8` application is now the active root application. Person A's earlier Week 1 project lives under `archive/person-a-week1/`. Local Windows dependencies live under `.runtime/`, and the reusable local Python environment is at `.venv/`.

No commit, push, message to the teammate, new chess evaluation, model rebuild, quantization/calibration change or GPU benchmark was authorized by this consolidation task. No original imported file was intentionally discarded. Files needing active edits have a preserved original copy; the preservation manifest records where to find it.

## 2. Current layout

```text
LC0/                              existing shared Git root
  README.md                       entry point and setup
  updated_plan.md                 current week-wise plan + deliverable register
  consolidation_context.md        this handoff
  AGENTS.md                       current agent/workflow instructions
  STATUS.md                       concise current progress and blocker
  LOG.md                          original B log + appended consolidation record
  RUN_4060.md                     current machine operation notes
  docs/runtime_notes.md            retained technical traps with corrected format assumptions
  config.example.json             shared frozen recipe; relative tool paths
  config.json                     local copy, ignored by Git
  requirements.txt                imported preparation dependencies
  requirements/windows-prep.lock.txt  versions observed in this Python environment
  ladder.py / overnight.py        active orchestrators
  common.py / modal_app.py        helpers; Modal remains optional/untested here
  quant/                          QDQ, smoothing, pruning, wrapping, swaps, encoder
  eval/                           UCI driver, scoring, raw/node/time studies, match
  tb/                             Syzygy-labelled root generation
  hw/                             benchmarks, NVML, batch sweep, profiles, roofline
  tests/                          imported fixtures + repository regression checks
  data/                           authoritative B root set and calibration/dev arrays
  models/                         B models + recipe sidecars; large binaries local
  nets/                           source BT3 checkpoint, local binary
  results/                        original B raw measurements
  reports/                        original B scores, configs, logs, captures and state
  analysis/tables/                 destination for final publication tables
  analysis/figures/                destination for final publication figures
  deliverables/                    report/presentation/demo/checklist destinations
  artifacts/manifest.json          checksum inventory for transferable research artifacts
  maintenance/                    artifact transfer and preservation metadata
  archive/person-a-week1/          original A code/data/docs/results/models
  archive/person-b-import/         original B files that active consolidation changed
  .runtime/tools/                 local lc0, TensorRT, Nsight and engine caches
  .runtime/syzygy/                 local 3–5-piece table files
  .runtime/imported-cache/         preserved old generated Python caches
  .venv/                          local preparation Python environment
```

Directories for future outputs contain short READMEs so they survive a clone. Their presence is not evidence that the planned report/figures have been produced.

## 3. Exact relocation rules

| Before, relative to the old Git root | Now | Meaning |
|---|---|---|
| `data/`, `models/`, `results/` | `archive/person-a-week1/<same path>` | A's old datasets, models and results; historical, not active inputs. |
| `docs/`, `environment/`, `requirements/`, `scripts/`, `src/` | `archive/person-a-week1/<same path>` | A's original documentation, manifests and WSL/Python implementation. |
| `Leela_INT8_Proposal.pdf`, `plan.pdf` | `archive/person-a-week1/<same filename>` | Original reference documents. |
| `LC0-B/leela-int8/<path>` | `<path>` at repository root | B's implementation, data, models and experiment evidence become active. |
| `LC0-B/tools/`, `LC0-B/syzygy/` | `.runtime/tools/`, `.runtime/syzygy/` | Local dependencies, ignored by Git. |
| `LC0-B/.venv/` | `.venv/` | Local environment; activation/launcher repair is infrastructure only. |
| `LC0-B/AGENTS.md` | `archive/person-b-import/AGENTS.md` | Historical instructions. Root `AGENTS.md` now governs the shared project. |
| B README, run guide, status, log, configs, `.gitignore`, `ladder.py`, `overnight.py` | originals also in `archive/person-b-import/` | Preserve exact imported originals before editing active versions. |
| Imported `__pycache__` directories | `.runtime/imported-cache/<original relative path>` | Reproducible caches retained outside active source. |

`maintenance/consolidation-manifest.json` gives the source, preserved destination, bytes and SHA256 for every original file, including local installations. `maintenance/consolidation-verification.json` records the final preservation/check results. These are migration evidence, not the final scientific reproducibility audit.

The independent directory `C:\Users\HP\Desktop\LC0-B` was not changed. It is a pre-consolidation copy, not a second active workspace. Both teammates should use the unified checkout going forward. Do not mix results newly generated there into this repository without recording their provenance.

The external WSL runtime at `/home/anjanrd/.local/share/lc0-int8` was not changed or imported. It contains historical A-side engines/builds. Those are distinct from the current Windows pipeline and are not a fresh-clone dependency of the adopted plan.

The local environment's activation scripts and 12 installed entry-point launchers were refreshed for the unified path without reinstalling scientific packages. Their original bytes and original `pyvenv.cfg` remain under `.runtime/imported-environment-scripts/`, and the preservation manifest points to those copies. Create a new environment on another computer rather than transferring this one.

## 4. Which code and scientific rules are active

Use root `quant/`, `eval/`, `tb/`, `hw/` and `ladder.py`. Do not merge A's older ModelOpt runner into this quantizer or combine datasets because filenames look similar.

The accepted active comparison is wrapped FP16 versus INT8 through lc0 `onnx-trt`. FP16 is `optimize=6`, INT8 is `optimize=8`. The raw BT3 checkpoint through the same backend checks wrapping and provides a reference; it is not an independent CUDA-native speed baseline. A's R32_CUDA/F16_TRT direct-runner results remain useful historical evidence but are not additional mandatory experimental branches.

The source BT3 checkpoint was reused from A; B generated its own root corpus/calibration, ONNX, QDQ models and engines. Do not call their ONNX/INT8 artifacts identical to A's even though they share the checkpoint. B quantizes 164 fixed-weight matmuls; `s4aa` also quantizes 31 dynamic matmuls. The accepted imported scope is used without reconstructing A's 160-target recipe.

| Model name | Actual identity |
|---|---|
| `fp16` | Wrapped FP32 ONNX, runtime allowed to execute in FP16 through TensorRT. |
| `s1` | Naive signed per-tensor W8A8 minmax PTQ. |
| `s2` | Per-channel weight PTQ. |
| `s3` | Per-channel + selected percentile 99.999 calibration. |
| `s4` | s3 + SmoothQuant alpha 0.7; selected best dense PTQ. |
| `s4aa` | Best recipe plus dynamic attention matmuls. |
| `s0` | Magnitude 2:4 pruning before quantization with the best recipe. |
| `s1sp` | Sequential SparseGPT 2:4 before best-recipe quantization. This is not the naive `s1`. |
| `swap_pol8` / `swap_val8` | Policy/value supplied by different bodies; accuracy-only probes. |

SmoothQuant inserts explicit compensating Mul nodes because a shared LayerNorm output also feeds a residual branch. It is not the original plan's unrestricted LayerNorm folding. Sparse masks show a pruning pattern, not proof of sparse Tensor Core execution. The kernel-name precision classifier is a heuristic. Final layer/sparse audits remain pending.

Python's installed ONNX Runtime 1.31.1 is the **CPU preparation/selection** package. The GPU runtime inside the imported Windows lc0 is its bundled **ONNX Runtime 1.22.1**, with TensorRT 10.12. Do not mistake the Python package version for the lc0 GPU provider version or replace lc0's runtime DLLs as a routine dependency update.

## 5. Evidence already in hand and how to read it

- `reports/C1-done.md`: day-1/wrapping/runtime gate.
- `reports/C2-recipe-choice.json`, `select_s3_dev.txt`, `select_s4_dev.txt`: development-set selection; best=s4.
- `reports/C2-build-manifest.json`: original hashes for nine model variants. Its absolute paths are historical; the files now live in root `models/`.
- `reports/scores_test.md` and `.json`: completed main Study A/B numerical tables, including sparse models and swaps.
- `reports/hard/`: existing 43-position subset and its standard-budget scores.
- `results/hard_lowbudget/`: completed 10/25/50/100/200-node follow-up for six dense models; needs a consolidated supplemental report.
- `results/s0_search/`: supplemental magnitude-pruning search measurements, not the standard all-model sweep.
- `results/studyc/`: completed 200/800 ms FP16/s4 runs on the selected common cohort, plus preserved extra historical FP16 rows.
- `reports/c3_hw/bench/`: latest ordinary throughput/GPU-energy measurements for fp16/s4/raw-checkpoint reference.
- `reports/c3_hw/batch_sweep/`: completed four-point sweep, CSV, JSON and PNG.
- `reports/trt/s2_lc0*`: early INT8 execution capture; not a complete per-model layer audit.
- `reports/c3_hw/trt/fp16_trtexec.log`: failed detailed profiler build.
- `reports/c3-part1/state.json`: last experiment controller BLOCKED at detailed profiling. Old PIDs are historical, not proof that a job is live.

Main Study A/B uses 2,437 test roots. FP16 and s4 each choose a preserving raw move on 2,431; both reach 2,437 at the larger requested node budgets. This leaves little room for tablebase-accuracy gains. The SparseGPT result is weaker, while magnitude pruning is substantially worse; these are completed negative findings.

Read `raw accuracy` as the score of the chosen move against external tablebase labels, not the neural value head's W/D/L percentages. Study A's KL uses rounded printed priors; value error and move correctness answer different questions. Fixed-node requested budgets overshoot, so retain actual-node statistics. Fixed-time runs can stop early; nominal time is not actual time.

There is a known small symmetry-related cross-split overlap from the earlier review: three positions in the measured cohort overlap a calibration/development symmetry group. Preserve the original corpus and results. Final integrity closure must document the impact or make a separately versioned sensitivity report; consolidation does not silently remove roots or retune anything.

## 6. Historical paths and resumability

Original JSON sidecars, controller state, UCI metadata, logs and archived source keep old absolute paths. This preserves the actual provenance and original hashes. A path in those files is not the current executable path.

For B references, map both `C:\Users\HP\Desktop\LC0-B\leela-int8\<path>` and `C:\Users\HP\Desktop\LC0\LC0-B\leela-int8\<path>` to this root's `<path>`. Map old B `tools`/`syzygy` paths to `.runtime/`. For A references within the old checkout, add `archive/person-a-week1/`. External WSL paths retain their historical meaning.

Do **not** run `reports/c2_*.py`, `reports/c3_*.py`, prepared PowerShell files or old `reports/c3-part1/config.*.json` verbatim: they are saved operational history with the old checkout paths. Their completed keys/raw results remain preserved, but controller-script continuation needs a newly reviewed root-relative command/config.

`ladder.py score` addresses the ordinary `results/<model>/` layout. It does not automatically consolidate nested `results/studyc/` or `results/hard_lowbudget/`. Likewise, a plain `ladder.py studyc` uses its normal output root, not the imported special Study C directory. Before resuming any experiment, choose the intended output path and matching completed IDs explicitly to avoid duplicate measurements.

The shared template sets Study C limit to 2,437, matching the actually completed resized run. The imported base config had a stale limit of zero; the original snapshot remains archived. Recipe, study budgets, minibatch, scoring, match configuration and model bytes were not changed by this administrative alignment.

The detailed profiler's saved blocker is `Unable to open library: nvinfer_plugin_10.dll`. Runtime files were relocated, but no TensorRT build was retried and the blocker is not marked resolved by this consolidation. Do not launch the whole overnight sequence as a repair attempt.

## 7. Working together from here

1. Both people use this same Git project and the same reviewed recipe. Follow the repository's existing branch/review practice; consolidation did not create a commit or push anything.
2. Person A owns model interpretation/figures, matched outlier analysis, roofline operation counts and model/report sections. The teammate's finished quantization/pruning/swaps count as completed A work.
3. Person B owns runtime/profiling repair, comparable model benchmarks, sparse hardware evidence, matched timed reporting and paired matches.
4. Coordinate a single GPU owner on this device before launches. CPU-only analysis can proceed independently. Keep outputs in distinct named analysis/run paths; do not overwrite imported results.
5. Changes to recipe, cohort, scoring, encoding, precision definitions or search conditions need agreement and a versioned record. A new trial must not silently replace the frozen evidence.
6. Record execution commands/results in `LOG.md`, update `STATUS.md` and the relevant `updated_plan.md` row after verification, then observe the agreed checkpoint protocol.
7. Finish C3 experiments before final C4 writing/package freeze. Omitted F8/F10 and training branches are not waiting tasks.

## 8. Git versus local artifacts

The repository retains code, docs, the labelled data/calibration arrays, model recipe sidecars, raw JSONL measurements, score tables, small configuration snapshots and manifests in Git-visible paths. Large model binaries, engine caches, captures, raw `.log` files, runtime installations, `.venv/` and local `config.json` are ignored, not deleted. Existing A tracked evidence is preserved under the archive.

The reorganization was initially left uncommitted; the user subsequently authorized publication as `consolidation 1 29th Oct`, with `main`, `anjan` and `ritwik` sharing that starting commit. Git can represent moved A paths as deletions/additions or detected renames; their contents are preserved and checksum-verified. All 217 previously tracked A files other than the deliberately revised root `.gitignore` have Git-visible archive counterparts. Two existing output arrays larger than 50 MB remain part of that historical tracked evidence; new model/tool binaries are ignored. Use `anjan` and `ritwik` for the respective teammates' subsequent work and review changes into `main`.

`artifacts/manifest.json` inventories the transferable research trees: models, checkpoint, data, results, reports and archived A model binaries. `maintenance/artifacts.py` can verify, package and restore those trees without replacing a teammate's different file. It excludes Windows tool installations, virtual environments and external WSL files. This file-based transfer is local; nothing is uploaded automatically.

On the source machine, using an existing directory outside the checkout:

```powershell
.\.venv\Scripts\python.exe -B maintenance/artifacts.py verify
.\.venv\Scripts\python.exe -B maintenance/artifacts.py pack ../lc0-artifacts.zip
```

`pack` creates a new ZIP64 bundle and refuses to overwrite an existing bundle. It can be large; the command is supplied for a handoff and was not run against all research artifacts during consolidation. Share the bundle through your chosen storage separately from Git. After changing/adding scientific outputs, explicitly refresh the manifest with `inventory` and review its diff before sharing.

On a fresh checkout, create a fresh Python environment and install `requirements.txt` or the same-platform observed lock, then:

```powershell
.\.venv\Scripts\python.exe -B maintenance/artifacts.py restore ../lc0-artifacts.zip
Copy-Item config.example.json config.json
# Edit config.json for this machine; install/provide compatible lc0/TRT/Syzygy separately.
.\.venv\Scripts\python.exe -B maintenance/artifacts.py verify
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_repository.py -v
```

Restore checks hashes and refuses to overwrite differing existing files. Engine caches depend on GPU/runtime and may need rebuilding locally; rebuilding is not the same as changing ONNX weights or recalibrating the model. A Git clone without the large artifacts is a code/data checkout, not a complete ready-to-benchmark installation.

## 9. What consolidation verification does and does not establish

Completed checks: all **10,722 original files (23,406,412,244 bytes)** match their preserved SHA256 values; all **328 transferable artifacts (8,588,237,031 bytes)** verify; **six repository regression tests** pass; **28 active Python files** parse; configured tool/checkpoint/table paths exist; local dependency and activation/launcher checks pass. Re-running the scorer into an OS temporary directory exactly reproduced the main/hard Markdown and JSON reports plus hard IDs (**five outputs**). Temporary verification files stayed outside the checkout. Only tiny test artifact bundles were created, outside the project, and removed with their temporary directories.

These checks do not count as fresh model inference, full encoder revalidation, GPU precision profiling, sparse tactic verification, match execution or experimental reproduction from a clean machine. Those remain assigned in `updated_plan.md`.

The earlier A frozen evidence manifest may contain LF hashes while files in the imported Windows checkout have CRLF. Its historical strict byte-hash verifier also assumes the former root/WSL layout. Do not rewrite that manifest to make it pass after migration. The consolidation manifest records the actual pre-move bytes and new archive paths separately.

## 10. First continuation point

The model ladder, main accuracy studies, SparseGPT and swaps are already implemented. Start with the current status and the specific next authorized task, not Week 1 setup. Remaining experiment work is the profiling blocker, sparse/comparable/repeated hardware measurements, matched timed/hard reporting and matches. Then produce final figures/report/presentation/demo, package/reproduce and check off every retained deliverable in the updated plan.


## 11. Person A Run 1 continuation

At the original Run 1 checkpoint (subsequently committed as `7f9bacc`), the independent block had executed on anjan after consolidation. A1–A4 and the independent portions of A6–A10 were verified/prepared; five figures had PNG/PDF/SVG exports. The user deferred A5 after its diagnostic consistency failure and authorized the A6 continuation. The original `analysis/person_a/run1/verification.json` and output manifest preserve that checkpoint, including its deferred A5 status. The Run 1 task itself did not commit/push. Current A5 completion is recorded below.

## 12. A5 resolution and current continuation point

Anjan subsequently authorized planning and implementation of A5. The earlier channel arrays came from preserved C1 s4 (alpha0.5, percentile99.99), as established by collection-log/backup model hashes and exact agreement for all 768 channels. The final selected C2 s4 uses alpha0.7/percentile99.999. The failed analysis had mixed these model versions; model corruption or broken smoothing is not indicated.

The new `analysis/person_a/smoothquant_diagnostic.py` collects both sides of the final model's same Mul using the unchanged 512 calibration inputs, CPU only. New small arrays, source identities and collection context live under `analysis/person_a/a5/`; the old arrays/model bytes and `run1/blocker-A5.json` remain unchanged. The final measured pair passes the original tolerance, with zero observed difference. F12 now includes the selected-model 101-group build summary (100 improve; one worsens) and the separate measured layer example. CSVs, findings and report explain these contexts. No quantization/evaluation/tablebase logic or scientific protocol changed; no GPU/chess/search/performance experiment was run.

Current verification/output inventory: `analysis/person_a/a5/closure.json` and `analysis/person_a/a5/output_manifest.json`. Current handoff: `person_a_execution_plan.md`; run `analysis/person_a/readiness.py` to review dependencies. A5 no longer requires a deferral reminder. R1/R2/R4/R5 still await Ritwik; R3 raw analysis needs canonical final alignment. Final shared delivery, experimental reproduction and Run 2 remain pending. This resolution task did not commit, push or message Ritwik.

## 13. Five-run takeover and new normal Run 1

On 30 October2026 Anjan chose to complete Ritwik's remaining work here too. The accepted five-run sequence in `docs/takeover_runs.md` absorbs the original A-side Run2; external R1–R5 handoffs become outputs produced/reviewed in this workspace. Only new normal Run1 was authorized so far. New exclusive Runs2/4 must be explicitly started after a preparation reminder and duration estimate.

New code under `execution/` wraps the unchanged imported pipeline with checked benchmark data, atomic match/game+PGN journals, model/settings/source contracts, a sequential resumable controller, child-only TensorRT PATH and native Windows/NVML activity monitoring. `execution/protocol.json` and `docs/takeover_protocol_note.md` document operating points/procedural additions and their limits. Actual Game/scorer/quantizer and all350 frozen original files are unchanged. Existing uncommitted A5 work is preserved.

Preparation evidence lives in `reports/takeover/run1/`; current five-run status is `reports/takeover/progress.json`. The final45-job command/input manifest is `run1/run2_jobs.json`; its earlier CPU-only draft is preserved separately.40 offline tests pass, including original score reproduction, fake-command resumption/failure handling, real CPU-only Windows/PE observations and synthetic match-clock/journal checks. No engine/profiler, GPU benchmark, match, model inference, app termination, global PATH/power change, commit or push ran in new Run1.

The SDK plugin exists and the scoped CPU child PATH check passes, but actual GPU loading remains unverified. Initial exclusive Run2 estimate is3–7hours; reserve up to8hours for cold compilation. Read its handoff before beginning. A repeated exact plugin-load error can defer only that branch; profiling-dependent retained deliverables remain open. Original A5 manifests are historical checkpoints; the new takeover verification/inventory describe current preparation.

## 14. Run 2 completion under the approved continuation policy

Run 2 is now collected and verified on anjan:35 original verified jobs plus ten jobs
under `reports/takeover/run2/codex-continuation-v2/`, covering all45 planned jobs,
28 benchmark trials and the two-game pilot. The continuation manifest links the original
manifest/state and records its own sources/session/policy. The original state remains a
lineage checkpoint, not the combined completion record; use `reports/takeover/progress.json`.
The original resource-flagged attempt and manual launch's pre-GPU PID-gate failure are
preserved. The user explicitly abandoned manual launching and approved Codex orchestration
with background flags informational; activity/AC/exit/output/identity checks remain.
Model bytes, scientific settings and original execution code are unchanged. Normal Run3
analysis/reproduction preparation is next; production matches are Run4. No new experiment
was launched merely to consolidate, and no commit/push or teammate message occurred here.
