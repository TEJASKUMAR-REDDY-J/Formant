# QZ1 · Thinker sweep

**Status:** in progress. Part 1 (feasibility from the published config and file sizes) is done. Part 2 (quality and measured speed) needs the model files: about 13 GB for the laptop and 26 GB for the Q6_K reference. Nothing has been downloaded.

## What was done

- Computed Sarvam 30B's RAM and bytes read per token for nine recipes from its own `config.json` ([script](../scripts/thinker_budget.py), [config](../configs/sarvam-30b.json)).
- Read the sizes of every published GGUF from the Hub ([gguf-sizes.json](../configs/gguf-sizes.json)).

## How it was checked

The parameter count computed from the config matches the published safetensors total (32,152,650,368) to within 0.1%; the script asserts this on every run.

## Result

Calculated, not measured. Tokens/s is the bandwidth bound: real speed is lower.

| Recipe | RAM | Read per token | Tokens/s at the planned 5.3 GB/s | Tokens/s with the whole bus (20.8) |
|---|---|---|---|---|
| Uniform Q4_K, head Q6 | 18.4 GB ✗ | 2.22 GB | 2.4 | 9.4 |
| Uniform IQ3_XXS, head Q6 | 12.8 GB | 1.79 GB | 3.0 | 11.6 |
| Mixed: experts IQ3_XXS, attention and shared Q6, head Q6 (the plan's recipe) | 13.4 GB | 2.24 GB | 2.4 | 9.3 |
| Mixed, head Q4 | 13.1 GB | 1.97 GB | 2.7 | 10.6 |
| Uniform IQ3_XXS, vocabulary cut by script to 186k, head Q4 | 12.3 GB | 1.34 GB | 4.0 | 15.6 |
| **Uniform IQ3_XXS, vocabulary trimmed to 80k, head Q4** | **11.9 GB** | **1.09 GB** | **4.9** | **19.0** |
| Mixed, trimmed to 80k, head Q4 | 12.3 GB | 1.55 GB | 3.4 | 13.4 |

**What this changes in the plan**

1. **The output head was missing from the speed estimate.** The "2.4B active" figure leaves out the 262,144 × 4,096 output head: 1.07B parameters read for every token, so 3.45B in all. The plan's "~5 tokens/s at 3.5 bits" does not hold; untrimmed recipes give 2.4–3.0.
2. **Trimming the thinker's vocabulary is the biggest lever.** 80k is a target, not a result: TK1's audit shows 186k tokens survive a cut by script alone, so reaching 80k needs a frequency cut on a corpus. Trimming must keep byte fragments and special tokens.
3. **Multi-token prediction is not available.** The config has no MTP layers, so `--spec-type draft-mtp` does not apply. N-gram speculation still does.
4. **Keeping attention at Q6 costs speed.** Attention and shared experts are read on every token; moving them from IQ3 to Q6 adds 0.45 GB per token. Their precision is a quality–speed trade the KL-divergence run must settle.
5. **Most of the planned sweep does not fit 14 GB.** Published sizes: Q3_K_M 15.7, IQ3_S 14.3, IQ4_XS 17.5, Q4_K_M 19.6 GB. Those that fit: IQ3_XS 13.6, IQ3_XXS 12.8, Q2_K 12.2, IQ2_M 11.1. The official repository ships only Q4_K_M.

## What changes next

1. Confirm the download (about 13 GB on F:, and 26 GB on Kaggle for the reference).
2. Sweep IQ3_XXS, IQ3_XS and Q2_K with an Indic importance matrix; KL divergence per language against Q6_K. The importance matrix needs text, so it waits for the data go-ahead.
3. Measure real tokens/s on the i3, alone and beside the talker.
4. Vocabulary trim experiment with TK2.

**T4-hours used:** 0
