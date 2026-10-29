"""Audit the active Person A Week 1 handoff without asserting joint completion."""
import argparse
import ast
import collections
import json
import re
from pathlib import Path

import chess
import chess.syzygy
import numpy as np

from complete_week1_v2 import (PROJECT,WORK,DEST,DATA,PROTOCOL,KEYS,artifact,
    base,read,save,rows,checkpoint,frozen)
from lc0_inputs import legal_move_indices

AUDIT = PROJECT/'environment/week1-v2-audit.json'
LEDGER = PROJECT/'environment/week1-v2-evidence-manifest.json'
HANDOFF = PROJECT/'docs/week1-v2-person-a-handoff.md'


def independent_scoring():
    """Recompute policy selection and selected-child WDL using local tables."""
    report = []
    tables = base.RUNTIME/'syzygy'
    with chess.syzygy.open_tablebase(str(tables)) as tb:
        for split in ['calibration','validation','test']:
            names = ['R32_CUDA','F16_TRT']+(['I1_TRT'] if split=='validation' else [])
            records = rows(split)
            for name in names:
                with np.load(DEST/f'{split}-{name}-outputs.npz',allow_pickle=False) as d:
                    logits = d['logits'].copy(); ids = d['ids'].copy()
                predictions = [json.loads(s) for s in (DEST/f'{split}-{name}-predictions.jsonl').read_text().splitlines()]
                assert len(logits)==len(predictions)==len(records)
                errors = 0
                for i,(root,pred) in enumerate(zip(records,predictions)):
                    assert str(ids[i])==root['id']==pred['id']
                    board = chess.Board(root['fen'])
                    mapping = legal_move_indices(board)
                    legal = sorted(mapping)
                    values = np.asarray([logits[i,mapping[m]] for m in legal],dtype=np.float32)
                    exp = np.exp(values-values.max()).astype(np.float32)
                    probabilities = exp/exp.sum(dtype=np.float32)
                    chosen = legal[int(np.argmax(probabilities))]
                    assert chosen==pred['move']
                    root_wdl = tb.probe_wdl(board)
                    root_sign = int(root_wdl>0)-int(root_wdl<0)
                    assert root_sign==root['root_outcome']
                    board.push_uci(chosen)
                    if board.is_checkmate(): child_sign=-1
                    elif board.is_stalemate() or board.is_insufficient_material(): child_sign=0
                    else:
                        wdl = tb.probe_wdl(board); child_sign=int(wdl>0)-int(wdl<0)
                    chosen_outcome = -child_sign
                    assert chosen_outcome==root['move_outcomes'][chosen]==pred['selected_outcome']
                    error=chosen_outcome<root_sign
                    assert error==pred['error']; errors+=error
                report.append({'split':split,'model':name,'n':len(records),'errors':errors,
                    'all_ids_legal_move_selection_and_local_tablebase_scores_match':True})
                print('Independent selected-move scoring verified',split,name,len(records),'errors',errors,flush=True)
    return report


def provenance():
    # The first inference source was captured by hash and reconstructed exactly
    # after a diagnostic-only repair. Point to the hash-verified executed copy.
    snapshot=WORK/'complete-executed-d2b7f0839143da8f.py'
    for path in DEST.glob('*-inference.json'):
        record=read(path)
        if base.sha256(record['script']['path']) != record['script']['sha256']:
            assert snapshot.exists() and base.sha256(snapshot)==record['script']['sha256']
            record['original_source_location']=record['script']['path']
            record['script']=artifact(snapshot)
            record['provenance_note']='Exact executed source retained externally by matching original recorded SHA; later repair changed only non-aborting drift diagnostics, not inference or saved outputs.'
            save(path,record)


def polish_activation_figure():
    """Render the same frozen statistics on a readable logarithmic histogram."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    path=DEST/'calibration-outliers.json'; report=read(path)
    meta=report['groups']; ordered=sorted(meta,key=lambda m:m['largest_over_median_channel_max'],reverse=True)
    with np.load(DEST/'calibration-channel-statistics.npz',allow_pickle=False) as arrays:
        fig,axes=plt.subplots(1,2,figsize=(12,4.5),constrained_layout=True)
        ratios=np.array([m['largest_over_median_channel_max'] for m in meta])
        bins=np.geomspace(max(ratios.min(),1e-6),ratios.max()*1.001,26)
        axes[0].hist(ratios,bins=bins,color='#245ea5',edgecolor='white'); axes[0].set_xscale('log')
        axes[0].set(xlabel='Largest / median channel maximum (log scale)',ylabel='Activation tensors',title='Imbalance across 113 calibration tensors')
        for m in ordered[:5]:
            mx=arrays[f'g{m["index"]}_activation_channel_max']
            axes[1].plot(np.linspace(0,1,len(mx)),np.sort(mx)/max(np.median(mx),1e-12),label=m['tensor'].replace('/encoder','/e')[-40:])
        axes[1].set(xlabel='Channel quantile',ylabel='Channel maximum / median',yscale='log',title='Five most imbalanced inputs')
        axes[1].legend(fontsize=7)
        figure=PROJECT/'docs/figures/week1-v2-channel-outliers.png'
        fig.savefig(figure,dpi=150); plt.close(fig)
    report['figure']=artifact(figure)
    report['figure_render_note']='Same saved statistics, logarithmic histogram axis to show all tensors despite one extreme max/median ratio; no new model inference or altered statistics.'
    report['figure_renderer']=artifact(Path(__file__))
    save(path,report)
    analysis_path=PROJECT/'environment/week1-v2-analysis.json'; record=read(analysis_path)
    record['activation_statistics']=artifact(path); save(analysis_path,record)
    document=PROJECT/'docs/week1-v2-activation-analysis.md'
    text=document.read_text()
    note='A very large max/median ratio can reflect a near-zero median as well as a large peak. Absolute maxima and medians are included in the JSON; ratios alone are not evidence of large absolute activations. The histogram uses a logarithmic horizontal axis.\n'
    if note not in text: document.write_text(text+'\n'+note)


def audit():
    checkpoint('W1-A17','IN_PROGRESS',detail='Auditing current Person A artifacts, independent selected-move scoring, provenance and reproducible handoff.')
    frozen(); provenance(); polish_activation_figure()
    state=read(PROJECT/'environment/week1-progress.json')
    assert all(state['tasks'][f'W1-A{i}']['status']=='DONE' for i in range(13,17))
    assert not state['roadmap']['joint_C1_complete'] and not state['roadmap']['Week2_started']
    manifest=read(DATA/'manifest.json')
    assert artifact(DATA/'manifest.json')==read(PROJECT/'environment/week1-input-refresh.json')['dataset_manifest']
    for value in manifest['splits'].values():
        for key in ['inputs','positions']:
            assert artifact(value[key]['path'])==value[key]
    source_hash=read(PROJECT/'environment/week1-input-refresh.json')['script']['sha256']
    assert base.sha256(PROJECT/'scripts/refresh_inputs_week1.py')==source_hash
    old=read(PROJECT/'environment/week1-evidence-manifest.json')
    historical=[]; intended_changes={'docs/project-roadmap.md','environment/week1-progress.json'}
    for item in old['project_artifacts']:
        path=PROJECT/item['relative_path']
        equal=base.sha256(path)==item['sha256']
        assert equal or item['relative_path'] in intended_changes,path
        historical.append({'relative_path':item['relative_path'],'hash_unchanged':equal})
    for path in [PROJECT/'scripts/complete_week1_v2.py',PROJECT/'scripts/refresh_int8_week1.py',
                 PROJECT/'scripts/tune_batches_week1.py',PROJECT/'scripts/refresh_analysis_week1.py',Path(__file__)]:
        ast.parse(path.read_text(),filename=str(path))
    assert not (PROJECT/'tmp').exists()
    assert not list(DEST.glob('test-I1*'))
    independent=independent_scoring()
    float_report=read(DEST/'baseline-accuracy.json')
    for item in independent:
        expected=(read(DEST/'int8-validation.json')['scoring']['strata']['all'] if item['model']=='I1_TRT'
                  else float_report['splits'][item['split']][item['model']]['strata']['all'])
        assert item['n']==expected['n'] and item['errors']==expected['errors']
    analysis=read(PROJECT/'environment/week1-v2-analysis.json')
    assert analysis['status']=='passed' and not analysis['training_performed']
    pilot=read(PROJECT/'environment/week1-v2-int8-pilot.json')
    assert pilot['status']=='passed_A_side'
    tuning=read(DEST/'batch-tuning.json')
    assert tuning['status']=='passed_bounded_batch_tuning'
    precision=[]
    for path in (PROJECT/'environment').glob('week1-v2-*-engine.json'):
        record=read(path)
        assert record['status']=='passed_execution'
        kernels={}
        for item in record['precision_evidence']:
            assert base.sha256(item['path'])==item['sha256']
            if item['path'].endswith('-kernels.json'):
                trace=read(item['path'])
                kernels=collections.Counter(e['name'] for e in trace['traceEvents'] if e.get('cat')=='kernel')
        fp32_gemm=[name for name in kernels if any(s in name.lower() for s in ['f32f32','sgemm','tf32'])]
        assert not fp32_gemm,fp32_gemm
        if record['kind']=='I1': assert record['actual_INT8_targets']==160 and record['executed_INT8_kernels']
        else: assert len(record['floating_matmuls_fp16'])==195 and record['executed_FP16_kernels']
        precision.append({'record':artifact(path),'kind':record['kind'],
            'INT8_targets':record['actual_INT8_targets'],'FP32_or_TF32_GEMM_kernel_names_observed':fp32_gemm,
            'declared_norm_FP32_compute':len(record['normalization_fp32_compute']),
            'executed_kernel_name_evidence_verified':True})
    result={'status':'passed_Person_A_only','verified_at_utc':base.now(),
        'protocol':artifact(PROTOCOL),'dataset':artifact(DATA/'manifest.json'),
        'all_A13_A16_verified_before_A17':True,'independent_scoring':independent,
        'historical_artifacts':historical,'historical_unchanged_count':sum(x['hash_unchanged'] for x in historical),
        'intentional_historical_tracker_changes':sorted(intended_changes),
        'source_scripts_parse':True,'no_project_tmp':True,'INT8_final_test_evaluated':False,
        'new_engine_precision_and_saved_trace_audit':precision,
        'Person_B_and_joint_C1':'UNVERIFIED; separate responsibilities, no teammate sign-off inferred',
        'Week2_started':False,'remaining_Person_A_Week1_work':[],
        'recorded_limitations':['Very high baseline accuracy leaves only 10 test errors for possible improvement; harder-set/search study remains B/joint work.',
          'FP16 numerical drift and the raw legacy probability-sum failure remain disclosed; no output renormalization or forced FP32 parity.',
          'Batch tuning uses separately identified engines for larger shapes; no universal optimum or MCTS-strength conclusion.',
          'Naive INT8 speed/quality are measurements, not success requirements.']}
    save(AUDIT,result)
    print('Person A audit passed; handoff/ledger finalization pending',flush=True)


def write_handoff():
    audit=read(AUDIT); assert audit['status']=='passed_Person_A_only'
    baseline=read(DEST/'baseline-accuracy.json'); int8=read(DEST/'int8-validation.json')
    tuning=read(DEST/'batch-tuning.json'); scope=read(PROJECT/'environment/step6-scope-v2.json')
    pilot=read(PROJECT/'environment/week1-v2-int8-pilot.json')
    analysis=read(DEST/'calibration-outliers.json')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure,axes=plt.subplots(1,2,figsize=(11,4.5),constrained_layout=True)
    colors={'F16_TRT':'#245ea5','I1_TRT':'#bf4a24'}
    for sweep in tuning['sweeps']:
        data=read(sweep['path'])
        if data['label'].startswith('finalists') or data['label']=='refinement': continue
        for name,values in data['combined'].items():
            points=sorted(values.values(),key=lambda r:r['batch'])
            style='--' if data['label']=='preserved' else '-'
            label=f'{name}, {data["label"]}'
            axes[0].plot([p['batch'] for p in points],[p['resident_gpu']['median_ms'] for p in points],style,color=colors[name],marker='.',label=label)
            axes[1].plot([p['batch'] for p in points],[p['resident_amortized_ms_per_position'] for p in points],style,color=colors[name],marker='.',label=label)
    for name in colors:
        for ax,which in zip(axes,['resident_latency','resident_throughput']):
            point=tuning['optima'][name][which]
            value=point['resident_gpu']['median_ms'] if which=='resident_latency' else point['resident_amortized_ms_per_position']
            ax.scatter([point['batch']],[value],marker='*',s=120,color=colors[name],edgecolor='black',zorder=5)
    for ax in axes:
        ax.set_xscale('log',base=2); ax.set_yscale('log'); ax.set_xlabel('Batch size'); ax.grid(alpha=.2)
    axes[0].set(ylabel='Complete-batch resident GPU latency (ms)',title='Response time for a complete batch')
    axes[1].set(ylabel='Resident GPU latency / batch (ms per position)',title='Amortized time: throughput objective')
    axes[0].legend(fontsize=7)
    figure_path=PROJECT/'docs/figures/week1-v2-batch-latency.png'
    figure.savefig(figure_path,dpi=160); plt.close(figure)
    lines=['# Person A Week 1: active verified handoff','',
        'Person A model/data responsibilities are complete. Person B integration, search/scoring extensions, systems/energy work and joint C1 remain separately unverified. Week 2 has not started.','',
        'The active run is `syzygy-v2` / `week1-v2`. Historical artifacts under `data/syzygy`, `results/week1` and the original handoff remain preserved.','',
        '| Completion step | Verified outcome | Evidence |','| --- | --- | --- |',
        '| 1 / A13 | 13,072 published four/five-piece roots and documented mirrors; source, splits, local labels and native fen_only encoding verified | [Input verification](../environment/week1-input-refresh.json) |',
        '| 2 / A14 | Exact two floating baselines, native/batch checks, all-split chosen-move accuracy and numerical drift | [Baseline results](../results/week1-v2/baseline-accuracy.json) |',
        '| 3 / A15 | Naive INT8 recalibrated; actual execution, reload, wrapper, validation and batch tuning | [Pilot](../environment/week1-v2-int8-pilot.json) |',
        '| 4 / A16 | Calibration-only activation statistics and existing-port forward compatibility | [Analysis](../environment/week1-v2-analysis.json) |',
        '| 5 / A17 | Artifact, scoring, historical-preservation and handoff audit | [Audit](../environment/week1-v2-audit.json) |','',
        '## Network-only chosen-move accuracy','',
        'Select the highest legal policy probability (float32 softmax, temperature 1, lexical UCI ties). A W→D/L or D→L move is an error, judged from the original mover’s perspective by external theoretical Syzygy WDL. Tablebases do not supply the NN inputs or select its move. This measures move-outcome preservation, not the NN value head’s WDL class, MCTS strength, Elo, or DTZ-optimality.','',
        '| Split | R32_CUDA | F16_TRT | I1_TRT |','| --- | ---: | ---: | ---: |']
    for split in ['calibration','validation','test']:
        values=[baseline['splits'][split][name]['strata']['all'] for name in ['R32_CUDA','F16_TRT']]
        other=int8['scoring']['strata']['all'] if split=='validation' else None
        lines.append('| '+split+' | '+' | '.join(f'{v["n"]-v["errors"]:,}/{v["n"]:,} ({v["accuracy"]:.4%})' for v in values)+' | '+(f'{other["n"]-other["errors"]:,}/{other["n"]:,} ({other["accuracy"]:.4%})' if other else 'Not evaluated')+' |')
    ds=baseline['splits']['test']['F16_TRT']['strata']['decision_sensitive']
    lines+=['',f'Test decision-sensitive subset: {ds["n"]:,} roots; FP16 accuracy {ds["accuracy"]:.4%}. This subset merely has at least one outcome-losing move; it is not the later hard-subset definition. All saved selected moves and outcomes were independently recomputed and locally tablebase-probed.','',
        '**Research limitation:** both floating baselines make only 10 errors in 10,000 test roots. This benchmark leaves little accuracy headroom for demonstrating a further search benefit; the later hard-subset/search study must account for that. No dataset redesign or test-driven tuning was performed.','',
        'The corpus is balanced by piece count, side and W/D, using one published game root per game, plus documented color/rank mirrors. It uses four/five pieces, not six/seven. Halfmove clocks are normalized under the theoretical-WDL contract, which ignores the fifty-move limit. Both corpus and history differ from the historical 55.42% result, so their individual contributions are not isolated.','',
        '## Numerical outputs and correctness','',
        'The network emits 1,858 policy logits, three side-to-move value probabilities (win/draw/loss), and one moves-left estimate. WDL numerical drift compares the value probabilities between runtimes; it is separate from tablebase chosen-move accuracy.','',
        'FP32 passed the 32-case native Eigen and batch-consistency checks within the original FP32 gates. FP16 is explicitly retained as a separately measured baseline, with raw numerical failures preserved rather than relabeled as passes.','',
        '| Split | Maximum FP16/FP32 WDL component difference | Positions failing any recorded legacy check |','| --- | ---: | ---: |']
    for split in ['calibration','validation','test']:
        drift=baseline['splits'][split]['drift']
        lines.append(f'| {split} | {100*drift["summary"]["wdl_max_abs"]:.4f} percentage points | {drift["failed_position_count_at_historical_limits"]} |')
    lines+=['','One test FP16 WDL row has a probability-sum error of about 0.1058 percentage points, just above the legacy comparator’s 0.1-point check. The existing standalone-runner validity check is 0.2 points. This failed legacy check is recorded; raw outputs were not normalized. Historical larger-drift evidence and earlier acceptance also remain intact.','',
        '## INT8 artifact and scope','',
        f'All 1,024 calibration roots supplied the new max-calibration scales. Scope v2 remains {len(scope["targets"])} selected fixed-weight multiplications, {scope["weight_parameter_fraction"]:.4%} of unique matrix weights and {scope["matrix_MAC_fraction"]:.4%} of matrix MACs. All selected operations were mapped to actual INT8 execution; kernel traces confirm it.','',
        'The recipe is signed symmetric per-tensor W8A8. Selected multiplications use INT8 operands and INT32 accumulation; TensorRT may emit FP32 dequantized intermediates, FP16 or requantized INT8. Four tiny weighted operations, 31 dynamic matrix products, normalization and other exceptions remain floating as documented. This is a mixed-precision model. ONNX Q/DQ weight source constants remain FP16, while engine operand execution and storage are separately audited.','',
        'Saved-engine reload outputs match exactly. The lc0 wrapper contains a byte-identical copy of the new ONNX graph. Actual lc0 GPU integration is still Person B’s work. No INT8 final-test evaluation or training was performed.','',
        '## Best measured batch settings','',
        'Timings are warmed, sequential standalone inference on this RTX 4060 Laptop GPU. Complete-batch latency is the wait for the whole request; amortized time divides that latency by batch size and describes throughput. Larger batches do not make a single waiting position finish in the amortized time.','',
        '| Objective | FP16 best batch | FP16 time | INT8 best batch | INT8 time | INT8 / FP16 |','| --- | ---: | ---: | ---: | ---: | ---: |']
    from tune_batches_week1 import objective
    labels={'resident_latency':'Resident GPU complete batch','host_latency':'Host-input to host-output complete batch',
        'resident_throughput':'Resident GPU amortized per position','host_throughput':'Host pipeline amortized per position'}
    for which,label in labels.items():
        a=tuning['optima']['F16_TRT'][which]; b=tuning['optima']['I1_TRT'][which]
        lines.append(f'| {label} | {a["batch"]} | {objective(a,which):.5f} ms | {b["batch"]} | {objective(b,which):.5f} ms | {tuning["I1_over_F16"][which]:.4f}× |')
    lines+=['','A ratio below 1 favors INT8; above 1 favors FP16. These are independently selected best measured settings, with fresh finalist repeats. Exact engine identities and all raw sweep samples are in [batch tuning](../results/week1-v2/batch-tuning.json).','',
        '![Batch latency and amortized throughput comparison](figures/week1-v2-batch-latency.png)','',
        'The exact accepted FP16 baseline supports batches 1–8 and was preserved. Separate timing engines extend the same graphs/precision controls to larger batches; their profiles, tactics, actual precision, reload and numerical differences are recorded separately. They do not silently replace the baseline used for the accuracy table. No global optimum or effective MCTS nodes/s gain is claimed.','',
        f'**Search-quality caution:** on validation, naive INT8 and FP16 choose the same top legal move on {int8["comparisons"]["F16_TRT"]["summary"]["top_move_agreement"]:.2%} of positions, and the largest value-head WDL component difference is {100*int8["comparisons"]["F16_TRT"]["summary"]["wdl_max_abs"]:.2f} percentage points. High tablebase move preservation does not establish equal value estimates or equal MCTS quality. Later quantization recovery and search evaluation remain necessary.','',
        '## Activation analysis and port','',
        f'All 1,024 calibration roots supplied exact per-channel maxima, means and RMS at {analysis["n_unique_activation_tensors"]} unique activation inputs serving {analysis["n_selected_matrix_consumers"]} selected matrix consumers. Instrumented outputs were checked against FP32 on every calibration root. [Plots and named analysis](week1-v2-activation-analysis.md).','',
        'The unchanged exact-operator PyTorch port passed FP32 forward checks on 32 preselected calibration cases at batch sizes 1 and 8. The earlier gradient-feasibility result is reused after checking identities. No optimizer, smoothing, QAT or distillation ran.','',
        '## Identities and reproduction','',
        '- [Active data manifest](../data/syzygy-v2/manifest.json) and [protocol](../environment/week1-v2-protocol.json).',
        '- [Original floating baseline specifications](../environment/step5-baselines.json); active history is fen_only under the new protocol.',
        '- [INT8 graph audit](../environment/week1-v2-i1-graph.json), [primary engine record](../environment/week1-v2-i1-engine.json), and [wrapper](../models/wrapped/bt3-i1-v2.pb.gz).',
        '- [Current evidence manifest](../environment/week1-v2-evidence-manifest.json) and [progress](../environment/week1-progress.json).','',
        'The following are the executed commands, in order, from the project root inside Ubuntu-22.04 WSL, using `/home/anjanrd/.local/share/lc0-int8/venv/bin/python` and `PYTHONDONTWRITEBYTECODE=1`. Original data acquisition commands are documented in the roadmap. Existing verified outputs are preserved; a full fresh rerun needs a separately versioned output/runtime location rather than overwriting this frozen run. TensorRT rebuilds may choose different tactics.','',
        '```text',
        'python scripts/complete_week1_v2.py initialize',
        'python scripts/complete_week1_v2.py baselines',
        'python scripts/refresh_int8_week1.py quantize',
        'python scripts/refresh_int8_week1.py build',
        'python scripts/refresh_int8_week1.py audit',
        'python scripts/refresh_int8_week1.py quality',
        'python scripts/refresh_int8_week1.py wrap',
        'python scripts/tune_batches_week1.py',
        'python scripts/refresh_analysis_week1.py statistics',
        'python scripts/refresh_analysis_week1.py port',
        'python scripts/handoff_week1_v2.py audit',
        'python scripts/handoff_week1_v2.py finalize',
        'python scripts/handoff_week1_v2.py verify',
        '```','',
        'Runtime engines, build files and kernel traces stay outside the project under `/home/anjanrd/.local/share/lc0-int8/week1-v2/`. No project tmp folder was created.','',
        '## Remaining work outside Person A Week 1','',
        'Person B retains actual lc0 GPU/provider integration, DTZ/hard-subset scoring work, fixed-node and one-second MCTS, integrated throughput/profiling and energy instrumentation. Joint C1 awaits its own evidence. Week 2 retains the quantization-improvement ladder. Batch tuning and NN accuracy alone do not establish the project’s full speed→nodes/s→accuracy chain.','']
    HANDOFF.write_text('\n'.join(lines))


def finalize():
    write_handoff()
    roadmap=PROJECT/'docs/project-roadmap.md'
    text=roadmap.read_text()
    text=text.replace('Roadmap version: **1.5 - Step 1 verified; published 4/5-piece dataset active**',
        'Roadmap version: **1.6 - Person A Week 1 complete and verified; joint C1 separate**')
    text=text.replace('### Combined Steps 2-5 discussion proposal (awaiting agreement)',
        '### Combined Steps 2-5 protocol (agreed and executed; see current evidence below)')
    text=text.replace('This proposal authorizes no experiment yet.',
        'The user subsequently agreed the complete block and requested wider batch tuning; execution and verification are recorded below.')
    text=text.replace('**Current authorization, 2026-10-27:** the user replaced autonomous progression',
        '**Historical discussion authorization, before the subsequently approved block:** the user replaced autonomous progression')
    text=text.replace('A14-A17 still need their own protocol/mode agreement.',
        'A14-A17 subsequently received combined agreement and autonomous Codex execution authorization; all four are now verified.')
    text=text.replace('Each arrow requires verification of the previous step and a fresh discussion/agreement before implementation.',
        'Each arrow requires verification of the previous step. The user approved one combined autonomous A14-A17 block, so those arrows do not require further approval rounds.')
    replacements={
        'Person A Step 5A-5G':'| Person A Step 5A-5G / A14 | Active two-baseline use verified with disclosed FP16 drift | Exact original engines retained; [current baseline evidence](../environment/week1-v2-baselines.json). Original failed numerical checks remain failures. |',
        'Scope review/profile, A06P/A06R':'| Scope review/profile, A06P/A06R | DONE; active 160-target execution reconfirmed in A15 | Original scope v2 retained; new engine inspector and executed INT8 kernel evidence verified. B03 still owns integration. |',
        'A07 naive INT8 pilot':'| A07 naive INT8 pilot / A15 | Active A-side pilot DONE | Recalibrated on all 1,024 active roots; validation, reload, wrapper and broad/refined batch tuning verified. [Evidence](../environment/week1-v2-int8-pilot.json). |',
        'A09 floating NN accuracy':'| A09 floating NN accuracy / A14 | Active measurements DONE | Both exact floating baselines score 9,990/10,000 test roots (99.90%); native/batch checks and raw drift recorded. No full native-strength claim. |',
        'A10 activation analysis':'| A10 activation analysis / A16 | Active refresh DONE | All 1,024 calibration-only maxima/means/RMS and named plots refreshed; original FP32 outputs checked across every root. |',
        'A11 trainable port':'| A11 trainable port / A16 | Feasibility reused; active parity DONE | Existing port passes 32 selected calibration cases at batches 1/8. No training, optimizer update or repeated backward run. |',
        'A12 audit':'| A12 audit / A17 | Current Person A audit DONE | Independent selected-move/tablebase checks, identities, historical preservation and [handoff](week1-v2-person-a-handoff.md) verified. Joint C1 remains separate. |'}
    for prefix,replacement in replacements.items():
        text=re.sub(r'^\| '+re.escape(prefix)+r' \|[^\n]*$',lambda _:replacement,text,flags=re.M)
    text=text.replace('**New acceptance gate:** the full 10,000-root baseline run',
        '**Historical raw numerical review (preserved):** the old 10,000-root baseline run')
    text=text.replace('The history design is now agreed but unimplemented. A13 checks inputs and A14 refreshes measured baseline results.',
        'The history design was subsequently implemented and verified in A13; A14 refreshed the baselines on the new corpus. Current measurements therefore change both history and roots.')
    text+='\n### R1.6 active closure (2026-10-27)\n\nA14-A17 are complete under the explicit combined authorization. The requested wider batch sweep supersedes the earlier brief 1/4/8-only proposal. All intended model/data outputs are versioned, raw drift and negative findings are retained, and historical artifacts remain unchanged except this roadmap and the progress tracker. Current [handoff](week1-v2-person-a-handoff.md), [audit](../environment/week1-v2-audit.json), and [evidence manifest](../environment/week1-v2-evidence-manifest.json) are authoritative for Person A completion. No Person B completion, joint C1 sign-off, Week 2 work, or MCTS-strength gain is inferred.\n'
    for task in ['W1-A14','W1-A15','W1-A16','W1-A17']:
        marker='#### '+task+' - '
        start=text.index(marker); finish=text.index('\n',start)
        if not text[finish:finish+80].startswith('\n\n- **Status:** DONE'):
            text=text[:finish]+ '\n\n- **Status:** DONE / Codex / verified under the approved combined protocol.' +text[finish:]
    roadmap.write_text(text)
    checkpoint('W1-A17','DONE','environment/week1-v2-audit.json','Person A Week 1 complete and verified; current handoff and evidence manifest ready. Person B and joint C1 remain separately unverified; Week 2 not started.')
    state_path=PROJECT/'environment/week1-progress.json'; state=read(state_path)
    state['roadmap']['version']='1.6'
    state['combined_completion_protocol']['status']='COMPLETED_AND_VERIFIED'
    state['workflow']['autonomous_block_completed']=['W1-A14','W1-A15','W1-A16','W1-A17']
    state['workflow']['authorization_scope']='Completed named A14-A17 block only; future work needs a new user instruction.'
    save(state_path,state)
    files=list(DEST.glob('*'))+list(DATA.glob('*'))+list((PROJECT/'environment').glob('week1-v2-*.json'))
    files += [PROJECT/'environment/week1-input-refresh.json',PROJECT/'environment/week1-progress.json',
        PROJECT/'docs/project-roadmap.md',HANDOFF,PROJECT/'docs/week1-v2-activation-analysis.md',
        PROJECT/'docs/figures/week1-v2-channel-outliers.png',PROJECT/'docs/figures/week1-v2-batch-latency.png',PROJECT/'models/onnx/bt3-i1-v2.onnx',
        PROJECT/'models/wrapped/bt3-i1-v2.pb.gz']
    files += [PROJECT/'scripts'/f for f in ['complete_week1_v2.py','refresh_int8_week1.py','tune_batches_week1.py','refresh_analysis_week1.py','handoff_week1_v2.py']]
    files=sorted(set(p for p in files if p.is_file() and p!=LEDGER))
    runtime_files=set()
    for path in (PROJECT/'environment').glob('week1-v2-*-engine.json'):
        record=read(path); runtime_files.add(Path(record['engine_path']))
        for item in record.get('precision_evidence',[]): runtime_files.add(Path(item['path']))
    runtime_files.add(Path(read(PROJECT/'environment/step5-engine.json')['engine_path']))
    runtime_files.add(WORK/'complete-executed-d2b7f0839143da8f.py')
    manifest={'status':'passed_Person_A_Week1_complete','frozen_at_utc':base.now(),
        'Person_A_complete':True,'joint_C1_complete':False,'Week2_started':False,
        'project_artifacts':[{'relative_path':str(p.relative_to(PROJECT)),'sha256':base.sha256(p),'bytes':p.stat().st_size} for p in files],
        'runtime_artifacts':[artifact(p) for p in sorted(runtime_files)],
        'exclusions':'This manifest excludes itself to avoid self-reference. Historical manifests and exact original floating artifacts remain separately verified.'}
    save(LEDGER,manifest)
    verify()


def verify():
    manifest=read(LEDGER)
    for item in manifest['project_artifacts']:
        assert base.sha256(PROJECT/item['relative_path'])==item['sha256'],item['relative_path']
    for item in manifest['runtime_artifacts']:
        assert base.sha256(item['path'])==item['sha256'],item['path']
    state=read(PROJECT/'environment/week1-progress.json')
    assert all(state['tasks'][f'W1-A{i}']['status']=='DONE' for i in range(13,18))
    assert state['roadmap']['A_side_week1_complete']
    assert not state['roadmap']['joint_C1_complete'] and not state['roadmap']['Week2_started']
    frozen()
    print('FINAL VERIFIED:',len(manifest['project_artifacts']),'project artifacts and',len(manifest['runtime_artifacts']),'runtime artifacts; Person A complete, joint C1 separate.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('action',choices=['audit','finalize','verify'])
    globals()[p.parse_args().action]()
