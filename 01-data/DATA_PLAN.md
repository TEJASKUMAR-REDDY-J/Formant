# Data plan · sharding, storage and training mixtures

How the v0.1 data in [`sources/hf_datasets.csv`](sources/hf_datasets.csv) is cut into shards, stored and mixed for training.

It assumes the talker becomes a **Mixture-of-Experts** model, made by sparse upcycling of Qwen3-0.6B (for example 8 experts, top-2 routing, with a shared expert). That puts it in the same family as the Qwen3-Omni MoE talker. AR1 fixes the exact shape, and nothing below depends on the exact expert count.

## 1. Principles

1. **Hugging Face is the only source and the only store.** Every clip traces to `repo@commit`. Our own data repo on the Hub holds tokens, text and manifests, never raw audio.
2. **Store what training reads, and re-derive the rest.** Speech is kept as codec tokens. Raw audio is re-streamed on demand from a pinned manifest: for test sets, for a codec change, or for the TK3 decoder fine-tune.
3. **Keep scores, not just pass/fail.** Every clip carries its gate scores, so later mixtures can re-weight or tier the data without re-ingesting it.
4. **Tokens are tied to a codec.** Each token tree sits under its codec's hash, and a codec change means a new tree built from the same manifests.
5. **Batches stay language-balanced.** MoE routers learn from what each batch contains, so the sampler controls language ratios. Shard order never does.

## 2. Layout on the Hub

One private dataset repo, `formant-data`, versioned with git tags (`v0.1-r1`, `v0.1-r2`, …):

```
formant-data/
  manifests/                       # source of truth: which clips, from which revision, why kept or dropped
    {source}.parquet               # clip_id, repo, commit, file, offset, split, gate scores, kept, drop_reason
  eval/
    {set}.json                     # repo, commit, files, sha256: pulled on demand, never stored
  tokens/{codec-hash}/             # canonical token shards (~64 MB, ~110 h each)
    {lang}/{source}/train-00000-of-0000N.parquet
    {lang}/{source}/dev-00000.parquet
  dialogue/{codec-hash}/           # two-channel data (DA2)
    {lang}/{synthetic|split-real|pseudo}/train-*.parquet
  aug/{codec-hash}/                # noisy / far-field / echo copies of the user stream (TR4)
    {lang}/train-*.parquet
  text/{lang}/{tokenizer|instruct|seed}-*.parquet
  timing/{indicvoices-conv|seamless}.parquet       # gap, overlap, backchannel events
  mixtures/{stage}.yaml            # sampling weights per stage (section 5)
  CARD.md                          # data card: sources, licences, hours, gate pass rates
```

Directory names carry the information every sampler and dashboard slices by: language, source, codec. The Hub viewer and `datasets.load_dataset(..., data_dir=...)` work on any subtree.

## 3. Shard schema

One row per clip, in Parquet with zstd and ~1k rows per row group:

| Column | Type | Why |
|---|---|---|
| `clip_id`, `source`, `source_commit` | string | Traces back to the exact source file |
| `lang`, `style`, `split` | string | Sampling and contamination checks |
| `speaker` | string | Salted hash of the source speaker id. Used for speaker-disjoint splits and speaker-coherent packing. |
| `gender`, `age_group`, `region` | string | Balance checks; probe prompts per group |
| `duration_s`, `n_frames` | float32, int32 | Bucketing and packing |
| `codes` | list<uint16> | Codebook-major `[K × T]` codes (K = 8 for Mimi) |
| `text_verbatim`, `text_norm` | string | Inner-monologue text, and the normalised text for CER |
| `word_start`, `word_end` | list<uint32> | Frame index of every word, from forced alignment. The talker needs text aligned to audio frames. |
| `lid`, `snr_db`, `c50_db`, `dnsmos`, `cer` | float16 | Gate scores, kept for tiers and re-weighting |
| `tier` | uint8 | 1 = studio/clean, 2 = good, 3 = passed the gates |

**Size:** ~0.6 MB per hour with the alignments; the 2.57k h kept come to about 1.5 GB.

**Shard target:** ~64 MB, about 110 h. Every (language, source) has at least two shards, and the whole set is about 35 shards.

## 4. Ingest sharding (DA2)

The work unit is **one source Parquet file**, which keeps jobs idempotent and resumable across Kaggle's 12-hour sessions:

```
for each source file not yet in manifests/:            # the manifest is the job ledger
    stream it → VAD segment 2–30 s → gates (LID, SNR/C50, DNSMOS, length, two-ASR CER)
    → dedup → resample 24 kHz, loudness-normalise → codec encode on T4, length-bucketed batches
    → forced alignment (CTC aligner) → write part file → upload → append manifest rows
weekly: compact part files into ~64 MB shards, shuffled within (lang, source)
```

- **Dedup:** IndicVoices-R is a cleaned re-release of IndicVoices clips. When the same (speaker, normalised text) appears in both, keep the IndicVoices-R copy. Exact audio repeats are dropped by hashing the first two codebooks.
- **Contamination:**
  - Speakers are held out across IndicVoices and IndicVoices-R together, because they share speakers.
  - 13-gram text overlap is checked against every test-set transcript (FLEURS, Lahaja, Svarah, Vaani-Benchmark, IN22).
  - Lahaja speakers are checked against IndicVoices, since both come from AI4Bharat.
- **Dev split:** 1% of speakers per (language, source), speaker-disjoint, used for loss tracking and mixture search.
- **Augmentation happens here, not in the dataloader.** Tokens cannot be noised after encoding, so the TR4 copies (noise, far-field, echo leak) are encoded once into `aug/` for ~200 h of **user-stream** audio. The talker's own stream is always clean.

## 5. Training mixtures

### Language ratio: temperature sampling with an epoch cap

Weights follow hours^0.5 (temperature sampling, as in mT5), and no language may repeat more than 4 times (the UniMax cap). The budget is 3 epochs of the 2.47k h of speech, ≈ 7.4k h seen, ≈ 334M frames.

| Language | Kept | Share of speech batches | Hours seen | Epochs |
|---|---|---|---|---|
| Hindi | 800 h | 23% | 1,715 | 2.1 |
| English (Indian) | 400 h | 16.5% | 1,213 | 3.0 |
| Bengali | 300 h | 14% | 1,050 | 3.5 |
| Marathi | 300 h | 14% | 1,050 | 3.5 |
| Tamil | 300 h | 14% | 1,050 | 3.5 |
| Telugu | 300 h | 14% | 1,050 | 3.5 |
| Hinglish | 71 h | 4% | 284 | 4.0 (capped) |

Before TR2 commits to these weights, TR1 runs a small mixture search. It trains 8 runs of the ~50M talker on different weightings and keeps the one with the best worst-language dev loss (a RegMix/DoReMi-style search, ~5 T4-hours).

### Online selection inside each step (OPUS, trial in TR1)

Temperature sampling fixes **how much** of each language the model sees. **OPUS** (Optimizer-induced Projected Utility Selection, arXiv 2602.05400, 2026) chooses **which** clips within that budget, at every step.

**How it works:**
1. The sampler draws a candidate buffer twice the batch size.
2. Each candidate gets a score: its gradient, seen through the optimizer's preconditioner (AdamW's second moments), dot a proxy gradient from data that looks like what we want to be good at.
3. Per-sample gradients come from "ghost" factors (layer input × output gradient), compressed with an m = 8,192 CountSketch.
4. Half the buffer is kept, sampled with a softmax at τ = 0.9 and a redundancy penalty so the batch stays diverse.

**Reported results:**
- about 4.7% extra compute;
- +2.2% average accuracy over random selection on 10 benchmarks;
- 8× less compute to match GPT-2 XL trained on FineWeb;
- Qwen3-8B continued pre-training matching 3B tokens with 0.5B (6×).

**Fitted to Formant:**

| Paper | Formant |
|---|---|
| Proxy built by retrieving pre-training documents close to the benchmark validation sets | Proxy pool = the **dev split** (speaker-disjoint, never the test sets) + tier-1 clips + conversational clips, weighted toward the worst languages in the latest eval |
| Free choice across the whole buffer | **Selection inside each language bucket**, so the temperature ratios and the MoE global-batch balance hold |
| AdamW / Muon preconditioner | AdamW (8-bit states dequantised for scoring) |
| Sketch every layer | Sketch the last 4 blocks + output heads first, to keep the cost down on T4s |

**The catch is cost on T4s.** Scoring needs a forward pass over the whole buffer, so the 4.7% figure may not carry over. TR1 measures it.

**TR1 runs it as an A/B at equal T4-hours:** random vs OPUS on the dense ~50M talker, compared on worst-language dev loss. TR2 adopts it only if it wins after paying its overhead.

**Possible upside:** if OPUS reaches the same dev loss in ~2 epochs instead of 3, pre-training drops by ~30–50 T4-hours, about a quarter of the gap to one Kaggle account. The budget does not count on this until TR1 shows it.

### Stages

| Stage | Plan cell | Mixture | Why |
|---|---|---|---|
| **A. Speech pre-training** | TR2–TR3 | 90% speech (language ratio above; within a language, sources by hours with conversational clips up-weighted 2×), 10% text replay (Sangraha sample) | Learn Indic speech. Text replay keeps the Qwen3 text ability the monologue slot needs. |
| **B. Quality anneal** | last 15% of A | Tier-1 speech only (IndicVoices-R, Rasa, top-DNSMOS Kathbath) + 10% text; learning rate decays to 0 | Finishing on clean data sharpens audio quality (the Llama 3 anneal and Qwen3-Omni's high-quality continued pre-training) |
| **C. Duplex** | TR3 | 50% two-channel dialogue (synthetic + split real), 30% pseudo-duplex, 20% Stage-A replay | Learn turn-taking without forgetting the other languages |
| **D. Robustness** | TR4 | 30% `aug/` user streams over C's mixture | Noise, far-field audio, crosstalk |
| **E. Voice lock** | PT3 | 80% chosen Rasa voice, 20% Stage-C replay | One voice; the replay guards against forgetting |

**Pseudo-duplex** data is two monologue clips from different speakers of the same language, laid on two channels with gaps, overlaps and backchannels sampled from the DA1 timing statistics. It costs nothing to make and gives Bengali, Marathi, Tamil and Telugu turn-taking practice before real dialogue exists for them (the Moshi multi-stream recipe, applied to monologue data).

## 6. Packing and batches

- **Sequences are 2,048 frames (164 s), packed per speaker.** Consecutive clips from the same speaker are joined with 3–8 silence frames, which teaches long-form, voice-consistent speech from short clips. Attention is masked at clip boundaries (document masking).
- **A micro-batch holds one language; the global batch holds the mixture.** On 2× T4 a micro-batch is only a few sequences. Gradient accumulation builds a global batch of ~64 sequences (~131k frames) that matches the stage ratios.
- **MoE load balancing is computed over the global batch, not each micro-batch.** Balancing per micro-batch forces every expert to see every language and blocks specialisation; balancing over the global batch lets experts specialise by language or codebook (Qiu et al., 2025). Use DeepSeek-V3's bias-based balancing without an auxiliary loss, plus a small per-sequence balance term.
- **The sampler is deterministic and resumable.** It is seeded by (run, step), and its state is saved in every checkpoint, so a killed Kaggle session resumes on the exact next batch.
- **There is no streaming dataloader.** All tokens (~1.5 GB) download to Kaggle in about a minute and sit in RAM. Packing builds `packed/{stage}/{lang}.bin` (uint16 memmap) plus an index in a few minutes per session.

## 7. What MoE changes for data

| Concern | What we do |
|---|---|
| Too little data for an MoE trained from scratch (334M frames) | **Upcycle** from the dense Qwen3-0.6B: experts start as copies of its FFN. Only the router and the expert divergence need data. |
| Experts collapse onto Hindi, the largest language | Temperature sampling + global-batch balancing; MO logs **expert use per language** and router entropy each eval |
| Experts never specialise | Single-language micro-batches + global-batch balancing |
| A stage shift (A → C) reshuffles the experts | 20% replay in every later stage; MO2 alarm on sudden routing shifts |
| Expert use depends on sample tags | Every packed sequence carries `lang`, `source`, `tier` in its index, so router stats can be sliced |

## 8. Storage after this plan

| Item | Stored |
|---|---|
| Speech tokens + alignments, 2.57k h | ~1.5 GB |
| Two-channel dialogue tokens, ≥ 250 h × 2 channels | ~0.3 GB |
| Augmented user streams, ~200 h | ~0.1 GB |
| Text (tokenizer sample, instruction, Hinglish seeds) | ~3 GB |
| Timing tables | ~0.1 GB |
| Manifests (training clips + test sets) | ~0.05 GB |
| **Total** | **~5 GB**, against 1.76 TB raw in our languages |

## 9. References

- **Moshi** (Défossez et al., 2024): multi-stream duplex data, inner-monologue text aligned to frames, synthetic dialogues.
- **Qwen3-Omni** (2025): MoE talker; staged training from broad data to a high-quality continued pre-train; speaker fine-tune last.
- **UniMax** (Chung et al., 2023): language sampling with an epoch cap.
- **DoReMi** (Xie et al., 2023) and **RegMix** (Liu et al., 2024): choosing mixtures with small proxy runs.
- **Sparse upcycling** (Komatsuzaki et al., 2022): building an MoE from a dense checkpoint.
- **DeepSeek-V3** (2024): load balancing without an auxiliary loss.
- **OPUS** (arXiv 2602.05400, 2026): per-step data selection in the optimizer's update space.
- **Qiu et al., 2025**, "Demons in the Detail": global-batch load balancing lets experts specialise.
- **Emilia-Pipe** (He et al., 2024): speech preprocessing (separation, VAD, quality scoring).
- **Llama 3** (2024): annealing on high-quality data, and document masking for packed sequences.
