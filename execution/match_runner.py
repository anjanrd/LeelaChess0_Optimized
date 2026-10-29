"""Recoverable match storage around the imported Game/search/adjudication.

Same openings, clocks and rules. Pilot games are retained in a separate folder.
One atomic envelope contains both a game record and its PGN; combined files are
derived exports, so an interrupted export cannot lose a completed game.
"""
import argparse
import io
import json
from pathlib import Path
import sys
import time

import chess
import chess.pgn

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'eval'))
from eval.match import Game, OPENINGS, opening_moves, parse_engine, parse_tc, summarize
from eval.lc0uci import Lc0
from execution.support import atomic_json, fingerprint, identity, read_json, require_session


def validate_envelope(envelope,contract,contract_hash):
    if envelope.get('contract')!=contract_hash:
        raise ValueError('Game belongs to different model/settings contract')
    r=envelope['record'];gi=r['game']
    if type(gi) is not int or gi<0 or r['pair']!=gi//2:
        raise ValueError('Invalid game/pair identity')
    a,b=contract['engine_names'];white,black=(a,b) if gi%2==0 else (b,a)
    if (r['white'],r['black'])!=(white,black) or r['opening']!=(gi//2)%len(OPENINGS):
        raise ValueError('Opening or color assignment changed')
    if r['result'] not in ('1-0','0-1','1/2-1/2'):
        raise ValueError('Game has no final result')
    sw={'1-0':1.0,'0-1':0.0,'1/2-1/2':0.5}[r['result']]
    if r['score_a']!=(sw if gi%2==0 else 1-sw):
        raise ValueError('Result and score disagree')
    stream=io.StringIO(envelope['pgn']);g=chess.pgn.read_game(stream)
    if g is None or g.errors or chess.pgn.read_game(stream) is not None:
        raise ValueError('Malformed or multiple PGNs in game envelope')
    for key,value in {'White':white,'Black':black,'Result':r['result'],'Round':str(gi+1),
                      'TimeControl':contract['settings']['tc'],'Termination':r['reason']}.items():
        if g.headers.get(key)!=value:
            raise ValueError('PGN/record mismatch: '+key)
    moves=[m.uci() for m in g.mainline_moves()]
    opening=opening_moves(gi//2)
    if moves[:len(opening)]!=opening or len(moves)!=r['plies']:
        raise ValueError('Opening/ply mismatch in PGN')
    return r


def journal_records(folder,contract):
    result=[];seen=set();h=fingerprint(contract)
    for p in sorted((Path(folder)/'games').glob('game-*.json')):
        e=read_json(p);r=validate_envelope(e,contract,h)
        if r['game'] in seen or p.name!=f"game-{r['game']:06d}.json":
            raise ValueError('Duplicate or wrongly named game envelope')
        seen.add(r['game']);result.append(e)
    return result


def checked_summary(envelopes,contract):
    games=[validate_envelope(e,contract,fingerprint(contract)) for e in envelopes]
    ids=[g['game'] for g in games]
    if len(set(ids))!=len(ids):
        raise ValueError('Duplicate games in summary')
    legacy=summarize(games,*contract['engine_names'])
    scores={}
    for g in games:scores.setdefault(g['pair'],[]).append(g['score_a'])
    full=[sum(v)/2 for v in scores.values() if len(v)==2]
    degenerate=len(full)<2 or len(set(full))<2
    interval=None
    if not degenerate:
        import math
        mu=sum(full)/len(full)
        se=math.sqrt(sum((x-mu)**2 for x in full)/len(full)/len(full))
        interval=[mu-1.96*se,mu+1.96*se]
    clipped=interval is not None and not (0<interval[0]<interval[1]<1)
    # Preserve the imported calculation for traceability; suppress inferential
    # use when its zero-variance normal interval would imply false certainty.
    return {'imported_summary':legacy,'complete_color_pairs':len(full),
            'incomplete_pair_ids':[k for k,v in scores.items() if len(v)!=2],
            'normal_score_interval':interval,'ci_reportable':not degenerate and not clipped,
            'elo_ci95_reportable':None if degenerate or clipped else legacy.get('elo_ci95'),
            'inference_limits':['normal-approximation pair interval; repeated 50-opening book',
                                *(['insufficient pairs or zero observed pair variance; no reliable CI'] if degenerate else []),
                                *(['normal interval reaches outside probability bounds; imported Elo clamps endpoints'] if clipped else [])]}


def commit_game(folder,contract,record,pgn):
    folder=Path(folder);path=folder/'games'/f"game-{record['game']:06d}.json"
    if path.exists():raise FileExistsError('Completed game is immutable: '+str(path))
    envelope={'contract':fingerprint(contract),'record':record,'pgn':pgn}
    validate_envelope(envelope,contract,envelope['contract'])
    atomic_json(path,envelope)


def export_journal(folder,contract):
    folder=Path(folder);envelopes=journal_records(folder,contract)
    summary=checked_summary(envelopes,contract)
    # These can be rebuilt from the atomic envelopes after any interruption.
    (folder/'games.jsonl').write_text(''.join(json.dumps(e['record'])+'\n' for e in envelopes),encoding='utf-8')
    (folder/'games.pgn').write_text('\n\n'.join(e['pgn'] for e in envelopes)+'\n',encoding='utf-8')
    atomic_json(folder/'summary.json',summary)
    return summary


def export_estimate(folder,contract,wall_seconds=None):
    records=[e['record'] for e in journal_records(folder,contract)]
    if len(records)!=2:raise ValueError('Pilot must contain exactly two completed games')
    per=sum(r['seconds'] for r in records)/2
    atomic_json(Path(folder)/'estimate.json',{'games':2,'seconds_per_game':per,
                'provisional_pairs':contract['settings']['pairs'],
                'provisional_hours':2*contract['settings']['pairs']*per/3600,
                'wall_seconds_current_invocation_including_startup':wall_seconds,
                'contract':fingerprint(contract),'scope':'two-game planning estimate, not strength evidence'})


def build_contract(a,ea,eb):
    settings={k:getattr(a,k) for k in ('tc','pairs','estimate','threads','minibatch','move_overhead',
               'tb_men','resign_cp','draw_cp','draw_after','max_plies','no_flag')}
    return {'engine_names':[ea['name'],eb['name']],
            'engines':[{'model':identity(e['weights']),'backend':e['backend'] or a.backend,
                        'opts':e['opts']} for e in (ea,eb)],
            'lc0':identity(a.lc0),'rules_source':identity(ROOT/'eval/match.py'),
            'uci_source':identity(ROOT/'eval/lc0uci.py'),'wrapper_source':identity(__file__),
            'opening_book':OPENINGS,'settings':settings,'syzygy_adjudicator_only':str(Path(a.syzygy).resolve()),
            'warmup':'one unscored 2000ms search per engine before starting match clocks'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--lc0',required=True);ap.add_argument('--a',required=True);ap.add_argument('--b',required=True)
    ap.add_argument('--name',required=True);ap.add_argument('--out-dir',required=True)
    ap.add_argument('--session',required=True);ap.add_argument('--backend',default='onnx-trt')
    ap.add_argument('--tc',default='10+0.1');ap.add_argument('--pairs',type=int,default=250)
    ap.add_argument('--estimate',type=int,default=0);ap.add_argument('--sizing')
    ap.add_argument('--threads',type=int,default=0);ap.add_argument('--minibatch',type=int,default=0)
    ap.add_argument('--move-overhead',type=int,default=50);ap.add_argument('--syzygy',required=True)
    ap.add_argument('--tb-men',type=int,default=5);ap.add_argument('--resign-cp',type=int,default=1000)
    ap.add_argument('--draw-cp',type=int,default=10);ap.add_argument('--draw-after',type=int,default=80)
    ap.add_argument('--max-plies',type=int,default=400)
    a=ap.parse_args();a.no_flag=False
    require_session(a.session)
    if a.estimate not in (0,2) or a.pairs<1:raise ValueError('Use two pilot games or a positive frozen production size')
    parse_tc(a.tc)
    if not a.estimate:
        if not a.sizing:raise ValueError('Production match requires Run 3 frozen sizing record')
        sizing=read_json(a.sizing)
        if sizing.get('frozen_before_production') is not True or sizing.get('pairs')!=a.pairs:
            raise ValueError('Match count was not frozen before production')
    out=Path(a.out_dir)/('pilot' if a.estimate else 'production')
    out.mkdir(parents=True,exist_ok=True)
    ea,eb=parse_engine(a.a),parse_engine(a.b)
    contract=build_contract(a,ea,eb)
    cp=out/'contract.json'
    if cp.exists():
        if read_json(cp)!=contract:raise ValueError('Refusing to resume different match settings/models')
    else:atomic_json(cp,contract)
    envelopes=journal_records(out,contract)
    done={e['record']['game'] for e in envelopes}
    target=a.estimate or 2*a.pairs
    if any(i>=target for i in done):raise ValueError('Existing game exceeds frozen target')
    if len(done)==target:
        export_journal(out,contract)
        if a.estimate:export_estimate(out,contract)
        return
    engines=[];started=time.perf_counter()
    try:
        for e in (ea,eb):
            opts={'MoveOverheadMs':a.move_overhead,'Ponder':False}
            if a.threads:opts['Threads']=a.threads
            if a.minibatch:opts['MinibatchSize']=a.minibatch
            engine=Lc0(a.lc0,e['weights'],backend=e['backend'] or a.backend,
                       backend_opts=e['opts'],options=opts,log=str(out/f"{e['name']}.lc0.log"),name=e['name'])
            engines.append(engine)
            engine.go(fen=chess.STARTING_FEN,movetime=2000)
        game=Game(a)
        for gi in range(target):
            if gi in done:continue
            aw=gi%2==0;white,black=engines if aw else engines[::-1]
            before=time.perf_counter()
            board,moves,result,reason,stats,clock=game.play(white,black,opening_moves(gi//2))
            secs=time.perf_counter()-before
            sw={'1-0':1.0,'0-1':0.0,'1/2-1/2':0.5}[result]
            aa=stats[chess.WHITE if aw else chess.BLACK];bb=stats[chess.BLACK if aw else chess.WHITE]
            avg=lambda d,k:sum(d[k])/len(d[k]) if d[k] else 0
            record={'game':gi,'pair':gi//2,'opening':(gi//2)%len(OPENINGS),
                    'white':ea['name'] if aw else eb['name'],'black':eb['name'] if aw else ea['name'],
                    'result':result,'reason':reason,'score_a':sw if aw else 1-sw,
                    'plies':len(moves),'seconds':secs,
                    'a_nodes_per_move':avg(aa,'nodes'),'b_nodes_per_move':avg(bb,'nodes'),
                    'a_ms_per_move':avg(aa,'ms'),'b_ms_per_move':avg(bb,'ms'),
                    'clock_left_ms':{'white':clock[chess.WHITE],'black':clock[chess.BLACK]}}
            pgn=chess.pgn.Game.from_board(board)
            pgn.headers.update({'Event':a.name,'Round':str(gi+1),'White':record['white'],
                                'Black':record['black'],'Result':result,'TimeControl':a.tc,'Termination':reason})
            commit_game(out,contract,record,str(pgn))
            export_journal(out,contract)
            print(f"game {gi+1}/{target}: {result}, {secs:.1f}s",flush=True)
    finally:
        for e in engines:e.quit()
    if a.estimate:
        export_estimate(out,contract,time.perf_counter()-started)


if __name__=='__main__':main()
