"""TR1 smoke run: train the talker on tokens, log the MO1 metric set, checkpoint with IN1's runner, resume exactly.

Needs src/formant/{ckpt,metrics}.py from the IN1 and MO1 branches. With no --tokens it uses synthetic tokens with a
per-language rule to learn, so every check except speech quality can run before any data exists.

    python 04-training/scripts/smoke.py --out runs/smoke-dense --steps 300
    python 04-training/scripts/smoke.py --out runs/smoke-moe   --steps 300 --moe
    python 04-training/scripts/smoke.py --out runs/smoke-moe   --steps 300 --moe --die-at 137   # then rerun without it
"""
import argparse
import json
import math
import os
import pathlib
import random
import subprocess
import time

import torch

from formant.ckpt import Checkpointer, Clock
from formant.metrics import LANGS, Metrics, jsonl_sink
from formant.sampler import V01_HOURS, Sampler, mixture
from formant.talker import Config, Talker

SIZES = {
    "tiny": dict(d=96, layers=3, heads=4, kv_heads=2, ffn=288, codebooks=4, code_vocab=64, text_vocab=128, depth_d=48, depth_layers=1),
    "50m": dict(d=512, layers=8, heads=8, kv_heads=4, ffn=1536, codebooks=8, code_vocab=2048, text_vocab=40000, depth_d=256, depth_layers=2),
}


def synthetic(c, item, T, seed=7):
    """A clip whose codes follow a rule of its language: code 0 maps from code 0 of the last frame, code k from code k-1."""
    lang, n = item
    r, rule = random.Random(f"{seed}/{lang}/{n}"), random.Random(lang)
    V = c.code_vocab
    maps = [rule.sample(range(V), V) for _ in range(c.codebooks)]
    x, rows = r.randrange(V), []
    for _ in range(T):
        x = maps[0][x] if r.random() < 0.9 else r.randrange(V)
        row = [x]
        for k in range(1, c.codebooks):
            row.append(maps[k][row[-1]] if r.random() < 0.95 else r.randrange(V))
        rows.append(row)
    codes = torch.tensor(rows)
    return codes, torch.where(torch.arange(T) % 3 == 0, codes[:, 0] % (c.text_vocab - 1) + 1, 0)


def wsd(step, total, peak, warmup=0.05, decay=0.15, final=0.05):
    """Warmup, stable, linear decay. The decay is also DATA_PLAN's quality anneal."""
    w, d = max(1, int(total * warmup)), max(1, int(total * decay))
    if step < w:
        return peak * (step + 1) / w
    return peak if step < total - d else peak * max(final, (total - step) / d)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", required=True)
    a.add_argument("--steps", type=int, default=300)
    a.add_argument("--size", choices=SIZES, default="tiny")
    a.add_argument("--moe", action="store_true")
    a.add_argument("--micro", type=int, default=8, help="micro-batches per global batch, one language each")
    a.add_argument("--batch", type=int, default=2)
    a.add_argument("--frames", type=int, default=64)
    a.add_argument("--lr", type=float, default=3e-3)
    a.add_argument("--save-every", type=int, default=50)
    a.add_argument("--log-every", type=int, default=25)
    a.add_argument("--die-at", type=int, default=0, help="kill this process hard right after this step (resume test)")
    a.add_argument("--seed", type=int, default=0)
    args = a.parse_args()

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(args.seed)
    torch.set_num_threads(2)
    kw = dict(SIZES[args.size])
    if args.moe:
        w = kw["ffn"]
        kw.update(experts=16, top_k=2, shared=w // 2, routed=w // 4, first_dense=1)
    c = Config(**kw)
    model = Talker(c).to(dev)
    opt = torch.optim.AdamW(model.parameters(), args.lr, betas=(0.9, 0.95), weight_decay=0.01)
    scaler = torch.amp.GradScaler(dev, enabled=dev == "cuda")
    items = {k: [(k, i) for i in range(40)] for k in V01_HOURS}
    sampler = Sampler(items, mixture(V01_HOURS), args.micro, args.seed)
    out = pathlib.Path(args.out)
    ck = Checkpointer(out / "ckpt")
    step, _ = ck.load_latest(model=model, opt=opt, scaler=scaler, sampler=sampler)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    met = Metrics(c.codebooks, c.code_vocab, c.experts, dev, args.log_every, [jsonl_sink(out / "metrics.jsonl")],
                  {"config": kw, "commit": commit, "seed": args.seed, "params": sum(p.numel() for p in model.parameters()), "resumed_at": step})
    print(f"{sum(p.numel() for p in model.parameters()) / 1e6:.2f}M parameters, {dev}, starting at step {step}")
    clock, cache, curve = Clock(), {}, open(out / "curve.jsonl", "a")
    model.train()
    while step < args.steps and not clock.over():
        lr = wsd(step, args.steps, args.lr)
        for g in opt.param_groups:
            g["lr"] = lr
        opt.zero_grad(set_to_none=True)
        tot = 0.0
        for j in range(args.micro):
            t0 = time.perf_counter()
            lang, rows = None, []
            for _ in range(args.batch):                                   # one language per micro-batch
                lang_, item = sampler.next() if lang is None else (lang, sampler.items[lang][(rows[-1][1] + 7) % len(sampler.items[lang])])
                lang = lang_
                rows.append(item)
            clips = [cache.setdefault(r, synthetic(c, r, args.frames)) for r in rows]
            own = torch.stack([x[0] for x in clips]).to(dev)
            text = torch.stack([x[1] for x in clips]).to(dev)
            user = torch.full_like(own, c.code_vocab)                      # silent user stream: monologue pre-training
            doc = torch.zeros(own.shape[:2], dtype=torch.long, device=dev)
            met.wait += time.perf_counter() - t0
            with torch.autocast(dev, torch.float16, enabled=dev == "cuda"):
                loss, al, valid, ts, tn, pred = model.loss(own, user, text, doc)
            if not math.isfinite(loss.item()):
                raise SystemExit(f"loss is {loss.item()} at step {step}")
            scaler.scale(loss / args.micro).backward()
            li = torch.full((len(rows),), LANGS.index(lang), device=dev)
            met.audio(al, li, valid.all(-1), pred)
            met.monologue(ts, tn)
            if c.experts and j == 0:
                for m in model.moes():
                    met.routing(*m.last, li)
            tot += loss.item() / args.micro
        scaler.unscale_(opt)
        gn = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt)
        scaler.update()
        for m in model.moes():
            m.rebalance()
        step += 1
        met.log(lr=lr, grad_norm=float(gn), loss_scale=scaler.get_scale(), **{f"epoch/{k}": v for k, v in sampler.epochs().items()})
        curve.write(json.dumps([step, tot]) + "\n")
        curve.flush()
        if d := met.step(step):
            extra = f" load {d['moe/max_over_mean']:.2f} dead {d['moe/dead_experts']}" if c.experts else ""
            print(f"step {step} loss {tot:.3f} cb0 {d['loss/codebook_0']:.3f} cb{c.codebooks - 1} {d[f'loss/codebook_{c.codebooks - 1}']:.3f}"
                  f" text {d['loss/text']:.3f} {d['speed/frames_per_s']:.0f} frames/s{extra}", flush=True)
        if step % args.save_every == 0 or clock.due() or step == args.steps:
            ck.save(step, model=model, opt=opt, scaler=scaler, sampler=sampler)
        if step == args.die_at:
            os._exit(9)


if __name__ == "__main__":
    main()
