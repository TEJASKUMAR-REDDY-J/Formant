# IN1 · Repo, storage, runner v0 — week 1 plan

**Goal:**
- repo and guidelines;
- pinned Kaggle and laptop environments;
- private Hub repos;
- manifest schema;
- a checkpoint-and-resume runner.

**Done when:** a fresh clone sets up both environments, and a killed run resumes.
**Needs:** nothing. **GPU:** none.

## Pieces

| Piece | Choice | Why |
|---|---|---|
| Repo | This repo; `GUIDELINES.md`; plan board on Vercel | Done |
| Laptop environment | `uv` virtual environment **on F:** (`F:\formant\.venv`), `uv.lock` committed; `HF_HOME=F:\hf-cache`; OpenVINO 2026.4, optimum-intel, llama.cpp release binaries (AVX2) | Reproducible; nothing on C or D |
| Kaggle environment | Same lock exported to `requirements-kaggle.txt`; the wheels are cached as a private Kaggle dataset and installed offline | Saves ~5 min per session; avoids version drift |
| Hub repos | `formant-data` (private dataset, layout from 01-data/DATA_PLAN.md), `formant-ckpt` (private model) | One store for everything |
| Transfers | `huggingface_hub` with Xet storage: chunk-level dedup, so re-uploading a slightly changed checkpoint sends only the changed chunks | Fast, cheap checkpoint pushes |
| Manifest schema | One Parquet schema shared by data, tokens and eval (DATA_PLAN section 3); validated on write | One contract |
| Secrets | `HF_TOKEN` as a Kaggle secret and a laptop environment variable; never in files | GUIDELINES section 1 |
| Tracking | **Trackio** (Hugging Face): local-first, wandb-compatible API, syncs to a private Hub Space | Free; data stays on the Hub |

## Runner v0

```
formant-run <config.yaml>
  → resolve config + git commit + data manifest version + tokenizer hash
  → pull the latest checkpoint for this run name from formant-ckpt (if any) and restore
     model, optimizer, loss scaler, sampler position, RNG states, step
  → train; every 30–45 min: save in the background thread, upload to the Hub, keep the last 3
  → at 11 h 30 min of session time: final save, clean exit
```

- **Launch:** from the laptop, `kaggle kernels push` with the config baked in. The next session is relaunched by hand, or by a small loop on the laptop. No CI runners.
- **Done test:** start TR1's smoke run, kill the kernel mid-epoch, relaunch, and check that the step count and loss continue.

## Week

| Day | Work |
|---|---|
| Mon | `uv` lock; laptop environment on F:; Hub repos; Kaggle wheels dataset |
| Tue | Manifest schema + validator; Trackio Space |
| Wed | Runner save/restore; background uploads |
| Thu | Kill-and-resume test with TR1; fresh-clone test on a second machine |
| Fri | `reports/IN1.md`; setup steps in the root README |
