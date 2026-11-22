# TR1 · Smoke runs — week 1 plan

> **Superseded in part:** [reports/TR1.md](../reports/TR1.md) corrects the upcycling recipe and the order of work.

**Goal:** prove the training stack on a ~50M talker, dense and MoE, before TR2 spends real T4-hours. Also fix the data-mixture weights.
**Done when:** loss falls on every codebook; experts stay balanced; resume reproduces the curve; mixture weights are fixed; OPUS adopted or dropped, with numbers.
**Needs:** ~IN1 (runner), ~MO1 (metrics). **GPU:** 10–12 T4-hours.

## Setup

- **Model:**
  - **Dense:** 8 layers, d = 512, 8 heads.
  - **MoE:** the same, with 1 shared + 16 routed experts, top-2. It mirrors the AR1 pattern at small scale.
- **Data:** FLEURS **train** split (open, ~10 h per language), Mimi-tokenised in one T4-hour. Smoke weights are thrown away, so this never touches the test splits. Thursday's mixture search uses the DA1 pilot tokens.
- **Sequence:** 2,048 frames, packed per speaker with document masking (01-data/DATA_PLAN.md).

## Efficiency stack for T4 (sm75: fp16, no bf16, no FlashAttention-2)

| Choice | Why |
|---|---|
| PyTorch SDPA (memory-efficient kernel) | Best attention on Turing |
| fp16 AMP with dynamic loss scaling; router, softmax and losses in fp32; router z-loss 1e-3 | Stable MoE in fp16 (ST-MoE) |
| `torch.compile` on the block | Triton runs on sm75; fuses the norms and SwiGLU |
| Liger-style fused linear + cross-entropy for the 40k text head and codebook heads | Never materialises full logits; large memory saving |
| Fused AdamW, or 8-bit AdamW (bitsandbytes) for the MoE | Optimizer memory |
| Activation checkpointing only if memory forces it | Costs ~30% speed |
| MoE dispatch: sort tokens by expert + per-expert GEMM, dropless; ScatterMoE (Triton) if it runs on sm75 | Measure both |
| DDP on 2× T4, gradient accumulation to the global batch | Simple and reliable; ZeRO-2 waits for TR2 at full size |
| WSD schedule (warmup–stable–decay) | Resume-friendly; the decay doubles as the DATA_PLAN quality anneal |

## Checks

| Check | Pass when |
|---|---|
| fp16 stability | No overflow streaks; the loss scale settles |
| Loss per codebook | All 8 fall; codebook 0 falls fastest |
| Router | Max/mean expert load ≤ 1.5 over the global batch; no dead experts; router entropy steady |
| Resume | Kill the run mid-epoch, then restart from the Hub checkpoint (model, optimizer, scaler, sampler, RNG). The loss curve matches within 1%. |
| Throughput | Frames per second per T4, dense vs MoE; MoE overhead ≤ 30% |

## Mixture search (Thursday, ~5 T4-hours)

- **Runs:** 8 runs of the dense ~50M model, ~0.5 T4-hour each, on the DA1 pilot tokens. Weights are sampled around the DATA_PLAN prior: hi 23 / en 16.5 / bn, mr, ta, te 14 each / Hinglish 4.
- **Pick:** the weights with the best **worst-language** dev loss (a RegMix/DoReMi-style search). If no run beats the prior by more than noise, keep the prior.

## OPUS A/B (Friday, ~2 T4-hours)

Online data selection per step (01-data/DATA_PLAN.md, section 5): score a 2× candidate buffer, keep the best half.

| Setting | Value |
|---|---|
| Buffer | 2× the micro-batch, drawn from one language bucket |
| Score | Per-sample gradient sketches (ghost factors, CountSketch m = 8,192) of the last 4 blocks + heads, preconditioned by AdamW's second moments, dot the proxy gradient |
| Proxy | Dev-split clips (speaker-disjoint), tier-1 and conversational, refreshed every 500 steps |
| Keep | 50%, softmax sampling at τ = 0.9 with a redundancy penalty |
| Compare | Random vs OPUS at **equal T4-hours**, not equal steps; worst-language dev loss and per-codebook loss |

**Adopt for TR2 only if OPUS wins after paying its overhead.** Also report the overhead itself; the paper says ~4.7%, but a T4 with a full candidate forward pass may cost more.

## Week

| Day | Work |
|---|---|
| Mon | Runner from IN1; tokenise FLEURS train; dense model trains |
| Tue | MoE variant; dispatch benchmark; fp16 and router checks |
| Wed | Kill-and-resume test; metric set from MO1 wired in |
| Thu | Mixture search on the DA1 pilot tokens |
| Fri | OPUS A/B; `reports/TR1.md`: curves, throughput, chosen weights, OPUS verdict, TR2 config draft |

## Risks

- **ScatterMoE or `torch.compile` fails on sm75.** Fall back to the plain sort-and-loop dispatch, which is slower but correct.
- **The pilot tokens arrive late.** The mixture search moves to Monday of week 2, before TR2 launches.
