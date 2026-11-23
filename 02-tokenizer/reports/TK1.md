# TK1 · Codec and vocabulary audit

**Status:** in progress. The vocabulary half has first numbers. The codec bake-off needs audio clips and codec weights; both wait for the data go-ahead.

## What was done

- Classified every token of the Qwen3 and Sarvam vocabularies by script, and measured tokens per word on 70 draft sentences ([script](../scripts/vocab_audit.py), [numbers](vocab-audit.json)).
- Read the codec candidates' cards on the Hub (metadata only).
- Downloaded two `tokenizer.json` files (45 MB in total). No data and no weights.

## How it was checked

The script asserts its script classifier on known cases, and the byte decoder on known Qwen3 tokens. The sentences are drafts by non-native authors: 10 per language, everyday topics, punctuation attached. **The fertility numbers are indicative, not final.**

## Result

Tokens per word (n = 10 sentences per language), and text tokens per second at an assumed 2.5 words/s. The monologue stream has 12.5 slots per second.

| Language | Qwen3 | Tokens/s | Sarvam | Tokens/s |
|---|---|---|---|---|
| English | 1.20 | 3.0 | 1.18 | 2.9 |
| Hinglish (Latin) | 1.77 | 4.4 | 1.43 | 3.6 |
| Hindi | 4.59 | 11.5 | 1.40 | 3.5 |
| Bengali | 5.68 | **14.2** | 1.61 | 4.0 |
| Marathi | 5.67 | **14.2** | 1.99 | 5.0 |
| Tamil | 8.70 | **21.8** | 2.32 | 5.8 |
| Telugu | 9.78 | **24.4** | 2.07 | 5.2 |

Vocabulary by script:

| | Qwen3 | Sarvam 30B |
|---|---|---|
| Tokens | 151,669 | 262,144 |
| In our Indic scripts (Devanagari, Bengali, Tamil, Telugu) | **149** | **31,650** |
| ASCII Latin | 88,492 | 139,589 |
| Kept by script | 98,807 (65%) | 186,088 (71%) |

**What this means**

1. **Qwen3's vocabulary cannot carry the inner monologue in Indian languages.** It holds 149 Indic tokens and falls back to bytes. Bengali, Marathi, Tamil and Telugu would overflow the 12.5 slots per second; Hindi would have no room for pauses.
2. **Proposal for TK2: build the talker's text vocabulary from Sarvam's tokens instead of adding merges to Qwen3.** 31,650 Indic tokens + a frequency-cut set of English and Hinglish tokens + byte fragments comes to about 40–45k, inside the plan's ~40k head budget.
   - The thinker's reply can then stream into the monologue slot **without re-tokenising**, because both share token ids.
   - The vocabulary is already trained on these languages (Apache-2.0).
   - Cost: every row of the talker's text table is new to Qwen3-0.6B, so it starts as the mean of its Qwen3 pieces, as already planned.
3. **Tamil (2.32) and Telugu (2.07) are slightly over the 2-tokens-per-word target** even with Sarvam's tokens. At 5–6 tokens/s they still fit the slots.

Codec facts corrected from the Hub:

| Codec | Fact | Plan said |
|---|---|---|
| LiquidCodec | `LiquidAI/Liquid-Codec`, 73.6M parameters, 12 groups of FSQ [8, 7, 6, 6] = 2,016 codes, so 1.65 kbps; licence **LFM 1.0** (conditional commercial use) | licence unknown, "~1–2 kbps" |
| NVIDIA NeMo nano codec | Two 12.5 Hz versions, 0.6 and 1.78 kbps; **22.05 kHz**, NVIDIA Open Model License | 24 kHz implied |
| Qwen3-TTS tokenizer | 170.6M parameters, about 1.8× Mimi's 96.2M | not stated |

## What changes next

1. Codec bake-off once audio is allowed. Both non-standard licences must clear RL1 first.
2. Re-measure fertility on a real corpus and real speaking rates (DA1).
3. Native speakers review the sentences and write the hard-sound set.

**T4-hours used:** 0
