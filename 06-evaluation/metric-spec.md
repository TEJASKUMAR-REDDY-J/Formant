# Metric spec (v0)

One definition per metric. Code: `src/formant/evalkit.py`. Every reported number carries a language, a 95% interval, and the label **target** or **result**.

| Metric | Definition | v0.1 target |
|---|---|---|
| **CER** | Total character edits ÷ total reference characters over the set (never a mean of per-clip rates), after `normalise()`, **spaces not scored**. Two recognisers per language: IndicConformer-600M for Indic languages and Whisper-large-v3-turbo as English main and second opinion. Report both. | Probe ≤ 25% (TR3) |
| **ΔCER** | CER of processed audio minus CER of the original, same recogniser, same clips | ≤ 2 points (TK1) |
| **Takeover rate** | Share of real user turn ends after which the agent starts within 3 s, before the user speaks again. Starting up to 200 ms early counts as on time. | ≥ 0.8 in Hindi and English (TR3) |
| **Response latency** | Agent start − user turn end, for takeovers; p50 and p95 | ≤ 400 ms p50 on a GPU |
| **False takeover** | Agent starts inside a user turn and overlaps it for more than 1 s. A shorter overlap is a **backchannel** and is counted separately. | Reported |
| **Barge-in stop** | User onset → agent silence, when the user speaks for at least 0.7 s over the agent | ≤ 300 ms for 95% |
| **Speaker similarity** | Cosine of speaker embeddings against the locked voice | ≥ 0.85 (PT3) |
| **Quality** | DNSMOS P.835 (all languages); UTMOS (English only: it was trained on English); CMOS panel of 5 raters × 20 clips | Relative to the cascade |
| **Style compliance** | `formant.style.check` (PT1) | ≥ 90% |

## Rules

- **Confidence intervals resample speakers, not clips.** Clips of one speaker are not independent, so resampling clips makes intervals too narrow (the tests show it).
- **`normalise()`** unifies Unicode (NFC, nukta spellings, zero-width joiners), maps digits of every script to 0–9, folds case, and turns punctuation into spaces.
- **Test speakers are chosen by `select_speakers()`**: 24 per language with at least 2 minutes each, balanced over gender, age group and region. The choice is deterministic (keyed hash, seed `formant-ev1-v1`) and does not depend on row order. `freeze()` gives the hash stored with the lists.
- A language that cannot supply 24 eligible speakers is an error, not a shorter list.

## Open

- **Speaker model:** `microsoft/wavlm-large` has no licence on its card (RL1 ledger), so it cannot be used until that is confirmed. `facebook/w2v-bert-2.0` is MIT but is not a speaker model. RL1 and EV1 pick a replacement.
- The turn-taking numbers need annotated turn ends. They come from the scenario scripts in Indic-FDB (EV2), not from a detector.
