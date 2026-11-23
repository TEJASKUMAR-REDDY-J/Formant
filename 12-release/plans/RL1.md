# RL1 · Licences and consent — week 1 plan

> **Superseded in part:** [reports/RL1.md](../reports/RL1.md) corrects Sarvam 30B, LiquidCodec and NVIDIA licences.

**Goal:**
- a ledger of every dataset and model licence (codec candidates included);
- a voice-consent rule;
- a PII policy;
- the project licence.

**Done when:** every source is tagged train-only, shareable or excluded.
**Needs:** nothing. **GPU:** none. Nothing below is legal advice; anything unclear is excluded until it is confirmed in writing.

## Ledger

The ledger lives in `12-release/licence-ledger.csv`. It starts from `01-data/sources/hf_datasets.csv` and adds the models.

| Item | Licence on record | Tag (draft) | To do |
|---|---|---|---|
| AI4Bharat speech sets (IndicVoices, IndicVoices-R, Kathbath, Rasa, NPTEL, Shrutilipi), Sangraha, indic-align | CC-BY-4.0 | Train + shareable derivatives, with attribution | Accept the gated terms; record their text |
| MUCS-Hinglish (community mirror) | CC-BY-4.0 on the mirror | Train-only until the original MUCS 2021 terms are confirmed | Find the original terms |
| IndicTTS English/Hindi/Telugu, Svarah | None on card | **Excluded** until confirmed | Email IIT Madras / AI4Bharat |
| Seamless Interaction | CC-BY-NC-4.0 | Timing statistics only | — |
| FLEURS, Lahaja, Vaani-Benchmark, IN22-Conv | CC-BY-4.0 / MIT | Evaluation only | — |
| Qwen3-0.6B | Apache-2.0 | Base of the talker | — |
| Sarvam 30B | Check | Thinker | Read the model licence and any usage policy |
| Mimi | CC-BY-4.0 | Codec candidate | — |
| LiquidCodec, NVIDIA NeMo codec, Qwen3-TTS tokenizer | Check / check / Apache-2.0 | Codec candidates | Must clear before TK1 chooses |
| IndicConformer | MIT | Recogniser | — |
| Indic Parler-TTS, Kokoro-82M | Apache-2.0 | Cascade voices, synthetic data | Confirm the speaker terms for named voices |
| Silero VAD, llama.cpp, OpenVINO, WebRTC AEC3 | MIT / MIT / Apache-2.0 / BSD-3 | Runtime | — |

## Voice consent rule

- **No real person's voice is cloned without written consent.** This applies even when the recordings are CC-BY. Indian courts have recognised voice as part of personality rights.
- **Preferred v0.1 voice:** a **designed synthetic voice**, generated from a text description by an Apache-licensed Indic TTS, so no real speaker is imitated. This is the tiny-voca recipe; PT3 trains on 50–100 h of it.
- **Alternative:** a Rasa speaker, only if their recording terms explicitly allow voice synthesis.

## PII policy

- **Raw audio is never stored** (01-data/DATA_PLAN.md).
- **Transcripts are scanned for personal data before tokens are stored:**
  - phone numbers and emails, by regex;
  - person names, by an Indic named-entity tagger.
  - Hits are masked in the text, and those clips' audio tokens are dropped.
- **The app runs offline and collects nothing.** Demo recordings are only of team members who consent.

## Project licence

- **Code:** Apache-2.0.
- **Weights:**
  - released under Apache-2.0 when every training source allows it;
  - the model card lists every CC-BY source for attribution;
  - non-commercial sources never touch released weights.
- **Recipe, manifests and Indic-FDB v0 scenarios:** published. Third-party audio is not.

## Week

| Day | Work |
|---|---|
| Mon | Build the ledger from the CSV; add the models |
| Tue | Read each licence; send the confirmation emails |
| Wed | Codec licences, so TK1 can choose; the voice rule agreed with PT |
| Thu | PII masking spec handed to DA2 |
| Fri | `reports/RL1.md`; every row tagged |
