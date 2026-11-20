# TK1 · Codec and vocabulary audit — week 1 plan

**Goal:** choose the audio codec by Friday on per-language evidence, and measure how each candidate text tokenizer handles our six languages.
**Done when:** codec chosen with per-language numbers; fertility table published.
**Needs:** ~DA1 (pilot clips), ~PF1 (UHD 620 timing harness). **GPU:** 2 T4-hours.

## Candidates (November 2026)

| Codec | Frame rate | Codes per frame | Bitrate | Licence (RL1 confirms) | Why it is in |
|---|---|---|---|---|---|
| **Mimi** (Kyutai) | 12.5 Hz | 8 RVQ × 2048 | 1.1 kbps | CC-BY-4.0 | Incumbent. Codebook 0 is distilled from WavLM, so it carries phonetic content. Behind Moshi and most open duplex models. |
| **LiquidCodec** (Liquid AI, Nov 2026) | 12.5 Hz | 12 FSQ groups | ~1–2 kbps | check | Trained on 107 languages; reported ~13× faster encode and ~3× faster decode than Mimi. FSQ allows parallel heads instead of a depth transformer. |
| **NVIDIA NeMo nano codec** (multilingual) | 12.5 Hz | FSQ | 0.6–1.9 kbps | check | Multilingual training, low frame rate |
| **Qwen3-TTS-Tokenizer-12Hz** (Jan 2026) | 12.5 Hz | 1 semantic + 15 acoustic RVQ | ~2.2 kbps | Apache-2.0 | Strong 2026 tokenizer. Tested at its first 8 codebooks so the talker's bus budget stays the same. |

**Watch, not tested:**
- **FlexiCodec** (ICLR 2026): dynamic 3–12.5 Hz, a v0.2 idea for fewer frames during silence.
- **NeuCodec:** 50 Hz, too fast for an 80 ms tick.

## What we measure

Per codec, 50 clips per language. The clips come from FLEURS **validation** (never test) and the DA1 pilot (IndicVoices-R).

| Metric | How | Why |
|---|---|---|
| ΔCER | CER of the round-tripped audio minus CER of the original. IndicConformer-600M for Indic, Whisper-large-v3-turbo for English. | Intelligibility loss caused by the codec alone |
| Hard-sound check | 20 sentences per language dense in retroflex/dental pairs (ट/त, ड/द), aspirates (क/ख) and geminates; a native speaker listens to 10 | Where codecs smear Indian languages |
| Speaker similarity | WavLM-large speaker-verification cosine, original vs round trip | Voice preserved |
| PESQ-WB, STOI, DNSMOS | Standard tools | Quality. UTMOS is English-centric, so it is reported but not decisive. |
| Decode speed | OpenVINO fp16 streaming decoder on the UHD 620, ms per 80 ms frame (PF1 harness); also 1 CPU thread | Runtime fit |
| Encode speed | Hours of audio per T4-hour, batched | DA2's GPU cost |
| Codebook-0 probe (optional, 1 T4-h) | Linear CTC probe from codebook-0 embeddings to phones | Whether the first codebook is semantic, which makes talker training easier |

### Decision rule, in order

1. ΔCER ≤ 2 points in **every** language, and the hard-sound check passes. Otherwise the codec is out, or TK3 fixes its decoder.
2. Decoder ≤ 15 ms per frame on the UHD 620.
3. Higher speaker similarity, then lower bus traffic (FSQ parallel heads beat a depth transformer).
4. The licence must clear RL1. On a tie, take Mimi for its ecosystem.

## Vocabulary audit

- **Corpus:** 10k sentences per language from Sangraha (a held-out slice) plus FLEURS validation transcripts.
- **Tokenizers:** Qwen3 (151,936), Sarvam 30B, Gemma.
- **Report per language:**
  - tokens per word;
  - **text tokens per second of speech**, using IndicVoices speaking rates. The inner-monologue slot carries at most one text token per 80 ms frame, so this must stay well under 12.5 per second;
  - share of the Qwen3 vocabulary our six languages actually use, which sets the trim target of ~40k.
- **TK2 hand-off:** a candidate keep-list of ids, and Indic merge candidates (BPE on the Sangraha sample) for any language above 2 tokens per word.

## Efficiency

- **One Kaggle session runs the whole bake-off.** The original clips are transcribed once and cached; every codec reuses those transcripts.
- **All clips are resampled once to 24 kHz** and stored as an in-memory batch, so no codec re-decodes FLAC.
- **Decode timing runs on the laptop** through the PF1 harness, with no extra tooling.

## Week

| Day | Work |
|---|---|
| Mon | Pull the codecs; build the clip list (FLEURS validation; the pilot list from DA1 on Wednesday); write the hard-sound sentences with native speakers |
| Tue | Round-trip all codecs on T4; ASR, speaker and quality metrics |
| Wed | Add the DA1 pilot clips; export decoders to OpenVINO; PF1 times them on the UHD 620 |
| Thu | Fertility and tokens-per-second table; listening check |
| Fri | Decision against the rule above; write `reports/TK1.md`; hand the codec choice to AR1, DA2, QZ2 and SV2 |

## Risks

- **Every codec fails a language.** TK3's decoder-only fine-tune is the fix: it freezes the encoder, so existing tokens stay valid.
- **LiquidCodec or the NVIDIA codec has an unusable licence.** It drops at RL1, before it can be chosen.
