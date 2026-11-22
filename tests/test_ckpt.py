"""Kill a real training process mid-run and check that resuming reproduces the uninterrupted run exactly."""
import json
import pathlib
import subprocess
import sys
import time

import pytest
import torch

from formant.ckpt import Checkpointer, Clock

SRC = str(pathlib.Path(__file__).resolve().parents[1] / "src")
RUN = """
import sys, json, time, torch
sys.path.insert(0, SRC)
from formant.ckpt import Checkpointer
root, log, total, delay = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
torch.manual_seed(0); torch.set_num_threads(1)
net = torch.nn.Sequential(torch.nn.Linear(16, 32), torch.nn.Dropout(.2), torch.nn.Linear(32, 1))
opt = torch.optim.AdamW(net.parameters(), 1e-2)
ck = Checkpointer(root)
step, plain = ck.load_latest(net=net, opt=opt)
pos = plain.get('pos', 0)
while step < total:
    x = torch.randn(8, 16); loss = (net(x) - x.sum(1, keepdim=True)).square().mean()
    opt.zero_grad(); loss.backward(); opt.step(); step += 1; pos += 8
    with open(log, 'a') as f: f.write(json.dumps([step, pos, loss.item()]) + chr(10))
    if step % 5 == 0: ck.save(step, net=net, opt=opt, pos=pos)
    time.sleep(delay)
"""


def curve(log):  # a step redone after the resume overwrites the first try
    return {s: (p, v) for s, p, v in map(json.loads, pathlib.Path(log).read_text().splitlines())}


def test_kill_and_resume_is_exact(tmp_path):
    script = tmp_path / "run.py"
    script.write_text(f"SRC = {SRC!r}\n" + RUN)

    def cmd(name, delay):
        return [sys.executable, str(script), str(tmp_path / name), str(tmp_path / f"{name}.log"), "40", str(delay)]

    subprocess.run(cmd("ref", 0), check=True, timeout=240)
    p = subprocess.Popen(cmd("cut", 0.1))
    log, deadline = tmp_path / "cut.log", time.time() + 200
    while time.time() < deadline and not (log.exists() and len(log.read_text().splitlines()) >= 17):
        time.sleep(0.05)
    p.kill()
    p.wait()
    assert 17 <= max(curve(log)) < 40, "the run finished before it was killed"
    subprocess.run(cmd("cut", 0), check=True, timeout=240)
    assert curve(log) == curve(tmp_path / "ref.log")  # bit-exact on CPU, sampler position included


def test_unreadable_checkpoint_falls_back(tmp_path):
    net, ck = torch.nn.Linear(2, 2), Checkpointer(tmp_path)
    ck.save(1, net=net)
    ck.save(2, net=net)
    ck.path(2).write_bytes(ck.path(2).read_bytes()[:50])
    assert ck.load_latest(net=net)[0] == 1


def test_rotation_missing_state_and_upload_errors(tmp_path):
    net, seen = torch.nn.Linear(2, 2), []

    def up(p):
        assert p.exists(), "rotated away before it was uploaded"
        seen.append(p.name)
        if len(seen) == 2:
            raise OSError("network")

    ck = Checkpointer(tmp_path, keep=2, upload=up)
    for s in range(1, 6):
        ck.save(s, net=net)
    ck.wait()
    assert ck.steps() == [4, 5] and len(seen) == 5 and len(ck.errors) == 1
    with pytest.raises(KeyError):
        ck.load_latest(net=net, opt=torch.optim.SGD(net.parameters(), .1))


def test_clock():
    t = [0.0]
    c = Clock(every_min=30, stop_after_min=690, now=lambda: t[0])
    t[0] = 29 * 60
    assert not c.due()
    t[0] = 30 * 60
    assert c.due() and not c.due()
    t[0] = 690 * 60
    assert c.over()
