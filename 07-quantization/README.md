# 07 · Quantization

Shrinking every model to fit the laptop's RAM and memory bandwidth, measuring the quality each step costs.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=QZ) (phase IDs start with `QZ`)
- **Branch:** `sec/07-quantization`. Cut feature branches from it and open PRs into it; it merges into `main` when a phase is done ([GUIDELINES.md](../GUIDELINES.md) section 5).

## Scope for v0.1

- Thinker GGUF sweep with Indic calibration
- Codec decoder in OpenVINO on the iGPU
- Talker int8 (int4 where it holds), with calibration covering every expert
- Final quantised bundle

**Not in v0.1:**

- Quantisation-aware training (only if a language drops too far)

## What to expect

- Q4_K_M Sarvam 30B is ~18 GB and does not fit the 14 GB budget; ~3.5 bits does, at ~5 tokens/s before speculation
- Talker int8 is close to free; int4 may hurt audio
- Thinker at ~3.5 bits loses some quality; Indic calibration text matters

## Takes in

- Checkpoints (04, 05)
- Harness (06-evaluation)

## Hands over

- GGUF and OpenVINO files → 08-performance, 09-serving, 12-release

## Phases

### QZ1 · Week 1 · Thinker sweep

Sarvam 30B at Q3_K_M, IQ3_S, IQ4_XS and a mixed MoE recipe (routed experts low-bit; attention, router and shared parts at Q6–Q8) with an Indic importance matrix; KL divergence against a Q6_K reference per language; tokens/s on the i3 alone and under talker load; MTP or n-gram speculative decoding.

- **Done when:** Speed–quality curve; one setting chosen.
- **Needs:** PF1 (same-week handoff), EV1 (same-week handoff)
- **Plan:** [plans/QZ1.md](plans/QZ1.md)
- **Status:** doing

### QZ2 · Week 2 · Codec on the iGPU

Export the chosen codec decoder to OpenVINO fp16; save fp16 reference outputs for every component.

- **Done when:** Decoder runs well inside one 80 ms frame on the UHD 620.
- **Needs:** TK1, PF1
- **GPU:** 1 T4-hours
- **Status:** todo

### QZ3 · Week 3 · Talker int8

NNCF int8 on the week-2 checkpoint (shapes are fixed); calibrate on all six languages so rarely used experts see data; try int4.

- **Done when:** CER within 2 points of fp16 on the probe set.
- **Needs:** TR2, QZ2, TR3 (same-week handoff)
- **GPU:** 2 T4-hours
- **Status:** todo

### QZ4 · Week 4 · Release bundle

Quantise the final talker and tuned thinker; run the full system against the references.

- **Done when:** Every language within 2 CER points of fp16; bundle tagged.
- **Needs:** QZ3, TR4 (same-week handoff), PT4 (same-week handoff)
- **GPU:** 2 T4-hours
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
07-quantization/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
├── plans/        one file per phase, written before the phase starts: QZ1.md, QZ2.md, QZ3.md, QZ4.md
└── reports/      one file per phase: QZ1.md, QZ2.md, QZ3.md, QZ4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
