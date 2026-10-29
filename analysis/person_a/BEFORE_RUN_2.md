# Reminder before autonomous Run 2

**Current workflow, 30 October 2026:** Anjan/Codex now performs remaining B work through `docs/takeover_runs.md`. This file describes the earlier A-side final-integration gate. New takeover Run2 collects R1/R2 and the pilot; it does not wait for Ritwik. Read `reports/takeover/run1/EXCLUSIVE_RUN_2.md`, prepare the quiet session, and wait for the user's explicit start. Original A readiness can remain false while those internal outputs are pending.

**A5/F12 was resolved and verified on 29 October 2026.** The user first deferred it while authorizing A6–A10, then explicitly authorized investigation and implementation.

The saved arrays belonged to the preserved C1 model (alpha 0.5), rather than the selected C2 model (alpha 0.7). Model hashes, collection history and the exact historical scaling check establish the cause. A new CPU-only diagnostic on the unchanged final model and the same 512 calibration inputs passes the original tolerance for all 768 channels. F12 uses this matched pair. The model, calibration data, quantizer and scorer were unchanged. Original arrays and `run1/blocker-A5.json` remain preserved.

Evidence: `A5_resolution_plan.md`, `a5/provenance.json`, `a5/collection.json`, `run1/smoothquant_verification.json` and `a5/closure.json`. The original Run 1 verification/output manifest describe the earlier deferred checkpoint; the A5 closure and its output manifest describe the updated state.

Before Run 2, check `run1/progress.json` and run `readiness.py`. A5 no longer needs a deferral reminder when its verified status and evidence are intact. Ritwik's R1/R2/R4/R5 handoffs and R3 final alignment still require review. Do not start Run 2 merely because A5 is complete; no Run 2 experiment is authorized by this resolution task.

Also check Ritwik's R1–R5 evidence, final systems/report inputs and GPU availability as listed in the execution plan. R3 already has raw timed results; it needs final alignment, not an automatic rerun.
