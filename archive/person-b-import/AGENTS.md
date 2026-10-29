# Rules for this folder (Leela INT8 pipeline, Person B work)

Read README.md and RUN_4060.md first. The README's "Traps" list is binding: do not work around it.

Scope
- Write only inside this folder. C:\Users\HP\Desktop\LC0 and the WSL env under /home/anjanrd/.local/share/lc0-int8 are Anjan's frozen run: read-only. Reuse his installs (lc0 build, TensorRT, checkpoint, Syzygy) by path; don't re-download if one works.
- No git commit or push. No config or code change to quant/, eval/ or tb/ logic without logging the diff in LOG.md.
- One GPU job at a time. Run nvidia-smi first; if the GPU is busy, wait.

Evidence
- Never state a number you did not see printed by a command. No estimates, no "should be".
- Append to LOG.md after every step: time, exact command, exit code, the key output lines (paste them), and the path of any file produced.
- Keep STATUS.md as a table: gate/step, state (todo / running / done / BLOCKED), one-line result.

Stop rules
- On the first failure: write BLOCKED plus the error to STATUS.md and stop. Do not try alternative fixes beyond one retry of an obvious typo.
- After each checkpoint below, write "CHECKPOINT <name>: ready for review" in STATUS.md and stop. Wait for me.
- Long jobs (study, studyc, match, hw) run in the background with output to a log file. They are resumable; say which command resumes them.

Order
0. Inventory: nvidia-smi + driver, python, lc0 (Windows and/or WSL, onnx-trt works?), trtexec, nsys, BT3 checkpoint, Syzygy 3-4-5 path. Write it to STATUS.md.
1. config.json, pip install -r requirements.txt, then tbset, calib, day1.  CHECKPOINT C1-day1
2. build --only s4 (outlier report), hw --parts bench, study --models fp16 --limit 50 (size Study B).  CHECKPOINT C1-done
3. select, select --alpha, set recipe in config.json from the reports.  CHECKPOINT C2-select
4. build, then study (overnight), then score.  CHECKPOINT C2-done
5. studyc, match --estimate 2, match, hw.  CHECKPOINT C3
Layout: ladder.py, README.md, RUN_4060.md, quant\, eval\, hw\, tb\ are in .\leela-int8\ - run ladder.py from there. Keep LOG.md and STATUS.md in .\leela-int8\.
The .venv\, tools\ and syzygy\ folders here were set up earlier by someone else. Inventory them in step 0 before reusing them; do not assume they are complete or correct.
