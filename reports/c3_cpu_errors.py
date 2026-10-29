"""CPU-only audit of saved results and swap provenance; no engine calls."""
import collections
import gc
import hashlib
import json
from pathlib import Path

import onnx

ROOT = Path(__file__).resolve().parents[1]
def read(p):
    return [json.loads(x) for x in (ROOT / p).read_bytes().splitlines() if x.strip()]
def digest(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

tb = {r['id']: r for r in read('data/tbset.jsonl')}
a = {n: {r['id']: r for r in read(f'results/{n}/study_a.jsonl')} for n in ('s1sp', 'fp16')}
b = {n: {r['id']: r for r in read(f'results/{n}/study_b.jsonl') if r['budget'] == 1600} for n in ('s1sp', 'fp16')}
ids = sorted(i for i in b['s1sp'] if tb[i]['split'] == 'test')
assert len(ids) == 2437
errors = [i for i in ids if b['s1sp'][i]['best'] not in tb[i]['correct']]
raw = [i for i in ids if tb[i]['cls'] == 'KQvK' and a['s1sp'][i]['best'] not in tb[i]['correct']]
assert len(errors) == 14, len(errors)
assert len(raw) == 6, len(raw)
md = ['# s1sp errors from existing results', '', 'No engines, tablebase probes, or scoring commands were run. Result values are the saved tablebase labels, from the root side-to-move perspective: +1 win, 0 draw, -1 loss. A chosen move is wrong when it is absent from `correct`.', '']
for title, subset, data in [('Study B, requested budget 1600', errors, b), ('Study A raw: six KQvK errors', raw, a)]:
    md += [f'## {title} ({len(subset)} positions)', '', '| ID | Class | FEN | s1sp chosen | Chosen TB result | Root TB result | Correct moves | fp16 chosen | fp16 correct? |', '|---:|---|---|---|---:|---:|---|---|---|']
    for i in subset:
        r = tb[i]
        chosen = data['s1sp'][i]['best']
        ref = data['fp16'][i]['best']
        res = r['moves'][chosen]['res']
        line = f"| {i} | {r['cls']} | `{r['fen']}` | {chosen} | {res:+d} | {r['root']:+d} | {', '.join(r['correct'])} | {ref} | {'yes' if ref in r['correct'] else 'no'} |"
        md.append(line)
        print(line)
    md.append('')
(ROOT / 'reports/s1sp_errors.md').write_text('\n'.join(md), encoding='utf-8')

provenance = {}
for name in ('swap_pol8', 'swap_val8'):
    sidecar = json.loads((ROOT / f'models/{name}.json').read_text(encoding='utf-8-sig'))
    info = {'pb_gz_sha256': digest(ROOT / f'models/{name}.pb.gz'), 'onnx_sha256': digest(ROOT / f'models/{name}.onnx')}
    for role in ('policy', 'value_mlh'):
        source = sidecar[role]
        actual = digest(source['onnx'])
        assert actual == source['sha256'], (name, role)
        info[role] = dict(source, verified_sha256=actual)
    model = onnx.load(str(ROOT / f'models/{name}.onnx'), load_external_data=False)
    info['shared_graph_inputs'] = [v.name for v in model.graph.input]
    info['quantize_nodes_by_branch'] = {prefix: sum(n.name.startswith(prefix) and n.op_type == 'QuantizeLinear' for n in model.graph.node) for prefix in ('P', 'V')}
    info['output_routes'] = {n.name: list(n.input) for n in model.graph.node if n.name.startswith('/swap')}
    provenance[name] = info
    del model
    gc.collect()
    print(name, json.dumps(info))
assert provenance['swap_pol8']['pb_gz_sha256'] != provenance['swap_val8']['pb_gz_sha256']
assert provenance['swap_pol8']['policy']['verified_sha256'] != provenance['swap_val8']['policy']['verified_sha256']
assert provenance['swap_pol8']['value_mlh']['verified_sha256'] != provenance['swap_val8']['value_mlh']['verified_sha256']
assert provenance['swap_pol8']['quantize_nodes_by_branch']['P'] > 0 and provenance['swap_pol8']['quantize_nodes_by_branch']['V'] == 0
assert provenance['swap_val8']['quantize_nodes_by_branch']['V'] > 0 and provenance['swap_val8']['quantize_nodes_by_branch']['P'] == 0
(ROOT / 'reports/c3_swap_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
print('CONFIRMED: 14 s1sp B1600 errors; 6 s1sp KQvK raw errors; swap weights differ; policy/value source files are reversed, hashes verified, quantized P/V branches reversed. Both intentionally share the board-plane input.')
print('PRODUCED reports/s1sp_errors.md reports/c3_swap_provenance.json')
