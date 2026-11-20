# 03 · Architecture

The shape of every model and how they connect: the talker, its codebook head, the thinker, the turn-state signals and the thinker–talker link.

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=AR) (phase IDs start with `AR`)

## Scope for v0.1

- Talker: Qwen3-0.6B over 80 ms frames, user + own audio streams, inner-monologue text
- Codebook head: depth transformer for RVQ codecs, parallel heads for FSQ codecs
- Thinker: Sarvam 30B (2.4B active) on the CPU
- Text-only thinker → talker coupling

**Not in v0.1:**

- Hidden-state coupling adapters (v0.2)
- Course 120B slice as the thinker (v0.2, depends on the course run)

## What to expect

- The talker shape is well trodden (Moshi pattern) and low risk
- Coupling is the novel part and the main design risk
- A 2B talker such as LFM3-Audio-2B would read ~1 GB every 80 ms at 4 bits, about 12.5 GB/s, which is too much for the i3's shared bus

## Takes in

- Measured budgets (08-performance)
- Codec choice (02-tokenizer)
- Thinker speed (07-quantization)

## Hands over

- Spec sheets and interface definitions → 04-training, 05-post-training, 09-serving

## Phases

### AR1 · Week 1 · Talker spec

Fix layers, width, streams, acoustic delay, context (3–5 min, sliding window) and the codebook head for the chosen codec; bytes and FLOPs per frame. Review 2026 duplex-adaptation recipes (D2, Awaken) for initialisation.

- **Done when:** Spec sheet that fits the talker's 4.4 GB/s share.
- **Needs:** PF1 (same-week handoff), TK1 (same-week handoff)
- **Status:** todo

### AR2 · Week 2 · Thinker and turn state

Confirm Sarvam 30B at the QZ1 setting. Define the talker's turn-state outputs (end-of-turn, backchannel, barge-in), following plug-in turn detectors such as SoulX-Duplug and X2-Turn.

- **Done when:** Thinker fixed for v0.1: ≥ 5 tokens/s on the i3, fits ≤ 14 GB. Turn-state spec written.
- **Needs:** AR1, QZ1, PT1
- **Status:** todo

### AR3 · Week 3 · Coupling interface

Thinker streams its reply plan as text into the talker's monologue slot; turn-state goes back; the thinker drafts while the user is still talking. Compare with 2026 designs for linking duplex models to external LLMs (Context Spanning, MoshiRAG).

- **Done when:** Protocol spec and a working text-coupled loop on a T4.
- **Needs:** AR2, TK2
- **Status:** todo

### AR4 · Week 4 · Review and v0.2 design

Use week-3 results to decide v0.2: adapters, five-language duplex, bigger voice set.

- **Done when:** Architecture note with v0.2 decisions.
- **Needs:** AR3, TR3, EV3
- **Status:** todo

## Folder layout

Create a subfolder the first time you need it.

```
03-architecture/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
└── reports/      one file per phase: AR1.md, AR2.md, AR3.md, AR4.md
```

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on 2026-11-20. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
