"""CPU-only canonical timed reporting, figures, match sizing and fresh artifacts."""
import argparse
import csv
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from execution.support import ROOT, identity, read_json, atomic_json
from analysis.person_a.run3_systems import REPORT, TABLE, MODELS, csvread, csvwrite, catalog
from analysis.person_a.run1 import paired, summary
from analysis.person_a.plotting import COLORS

FIG = ROOT / 'analysis/figures'


def jsonlines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def timed():
    ids = sorted(int(i) for i in (ROOT / 'analysis/person_a/run1/cohort_ids.txt').read_text().split())
    if len(ids) != 2437 or len(set(ids)) != 2437: raise ValueError('Wrong frozen cohort')
    tb = {r['id']: r for r in jsonlines(ROOT / 'data/tbset.jsonl')}
    data = {}; extras = {}; sources = [identity(ROOT / 'data/tbset.jsonl')]
    for model in ('fp16', 's4'):
        path = ROOT / 'results/studyc' / model / 'study_c.jsonl'; raw = jsonlines(path)
        keys = [(r['id'], r['movetime']) for r in raw]
        if len(keys) != len(set(keys)): raise ValueError('Duplicate timed keys')
        data[model] = {t: {r['id']: r for r in raw if r['movetime'] == t and r['id'] in set(ids)} for t in (200, 800)}
        extras[model] = len(raw) - sum(len(d) for d in data[model].values()); sources.append(identity(path))
    rows = []; positions = []
    for t in (200, 800):
        reference = data['fp16'][t]
        for model in ('fp16', 's4'):
            d = data[model][t]
            if set(d) != set(ids): raise ValueError('Timed IDs mismatch')
            ns = summary([d[i]['nodes'] for i in ids])
            row = {'model': model, 'nominal_ms': t, **paired(tb, ids, d, reference),
                   **{'nodes_' + k: v for k, v in ns.items()},
                   **{'reported_ms_' + k: v for k, v in summary([d[i]['time_ms'] for i in ids]).items()},
                   **{'wall_ms_' + k: v for k, v in summary([d[i]['wall'] * 1000 for i in ids]).items()},
                   'mean_nodes_ratio_vs_fp16': ns['mean'] / statistics.mean(reference[i]['nodes'] for i in ids)}
            rows.append(row)
            positions.extend({'model': model, 'id': i, 'nominal_ms': t, 'best': d[i]['best'],
                              'correct': d[i]['best'] in tb[i]['correct'], 'nodes': d[i]['nodes'],
                              'reported_ms': d[i]['time_ms'], 'wall_ms': d[i]['wall'] * 1000} for i in ids)
    old = csvread(TABLE / 'timed-matched-review.csv')
    for r, ref in zip(rows, old):
        for k, v in r.items():
            if isinstance(v, (int, float)):
                if not math.isclose(v, float(ref[k]), rel_tol=1e-10, abs_tol=1e-10): raise ValueError('Prior timed review disagrees: ' + k)
            elif v != ref[k]: raise ValueError('Prior timed row order/model disagrees')
    csvwrite(TABLE / 'T6-timed-canonical.csv', rows)
    csvwrite(TABLE / 'T6-timed-positions.csv', positions)
    atomic_json(REPORT / 'timed-canonical.json', {'sources': sources, 'cohort_n': 2437, 'rows': rows,
                'extra_historical_rows_preserved_not_scored': extras, 'prior_review_exactly_reproduced': True,
                'interpretation': '200ms: one paired difference, exact p=1;800ms: both saturated. No robust fixed-time accuracy gain established.',
                'settings': 'Original Study C settings retained; nominal200/800ms differ from realized time; no new engine run'})
    return rows


def sizing():
    pilot_job = catalog()['match-estimate-2']
    folder = Path(pilot_job['attempt']) / 'work/pilot'
    estimate = read_json(folder / 'estimate.json'); contract = read_json(folder / 'contract.json')
    if estimate['games'] != 2: raise ValueError('Wrong planning pilot')
    pairs = 250; game_hours = 2 * pairs * estimate['seconds_per_game'] / 3600
    score_margin = 1.96 * 0.5 / math.sqrt(pairs)
    worst_elo_margin = 400 * math.log10((0.5 + score_margin) / (0.5 - score_margin))
    result = {'schema_version': 1, 'frozen_before_production': True, 'pairs': pairs, 'games': pairs * 2,
              'frozen_unix': time.time(), 'production_started': False,
              'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'pilot_estimate': identity(folder / 'estimate.json'), 'pilot_contract': identity(folder / 'contract.json'),
              'seconds_per_game_observed': estimate['seconds_per_game'], 'production_game_hours_point_estimate': game_hours,
              'run4_planning_hours': [5, 6], 'run4_reserve_hours': 7,
              'allocation': 'game estimate3.746h;25-35% duration contingency plus fresh GPU checks/engine builds and post-measurement demo',
              'selection_rule': 'Keep the existing250-pair candidate because observed runtime fits one exclusive session; use five cycles of50 openings, both colors. No outcome-based sizing.',
              'settings': contract['settings'], 'engines': contract['engines'], 'openings': contract['opening_book'],
              'syzygy_arbiter_only': True, 'same_clocks_and_adjudication': True,
              'precision_limit': {'worst_case_95_score_halfwidth_if_independent_pairs': score_margin,
                                  'approx_Elo_halfwidth_near_equal_score': worst_elo_margin,
                                  'limitation': 'Not a guaranteed CI or power calculation:50 repeated openings, pair correlation and unknown draws reduce effective information.'},
              'completion_rule': 'Exactly250 complete color-swapped pairs; no outcome-based early stop/resizing; resume committed games after authorized review',
              'pilot_outcomes_used_for_size': False, 'strength_inference_from_pilot': False}
    path = REPORT / 'match-sizing.json'
    if path.exists():
        previous = read_json(path)
        # Frozen count is not changed by a rerun of this normal preparation.
        if previous['pairs'] != pairs or previous['pilot_estimate'] != result['pilot_estimate']:
            raise ValueError('Previously frozen match sizing differs')
        return previous
    atomic_json(path, result)
    return result


def fresh_artifacts():
    from maintenance import artifacts
    setup = read_json(REPORT / 'fresh_setup.json')
    if setup['status'] != 'fresh_source_and_python_environment_ready': raise ValueError('Fresh setup incomplete')
    workspace = Path(setup['workspace']); repo = Path(setup['repo']); control = workspace / 'control'
    files = ['models/fp16.pb.gz', 'models/s4.pb.gz', 'models/s1sp.pb.gz', 'models/s1sp.onnx',
             'nets/BT3.pb.gz', 'data/tbset.jsonl']
    manifest = {'schema_version': 1, 'roots': list(artifacts.ROOTS),
                'files': [{'path': p, 'bytes': (ROOT / p).stat().st_size, 'sha256': artifacts.digest(ROOT / p)} for p in files],
                'scope': 'Declared FP16/s4/SparseGPT reproduction subset, not the full final research bundle'}
    bundle = workspace / 'reproduction-artifacts.zip'
    if not bundle.exists(): artifacts.pack(bundle, manifest, ROOT)
    restored, skipped = artifacts.restore(bundle, repo)
    if artifacts.verify(manifest, repo): raise ValueError('Fresh restored artifact mismatch')
    config = read_json(ROOT / 'config.json')
    for key in ('lc0', 'trtexec', 'nsys', 'syzygy'): config[key] = str((ROOT / config[key]).resolve())
    config['work'] = str(repo); config['bt3'] = str(repo / 'nets/BT3.pb.gz')
    (repo / 'config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8', newline='\n')
    py = Path(setup['venv']) / 'Scripts/python.exe'
    packages = subprocess.check_output([str(py), '-B', '-m', 'pip', 'freeze'], text=True)
    (control / 'installed-packages.txt').write_text(packages, encoding='utf-8', newline='\n')
    tracked = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=repo, text=True)
    if tracked.strip(): raise ValueError('Fresh source was modified')
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip() != setup['source_revision']:
        raise ValueError('Fresh source revision mismatch')
    atomic_json(REPORT / 'fresh-artifact-restore.json', {'workspace': str(workspace), 'repo': str(repo),
        'source_revision': setup['source_revision'], 'fresh_venv': setup['venv'], 'bundle': identity(bundle),
        'manifest': manifest, 'restored': restored, 'already_identical': skipped,
        'native_tools_reused_same_host': True, 'old_venv_copied': False, 'tracked_source_clean': True,
        'installed_package_snapshot': identity(control / 'installed-packages.txt'),
        'GPU_reproduction_executed': False, 'limitation': 'Same hardware and native tool installation; independent Python/source/artifact setup, not cross-machine validation'})
    return repo


def save(fig, name, caption):
    FIG.mkdir(exist_ok=True); fig.tight_layout(rect=(0, .11, 1, .94))
    fig.text(.02, .015, caption, fontsize=8, va='bottom')
    for suffix in ('png', 'pdf', 'svg'): fig.savefig(FIG / (name + '.' + suffix), bbox_inches='tight', dpi=170)
    plt.close(fig)


def plots():
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    timed_rows = csvread(TABLE / 'T6-timed-canonical.csv')
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.4))
    for model in ('fp16', 's4'):
        rows = [r for r in timed_rows if r['model'] == model]; x = [int(r['nominal_ms']) for r in rows]
        for ax, key, title in zip(axes, ('errors', 'nodes_mean', 'wall_ms_mean'),
                                   ('Move errors / 2,437', 'Mean actual visits', 'Mean measured wall time (ms)')):
            ax.plot(x, [float(r[key]) for r in rows], 'o-', label=model, color=COLORS[model])
            ax.set_xticks([200, 800]); ax.set_title(title); ax.set_xlabel('Nominal budget (ms)'); ax.grid(alpha=.2)
    axes[0].set_ylim(-.08, 1.2); axes[1].legend(); fig.suptitle('F5 · Canonical fixed-time results on matched roots')
    save(fig, 'F5-time', 'Original 200/800 ms runs; identical 2,437 IDs. One paired discordance at 200 ms (p=1); both perfect at 800 ms.\nActual early stopping and skewed visit distributions are retained in T6. This does not establish a strength gain.')

    profiles = csvread(TABLE / 'T2-standalone-profiles.csv')
    rows = [r for r in profiles if r['model'] in ('fp16', 's4')]
    fig, ax = plt.subplots(figsize=(11, 4.8)); x = np.arange(len(rows)); bottom = np.zeros(len(rows))
    categories = [('fp16_gemm_ms', 'Visible FP16 GEMM'), ('int8_gemm_ms', 'Visible INT8 GEMM'),
                  ('opaque_fused_matrix_ms', 'Opaque matrix fusion'), ('norm_softmax_fused_ms', 'Norm/softmax/attention fusion'),
                  ('conversion_ms', 'Conversion'), ('other_fused_ms', 'Other fusion / unresolved attention')]
    for key, label in categories:
        vals = np.array([float(r[key]) for r in rows]); ax.bar(x, vals, bottom=bottom, label=label); bottom += vals
    ax.set_xticks(x, [r['model'] + '\nB=' + r['batch'] for r in rows]); ax.set_ylabel('Sum of profiled layer averages (ms)')
    ax.legend(fontsize=8, loc='upper left', bbox_to_anchor=(1.01, 1)); ax.set_title('F6a · Standalone TensorRT layer-time breakdown')
    save(fig, 'F6-profile-breakdown', 'Each measured region is counted once. Profile sums include profiler overhead; non-profile GPU latency is separate in T2.\nThe INT8 graph leaves 30 attention matmuls unresolved by exact metadata; no precision is guessed for them.')

    peaks = read_json(REPORT / 'measured-reference-peaks.json'); points = csvread(TABLE / 'F6-roofline-points.csv')
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.9)); xx = np.logspace(-1, 5, 250)
    for ax, pr in zip(axes, ('fp16', 'int8')):
        pk = peaks[pr]['gemm_reference_rate']; bw = peaks['bandwidth']['gemm_reference_rate']
        ax.plot(xx, np.minimum(pk, xx * bw / 1000), '--', color='#333', label='Measured GEMM reference')
        for model, marker in (('fp16', 'o'), ('s4', 's')):
            rows = [r for r in points if r['precision'] == pr and r['model'] == model]
            if not rows: continue
            ax.scatter([float(r['ops_per_modeled_byte']) for r in rows],
                       [float(r['achieved_tera_ops_s']) for r in rows], s=16, alpha=.4,
                       marker=marker, color=COLORS[model], label=model + ' single-matrix regions')
        ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlabel('Arithmetic operations / modeled byte')
        ax.set_ylabel('Tera arithmetic operations/s'); ax.set_title(pr.upper() + ' operands; B=64/256'); ax.grid(alpha=.2); ax.legend(fontsize=8)
    fig.suptitle('F6b · Precision-aware modeled roofline (directly mapped subset)')
    save(fig, 'F6-roofline', 'FP16 axis uses FLOP/s; INT8 axis uses integer ops/s (2 operations/MAC). Roof is a measured microbenchmark reference.\nLogical I/O+weight bytes are not measured DRAM traffic. Packed/opaque regions are excluded; references are not hard limits.')

    speed = csvread(TABLE / 'T2-speed.csv'); fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, key, title in zip(axes, ('gpu_mJ_node_total', 'gpu_mJ_node_above_idle'),
                              ('Total GPU energy under load', 'Reported above-idle energy · provisional')):
        y = [float(r[key + '_median']) for r in speed]
        lo = [v - float(r[key + '_min']) for v, r in zip(y, speed)]
        hi = [float(r[key + '_max']) - v for v, r in zip(y, speed)]
        ax.bar(range(len(speed)), y, color=[COLORS[r['model']] for r in speed], yerr=[lo, hi], capsize=3)
        ax.set_xticks(range(len(speed)), [r['model'] for r in speed], rotation=25); ax.set_ylabel('GPU mJ / search visit')
        ax.set_title(title); ax.grid(axis='y', alpha=.2)
    fig.suptitle('F7 · GPU energy at the common search setting')
    save(fig, 'F7-energy', 'Medians; whiskers are repeat ranges, not confidence intervals. Under-load counter/sample means agree within0.60%.\nRepeated impossible idle power samples prevent validating the subtraction. Both measures retained; no equal-energy accuracy claim.')

    front = csvread(TABLE / 'F11-frontier.csv'); fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, zoom in zip(axes, (False, True)):
        for r in front:
            if zoom and r['model'] == 's0': continue
            x = float(r['search_nps_median']); y = 100 * float(r['raw_preserving_move_accuracy'])
            ax.errorbar(x, y, xerr=[[x - float(r['search_nps_min'])], [float(r['search_nps_max']) - x]],
                        yerr=[[y - 100 * float(r['accuracy_ci_low'])], [100 * float(r['accuracy_ci_high']) - y]],
                        fmt='o', color=COLORS[r['model']], capsize=3)
            if zoom or r['model'] in ('s0', 'fp16', 's4'):
                offset = (3, -16) if zoom and r['model'] == 's1' else (5, 5)
                ax.annotate(r['model'], (x, y), xytext=offset, textcoords='offset points', fontsize=9)
        ax.set_xlabel('lc0 search visits/s (median; minibatch cap 64)'); ax.set_ylabel('Raw NN preserving-move accuracy (%)')
        ax.set_title('Detail excluding s0' if zoom else 'All eight models'); ax.grid(alpha=.2)
        if zoom: ax.set_ylim(98.45, 100.1)
    fig.suptitle('F11 · NN quality / search throughput coordinates')
    save(fig, 'F11-frontier', 'x whiskers: repeat min/max; y whiskers: marginal Wilson intervals on the same 2,437 roots (correlated models).\nNN move quality and search throughput are different workloads. This is not fixed-time accuracy, Elo or a strength frontier.')
    return {'figures': ['F5-time', 'F6-profile-breakdown', 'F6-roofline', 'F7-energy', 'F11-frontier']}


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('stage', choices=('timed', 'sizing', 'artifacts', 'plots'))
    args = ap.parse_args(); result = {'timed': timed, 'sizing': sizing, 'artifacts': fresh_artifacts, 'plots': plots}[args.stage]()
    print('VERIFIED_CPU_PREPARATION ' + args.stage)


if __name__ == '__main__': main()
