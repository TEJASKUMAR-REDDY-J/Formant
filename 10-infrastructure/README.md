# 10 · Infrastructure

Kaggle, the Hugging Face Hub, the laptop and this repo working as one pipeline.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=IN) (phase IDs start with `IN`)

## Scope for v0.1

- Repo, environments, storage layout, Vercel site
- Resumable Kaggle runner and data jobs
- Export toolchain for the laptop
- Release pipeline

**Not in v0.1:**

- Paid cloud, CI runners

## What to expect

- Kaggle sessions end after 12 h and keep 20 GB of output, so the Hub is the real disk
- Resume logic decides whether long runs survive

## Takes in

- Everything

## Hands over

- Runner, layouts, export scripts → every section

## Phases

### IN1 · Week 1 · Repo, storage, runner v0

This repo and guidelines; uv-locked Kaggle and laptop environments (laptop on F:, offline wheels on Kaggle); private Hub repos with Xet transfers; manifest schema; Trackio tracking; checkpoint-and-resume runner.

- **Done when:** Fresh clone sets up both environments; a killed run resumes.
- **Needs:** nothing
- **Plan:** [plans/IN1.md](plans/IN1.md)
- **Status:** doing

### IN2 · Week 2 · Data jobs

GPU jobs for tokenising and pseudo-labelling, CPU jobs for filters, a job ledger.

- **Done when:** Every shard traceable to source, filter version and tokenizer hash.
- **Needs:** IN1
- **Status:** todo

### IN3 · Week 3 · Export toolchain

One command exports a checkpoint to OpenVINO IR and GGUF and benchmarks it on the laptop.

- **Done when:** Export + benchmark in one command.
- **Needs:** IN2, QZ2
- **Status:** todo

### IN4 · Week 4 · Release pipeline

Push models to Hub repos, deploy the site, rebuild from a clean clone.

- **Done when:** Clean-clone rebuild works.
- **Needs:** IN3, RL4 (same-week handoff)
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
10-infrastructure/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
├── plans/        one file per phase, written before the phase starts: IN1.md, IN2.md, IN3.md, IN4.md
└── reports/      one file per phase: IN1.md, IN2.md, IN3.md, IN4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
