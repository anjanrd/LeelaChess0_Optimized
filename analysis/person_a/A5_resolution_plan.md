# A5 resolution plan

Authorized by Anjan on 29 October 2026: formulate a plan, then implement A5. Work on `anjan`; do not start autonomous Run 2.

## Objective

Complete the SmoothQuant activation illustration (F12) using measurements that belong to the selected model. Preserve the original statistics, model bytes and failed check.

## Steps and verification gates

1. **Identify the mismatch.** Compare the saved channel maxima with the current and preserved C1 model multipliers; check the collection log and backup manifest hashes. Pass only with a documented model identity and recipe for the historical measurement.
2. **Collect the selected-model diagnostic.** Run the unchanged final `models/s4.onnx` on the unchanged 512 inputs in `data/calib.npz`, CPU only, batch 32. Collect `/encoder14/ln2` and its immediate `/smoothed` output in the same pass. Save new arrays and provenance under `analysis/person_a/a5/`. Do not rebuild, recalibrate, tune or run chess/search/performance experiments. Verify source hashes before/after, finite/nonnegative 768-channel maxima and the original `rtol=1e-5, atol=1e-12` scaling check. Record provider, versions, time and exit status. Resume from verified saved arrays rather than silently rerunning inference.
3. **Generate and verify F12.** Use the final model's 101-group sidecar summary plus the new matched measured channel pair. Keep build-time derived statistics separate from measured final-model statistics and the historical alpha-0.5 example. Explain what the max/median statistic means, retain groups that worsen, and make no speed/strength inference from this plot. Export PNG/PDF/SVG and visually inspect the figure.
4. **Close the handoff.** Add regression coverage for model/statistics identity and the mismatch guard. Refresh the report, deliverable register, A5 status and Run 2 preflight note. Verify all 350 frozen source hashes, local document links and appropriate tests. Preserve `run1/blocker-A5.json` and prior verification/history; write a separate A5 closure record. Final systems results remain dependent on Ritwik. No commit or push.

## Investigation already confirmed

The original collection log records model SHA256 `574f555e5aa2d6b49e319e268a2d572c640d802399246767f1ac58c7161893ec`. This matches `reports/c1-s4-backup/s4.onnx` and its manifest. That recipe used alpha 0.5 and percentile 99.99; the final model uses alpha 0.7 and percentile 99.999. All 768 saved before/after channels match the backup multiplier exactly. All 768 fail when paired with the final model's multiplier. This is a provenance mismatch in the analysis, not evidence that the selected model's smoothing operation is broken.

Results and commands will be appended to `LOG.md`; final detailed evidence will live in `a5/provenance.json`, `a5/collection.json`, `run1/smoothquant_verification.json` and `a5/closure.json`.

## Implemented outcome

Steps 1–3 passed: historical model identity established; final-model CPU collection completed on all 512 inputs; all 768 immediate before/after checks passed with zero observed difference at the original tolerance. The final-layer peak/median channel-maximum ratio is 676,662.01 before and 1,131.17 after. Across 101 build-time groups, 100 improve and one worsens (embedding/reshape: 1 to 1.2492). F12 exports and final visual inspection passed.

Step 4 passed: 11 regression tests, 350 frozen-source hashes, 36 local document links and final figure checks. Report, register and preflight state are updated; detailed commands/results are in LOG.md and a5/closure.json. A first collection attempt stopped on the new collector's incorrect unflattened shape assertion. Read-only graph metadata established [batch*64,768]; the single permitted correction matched the imported generic channel reduction, and the retry passed. The failure record is retained. No model/protocol change was needed. A5 is complete; Run 2 was not started.
