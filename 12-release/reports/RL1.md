# RL1 · Licences and consent

**Status:** in progress. Every dataset, model and tool has a tag. **No licence text has been read by a person yet:** every row says `confirmed: no`. Not legal advice.

## What was done

- [`licence-ledger.csv`](../licence-ledger.csv), 42 rows, rebuilt from live Hub metadata by [`licence_ledger.py`](../scripts/licence_ledger.py): licence, gating, the revision seen, tag and reason.
- [`src/formant/pii.py`](../../src/formant/pii.py): masks personal data in transcripts before anything is stored.

## How it was checked

- The tagging rules are asserted on each run. Unknown, missing and share-alike licences are excluded by default, never waved through.
- `python -m pytest tests/test_pii.py`, 30 tests: 19 kinds of identifier are found, in several scripts and read out digit by digit; 9 ordinary sentences (years, prices, scores, PIN codes, counting) are left alone.

## Result

| | shareable | train-only | evaluation-only | statistics-only | excluded |
|---|---|---|---|---|---|
| Datasets (22) | 12 | 1 | 4 | 1 | 4 |
| Models (16) | 12 | – | – | – | 4 |
| Software (4) | 4 | – | – | – | – |

**Excluded until someone reads the terms**

- Datasets: IndicTTS English, Hindi and Telugu; Svarah (no licence on the card).
- Codecs: LiquidCodec (LFM 1.0) and both NVIDIA NeMo codecs (NVIDIA Open Model License). **TK1 may choose only Mimi or the Qwen3-TTS tokenizer today.**
- `microsoft/wavlm-large`: no licence on the card, so EV1 needs another speaker model.

**Confirmed from the cards:** Sarvam 30B is Apache-2.0 (the plan had it as unknown). IndicF5 is MIT. IndicConformer, Indic Parler-TTS and IndicF5 are gated: accept once per account.

**PII limits:** names and street addresses have no fixed shape and are **not** caught. DA2 needs a named-entity tagger as well. The masker errs towards masking: any other number of 9 or more digits is masked.

**Voice rule (unchanged):** no real person's voice without written consent; the preferred v0.1 voice is a designed synthetic one.

## What changes next

1. A person reads each licence, fills in `CONFIRMED` in the script, and asks IIT Madras / AI4Bharat about the four datasets.
2. The team decides the project licence. Recommendation: Apache-2.0 for code. No LICENSE file has been added, because that choice is the owner's.
3. Name tagger for Indian languages (DA2).

**T4-hours used:** 0
