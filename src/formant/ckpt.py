"""Checkpoint and resume for killed sessions (IN1).

A checkpoint is one file holding everything a run needs to continue exactly: model, optimizer, loss scaler,
sampler position, RNG states and step. Writes are atomic (temp file, then rename), so a kill mid-write leaves
the previous checkpoint intact. The last `keep` are kept. Uploads run in one background thread.
"""
import os
import pathlib
import queue
import random
import re
import threading
import time

import numpy as np
import torch

_NAME = re.compile(r"^step-(\d{9})\.ckpt$")


def rng_state():
    return {"python": random.getstate(), "numpy": np.random.get_state(), "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}


def set_rng_state(s):
    random.setstate(s["python"])
    np.random.set_state(s["numpy"])
    torch.set_rng_state(s["torch"])
    if s["cuda"] and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(s["cuda"])


class Checkpointer:
    def __init__(self, root, keep=3, upload=None):
        """upload: callable(path) run in the background, e.g. a Hub upload. Failures go to .errors, never raised mid-run."""
        self.root, self.keep, self.errors = pathlib.Path(root), keep, []
        self.root.mkdir(parents=True, exist_ok=True)
        self._q = queue.Queue() if upload else None
        if upload:
            threading.Thread(target=self._drain, args=(upload,), daemon=True).start()

    def _drain(self, upload):
        while True:
            path = self._q.get()
            try:
                upload(path)
            except Exception as e:  # a failed upload must not kill training
                self.errors.append((path, e))
            finally:
                self._q.task_done()

    def steps(self):
        return sorted(int(m[1]) for p in self.root.iterdir() if (m := _NAME.match(p.name)))

    def path(self, step):
        return self.root / f"step-{step:09d}.ckpt"

    def save(self, step, **parts):
        """parts: name -> object with state_dict(), or a plain picklable value."""
        state = {k: v.state_dict() if hasattr(v, "state_dict") else v for k, v in parts.items()}
        tmp = self.root / f".step-{step}.{os.getpid()}.tmp"
        with open(tmp, "wb") as f:
            torch.save({"step": step, "state": state, "rng": rng_state(), "time": time.time()}, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path(step))
        if self._q:
            self._q.put(self.path(step))
            self._q.join() if len(self.steps()) > self.keep else None  # never delete a file that is still uploading
        for old in self.steps()[: -self.keep]:
            self.path(old).unlink(missing_ok=True)

    def load_latest(self, **parts):
        """Restore into objects with load_state_dict(). Returns (step, {name: plain value}); (0, {}) with no checkpoint.
        A file that cannot be read (truncated, disk error) is skipped with a warning and the next older one is used."""
        for step in reversed(self.steps()):
            try:
                blob = torch.load(self.path(step), map_location="cpu", weights_only=False)  # our own files only
            except Exception as e:
                print(f"warning: {self.path(step).name} is unreadable ({type(e).__name__}), trying an older one")
                continue
            missing = set(parts) - set(blob["state"])
            if missing:
                raise KeyError(f"checkpoint {step} has no state for {sorted(missing)}")
            plain = {}
            for k, v in blob["state"].items():
                if k in parts:
                    parts[k].load_state_dict(v)
                else:
                    plain[k] = v
            set_rng_state(blob["rng"])
            return blob["step"], plain
        return 0, {}

    def wait(self):
        if self._q:
            self._q.join()


class Clock:
    """Tells the loop when to checkpoint and when to stop, so a 12-hour session ends cleanly."""

    def __init__(self, every_min=30, stop_after_min=690, now=time.monotonic):
        self.now, self.t0, self.last = now, now(), now()
        self.every, self.stop = every_min * 60, stop_after_min * 60

    def due(self):
        if self.now() - self.last >= self.every:
            self.last = self.now()
            return True
        return False

    def over(self):
        return self.now() - self.t0 >= self.stop


def hub_uploader(repo_id, run_name, token=None):
    """Upload callback for Checkpointer. Needs HF_TOKEN; the repo must exist. Not exercised by the tests."""
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    return lambda p: api.upload_file(path_or_fileobj=str(p), path_in_repo=f"{run_name}/{p.name}", repo_id=repo_id, repo_type="model")
