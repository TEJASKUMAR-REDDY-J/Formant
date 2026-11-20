# 05 · Post-training

Making trained models behave: spoken-style tuning for the thinker, one consistent voice for the talker, and the talker learning to voice the thinker's plan.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=PT) (phase IDs start with `PT`)
- **Branch:** `sec/05-post-training`. Cut feature branches from it and open PRs into it; it merges into `main` when a phase is done ([GUIDELINES.md](../GUIDELINES.md) section 5).

## Scope for v0.1

- Thinker QLoRA for spoken-style replies
- Voice lock on one licensed or consenting voice
- Coupled fine-tune (plan text → speech, natural fillers when late)
- Basic refusal behaviour

**Not in v0.1:**

- Preference or RL tuning for timing (v0.2)
- 500 h own-voice set (v0.2)

## What to expect

- Thinker style tuning is routine and low risk
- Voice lock with ~50–100 h gives a stable voice, not an expressive one

## Takes in

- Thinker choice (03-architecture)
- Talker checkpoints (04-training)
- Thinker text (01-data)

## Hands over

- Tuned thinker and talker → 07-quantization, 09-serving

## Phases

### PT1 · Week 1 · Thinker baseline

Score Sarvam 30B on Indic QA with spoken-style prompts; write the style spec: short replies, spoken numbers, code-mixing on request.

- **Done when:** Baseline scores and style spec.
- **Needs:** EV1 (same-week handoff)
- **Plan:** [plans/PT1.md](plans/PT1.md)
- **Status:** todo

### PT2 · Week 2 · Thinker style tuning

QLoRA on 2× T4 with the spoken-style set.

- **Done when:** Replies under ~3 spoken sentences; Indic QA no worse than baseline.
- **Needs:** PT1, DA2 (same-week handoff), AR2 (same-week handoff)
- **GPU:** 30–45 T4-hours
- **Status:** todo

### PT3 · Week 3 · Voice lock

Fine-tune the talker on ~50–100 h of one voice. Preferred: a designed synthetic voice from an Apache-licensed Indic TTS, so no real person is imitated (the tiny-voca recipe); otherwise a Rasa speaker whose terms allow synthesis.

- **Done when:** Speaker similarity ≥ 0.85 to the reference across languages.
- **Needs:** TR2, DA2, RL1
- **GPU:** 10–15 T4-hours
- **Status:** todo

### PT4 · Week 4 · Coupled fine-tune

Teacher-force thinker plan text into the monologue slot; train fillers for late plans and stopping on barge-in.

- **Done when:** ≥ 80% complete replies and p50 latency ≤ 400 ms on a GPU.
- **Needs:** TR3, AR3, PT2
- **GPU:** 15–25 T4-hours
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
05-post-training/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
├── plans/        one file per phase, written before the phase starts: PT1.md, PT2.md, PT3.md, PT4.md
└── reports/      one file per phase: PT1.md, PT2.md, PT3.md, PT4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
