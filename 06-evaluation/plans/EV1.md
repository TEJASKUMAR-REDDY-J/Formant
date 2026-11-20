# EV1 · Metrics and test speakers — week 1 plan

**Goal:** define every metric, freeze speaker-disjoint test speakers **before** ingest starts, and stand up the harness skeleton.
**Done when:** the metric spec and frozen test-speaker lists are on the Hub.
**Needs:** ~DA1 (speaker ids from the source cards). **GPU:** none.

## Metric spec

| Area | Metric | Tool | Target (v0.1) |
|---|---|---|---|
| Intelligibility | CER from **two** recognisers: IndicConformer-600M (Indic), Whisper-large-v3-turbo (English and a second opinion) | Text normalised with the Indic NLP normaliser (nukta, punctuation, numerals) | Probe CER ≤ 25% (TR3) |
| Voice | Speaker similarity | WavLM-large speaker verification | ≥ 0.85 to the locked voice (PT3) |
| Quality | DNSMOS P.835; UTMOS22 for English only; CMOS panel (5 raters × 20 clips) | | Relative to the cascade |
| Turn-taking | Takeover rate, response latency, false takeovers on pauses, backchannel rate | Full-Duplex-Bench v1–v3 definitions; M3-DuplexBench for multilingual | Takeover ≥ 0.8 (Hindi, English) |
| Barge-in | Time from user onset to talker silence | Logged frame clock | ≤ 300 ms at p95 |
| Latency | User end-of-turn → first audio, p50/p95 | Logged frame clock | Duplex ≤ 400 ms p50 on GPU; cascade ≤ 1.5 s p50 on the i3 |
| Thinker | MILU accuracy, spoken-style compliance | PT1 checks | No worse than the baseline |
| Codec | ΔCER, speaker similarity, PESQ/STOI | TK1 definitions | ΔCER ≤ 2 points |

**Every number carries:**
- a bootstrap 95% confidence interval;
- a per-language row;
- the label **target** or **result**.

## Test speakers (frozen Thursday)

| Language | Held-out speakers | From |
|---|---|---|
| hi, bn, mr, ta, te | 24 per language, balanced by gender, age group and region. Drawn from IndicVoices and **excluded from IndicVoices-R too**, since they share speakers. | IndicVoices `speaker_id` metadata |
| hi, bn, mr, ta, te | Kathbath test-known and test-unknown speakers | Kathbath splits |
| English (Indian) | All of Svarah (already test-only) | Svarah |
| Hinglish | MUCS test split | MUCS-Hinglish |
| Accents | All of Lahaja (Hindi accents) | Lahaja |

- **The lists are hashed and stored** as `eval/test-speakers-v1.json` in `formant-data`.
- **DA2's filter rejects any clip whose speaker is on a list,** and checks 13-gram overlap with every test transcript.

## Harness skeleton

- **One command:** `python -m formant.eval --suite smoke|codec|duplex|thinker --model <hub-id>`.
- **Suites read pinned manifests** (test audio pulled on demand, 01-data/DATA_PLAN.md) and write JSON plus a markdown table to the Hub.
- **References are transcribed once** per recogniser and cached; every later run reuses them.
- **The Indic-FDB v0 scenario list is drafted here and built in EV2:** pauses, backchannels, barge-in, code-switching, noise.

## Week

| Day | Work |
|---|---|
| Mon | Metric spec draft; agree the targets with each section owner |
| Tue | Speaker statistics from the cards; draw the held-out lists |
| Wed | Hand the lists to DA1/DA2 (filter hook); harness skeleton + codec suite for TK1 |
| Thu | Freeze and hash the lists; smoke suite runs end to end on 10 clips |
| Fri | `reports/EV1.md` + `metric-spec.md` |

## Risks

- **Speaker ids are missing or inconsistent across releases.** Fall back to holding out whole districts, and say so in the data card.
