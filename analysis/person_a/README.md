# Person A analysis workspace

Execution script: `run1.py`; outputs and progress: `run1/`; plots: `../figures/`; publication CSVs: `../tables/`. Work is on `anjan` and derives from the frozen consolidation evidence.

The user authorized Run 1 in one autonomous block, initially deferred A5 while resuming A6–A10, then authorized A5 resolution. The original failure is preserved at `run1/blocker-A5.json`. **A5/F12 is now verified; read BEFORE_RUN_2.md and validate Ritwik's handoffs before Run 2.** Details: `A5_resolution_plan.md`, `a5/provenance.json`, `a5/collection.json` and `run1/smoothquant_verification.json`.

A1–A4 reproduce/cohort-check existing accuracy and swaps. A5 verifies model/statistics identities and generates the selected-model F12; collection is an explicit CPU-only diagnostic on existing calibration inputs. A6 audits sparse masks and quality. A7 verifies the active graph geometry and prepares roofline work. A8 creates matched timed review, eight-model frontier quality and the legal opening-book review. A9 writes the evidence-linked draft and references. A10 prepares the retained-deliverable checklist, slide/demo and fresh-reproduction plans. Final measured R1/R2/R4/R5 conclusions wait for B; R3 already has raw data and needs canonical alignment.

Normal reproduction commands use `.venv/Scripts/python.exe -B analysis/person_a/run1.py <step>` sequentially. Do not rerun finished steps just to refresh timestamps. A5 reuses verified arrays; `smoothquant_diagnostic.py verify` checks their identities. Explicit `collect` reuses an existing verified collection and refuses incompatible/incomplete files. Historical evidence, numerical/scorer logic and the scientific protocol remain unchanged.

`run1/source_manifest.json` records frozen inputs; the original `run1/verification.json` describes the earlier A5-deferred checkpoint. The subsequent `a5/closure.json` records A5 verification and the current output inventory. A complete independent block does not mean the entire project or C4 is complete.
