# PF1 · Baselines — week 1 plan

**Goal:** measure every number the rest of the plan depends on, on the real machines, before anyone optimises.
**Done when:** the baseline sheet exists and every later number is compared to it.
**Needs:** nothing. **GPU:** 2 T4-hours.

## Laptop (i3-10110U, UHD 620, 24 GB DDR4)

| Measure | How | Feeds |
|---|---|---|
| Memory bandwidth | Done: 20.8 GB/s copy. Add read-only (STREAM triad), and CPU + iGPU at the same time. | All budgets |
| Dense talker step | Qwen3-0.6B, OpenVINO GenAI, int4 and int8, batch 1, KV cache, static shapes: ms per token on the **GPU** and on the CPU | AR1 |
| **MoE talker step** | A random-weight **Qwen2-MoE** config with AR1's shape (28 layers, d = 1024, 1 shared expert of 1,536 + 32 routed of 384, top-4), exported with optimum-intel at int4: ms per token on the GPU and on the CPU | AR1 go/no-go |
| Codec decoder | Each TK1 candidate's decoder, OpenVINO fp16, streaming: ms per 80 ms frame | TK1, QZ2 |
| Thinker | Sarvam 30B GGUFs from QZ1 with llama-bench: generation and prefill tokens/s, 2–4 threads | QZ1, SV1 |
| Contention | Talker and thinker benchmarks run together; the slowdown of each | PF4, SV3 |
| Thermals | 30-minute sustained run: CPU clock, package temperature, iGPU clock | PF4 |

- **Every run uses the same machine setup:** on mains power, Windows "Best performance", background apps closed, OpenVINO 2026.4, llama.cpp release build (AVX2).
- **Known gap:** OpenVINO 2026.4 lists MoE support for CPUs and **Xe** GPUs; the UHD 620 is Gen9.5. The MoE row answers whether that matters.

## Kaggle (2× T4)

| Measure | How | Feeds |
|---|---|---|
| Training throughput | Qwen3-0.6B at seq 2,048, fp16, SDPA, with and without `torch.compile` and fused cross-entropy: tokens/s per T4 and MFU | TR1, TR2 |
| MoE overhead | The ~1.4B upcycled shape at reduced depth, sort-and-loop dispatch vs ScatterMoE | TR2 |
| Codec encode | Hours of audio per T4-hour per codec | DA2 |

## Efficiency

- **One script per machine.** It writes JSON to `08-performance/reports/baseline-v1.json`, so every later week reruns the same script and diffs the results.
- **The random-weight MoE avoids waiting for a trained model.** Dispatch speed depends on shapes, not on the weight values.

## Week

| Day | Work |
|---|---|
| Mon | Laptop setup and bandwidth; dense talker step |
| Tue | MoE step on GPU and CPU (the AR1 question) |
| Wed | Codec decoders for TK1; thinker with QZ1 |
| Thu | Contention and thermals; Kaggle throughput |
| Fri | `reports/PF1.md` + `baseline-v1.json` |

## Decision it unlocks

If the MoE step is more than 1.3× the dense step on the UHD 620, AR1 keeps the dense talker for v0.1, and MoE moves to v0.2 behind a custom dispatch kernel.
