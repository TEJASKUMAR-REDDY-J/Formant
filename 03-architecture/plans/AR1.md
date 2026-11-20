# AR1 · Talker spec — week 1 plan

**Goal:** fix the talker's shape, so that its active bytes per frame fit the talker's 4.4 GB/s share of the bus and its total size is ≤ 1.5 GB at int8. Keep a dense fallback.
**Needs:** ~PF1 (UHD 620 timings), ~TK1 (codec). **GPU:** none.

## Draft spec (MoE talker, upcycled from Qwen3-0.6B)

| Part | Spec | Source / reason |
|---|---|---|
| Backbone | 28 layers, d = 1024, 16 query / 8 KV heads × 128, RoPE, RMSNorm, SwiGLU | Qwen3-0.6B, unchanged |
| Expert layout | Layers 0–1 dense; layers 2–27 MoE | Dense early layers keep training stable (DeepSeek practice) |
| Experts per MoE layer | 1 shared expert, 1,536 wide (the first half of the dense FFN) + 32 routed experts, 384 wide (the other half cut into 4 slices, each copied 8× with 1% noise), top-4 | Active FFN width = 3,072 = the dense model, so compute and bytes match the dense talker (Qwen1.5-MoE-style fine-grained upcycling) |
| Router | Linear 1024 → 32, sigmoid scores, top-4 normalised, bias-based balancing with no auxiliary loss, small per-sequence balance term; runs in fp32 | DeepSeek-V3; Qiu et al. 2025 (global-batch balancing) |
| Streams per 80 ms frame | Input = sum of embeddings: own 8 codes + user 8 codes + 1 inner-monologue text token | Moshi multi-stream |
| Outputs per frame | Monologue text token (40k head, tied); own codes through the codebook head; turn-state head (end-of-turn, backchannel, barge-in, hold) | Moshi + AR2 |
| Acoustic delay | Codebooks 1–7 lag codebook 0 by 1 frame | Moshi; better audio at no runtime cost |
| Codebook head | **RVQ codec (Mimi):** depth transformer, 4 layers, d = 512, per-codebook in/out projections (~30M params). **FSQ codec (LiquidCodec):** 12 parallel heads, no depth transformer. | TK1 decides |
| Attention and context | 24 layers use a 60 s sliding window (750 frames); 4 layers (6, 13, 20, 27) see the full 3 min (2,250 frames); KV cache int8 | Keeps KV reads at ~55 MB per frame, about 0.7 GB/s |
| Initialisation | Backbone and FFN from Qwen3-0.6B; audio tables new, initialised from code statistics; text table = the trimmed TK2 table | Upcycling; D2/Awaken recipes reviewed for keeping text ability while going duplex |

## Budget

| | Params | Bytes per frame | GB/s at 12.5 Hz |
|---|---|---|---|
| Attention (int4 weights) | 176M | 88 MB | 1.1 |
| FFN, active (int4) | 264M | 132 MB | 1.65 |
| Text head (int8) | 41M | 41 MB | 0.5 |
| KV cache reads (int8) | | 55 MB | 0.7 |
| **Talker total** | **~1.44B total, ~0.48B active** | **~316 MB** | **~4.0 of 4.4** |
| Depth transformer, Mimi only (int4, 8 steps) | ~30M | 120 MB | 1.5 of 2.5 |

- **Size:** ~1.44B params × 1 byte = 1.44 GB at full int8, or ~0.85 GB with int4 experts, inside the ≤ 1.5 GB limit.
- **Compute:** ~1 GFLOP per frame, about 12.5 GFLOP/s. That is far below the UHD 620's fp16 peak, so the talker is **bandwidth-bound**. The open risk is expert-dispatch overhead, not FLOPs.
- **Dense fallback:** the same spec with a dense 3,072-wide FFN has identical active bytes. It is used if PF1 shows MoE dispatch missing the frame.

## Runtime evidence to collect (with PF1)

- **OpenVINO 2026.4 supports MoE on CPU and on Intel Xe GPUs** (validated on Qwen3-30B-A3B and Arc A770). The UHD 620 is Gen9.5, not Xe, so MoE on it is untested.
- **PF1 tests it** by building a random-weight Qwen2-MoE config with exactly this shape (Qwen2-MoE has a shared expert, so it matches). It is exported with optimum-intel at int4, and its step time is measured on the UHD 620 and on the CPU.

## Week

| Day | Work |
|---|---|
| Mon | Write the spec skeleton; parameter and byte calculator (one script); review D2/Awaken and the Qwen3-Omni talker |
| Tue | Fix streams, delay, turn-state head; draft the context and KV plan |
| Wed | Fold in the TK1 codec choice (depth transformer or parallel heads); hand PF1 the MoE config |
| Thu | Read PF1's dense-vs-MoE step times; settle int4/int8 per tensor with QZ |
| Fri | `reports/AR1.md` with the spec sheet, budget table and dense fallback; hand the config to TR1/TR2 |

## Risks

- **MoE dispatch too slow on Gen9 graphics.** The dense fallback runs on the same data and tables.
- **Sliding-window retrofit.** Qwen3 was pre-trained with full attention; the ~2.5k h pre-training adapts it. If the TR1 smoke runs show damage, use 8 global layers.
