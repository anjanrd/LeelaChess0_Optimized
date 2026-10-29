"""Publication figures from saved-result CSVs; no inference or scoring changes."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"analysis/figures"
COLORS={"fp16":"#172b4d","s1":"#bf5b04","s2":"#906ab1","s3":"#2a7e95",
        "s4":"#198754","s4aa":"#46a98f","s0":"#bd3838","s1sp":"#b68b25",
        "swap_pol8":"#be5192","swap_val8":"#546bc5"}
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,
                     "figure.dpi":130,"savefig.dpi":200,"pdf.fonttype":42,"svg.fonttype":"none"})


def save(fig,name,caption):
    OUT.mkdir(parents=True,exist_ok=True)
    fig.tight_layout(rect=(0,.08,1,.94))
    fig.text(.02,.015,caption,fontsize=8,va="bottom",wrap=True)
    for suffix in ["png","pdf","svg"]:
        fig.savefig(OUT/f"{name}.{suffix}",bbox_inches="tight")
    plt.close(fig)


def network(rows):
    rr=[r for r in rows if r['model'] in ['fp16','s1','s2','s3','s4','s4aa']]
    x=np.arange(len(rr));labels=[r['model'] for r in rr]
    fig,axes=plt.subplots(1,3,figsize=(12,4.2))
    for ax,key,title in zip(axes,['errors','policy_KL_approx','mean_abs_delta_V'],
                            ['Tablebase move errors','Approximate policy KL','Mean absolute value difference']):
        y=[r[key] for r in rr]
        ax.bar(x,y,color=[COLORS[m] for m in labels],width=.7)
        for i,v in enumerate(y):ax.annotate(f'{v:.3g}',(i,v),xytext=(0,5),textcoords='offset points',ha='center',fontsize=8)
        ax.set_xticks(x,labels);ax.set_title(title);ax.margins(y=.22)
        ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.suptitle('F1 · Dense PTQ: move correctness and NN-output drift (n = 2,437)')
    save(fig,'F1-ablation','Source: T1-network.csv. Lower is better. Raw policy choices are scored against saved Syzygy labels.\n'
         'KL/value are printed lc0 output differences, not chess-error probabilities; marginal intervals are in T1.')


def search_figures(rows,low,scores):
    fig,axes=plt.subplots(1,2,figsize=(12,4.6))
    for ax,names,title in [(axes[0],['fp16','s1','s2','s3','s4','s4aa'],'Dense models: near-ceiling detail'),
                           (axes[1],['fp16','s4','s0','s1sp'],'Sparse models: quality loss')]:
        for m in names:
            rr=sorted([r for r in rows if r['model']==m],key=lambda r:r['requested_nodes'])
            raw=scores['models'][m]['A']['acc']
            x=[1]+[r['requested_nodes'] for r in rr];y=[raw*100]+[r['accuracy']*100 for r in rr]
            ax.plot(x,y,marker='o',label=m,color=COLORS[m],linewidth=1.6,markersize=4)
        ax.set_xscale('log');ax.set_xticks([1,100,400,800,1600],['raw','100','400','800','1600'])
        ax.set_xlabel('Requested node budget (log spacing)');ax.set_ylabel('Preserving-move accuracy (%)')
        ax.set_title(title);ax.grid(alpha=.2);ax.legend(fontsize=8,ncol=2)
    axes[0].set_ylim(99.35,100.08);axes[1].set_ylim(50,101)
    fig.suptitle('F2 · Search quality at requested node budgets (n = 2,437)')
    save(fig,'F2-nodes','Source: T1-search.csv and T1-network.csv. Actual visits overshoot; means/ranges are in the CSV.\n'
         's0 uses a separate supplemental 100/400 run; no 800/1,600 result is implied. Lines join observed points only.')

    names=['s1','s2','s3','s4','s4aa','s1sp']
    mat=np.array([[float(v) for v in scores['models'][m]['B']['node_equiv']] for m in names])
    fig,ax=plt.subplots(figsize=(8,4.4))
    im=ax.imshow(mat,cmap='YlGnBu',vmin=0,vmax=1.1,aspect='auto')
    for i in range(len(names)):
        for j in range(4):ax.text(j,i,f'{mat[i,j]:.2f}',ha='center',va='center',color='white' if mat[i,j]>.75 else 'black')
    ax.set_yticks(range(len(names)),names);ax.set_xticks(range(4),['100','400','800','1,600'])
    ax.set_xlabel('Requested node budget');fig.colorbar(im,ax=ax,label='Reported node-equivalent ratio')
    fig.suptitle('F3 · Node-equivalents under the frozen scorer convention')
    save(fig,'F3-node-equivalents','Source: scores_test.json. 0 = below FP16 raw accuracy; values are printed to two decimals.\n'
         'Flat/saturated reference curves have non-unique inverses; ratios near 1 do not prove equivalent search quality.')

    fig,ax=plt.subplots(figsize=(8,4.5))
    for m in ['fp16','s1','s2','s3','s4','s4aa']:
        rr=sorted([r for r in low if r['model']==m],key=lambda r:r['requested_nodes'])
        ax.plot([r['requested_nodes'] for r in rr],[r['errors'] for r in rr],marker='o',label=m,color=COLORS[m])
    ax.set_xscale('log');ax.set_xticks([10,25,50,100,200],['10','25','50','100','200'])
    ax.set_xlabel('Requested node budget');ax.set_ylabel('Errors / 43 positions');ax.set_ylim(-.2,5.5)
    ax.grid(alpha=.2);ax.legend(ncol=3,fontsize=8);fig.suptitle('Supplement · Existing hard-subset low-budget runs')
    save(fig,'S1-hard-lowbudget','Source: hard-lowbudget.csv. Subset was selected using viewed FP16 test outputs; descriptive only.\n'
         'Actual visits vary/overshoot. A one-position difference and a crossing curve do not establish robust superiority.')


def swaps(rows):
    names=['fp16','s4','swap_pol8','swap_val8'];budgets=[0,100,400,800,1600]
    mat=np.array([[next(r['errors'] for r in rows if r['model']==m and r['requested_nodes']==b)
                   for b in budgets] for m in names])
    fig,axes=plt.subplots(1,2,figsize=(11,4.2),gridspec_kw={'width_ratios':[1.4,1]})
    axes[0].imshow(mat,cmap='YlOrRd',aspect='auto',vmin=0,vmax=max(1,mat.max()))
    for i in range(4):
        for j in range(5):axes[0].text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]>=4 else 'black')
    axes[0].set_yticks(range(4),names);axes[0].set_xticks(range(5),['raw','100','400','800','1,600'])
    axes[0].set_title('Move errors / 2,437');axes[0].set_xlabel('Requested node budget')
    vals=[next(r['actual_nodes_mean'] for r in rows if r['model']==m and r['requested_nodes']==100) for m in names]
    axes[1].barh(names,vals,color=[COLORS[m] for m in names]);axes[1].invert_yaxis()
    axes[1].set_xlabel('Mean actual visits');axes[1].set_title('Requested 100: different actual work')
    fig.suptitle('F4 · Policy/value swaps: no correctness separation on this cohort')
    save(fig,'F4-swaps','Source: policy-value-swap.csv. Value-side route includes moves-left. Swaps execute two bodies.\n'
         'Ties under saturation are inconclusive about head importance; this is not a speed comparison.')


def outliers(groups,channels):
    before=np.array([r['ratio_before'] for r in groups]);after=np.array([r['ratio_after'] for r in groups])
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.6))
    colors=np.where(after<before,'#198754','#bd3838')
    axes[0].scatter(before,after,c=colors,s=22,alpha=.8)
    bounds=[min(before.min(),after.min())*.8,max(before.max(),after.max())*1.3]
    axes[0].plot(bounds,bounds,'--',color='gray',linewidth=1)
    axes[0].set_xscale('log');axes[0].set_yscale('log');axes[0].set_xlim(bounds);axes[0].set_ylim(bounds)
    axes[0].set_xlabel('Before: max / median channel maximum');axes[0].set_ylabel('After: max / median channel maximum')
    axes[0].set_title(f'Selected alpha 0.7: all {len(groups)} build-time groups')
    axes[0].text(.04,.96,f'{int((after<before).sum())} improve; {int((after>=before).sum())} worsens',
                 transform=axes[0].transAxes,va='top',fontsize=9)
    order=np.argsort([-r['s4_raw'] for r in channels])
    for key,label,color in [('s4_raw','s4 before explicit Mul','#172b4d'),('s4_smoothed','s4 after explicit Mul','#198754')]:
        axes[1].plot(range(len(channels)),[channels[i][key] for i in order],label=label,color=color,linewidth=1.2)
    axes[1].set_yscale('log');axes[1].set_xlabel('Channel rank by before-Mul maximum');axes[1].set_ylabel('Maximum absolute activation')
    axes[1].set_title('Selected s4: measured encoder14/ln2, 768 channels');axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(alpha=.2)
    fig.suptitle('F12 · SmoothQuant rescaling: group summary and matched channel example')
    save(fig,'F12-outliers','Sources: smoothquant-groups.csv, smoothquant-channels.csv; alpha 0.7 / percentile 99.999. Left: build-time derived ratios.\n'
         'Right: matched CPU measurements on 512 unchanged calibration inputs. Contexts are distinct; no speed/accuracy claim.')
