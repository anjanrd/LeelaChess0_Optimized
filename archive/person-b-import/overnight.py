#!/usr/bin/env python3
"""Unattended run of everything that needs the GPU, one stage after another.

    python overnight.py                       # defaults: ~14 h of GPU work
    python overnight.py --dry-run             # print the plan, run nothing
    python overnight.py --study-hours 4 --match-hours 5

Run it from the repo folder, after the bundle (data/, models/, nets/) and
config.json are in place and `python ladder.py day1` has NOT been run yet
(this script runs it). Close every other program first.

Stages, in order (each is skipped on a rerun once it has finished, so after a
crash or reboot just run the same command again):

  preflight  files and GPU present, other GPU processes listed
  day1       gate: wrapped FP16 must match native lc0 and lc0 must run the INT8
             file, otherwise the script STOPS (everything after is invalid)
  bench      FP16 / best / native nps and J/node
  size       times 50 positions of FP16, then sets study.limit and studyc.limit
             so Study B and Study C fit --study-hours / --studyc-hours
  study      Studies A + B, models in priority order; stops launching models when
             the hour budget is spent and says which were skipped
  studyc     Study C
  hw         batch sweep, trtexec builds, peaks, roofline
  match      plays 2 games, sets the number of pairs that fit --match-hours, runs
  score      scores everything and zips results/ and reports/ into send_back.zip

Settings are written to config.run.json; your config.json is never modified.
Logs: reports/overnight/<stage>.log. Status: reports/overnight/status.json and
reports/overnight/summary.md. The machine is kept awake on Windows while this runs.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import ladder  # noqa: E402

PY = sys.executable
STAGES = ["preflight", "day1", "bench", "size", "study", "studyc", "hw", "match", "score"]


def keep_awake():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)  # CONTINUOUS | SYSTEM_REQUIRED
            return True
        except Exception:
            return False
    return False


class Runner:
    def __init__(self, a):
        self.a = a
        self.base = Path(a.config)
        self.cfg_path = self.base.resolve().with_name("config.run.json")
        user = json.loads(self.base.read_text()) if self.base.exists() else {}
        self.user = user
        self.run_cfg = json.loads(self.cfg_path.read_text()) if self.cfg_path.exists() else json.loads(json.dumps(user))
        # child processes run inside the work folder, so make it absolute here
        self.run_cfg["work"] = str(Path(user.get("work", ".")).resolve())
        self.save_cfg()
        self.cfg = ladder.load_config(str(self.cfg_path))
        self.w = self.cfg["_w"]
        self.out = self.w / "reports" / "overnight"
        self.out.mkdir(parents=True, exist_ok=True)
        self.status_path = self.out / "status.json"
        self.status = json.loads(self.status_path.read_text()) if self.status_path.exists() else {}
        self.t_begin = time.time()

    # ---------------------------------------------------------------- plumbing
    def save_cfg(self):
        self.cfg_path.write_text(json.dumps(self.run_cfg, indent=1))

    def reload(self):
        self.save_cfg()
        self.cfg = ladder.load_config(str(self.cfg_path))

    def set_status(self, stage, **kw):
        self.status.setdefault(stage, {}).update(kw)
        self.status_path.write_text(json.dumps(self.status, indent=1))
        self.write_summary()

    def write_summary(self):
        lines = ["# Overnight run", "", f"elapsed {(time.time() - self.t_begin) / 3600:.1f} h this session", "",
                 "| stage | state | minutes | note |", "|---|---|---|---|"]
        for s in STAGES:
            v = self.status.get(s)
            if v:
                lines.append(f"| {s} | {v.get('state', '')} | {v.get('minutes', '')} | {v.get('note', '')} |")
        (self.out / "summary.md").write_text("\n".join(lines) + "\n")

    def sh(self, cmd, log, check=False, capture=False):
        """Run a command, tee its output to a log file. Returns (rc, text)."""
        cmd = [str(c) for c in cmd]
        stamp = time.strftime("%H:%M:%S")
        print(f"[{stamp}] $ {' '.join(cmd)}", flush=True)
        buf = []
        with open(log, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"\n[{stamp}] $ {' '.join(cmd)}\n")
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 errors="replace", cwd=str(self.w))
            for line in p.stdout:
                f.write(line)
                f.flush()
                if capture:
                    buf.append(line)
                if len(line) < 400:
                    sys.stdout.write(line)
            p.wait()
            f.write(f"[exit {p.returncode}]\n")
        return p.returncode, "".join(buf)

    def lad(self, stage, *args, retries=1, capture=False):
        """`python ladder.py <args> --config config.run.json`, retried because every step resumes."""
        log = self.out / f"{stage}.log"
        cmd = [PY, str(ROOT / "ladder.py"), *args, "--config", str(self.cfg_path)]
        rc, txt = 1, ""
        for k in range(retries + 1):
            rc, txt = self.sh(cmd, log, capture=capture)
            if rc == 0:
                break
            print(f"  stage {stage}: exit {rc}" + (", retrying (resumes where it stopped)" if k < retries else ""))
            time.sleep(20)
        return rc, txt

    def run_stage(self, name, fn):
        if self.status.get(name, {}).get("state") == "done" and not self.a.redo:
            print(f"== {name}: already done, skipping")
            return True
        if name in self.a.skip or (self.a.only and name not in self.a.only):
            print(f"== {name}: skipped by option")
            if self.status.get(name, {}).get("state") not in ("done",):
                self.set_status(name, state="skipped", note="skipped by option")
            return True
        print(f"\n==== {name} ====", flush=True)
        t0 = time.time()
        self.set_status(name, state="running", started=time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            ok, note = fn()
        except Exception as e:  # a bug in a stage must not take the night with it
            ok, note = False, f"exception: {e!r}"
        mins = round((time.time() - t0) / 60, 1)
        self.set_status(name, state="done" if ok else "FAILED", minutes=mins, note=note)
        print(f"==== {name}: {'done' if ok else 'FAILED'} in {mins} min. {note}", flush=True)
        return ok

    def model_path(self, n):
        return Path(ladder.model_weights(self.cfg, n))

    # ---------------------------------------------------------------- stages
    def preflight(self):
        c, problems, notes = self.cfg, [], []
        lc0 = shutil.which(str(c["lc0"])) or (Path(c["lc0"]).exists() and c["lc0"])
        if not lc0:
            problems.append(f"lc0 not found: {c['lc0']}")
        if not (self.w / "data" / "tbset.jsonl").exists():
            problems.append("data/tbset.jsonl missing (unzip the bundle into the repo folder)")
        for n in ("fp16", c["best"], "s2"):
            if not self.model_path(n).exists():
                problems.append(f"{self.model_path(n)} missing")
        if not Path(c["bt3"]).exists() and not (self.w / c["bt3"]).exists():
            problems.append(f"{c['bt3']} missing (needed as the native reference)")
        if not c.get("syzygy") or not Path(c["syzygy"]).exists():
            notes.append("syzygy folder not found: the match will have no tablebase adjudication")
        if not (shutil.which(str(c["trtexec"])) or Path(c["trtexec"]).exists()):
            notes.append("trtexec not found: the trtexec/roofline part of hw will be skipped")
        smi = shutil.which("nvidia-smi")
        if smi:
            r = subprocess.run([smi, "--query-gpu=name,driver_version,memory.used,memory.total,temperature.gpu",
                                "--format=csv,noheader"], capture_output=True, text=True)
            notes.append("GPU: " + r.stdout.strip())
            r = subprocess.run([smi, "--query-compute-apps=pid,process_name,used_memory",
                                "--format=csv,noheader"], capture_output=True, text=True)
            if r.stdout.strip():
                notes.append("OTHER GPU PROCESSES RUNNING (close them, they spoil timings): "
                             + r.stdout.strip().replace("\n", "; "))
        elif "cpu" in str(c["backend"]):
            notes.append("CPU backend: no GPU checks (test run)")
        else:
            problems.append("nvidia-smi not found: is the NVIDIA driver installed?")
        if keep_awake():
            notes.append("sleep disabled while this runs")
        elif sys.platform == "win32":
            notes.append("could not disable sleep: set Power & sleep to Never yourself")
        for n in notes:
            print("  note:", n)
        for p in problems:
            print("  PROBLEM:", p)
        return (not problems), "; ".join(problems or notes)[:300]

    def day1(self):
        rc, _ = self.lad("day1", "day1", retries=0)
        p = self.w / "reports" / "day1" / "scores_dev.json"
        if rc != 0 or not p.exists():
            return False, f"day1 exited {rc}; see reports/overnight/day1.log. Stopping: nothing after this is valid."
        js = json.loads(p.read_text())["models"]
        fp, s2 = js.get("fp16", {}).get("A", {}), js.get("s2", {}).get("A", {})
        note = (f"wrapped FP16 vs native: KL {fp.get('kl', float('nan')):.2e}, top-1 {fp.get('top1', 0):.3f}; "
                f"INT8 file {'ran' if s2 else 'DID NOT RUN'}")
        if fp.get("top1", 0) < 0.97:
            return False, note + ". Wrapped path differs from native lc0: STOP and send reports/day1 to Ritwik."
        if not s2:
            return False, note + ". lc0 could not run the INT8 file: STOP and send reports/overnight/day1.log."
        return True, note

    def bench(self):
        rc, _ = self.lad("bench", "hw", "--parts", "bench", retries=1)
        return rc == 0, f"exit {rc}"

    def size(self):
        a, c = self.a, self.cfg
        t0 = time.time()
        rc, _ = self.lad("size", "study", "--models", "fp16", "--limit", "50", "--split", c["study"]["split"])
        if rc != 0:
            return False, "sizing run failed"
        rows = [json.loads(l) for l in (self.w / "results" / "fp16" / "study_b.jsonl").read_text().splitlines()
                if l.strip().startswith("{")]
        ids = {r["id"] for r in rows}
        if not ids:
            return False, "no Study B rows from the sizing run"
        search_s = sum(r.get("wall", r.get("time_ms", 0) / 1000) for r in rows) / len(ids)
        sec_pos = search_s * a.overhead
        names = ladder.resolve(c, c["study"]["models"])
        equiv = len(names)
        if c["extras"]["swap"]:
            equiv += 4            # two swap models, each runs two bodies
        if c["extras"]["s1sp"]:
            equiv += 1
        full = sum(1 for l in (self.w / "data" / "tbset.jsonl").read_text().splitlines()
                   if l.strip() and json.loads(l).get("split") == c["study"]["split"])
        lim = int(a.study_hours * 3600 / (sec_pos * equiv))
        cap = a.max_limit or full or lim
        user_lim = self.user.get("study", {}).get("limit", 0) or 0
        limit = max(a.min_limit, min(lim, cap, user_lim or cap))
        mts = [int(x) for x in c["studyc"]["movetimes"].split(",")]
        per_c = sum(mts) / 1000 + 0.25 * len(mts)           # search + newgame/overhead per position
        c_models = len(ladder.resolve(c, c["studyc"]["models"]))
        limc = int(a.studyc_hours * 3600 / (per_c * c_models))
        user_limc = self.user.get("studyc", {}).get("limit", 0) or 0
        limitc = max(a.min_limit, min(limc, limit, user_limc or limit))
        self.run_cfg.setdefault("study", {})["limit"] = limit
        self.run_cfg.setdefault("studyc", {})["limit"] = limitc
        self.reload()
        eta_s = limit * sec_pos * equiv / 3600
        note = (f"{search_s:.1f} s search/position/model (x{a.overhead} = {sec_pos:.1f}); {equiv} model-equivalents; "
                f"study.limit={limit} (about {eta_s:.1f} h), studyc.limit={limitc}")
        if lim < a.min_limit:
            note += f". WARNING: budget only fits {lim} positions, using the floor {a.min_limit} " \
                    f"(expect {a.min_limit * sec_pos * equiv / 3600:.1f} h)"
        return True, note

    def study(self):
        c, a = self.cfg, self.a
        limit = c["study"]["limit"]
        names = ladder.resolve(c, c["study"]["models"])
        order = [c["best"], "s2", "s3", "s1", "s4aa"]
        names = ["fp16"] + [n for n in order if n in names and n != "fp16"] + \
                [n for n in names if n not in order and n != "fp16"]
        extras = []
        if c["extras"]["s1sp"]:
            extras.append("s1sp")
        if c["extras"]["swap"]:
            extras += ["swap_pol8", "swap_val8"]
        names = list(dict.fromkeys(names + extras))
        t0, log = time.time(), self.out / "study.log"
        done, skipped, failed = [], [], []
        for n in names:
            if n != "fp16" and not self.model_path(n).exists():
                skipped.append(f"{n}(not built)")
                continue
            if n != "fp16" and (time.time() - t0) > a.study_hours * 3600 * 1.15:
                skipped.append(f"{n}(out of time)")
                continue
            ok = False
            for k in range(2):
                rc, _ = self.sh(ladder.study_cmd(c, n, c["study"]["budgets"], c["study"]["split"], limit), log)
                if rc == 0:
                    ok = True
                    break
                time.sleep(20)
            (done if ok else failed).append(n)
        # S0: raw-net Study A only (cheap); Study B too if the user switched it on
        if self.model_path("s0").exists():
            b = c["study"]["budgets"] if c["extras"]["s0_in_study_b"] else "0"
            rc, _ = self.sh(ladder.study_cmd(c, "s0", b, c["study"]["split"], limit), log)
            (done if rc == 0 else failed).append("s0")
        note = f"done {','.join(done)}"
        if skipped:
            note += f"; SKIPPED {','.join(skipped)}"
        if failed:
            note += f"; FAILED {','.join(failed)}"
        return (not failed and not any("out of time" in s for s in skipped)), note

    def studyc(self):
        rc, _ = self.lad("studyc", "studyc", retries=1)
        return rc == 0, f"exit {rc}"

    def hw(self):
        rc, _ = self.lad("hw", "hw", "--parts", "sweep,trt,roofline", retries=0)
        return rc == 0, f"exit {rc} (trtexec/roofline failures are logged, not fatal)"

    def match(self):
        c, a = self.cfg, self.a
        rc, txt = self.lad("match", "match", "--estimate", "2", retries=0, capture=True)
        m = re.search(r"~(\d+) s/game", txt)
        if rc != 0 or not m:
            return False, "could not time the match games; see reports/overnight/match.log"
        per = float(m.group(1))
        pairs = int(a.match_hours * 3600 / per / 2)
        want = (self.user.get("match", {}) or {}).get("pairs", 250)
        pairs = min(pairs, want)
        if pairs < a.min_pairs:
            return False, f"only {pairs} pairs fit {a.match_hours} h at {per:.0f} s/game; not worth running"
        self.run_cfg.setdefault("match", {})["pairs"] = pairs
        self.reload()
        rc, _ = self.lad("match", "match", retries=2)
        return rc == 0, f"{per:.0f} s/game, {pairs} pairs ({2 * pairs} games)"

    def score(self):
        self.lad("score", "score", retries=0)
        zp = self.w / "send_back.zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for d in ("results", "reports"):
                for f in (self.w / d).rglob("*"):
                    if f.is_file() and f.suffix not in (".nsys-rep", ".sqlite", ".engine", ".plan") \
                            and f.stat().st_size < 200e6:
                        z.write(f, f.relative_to(self.w))
            z.write(self.cfg_path, "config.run.json")
        return True, f"wrote {zp} ({zp.stat().st_size / 1e6:.0f} MB): send this file to Ritwik"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--study-hours", type=float, default=5.0, help="budget for Studies A+B")
    ap.add_argument("--studyc-hours", type=float, default=1.0)
    ap.add_argument("--match-hours", type=float, default=6.0)
    ap.add_argument("--overhead", type=float, default=1.3,
                    help="multiplier on measured search time for UCI/newgame overhead")
    ap.add_argument("--min-limit", type=int, default=300, help="never size the study below this many positions")
    ap.add_argument("--min-pairs", type=int, default=10, help="skip the match if fewer pairs than this fit")
    ap.add_argument("--max-limit", type=int, default=0)
    ap.add_argument("--only", default="", help="comma list of stages")
    ap.add_argument("--skip", default="", help="comma list of stages")
    ap.add_argument("--redo", action="store_true", help="rerun stages already marked done")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    a.only = [s for s in a.only.split(",") if s]
    a.skip = [s for s in a.skip.split(",") if s]
    if a.dry_run:
        print(__doc__)
        print("stages:", ", ".join(s for s in STAGES if s not in a.skip and (not a.only or s in a.only)))
        print(f"budgets: study {a.study_hours} h, studyc {a.studyc_hours} h, match {a.match_hours} h "
              f"(plus day1, bench, hw: about 2-3 h)")
        return
    r = Runner(a)
    fns = {"preflight": r.preflight, "day1": r.day1, "bench": r.bench, "size": r.size, "study": r.study,
           "studyc": r.studyc, "hw": r.hw, "match": r.match, "score": r.score}
    hard_stop = {"preflight", "day1"}          # nothing after these is valid if they fail
    for s in STAGES:
        ok = r.run_stage(s, fns[s])
        if not ok and s in hard_stop:
            print(f"\nSTOPPED at {s}. Fix it (see reports/overnight/{s}.log) and rerun the same command.")
            sys.exit(1)
    print("\nALL STAGES FINISHED. Summary:\n" + (r.out / "summary.md").read_text())


if __name__ == "__main__":
    main()
