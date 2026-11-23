# 02 · Tokenizer & embeddings

The audio codec that turns speech into tokens and back, the text vocabulary for the talker's inner-monologue stream, and the embedding tables both feed.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=TK) (phase IDs start with `TK`)
- **Branch:** `sec/02-tokenizer`. Cut feature branches from it and open PRs into it; it merges into `main` when a phase is done ([GUIDELINES.md](../GUIDELINES.md) section 5).

> Embedding is merged in here: it is the vocabulary and code tables these tokenizers feed, about two days of work on its own.

## Scope for v0.1

- Codec bake-off: Mimi vs LiquidCodec vs NVIDIA's multilingual codec
- Trim and extend the text vocabulary (~40k tokens with Indic merges)
- Audio code tables for the user and own streams
- Decoder-only codec fine-tune if a language fails

**Not in v0.1:**

- Training a codec from scratch
- Kronecker-factored tables (they save storage, not memory bandwidth)

## What to expect

- Retroflex, aspirated and geminate consonants are where codecs lose detail
- Trimming Qwen3's 151,936-token output head to ~40k cuts its read from ~1.9 to ~0.5 GB/s, the cheapest speed win in the project
- Freezing the encoder and tuning only the decoder keeps every token already made valid

## Takes in

- Pilot clips (01-data)
- Bandwidth budget (08-performance)

## Hands over

- Versioned codec and text tokenizer → 01-data, 04-training, 07-quantization

## Phases

### TK1 · Week 1 · Codec and vocabulary audit

Round-trip 50 clips per language through each codec: CER, speaker similarity, PESQ/STOI, plus decode speed on the UHD 620. Count tokens per word and per second for the Qwen3, Sarvam and Gemma tokenizers.

- **Done when:** Codec chosen by Friday with per-language numbers; fertility table.
- **Needs:** DA1 (same-week handoff), PF1 (same-week handoff)
- **GPU:** 2 T4-hours
- **Plan:** [plans/TK1.md](plans/TK1.md)
- **Status:** doing

### TK2 · Week 2 · Freeze tokenizers

Trim the vocabulary to the tokens Indic + English text uses, add Indic merges, initialise new rows as the mean of their old pieces; build audio code tables; short warm-up with the body frozen.

- **Done when:** Both tokenizers hashed and versioned; ≤ 2 text tokens per word in every language; Hindi text loss within 5% after warm-up.
- **Needs:** TK1, AR1
- **GPU:** 5 T4-hours
- **Status:** todo

### TK3 · Week 3 · Decoder fix if needed

Only if a language failed TK1: fine-tune the codec decoder on IndicVoices-R with the encoder frozen.

- **Done when:** Round-trip CER within 2 points of the original audio for every language, or no fix needed.
- **Needs:** TK1, DA2
- **GPU:** 0–30 T4-hours
- **Status:** todo

### TK4 · Week 4 · Tokenizer card

Publish both tokenizers with round-trip and fertility tables; list v0.2 vocabulary changes for more languages.

- **Done when:** Tokenizer card in the release.
- **Needs:** TK2, TK3
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
02-tokenizer/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
├── plans/        one file per phase, written before the phase starts: TK1.md, TK2.md, TK3.md, TK4.md
└── reports/      one file per phase: TK1.md, TK2.md, TK3.md, TK4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
