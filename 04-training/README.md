# 04 · Training

Pre-training the talker: smoke runs, speech pre-training on the voice set, two-stream dialogue training, robustness.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=TR) (phase IDs start with `TR`)

> New section: the first draft had post-training but no pre-training, which is the largest GPU cost.

## Scope for v0.1

- Smoke runs on a small model
- 0.6B speech pre-training on ~1.5–2k h, 2–3 epochs
- Hindi/Hinglish two-stream dialogue training
- Noise, crosstalk and echo robustness

**Not in v0.1:**

- Training on 5–10k h (v0.2)
- Duplex training in all five languages (v0.2)

## What to expect

- About 20–30 T4-hours per epoch on ~2k h at realistic T4 efficiency
- fp16 only, so loss scaling must be watched
- Expect intelligible Hindi speech with natural turn timing; voice quality below Sarvam's Bulbul

## Takes in

- Token shards (01-data)
- Frozen tokenizers (02-tokenizer)
- Runner (10-infrastructure)
- Dashboards (11-monitoring)

## Hands over

- Talker checkpoints on the Hub → 05-post-training, 07-quantization, 09-serving

## Phases

### TR1 · Week 1 · Smoke runs

~50M talker on pilot or public codec tokens: check fp16 stability, loss per codebook, resume after a killed session.

- **Done when:** Loss falls on every codebook; resume reproduces the curve.
- **Needs:** IN1 (same-week handoff), MO1 (same-week handoff)
- **GPU:** 5 T4-hours
- **Status:** todo

### TR2 · Week 2 · Launch pre-training

Initialise from Qwen3-0.6B with the frozen tables; stream shards as they land; DDP on 2× T4.

- **Done when:** Run passes 1 epoch with stable loss; checkpoint every 30–45 min on the Hub.
- **Needs:** TR1, AR1, TK2 (same-week handoff), DA2 (same-week handoff), PF2 (same-week handoff)
- **GPU:** 25–35 T4-hours
- **Status:** todo

### TR3 · Week 3 · Finish pre-training, dialogue

Complete 2–3 epochs; then train both streams on Hindi/Hinglish dialogues (synthetic + split real).

- **Done when:** Probe CER ≤ 25% in all five languages; Hindi takeover rate ≥ 0.8 on held-out clips.
- **Needs:** TR2, DA2, TK2
- **GPU:** 60–100 T4-hours
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
└── reports/      one file per phase: TR1.md, TR2.md, TR3.md, TR4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
