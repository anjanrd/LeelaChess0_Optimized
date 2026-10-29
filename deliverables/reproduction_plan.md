# Fresh reproduction and packaging procedure — prepared, not executed

**Before autonomous Run 2: address A5**, then validate Ritwik's R1–R5 handoffs and the final model/configuration identities. The final reproduction is distinct from the existing repository and artifact-transfer tests.

1. Freeze source revision, model/recipe hashes, labelled root/cohort IDs, calibration/development inputs, scorer, runtime/backend versions and final system conditions. Preserve original evidence and failed-run records.
2. Create a clean checkout and a fresh local Python environment; install compatible runtime tools separately. Restore a verified artifact bundle using maintenance/artifacts.py. Do not copy the old virtual environment or assume TensorRT engine portability.
3. Reproduce a declared, deterministic subset containing **FP16, best PTQ s4 and the selected sparse path (s1sp or the final agreed sparse variant)**. Record exact IDs, budget/batch settings, input/history convention, commands and success tolerances before execution. These are execution checks of frozen variants, not a new selection experiment.
4. Check model loading/encoding/output routing, selected-move scoring, numerical agreement with the appropriate reference and runtime precision where required. Record any GPU-specific engine rebuild. Actual profiling/performance checks use the frozen B procedure and one GPU job at a time.
5. A documented sparse-runtime limitation can be an honest outcome, but an unperformed required dense check is not a pass. Do not replace experimental reproduction with parsing old score JSONs or six repository tests.
6. Regenerate A tables/figures from immutable saved evidence in new output paths and compare them with declared tolerances; review captions and source identities. Keep F12 unfinished until A5 is resolved or explicitly handled by the user.
7. Audit every final report/slide number and citation. Reconcile paired match results, systems tables, retained deliverables and omitted F8/F10. Generate final artifact inventory/package only after the freeze; verify its hashes and a receiving-side restore.
8. Record the fresh setup, commands, outputs, runtime limitations and final checklist sign-off. Render/review the final report/deck and complete the real demo before C4.

This procedure is ready for execution after inputs/conditions are finalized. No fresh model inference, GPU reproduction or full-size bundle was created during this Run 1 block.
