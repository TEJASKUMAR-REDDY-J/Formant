# DA1 · Licences and pilot

**Status:** in progress. This report covers part 1: which datasets we keep, and how small they get. Part 2 is the pilot run, 10 h per language through every gate.

## What was done

Built the list of datasets Formant keeps. **Rule: Hugging Face only.** Every source is a Hub repository, so every pull is scriptable on Kaggle and every shard traces back to a repo and revision.

- List: [`01-data/sources/hf_datasets.csv`](../sources/hf_datasets.csv), 22 rows.
- Column guide: [`01-data/sources/README.md`](../sources/README.md).
- Sharding, storage and training mixtures: [`01-data/DATA_PLAN.md`](../DATA_PLAN.md).
- Script: [`01-data/scripts/hf_inventory.py`](../scripts/hf_inventory.py) rebuilds the CSV from the public Hub API, with no login needed.

## How small it gets

We keep only our six languages (hi, bn, mr, ta, te, en), only the clips that pass the filters, and only in the form training reads.

Two separate reductions happen, and they are reported separately so neither inflates the other:

1. **Selection:** v0.1 reads only the slices it needs.
2. **Transform:** what it reads becomes tokens or text.

| | Available in our languages | Read once for v0.1 | Stored |
|---|---|---|---|
| Speech for the talker (2.57k h kept) | 915 GB | 459 GB + the NPTEL and Rasa slices (their GB per hour is measured in the pilot) | **1.4 GB** of codec tokens + transcripts |
| Text: tokenizer sample, instruction and seed text | 172 GB | 3.0 GB | 3.0 GB |
| Test sets | 21 GB | 10.6 GB, re-read on demand per evaluation run | ~0 (pinned manifests) |
| English turn timing (Seamless, 200 h sample) | 374 GB | 18.7 GB | 0.01 GB |
| Reserves not used in v0.1 (Vaani transcribed, IndicTTS) | 276 GB | 0 | 0 |
| **Total** | **1.76 TB** | **~490 GB + NPTEL/Rasa slices** | **~4.4 GB** |

**Transform, per hour of speech: raw audio is 42–615 MB per hour depending on the dataset; stored tokens are 0.54 MB per hour.** So tokenising alone makes speech **78–1,139×** smaller per hour (`shrink_per_hour` in the CSV).

The 0.54 MB figure is measured:
- one hour of 6 s clips stored as Mimi codes (8 codebooks, 12.5 Hz, uint16);
- plus transcript, speaker, gender and duration;
- in Parquet with zstd-9.

The codes were uniformly random, so this is the worst case. With 12 codebooks it is 0.79 MB per hour.

**Streamed, never stored:** each Kaggle shard is streamed, filtered, tokenised and uploaded, then its audio is deleted.

**Only what fits is kept.** Every clip passes language ID, SNR, length and transcript agreement (CER against an ASR pass). The pass rate is assumed to be 75% until the pilot measures it.

### Hours kept for v0.1

| Language | Kept | From |
|---|---|---|
| Hindi | 800 h | IndicVoices-R 58 → IndicVoices 562 → Kathbath 120 → Shrutilipi 60 |
| English (Indian) | 400 h | NPTEL En-Indic |
| Bengali | 300 h | IndicVoices-R 88 → IndicVoices 212 |
| Marathi | 300 h | IndicVoices-R 38 → IndicVoices 262 |
| Tamil | 300 h | IndicVoices-R 77 → IndicVoices 223 |
| Telugu | 300 h | IndicVoices-R 105 → IndicVoices 195 |
| Hinglish | 71 h | MUCS-Hinglish, all that passes |
| Voice-lock candidates | 100 h | Rasa, 20 h per Indian language |

Per-language hours are estimates: language GB ÷ the repo's GB per hour. The IndicVoices figure assumes the Hub copy holds the 11.2k transcribed hours. The pilot measures real hours.

Tokens are so small that storage stops mattering. If v0.1 needs more speech, tokenising **all** ~4.6k estimated hours of IndicVoices-R, IndicVoices, Kathbath and MUCS in our languages would still be about 2.5 GB. The real limits are T4-hours and download time.

## Result by priority

| Priority | Meaning | Datasets | Available, our languages | Read once for v0.1 | Stored |
|---|---|---|---|---|---|
| P1 | Pulled for v0.1 | 7 | 885.5 GB | 457.5 GB + NPTEL/Rasa slices | 3.15 GB |
| P2 | Reserve: only if P1 falls short or once the licence clears; Seamless timing sample | 10 | 851.2 GB | 23.3 GB | 1.22 GB |
| EVAL | Test only, never trained on | 5 | 21.3 GB | 10.6 GB per evaluation run | ~0 (manifests) |

"Available" for P1 includes all 143.8 GB of Sangraha, of which only a 1.8 GB sample is read.

## Dropped from the list

Ten datasets from the first pass are out. Each one is either not needed or not safe to use.

| Dataset | Why it is out |
|---|---|
| ARTPARK-IISc/Vaani (full) | 7.2 TB, mostly untranscribed; the transcribed part is already a P2 reserve |
| shiprocket-ai/nirantar | Needs owner approval; provenance unclear |
| SPRINGLab/Hindi-1482Hrs | No licence on the card; Hindi is already covered |
| SPRINGLab/SPRING_INX Bengali, Marathi, Tamil R1 | No licence on the card; those languages are already covered |
| fsicoli/common_voice_22_0 | Community mirror; under 1 GB for hi, mr and te |
| krutrim-ai-labs/IndicST | Repackages sources already listed; custom licence |
| amphion/Emilia-Dataset | 1.5 TB of English, mixed NC/BY licences; NPTEL covers English |
| facebook/seamless-interaction | 25.6 TB with video; the audio-only copy is the P2 row |

## Flags

- **Gated repos** (ai4bharat, ARTPARK-IISc): the team's Hugging Face account must accept each repo once before Kaggle can pull.
- **No licence on the card:** IndicTTS English, Hindi and Telugu, and Svarah. They are P2/EVAL and cannot be used until RL1 confirms their terms.
- **Non-commercial:** Seamless Interaction (CC-BY-NC). It is used only for the turn-timing table, never for audio or weights.
- **Community mirror:** MUCS-Hinglish. It is kept only if RL1 confirms the original MUCS licence.
- **Test sets:** FLEURS, Svarah, Lahaja, Vaani-Benchmark and IN22-Conv, plus the held-out speakers EV1 reserves, never enter training. The DA2 filter checks this.

## Next (rest of DA1)

1. Accept the gated repos with the team's Hugging Face account. Add the Hub token as a Kaggle secret.
2. Pilot: stream 10 h per language from the P1 sets through every gate. Measure real hours, pass rate, GB per hour and T4-minutes per 1,000 h. Then rerun the script with the measured numbers.
3. Measure pause, overlap and backchannel statistics on the conversational part of IndicVoices (Indian languages) and on Seamless Interaction (English).
4. RL1: confirm the terms for every `none on card` row, and mark each one train-only, shareable or excluded.
