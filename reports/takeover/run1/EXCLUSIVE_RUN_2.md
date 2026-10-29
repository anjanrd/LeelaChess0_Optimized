# Handoff: new exclusive Run 2

Run 1 prepared the executable schedule; GPU validation remains pending. Current source/command freeze: `run2_jobs.json`. CPU verification: `verification.json`. Master sequence: `docs/takeover_runs.md`.

**Provisional duration: 3–7 hours. Reserve up to 8 hours for first-build uncertainty.** Production matches are not part of this run; the two-game pilot will size the later Run 4.

Before starting:

1. Save your work, plug into AC, keep the laptop open with clear airflow, and pause other laptop use.
2. Keep one recorded power/performance mode. Current normal-run observation was the Balanced power scheme; that observation alone does not describe the Windows power slider or OEM cooling/performance mode. Record the actual chosen settings for experiments and preserve them across sessions.
3. Close unrelated apps, calls, GPU jobs, WSL/VM/Docker workloads, builds, video/recording, sync and downloads. Codex can close identified nonessential processes after your work is saved. Keep required Windows/security/driver/Codex processes.
4. Codex inspects current processes/GPU/AC/temperature, records activity and creates a fresh real session file. The all-false template is not execution approval or evidence of a quiet machine.
5. Only then begin the sequential job controller. It applies the child-only TensorRT lib PATH fix and performs the real probe. The known plugin error can defer its branch; unrelated failures stop the run.

Execution mode: **coordination for the initial physical/save/idle preparation; Codex handles the experiment sequence autonomously afterward.** If you prefer a learning task, you can perform the DLL-path check and two-game pilot manually with step-by-step instructions; it is optional.

No GPU engine, profiler, benchmark, match or process-termination command was executed in Run 1. No global PATH or power setting was changed.
