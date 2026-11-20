# 09 · Serving

The real-time program on the laptop, not a server: audio in and out every 80 ms, echo cancellation, talker on the iGPU, thinker on the CPU.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=SV) (phase IDs start with `SV`)

## Scope for v0.1

- Cascade floor (recogniser → thinker → TTS), the fallback for all languages
- Duplex audio loop with WebRTC AEC3
- Talker in the loop with barge-in
- Coupled agent, one-command launch

**Not in v0.1:**

- Windows installer and phone port (v0.2)

## What to expect

- Echo is the biggest unknown: in full duplex the laptop hears its own speakers; demos fall back to a headset
- The cascade is the safety net and the baseline every later build must beat

## Takes in

- Quantised models (07)
- Runtime speed work (08)
- Coupling spec (03)

## Hands over

- The demo and the runtime → 06-evaluation, 12-release

## Phases

### SV1 · Week 1 · Cascade floor

Offline recogniser (IndicConformer class) → Sarvam 30B in llama.cpp → open Indic TTS (Indic Parler-TTS or IndicF5), push-to-talk, all five languages.

- **Done when:** ≤ 1.5 s p50 response latency on the i3.
- **Needs:** PF1 (same-week handoff), QZ1 (same-week handoff)
- **Status:** todo

### SV2 · Week 2 · Duplex audio loop

80 ms frame clock, mic and speaker I/O, WebRTC AEC3, codec decoder on the iGPU, replayed talker output to test the loop.

- **Done when:** Plays and listens at once on laptop speakers without hearing itself.
- **Needs:** SV1, QZ2 (same-week handoff)
- **Status:** todo

### SV3 · Week 3 · Talker in the loop

int8 talker on the iGPU; barge-in stops speech within 300 ms; falls back to the cascade when frames are late.

- **Done when:** Live Hindi duplex conversation on the i3.
- **Needs:** SV2, QZ3 (same-week handoff), PF3 (same-week handoff)
- **Status:** todo

### SV4 · Week 4 · Coupled agent

Thinker streams into the talker live; one command starts everything; 30-minute soak.

- **Done when:** Full offline conversation recorded for the release video.
- **Needs:** SV3, PT4 (same-week handoff), PF4 (same-week handoff)
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
09-serving/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
└── reports/      one file per phase: SV1.md, SV2.md, SV3.md, SV4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
