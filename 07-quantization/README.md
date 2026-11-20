# 07 · Quantization

Shrinking every model to fit the laptop's RAM and memory bandwidth, measuring the quality each step costs.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=QZ) (phase IDs start with `QZ`)

## Scope for v0.1

- Thinker GGUF sweep with Indic calibration
- Codec decoder in OpenVINO on the iGPU
- Talker int8 (int4 where it holds)
- Final quantised bundle

**Not in v0.1:**

- Quantisation-aware training (only if a language drops too far)

## What to expect

- Talker int8 is close to free; int4 may hurt audio
- Thinker at ~3.5 bits loses some quality; Indic calibration text matters

## Takes in

- Checkpoints (04, 05)
- Harness (06-evaluation)

## Hands over

- GGUF and OpenVINO files → 08-performance, 09-serving, 12-release

## Phases

### QZ1 · Week 1 · Thinker sweep

Sarvam 30B at Q4_K_M, Q3_K_M and IQ3 with an Indic importance matrix; tokens/s on the i3 and Indic quality.

- **Done when:** Speed–quality curve; one setting chosen.
- **Needs:** PF1 (same-week handoff), EV1 (same-week handoff)
- **Status:** todo

### QZ2 · Week 2 · Codec on the iGPU

Export the chosen codec decoder to OpenVINO fp16; save fp16 reference outputs for every component.

- **Done when:** Decoder runs well inside one 80 ms frame on the UHD 620.
- **Needs:** TK1, PF1
- **GPU:** 1 T4-hours
- **Status:** todo

### QZ3 · Week 3 · Talker int8

NNCF int8 on the week-2 checkpoint (shapes are fixed); try int4.

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
└── reports/      one file per phase: QZ1.md, QZ2.md, QZ3.md, QZ4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
