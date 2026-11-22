"""The talker: a causal transformer over 80 ms frames with user and own audio streams, an inner-monologue text stream,
a depth decoder over codebooks, and an optional Mixture-of-Experts feed-forward (TR1; shapes from 03-architecture).

Frame t sees the embeddings of frame t-1's own codes and text, and of frame t's user codes. It predicts frame t's
text token and own codes. Codebooks 1..K-1 lag codebook 0 by `delay` frames; apply `shift_codes` to the targets.
"""
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class Config:
    d: int = 256
    layers: int = 4
    heads: int = 8
    kv_heads: int = 4
    ffn: int = 768
    codebooks: int = 8
    code_vocab: int = 2048
    text_vocab: int = 4096
    delay: int = 1
    window: int = 0              # 0 = full context, else a sliding window of this many frames
    depth_d: int = 128
    depth_layers: int = 2
    experts: int = 0             # 0 = dense
    top_k: int = 4
    shared: int = 0              # width of the shared expert
    routed: int = 0              # width of one routed expert
    first_dense: int = 1
    balance_lr: float = 1e-3     # DeepSeek-V3 style bias update; no auxiliary loss
    z_loss: float = 1e-3

    def __post_init__(self):
        assert self.d % self.heads == 0 and self.heads % self.kv_heads == 0
        assert (self.d // self.heads) % 2 == 0, "rotary embeddings need an even head size"
        if self.experts:
            assert 0 < self.top_k <= self.experts and self.routed > 0


def rms_norm(x, scale):
    return F.rms_norm(x, (x.shape[-1],), scale, 1e-6)


class SwiGLU(nn.Module):
    def __init__(self, d, w):
        super().__init__()
        self.up, self.gate, self.down = nn.Linear(d, w, False), nn.Linear(d, w, False), nn.Linear(w, d, False)

    def forward(self, x):
        return self.down(F.silu(self.gate(x)) * self.up(x))


class MoE(nn.Module):
    """One shared expert plus top-k of E routed experts. Dropless sort-and-loop dispatch; router in fp32.
    `bias` steers load (added to the scores for selection only); `rebalance()` moves it once per global batch."""

    def __init__(self, c):
        super().__init__()
        self.c = c
        self.shared = SwiGLU(c.d, c.shared) if c.shared else None
        self.experts = nn.ModuleList(SwiGLU(c.d, c.routed) for _ in range(c.experts))
        self.router = nn.Linear(c.d, c.experts, False)
        self.register_buffer("bias", torch.zeros(c.experts))
        self.register_buffer("load", torch.zeros(c.experts))            # tokens per expert since the last rebalance
        self.z = torch.zeros(())
        self.last = None

    def forward(self, x):
        shape, x = x.shape, x.reshape(-1, x.shape[-1])
        with torch.autocast(x.device.type, enabled=False):
            logits = F.linear(x.float(), self.router.weight.float())
            scores = logits.sigmoid()
            top = (scores + self.bias).topk(self.c.top_k, -1).indices
            w = scores.gather(1, top)
            w = w / w.sum(-1, keepdim=True).clamp_min(1e-6)
            self.z = logits.square().mean() * self.c.z_loss
        out = self.shared(x) if self.shared else torch.zeros_like(x)
        rows, slot = torch.arange(len(x), device=x.device).repeat_interleave(self.c.top_k), top.flatten()
        order = slot.argsort(stable=True)
        counts = torch.bincount(slot, minlength=self.c.experts)
        for e, idx in enumerate(order.split(counts.tolist())):
            if len(idx):
                r = rows[idx]
                y = self.experts[e](x[r]) * w.flatten()[idx, None].to(x.dtype)
                out = out.index_add(0, r, y.to(out.dtype))
        if self.training:
            self.load += counts
            self.last = (top.detach().view(*shape[:-1], -1), scores.detach().view(*shape[:-1], -1))
        return out.view(shape)

    @torch.no_grad()
    def rebalance(self):
        """Call once per global batch. With DDP, all-reduce `load` first: balancing must see the whole global batch."""
        if self.load.sum() > 0:
            self.bias += self.c.balance_lr * torch.sign(self.load.mean() - self.load)
            self.load.zero_()


class Block(nn.Module):
    def __init__(self, c, i, moe):
        super().__init__()
        self.c, self.hd = c, c.d // c.heads
        self.q, self.k = nn.Linear(c.d, c.d, False), nn.Linear(c.d, c.kv_heads * self.hd, False)
        self.v, self.o = nn.Linear(c.d, c.kv_heads * self.hd, False), nn.Linear(c.d, c.d, False)
        self.n1, self.n2 = nn.Parameter(torch.ones(c.d)), nn.Parameter(torch.ones(c.d))
        self.ffn = MoE(c) if moe else SwiGLU(c.d, c.ffn)

    def forward(self, x, rope, mask):
        B, T, _ = x.shape
        h = rms_norm(x, self.n1)
        q = self.q(h).view(B, T, -1, self.hd).transpose(1, 2)
        k, v = (f(h).view(B, T, -1, self.hd).transpose(1, 2).repeat_interleave(self.c.heads // self.c.kv_heads, 1) for f in (self.k, self.v))
        q, k = rotate(q, rope), rotate(k, rope)
        a = F.scaled_dot_product_attention(q, k, v, attn_mask=mask)
        x = x + self.o(a.transpose(1, 2).reshape(B, T, -1))
        return x + self.ffn(rms_norm(x, self.n2))


def make_rope(T, hd, device):
    f = 1.0 / 1e4 ** (torch.arange(0, hd, 2, device=device) / hd)
    a = torch.arange(T, device=device)[:, None] * f
    return torch.cos(a), torch.sin(a)


def rotate(x, rope):
    cos, sin = (r.to(x.dtype) for r in rope)
    a, b = x[..., ::2], x[..., 1::2]
    return torch.stack([a * cos - b * sin, a * sin + b * cos], -1).flatten(-2)


def attention_mask(doc, window=0):
    """doc: [B, T] document id per frame. True = may attend: causal, same document, inside the window."""
    T = doc.shape[1]
    i = torch.arange(T, device=doc.device)
    dist = i[:, None] - i[None]
    ok = (dist >= 0) & ((dist < window) if window else True)
    return (ok[None] & (doc[:, :, None] == doc[:, None, :]))[:, None]


def shift_codes(codes, delay, pad):
    """[B, T, K]: delay codebooks 1..K-1 by `delay` frames. Returns (shifted, valid)."""
    if not delay:
        return codes, torch.ones_like(codes, dtype=torch.bool)
    out, valid = codes.clone(), torch.ones_like(codes, dtype=torch.bool)
    out[:, delay:, 1:] = codes[:, :-delay, 1:]
    out[:, :delay, 1:] = pad
    valid[:, :delay, 1:] = False
    return out, valid


class Depth(nn.Module):
    """Predicts the codebooks of one frame in order, given the frame state. A small causal transformer over K steps."""

    def __init__(self, c):
        super().__init__()
        self.c = c
        dc = Config(d=c.depth_d, layers=c.depth_layers, heads=4, kv_heads=4, ffn=3 * c.depth_d)
        self.inp = nn.Linear(c.d, c.depth_d * c.codebooks)
        self.emb = nn.ModuleList(nn.Embedding(c.code_vocab + 1, c.depth_d) for _ in range(c.codebooks - 1))
        self.blocks = nn.ModuleList(Block(dc, i, False) for i in range(c.depth_layers))
        self.heads = nn.ModuleList(nn.Linear(c.depth_d, c.code_vocab, False) for _ in range(c.codebooks))
        self.norm = nn.Parameter(torch.ones(c.depth_d))

    def forward(self, h, codes):
        B, T, K = codes.shape
        x = self.inp(h).view(B * T, K, -1)
        prev = torch.stack([e(codes[..., k]) for k, e in enumerate(self.emb)], 2).view(B * T, K - 1, -1)
        x = x + F.pad(prev, (0, 0, 1, 0))                                # step k sees codes 0..k-1
        mask = torch.ones(K, K, dtype=torch.bool, device=x.device).tril()[None, None]
        rope = make_rope(K, self.c.depth_d // 4, x.device)
        for b in self.blocks:
            x = b(x, rope, mask)
        x = rms_norm(x, self.norm).view(B, T, K, -1)
        return torch.stack([hd(x[:, :, k]) for k, hd in enumerate(self.heads)], 2)


class Talker(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.c = c
        pad = c.code_vocab                                               # one extra row = padding / silence of the other stream
        self.own = nn.ModuleList(nn.Embedding(c.code_vocab + 1, c.d) for _ in range(c.codebooks))
        self.user = nn.ModuleList(nn.Embedding(c.code_vocab + 1, c.d) for _ in range(c.codebooks))
        self.text = nn.Embedding(c.text_vocab, c.d)
        self.blocks = nn.ModuleList(Block(c, i, bool(c.experts) and i >= c.first_dense) for i in range(c.layers))
        self.norm = nn.Parameter(torch.ones(c.d))
        self.depth, self.pad = Depth(c), pad
        self.apply(lambda m: nn.init.normal_(m.weight, std=0.02) if isinstance(m, (nn.Linear, nn.Embedding)) else None)

    def moes(self):
        return [b.ffn for b in self.blocks if isinstance(b.ffn, MoE)]

    def forward(self, own, user, text, doc):
        """own, user: [B, T, K] codes (pad = code_vocab). text: [B, T]. doc: [B, T]. `own` must already be delay-shifted."""
        first = F.pad(doc[:, 1:] != doc[:, :-1], (1, 0), value=True)      # no history crosses a document boundary
        prev_own = own.roll(1, 1).masked_fill(first[..., None], self.pad)
        prev_text = text.roll(1, 1).masked_fill(first, 0)
        x = self.text(prev_text)
        for k in range(self.c.codebooks):
            x = x + self.own[k](prev_own[..., k]) + self.user[k](user[..., k])
        mask, rope = attention_mask(doc, self.c.window), make_rope(own.shape[1], self.c.d // self.c.heads, own.device)
        for b in self.blocks:
            x = b(x, rope, mask)
        x = rms_norm(x, self.norm)
        return F.linear(x, self.text.weight), self.depth(x, own)

    def loss(self, own, user, text, doc):
        """Returns (total, per-token audio loss [B, T, K], valid mask [B, T, K], text loss sum, text count, predicted codes)."""
        shifted, valid = shift_codes(own, self.c.delay, self.pad)
        tl, al = self(shifted, user, text, doc)
        valid = valid & (shifted < self.c.code_vocab)
        audio = F.cross_entropy(al.float().flatten(0, 2), shifted.clamp_max(self.c.code_vocab - 1).flatten(), reduction="none").view_as(shifted)
        audio = audio * valid
        has = text > 0                                                   # 0 = no text in this frame
        tsum = F.cross_entropy(tl.float()[has], text[has], reduction="sum") if has.any() else tl.sum() * 0
        total = audio.sum() / valid.sum().clamp_min(1) + tsum / has.sum().clamp_min(1)
        for m in self.moes():
            total = total + m.z
        return total, audio.detach(), valid, tsum.detach(), has.sum(), al.argmax(-1)


def upcycle(ffn, c, noise=0.01):
    """Build an MoE from a dense SwiGLU: the first `shared` hidden units become the shared expert; the rest is cut into
    slices of `routed` units, and the experts cycle through copies of those slices with a little noise."""
    width = ffn.up.out_features
    rest = width - c.shared
    assert rest > 0 and rest % c.routed == 0, "the non-shared width must split into whole experts"
    slices = rest // c.routed
    assert c.experts % slices == 0 and c.top_k % slices == 0, "top_k must cover every slice for the sum to match the dense layer"
    m = MoE(c)

    def copy(dst, lo, hi, scale=1.0, eps=0.0):
        for name in ("up", "gate"):
            w = getattr(ffn, name).weight[lo:hi]
            getattr(dst, name).weight.data.copy_(w + eps * w.std() * torch.randn_like(w))
        w = ffn.down.weight[:, lo:hi]
        dst.down.weight.data.copy_(scale * (w + eps * w.std() * torch.randn_like(w)))
    if m.shared:
        copy(m.shared, 0, c.shared)
    for e in range(c.experts):
        s = e % slices
        # Router weights are normalised over top_k, so scale each slice back up to its dense contribution.
        copy(m.experts[e], c.shared + s * c.routed, c.shared + (s + 1) * c.routed, slices, noise)
    return m
