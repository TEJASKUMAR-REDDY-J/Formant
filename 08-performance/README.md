# 08 · Performance

Two things: training speed on T4s, and real-time speed on the i3 (80 ms frame deadline, thinker at ≥ 5 tokens/s).

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=PF) (phase IDs start with `PF`)

## Scope for v0.1

- Baselines on both machines
- Training speed-ups
- Runtime speed for talker, codec and thinker
- Both models together, sustained

**Not in v0.1:**

- EAGLE3-style draft head for the thinker (v0.2)

## What to expect

- T4 has no FlashAttention-2, so use PyTorch SDPA; aim for 1.5–2× over the naive baseline
- The iGPU and CPU share one 20.8 GB/s bus; running both together is the real limit
- Heat and throttling show up in 30-minute runs

## Takes in

- Specs (03-architecture)
- Quantised models (07-quantization)

## Hands over

- Budgets and measurements → every section

## Phases

### PF1 · Week 1 · Baselines

Bandwidth (done: 20.8 GB/s). OpenVINO step time on the UHD 620 for a dense 0.6B model and for an MoE with the same active size (expert dispatch); llama.cpp tokens/s for Sarvam 30B; T4 training tokens/s for Qwen3-0.6B.

- **Done when:** Baseline sheet every later number is compared to.
- **Needs:** nothing
- **GPU:** 2 T4-hours
- **Status:** doing

### PF2 · Week 2 · Training speed

Sequence packing, SDPA, chunked cross-entropy, gradient checkpointing, DDP on 2× T4, 8-bit AdamW.

- **Done when:** ≥ 1.5× PF1 tokens/s with an unchanged loss curve.
- **Needs:** TR1, PF1
- **GPU:** 5 T4-hours
- **Status:** todo

### PF3 · Week 3 · Runtime speed

Talker int8 on the iGPU with KV cache and static shapes; thinker thread pinning and incremental prefill.

- **Done when:** Talker + head + codec ≤ 60 ms per 80 ms frame; thinker ≥ 5 tokens/s.
- **Needs:** QZ2, AR2, QZ3 (same-week handoff)
- **Status:** todo

### PF4 · Week 4 · Sustained run

Both models live for 30 minutes; throttle the thinker to protect the frame deadline; record temperatures.

- **Done when:** < 1% missed frames over 30 minutes.
- **Needs:** PF3, SV3
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
08-performance/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
└── reports/      one file per phase: PF1.md, PF2.md, PF3.md, PF4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
