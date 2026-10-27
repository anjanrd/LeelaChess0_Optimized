"""Bounded, exact-operator ONNX-to-PyTorch feasibility; no optimizer or training run."""
import collections
import gc
import json
import time

import chess
import numpy as np
import onnx
import torch
import torch.nn.functional as F

from week1_common import PROJECT, RUNTIME, artifact, base, frozen, progress, read, save
from lc0_inputs import legal_policy


class BT3Module(torch.nn.Module):
    """Execute the source ONNX operators with unique, shared trainable matrices.

    Integer shape/index initializers stay on CPU. Floating nonscalar initializers
    are Parameters; scalar multipliers stay fixed buffers in this feasibility
    port. This explicit choice is not a claim to reconstruct a training recipe.
    """
    SUPPORTED = {'Transpose', 'Reshape', 'Slice', 'MatMul', 'Add', 'Concat', 'Softplus',
                 'Tanh', 'Mul', 'LayerNormalization', 'Softmax', 'Split', 'Gather', 'Relu'}

    def __init__(self, path):
        super().__init__()
        graph = onnx.load(path).graph
        assert {n.op_type for n in graph.node} <= self.SUPPORTED
        self.weights = torch.nn.ParameterDict(); self.names = {}; self.integers = {}; self.index_cache = {}
        for index, initializer in enumerate(graph.initializer):
            array = onnx.numpy_helper.to_array(initializer).copy()
            name = 'p'+str(index)
            if np.issubdtype(array.dtype, np.floating):
                value = torch.from_numpy(array)
                if array.size > 1:
                    self.weights[name] = torch.nn.Parameter(value)
                    self.names[initializer.name] = ('parameter', name)
                else:
                    self.register_buffer(name, value)
                    self.names[initializer.name] = ('buffer', name)
            else:
                self.integers[initializer.name] = torch.from_numpy(array)
        self.nodes = [(n.name, n.op_type, list(n.input), list(n.output),
                      {a.name: onnx.helper.get_attribute_value(a) for a in n.attribute}) for n in graph.node]
        self.uses = collections.Counter(v for _,_,inputs,_,_ in self.nodes for v in inputs)
        self.outputs = [x.name for x in graph.output]
        self.uses.update(self.outputs)

    def forward(self, planes):
        values = dict(self.integers)
        values.update({name: self.weights[key] if kind == 'parameter' else getattr(self, key)
                       for name, (kind, key) in self.names.items()})
        values['/input/planes'] = planes
        remaining = self.uses.copy()
        for name, op, inputs, outputs, attributes in self.nodes:
            x = [values[v] if v else None for v in inputs]
            axis = attributes.get('axis', -1)
            if op == 'MatMul': result = x[0] @ x[1]
            elif op == 'Add': result = x[0] + x[1]
            elif op == 'Mul': result = x[0] * x[1]
            elif op == 'Transpose': result = x[0].permute(tuple(attributes.get('perm', reversed(range(x[0].ndim)))))
            elif op == 'Reshape':
                shape = [int(v) for v in x[1].tolist()]
                if not attributes.get('allowzero', 0): shape = [x[0].shape[i] if v == 0 else v for i,v in enumerate(shape)]
                result = x[0].reshape(shape)
            elif op == 'Concat': result = torch.cat(x, dim=attributes['axis'])
            elif op == 'Softplus': result = F.softplus(x[0])
            elif op == 'Tanh': result = torch.tanh(x[0])
            elif op == 'Relu': result = torch.relu(x[0])
            elif op == 'Softmax': result = torch.softmax(x[0], dim=axis)
            elif op == 'LayerNormalization':
                axis = axis if axis >= 0 else x[0].ndim+axis
                result = F.layer_norm(x[0], x[0].shape[axis:], x[1], x[2], eps=attributes.get('epsilon', 1e-5))
                assert len(outputs) == 1
            elif op == 'Slice':
                starts, ends = x[1].tolist(), x[2].tolist()
                axes = x[3].tolist() if len(x)>3 else list(range(len(starts)))
                steps = x[4].tolist() if len(x)>4 else [1]*len(starts)
                slices = [slice(None)]*x[0].ndim
                for a,s,e,step in zip(axes,starts,ends,steps): slices[a] = slice(s,e,step)
                result = x[0][tuple(slices)]
            elif op == 'Split': result = torch.split(x[0], [int(v) for v in x[1].tolist()], dim=axis)
            elif op == 'Gather':
                cache_key = (inputs[1], str(x[0].device))
                if cache_key not in self.index_cache: self.index_cache[cache_key] = x[1].long().to(x[0].device)
                index = self.index_cache[cache_key]
                shape = tuple(x[0].shape[:axis])+tuple(index.shape)+tuple(x[0].shape[axis+1:])
                result = torch.index_select(x[0], axis, index.flatten()).reshape(shape)
            else: raise NotImplementedError((name, op))
            result = result if isinstance(result, (list,tuple)) else [result]
            assert len(result) == len(outputs), name
            values.update(zip(outputs,result))
            for key in inputs:
                remaining[key] -= 1
                if remaining[key] == 0: values.pop(key, None)
        return [values[k] for k in self.outputs]


def main():
    assert read(PROJECT/'results/week1/calibration-outliers.json')['status'] == 'passed'
    frozen()
    protocol = {'registered_at_utc': base.now(), 'budget': '45 minutes; one exact-operator port and at most two implementation repairs; FP32 batch 1 backward only',
        'source': artifact(PROJECT/'models/onnx/bt3-r32.onnx'), 'parity_data': 'First 16 calibration roots, batches 1 and 4',
        'parity_limits': {'legal_probability_max_abs': .0002, 'policy_KL_max': .00001, 'WDL_max_abs': .0005, 'moves_left_atol': .02, 'moves_left_rtol': .0002},
        'gradient': 'One differentiability/memory check using policy-logit, WDL and moves-left surrogate terms. No optimizer step, QAT or distillation.',
        'failure_outcome': 'Document precise unsupported/parity/memory limitation after bounded investigation; mandatory PTQ path remains independent'}
    save(PROJECT/'environment/week1-torch-protocol.json', protocol)
    progress('W1-A11', 'IN_PROGRESS', detail='Bounded exact-operator trainable conversion; checking FP32 parity and one gradient/memory pass, without an optimizer.')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_float32_matmul_precision('highest')
    began = time.perf_counter()
    model = BT3Module(PROJECT/'models/onnx/bt3-r32.onnx').cuda()
    model.eval()
    with np.load(PROJECT/'data/syzygy/calibration-inputs.npz', allow_pickle=False) as d: planes = d['planes'][:16].copy()
    rows = [json.loads(s) for s in (PROJECT/'data/syzygy/calibration.jsonl').read_text().splitlines()][:16]
    with np.load(PROJECT/'results/week1/calibration-R32_CUDA-outputs.npz', allow_pickle=False) as d:
        expected = [d[n][:16].copy() for n in ['logits', 'wdl', 'moves_left']]
    metrics = {}
    with torch.no_grad():
        for batch in [1,4]:
            chunks = [[v.cpu().numpy() for v in model(torch.from_numpy(planes[s:s+batch]).cuda())] for s in range(0,16,batch)]
            output = [np.concatenate([c[j] for c in chunks]) for j in range(3)]
            probability_max = 0.; kl_max = 0.; agreement = 0
            for row, a, b in zip(rows, expected[0], output[0]):
                _, p, move = legal_policy(a, chess.Board(row['fen'])); _, q, other = legal_policy(b, chess.Board(row['fen']))
                probability_max = max(probability_max, float(abs(p-q).max()))
                kl_max = max(kl_max, float(np.sum(p.astype(float)*np.log(np.maximum(p,1e-30)/np.maximum(q,1e-30)))))
                agreement += move == other
            wdl_max = float(abs(output[1]-expected[1]).max())
            mlh_max = float(abs(output[2]-expected[2]).max())
            metrics[str(batch)] = {'legal_probability_max_abs': probability_max, 'policy_KL_max': kl_max,
                'WDL_max_abs': wdl_max, 'moves_left_max_abs': mlh_max, 'top_move_agreement': agreement/16}
            assert probability_max <= .0002 and kl_max <= .00001 and wdl_max <= .0005, metrics[str(batch)]
            np.testing.assert_allclose(output[2], expected[2], atol=.02, rtol=.0002)
    model.train(); model.zero_grad(set_to_none=True)
    torch.cuda.reset_peak_memory_stats()
    output = model(torch.from_numpy(planes[:1]).cuda())
    # Deliberately small surrogate; this is a backward feasibility check only.
    loss = output[0].square().mean()*1e-3 + output[1][:,0].mean() + output[2].mean()*1e-4
    assert torch.isfinite(loss)
    loss.backward(); torch.cuda.synchronize()
    grads = {}; missing = []; zero = []
    for name, (kind, key) in model.names.items():
        if kind != 'parameter': continue
        grad = model.weights[key].grad
        if grad is None: missing.append(name); continue
        assert torch.isfinite(grad).all(), name
        norm = float(grad.norm())
        grads[name] = norm
        if norm == 0: zero.append(name)
    assert not missing, missing
    assert grads['/attn_body/matmul/w'] > 0
    assert grads['/const/smolgen_w'] > 0
    assert any(v > 0 and name.startswith('/policy') for name,v in grads.items())
    assert any(v > 0 and name.startswith('/value') for name,v in grads.items())
    assert any(v > 0 and name.startswith('/mlh') for name,v in grads.items())
    result = {'status': 'passed_feasibility', 'created_at_utc': base.now(), 'parity': metrics,
        'unique_trainable_initializer_tensors': len(model.weights), 'trainable_parameters': sum(p.numel() for p in model.parameters()),
        'shared_initializer_instances_preserved': True, 'fixed_scalar_initializers': [name for name,(kind,_) in model.names.items() if kind=='buffer'],
        'gradient_norms': grads, 'zero_gradient_tensors': zero, 'missing_gradients': missing,
        'CUDA_peak_allocated_bytes': torch.cuda.max_memory_allocated(), 'CUDA_peak_reserved_bytes': torch.cuda.max_memory_reserved(),
        'batch_for_backward': 1, 'optimizer_steps': 0, 'QAT_or_distillation_performed': False,
        'scope': 'Trainable exact-operator feasibility port; original FP32 ONNX/checkpoint remain source of truth. Scalar multipliers are fixed; this is not a reconstruction of original lc0 training configuration.',
        'limitations': 'One batch and one backward pass do not establish QAT convergence, full optimizer memory or larger-batch feasibility. A later training branch requires a separately registered protocol and validation.',
        'protocol': artifact(PROJECT/'environment/week1-torch-protocol.json'), 'script': artifact(PROJECT/'scripts/torch_feasibility_week1.py'),
        'source': protocol['source'], 'torch': torch.__version__, 'gpu': torch.cuda.get_device_name(0), 'seconds': time.perf_counter()-began}
    model.zero_grad(set_to_none=True)
    # The deterministic reconstruction script plus frozen ONNX stores the model;
    # do not duplicate another 410 MB weight file in the project.
    save(PROJECT/'environment/week1-torch-feasibility.json', result)
    del model; gc.collect(); torch.cuda.empty_cache()
    frozen()
    progress('W1-A11', 'DONE', 'environment/week1-torch-feasibility.json', 'Exact-operator FP32 forward parity and a batch-1 finite-gradient/memory check verified. No optimizer step, QAT or distillation performed.')
    print('PyTorch feasibility verified', result['CUDA_peak_allocated_bytes'], metrics, flush=True)


if __name__ == '__main__': main()
