# Does INT8 make Leela stronger per second?

Code for the whole v5.1 plan as trimmed on Oct 26: gates C1 (FP16 end to end), C2 (best PTQ frozen) and C3 (speed and strength), plus the add-backs we kept (INT8 attention matmuls, SparseGPT 2:4, the policy/value swap). Everything runs through one script, `ladder.py`, on Windows or Linux.

What has and hasn't been tested: every step ran end to end on CPU (lc0 v0.33.0-rc0 built for Linux, onnx-cpu backend) against two stand-in nets. One is the T79-era 15x192 SE-ResNet that ships in the Windows lc0 package (`791556.pb.gz`, a real trained net). The other is a tiny random-weight net with BT3's exact structure (attention body, smolgen, PE_DENSE embedding, canonical V2 input), made by `tests/make_toy_bt.py` so every BT3 graph path goes through `lc0 leela2onnx` as it will on the real net. Nothing has touched BT3, TensorRT or a GPU. Those runs are yours.

Dropped from the plan and not in the code: s5 (search-visited calibration), partial INT8, the full 5-point batch sweep and the fixed 1000-game match (the match is sized from a smoke run instead).

## Layout

```
ladder.py                one entry point; reads config.json (copy config.example.json)
tb/build_tbset.py        Syzygy test set: exact result of every legal move, calib/dev/test splits
quant/lc0_encode.py      pure-Python port of lc0's input encoder (bit-exact, all 7 input formats)
quant/make_calib.py      calibration and dev planes (.npz) in lc0's exact encoding
quant/quantize.py        W8A8 QDQ: per-tensor/per-channel, minmax/percentile/entropy, SmoothQuant,
                         --act-act-matmul, outlier report
quant/prune24.py         S0: magnitude 2:4
quant/sparsegpt24.py     S1: SparseGPT 2:4 (sequential by default)
quant/stitch_swap.py     one ONNX with policy from model P and value/MLH from model V
quant/wrap.py            onnx2leela with formats copied from the original net, verified
eval/lc0uci.py           UCI driver (stock lc0, never given SyzygyPath)
eval/run_study.py        Study A (raw net), B (fixed nodes), C (fixed time); resumable, shardable
eval/score.py            accuracy + CI, paired worse/better + McNemar, KL, top-1, dV,
                         node-equivalents, Study C node ratios, hard subset, per-class table
eval/quick_compare.py    seconds-fast ONNX Runtime check on dev (for choosing knobs, not reporting)
eval/match.py            time-parity match with paired openings, TB/resign/draw adjudication,
                         pentanomial Elo + CI
hw/bench.py              backendbench + benchmark with GPU (NVML) and CPU (RAPL) energy above idle
hw/batch_sweep.py        MinibatchSize sweep: nps and mJ/node
hw/trt_layers.py         trtexec builds with lc0's settings; per-layer precision; nsys kernel check
hw/roofline.py           measured GEMM peaks + per-layer roofline from the trtexec profile
modal_app.py             Studies A/B on Modal L4s in parallel shards (untested, see below)
lc0-bindings.patch       only if you want lc0's Python bindings (not needed any more)
tests/                   toy BT-structured net, encoder test against lc0, parser fixtures
```

## Traps (read these first)

1. `onnx2leela` defaults to INPUT_CLASSICAL_112_PLANE. BT3 uses a canonical format, and with the default lc0 loads the file and feeds it wrongly encoded planes without complaint. `quant/wrap.py` copies every format from `lc0 describenet` and re-checks the result.
2. ONNX Runtime's entropy calibration is unusable here (one candidate threshold with its defaults, a no-merge first candidate with more bins). `quantize.py` calibrates minmax in ORT and computes percentile and entropy thresholds itself. Its entropy matches pytorch-quantization's TensorRT-style implementation exactly on a test histogram. On both stand-in nets entropy clipped some mish outputs to 1/8 of their range and did badly, so don't assume it beats percentile; that's what `select` is for.
3. onnxruntime >= 1.27 with TensorRT 10 silently runs FP32 instead of FP16. The Windows v0.33.0-rc0 package bundles onnxruntime 1.22.1, so it's safe. `run_study.py` and `bench.py` shout if lc0 warns about FP32.
4. `optimize=8` turns on INT8 and FP16, and also BF16 when lc0 was built against onnxruntime >= 1.23. With the bundled 1.22.1 it means FP16 + INT8 only, so unquantized layers run in FP16. Confirm with the kernel check in `day1`.
5. V2 canonical formats hang lc0 on a FEN-only position with a nonzero halfmove clock. All tablebase FENs use 0 and `make_calib.py` forces it. The Python encoder raises instead of hanging.
6. `go nodes N` overshoots by up to a minibatch. Studies record actual nodes and node-equivalents use them. Keep Threads and MinibatchSize the same across models.
7. lc0 prints P to 0.01% after storing priors in 16 bits, so Study A's KL is approximate below about 1e-4. Study A runs with PolicyTemperature=1; searches use lc0's default.
8. New today: lc0 subtracts MoveOverheadMs (default 200 ms) from every `go movetime`, so `movetime 200` searched for about 0 ms. Study C sets it to 20 ms and the match to 50 ms.
9. New today: lc0's Python bindings compute the canonical board transform in `as_input` but `policy_indices` ignores it, so legal-move indices are wrong on every pawnless position. `lc0-bindings.patch` fixes it, but the default path no longer uses the bindings at all: `quant/lc0_encode.py` reproduces lc0's encoder and policy indices bit for bit (`tests/test_encoder.py`: 850 positions per format, all 7 formats, including castling, en passant, repetitions and tablebase FENs).
10. New today: `lc0 benchmark`'s built-in position 4 has a nonzero halfmove clock, and lc0 segfaults on it with a V2-canonical net (trap 5's cause again). BT3 is most likely V2, so `bench.py` and `batch_sweep.py` time UCI searches on their own halfmove-0 positions instead, and meter energy only around those searches. Don't use `lc0 benchmark` beyond `--num-positions=3` with BT3.
11. Study B turns smart pruning off (SmartPruningFactor=0) so the search spends its budget. Study C and the match leave lc0's defaults, because that's how the engine plays.

## Setup (GPU machine, Windows)

1. lc0: unzip `lc0-v0_33_0-rc0-windows-onnx-trt.zip`, run `install.cmd` (downloads the CUDA, cuDNN and TensorRT 10.12 DLLs), and check `lc0.exe benchmark --backend=onnx-trt` starts.
2. trtexec: it's in the TensorRT 10.12 zip under `bin/` (the same zip install.cmd pulls the DLLs from). Nsight Systems (`nsys`) is a separate free download, needed only for the kernel check.
3. Python 3.10+: `pip install -r requirements.txt`. `onnxruntime-gpu` instead of `onnxruntime` makes `select`, `build` and SparseGPT faster but isn't required.
4. Syzygy 3-4-5 man WDL + DTZ (about 1 GB). Only the scorer and the match arbiter read them.
5. `copy config.example.json config.json` and edit the paths. Relative paths are relative to `work`.

The CPU-only steps (tbset, calib, select, build) can run on either of your laptops; copy `data/` and `models/` across. TensorRT engines are built per GPU, so the 4060 builds its own the first time each model loads (minutes per model, cached in `trt_cache` next to lc0.exe).

## Unattended run

`python overnight.py` runs day1 (as a go/no-go gate), bench, a sizing run that sets `study.limit` and `studyc.limit` to fit `--study-hours`/`--studyc-hours`, Studies A+B, Study C, hw, the match (pairs sized to `--match-hours`), score, and zips everything into `send_back.zip`. It is resumable and never edits `config.json` (it writes `config.run.json`). Tested end to end on CPU only. The sections below describe each step.

## Gate C1: FP16 end to end (tonight)

```
python ladder.py tbset                 # ~10k positions, 28 classes, 60% test
python ladder.py calib                 # data/calib.npz + data/dev.npz
python ladder.py day1                  # 200 dev positions
```

`day1` exports BT3 to ONNX, wraps it as `models/fp16.pb.gz`, builds `s2` (per-channel minmax INT8) and checks three things:

1. Wrapped FP16 matches native lc0 (BT3.pb.gz loaded directly by onnx-trt): KL about 0 and top-1 agreement about 1. If not, the wrapped path is wrong and nothing downstream is valid.
2. lc0 runs the INT8 file. If the engine build fails, that's the risk-row-1 fallback decision, today.
3. The matmuls really run in INT8. With `nsys` on PATH it profiles an lc0 benchmark and prints the share of GEMM kernel time by precision. Most should be int8.

Then the outlier report and FP16 baselines:

```
python ladder.py build --only s4       # also writes reports/outliers.txt
python ladder.py hw --parts bench      # fp16, best and native: nps, J/node above idle, clocks
```

`outlier_ratio` is the worst input channel's |x|max over the median live channel's. Tens to hundreds on the LN outputs feeding QKV/FFN means SmoothQuant has work to do. Near 1-5 everywhere is risk row 3. Try `nvidia-smi -lgc <clock>` first (admin); if it refuses, the logged SM clock is your evidence.

Size Study B before committing a night: `python ladder.py study --models fp16 --limit 50` and read the s/position from the progress line at 1600 nodes. Multiply by the number of models and pick `study.limit` so it fits. Don't pick the size and hope.

## Gate C2: best PTQ frozen (night of the 27th)

```
python ladder.py select                # step 3 grid on dev: percentile 99.9/99.99/99.999, entropy
#   set recipe.s3_method / s3_percentile in config.json from reports/select_s3_dev.txt
python ladder.py select --alpha        # step 4 grid: SmoothQuant alpha 0.3..0.8
#   set recipe.s4_alpha; if no alpha beats step 3, set "best": "s3"
python ladder.py build                 # s1 s2 s3 s4 s4aa s0 s1sp swap_pol8 swap_val8, wrapped
python ladder.py study                 # overnight: Studies A + B on test
python ladder.py score                 # reports/scores_test.md, reports/hard/
```

Choosing on dev and reporting on test keeps the ablation honest. `reports/quick_compare_dev.txt` has every built model's ORT numbers on dev.

The ladder: s1 per-tensor minmax, s2 per-channel, s3 per-channel + the chosen clipping, s4 = s3 + SmoothQuant. Add-backs: s4aa is the best recipe with Q·Kᵀ and attn·V also in INT8. s0 and s1sp are magnitude and SparseGPT 2:4 followed by the best recipe (zeros stay zeros under symmetric INT8). swap_pol8 takes policy from the best INT8 model and value from FP16; swap_val8 the reverse. Each runs both bodies, so they're about 2x slower: accuracy only, never timed. Each model's `.json` sidecar records the recipe, clip fractions, smoothing groups and, for SparseGPT, per-layer reconstruction error against what magnitude pruning would give.

SparseGPT is the slowest build step: about 90 dependency stages on BT3, each a pass over the calibration set. With `onnxruntime-gpu` installed it uses the GPU; on CPU expect most of an hour, or run `quant/sparsegpt24.py ... --one-shot` (one pass, slightly worse). It warns on layers with fewer calibration rows than 2x their inputs; smolgen's dense1 sees one row per position, so give it a big calibration set (`calib.random_games` 1024 or more) if those warnings show up.

S0 gets Study A only by default. If its raw accuracy comes out close to FP16, set `extras.s0_in_study_b` to true and rerun `study` (it resumes).

SmoothQuant inserts a Mul before each smoothed group instead of folding into the LayerNorm, because in lc0's graphs the LN output also feeds the residual skip. TensorRT normally fuses that Mul into the following quantize. smolgen's global weight is shared by every layer, so it can't take per-layer scales and is left unsmoothed.

Reading `scores_test.md`: each row is scored on positions that model and FP16 both finished at every budget (the `n` column); the header warns if n differs. Node-equivalent = FP16 nodes needed to reach the model's accuracy divided by the model's nodes: 1.00 when it matches FP16, 0 when it's below even FP16's raw net, inf above FP16's largest budget. Where FP16's curve is flat the closest point to the model's own node count is used, so a model matching a saturated FP16 gets 1.00. Paired counts are "−worse/+better" with an exact McNemar p. If the full set can't separate models, the hard subset (FP16's raw move wrong, or under 80% raw policy mass on correct moves) is risk row 7.

## Gate C3: speed and strength (nights of the 27th and 28th)

```
python ladder.py studyc                # fp16 and best at 200 and 800 ms/move, lc0 default Threads
python ladder.py match --estimate 2    # time two games, prints how many pairs fit 8 h
#   set match.pairs from that, then:
python ladder.py match                 # resumable; summary.json every 10 games
python ladder.py hw                    # bench, batch sweep, trtexec builds (incl. sparse), peaks, roofline
```

Study C's table shows accuracy at fixed time and `×` = the model's nodes over FP16's at the same time, which is the realised search speed-up. The match's Elo comes from game pairs (pentanomial), the right error model for paired openings; `elo_ci95` and `los` are in `summary.json`. If 250 pairs don't fit a night at your time control, cut pairs before cutting the time control.

`hw` writes:
- `reports/bench/<model>.json`: backendbench nps per batch, search nps over 10 fixed positions (10 s each), GPU J/node above idle, SM clock min/mean, max temperature.
- `reports/batch_sweep/`: nps and mJ/node vs MinibatchSize for fp16 and best (4 points).
- `reports/trt/`: trtexec builds of fp16, best, and s0/s1sp with and without `--sparsity=enable`, each with a per-layer precision table and qps. lc0's onnx-trt doesn't pass a sparsity flag, so S0's speed ceiling comes from the trtexec sparse vs dense numbers.
- `reports/trt/peak.json`: measured FP16 and INT8 GEMM peaks and bandwidth on this GPU.
- `reports/roofline/`: per-layer arithmetic intensity vs achieved TFLOPS against those peaks, CSV + PNG. Myelin `ForeignNode` regions are attributed to every ONNX node between their first and last op; bytes are modelled, not measured.

## Modal (optional, for accuracy only)

`modal_app.py` runs Studies A/B on L4 GPUs (Ada, like the 4060) in parallel shards and merges them. It has not been run: there was no Modal account where this was written, so start with `--models fp16 --limit 50 --shards 1`. Never mix machines within one table: run FP16 and every INT8 model on the same hardware. Speed, energy, Study C and the match stay on the 4060.

## Testing this code on CPU (what was done)

```
python tests/make_toy_bt.py --proto <lc0>/proto/net.proto --out nets/toy_bt.pb.gz
python tests/test_encoder.py --lc0-py <lc0>/build --proto <lc0>/proto/net.proto --tbset data/tbset.jsonl
# then config.json with "backend": "onnx-cpu", empty opts, and the toy net as "bt3"; run every step
```

What that showed, on stand-in nets (not results): wrapped FP32 matched native lc0 to KL 1e-8. On the trained T79 net, per-channel INT8 kept raw tablebase accuracy (0.993 vs 0.993) with policy KL 0.025; magnitude 2:4 dropped it to 0.972 and SparseGPT cut the value error versus magnitude by about 40% on the layers it could prune (T79's convs fall back to magnitude). On the toy transformer with planted outlier channels, SmoothQuant at alpha 0.5 cut policy KL about 3x versus percentile alone. SparseGPT's per-layer reconstruction error was about 30x below magnitude's, and it beat magnitude on held-out data in a synthetic check.
