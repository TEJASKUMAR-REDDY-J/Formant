# MO1 · Training metrics — week 1 plan

**Goal:** every run logs the same metric set, so runs can be compared and MO2's alarms have something to watch.
**Done when:** every run logs the same metric set.
**Needs:** ~IN1 (tracking backend). **GPU:** none.

## Backend

**Trackio** (Hugging Face):
- wandb-compatible `init/log/finish`;
- writes locally, then syncs to a private Hub Space;
- free, with the data on the Hub alongside the checkpoints.

## Metric set (logged every 50 steps unless noted)

| Group | Metrics |
|---|---|
| Loss | Total; text (monologue); **per codebook** (0–7); **per language** (from each sequence's `lang` tag); turn-state head |
| Optimisation | Learning rate; grad norm (total and per block group); fp16 loss scale; overflow count |
| MoE | Expert load per layer (max/mean); **expert use per language** (32-bin histogram per language, every 500 steps); router entropy; balance-bias values; tokens per expert |
| Codebooks | Predicted-code entropy per codebook (falling entropy means collapse) |
| Throughput | Frames per second; tokens per second; MFU; step time; data-wait time |
| Memory | Peak allocated / reserved per GPU |
| Data | Epoch per language; current shard; share of each mixture bucket actually seen |
| Run identity (once) | Config, git commit, data manifest version, tokenizer hash, seed |

## Efficiency

- **Statistics are accumulated on the GPU and synced every 50 steps,** never every step, so logging does not stall the T4s.
- **Per-language loss uses a single scatter-add over the batch's language ids.** It needs no extra forward pass.
- **Expert histograms are sampled on one micro-batch** every 500 steps.

## Code

- **One logger module, `src/formant/metrics.py`.** It is shared by TR, PT and the data jobs, so it is the first shared code under GUIDELINES section 4.
- **The metric names are frozen** in `11-monitoring/metric-set.md`. MO2's alarms read those names: NaN, loss spikes, codebook-entropy drops, dead or collapsed experts.

## Week

| Day | Work |
|---|---|
| Mon | Trackio Space; metric names frozen |
| Tue | `metrics.py` with per-language and per-codebook losses |
| Wed | MoE statistics; wired into TR1 |
| Thu | Dashboard layout: one page per run, one comparison page |
| Fri | `reports/MO1.md`; TR1 runs visible on the dashboard |
