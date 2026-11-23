# AR1 · Talker spec

**Status:** in progress. The budgets are computed and PF1 has measured the two shapes. **The dense-or-MoE decision is the team's;** the codec head waits for TK1.

## What was done

- [`scripts/budget.py`](../scripts/budget.py): parameters, RAM and bytes per 80 ms frame for any spec in [`configs/`](../configs/).
- Five specs: dense with an int4 body (fp16 or int8 KV cache) and with an int8 body, and the MoE with int8 or int4 routed experts.

## How it was checked

The dense budget reproduces Qwen3-0.6B's published 751.6M parameters (tied head counted twice on the Hub); the script asserts it on every run. Speed comes from PF1's random-weight graphs on this laptop, in [`08-performance/reports`](../../08-performance/reports).

## Result

| Spec | Parameters | RAM | Talker reads | Fits 4.4 GB/s | iGPU kernel time, 28 layers (PF1) |
|---|---|---|---|---|---|
| Dense, int4 body, int8 KV | 550M | 0.37 GB | 3.96 GB/s | ✓ | not measured (int8 KV) |
| Dense, int4 body, fp16 KV | 550M | 0.42 GB | 4.65 GB/s | ✗ by 0.25 | 47–48 ms |
| Dense, **int8** body, fp16 KV | 550M | 0.64 GB | 7.40 GB/s | ✗ | **39–40 ms** |
| MoE, int8 experts, fp16 KV | 1.41B | 1.34 GB | 5.43 GB/s | ✗ | **134–141 ms** |
| MoE, int4 experts, int8 KV (the plan) | 1.41B | 0.80 GB | 3.98 GB/s | ✓ on paper | not runnable: needs a custom kernel |

**The frame is 80 ms, and the depth decoder and codec must fit in it too.**

1. **The MoE talker misses the frame.** At full depth it needs 134–141 ms of iGPU kernel time, about 3.5× the dense int8 talker (39–40 ms), with gather-based routing. Keeping experts in fp16 makes routing cheaper (2.0× at 16 layers) but takes about 2 GB of RAM. The rule agreed in PF1's plan was MoE ≤ 1.3× dense. **It is not met, so by that rule v0.1 is dense.**
2. **"Bandwidth-bound" was wrong here.** int8 is *faster* than int4 in kernel time (39–40 against 47–48 ms) although it reads twice the weight bytes. With the talker alone, the iGPU is limited by compute, and unpacking int4 costs more than it saves. But int8 takes 7.4 GB/s of a bus that also feeds the thinker, so int4 stays the choice until PF4 measures both together.
3. **Where the MoE's time goes** (16 layers, int8 experts, int4 elsewhere): 42 of 76 ms are copying out and unpacking the chosen experts' weights (gather 20, multiply 22); about 10 ms multiplies by them. A custom kernel could read the chosen experts in place.
4. **Corrections to the plan's budget table:** the depth decoder reads 61 MB per frame (0.76 GB/s), not 120 MB (1.5 GB/s); the KV cache is 110 MB per frame at fp16, 55 MB at int8; the MoE totals 1.41B parameters, not 1.44B.
5. **Upcycling (found in TR1):** a free top-4 over 32 experts does not start out equal to the dense layer. Route top-1 inside each of 4 groups of 8 copies.

**Options for the team**

| Option | Cost | Keeps |
|---|---|---|
| **A. Dense talker for v0.1** (the pre-agreed rule) | Less model capacity | The plan's timeline and training budget |
| **B. Dense v0.1, MoE in v0.2** with a custom OpenVINO kernel or frame-level routing chosen on the CPU | A kernel-writing task | The MoE goal, later |
| **C. MoE in training only,** then distil into the dense talker for the laptop | More T4-hours | The MoE as a teacher; meets the course's MoE goal off the laptop |
| **D. MoE in a few layers only** (say the last 4) | About +7 ms (fp16 experts) to +15 ms (int8) over dense | A small MoE on the laptop |

**Recommendation:** A for the laptop, with C if an MoE is required: the MoE trains on T4s, where expert routing is not a bottleneck, and the laptop ships the distilled dense model. TR2's plan needs the team's choice before it launches.

## What changes next

1. The team picks A–D.
2. A valid quiet-machine run of PF1 (this report's timings come from a run on a busy machine; the ratios are stable).
3. Codec-dependent head after TK1.

**T4-hours used:** 0
