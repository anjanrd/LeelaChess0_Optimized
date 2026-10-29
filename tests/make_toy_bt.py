#!/usr/bin/env python3
"""Write a tiny random-weight lc0 net with BT3's *structure* (attention body,
PE_DENSE embedding, smolgen, post-LN encoders, attention policy, WDL value,
MLH, canonical V2 input). Plays nonsense chess; it exists so every graph
path the pipeline touches on BT3 (LayerNorm, smolgen's shared weight, Q·Kᵀ
and attn·V act-act matmuls, policy attention) can be exercised on CPU
through `lc0 leela2onnx` exactly as it will be on the real net.

    python tests/make_toy_bt.py --proto /path/to/lc0/proto/net.proto --out nets/toy_bt.pb.gz
"""
import argparse
import gzip
import importlib
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


def load_pb2(proto):
    d = Path(tempfile.mkdtemp())
    proto = Path(proto).resolve()
    subprocess.check_call([sys.executable, "-m", "grpc_tools.protoc",
                           f"-I{proto.parent}", f"--python_out={d}", str(proto)])
    sys.path.insert(0, str(d))
    return importlib.import_module(proto.stem + "_pb2")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proto", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--emb", type=int, default=64)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--dff", type=int, default=128)
    ap.add_argument("--layers", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--input-format", type=int, default=5,
                    help="lc0 InputFormat enum (BT3-era nets: 5 = CANONICALIZATION_V2)")
    a = ap.parse_args()
    pb = load_pb2(a.proto)
    rng = np.random.default_rng(a.seed)
    E, H, F, L = a.emb, a.heads, a.dff, a.layers
    DENSE, SG_CH, SG_HID, SG_GEN = 16, 8, 64, 64

    def put(layer, arr):
        arr = np.asarray(arr, dtype=np.float32).ravel()
        layer.encoding = pb.Weights.Layer.FLOAT16  # 2-byte, as real nets
        layer.params = arr.astype(np.float16).tobytes()
        layer.min_val, layer.max_val = float(arr.min()), float(arr.max())

    def lin(layer_w, layer_b, n_out, n_in, scale=1.0):
        # lc0 stores dense weights as [out, in].
        put(layer_w, rng.normal(0, scale / np.sqrt(n_in), (n_out, n_in)))
        if layer_b is not None:
            put(layer_b, rng.normal(0, 0.02, n_out))

    def ln(g, b, n, outliers=0):
        gam = 1 + rng.normal(0, 0.05, n)
        if outliers:  # a few large channels, as real transformers have
            gam[rng.choice(n, outliers, replace=False)] *= 25
        put(g, gam)
        put(b, rng.normal(0, 0.02, n))

    net = pb.Net()
    net.magic = 0x1c0
    net.min_version.major, net.min_version.minor = 0, 33
    nf = net.format.network_format
    net.format.weights_encoding = pb.Format.LINEAR16
    nf.input = a.input_format
    nf.output = pb.NetworkFormat.OUTPUT_WDL
    nf.network = pb.NetworkFormat.NETWORK_ATTENTIONBODY_WITH_MULTIHEADFORMAT
    nf.policy = pb.NetworkFormat.POLICY_ATTENTION
    nf.value = pb.NetworkFormat.VALUE_WDL
    nf.moves_left = pb.NetworkFormat.MOVES_LEFT_V1
    nf.default_activation = pb.NetworkFormat.DEFAULT_ACTIVATION_MISH
    nf.smolgen_activation = pb.NetworkFormat.ACTIVATION_SWISH
    nf.ffn_activation = pb.NetworkFormat.ACTIVATION_DEFAULT
    nf.input_embedding = pb.NetworkFormat.INPUT_EMBEDDING_PE_DENSE

    w = net.weights
    lin(w.ip_emb_preproc_w, w.ip_emb_preproc_b, 64 * DENSE, 64 * 12)
    lin(w.ip_emb_w, w.ip_emb_b, E, 112 + DENSE)
    ln(w.ip_emb_ln_gammas, w.ip_emb_ln_betas, E)
    put(w.ip_mult_gate, 1 + rng.normal(0, 0.05, (E, 64)))
    put(w.ip_add_gate, rng.normal(0, 0.02, (E, 64)))
    lin(w.ip_emb_ffn.dense1_w, w.ip_emb_ffn.dense1_b, F, E)
    lin(w.ip_emb_ffn.dense2_w, w.ip_emb_ffn.dense2_b, E, F)
    ln(w.ip_emb_ffn_ln_gammas, w.ip_emb_ffn_ln_betas, E)
    w.headcount = H
    put(w.smolgen_w, rng.normal(0, 0.05, (4096, SG_GEN)))
    for i in range(L):
        enc = w.encoder.add()
        m = enc.mha
        for wn, bn in (("q_w", "q_b"), ("k_w", "k_b"), ("v_w", "v_b")):
            lin(getattr(m, wn), getattr(m, bn), E, E)
        lin(m.dense_w, m.dense_b, E, E)
        s = m.smolgen
        put(s.compress, rng.normal(0, 1 / np.sqrt(E), (SG_CH, E)))
        lin(s.dense1_w, s.dense1_b, SG_HID, 64 * SG_CH)
        ln(s.ln1_gammas, s.ln1_betas, SG_HID)
        lin(s.dense2_w, s.dense2_b, SG_GEN * H, SG_HID)
        ln(s.ln2_gammas, s.ln2_betas, SG_GEN * H)
        ln(enc.ln1_gammas, enc.ln1_betas, E, outliers=2)
        lin(enc.ffn.dense1_w, enc.ffn.dense1_b, F, E)
        lin(enc.ffn.dense2_w, enc.ffn.dense2_b, E, F)
        ln(enc.ln2_gammas, enc.ln2_betas, E, outliers=2)

    ph = w.policy_heads
    lin(ph.ip_pol_w, ph.ip_pol_b, E, E)
    v = ph.vanilla
    lin(v.ip2_pol_w, v.ip2_pol_b, E, E)
    lin(v.ip3_pol_w, v.ip3_pol_b, E, E)
    put(v.ip4_pol_w, rng.normal(0, 1 / np.sqrt(E), (4, E)))

    vh = w.value_heads.winner
    lin(vh.ip_val_w, vh.ip_val_b, 8, E)
    lin(vh.ip1_val_w, vh.ip1_val_b, 128, 8 * 64)
    lin(vh.ip2_val_w, vh.ip2_val_b, 3, 128)

    lin(w.ip_mov_w, w.ip_mov_b, 8, E)
    lin(w.ip1_mov_w, w.ip1_mov_b, 32, 8 * 64)
    lin(w.ip2_mov_w, w.ip2_mov_b, 1, 32)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(a.out, "wb") as f:
        f.write(net.SerializeToString())
    print("wrote", a.out)


if __name__ == "__main__":
    main()
