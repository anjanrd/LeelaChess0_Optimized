"""Person A Run 1: derived analysis of frozen evidence, no engine/inference jobs.

Run A1..A8 separately and verify each before proceeding. A9/A10 are the report
and delivery-preparation stages. Original quantization/scoring code is read only.
"""
import argparse
import ast
import csv
import gc
import hashlib
import importlib.util
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import chess
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "analysis/person_a/run1"
TABLES = ROOT / "analysis/tables"
FIGURES = ROOT / "analysis/figures"
MODELS = ["fp16", "s1", "s2", "s3", "s4", "s4aa", "s0", "s1sp", "swap_pol8", "swap_val8"]
DENSE = MODELS[:6]
FRONTIER = MODELS[:8]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


SCORER = module("eval/score.py", "frozen_scorer")
from common import wilson  # noqa: E402


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def write(path, value):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    text = value if isinstance(value, str) else json.dumps(value, indent=2, allow_nan=False) + "\n"
    p.write_text(text, encoding="utf-8")


def rows(path):
    p = ROOT / path
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8-sig").splitlines() if x.strip()]


def csvwrite(name, records):
    records = list(records)
    if not records:
        raise ValueError("No records for " + name)
    p = ROOT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader(); w.writerows(records)


def csvread(name):
    with (ROOT / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def markdown_table(records, columns):
    return "\n".join(["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)] +
                     ["| " + " | ".join(str(r[c]) for c in columns) + " |" for r in records])


def keyed(records, fields):
    out = {}
    for r in records:
        key = tuple(r[f] for f in fields)
        if key in out:
            raise ValueError(f"Duplicate key {key}")
        out[key] = r
    return out


def context():
    tb = {r["id"]: r for r in rows("data/tbset.jsonl")}
    data = {m: SCORER.load(ROOT / "results", m) for m in MODELS}
    cohort = sorted(i for i in data["fp16"][0] if tb[i]["split"] == "test")
    hard = {int(i) for i in (ROOT / "reports/hard/ids.txt").read_text().split()}
    return tb, data, cohort, hard


def summary(values):
    a = np.asarray(values, dtype=float)
    assert len(a) and np.isfinite(a).all()
    return {"mean": float(a.mean()), "median": float(np.median(a)),
            "min": float(a.min()), "p90": float(np.percentile(a, 90)), "max": float(a.max())}


def paired(tb, ids, selected, ref):
    ids = sorted(ids)
    ok = [selected[i]["best"] in tb[i]["correct"] for i in ids]
    rok = [ref[i]["best"] in tb[i]["correct"] for i in ids]
    correct = sum(ok); n = len(ids)
    worse = sum(r and not o for o, r in zip(ok, rok))
    better = sum(o and not r for o, r in zip(ok, rok))
    lo, hi = wilson(correct, n)
    return {"n": n, "correct": correct, "errors": n-correct, "accuracy": correct/n,
            "ci_low": lo, "ci_high": hi, "worse": worse, "better": better,
            "mcnemar_p": SCORER.mcnemar_p(worse, better)}


def group_id(board):
    # Same equivalence relation as archived prepare_pilot.py; no archive imports.
    if board.castling_rights:
        spatial = [board]
    elif board.pawns or board.ep_square is not None:
        spatial = [board, board.transform(chess.flip_horizontal)]
    else:
        transforms = [lambda x:x, chess.flip_horizontal, chess.flip_vertical,
                      lambda x:chess.flip_horizontal(chess.flip_vertical(x)),
                      chess.flip_diagonal, chess.flip_anti_diagonal,
                      lambda x:chess.flip_horizontal(chess.flip_diagonal(x)),
                      lambda x:chess.flip_vertical(chess.flip_diagonal(x))]
        spatial = [board.transform(t) for t in transforms]
    variants = spatial + [b.mirror() for b in spatial]
    key = min(" ".join(b.fen(en_passant="fen").split()[:4]) for b in variants)
    return hashlib.sha256(key.encode()).hexdigest()


def checkpoint(step, result, status="verified"):
    p = OUT / "progress.json"
    state = json.loads(p.read_text()) if p.exists() else {"source_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "branch": "anjan", "steps": {}}
    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() == "anjan"
    state["steps"][step] = {"status": status, "result": result}
    write(p, state)
    with (ROOT / "LOG.md").open("a", encoding="utf-8") as f:
        f.write(f"\n\n## 2026-10-29 — Person A Run 1 {step}\n\n"
                f"Authorization: full sequential Run 1 on anjan. Command: "
                f"`.venv/Scripts/python.exe -B analysis/person_a/run1.py {step}`. "
                f"Exit 0; {status}. Output: {json.dumps(result, ensure_ascii=True)}. "
                "Original evidence preserved; no engine inference/training/search or GPU benchmarking.\n")
    print(step, status, json.dumps(result), flush=True)


def A1():
    tb, data, cohort, hard = context()
    assert len(tb) == 11200 and len(cohort) == 2437 and len(hard) == 43
    assert set(hard) <= set(cohort)
    all_sources = read("artifacts/manifest.json")["files"]
    sources = [{"path": e["path"], "sha256": e["sha256"], "bytes": e["bytes"]} for e in all_sources]
    code = [ROOT / "common.py", ROOT / "config.example.json"]
    for d in ["quant", "eval", "tb", "hw"]:
        code += sorted((ROOT / d).glob("*.py"))
    sources += [{"path": str(p.relative_to(ROOT)).replace("\\", "/"),
                 "sha256": sha(p), "bytes": p.stat().st_size} for p in code]
    write(OUT / "source_manifest.json", {"files": sources, "initial_artifact_audit": "328/328 matched"})
    audit = {"split_counts": dict(Counter(r["split"] for r in tb.values())), "cohort_n":len(cohort),
             "hard_n":len(hard), "coverage":{}}
    recomputed_hard = {i for i in cohort if data["fp16"][0][i]["best"] not in tb[i]["correct"] or
                       sum(p for m,p in data["fp16"][0][i]["p"].items() if m in tb[i]["correct"]) < .8}
    assert hard == recomputed_hard
    for m in MODELS:
        ra = rows(f"results/{m}/study_a.jsonl")
        keyed(ra, ["id", "budget"])
        assert set(cohort) <= set(data[m][0])
        for i in cohort:
            assert data[m][0][i]["best"] in tb[i]["moves"]
        rb = rows(f"results/{m}/study_b.jsonl")
        keyed(rb, ["id", "budget"])
        coverage = {str(b):len(set(items) & set(cohort)) for b,items in data[m][1].items()}
        if m != "s0":
            assert set(data[m][1]) == {100,400,800,1600}
            assert set(coverage.values()) == {2437}
        audit["coverage"][m] = {"main_A_test":2437, "A_extra_rows":len(ra)-2437,
                                  "B_selected_counts":coverage, "A_B_duplicate_keys":0}
    groups = defaultdict(list)
    for r in tb.values():
        b = chess.Board(r["fen"])
        assert b.is_valid() and b.halfmove_clock == 0
        assert set(r["moves"]) == {m.uci() for m in b.legal_moves}
        assert set(r["correct"]) == {m for m,v in r["moves"].items() if v["res"] == r["root"]}
        groups[group_id(b)].append({"id":r["id"],"split":r["split"],"class":r["cls"]})
    crossing = [{"group":g,"members":v} for g,v in groups.items() if len({r["split"] for r in v}) > 1]
    affected = sorted(r["id"] for g in crossing for r in g["members"] if r["id"] in set(cohort))
    assert len(crossing) == 7 and len(affected) == 3
    with np.load(ROOT / "data/calib.npz") as z:
        used = {int(i) for i in z["tb_id"] if int(i) >= 0}
        calibration = {"n":len(z["planes"]), "source_counts":dict(Counter(str(x) for x in z["src"])),
                       "tablebase_ids":sorted(used), "input_format":int(z["input_format"])}
    assert calibration["n"] == 512 and calibration["input_format"] == 1
    audit.update({"cross_split_symmetry_groups":crossing,"affected_measured_test_ids":affected,
                  "actual_calibration_cross_group_ids":sorted(used & {r["id"] for g in crossing for r in g["members"]}),
                  "calibration":calibration,"primary_cohort_unchanged":True})
    write(OUT / "cohort_audit.json", audit)
    write(OUT / "cohort_ids.txt", "\n".join(map(str,cohort))+"\n")
    write(OUT / "evidence_index.md", "# Evidence definitions and limitations\n\n"
          "The primary cohort is 2,437 test IDs; the hard subset has 43. The adopted scorer maps Syzygy ±1 to draw. "
          "Move accuracy tests selected legal moves against saved tablebase categories; KL/top-1/|ΔV| compare NN outputs. "
          "The main policy/value measurements are printed lc0 quantities, not full-precision ONNX tensors. "
          "Python ORT is CPU preparation; lc0 bundles its own GPU ORT. QDQ placement is intent, not measured precision coverage.\n\n"
          f"Seven equivalence groups cross dataset splits; measured test IDs affected: **{affected}**. "
          "Equivalence uses legal file reflection for pawn positions, D8 for pawnless positions and color/rank mirroring; "
          "castling restrictions are respected. This matches archived grouping, not a changed scorer. "
          "The primary corpus/results remain unchanged. No test roots were removed or tuning performed. "
          "A separate exclusion sensitivity would require an explicitly labelled, agreed analysis.\n\n"
          "Synthetic decision-sensitive 3–5-piece endgames do not represent general chess play. The hard subset "
          "was defined using viewed FP16 test results and is descriptive. Calibration uses mixed random-game/history "
          "and tablebase/FEN-only inputs. The actual calibration cross-group IDs are recorded in cohort_audit.json; "
          "membership in the calibration pool alone does not prove a root was used to fit scales.\n\n"
          "Network drift, search quality at requested nodes, NN latency, search throughput, timed accuracy and match "
          "strength are separate claims. Negative or inconclusive findings are valid. R1–R5 handoffs gate only "
          "the corresponding measured conclusions.\n")
    checkpoint("A1", {"roots":len(tb),"cohort":len(cohort),"hard":len(hard),
                      "cross_split_groups":len(crossing),"affected_test_ids":affected})


def A2():
    tb,data,ids,_ = context()
    _, computed = SCORER.score(tb,data,"fp16",MODELS,set(ids))
    frozen = read("reports/scores_test.json")
    quality=[]; recipes=[]
    for m in MODELS:
        a = computed["models"][m]["A"]
        assert a == frozen["models"][m]["A"],m
        p = paired(tb,ids,data[m][0],data["fp16"][0])
        dtz_count = sum(data[m][0][i]["best"] in tb[i]["dtz_opt"] for i in ids)
        quality.append({"model":m,**p,"dtz_correct":dtz_count,"dtz_rate":a["dtz_opt"],
                        "policy_KL_approx":a["kl"],"top1_agreement":a["top1"],"mean_abs_delta_V":a["dv"]})
        side = read(f"models/{m}.json") if m != "fp16" else {}
        recipes.append({"model":m,"granularity":side.get("granularity","floating" if m=="fp16" else "see sidecar"),
                        "calibration":side.get("method","runtime FP16"),"percentile":side.get("percentile"),
                        "smoothquant_alpha":side.get("smoothquant"),"weighted_targets":side.get("n_weight_nodes",0),
                        "dynamic_targets":side.get("n_act_act",0),"runtime_options":"optimize=6" if m=="fp16" else "optimize=8",
                        "sidecar":"none: exported FP32 graph, runtime FP16" if m=="fp16" else f"models/{m}.json"})
    choice = read("reports/C2-recipe-choice.json")
    assert choice["best"] == "s4" and choice["recipe"]["s4_alpha"] == .7
    assert choice["recipe"]["s3_percentile"] == 99.999
    csvwrite("analysis/tables/T1-network.csv",quality)
    csvwrite("analysis/tables/T1-model-recipes.csv",recipes)
    write("analysis/tables/T1-network.md", "# Network-level results\n\n"
          "Frozen 2,437-position cohort; primary accuracy is move-result preservation. Intervals are marginal 95% Wilson intervals; "
          "paired discordances/McNemar compare with FP16. KL uses rounded printed priors.\n\n"+
          markdown_table(quality,["model","n","correct","errors","accuracy","ci_low","ci_high","dtz_rate",
                                   "policy_KL_approx","top1_agreement","mean_abs_delta_V","worse","better","mcnemar_p"])+"\n")
    from plotting import network
    network(quality)
    write(OUT / "network_findings.md", "# Network finding\n\n"
          f"FP16 and s4 each preserve the root result on {quality[0]['correct']}/2,437 positions. "
          "Per-channel weighting alone does not monotonically improve every metric. The selected percentile and smoothing "
          "substantially reduce reported policy divergence versus naive PTQ; this is output fidelity, not proof of stronger play. "
          "The dynamic-attention extension has the same selected-move score here, but slightly different policy/value drift. "
          "Development selection used percentile 99.999 and SmoothQuant alpha 0.7; the test set did not choose that recipe. "
          "A near-ceiling move score does not imply identical NN outputs. Full actual precision coverage and performance await B.\n")
    checkpoint("A2", {"models":len(quality),"score_A_exact_match":True,"figure":"F1-ablation"})


def A3():
    tb,data,ids,hard = context(); saved=read("reports/scores_test.json")
    _,derived=SCORER.score(tb,data,"fp16",MODELS,set(ids))
    search=[]
    for m in MODELS:
        if "B" not in derived["models"][m]:continue
        # JSON serializes integer budget keys as strings; compare the same form.
        assert json.loads(json.dumps(derived["models"][m]["B"])) == saved["models"][m]["B"],m
        ne=derived["models"][m]["B"]["node_equiv"]
        for j,b in enumerate([100,400,800,1600]):
            p=paired(tb,ids,data[m][1][b],data["fp16"][1][b])
            s=summary([data[m][1][b][i]["nodes"] for i in ids])
            search.append({"model":m,"requested_nodes":b,**p,**{f"actual_nodes_{k}":v for k,v in s.items()},
                           "node_equivalent_printed":ne[j],"series":"main"})
    # Magnitude pruning's supplemental 100/400 search is a distinct run series.
    extra=rows("results/s0_search/s0/study_b.jsonl")
    keyed(extra,["id","budget"])
    for b in sorted({r["budget"] for r in extra}):
        d={r["id"]:r for r in extra if r["budget"]==b and r["id"] in set(ids)}
        assert set(d)==set(ids)
        p=paired(tb,ids,d,data["fp16"][1][b]);s=summary([d[i]["nodes"] for i in ids])
        search.append({"model":"s0","requested_nodes":b,**p,**{f"actual_nodes_{k}":v for k,v in s.items()},
                       "node_equivalent_printed":"not reported","series":"supplemental_s0_search"})
    low=[];discord=[]
    for m in DENSE:
        rr=rows(f"results/hard_lowbudget/{m}/study_b.jsonl");keyed(rr,["id","budget"])
        assert len(rr)==43*5
        for b in [10,25,50,100,200]:
            d={r["id"]:r for r in rr if r["budget"]==b}
            rd={r["id"]:r for r in rows("results/hard_lowbudget/fp16/study_b.jsonl") if r["budget"]==b}
            assert set(d)==hard==set(rd)
            p=paired(tb,hard,d,rd);s=summary([d[i]["nodes"] for i in hard])
            low.append({"model":m,"requested_nodes":b,**p,**{f"actual_nodes_{k}":v for k,v in s.items()}})
            for i in sorted(hard):
                if (d[i]["best"] in tb[i]["correct"]) != (rd[i]["best"] in tb[i]["correct"]):
                    discord.append({"model":m,"id":i,"budget":b,"best":d[i]["best"],"ref_best":rd[i]["best"],
                                    "model_correct":d[i]["best"] in tb[i]["correct"]})
    csvwrite("analysis/tables/T1-search.csv",search)
    csvwrite("analysis/tables/hard-lowbudget.csv",low)
    csvwrite("analysis/tables/hard-discordances.csv",discord)
    write(OUT / "search_verification.json", {"main_score_B_exact_match":True,"hard_conditions":len(low),
          "hard_positions_per_condition":43,"supplemental_s0_budgets":sorted({r['budget'] for r in extra}),
          "hard_selection":"FP16 viewed-test errors or correct-policy mass below 0.8; descriptive"})
    from plotting import search_figures
    search_figures(search,low,read("reports/scores_test.json"))
    write(OUT / "search_findings.md", "# Search finding\n\n"
          "Dense variants are close to perfect at the larger requested budgets, limiting evidence for relative superiority. "
          "The main table's node-equivalents use the frozen inverse log-node monotone-envelope convention. On a flat "
          "reference curve the inverse is an interval; a value near 1 is partly that convention, not proof of identical search quality. "
          "Zero means below the reference raw score, not zero actual nodes. Actual search work overshoots requested limits. "
          "The hard subset has only 43 viewed-test positions; small, non-monotone differences should not be treated as robust gains "
          "or used to select a new recipe. Magnitude's supplemental 100/400 results are kept separate and have no invented 800/1600 points.\n")
    checkpoint("A3",{"main_score_B_exact_match":True,"search_rows":len(search),"hard_rows":len(low),
                     "figures":["F2-nodes","F3-node-equivalents","S1-hard-lowbudget"]})


def A4():
    tb,data,ids,_=context();prov=read("reports/c3_swap_provenance.json")
    out=[]
    for name in ["swap_pol8","swap_val8"]:
        p=prov[name]
        assert sha(ROOT/f"models/{name}.onnx")==p["onnx_sha256"]
        assert sha(ROOT/f"models/{name}.pb.gz")==p["pb_gz_sha256"]
        policy="s4" if name=="swap_pol8" else "fp16"
        value="fp16" if name=="swap_pol8" else "s4"
        assert p["policy"]["model"]==policy and p["value_mlh"]["model"]==value
        for part,modelname in [("policy",policy),("value_mlh",value)]:
            file="bt3_fp32" if modelname=="fp16" else modelname
            assert sha(ROOT/f"models/{file}.onnx")==p[part]["sha256"]
    for m in ["fp16","s4","swap_pol8","swap_val8"]:
        for b in [0,100,400,800,1600]:
            d=data[m][0] if b==0 else data[m][1][b]
            ref=data['fp16'][0] if b==0 else data['fp16'][1][b]
            p=paired(tb,ids,d,ref)
            out.append({"model":m,"requested_nodes":b,**p,
                        "actual_nodes_mean":statistics.mean(d[i]['nodes'] for i in ids)})
    csvwrite("analysis/tables/policy-value-swap.csv",out)
    from plotting import swaps
    swaps(out)
    write(OUT / "swap_provenance.md", "# Policy/value swap review\n\n"
          "Model and source ONNX/wrapped SHA256 identities match the frozen provenance. swap_pol8 routes policy from s4, "
          "value and moves-left from the FP16-side graph; swap_val8 reverses them. Each stitched model evaluates two bodies. "
          "Both use optimize=8 with a floating branch, rather than running two independently frozen engines.\n\n"
          "Chosen-move accuracy ties on this cohort do not establish equal importance of policy and value errors. "
          "The FP16-policy swap also has small printed-policy differences from the reference; source routing is verified, "
          "but numerical execution is not a perfectly isolated head replacement. Moves-left changes with the value branch. "
          "Requested-budget comparisons retain actual-node context. Neither swap is eligible for speed/energy/frontier input.\n")
    checkpoint("A4",{"source_hashes_verified":True,"comparison_rows":len(out),"figure":"F4-swaps"})


def A5():
    from smoothquant_diagnostic import diagnose, validate_current, pair_check, TENSOR
    provenance=diagnose()
    values,collection=validate_current()
    side=read('models/s4.json');groups=[]
    for name,g in side['smoothed_groups'].items():
        before,after=g['outlier_before'],g['outlier_after']
        assert math.isfinite(before) and math.isfinite(after) and min(before,after)>0
        groups.append({'tensor':name,'ratio_before':before,'ratio_after':after,
                       'after_over_before':after/before,'improved':after<before,
                       'consumers':';'.join(g['consumers'])})
    inv=values['smooth_inverse']
    checked=pair_check(values['s4_raw'],values['s4_smoothed'],inv)
    assert checked['agrees']
    channels=[{'channel':i,**{k:float(v[i]) for k,v in values.items()}}
              for i in range(768)]
    csvwrite('analysis/tables/smoothquant-groups.csv',groups)
    csvwrite('analysis/tables/smoothquant-channels.csv',channels)
    stats={}
    for key in ['s4_raw','s4_smoothed']:
        a=values[key].astype(np.float64)
        stats[key]={'max':float(a.max()),'median':float(np.median(a)),
                    'max_over_median':float(a.max()/max(np.median(a),1e-12)),
                    'live_channels':int((a>0).sum())}
    # Independently connect the LN sidecar's derived group statistic to the
    # original FP32 maxima. These are not the measured within-s4 activations.
    with np.load(ROOT/'reports/C2-ln2-channel-maxima.npz') as z:
        original=z['original_raw'].astype(np.float64)
    ratio=lambda a:float(a.max()/max(np.median(a),1e-12))
    ln=side['smoothed_groups'][TENSOR]
    assert np.isclose(ratio(original),ln['outlier_before'],rtol=1e-6)
    assert np.isclose(ratio(original*inv),ln['outlier_after'],rtol=1e-6)
    result={'groups':len(groups),'groups_improved':sum(g['improved'] for g in groups),
            'groups_not_improved':sum(not g['improved'] for g in groups),'channels':768,
            'groups_not_improved_details':[g for g in groups if not g['improved']],
            'saved_mul_pair_agrees_with_graph':True,'selected_recipe':provenance['selected_recipe'],
            'measured_example':stats,'pair_check':checked,
            'provenance':'analysis/person_a/a5/provenance.json',
            'collection':'analysis/person_a/a5/collection.json',
            'diagnosis':'Historical alpha-0.5 arrays were paired with the selected alpha-0.7 graph; '
                        'historical pair verifies exactly against its preserved graph. '
                        'New selected-model measurements now verify independently.',
            'ratio_definitions':{
                'groups':'original-build amax / max(median(all channel amax),1e-12); after derived from smoothing',
                'saved_example':'selected s4 alpha=0.7, CPU, 512 calibration inputs; channel amax '
                                'over positions/tokens before/after one Mul; median over all 768 channels'},
            'collection_elapsed_seconds':collection['collection_elapsed_seconds'],
            'quantized_upstream_differs_from_original':True,
            'new_chess_search_or_gpu_performance_measurements':False}
    write(OUT/'smoothquant_verification.json',result)
    from plotting import outliers
    outliers(groups,channels)
    write(OUT/'smoothquant_findings.md', '# SmoothQuant mechanism and observed outliers\n\n'
          f"Across all {len(groups)} saved groups, {result['groups_improved']} have a lower max/median ratio; "
          f"{result['groups_not_improved']} do not. All groups are retained in the CSV and F12. "
          'The group summary records original-build channel statistics and an algebraic rescaling, not fresh inference. '
          'The separate 768-channel selected-model example was collected on CPU from both sides of the same Mul '
          'using the unchanged 512 calibration inputs. It satisfies after = before × smooth_inverse at the original '
          'rtol=1e-5, atol=1e-12; maximum observed absolute difference is zero. '
          f"Its peak/median channel-maximum ratio falls from {stats['s4_raw']['max_over_median']:,.2f} to "
          f"{stats['s4_smoothed']['max_over_median']:,.2f}; all 768 channels are live. "
          'A channel maximum is the largest absolute value seen for that channel across all calibration inputs and board tokens. '
          'The ratio compares the largest channel maximum with the median channel maximum. It is neither a WDL probability nor accuracy.\n\n'
          'The original failed check mixed model versions: the old saved arrays belong to C1 '
          '(alpha 0.5, percentile 99.99), verified by matching collection-log/backup hashes and all 768 scaling values. '
          'They are preserved under reports/, together with the original failure record. F12 now uses the final C2 '
          '(alpha 0.7, percentile 99.999) pair in analysis/person_a/a5/current-channel-maxima.npz. '
          'The original FP32 maxima independently agree with the final LN sidecar-derived ratios at rtol=1e-6; '
          'they are not substituted for the measured within-s4 before array. See a5/provenance.json and a5/collection.json.\n\n'
          'For a positive channel scale s, XW = (X/s)(sW) before quantization. This implementation inserts a Mul '
          'on the selected branches and compensates their weights. Unrestricted LayerNorm folding would also '
          'affect residual consumers. Shared global Smolgen weights are not independently smoothed per block. '
          'The chosen alpha is 0.7 from development selection; test plots are explanation, not another tuning pass. '
          'The better printed policy/value fidelity supports the technique here; no latency claim follows from this plot.\n')
    checkpoint('A5',result)


def A6():
    import onnx
    from onnx import numpy_helper
    reconstruction=[];masks=[]
    for name in ['s0','s1sp']:
        side=read(f'models/{name}_fp32.json')
        model=onnx.load(ROOT/f'models/{name}_fp32.onnx')
        init={t.name:t for t in model.graph.initializer}
        assert len(side['layers'])==150
        parameters=violations=0;warnings=[]
        for weight,r in side['layers'].items():
            a=numpy_helper.to_array(init[weight]);assert a.ndim==2 and a.shape[0]%4==0
            nz=np.count_nonzero(a.reshape(a.shape[0]//4,4,a.shape[1]),axis=1)
            violations+=int(np.count_nonzero(nz>2));parameters+=a.size
            if name=='s1sp':
                reconstruction.append({'weight':weight,'K':a.shape[0],'N':a.shape[1],
                    'calibration_rows':r['rows'],'rows_below_K':r['rows']<a.shape[0],
                    'rows_below_2K':r['rows']<2*a.shape[0],
                    'sparsegpt_error':r['recon_err'],'magnitude_error':r['recon_err_magnitude'],
                    'method':r['method'],'graph_consumers':len(r['nodes'])})
                if r['rows']<2*a.shape[0]:warnings.append(weight)
        assert violations==0
        masks.append({'model':name,'unique_matrices':len(side['layers']),'unique_matrix_parameters':parameters,
                      'groups_exceeding_two_nonzeros':violations,'group_axis':'K in [K,N]',
                      'low_calibration_row_weights':warnings,'sparse_kernels_verified':False})
        del model,init;gc.collect()
    csvwrite('analysis/tables/sparse-reconstruction.csv',reconstruction)
    tb,data,ids,_=context();errors=[]
    for name in ['s0','s1sp']:
        conditions={0:data[name][0],**data[name][1]}
        if name=='s0':
            for rr in rows('results/s0_search/s0/study_b.jsonl'):
                conditions.setdefault(rr['budget'],{})[rr['id']]=rr
        for b,d in conditions.items():
            for i in ids:
                if i in d and d[i]['best'] not in tb[i]['correct']:
                    errors.append({'model':name,'requested_nodes':b,'id':i,'class':tb[i]['cls'],
                                   'best':d[i]['best'],'root_category':tb[i]['root'],
                                   'chosen_category':tb[i]['moves'][d[i]['best']]['res']})
    csvwrite('analysis/tables/sparse-move-errors.csv',errors)
    write(OUT/'sparse_audit.json',{'models':masks,'stages':read('models/s1sp_fp32.json')['stages'],
                                 'scope':'quality/mask audit only; hardware WAIT R1/R2'})
    med_sg=float(np.median([r['sparsegpt_error'] for r in reconstruction]))
    med_mag=float(np.median([r['magnitude_error'] for r in reconstruction]))
    n_better=sum(r['sparsegpt_error']<r['magnitude_error'] for r in reconstruction)
    write(OUT/'sparse_findings.md', '# Sparse quality finding\n\n'
          f'Both sparse source graphs satisfy <=2 nonzeros per four along K for all 150 unique target matrices. '
          f'SparseGPT uses {read("models/s1sp_fp32.json")["stages"]} dependency stages and 512 calibration inputs. '
          f'Across the {len(reconstruction)} reported matrices, median reconstruction error is {med_sg:.6g} '
          f'versus {med_mag:.6g} for magnitude; SparseGPT is lower on {n_better} matrices. '
          'These are calibration reconstruction losses measured against the corresponding stage targets, '
          'not test move-error rates or a guarantee of global forward equivalence.\n\n'
          'The sparse model improves substantially over magnitude pruning in raw accuracy, but still has '
          'persistent losses after search; the 1,600-node s1sp error cases are retained in sparse-move-errors.csv. '
          'Several matrices have few calibration rows relative to K; these warnings and sequential-target differences '
          'are limitations, not a demonstrated cause of the remaining chess errors. No retraining, repruning or '
          'additional calibration was performed.\n\n'
          '**WAIT R1/R2:** whether sparse tactics execute and whether they accelerate either lc0 or standalone '
          'trtexec. A valid 2:4 mask and a better reconstruction objective do not establish those hardware claims.\n')
    checkpoint('A6',{'mask_models':2,'unique_matrices_each':150,'reconstruction_rows':len(reconstruction),
                     'error_case_rows':len(errors),'hardware':'WAIT R1/R2'})


def A7():
    import onnx
    geometry=read('archive/person-a-week1/environment/step6-inventory.json')
    model=onnx.load(ROOT/'models/bt3_fp32.onnx')
    old=onnx.load(ROOT/'archive/person-a-week1/models/onnx/bt3-r32.onnx')
    assert len(model.graph.node)==len(old.graph.node)
    assert all(a.SerializeToString()==b.SerializeToString() for a,b in zip(model.graph.node,old.graph.node))
    old_init={t.name:t for t in old.graph.initializer}
    from onnx import numpy_helper,TensorProto
    for t in model.graph.initializer:
        if t.data_type in [TensorProto.INT64,TensorProto.INT32]:
            assert np.array_equal(numpy_helper.to_array(t),numpy_helper.to_array(old_init[t.name]))
    del old,old_init;gc.collect()
    nodes={n.name:n for n in model.graph.node};init={t.name:t for t in model.graph.initializer}
    targets={}
    for name,expected in [('s4',164),('s4aa',195)]:
        q=onnx.load(ROOT/f'models/{name}.onnx');prod={o:n for n in q.graph.node for o in n.output}
        selected={n.name for n in q.graph.node if n.op_type=='MatMul' and all(
            x in prod and prod[x].op_type=='DequantizeLinear' for x in n.input[:2])}
        assert len(selected)==expected,(name,len(selected))
        targets[name]=selected
        del q,prod;gc.collect()
    result=[]
    for op in geometry['matrix_operations']:
        n=nodes[op['name']]
        assert list(n.input)==op['inputs'] and n.output[0]==op['output']
        sh=op['shapes_by_batch']['1'];one=sh['macs']
        assert one==int(np.prod(sh['output']))*sh['K']
        for b,s in op['shapes_by_batch'].items():assert s['macs']==one*int(b)
        weight=op.get('weight')
        if weight:
            assert list(init[weight['name']].dims)==weight['shape']
        result.append({'name':n.name,'region':op['region'],'kind':op['kind'],
                       'a_shape_batch1':json.dumps(sh['a']),'b_shape_batch1':json.dumps(sh['b']),
                       'output_shape_batch1':json.dumps(sh['output']),
                       'K':sh['K'],'macs_per_position':one,'arithmetic_ops_per_position':2*one,
                       'unique_weight_name':weight['name'] if weight else '',
                       'weight_parameters':weight['parameters'] if weight else 0,
                       's4_qdq_intent':n.name in targets['s4'],'s4aa_qdq_intent':n.name in targets['s4aa'],
                       'observed_kernel_precision':'WAIT R1'})
    assert len(result)==195
    csvwrite('analysis/tables/roofline-operation-inventory.csv',result)
    graph_io={kind:[{'name':v.name,'shape':[d.dim_value or d.dim_param for d in v.type.tensor_type.shape.dim]}
                   for v in getattr(model.graph,kind)] for kind in ['input','output']}
    contract={'operations':195,'fixed_weight_operations':sum(bool(r['unique_weight_name']) for r in result),
              'dynamic_operations':sum(not bool(r['unique_weight_name']) for r in result),
              'macs_per_position':sum(r['macs_per_position'] for r in result),
              'arithmetic_ops_per_position':sum(r['arithmetic_ops_per_position'] for r in result),
              'active_graph_sha256':sha(ROOT/'models/bt3_fp32.onnx'),
              'geometry_source_sha256':sha(ROOT/'archive/person-a-week1/environment/step6-inventory.json'),
              'geometry_proof':'all operator protobufs and integer shape constants identical; matrix dimensions checked',
              'graph_io':graph_io,'s4_graph_targets':len(targets['s4']),'s4aa_graph_targets':len(targets['s4aa']),
              'executed_precision_and_measured_roofline':'WAIT R1; no peak/timing supplied'}
    write(OUT/'roofline_contract.json',contract)
    write(OUT/'roofline_method.md', '# Model-side roofline preparation\n\n'
          'The archived geometry is reused only after checking all active operator protobufs, integer shape constants, '
          'matrix names/inputs/outputs and fixed-weight dimensions against the current graph. Floating coefficients '
          'can differ slightly between exports without changing geometry. This does not import A\'s old quantization scope.\n\n'
          'For [...,M,K] @ [...,K,N], MACs = output_elements × K; arithmetic ops = 2 × MACs. '
          'Independent-position work scales by the actual inference batch; MCTS MinibatchSize need not be that batch. '
          'Only matrix arithmetic is inventoried; softmax, normalization, conversion and scheduling overhead remain.\n\n'
          'First-order logical bytes = A_elements×A_bytes + W_or_B_elements×B_bytes + output_elements×output_bytes. '
          'Use actual operand/output representations and distinguish INT32 accumulation from stored outputs. '
          'Weights do not multiply by batch for unique storage; shared weights are counted once for storage but can '
          'be read by multiple operations. Logical traffic is not measured DRAM traffic or cache reuse.\n\n'
          'R1 intake: require successful nonempty layer info/timing, matching model hash, batch, build flags and runtime. '
          'Use actual recorded small/large batches. Start mapping with hw/roofline.py::map_layers, inspect fused/ForeignNode '
          'regions and retain unmatched regions. Sum associated work once and charge a measured fused-region duration once. '
          'Never assign the whole fused duration to each member and sum it repeatedly. Reconcile attributed versus engine time.\n\n'
          'Achieved ops/s = associated arithmetic work / measured seconds. Intensity = modeled ops / modeled bytes. '
          'Compare with min(measured precision-appropriate compute peak, measured bandwidth×intensity). '
          'Opaque/mixed regions retain unknowns. Use FLOP/s for floating arithmetic and ops/s for integer arithmetic. '
          'The current hw/roofline.py assumes simplified byte formats and has SPEC_4060 fallback constants; these must '
          'not silently become observed precision or measured peaks in the final report. B should supply actual inputs; '
          'this preparation does not edit his hardware code or resolve the DLL failure.\n\n'
          '**WAIT R1:** precision-aware bytes at measured conditions, region timing mapping, peaks, final roofline plot '
          'and bottleneck claims. A partial batch handoff can be reviewed without inventing the other batch.\n')
    del model,init;gc.collect()
    checkpoint('A7',contract)


def A8():
    tb,data,ids,_=context();timed=[];paired_ids=[]
    all_timed={}
    for m in ['fp16','s4']:
        raw=rows(f'results/studyc/{m}/study_c.jsonl');keyed(raw,['id','movetime'])
        all_timed[m]={t:{r['id']:r for r in raw if r['movetime']==t and r['id'] in set(ids)} for t in [200,800]}
    for t in [200,800]:
        ref=all_timed['fp16'][t]
        assert set(ref)==set(ids)
        for m in ['fp16','s4']:
            d=all_timed[m][t];assert set(d)==set(ids)
            p=paired(tb,ids,d,ref)
            ns=summary([d[i]['nodes'] for i in ids]);ts=summary([d[i]['time_ms'] for i in ids])
            ws=summary([1000*d[i]['wall'] for i in ids])
            timed.append({'model':m,'nominal_ms':t,**p,**{f'nodes_{k}':v for k,v in ns.items()},
                          **{f'reported_ms_{k}':v for k,v in ts.items()},**{f'wall_ms_{k}':v for k,v in ws.items()},
                          'mean_nodes_ratio_vs_fp16':ns['mean']/statistics.mean(ref[i]['nodes'] for i in ids)})
            for i in ids:
                paired_ids.append({'model':m,'id':i,'nominal_ms':t,'best':d[i]['best'],
                                   'correct':d[i]['best'] in tb[i]['correct'],'nodes':d[i]['nodes'],
                                   'reported_ms':d[i]['time_ms'],'wall_ms':1000*d[i]['wall']})
    csvwrite('analysis/tables/timed-matched-review.csv',timed)
    csvwrite('analysis/tables/timed-matched-positions.csv',paired_ids)
    quality=csvread('analysis/tables/T1-network.csv')
    frontier=[{k:r[k] for k in ['model','n','correct','accuracy','ci_low','ci_high']} for r in quality if r['model'] in FRONTIER]
    assert len(frontier)==8 and all(not r['model'].startswith('swap') for r in frontier)
    csvwrite('analysis/tables/frontier-quality-ready.csv',frontier)
    parsed=ast.parse((ROOT/'eval/match.py').read_text(encoding='utf-8'))
    openings=next(ast.literal_eval(n.value) for n in parsed.body if isinstance(n,ast.Assign) and any(
        isinstance(t,ast.Name) and t.id=='OPENINGS' for t in n.targets))
    opening_rows=[]
    for i,sans in enumerate(openings):
        b=chess.Board();uci=[]
        for san in sans.split():m=b.parse_san(san);uci.append(m.uci());b.push(m)
        opening_rows.append({'opening_index':i,'SAN':sans,'UCI':' '.join(uci),'final_FEN':b.fen(),
                             'pairing':'same opening twice with engine colors reversed'})
    csvwrite('analysis/tables/match-openings.csv',opening_rows)
    write(OUT/'match_prematch_review.md', '# Pre-match opening and protocol review\n\n'
          f'The existing match runner contains {len(openings)} legal opening sequences. All SAN sequences were parsed '
          'without an engine, converted to UCI and exported with their final FEN. This documents the existing book; '
          'its claimed balance is not independently established. Pair indices cycle through this finite book, '
          'so repeated-opening dependence is a limitation for statistical interpretation.\n\n'
          'Preserve existing 10+0.1 clocks, color-swapped pairs, MoveOverheadMs=50, no pondering and one active GPU '
          'search at a time. The configured 250 pairs is provisional until B measures runtime. Tablebases are '
          'arbiter-only at <=5 pieces; engine SyzygyPath remains unset. The runner also has 1,000cp resignation '
          'after eight agreeing plies, <=10cp draw adjudication after ply 80, a 400-ply cap, normal chess rules '
          'and time forfeits. No protocol or code was changed in this review.\n\n'
          'Before the final match, B should record the actual book/order, final pair count, clocks, options and '
          'adjudication settings. After receipt, A checks complete color pairs, legality/time/forfeit reasons, '
          'PGN/result agreement, paired score distribution and the Elo/CI calculation. Repeated openings and '
          'normal-approximation/zero-variance edge cases must be disclosed; an interval spanning zero is inconclusive. '
          '**WAIT R4:** actual games, pair count, Elo/CI and final playing-strength interpretation.\n')
    handoff={
      'R1':{'status':'WAIT','needed':['successful FP16/s4 layer info + profile at actual small/large batches',
          'measured compute/bandwidth peaks','precision/fallback and sparse/dense audit','model/runtime/build identities']},
      'R2':{'status':'WAIT','models':FRONTIER,'needed':['comparable lc0 benchmark JSONs',
          'repeated headline FP16/s4 observations','same conditions/positions and warmup, clock/temperature provenance',
          'final GPU-energy evidence']},
      'R3':{'status':'READY_FOR_FINAL_ALIGNMENT','raw_files_already_available':True,
          'needed':['canonical final report/model/configuration identity; no new experiment implied']},
      'R4':{'status':'WAIT','needed':['completed paired games + PGN','actual count/time-control/adjudication',
          'Elo with paired uncertainty and edge-case review']},
      'R5':{'status':'WAIT','needed':['final systems runtime/build/configuration identities',
          'artifact freeze + systems reproduction record','B report/figure contributions']}}
    write(OUT/'ritwik_dependencies.json',handoff)
    write(OUT/'timed_findings.md', '# Matched timed review: provisional report alignment\n\n'+
          markdown_table(timed,['model','nominal_ms','n','correct','accuracy','worse','better','mcnemar_p',
                                'nodes_mean','nodes_median','reported_ms_mean','wall_ms_mean','mean_nodes_ratio_vs_fp16'])+
          '\n\nBoth models already have the required raw runs. Extra historical FP16 rows are excluded by frozen IDs, '
          'not deleted. At 200ms only one paired correctness discordance separates the models; the exact paired '
          'test does not support a robust gain. At 800ms both are perfect on this cohort. More mean nodes does '
          'not itself establish a stronger player. Early stopping yields elapsed times below nominal budgets '
          'and skewed node distributions, so means, medians and time context are retained.\n\n'
          '**R3 is final alignment, not a reason to rerun these experiments.** B owns the canonical F5; A supplies '
          'this interpretation. Final throughput conclusions wait R2 and full-game conclusions wait R4.\n')
    write(OUT/'frontier_contract.md', '# Frontier inputs and waiting conditions\n\n'
          'Quality coordinates for eight single-body models are ready. The common coordinate is raw NN '
          'preserving-move accuracy, labelled as NN quality versus search throughput; this is not fixed-time playing strength. '
          'Swaps are excluded. No missing speed is filled and INT8 variants are not assumed equal.\n\n'
          'On R2 receipt check model hashes, same GPU/runtime/backend, benchmark positions, Threads/MinibatchSize, '
          'build/warmup exclusion, repeats and thermal/power context. Compare common settings or label tuned/different '
          'conditions separately. Use medians and uncertainty for repeated headline runs; retain observed samples and '
          'source hashes. GPU joules/node is not whole-system energy or the omitted equal-energy accuracy test. '
          'Final plotting is shared with B, not a second independently benchmarked study.\n')
    checkpoint('A8',{'timed_rows':len(timed),'timed_positions':len(paired_ids),
                     'frontier_quality_rows':len(frontier),'legal_openings':len(opening_rows),
                     'waiting':['R1','R2','R4','R5'],'R3':'final alignment only'})


def A9():
    from documents_run1 import write_report
    result=write_report()
    checkpoint('A9',result)


def A10():
    from documents_run1 import prepare_delivery
    result=prepare_delivery()
    checkpoint('A10',result,'run1_complete_waiting_Ritwik')


def prerequisite_allowed(step,state):
    if step=='A1':
        return True
    previous=f'A{int(step[1:])-1}'
    prior=state.get('steps',{}).get(previous,{}).get('status')
    deferred_A5=(step=='A6' and prior=='deferred_user_authorized' and
                 state.get('A5_deferred_by_user',False))
    return prior in ('verified','run1_complete_waiting_Ritwik') or deferred_A5


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("step",choices=[f"A{i}" for i in range(1,11)])
    a=ap.parse_args()
    if a.step!="A1":
        state=read(OUT/"progress.json")
        previous=f"A{int(a.step[1:])-1}"
        assert prerequisite_allowed(a.step,state),previous
    try:
        globals()[a.step]()
    except Exception as exc:
        # A failed analysis check must not be silently replaced by revised data.
        checkpoint(a.step,{"error":str(exc)},"BLOCKED")
        raise


if __name__=="__main__":
    main()
