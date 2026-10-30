# Before exclusive Run 4

Run 3 is normal CPU-only analysis/preparation. Run 4 has **not started** and needs Anjan's explicit start. Work on `anjan`. Read `analysis/person_a/run3_findings.md`, this handoff, `run4-preparation.json` and `run4-manifest.json` first.

## Time and laptop preparation

**Plan 5–6 hours; reserve 7 hours.** The two-game pilot estimates 3.746 hours for 500 games, with broad uncertainty. First builds, fresh checks and cooling may extend the run. Match size is already fixed at 250 pairs; do not resize from observed match results.

1. Save all work, plug into AC and pause laptop use for the entire exclusive block.
2. Keep the same Windows Balanced and OEM performance settings used for Run 2; record actual settings rather than assuming they are unchanged. Leave the lid open, vents clear and cooling unobstructed. Do not change clock/power settings during the run. Clock locking remains unavailable.
3. Close nonessential applications and pause competing GPU/CPU jobs, WSL/VMs, downloads and sync. Codex remains the orchestrator. Preserve Windows, security and drivers. Only identified nonessential jobs may be closed after saved-work authorization; no blanket process killing.
4. Codex inspects and records real `nvidia-smi`, processes, AC, temperature/clocks and power mode before execution. Background-interference flags remain informational under the approved policy. AC loss, monitor errors, workload exit/output/identity failures and the one-GPU-workload lock still stop execution. Codex load is not assumed constant across trials.

## Frozen order and checks

The 15 jobs execute sequentially with verification before proceeding:

1. Three 10-second idle telemetry windows. Preserve samples, counters and consistency diagnosis. Unresolved idle telemetry is an explicit energy limitation, not fabricated validation or an automatic chess-match failure; missing energy telemetry is a real failure.
2. Fresh source/Python/artifact FP16, s4 and SparseGPT on 32 deterministic frozen roots, raw and 100 requested nodes. Numerical check before subsequent measurements: absolute WL/D/V drift <=0.005, moves-left <=0.25, normalized policy max drift <=0.005; raw preserving-outcome vector must match. Search outcomes are reported descriptively because search is not bitwise deterministic. These are reproduction limits, not new accuracy acceptance rules.
3. One fresh common-setting speed/energy trial per model; three lc0 precision captures; one sparse-enabled standalone profile. NPS and batch-64 NN latency ratios outside 0.8–1.2 of source medians stop for review. Selected sparse tactics or their documented runtime limitation are recorded. Precision kernel tags are not full graph coverage.
4. Only after both reproduction gates pass, run all **500 production games / 250 complete color-swapped pairs**, 10+0.1, unchanged opening book, clocks and adjudication. Syzygy is arbiter-only. No outcome-based stopping or resizing. The individual-game journal permits recovery after reviewed interruptions; preserve failed attempts and committed games.
5. Capture actual s4 gameplay, moves, nodes, elapsed time and printed NPS after measurements. Video rendering and final presentation/report/package/statistics remain normal Run 5.

The fresh clone is at `eb9e8cf8811f2426884d293e780a55d68240be48` under `%LOCALAPPDATA%\LC0-BT3-Reproduction\run4-eb9e8cf\repo`, with its own newly installed `.venv` beside it. The separately hashed check driver is in that workspace's `control` directory. Native tools remain the same-host verified installations; global/native caches may be reused and must not be called a guaranteed cold rebuild.

## Safe command and execution gate

This command is plan-only and launches zero GPU workloads:

```powershell
.\.venv\Scripts\python.exe -B -m execution.run4
```

After explicit user start, Codex creates a **new actual session** from `run4-session-template.json`, records real resource/runtime observations and power-mode continuity, verifies all manifest identities, then uses:

```powershell
.\.venv\Scripts\python.exe -B -m execution.run4 --execute --session reports/takeover/run4/session.json
```

The false template cannot authorize execution. Do not reuse Run 2's old session, launch legacy/manual Run 2 commands, edit the manifest after measurements begin, overwrite raw evidence or automatically retry a failed job. Preserve/log BLOCKED and review before continuation. Stop at Run 4 completion and perform the agreed read-only cumulative objective/hypothesis check in conversation.

## Required interpretation at the next handoff

Selected s4 is faster with more search visits; near-ceiling timed accuracy does not establish better accuracy per second. Sparse/pruned variants can lose quality, and standalone sparse gains are modest. Historical above-idle energy remains provisional because repeated idle telemetry is anomalous; a new successful check cannot retroactively certify every old baseline. Report Run 4's actual outcomes even when adverse. Final match uncertainty must account for color pairs and reuse of 50 openings; no reliable strength claim comes from the two-game pilot.
