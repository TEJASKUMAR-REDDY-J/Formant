# IN1 · Repo, storage, runner v0

**Status:** in progress. The laptop environment, the manifest schema and the checkpoint-and-resume runner work. The Hub repositories and the Kaggle session are not set up: both need the team's accounts.

## What was done

- **Environment:** `pyproject.toml` + `uv.lock`. `requirements-kaggle.txt` lists only what the Kaggle image may lack, because replacing Kaggle's torch can break CUDA.
- **Runner:** [`src/formant/ckpt.py`](../../src/formant/ckpt.py) saves model, optimizer, scaler, sampler, RNG and step in one atomic file, keeps the last 3, uploads in the background, and skips an unreadable file. `Clock` says when to save and when to stop before the 12-hour limit.
- **Schema:** [`src/formant/manifest.py`](../../src/formant/manifest.py), one schema for data, tokens and evaluation, with a validator that also catches test speakers in training data.
- **Kaggle launcher:** [`kaggle_kernel.py`](../scripts/kaggle_kernel.py) builds a kernel that runs one command at one exact commit.
- **Site build:** section pages are no longer committed. Vercel runs `gen-sections.js` on deploy.

## How it was checked

- `python -m pytest`: 6 tests. One kills a real training process mid-run and compares the resumed run with an uninterrupted one: **bit-identical** losses and sampler position on CPU. Others cover a truncated checkpoint, a failing upload, rotation that waits for uploads, and every validator rule.
- **Fresh environment:** `uv sync --frozen` into a new folder on F: (940 MB) gave torch 2.15.0, OpenVINO 2026.4.1 with CPU and GPU devices; the 6 tests pass in it as well as in the older conda environment (torch 2.8).
- TR1's 200-step smoke run was killed and resumed with this runner: bit-identical.

## Result

| "Done when" | State |
|---|---|
| A killed run resumes | ✓ on CPU; not yet on Kaggle |
| A fresh clone sets up the laptop environment | ✓ |
| A fresh clone sets up the Kaggle environment | not tested |

**Why the section pages left git.** The workflow told every section PR to commit the same generated index page, so any two section PRs would have conflicted. `GUIDELINES.md` is updated. This PR's Vercel preview is the first real test of the build step.

## What changes next

1. Team: a Hugging Face account and token; create `formant-data` and `formant-ckpt` (private).
2. First Kaggle session: run the smoke script, record `pip freeze`, pin `requirements-kaggle.txt`.

**T4-hours used:** 0

## Setup (laptop)

```
set UV_CACHE_DIR=F:\tools\uv-cache
uv sync --frozen --extra laptop --extra test
.venv\Scripts\python -m pytest
```
