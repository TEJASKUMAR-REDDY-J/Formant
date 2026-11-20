# 01 · Data

All audio and text the models learn from: licensed sources, quality gates, speaker splitting, conversation timing statistics, synthetic dialogues, thinker text and the held-out tests.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=DA) (phase IDs start with `DA`)

## Scope for v0.1

- ~1.5–2k h single-speaker speech as codec tokens (Hindi ~800 h, 300 h each other language)
- ≥ 200 h two-channel Hindi/Hinglish dialogue (synthetic + split real)
- Spoken-style Q&A text for the thinker
- Speaker-disjoint test sets

**Not in v0.1:**

- 5–10k h voice set and all-language dialogue (v0.2)
- Buying data or recording new conversations

## What to expect

- Hindi is the strongest language; Tamil and Telugu have fewer clean hours
- Real two-party Indic conversation is scarce, so synthetic speech carries most of the duplex signal
- Data is the biggest schedule risk in week 2

## Takes in

- Licence ledger (12-release)
- Frozen codec (02-tokenizer)
- Test-speaker lists (06-evaluation)

## Hands over

- Token shards and manifests on the Hub → 04-training, 05-post-training
- Timing statistics → 03-architecture, 06-evaluation

## Phases

### DA1 · Week 1 · Licences and pilot

Licence ledger per source. Run 10 h per language through every gate: language ID ≥ 0.9, SNR ≥ 15 dB, 2–30 s clips, two-recogniser CER agreement ≤ 15%, PII masking. Measure gaps, overlaps and backchannels on pilot conversations.

- **Done when:** Pilot manifest on the Hub; gate pass rate and cost per 1,000 h for each step; first timing statistics.
- **Needs:** IN1 (same-week handoff), EV1 (same-week handoff), RL1 (same-week handoff)
- **Status:** todo

### DA2 · Week 2 · Voice set and dialogues v0

Ingest ~1.5–2k h and tokenise with the chosen codec. Generate ≥ 200 h of Hindi/Hinglish two-channel dialogue: LLM-written scripts, open Indic TTS voices, DA1 timings. Split real conversations with the speaker splitter. Build the thinker's spoken-style text set.

- **Done when:** ≥ 1.5k h of tokens and ≥ 200 h of dialogue on the Hub, every shard tagged with source, licence and tokenizer hash.
- **Needs:** DA1, TK1, EV1
- **GPU:** 60–80 T4-hours
- **Status:** todo

### DA3 · Week 3 · Grow and check

Keep shards flowing into training runs; top up the weaker languages; native-speaker spot-check of 100 synthetic clips per language.

- **Done when:** Naturalness spot-check ≥ 3.5/5; hours report per language.
- **Needs:** DA2
- **GPU:** 20–30 T4-hours
- **Status:** todo

### DA4 · Week 4 · Freeze and document

Freeze v0.1 splits; write data cards; publish the recipe (scripts and manifests, not audio).

- **Done when:** Data cards and recipe in the repo; someone else can rebuild the manifests.
- **Needs:** DA3, RL3
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
01-data/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
└── reports/      one file per phase: DA1.md, DA2.md, DA3.md, DA4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
