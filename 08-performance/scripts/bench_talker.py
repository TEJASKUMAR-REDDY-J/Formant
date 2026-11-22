"""PF1: time one 80 ms talker step on the laptop, dense vs MoE, with random weights.

Speed depends on shapes, not on weight values, so nothing is downloaded. The graph is AR1's spec:
28 layers, d = 1024, 16 query / 8 KV heads, 24 layers with a 750-frame window and 4 with 2,250,
a 40k text head, and either a dense 3,072-wide SwiGLU FFN or (layers 2-27) a 1,536-wide shared expert
plus 32 routed experts of width 384, top-4. Active FFN width is 3,072 in both.

Left out on purpose (small or not decided yet): RoPE, embedding lookups, turn-state head, depth decoder, codec.
The KV cache is read-only host memory here; a real loop writes one new column per frame (about 115 KB in all).

    python 08-performance/scripts/bench_talker.py --kind dense --ffn-bits 4 --device GPU
"""
import argparse, json, time
import numpy as np
import openvino as ov
import openvino.opset13 as op

D, FFN, KVH, QPK, HD, VOCAB = 1024, 3072, 8, 2, 128, 40_000  # QPK: query heads per KV head
SHARED, ROUTED, N_EXP, TOPK = 1536, 384, 32, 4
GLOBAL_LAYERS, WIN, GLOBAL_WIN = {6, 13, 20, 27}, 750, 2250
F16 = np.float16
rng = np.random.default_rng(0)
KEEP = []


def weight(shape, bits, group=128):
    """Random constant in the layout OpenVINO compresses weights in, decompressed to f16. Last axis = input dim."""
    if bits == 16:
        return op.constant(rng.standard_normal(shape, dtype=np.float32).astype(F16) * F16(0.02))
    if bits == 8:
        w = op.convert(op.constant(rng.integers(-127, 127, shape, dtype=np.int8)), "f16")
        return op.multiply(w, op.constant(np.full((*shape[:-1], 1), 2e-4, F16)))
    g = [*shape[:-1], shape[-1] // group, group]                      # 4-bit, group-wise scales
    raw = rng.integers(0, 256, int(np.prod(g)) // 2, dtype=np.uint8)
    zps = np.full(int(np.prod(g[:-1])) // 2, 0x88, np.uint8)
    KEEP.extend((raw, zps))                                            # ov.Tensor shares this memory; freeing it crashes the compiler
    w = op.convert(op.constant(ov.Tensor(raw, ov.Shape(g), ov.Type.u4)), "f16")
    zp = op.convert(op.constant(ov.Tensor(zps, ov.Shape([*g[:-1], 1]), ov.Type.u4)), "f16")
    w = op.multiply(op.subtract(w, zp), op.constant(np.full((*g[:-1], 1), 3e-3, F16)))
    return op.reshape(w, op.constant(np.array(shape)), False)


def fc(x, n_in, n_out, bits):
    return op.matmul(x, weight((n_out, n_in), bits), False, True)


def silu(x):
    return op.swish(x, op.constant(F16(1.0)))


def swiglu(x, width, bits):
    return fc(op.multiply(silu(fc(x, D, width, bits)), fc(x, D, width, bits)), width, D, bits)


def rms(x):
    var = op.reduce_mean(op.multiply(x, x), op.constant(np.array([-1])), True)
    return op.divide(x, op.sqrt(op.add(var, op.constant(F16(1e-3)))))


def routed(x, bits):
    """Top-4 of 32 experts for one frame: gather only the chosen experts' weights, then multiply."""
    scores = op.sigmoid(fc(x, D, N_EXP, 16))
    top = op.topk(scores, op.constant(np.int64(TOPK)), -1, "max", "value")
    idx = op.reshape(top.output(1), op.constant(np.array([TOPK])), False)
    p = op.reshape(op.divide(top.output(0), op.reduce_sum(top.output(0), op.constant(np.array([-1])), True)),
                   op.constant(np.array([TOPK, 1, 1])), False)

    def pick(n_in, n_out):  # gather the compressed bytes first, decompress only what was picked; stored [E, in, out]
        if bits == 16:
            return op.gather(op.constant(rng.standard_normal((N_EXP, n_in, n_out), dtype=np.float32).astype(F16)), idx, op.constant(0))
        w = op.gather(op.constant(rng.integers(-127, 127, (N_EXP, n_in, n_out), dtype=np.int8)), idx, op.constant(0))
        s = op.gather(op.constant(np.full((N_EXP, 1, n_out), 2e-4, F16)), idx, op.constant(0))
        return op.multiply(op.convert(w, "f16"), s)

    h = op.multiply(silu(op.matmul(x, pick(D, ROUTED), False, False)), op.matmul(x, pick(D, ROUTED), False, False))
    out = op.matmul(h, pick(ROUTED, D), False, False)                  # [4, 1, D]
    return op.reduce_sum(op.multiply(out, p), op.constant(np.array([0])), True)


def build(kind, layers, attn_bits, ffn_bits, expert_bits, head_bits):
    x0 = op.parameter([1, 1, D], ov.Type.f16, name="x")
    params, results, x = [x0], [], x0
    for i in range(layers):
        w = GLOBAL_WIN if i in GLOBAL_LAYERS else WIN
        kc = op.parameter([1, KVH, HD, w], ov.Type.f16, name=f"k{i}")  # keys kept transposed: no per-step permute
        vc = op.parameter([1, KVH, w, HD], ov.Type.f16, name=f"v{i}")
        params += [kc, vc]
        h = rms(x)
        shp = lambda n: op.constant(np.array([1, KVH, n, HD]))
        q = op.reshape(fc(h, D, KVH * QPK * HD, attn_bits), shp(QPK), False)  # 2 queries per KV head: GQA without repeating KV
        k, v = (op.reshape(fc(h, D, KVH * HD, attn_bits), shp(1), False) for _ in range(2))
        att = op.concat([op.matmul(q, kc, False, False), op.reduce_sum(op.multiply(q, k), op.constant(np.array([-1])), True)], -1)
        att = op.softmax(op.multiply(att, op.constant(F16(HD ** -0.5))), -1)
        cut = op.variadic_split(att, op.constant(np.int64(-1)), op.constant(np.array([w, 1])))
        o = op.add(op.matmul(cut.output(0), vc, False, False), op.multiply(cut.output(1), v))
        o = op.reshape(o, op.constant(np.array([1, 1, KVH * QPK * HD])), False)
        x = op.add(x, fc(o, KVH * QPK * HD, D, attn_bits))
        h = rms(x)
        if kind == "dense" or i < 2:
            y = swiglu(h, FFN, ffn_bits)
        else:
            y = op.add(swiglu(h, SHARED, ffn_bits), routed(h, expert_bits))
        x = op.add(x, y)
        results += [op.result(k), op.result(v)]
    logits = fc(rms(x), D, VOCAB, head_bits)
    results += [op.result(logits), op.result(x)]                          # argmax of 40k logits on the host: cheaper than TopK on the iGPU
    return ov.Model(results, params, f"talker_{kind}")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--kind", choices=["dense", "moe"], required=True)
    a.add_argument("--device", default="GPU")
    a.add_argument("--layers", type=int, default=28)
    a.add_argument("--attn-bits", type=int, default=4)
    a.add_argument("--ffn-bits", type=int, default=4)
    a.add_argument("--expert-bits", type=int, default=8, choices=[8, 16], help="routed experts; 4-bit gather is not expressible per element")
    a.add_argument("--head-bits", type=int, default=8)
    a.add_argument("--threads", type=int, default=0, help="CPU only; 0 = default")
    a.add_argument("--steps", type=int, default=150)
    a.add_argument("--warmup", type=int, default=20)
    a.add_argument("--profile", action="store_true")
    args = a.parse_args()

    core = ov.Core()
    model = build(args.kind, args.layers, args.attn_bits, args.ffn_bits, args.expert_bits, args.head_bits)
    cfg = {"PERFORMANCE_HINT": "LATENCY", "INFERENCE_PRECISION_HINT": "f16" if args.device == "GPU" else "f32"}
    if args.device == "CPU" and args.threads:
        cfg["INFERENCE_NUM_THREADS"] = args.threads
    if args.profile:
        cfg["PERF_COUNT"] = True
    t0 = time.perf_counter()
    cm = core.compile_model(model, args.device, cfg)
    compile_s = time.perf_counter() - t0
    req = cm.create_infer_request()
    ctx = core.get_default_context("GPU") if args.device == "GPU" else None
    for port in cm.inputs:
        # USM host memory on the iGPU: the cache is read in place instead of being copied every step.
        t = ctx.create_host_tensor(port.get_element_type(), port.get_shape()) if ctx else ov.Tensor(port.get_element_type(), port.get_shape())
        t.data[...] = rng.standard_normal(t.data.shape, dtype=np.float32).astype(t.data.dtype) * t.data.dtype.type(0.1)
        req.set_tensor(port, t)
    if ctx:
        for port in cm.outputs:
            req.set_tensor(port, ctx.create_host_tensor(port.get_element_type(), port.get_shape()))
    ms = []
    for i in range(args.warmup + args.steps):
        t0 = time.perf_counter()
        req.infer()
        ms.append((time.perf_counter() - t0) * 1e3)
    ms = np.array(ms[args.warmup:])
    out = dict(vars(args), step_ms_p50=round(float(np.median(ms)), 2), step_ms_p95=round(float(np.percentile(ms, 95)), 2),
               step_ms_min=round(float(ms.min()), 2), compile_s=round(compile_s, 1))
    if args.profile:
        agg = {}
        for n in req.get_profiling_info():
            agg[n.node_type] = agg.get(n.node_type, 0) + n.real_time.total_seconds() * 1e3
        out["kernel_ms"] = round(sum(agg.values()), 2)                 # device time of the last step, without host overhead
        out["profile_ms"] = {k: round(v, 2) for k, v in sorted(agg.items(), key=lambda kv: -kv[1])[:10]}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
