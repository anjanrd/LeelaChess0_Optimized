# Finish Run 2 with Codex closed

Approved by Anjan on 30 October 2026. Launcher: `execution/manual_run2.py`.
This changes how the existing jobs are launched. The 45-job manifest, 69 frozen
inputs, original controller/resource guard, models, settings and scoring stay
unchanged. Preparation and offline tests do not run GPU experiments.

The current checkpoint has 35 verified jobs. Remaining work is nine benchmark
jobs (one fresh attempt of the flagged SparseGPT trial and eight unstarted
trials), followed by the two-game planning pilot. Production matches remain Run 4.

## Operator instructions

1. Save other work. Connect AC, keep the lid open and vents clear, and keep the
   same Windows/OEM power settings used in the first session. Do not switch to a
   different performance mode for this continuation. Pause other laptop use.
   Reserve 30–45 minutes; allow a one-hour window.
2. Open **Windows Start**, type **PowerShell**, and open a normal PowerShell
   window. Use a window opened outside Codex; the integrated terminal is rejected.
   Administrator access and virtual-environment activation are not required.
3. Paste these commands:

   ```powershell
   Set-Location -LiteralPath 'C:\Users\HP\Desktop\LC0'
   .\.venv\Scripts\python.exe -B -u -m execution.manual_run2 --execute --confirm-exclusive --confirm-same-power-mode --approve-retry bench-s1sp-r3
   ```

   The confirmation flags mean work is saved, other use is paused, AC is connected
   and Windows/OEM power modes are unchanged. Supply them only when true.
4. When the terminal prints **Waiting for Codex to fully close**, fully quit
   Codex. Keep the external PowerShell window open. The launcher lists any
   remaining `ChatGPT.exe`/`codex.exe` PIDs and waits up to ten minutes. Merely
   minimizing the app does not satisfy this check. It never kills Codex or other
   user applications for you.
5. Leave the laptop unused. The launcher checks a 60-second quiet window and
   runs one GPU job at a time. Do not reopen Codex until the final status line.
   Reopening it during measurement stops the owned experiment processes.
6. Wait for one of these terminal results:
   - **COLLECTED_AWAITING_CODEX_VERIFICATION**: reopen this chat, reply **done**
     and include that terminal status. Codex will verify before declaring Run 2
     complete. `VERIFIED` for an individual job is not the final status.
   - **BLOCKED**: reopen this chat and report the message and evidence-folder
     path. Do not repeatedly retry, change the guard or delete a lock file.
     The launcher stops on the first new failure; it does not run later jobs.

Closing PowerShell or pressing Ctrl+C cancels execution. The worker and its
descendants are contained in a Windows job with kill-on-close cleanup; unrelated
processes are not assigned to it. An abrupt window/process close can leave locks
or an incomplete status that needs review. Leave the power settings unchanged
until the measurements finish; the temporary awake request does not change the
persistent Windows power plan.

## Preservation and verification

- The launcher verifies all frozen inputs and saved reusable outputs. A changed
  GPU/driver/runtime/power identity blocks execution rather than silently pooling
  incompatible results.
- Only the original `bench-s1sp-r3/attempt-001` receipt with SHA256
  `32d081af30df79797f1400de2fea0291b1cd24629e4d880a427776a9201e7811`
  is covered by this retry approval. Its receipt, raw output and inventory remain
  immutable. The review record preserves the prior state row; the next trial
  gets a new attempt directory. A different failure requires another review.
- The manifest is not regenerated and the 35 verified jobs are skipped only
  after identity/runtime checks. The original >5% whole-machine CPU for three
  consecutive two-second intervals rule still applies. No host whitelist is added.
- A new `reports/takeover/run2/manual-resume-<id>/` holds the runtime/preflight,
  fresh session, retry review, launcher-source identity, worker command/log and
  final summary. Temperatures/clocks remain in the existing per-job records.
  Codex being closed is explicitly recorded as a session difference for Run 3.
- The success marker requires every job verified, 28 benchmark trials, two
  correctly numbered pilot game records, unchanged inputs and preserved old
  failure evidence. It means collection is ready for Codex review; precision,
  sparsity, roofline interpretation and the final match remain later work.
- After **done**, Codex checks the new summary/session/review, all receipts and
  hashes, original failed evidence, resource flags, benchmark data, two pilot
  games and source/runtime consistency. Then it performs the agreed read-only
  cumulative objective/hypothesis alignment check and updates normal progress
  records. Do not automatically start Run 3 or production matches.

For a read-only audit while Codex is open (no GPU experiment):

```powershell
.\.venv\Scripts\python.exe -B -m execution.manual_run2 --check
```

Preparation verification: `reports/takeover/run2/manual-launcher-verification.json`.
