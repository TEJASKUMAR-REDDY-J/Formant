# 12 · Release

What goes public and on what terms: licences, consent, cards, the site, and the v0.1 release.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=RL) (phase IDs start with `RL`)
- **Branch:** `sec/12-release`. Cut feature branches from it and open PRs into it; it merges into `main` when a phase is done ([GUIDELINES.md](../GUIDELINES.md) section 5).

## Scope for v0.1

- Licence and consent ledger from day one
- Public repo and Vercel site
- Model, data and benchmark cards
- v0.1: weights, tokenizers, recipe, Indic-FDB v0, demo

**Not in v0.1:**

- Paper (v0.2)

## What to expect

- Some sources may not allow sharing derived tokens; publish scripts and manifests, not audio
- The codec's and thinker's licences decide what ships together

## Takes in

- Results (06)
- Bundle (07)
- Data recipe (01)

## Hands over

- Public releases

## Phases

### RL1 · Week 1 · Licences and consent

Ledger of every dataset and model licence (codec candidates included); voice consent; PII policy; project licence.

- **Done when:** Every source tagged train-only, shareable or excluded.
- **Needs:** nothing
- **Plan:** [plans/RL1.md](plans/RL1.md)
- **Status:** doing

### RL2 · Week 2 · Public site

Public repo; site and plan on Vercel; alpha video of the cascade.

- **Done when:** Site live; plan status visible to anyone.
- **Needs:** IN1, SV1, RL1
- **Status:** todo

### RL3 · Week 3 · Cards

Draft model, data and Indic-FDB cards with limitations.

- **Done when:** Cards reviewed by two teammates.
- **Needs:** RL2, DA2, EV2
- **Status:** todo

### RL4 · Week 4 · v0.1 release

Quantised talker, tokenizers, recipe, Indic-FDB v0, technical note, demo video.

- **Done when:** v0.1 tag; a stranger can run the demo.
- **Needs:** RL3, QZ4 (same-week handoff), EV4 (same-week handoff), DA4 (same-week handoff)
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
12-release/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
├── plans/        one file per phase, written before the phase starts: RL1.md, RL2.md, RL3.md, RL4.md
└── reports/      one file per phase: RL1.md, RL2.md, RL3.md, RL4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
