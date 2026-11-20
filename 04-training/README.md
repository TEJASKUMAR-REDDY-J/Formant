# 04 · Training

Pre-training the talker: smoke runs, speech pre-training on the voice set, two-stream dialogue training, robustness.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=TR) (phase IDs start with `TR`)
- **Branch:** `sec/04-training`. Cut feature branches from it and open PRs into it; it merges into `main` when a phase is done ([GUIDELINES.md](../GUIDELINES.md) section 5).

> New section: the first draft had post-training but no pre-training, which is the largest GPU cost.

## Scope for v0.1

- Smoke runs on a small model, dense vs MoE, and the data-mixture search
- MoE talker speech pre-training on ~2–2.4k h, 2–3 epochs, upcycled from Qwen3-0.6B
- Hindi, English and Hinglish two-stream dialogue training
- Noise, crosstalk and echo robustness

**Not in v0.1:**

- Training on 5–10k h (v0.2)
- Duplex training in Bengali, Marathi, Tamil and Telugu (v0.2)

## What to expect

- About 25–40 T4-hours per epoch on ~2k h at realistic T4 efficiency; expert dispatch costs ~20–30% over dense
- fp16 only, so loss scaling must be watched; the router runs in fp32 with a z-loss
- Upcycling, not training from scratch: ~334M frames is too little data for a fresh MoE
- Expect intelligible Hindi and English speech with natural turn timing; voice quality below Sarvam's Bulbul

## Takes in

- Token shards (01-data)
- Frozen tokenizers (02-tokenizer)
- Runner (10-infrastructure)
- Dashboards (11-monitoring)

## Hands over

- Talker checkpoints on the Hub → 05-post-training, 07-quantization, 09-serving

## Phases

### TR1 · Week 1 · Smoke runs

~50M talker on pilot or public codec tokens, dense and MoE: check fp16 stability, router balance, loss per codebook, resume after a killed session. Run 8 tiny mixture-search runs and pick the language weights with the best worst-language dev loss; A/B online data selection (OPUS) against random at equal T4-hours (01-data/DATA_PLAN.md).

- **Done when:** Loss falls on every codebook; experts stay balanced; resume reproduces the curve; mixture weights fixed; OPUS adopted or dropped with numbers.
- **Needs:** IN1 (same-week handoff), MO1 (same-week handoff)
- **GPU:** 10–12 T4-hours
- **Plan:** [plans/TR1.md](plans/TR1.md)
- **Status:** todo

### TR2 · Week 2 · Launch pre-training

Upcycle Qwen3-0.6B into the AR1 MoE with the frozen tables; ZeRO-2 across 2× T4 with 8-bit AdamW; global-batch load balancing (bias-based, no auxiliary loss); single-language micro-batches mixed to the DATA_PLAN ratios; add shards as they land.

- **Done when:** Run passes 1 epoch with stable loss and no dead experts; checkpoint every 30–45 min on the Hub.
- **Needs:** TR1, AR1, TK2 (same-week handoff), DA2 (same-week handoff), PF2 (same-week handoff)
- **GPU:** 30–45 T4-hours
- **Status:** todo

### TR3 · Week 3 · Finish pre-training, dialogue

Complete 2–3 epochs; then train both streams on Hindi, English and Hinglish dialogues (synthetic + split real).

- **Done when:** Probe CER ≤ 25% in all six languages; takeover rate ≥ 0.8 in Hindi and English on held-out clips.
- **Needs:** TR2, DA2, TK2
- **GPU:** 80–125 T4-hours
- **Status:** todo

### TR4 · Week 4 · Robustness

Add noise, far-field audio, crosstalk and echo-like leakage; pick the final checkpoint with evaluation.

- **Done when:** Noisy CER within 5 points of clean; final checkpoint tagged.
- **Needs:** TR3, EV3
- **GPU:** 10 T4-hours
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
04-training/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
├── plans/        one file per phase, written before the phase starts: TR1.md, TR2.md, TR3.md, TR4.md
└── reports/      one file per phase: TR1.md, TR2.md, TR3.md, TR4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
