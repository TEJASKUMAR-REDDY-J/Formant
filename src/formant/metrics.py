"""The one metric set every run logs (MO1). Names are fixed in 11-monitoring/metric-set.md; MO2's alarms read them.

Statistics accumulate as tensors on the training device and are read back once per `every` steps, so logging
never forces a GPU sync on ordinary steps.
"""
import json
import math
import pathlib
import time

import torch

LANGS = ["hi", "en", "bn", "mr", "ta", "te", "hi-en"]


class Metrics:
    def __init__(self, codebooks=8, code_vocab=2048, experts=0, device="cpu", every=50, sinks=(), identity=None):
        """experts: routed experts per layer (0 = dense). sinks: callables(step, dict). identity: config, commit, hashes, seed."""
        self.K, self.V, self.E, self.dev, self.every, self.sinks = codebooks, code_vocab, experts, device, every, list(sinks)
        self._reset()
        for s in self.sinks:
            s(0, {f"run/{k}": v for k, v in (identity or {}).items()})

    def _reset(self):
        z = lambda *s: torch.zeros(*s, device=self.dev, dtype=torch.float64 if self.dev == "cpu" else torch.float32)
        L = len(LANGS)
        self.cb_sum, self.cb_n, self.lang_sum, self.lang_n, self.text = z(self.K), z(self.K), z(L), z(L), z(2)
        self.pred = z(self.K, self.V)
        self.use = z(L, self.E) if self.E else None
        self.ent = z(2)
        self.plain, self.frames, self.steps, self.t0, self.wait = {}, 0, 0, time.perf_counter(), 0.0

    @torch.no_grad()
    def audio(self, loss, lang, mask=None, pred=None):
        """loss: [B, T, K] per-token loss. lang: [B] index into LANGS. mask: [B, T] 1 = counts. pred: [B, T, K] argmax codes."""
        B, T, K = loss.shape
        m = torch.ones(B, T, device=loss.device) if mask is None else mask.float()
        w = m[..., None]
        loss = loss.float() * w
        self.cb_sum += loss.sum((0, 1))
        self.cb_n += m.sum()
        self.lang_sum.index_add_(0, lang, loss.sum((1, 2)).to(self.lang_sum.dtype))
        self.lang_n.index_add_(0, lang, (m.sum(1) * K).to(self.lang_n.dtype))
        self.frames += B * T
        if pred is not None:
            for k in range(K):
                self.pred[k].index_add_(0, pred[..., k][m.bool()].flatten(), torch.ones(int(m.sum()), device=loss.device, dtype=self.pred.dtype))

    @torch.no_grad()
    def monologue(self, loss_sum, count):
        self.text += torch.stack([loss_sum.float(), count.float()]).to(self.text.dtype)

    @torch.no_grad()
    def routing(self, chosen, probs, lang):
        """chosen: [B, T, k] expert ids of one layer. probs: [B, T, E] router scores. lang: [B]. Call on a sampled micro-batch."""
        flat = chosen.flatten(1)
        for b in range(len(lang)):
            self.use[lang[b]].index_add_(0, flat[b], torch.ones(flat.shape[1], device=flat.device, dtype=self.use.dtype))
        p = probs.float() / probs.float().sum(-1, keepdim=True).clamp_min(1e-9)
        h = -(p * p.clamp_min(1e-9).log()).sum(-1)
        self.ent += torch.stack([h.sum(), torch.tensor(float(h.numel()), device=h.device)]).to(self.ent.dtype)

    def log(self, **values):
        """Plain numbers: lr, grad_norm, loss_scale, overflows, shard, epoch/hi, ..."""
        self.plain.update(values)

    def step(self, step):
        self.steps += 1
        if self.steps < self.every:
            return None
        dt = time.perf_counter() - self.t0
        out = {f"opt/{k}" if "/" not in k else k: v for k, v in self.plain.items()}
        cb, n = self.cb_sum.tolist(), self.cb_n.tolist()
        seen = [k for k in range(self.K) if n[k]]
        out.update({f"loss/codebook_{k}": cb[k] / n[k] for k in seen})
        if seen:
            out["loss/audio"] = sum(cb[k] for k in seen) / sum(n[k] for k in seen)
        ls, ln = self.lang_sum.tolist(), self.lang_n.tolist()
        out.update({f"loss/lang_{g}": s / c for g, s, c in zip(LANGS, ls, ln) if c})
        out.update({f"data/share_{g}": c / sum(ln) for g, c in zip(LANGS, ln) if c})
        t, tn = self.text.tolist()
        if tn:
            out["loss/text"] = t / tn
        if self.pred.sum() > 0:
            p = self.pred / self.pred.sum(1, keepdim=True).clamp_min(1)
            ent = (-(p * p.clamp_min(1e-12).log()).sum(1) / math.log(self.V)).tolist()     # 1 = uniform, 0 = one code
            out.update({f"codes/entropy_{k}": e for k, e in enumerate(ent)})
        if self.E and self.use.sum() > 0:
            load = self.use.sum(0)
            out["moe/max_over_mean"] = (load.max() / load.mean()).item()
            out["moe/dead_experts"] = int((load < 0.1 * load.mean()).sum())
            h, hn = self.ent.tolist()
            out["moe/router_entropy"] = h / hn / math.log(self.E)
            for g, row in zip(LANGS, self.use):
                if row.sum() > 0:
                    out[f"moe/use_{g}"] = (row / row.sum()).tolist()
        out["speed/frames_per_s"], out["speed/step_s"] = self.frames / dt, dt / self.steps
        out["speed/data_wait_s"] = self.wait / self.steps
        if str(self.dev).startswith("cuda"):
            out["memory/peak_gb"] = torch.cuda.max_memory_allocated(self.dev) / 1e9
        for s in self.sinks:
            s(step, out)
        self._reset()
        return out


def jsonl_sink(path):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    def sink(step, d):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"step": step, "time": time.time(), **d}) + "\n")
    return sink


def trackio_sink(project, name, space_id=None):
    """Optional dashboard; pip install trackio. Lists (expert-use histograms) stay in the JSONL file."""
    import trackio
    trackio.init(project=project, name=name, space_id=space_id)
    return lambda step, d: trackio.log({k: v for k, v in d.items() if not isinstance(v, (list, dict))}, step=step)
