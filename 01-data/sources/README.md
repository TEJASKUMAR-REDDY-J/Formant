# Sources

`hf_datasets.csv` lists every dataset Formant keeps. All of them are on Hugging Face, and nothing comes from anywhere else. Each row also says how small the dataset gets once we keep only our languages and convert it to what training reads.

How the data is sharded and mixed for training: [`../DATA_PLAN.md`](../DATA_PLAN.md).

Rebuild: `python 01-data/scripts/hf_inventory.py`. Sizes, licences, clip counts, fields, dates and downloads come live from the Hub API.

## What we store, and how small it gets

| What | Stored as | Size per hour |
|---|---|---|
| Training speech | Codec tokens (Mimi: 8 codebooks at 12.5 Hz, uint16) + transcript + speaker, gender, duration. Parquet, zstd. | **0.54 MB** (measured, worst case) |
| Test sets, codec fine-tune audio (TK3) | Manifest only: repo, commit and clip ids. The audio is re-streamed from the Hub when needed. | ~0 |
| Text | Parquet, zstd, sampled | Fixed budget per row |
| English turn timing | Speech/silence start and end times per speaker, no audio | ~0.1 GB in total |

For comparison, the raw audio runs 42–615 MB per hour depending on the dataset (`raw_mb_per_hour`).

The 0.54 MB figure was measured on one hour of 6-second clips filled with uniformly random codes, so it is an upper bound: real codes compress a little better. With 12 codebooks (LiquidCodec, if TK1 picks it) the figure is 0.79 MB per hour.

**Only what fits is kept.** Every clip passes language ID, SNR, length and transcript-agreement (CER) filters before it is tokenised. The pass rate is assumed to be 75% until the DA1 pilot measures it. Clips that fail are never stored.

## Columns

| Column | Meaning |
|---|---|
| `priority` | **P1**: pulled for v0.1. **P2**: reserve, used only if P1 falls short or once its licence clears. **EVAL**: test only, never trained on. |
| `dataset` | Hub repo id |
| `what_it_is` | One-line description |
| `style` | Read, extempore, conversation, studio TTS, lectures, news or text |
| `used_for` | Its job in Formant, with the plan cell |
| `licence` | As declared on the card. `none on card` means it stays unused until RL1 confirms the terms. |
| `commercial_use` | `yes`, `no` (non-commercial), or `check` |
| `access` | `open`, `click to accept` (log in and accept once), or `owner approval` |
| `hours_reported` | Hours the card reports for the whole repo |
| `hours_our_languages_est` | Hours in hi, bn, mr, ta, te and en, estimated as language GB ÷ repo GB per hour. The pilot replaces this with measured hours. |
| `hours_by_language_est` | The same, per language |
| `clips_our_languages` | Clips in our languages, all splits, from the card |
| `raw_gb_our_languages` | Bytes on the Hub that are **available** to us. This is not what v0.1 downloads (see `v01_raw_gb_streamed`). |
| `raw_gb_scope` | What that number covers: only our-language folders, a whole one-language repo, or a whole multi-language repo with no language folders (an upper bound) |
| `raw_gb_by_language` | The same, per language |
| `raw_mb_per_hour` | Repo size ÷ reported hours: how heavy the raw audio is. Blank when the card reports no hours. |
| `v01_hours_kept` | Hours of speech v0.1 keeps after filtering |
| `v01_hours_kept_by_language` | The same, per language |
| `v01_raw_gb_streamed` | What v0.1 actually reads from the repo, once: kept hours ÷ pass rate × MB per hour for speech; the sample size for text and timing; the test split for evaluation sets (re-read for each run). Blank = unknown until the pilot measures MB per hour (NPTEL, Rasa) or not read in v0.1. Never stored. |
| `v01_stored_as` | Storage form (see the table above) |
| `v01_stored_gb` | What we keep on the Hub. Speech uses the measured worst case of 0.54 MB per hour. Blank = nothing stored (a reserve not used in v0.1, or a test set kept as a manifest only). |
| `shrink_per_hour` | `raw_mb_per_hour` ÷ 0.54: how much smaller one hour of speech gets once it is tokenised. It is a per-hour ratio, so it measures compression alone, never how much of the dataset we skip. |
| `keep_rule` | Exactly which configs, splits and slices are kept |
| `splits` | Splits the dataset ships |
| `metadata_fields` | Non-audio columns it ships, for example speaker, gender, age, district or scenario |
| `total_repo_gb` | Whole repo, all languages |
| `last_updated` | Last commit on the Hub |
| `downloads_30d` | Hub downloads in the last 30 days |
| `url` | Repo page |
