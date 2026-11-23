import json
import math

import pytest
import torch

from formant.metrics import LANGS, Metrics, jsonl_sink


def test_losses_split_by_codebook_and_language_with_mask(tmp_path):
    out = []
    m = Metrics(codebooks=2, code_vocab=4, every=1, sinks=[lambda s, d: out.append(d), jsonl_sink(tmp_path / "x.jsonl")], identity={"seed": 1})
    loss = torch.tensor([[[1., 3.], [100., 100.]], [[2., 4.], [2., 4.]]])          # frame 1 of row 0 is padding
    m.audio(loss, torch.tensor([0, 2]), mask=torch.tensor([[1, 0], [1, 1]]))
    m.monologue(torch.tensor(6.), torch.tensor(3))
    m.log(lr=1e-3, grad_norm=.5)
    d = m.step(1)
    assert out[0] == {"run/seed": 1}
    assert d["loss/codebook_0"] == pytest.approx(5 / 3) and d["loss/codebook_1"] == pytest.approx(11 / 3)
    assert d["loss/lang_hi"] == pytest.approx(2) and d["loss/lang_bn"] == pytest.approx(3)
    assert "loss/lang_en" not in d and d["loss/text"] == 2 and d["opt/lr"] == 1e-3
    assert sum(v for k, v in d.items() if k.startswith("data/share_")) == pytest.approx(1)
    assert len((tmp_path / "x.jsonl").read_text().splitlines()) == 2
    json.dumps(d)


def test_reports_only_every_n_and_resets():
    m = Metrics(codebooks=1, code_vocab=4, every=3)
    for i in range(3):
        m.audio(torch.full((1, 2, 1), float(i)), torch.tensor([1]))
        r = m.step(i)
    assert r["loss/codebook_0"] == 1 and m.steps == 0
    m.audio(torch.full((1, 2, 1), 9.), torch.tensor([1]))
    assert m.step(9) is None


def test_code_entropy_spots_collapse():
    m = Metrics(codebooks=2, code_vocab=8, every=1)
    pred = torch.stack([torch.arange(8)[None], torch.zeros(1, 8, dtype=torch.long)], -1)
    m.audio(torch.zeros(1, 8, 2), torch.tensor([0]), pred=pred)
    d = m.step(0)
    assert d["codes/entropy_0"] == pytest.approx(1) and d["codes/entropy_1"] == pytest.approx(0, abs=1e-6)


def test_expert_use_per_language():
    m = Metrics(codebooks=1, code_vocab=4, experts=4, every=1)
    chosen = torch.tensor([[[0, 1]] * 6, [[2, 1]] * 6])                              # Hindi uses 0,1; Tamil uses 2,1; 3 is dead
    m.audio(torch.zeros(2, 6, 1), torch.tensor([0, 4]))
    m.routing(chosen, torch.full((2, 6, 4), .25), torch.tensor([0, 4]))
    d = m.step(0)
    assert d["moe/use_hi"] == [.5, .5, 0, 0] and d["moe/use_ta"] == [0, .5, .5, 0]
    assert d["moe/dead_experts"] == 1 and d["moe/max_over_mean"] == pytest.approx(2)
    assert d["moe/router_entropy"] == pytest.approx(1)
    assert not math.isnan(d["speed/frames_per_s"]) and LANGS[4] == "ta"
