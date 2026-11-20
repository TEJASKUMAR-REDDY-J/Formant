# 06 · Evaluation

How we know it works: automatic metrics, Indic-FDB (our Indian-language full-duplex benchmark), small human panels and comparison with baselines.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=EV) (phase IDs start with `EV`)

## Scope for v0.1

- Metric spec and speaker-disjoint test sets
- One-command harness
- Indic-FDB v0 for Hindi, English and Hinglish; Full-Duplex-Bench in English
- Comparison with the cascade, Human-1 and a Sarvam cloud sample

**Not in v0.1:**

- Full blind head-to-head against Sarvam with many raters (v0.2)

## What to expect

- Automatic MOS predictors are not validated for Indian languages, so they only compare our own versions
- Panels of 2–3 raters per language give direction, not proof

## Takes in

- Test speakers (01-data)
- Builds to test (04, 07, 09)

## Hands over

- Scores and reports → every section; release numbers → 12-release

## Phases

### EV1 · Week 1 · Metrics and test speakers

Define every metric (two-recogniser CER, speaker similarity, DNSMOS and CMOS, Full-Duplex-Bench turn-taking metrics, barge-in and response latency); reserve test speakers per language before ingest; harness skeleton.

- **Done when:** Metric spec and frozen test-speaker lists.
- **Needs:** DA1 (same-week handoff)
- **Plan:** [plans/EV1.md](plans/EV1.md)
- **Status:** todo

### EV2 · Week 2 · Harness and Indic-FDB scripts

CER from two recognisers, speaker similarity, relative MOS, turn-taking metrics, latency logs. Write Indic-FDB v0 scenarios (pauses, backchannels, barge-in, code-switching, noise) using the methods of Full-Duplex-Bench v3 and M3-DuplexBench.

- **Done when:** One command scores the cascade and any checkpoint.
- **Needs:** EV1, SV1
- **GPU:** 5 T4-hours
- **Status:** todo

### EV3 · Week 3 · Evaluate during training

Score probe checkpoints, the tuned thinker and each quantisation step.

- **Done when:** Weekly score sheet that TR4 and QZ4 decide on.
- **Needs:** EV2, MO3 (same-week handoff)
- **GPU:** 5 T4-hours
- **Status:** todo

### EV4 · Week 4 · Indic-FDB v0 run

Run the benchmark on the cascade, Formant duplex, Human-1 (Hindi) and a small Sarvam cloud sample; 2 native raters per language for naturalness. Run Full-Duplex-Bench in English so the results sit next to published open models.

- **Done when:** v0.1 results page with targets and results clearly labelled.
- **Needs:** EV3, SV3, QZ4 (same-week handoff)
- **GPU:** 10 T4-hours
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
06-evaluation/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
├── plans/        one file per phase, written before the phase starts: EV1.md, EV2.md, EV3.md, EV4.md
└── reports/      one file per phase: EV1.md, EV2.md, EV3.md, EV4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
