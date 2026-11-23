import itertools

import pytest
import torch

from formant.sampler import V01_HOURS, Sampler, mixture
from formant.talker import Config, MoE, SwiGLU, Talker, attention_mask, shift_codes, upcycle

SMALL = dict(d=32, layers=2, heads=4, kv_heads=2, ffn=64, codebooks=3, code_vocab=16, text_vocab=32, depth_d=16, depth_layers=1)
MOE = dict(experts=8, top_k=4, shared=32, routed=8, first_dense=1)


def batch(c, B=2, T=10, seed=0):
    g = torch.Generator().manual_seed(seed)
    r = lambda hi, *s: torch.randint(0, hi, s, generator=g)
    return r(c.code_vocab, B, T, c.codebooks), r(c.code_vocab, B, T, c.codebooks), r(c.text_vocab, B, T), torch.zeros(B, T, dtype=torch.long)


@pytest.mark.parametrize("extra", [{}, MOE])
def test_no_leak_from_the_future(extra):
    """Frame t's outputs must not change when own codes or text at t, or anything later, change. User codes at t are visible."""
    torch.manual_seed(0)
    c = Config(**SMALL, **extra)
    m = Talker(c).eval()
    own, user, text, doc = batch(c)
    t = 5
    tl, al = m(own, user, text, doc)
    own2, user2, text2 = own.clone(), user.clone(), text.clone()
    own2[:, t + 1:] = (own2[:, t + 1:] + 1) % c.code_vocab
    user2[:, t + 1:] = (user2[:, t + 1:] + 1) % c.code_vocab
    text2[:, t:] = (text2[:, t:] + 1) % c.text_vocab
    tl2, al2 = m(own2, user2, text2, doc)
    assert torch.allclose(tl[:, :t + 1], tl2[:, :t + 1], atol=1e-5) and torch.allclose(al[:, :t + 1], al2[:, :t + 1], atol=1e-5)
    own3 = own.clone()
    own3[:, t, 1] = (own3[:, t, 1] + 1) % c.code_vocab                                # codebook 1 of frame t ...
    _, al3 = m(own3, user, text, doc)
    assert torch.allclose(al[:, t, :2], al3[:, t, :2], atol=1e-5)                     # ... is invisible to codebooks 0 and 1
    assert not torch.allclose(al[:, t, 2], al3[:, t, 2], atol=1e-5)                   # ... and visible to codebook 2
    user4 = user.clone()
    user4[:, t] = (user4[:, t] + 1) % c.code_vocab
    assert not torch.allclose(m(own, user4, text, doc)[0][:, t], tl[:, t], atol=1e-5)  # it does hear the user now


def test_documents_do_not_mix():
    torch.manual_seed(0)
    c = Config(**SMALL)
    m = Talker(c).eval()
    own, user, text, doc = batch(c)
    doc[:, 6:] = 1
    a = m(own, user, text, doc)[0][:, 6:]
    own[:, :6], user[:, :6], text[:, :6] = 1, 1, 1
    assert torch.allclose(a, m(own, user, text, doc)[0][:, 6:], atol=1e-5)
    assert attention_mask(torch.zeros(1, 5, dtype=torch.long), 2)[0, 0].sum() == 9


def test_delay_shift():
    x = torch.arange(12).view(1, 4, 3)
    s, v = shift_codes(x, 1, 99)
    assert s[0, :, 0].tolist() == [0, 3, 6, 9] and s[0, :, 1].tolist() == [99, 1, 4, 7] and not v[0, 0, 1:].any() and v[0, 1:].all()


def test_upcycled_moe_equals_the_dense_layer():
    torch.manual_seed(0)
    c = Config(d=16, heads=4, kv_heads=2, experts=8, top_k=4, shared=16, routed=8)
    dense = SwiGLU(16, 48)                                                            # 16 shared + 4 slices of 8
    m = upcycle(dense, c, noise=0.0).eval()
    x = torch.randn(1, 6, 16)
    want = dense(x)
    # Equal router scores and one copy of every slice chosen: exactly the dense output.
    m.router.weight.data.zero_()
    m.bias[:] = torch.tensor([1., 1., 1., 1., 0., 0., 0., 0.])
    assert torch.allclose(m(x), want, atol=1e-5)


def test_moe_dispatch_matches_brute_force_and_balances():
    torch.manual_seed(0)
    c = Config(d=16, heads=4, kv_heads=2, experts=6, top_k=2, shared=0, routed=8, balance_lr=0.05)
    m = MoE(c)
    x = torch.randn(4, 5, 16)
    s = (x @ m.router.weight.T).sigmoid()
    top = s.topk(2, -1).indices
    w = s.gather(-1, top)
    w = w / w.sum(-1, keepdim=True)
    want = torch.stack([torch.stack([sum(w[b, t, j] * m.experts[top[b, t, j]](x[b, t]) for j in range(2)) for t in range(5)]) for b in range(4)])
    assert torch.allclose(m(x), want, atol=1e-5) and m.load.sum() == 40
    x = torch.randn(64, 8, 16) + 2 * torch.randn(16)                                  # a skewed input overloads some experts
    m.load.zero_(); m(x)
    skew = (m.load.max() / m.load.mean()).item()
    for _ in range(60):
        m.rebalance(); m(x)
    assert (m.load.max() / m.load.mean()).item() < 0.7 * skew


def test_gradients_reach_every_part():
    torch.manual_seed(0)
    c = Config(**SMALL, **MOE)
    m = Talker(c).train()
    m.loss(*batch(c, B=8, T=32))[0].backward()
    none = [n for n, p in m.named_parameters() if p.grad is None or not p.grad.abs().sum() > 0]
    assert not [n for n in none if "experts" not in n], none


def test_mixture_reproduces_the_data_plan():
    s = mixture(V01_HOURS)
    assert {k: round(100 * v, 1) for k, v in s.items()} == {"hi": 23.1, "en": 16.4, "bn": 14.2, "mr": 14.2, "ta": 14.2, "te": 14.2, "hi-en": 3.8}
    with pytest.raises(ValueError):
        mixture(V01_HOURS, epochs=5)


def test_sampler_is_stratified_deterministic_and_resumable():
    items = {k: [f"{k}{i}" for i in range(7)] for k in V01_HOURS}
    s = mixture(V01_HOURS)
    a, b = Sampler(items, s), Sampler(items, s)
    seq = [a.next() for _ in range(3200)]
    assert seq[:500] == [b.next() for _ in range(500)]
    for k, share in s.items():
        got = sum(1 for x, _ in seq if x == k)
        assert abs(got - 3200 * share) <= 2, (k, got, 3200 * share)
    c = Sampler(items, s)
    c.load_state_dict(b.state_dict())
    assert [c.next() for _ in range(2700)] == seq[500:]
    one = [v for k, v in itertools.islice((x for x in seq if x[0] == "ta"), 7)]
    assert sorted(one) == sorted(items["ta"])                                         # a full epoch before any repeat
    with pytest.raises(ValueError):
        Sampler(items, s, seed=1).load_state_dict(b.state_dict())
