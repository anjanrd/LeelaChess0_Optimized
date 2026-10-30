# Fresh reproduction and packaging procedure - current preparation

**New Runs1-3 are complete.** Fresh source/Python/subset preparation is verified; actual GPU reproduction awaits exclusive Run4 and final full packaging/C4 awaits Run5. This remains distinct from repository smoke tests.

1. Freeze source revision, model/recipe hashes, labelled root/cohort IDs, calibration/development inputs, scorer, runtime/backend versions and final system conditions. Preserve original evidence and failed-run records.
2. Create a clean checkout and a fresh local Python environment; install compatible runtime tools separately. Restore a verified artifact bundle using maintenance/artifacts.py. Do not copy the old virtual environment or assume TensorRT engine portability.
3. Reproduce a declared, deterministic subset containing **FP16, best PTQ s4 and the selected sparse path (s1sp or the final agreed sparse variant)**. Record exact IDs, budget/batch settings, input/history convention, commands and success tolerances before execution. These are execution checks of frozen variants, not a new selection experiment.
4. Check model loading/encoding/output routing, selected-move scoring, numerical agreement with the appropriate reference and runtime precision where required. Record any GPU-specific engine rebuild. Actual profiling/performance checks use the frozen B procedure and one GPU job at a time.
5. A documented sparse-runtime limitation can be an honest outcome, but an unperformed required dense check is not a pass. Do not replace experimental reproduction with parsing old score JSONs or six repository tests.
6. Regenerate A tables/figures from immutable saved evidence in new output paths and compare them with declared tolerances; review captions and source identities. For F12, verify/reuse the version-matched arrays in analysis/person_a/a5/; do not pair C1 measurements with the final C2 graph or silently recollect inputs.
7. Audit every final report/slide number and citation. Reconcile paired match results, systems tables, retained deliverables and omitted F8/F10. Generate final artifact inventory/package only after the freeze; verify its hashes and a receiving-side restore.
8. Record the fresh setup, commands, outputs, runtime limitations and final checklist sign-off. Render/review the final report/deck and complete the real demo before C4.

This procedure is ready for execution after inputs/conditions are finalized. Original Run 1 collected no fresh inference. The subsequent A5 closure collected a bounded CPU activation diagnostic only; fresh experimental/GPU reproduction and a full-size bundle remain unperformed.

## Prepared implementation after normal Run 3

The clean clone, independently installed21-pin Python environment and758MB verified reproduction subset are ready under `%LOCALAPPDATA%/LC0-BT3-Reproduction/run4-eb9e8cf`. Source commit eb9e8cf remains tracked-clean; the check driver is a declared external hashed overlay. Existing same-host native tools and possible driver caches are reused, so this is not cross-machine/native-tool installation validation or a guaranteed cold engine build. No old Python environment or serialized engine cache was copied.

The32 IDs, value/policy tolerances, raw-outcome comparison, speed review band and exact job order are frozen in reports/takeover/run3/reproduction-contract.json and run4-manifest.json. CPU imports and package/artifact/source checks passed; actual GPU reproduction is pending exclusive Run4 before production match. Historical idle-energy subtraction remains provisional; the prepared controlled diagnostic can inform the final limitation but cannot retroactively validate every old baseline. Full final research bundle/restore/C4 remain Run5.
