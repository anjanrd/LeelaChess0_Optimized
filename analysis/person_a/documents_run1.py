"""Write A's evidence-linked report draft and remaining-delivery preparation."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'analysis/person_a/run1'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))


def csvrows(path):
    with (ROOT/path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def put(path,text):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')


def table(records,columns):
    return '\n'.join(['| '+' | '.join(columns)+' |','|'+'---|'*len(columns)]+
                     ['| '+' | '.join(str(r[c]) for c in columns)+' |' for r in records])


def write_report():
    quality=csvrows('analysis/tables/T1-network.csv')
    q={r['model']:r for r in quality}
    search=csvrows('analysis/tables/T1-search.csv')
    timed=csvrows('analysis/tables/timed-matched-review.csv')
    sparse=read(RUN/'sparse_audit.json');roof=read(RUN/'roofline_contract.json')
    audit=read(RUN/'cohort_audit.json')
    references=read('deliverables/report/reference_audit.json')
    assert len(references['references'])>=6
    assert read(RUN/'progress.json')['steps']['A5']['status']=='deferred_user_authorized'
    compact=[{'model':r['model'],'correct/n':f"{r['correct']}/{r['n']}",
              'accuracy %':f"{100*float(r['accuracy']):.4f}",
              'approx KL':f"{float(r['policy_KL_approx']):.6g}",
              'top1':f"{float(r['top1_agreement']):.4f}",
              'mean abs(delta V)':f"{float(r['mean_abs_delta_V']):.6g}"}
             for r in quality if not r['model'].startswith('swap')]
    b1600={r['model']:r for r in search if r['requested_nodes']=='1600' and r['series']=='main'}
    body='''# Person A model-side report draft

Status: verified draft from frozen evidence, not the final shared report. A5/F12 is explicitly deferred. Systems conclusions and final report alignment await Ritwik. Tables/figures are derived analysis; no new model inference or search was performed.

## Abstract — provisional shared text

We study a BT3 chess transformer deployed inside lc0 using FP16 and a cumulative W8A8 post-training quantization ladder. We separate changes in neural outputs, preservation of tablebase move results, search at requested node budgets, and performance at fixed time. Percentile calibration and SmoothQuant improve output fidelity relative to naive quantization on the evaluated endgames, while the dense search scores saturate. SparseGPT preserves quality better than magnitude pruning but retains search errors. These observations establish model-side tradeoffs; final throughput, hardware and full-game strength conclusions will be inserted after systems evidence is reviewed. The activation illustration remains deferred until its saved-data consistency issue is resolved.

## Introduction and research questions

The hypothesis is that lower-precision inference may enable more search within a time budget, and that the extra search may compensate for changed neural outputs. Each link needs evidence: an output-fidelity improvement does not prove a latency improvement, and more nodes does not prove stronger play. We ask (RQ1) how the ladder changes policy/value outputs and move selection, (RQ2) what search masks and whether output swaps separate sensitivity, and (RQ3) what the measured quality/performance/strength evidence ultimately supports. Negative and inconclusive outcomes answer these questions too.

Haque, Wei and Müller compare raw Lc0 decisions with MCTS using exact endgame solutions [1]. That study motivates separate network/search measurements, not an expectation about BT3 INT8. Our corpus, network and runtime differ. The proposal's exact historical error counts are not repeated here without a checked source table.

## Related work and methodological distinctions

Tablebase evaluation [1] motivates separating neural move choice from search. SmoothQuant [2] addresses activation ranges through compensated rescaling, while SparseGPT [3] uses calibration-dependent pruning compensation. Their LLM results are motivation, not guarantees for this chess model. GPTQ [4] is a related weight-quantization method and is not the quantizer used here. Sparse hardware support [5], roofline modelling [6] and incremental NNUE evaluation [7] provide context for distinct implementation/performance questions. None supplies a measured result for our laptop experiment.

## Model, outputs and runtime boundary

The checkpoint is `BT3-768x15x24h-swa-2790000.pb.gz`, SHA256 `e3067757d1fc2dfc66947b21d15ace0cedf4c54254fc1de83d77c378a3e8b8e1`. The exported graph accepts `[batch,112,8,8]` classical input planes and produces policy `[batch,1858]`, WDL `[batch,3]` and moves-left `[batch,1]`. Policy guides legal-move priors; WDL is the neural outcome prediction; moves-left is auxiliary. Our chess-accuracy score evaluates a selected move using external tablebase labels, not the argmax of WDL. The value-drift column is the frozen scorer's saved printed `V` difference, not a per-component WDL probability distance.

The wrapped FP16 baseline contains exported FP32 ONNX and runs through lc0 `onnx-trt optimize=6`. Quantized variants use `optimize=8`. The raw checkpoint through the same backend is a wrapping/reference check. Python CPU ONNX Runtime used for preparation is separate from lc0's bundled GPU ONNX Runtime. A runtime flag permits precision; per-model executed coverage remains a systems measurement. Graph target counts must not be labelled measured Tensor Core coverage.

## Data, scoring and analysis cohort

The adopted corpus contains 11,200 synthetic legal, nonterminal, decision-sensitive roots from 28 three-to-five-piece material classes, labelled with local Syzygy tables. Pools contain 1,120 calibration, 3,360 development and 6,720 test roots. Quantization calibration actually uses 512 inputs: 256 random-game inputs with supplied history and 256 tablebase inputs. Standalone tablebase roots use the imported FEN-only convention and zero halfmove clocks. The primary evaluated cohort is the same 2,437 test IDs for every model.

The imported rule maps Syzygy +2 to win, -2 to loss and 0/±1 to draw. A selected move is correct if it preserves the root category; DTZ-optimal rate is secondary. Missing conditions are not losses or zero values. We retain the original labels, results and scorer.

Seven symmetry-equivalence groups cross pool splits, affecting measured IDs 611, 627 and 965. The grouping and actual calibration membership are recorded in `analysis/person_a/run1/cohort_audit.json`. This limits a fully independent holdout claim. We preserve and disclose the primary results; no roots were silently removed. The 43-position hard subset was defined using viewed FP16 test outputs and is descriptive, not another model-selection set.

## Quantization methods and development selection

The ladder is s1 per-tensor signed symmetric minmax W8A8; s2 adds per-channel weight scales; s3 uses selected percentile 99.999; s4 adds SmoothQuant alpha 0.7. The attention extension s4aa additionally quantizes dynamic matrix products. The active graphs request QDQ on 164 fixed-weight matmuls in s4 and all 195 matmuls in s4aa. Biases, normalization, softmax and other floating work are not described as uniformly INT8. Calibration and recipe selection use their prescribed pools; final test plots are not used to choose a new recipe.

SmoothQuant transfers range imbalance between activations and weights [2]. For positive scales, `XW = (X/s)(sW)` before rounding. This implementation inserts explicit branch Mul nodes instead of unrestricted LayerNorm folding because residual/shared consumers must remain correct; shared global Smolgen weights constrain per-block smoothing. The saved activation arrays did not pass their current-model consistency check. **A5 is deferred by the user: F12 and any claims based on that example remain unfinished.** The algebraic mechanism and saved quality metrics can be described independently of that plot.

Magnitude pruning retains the largest two values per group of four along the reduction dimension. SparseGPT uses calibration-dependent compensation [3]; the imported implementation is sequential across 98 dependency stages with 512 calibration inputs. Both pruned source graphs were checked: all 150 unique targeted matrices satisfy at most two nonzeros per K-group of four. The sparse branch is pruned before best-recipe quantization. This experiment is not GPTQ weight quantization, though GPTQ provides related second-order compression context [4].

## RQ1 — Network-level results

'''+table(compact,['model','correct/n','accuracy %','approx KL','top1','mean abs(delta V)'])+'''

The complete T1 table includes secondary DTZ scores, Wilson intervals and paired discordances. Policy KL is approximate because lc0 prints rounded priors; top1 on printed priors is distinct from the selected legal best move. Multiple comparisons are descriptive; isolated unadjusted p-values are not global superiority claims.

FP16 and s4 each make six preserving-move errors, but s4 has nonzero policy/value drift. Per-channel weighting does not monotonically improve every metric. Selected clipping and smoothing reduce divergence relative to naive PTQ. s4aa has the same move score here with somewhat different output fidelity. None of these results assigns all INT8 variants the same speed.

![F1: dense quantization outputs](../../analysis/figures/F1-ablation.png)

## RQ2 — Search, actual budgets and the hard subset

Study B uses requested 100/400/800/1,600 nodes, Threads=1, MinibatchSize=256 and smart pruning off. Actual visits overshoot, so requests are not exactly equal completed work. At larger budgets the dense scores approach or reach the ceiling. The 43-position supplementary analysis preserves the existing 10/25/50/100/200 requests, paired identities and actual-node distributions; it neither adds search nor tunes the model.

Node-equivalents use the imported monotone reference envelope and inverse in log node count. A flat reference curve has an interval of inverse solutions; the scorer chooses a point near the compared model's node count. Ratios near one under saturation are therefore not precise evidence of equivalent search efficiency. Zero indicates a score below reference raw accuracy, not zero work.

![F2: accuracy against requested nodes](../../analysis/figures/F2-nodes.png)

![F3: reported node-equivalents](../../analysis/figures/F3-node-equivalents.png)

The hard-set curves have few discordant positions and can be non-monotone. A one-position change or crossing curve is weak evidence of a systematic gain. The per-condition table contains confidence intervals and exact paired counts rather than treating every point as a separate success claim.

## Policy/value swaps

`swap_pol8` takes policy from s4 and value/moves-left from the FP16-side graph; `swap_val8` reverses these routes. Source/stitched ONNX and wrapped identities agree with the recorded provenance. These evaluate two bodies and are used only for fixed-node quality comparisons. Different TensorRT builds can retain small numerical differences even in the nominally floating branch, and moves-left changes with value; the experiment is not a perfectly isolated intervention on a single scalar output.

All four configurations have the same aggregate correctness counts here: six raw errors, one at requested 100 and zero at the larger budgets. Actual visit counts differ. The saturated test does not identify which head's error is more harmful; a tie does not establish equal head importance.

![F4: output swaps](../../analysis/figures/F4-swaps.png)

## Sparse quality findings

'''+(RUN/'sparse_findings.md').read_text(encoding='utf-8').split('\n\n',1)[1]+f'''

At requested 1,600 nodes, s1sp retains {b1600['s1sp']['errors']} errors versus {b1600['fp16']['errors']} for FP16 on the common cohort. Magnitude pruning has only supplemental 100/400-node search results, kept separate; no later points are invented. Per-position mistakes and calibration-row warnings are saved with the analysis tables. Theoretical sparse arithmetic support [5] does not establish selected sparse tactics or end-to-end speed here.

## Model work and systems handoff

The verified active graph contains {roof['operations']} matrix operations: {roof['fixed_weight_operations']} fixed-weight and {roof['dynamic_operations']} dynamic. Matrix work is {roof['macs_per_position']:,} MACs per position, or {roof['arithmetic_ops_per_position']:,} arithmetic operations under the two-ops-per-MAC convention. This excludes non-matmul work. The model side provides per-operation geometry, batch scaling and a traffic model; fused timings, actual operand/output representations and measured peaks remain R1 inputs. Logical traffic is not measured DRAM traffic. Roofline is an explanatory model [6], with the implementation caveats recorded separately.

**WAIT R1/R2:** actual layer/precision/sparse execution, measured roofline and comparable/repeated NN/search performance. Sparse-enabled standalone trtexec and actual lc0 timings remain different conditions. **WAIT R4:** match outcomes and Elo. GPU energy/node, when supplied, is not the omitted equal-energy accuracy test. NNUE illustrates a different evaluation/search design [7]; it is related context, not another measured baseline.

## Existing fixed-time review and provisional RQ3 interpretation

'''+(RUN/'timed_findings.md').read_text(encoding='utf-8').split('\n\n',1)[1]+'''

## Limitations and provisional conclusion

The study uses one checkpoint/device, synthetic decision-sensitive endgames, limited accuracy headroom, printed-output approximations and requested budgets with overshoot. Cross-split symmetry overlap, test-defined hard analysis and sparse calibration coverage constrain generalization. The finite repeated opening book and match uncertainty need review after actual games arrive. A5/F12 remains deferred, not repaired or waived.

The current evidence supports model fidelity/quality tradeoffs and substantial masking of dense-model errors by search on this corpus. It does not yet establish a full-game playing-strength gain. Final conclusions require the independent hardware/time/match evidence and shared review; a negative or inconclusive result remains a valid answer.

Accepted scope omissions are search-visited calibration, partial INT8, QAT/KD/recovery, the additional R32 baseline, one-second timing, CPU/whole-machine energy, equal-energy accuracy (F8) and accuracy-versus-batch (F10). No new variants were introduced to obtain a positive outcome.

## Final integration checklist

- Address A5 before autonomous Run 2; resolve the diagnostic example/F12 or obtain an explicit handling decision.
- Integrate R1/R2/R4 measured findings and align R3 with B's canonical report; audit paired conditions and uncertainty.
- Combine A/B contributions to the abstract, introduction, related work, discussion, limitations and conclusion.
- Complete the shared report/presentation/demo and verify the final package/reproduction (R5).
- Reproduction must include FP16, best PTQ s4 and the selected sparse path or its documented runtime limitation; repository smoke tests alone are insufficient.

References and checked claim scope: [references.md](references.md) and [reference_audit.json](reference_audit.json). Source-to-claim links: [claim_register.md](../../analysis/person_a/run1/claim_register.md).
'''
    put('deliverables/report/person_a_sections.md',body)
    claims=[
      {'claim':'Dense network fidelity and move correctness','evidence':'T1-network.csv; F1; scores_test.json','state':'verified for this cohort','limit':'printed priors/value and ceiling accuracy'},
      {'claim':'Search masks dense errors','evidence':'T1-search.csv; F2/F3; hard-lowbudget.csv','state':'verified descriptive finding','limit':'requested-node overshoot; saturated reference'},
      {'claim':'Swap head importance','evidence':'policy-value-swap.csv; F4; swap_provenance.md','state':'inconclusive','limit':'ties, two bodies, moves-left co-swap and numeric differences'},
      {'claim':'SmoothQuant activation illustration','evidence':'blocker-A5.json','state':'DEFERRED A5','limit':'address before Run 2; no F12 result'},
      {'claim':'2:4 masks and sparse quality','evidence':'sparse_audit.json; sparse-reconstruction.csv; sparse-move-errors.csv','state':'verified masks/quality','limit':'hardware acceleration WAIT R1/R2'},
      {'claim':'Measured model performance/roofline','evidence':'roofline-operation-inventory.csv; roofline_contract.json','state':'static work ready; WAIT R1/R2','limit':'no measured peaks/timings supplied'},
      {'claim':'Fixed-time accuracy','evidence':'timed-matched-review.csv; timed-matched-positions.csv','state':'existing matched data reviewed; R3 final alignment','limit':'one discordance at 200ms; ceiling at 800ms; early stopping'},
      {'claim':'Full-game strength','evidence':'R4 games/Elo not supplied','state':'WAIT R4','limit':'no inference from throughput alone'},
      {'claim':'Final systems/reproduction','evidence':'R5 not supplied','state':'WAIT R5','limit':'no C3/C4 final sign-off'},
    ]
    put('analysis/person_a/run1/claim_register.md','# Claim/evidence register\n\n'+table(claims,['claim','evidence','state','limit'])+'\n')
    put('analysis/tables/project_hypothesis_evidence.md','# Hypothesis evidence\n\n'+table(claims,['claim','state','evidence','limit'])+
        '\n\nSpeed, more search, timed root accuracy and game strength need separate evidence. GPU energy/node does not complete omitted F8.\n')
    assert 'F12-outliers.png' not in body
    assert all(x in body for x in ['A5','R1','R2','R3','R4','R5','F8','F10'])
    return {'report':'deliverables/report/person_a_sections.md','claim_rows':len(claims),
            'verified_primary_references':len(references['references']),'A5':'deferred; no activation claim',
            'final_shared_report':'WAIT systems evidence and final integration'}


def prepare_delivery():
    assert (ROOT/'deliverables/report/person_a_sections.md').exists()
    ledger=[
      ('D1','Shared code/setup','In progress','README.md; maintenance/artifacts.py','R5 fresh setup/reproduction'),
      ('D2','Models/calibration/recipes/engine identities','In progress','models/; data/; frozen manifests','R5 final engine/runtime freeze'),
      ('D3','Root lists/splits/scorer','A-side audit complete; shared closure pending','analysis/person_a/run1/cohort_audit.json','R5 final shared package'),
      ('T1','Network/search ablation','Completed numerical/publication tables','analysis/tables/T1-network.md; T1-search.csv','final report styling only'),
      ('T2','Speed/coverage/reference','WAIT R1/R2','reports/c3_hw/bench/ preliminary','R1/R2 measured conditions'),
      ('T3','GPU energy','WAIT R2 final table','reports/c3_hw/bench/ preliminary','R2; CPU energy omitted'),
      ('T4','Paired-match Elo/CI','WAIT R4','no completed match evidence','R4 games and reviewed uncertainty'),
      ('T5','Sparse hardware','WAIT R1/R2','valid masks; no complete sparse tactic/timing audit','actual sparse/dense evidence'),
      ('F1','Dense ablation','Generated; visual QA recorded separately','analysis/figures/F1-ablation.png','final shared report styling'),
      ('F2','Accuracy/nodes','Generated; visual QA recorded separately','analysis/figures/F2-nodes.png','caption preserves actual-node context'),
      ('F3','Node-equivalents','Generated; visual QA recorded separately','analysis/figures/F3-node-equivalents.png','saturation convention disclosed'),
      ('F4','Output swaps','Generated; visual QA recorded separately','analysis/figures/F4-swaps.png','accuracy only; head importance inconclusive'),
      ('F5','Accuracy/time','Existing matched data reviewed; B final figure pending','analysis/tables/timed-matched-review.csv','R3 canonical final report'),
      ('F6','Layer profile/roofline','Static contribution ready; WAIT R1','analysis/tables/roofline-operation-inventory.csv','measured profiles/peaks/precision'),
      ('F7','GPU energy/node','WAIT R2 final figure','preliminary benchmark/sweep evidence','B final figure/provenance'),
      ('F8','Accuracy/equal energy','Omitted','updated_plan.md','no substitute claim'),
      ('F9','Batch throughput','Completed reduced sweep','reports/c3_hw/batch_sweep/sweep.png','B final caption'),
      ('F10','Accuracy/batch','Omitted','updated_plan.md','no substitute claim'),
      ('F11','Quality/throughput frontier','Quality ready; WAIT R2','analysis/tables/frontier-quality-ready.csv','eight comparable speeds; no swaps'),
      ('F12','Activation illustration','DEFERRED A5','analysis/person_a/run1/blocker-A5.json','REMINDER: address before autonomous Run 2'),
      ('D4','Report','A draft ready; shared final pending','deliverables/report/person_a_sections.md','A5 + R1–R5 final integration'),
      ('D5','Presentation','A outline ready; final pending','deliverables/presentation/person_a_slides.md','final figures/results and rendered deck'),
      ('D6','Playing demo','Outline ready; recording pending','deliverables/demo/recording_plan.md','R5 runtime + exclusive GPU slot'),
      ('D7','Package/fresh reproduction','Procedure ready; final pending','deliverables/reproduction_plan.md','FP16+s4+sparse path; R5 final assets'),
      ('D8','Numbers/citations/C4','A-side checks prepared; final pending','deliverables/completion-checklist.md','every retained row verified; A5/R inputs resolved'),
    ]
    records=[dict(zip(['ID','deliverable','status','evidence','remaining_check'],r)) for r in ledger]
    put('deliverables/completion-checklist.md','# Final deliverable checklist — Run 1 preparation\n\n'
        '**Before Run 2: address A5.** This is not C4 sign-off. A deferred item is not completed.\n\n'+
        table(records,['ID','deliverable','status','evidence','remaining_check'])+'\n')
    put('deliverables/presentation/person_a_slides.md','''# Person A slide contribution

Prepared content for the shared deck; not a rendered final presentation.

1. **Question and outputs:** one BT3 checkpoint; policy, WDL and moves-left; separate network drift, move accuracy and game strength. Use the report's model/input diagram description.
2. **Compression ladder:** per-tensor -> per-channel -> percentile -> SmoothQuant; attention and sparse branches separate. Use F1 and the recipe table.
3. **Search:** use F2/F3 and the hard supplement. Explain actual-node overshoot, near-ceiling results and why node-equivalents can be ambiguous.
4. **Policy/value swap:** use F4. Explain both routes, moves-left co-swap and why ties do not establish equal importance.
5. **Sparse quality:** verified masks, lower calibration reconstruction loss and persistent chess errors. Hardware conclusions WAIT R1/R2.
6. **Activation mechanism:** explain compensating rescaling algebraically. A5/F12 is DEFERRED; no unverified channel plot is included. Address it before Run 2.
7. **Model work meets hardware:** static 195-operation inventory ready. Final profile/roofline WAIT R1; quality-versus-throughput WAIT R2. Keep actual lc0 separate from standalone sparse probes.
8. **Does speed pay off?:** existing timed review is near ceiling; final speed/match findings WAIT R2/R3/R4. Include negative/inconclusive outcomes and uncertainty.
9. **Limits and reproduction:** synthetic endgames, one network/device, split caveat, printed priors, scope omissions; final systems reproduction WAIT R5.

Final deck: combine with B's systems slides, verify numbers against source CSVs, remove placeholders only when evidence arrives, render/review and rehearse. Shared abstract/introduction/related work/discussion/limitations/conclusion must agree with the report.
''')
    put('deliverables/demo/recording_plan.md','''# INT8-lc0 demo preparation

No engine was launched or recording made in Run 1. A real playing demo remains a shared Run 2 deliverable.

Use the frozen `models/s4.pb.gz` with lc0 onnx-trt optimize=8, final recorded runtime identities and an exclusive GPU slot after benchmarking. Keep tablebase assistance disabled. Show model/backend identity, legal moves and actual printed nodes/s. Narrate policy/value/moves-left and the role of search using verified report definitions.

Prepare a short terminal/UCI or available-GUI sequence without replacing the measured backend or recalibrating. Record actual engine output, not typed performance figures. Save demo logs/recording separately from benchmark results. If final speed/strength is mentioned, use only reviewed R2/R3/R4 findings.

Acceptance: a short playable demo/recording exists; model/backend identifiable; legal moves and nodes/s legible; explanation matches the report. Runtime execution/recording waits for the final environment/GPU slot (R5). A5 is a separate pre-Run2 reminder, not a reason to add an unverified activation illustration to the demo.
''')
    put('deliverables/reproduction_plan.md','''# Fresh reproduction and packaging procedure — prepared, not executed

**Before autonomous Run 2: address A5**, then validate Ritwik's R1–R5 handoffs and the final model/configuration identities. The final reproduction is distinct from the existing repository and artifact-transfer tests.

1. Freeze source revision, model/recipe hashes, labelled root/cohort IDs, calibration/development inputs, scorer, runtime/backend versions and final system conditions. Preserve original evidence and failed-run records.
2. Create a clean checkout and a fresh local Python environment; install compatible runtime tools separately. Restore a verified artifact bundle using maintenance/artifacts.py. Do not copy the old virtual environment or assume TensorRT engine portability.
3. Reproduce a declared, deterministic subset containing **FP16, best PTQ s4 and the selected sparse path (s1sp or the final agreed sparse variant)**. Record exact IDs, budget/batch settings, input/history convention, commands and success tolerances before execution. These are execution checks of frozen variants, not a new selection experiment.
4. Check model loading/encoding/output routing, selected-move scoring, numerical agreement with the appropriate reference and runtime precision where required. Record any GPU-specific engine rebuild. Actual profiling/performance checks use the frozen B procedure and one GPU job at a time.
5. A documented sparse-runtime limitation can be an honest outcome, but an unperformed required dense check is not a pass. Do not replace experimental reproduction with parsing old score JSONs or six repository tests.
6. Regenerate A tables/figures from immutable saved evidence in new output paths and compare them with declared tolerances; review captions and source identities. Keep F12 unfinished until A5 is resolved or explicitly handled by the user.
7. Audit every final report/slide number and citation. Reconcile paired match results, systems tables, retained deliverables and omitted F8/F10. Generate final artifact inventory/package only after the freeze; verify its hashes and a receiving-side restore.
8. Record the fresh setup, commands, outputs, runtime limitations and final checklist sign-off. Render/review the final report/deck and complete the real demo before C4.

This procedure is ready for execution after inputs/conditions are finalized. No fresh model inference, GPU reproduction or full-size bundle was created during this Run 1 block.
''')
    put('analysis/person_a/README.md','''# Person A analysis workspace

Execution script: `run1.py`; outputs and progress: `run1/`; plots: `../figures/`; publication CSVs: `../tables/`. Work is on `anjan` and derives from the frozen consolidation evidence.

The user authorized Run 1 in one autonomous block and then explicitly deferred A5 while resuming A6–A10. The original A5 failure is preserved at `run1/blocker-A5.json`. **Read BEFORE_RUN_2.md and remind Anjan to address A5 before launching Run 2.** No F12 result is fabricated.

A1–A4 reproduce/cohort-check existing accuracy and swaps. A6 audits sparse masks and quality. A7 verifies the active graph geometry and prepares roofline work. A8 creates matched timed review, eight-model frontier quality and the legal opening-book review. A9 writes the evidence-linked draft and references. A10 prepares the retained-deliverable checklist, slide/demo and fresh-reproduction plans. Final measured R1/R2/R4/R5 conclusions wait for B; R3 already has raw data and needs canonical alignment.

Normal reproduction commands use `.venv/Scripts/python.exe -B analysis/person_a/run1.py <step>` sequentially. Do not rerun finished steps just to refresh timestamps, and do not run A5 without authorization. The runner's only deferred prerequisite bypass is the user-approved A5 -> A6 transition. Numerical/scorer logic and raw evidence remain unchanged.

`run1/source_manifest.json` records frozen inputs; closing verification and output inventory distinguish completed independent work from A5/system-dependent deliverables. A complete independent block does not mean the entire project or C4 is complete.
''')
    return {'checklist_rows':len(records),'slides':'prepared outline','demo':'prepared recording plan',
            'reproduction':'prepared FP16 + s4 + sparse-path procedure; not executed',
            'before_run2':'Address deferred A5 first; then validate Ritwik inputs',
            'final_delivery':'WAIT A5 handling and R1–R5 integration'}
