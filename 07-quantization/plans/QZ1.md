# QZ1 · Thinker sweep — week 1 plan

> **Superseded in part:** [reports/QZ1.md](../reports/QZ1.md) corrects the speed estimate, MTP speculation and the list of quantisations.

**Goal:** pick the Sarvam 30B quantisation that fits ≤ 14 GB, runs at ≥ 5 tokens/s on the i3, and keeps Indic quality.
**Done when:** the speed–quality curve is published and one setting is chosen.
**Needs:** ~PF1 (i3 timing), ~EV1 (metrics). **GPU:** none counted (Kaggle T4s only compute reference logits).

## Why this is tight

- **Size:** ~30B weights at Q4_K_M (~4.8 bits) is ~18 GB, which **does not fit** the 14 GB thinker budget. ~3.5 bits is ~13 GB.
- **Speed:** each token reads the ~2.4B active parameters. At 3.5 bits that is ~1.05 GB per token, and the thinker's ~5.3 GB/s share gives **~5 tokens/s**. Speed comes from fewer bits per active weight and from speculative decoding.

## Sweep

| Setting | Idea |
|---|---|
| Q3_K_M, IQ3_S, IQ3_XXS | Plain low-bit baselines, with an **Indic importance matrix** |
| IQ4_XS | Quality ceiling that still nearly fits |
| **Mixed MoE recipe** | Routed experts at IQ3_S; attention, shared expert, router, embeddings and output at Q6_K/Q8_0 (llama.cpp `--tensor-type` overrides, Unsloth-Dynamic style) |
| KV cache q8_0 | Halves KV memory and reads; quality check |

- **Importance matrix:** ~300k tokens covering all six languages, from Sangraha plus spoken-style replies from PT1. It is kept separate from the evaluation text.

## Measures

| Measure | How |
|---|---|
| KL divergence vs a Q6_K reference, per language | `llama-perplexity --kl-divergence`. The Q6_K reference fits in 2× T4 (32 GB). KLD catches damage that perplexity hides. |
| Perplexity per language | Held-out Sangraha slice |
| MILU subset + spoken-style compliance | PT1 set |
| Generation and prefill tokens/s on the i3 | `llama-bench`, 3 threads, `--mlock`; once alone, and once with a bandwidth load running on the iGPU that mimics the talker |

## Speed-ups to test

- **Multi-token prediction (MTP) speculative decoding.** llama.cpp has `--spec-type draft-mtp` (2026), reported at ~2× for models that ship MTP layers. Check whether the Sarvam 30B GGUF has them.
- **N-gram / prompt-lookup speculation** (`ngram-mod`) as a fallback that needs no extra weights.
- **Thread placement:** 3 threads for the thinker, pinned; one hardware thread left for audio I/O and the iGPU driver.

## Week

| Day | Work |
|---|---|
| Mon | Pull or convert the GGUFs; build the importance-matrix text |
| Tue | Importance matrix on Kaggle; quantise the sweep |
| Wed | KL divergence + perplexity on Kaggle; MILU subset |
| Thu | i3 speed with PF1, alone and under talker load; MTP / n-gram trials |
| Fri | `reports/QZ1.md`: curve, chosen setting, handed to SV1, PT1 and AR2 |

## Decision rule

1. **Fits ≤ 14 GB** with an 8k context.
2. **≥ 5 tokens/s under talker load,** speculation included.
3. **Smallest mean KL divergence,** with no language more than 2× the best.
