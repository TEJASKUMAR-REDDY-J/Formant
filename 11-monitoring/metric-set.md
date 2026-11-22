# Metric set (v0)

Frozen names. Every run logs these through `src/formant/metrics.py`, once per 50 steps. MO2's alarms read them.

| Name | Meaning |
|---|---|
| `loss/audio`, `loss/codebook_<k>` | Mean cross-entropy over valid frames, all codebooks and each one |
| `loss/text` | Monologue loss over frames that carry text |
| `loss/lang_<xx>` | Audio loss per language; `<xx>` is hi, en, bn, mr, ta, te or hi-en |
| `opt/lr`, `opt/grad_norm`, `opt/loss_scale`, `opt/overflows` | Optimiser state |
| `codes/entropy_<k>` | Entropy of predicted codes over the window, 0 (one code) to 1 (uniform). Falling towards 0 means collapse. |
| `moe/max_over_mean`, `moe/dead_experts` | Expert load; dead = under 10% of the mean load |
| `moe/router_entropy` | 0 to 1 |
| `moe/use_<xx>` | Share of routed tokens per expert, per language (a list; kept in the JSONL file) |
| `data/share_<xx>`, `epoch/<xx>` | What the sampler actually served |
| `speed/frames_per_s`, `speed/step_s`, `speed/data_wait_s` | Throughput |
| `memory/peak_gb` | CUDA only |
| `run/*` | Once, at step 0: config, commit, manifest version, tokenizer hash, seed, resume step |

Sinks: a JSONL file always; Trackio when it is installed (`trackio_sink`).

Routing statistics are sampled on one micro-batch per step. Everything accumulates on the device and is read back once per 50 steps.
