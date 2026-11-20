# 11 · Monitoring

Watching training, data and the live laptop runtime so problems show up in hours, not weeks.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=MO) (phase IDs start with `MO`)

## Scope for v0.1

- Training metrics
- Alarms and rollback
- Listening probes
- Runtime telemetry

**Not in v0.1:**

- Paid monitoring tools

## What to expect

- Codebook collapse and fp16 overflow are the two silent killers
- Free tiers (W&B or TensorBoard on the Hub) are enough

## Takes in

- Runs (04, 05)
- Harness (06)
- Runtime (09)

## Hands over

- Dashboards and alerts → every section

## Phases

### MO1 · Week 1 · Training metrics

Loss per codebook, text loss, loss per language, grad norm, fp16 loss scale and overflows, tokens/s, memory; expert use per language, router entropy and load imbalance.

- **Done when:** Every run logs the same metric set.
- **Needs:** IN1 (same-week handoff)
- **Status:** todo

### MO2 · Week 2 · Alarms

Auto-stop on NaN, loss spikes, falling codebook entropy and dead or collapsed experts; roll back to the last good checkpoint; data-gate pass-rate dashboard.

- **Done when:** A deliberately broken run is stopped automatically.
- **Needs:** MO1, TR2 (same-week handoff)
- **Status:** todo

### MO3 · Week 3 · Listening probes

Every N steps generate 10 fixed prompts per language; auto CER and speaker similarity; audio on the dashboard.

- **Done when:** Probe trends visible for TR3.
- **Needs:** MO2, EV2
- **Status:** todo

### MO4 · Week 4 · Runtime telemetry

Missed frames, latency p50/p95, CPU clock and temperature, leftover echo, logged for every demo session.

- **Done when:** Telemetry attached to the release demo.
- **Needs:** MO3, SV3
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
11-monitoring/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
└── reports/      one file per phase: MO1.md, MO2.md, MO3.md, MO4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
