# DA1 · Licences and pilot

**Status:** in progress. This report covers part 1, the source inventory. The pilot run (10 h per language through every gate) is part 2.

## What was done

Built the list of datasets Formant will pull. **Rule: Hugging Face only.** Every source is a Hub repository, so pulls are scriptable on Kaggle (`datasets` streaming or `huggingface_hub`) and every shard can be traced back to a repo and revision.

- List: [`01-data/sources/hf_datasets.csv`](../sources/hf_datasets.csv), 32 rows.
- Script: [`01-data/scripts/hf_inventory.py`](../scripts/hf_inventory.py). It rebuilds the CSV and refreshes licence, gating and sizes from the public Hub API (no login needed): `python 01-data/scripts/hf_inventory.py`

## How the numbers were measured

- **Sizes** are the bytes in each repo's `main` branch today (Hub `treesize` API), not the repo's storage history.
- **`our_languages_size_gb`** sums only the folders for Hindi, Bengali, Marathi, Tamil, Telugu and English when the repo is split by language. Single-language repos count in full.
- **Hours** are as reported on each dataset card for the whole dataset. Hours per language are measured in part 2, not guessed here.
- **Licence** is the card's declared licence. "none on card" means the card declares nothing, so we cannot use it until RL1 confirms the terms.

## Result

| Priority | Meaning | Datasets | Size in our languages |
|---|---|---|---|
| P1 | Pull for v0.1 | 7 | 885.5 GB |
| P2 | Top-up or licence pending | 10 | 851.2 GB |
| P3 | Only if P1 + P2 fall short | 9 | 4,466.5 GB |
| EVAL | Test sets, never trained on | 5 | 21.3 GB |
| X | Listed so nobody pulls it | 1 | 25.6 TB (video) |

### P1: what v0.1 is built from

| Dataset | Licence | Reported hours | Our languages (GB) | Role |
|---|---|---|---|---|
| ai4bharat/indicvoices_r | CC-BY-4.0 | 1,704 h (22 langs) | hi 47 · bn 72 · mr 31 · ta 63 · te 86 | Cleanest natural speech; codec tests |
| ai4bharat/IndicVoices | CC-BY-4.0 | 11.2k h transcribed | hi 50 · bn 41 · mr 38 · ta 50 · te 34 | Natural speech + real conversations |
| ai4bharat/Kathbath | CC-BY-4.0 | 1,684 h (12 langs) | hi 17 · bn 11 · mr 18 · ta 21 · te 17 | Read speech |
| ai4bharat/Rasa | CC-BY-4.0 | ≥ 20 h per speaker | hi 18 · bn 18 · mr 18 · ta 20 · te 17 | Voice-lock candidates |
| ai4bharat/NPTEL (En-Indic) | CC-BY-4.0 | 44.4k h (collection) | en 46 | Indian-accented English |
| dianavdavidson/MUCS-Hinglish | CC-BY-4.0 | 89.9 h + 5.2 h | 10 | Hinglish speech |
| ai4bharat/sangraha (verified) | CC-BY-4.0 | text | hi 37 · bn 30 · mr 13 · ta 19 · te 15 · en 30 | Vocabulary merges, thinker text |

### Pull plan for v0.1 (~2–2.4k h)

| Language | Target | Sources, in order |
|---|---|---|
| Hindi | ~800 h | IndicVoices-R → IndicVoices → Kathbath → Shrutilipi |
| English (Indian) | ~400 h | NPTEL En-Indic → IndicTTS-English (if RL1 clears it) |
| Bengali, Marathi, Tamil, Telugu | ~300 h each | IndicVoices-R → IndicVoices → Kathbath |
| Hinglish | all of it (~95 h) | MUCS-Hinglish + code-mixed IndicVoices clips |

**We never store raw audio.** P1 alone is ~885 GB, and IndicVoices-R works out to roughly 0.6 GB per hour, so 2.4k h of raw audio would be over 1 TB, far more than a Kaggle session's disk. The DA2 job instead runs shard by shard on Kaggle: stream a shard → filter (language ID, SNR, length, CER agreement) → tokenise with the codec → upload tokens to the Hub → delete the audio. Tokens for 10k h are about 7 GB.

## Flags

- **Gated repos** (ai4bharat, ARTPARK-IISc, Emilia): the team's Hugging Face account must click "accept" on each repo page once before Kaggle can pull. `shiprocket-ai/nirantar` needs manual approval and its provenance checked.
- **No licence on the card:** SPRINGLab IndicTTS (English, Hindi, Telugu), Hindi-1482Hrs, SPRING-INX, Svarah. Unusable until RL1 confirms the terms with IIT Madras / AI4Bharat.
- **Non-commercial:** Seamless Interaction (CC-BY-NC). Used only for English turn-timing statistics; its audio must not train shipped weights.
- **Community mirrors**, not the original publishers: MUCS-Hinglish, Common Voice 22, Seamless audio-only. Keep them only if the original licence is confirmed.
- **Evaluation sets** (FLEURS, Svarah, Lahaja, Vaani-Benchmark, IN22-Conv), plus the held-out speakers EV1 reserves, never enter training. The DA2 filter checks this.

## Next (rest of DA1)

1. Accept the gated repos with the team's Hugging Face account. Add the Hub token as a Kaggle secret.
2. Pilot: stream 10 h per language from the P1 sets through every gate. Measure pass rate, GB per hour and T4-minutes per 1,000 h.
3. Measure pause, overlap and backchannel statistics on the conversational part of IndicVoices (Indian languages) and on Seamless Interaction (English).
4. RL1: confirm terms for every "none on card" row; mark each row train-only, shareable or excluded.
