# TR1 · Smoke runs

**Status:** in progress. The training stack works end to end on the laptop's CPU with **synthetic tokens** and a small model. Not done: the ~50M model on T4s in fp16, real tokens, the mixture search and the OPUS A/B. The last three need the pilot data.

## What was done

- [`src/formant/talker.py`](../../src/formant/talker.py): multi-stream talker with acoustic delay, depth decoder, document masking, sliding window, and an optional MoE (shared + routed experts, bias balancing, upcycling from a dense layer).
- [`src/formant/sampler.py`](../../src/formant/sampler.py): the DATA_PLAN language mixture and a deterministic, resumable, stratified sampler.
- [`scripts/smoke.py`](../scripts/smoke.py): training loop using IN1's checkpoints and MO1's metrics.

It needs `src/formant/ckpt.py` (IN1) and `src/formant/metrics.py` (MO1): **merge those two PRs first.**

## How it was checked

- `python -m pytest tests/test_talker.py`, 9 tests. Among them: outputs at frame t do not change when anything later changes; documents do not mix; MoE dispatch equals a brute-force sum; an upcycled MoE reproduces the dense layer; the mixture reproduces DATA_PLAN's table; the sampler resumes exactly.
- Four runs of 200 steps on the i3, at low priority beside other work: dense (0.47M parameters), MoE (1.05M), and the MoE again killed hard at step 117 and resumed.

## Result

| Check | Pass when | Result |
|---|---|---|
| Loss per codebook | all fall | ✓ 4.10 → 0.88 / 0.51 / 0.55 / 0.61 (dense); the MoE ends within 0.02 of it |
| Resume after a kill | within 1% | ✓ **bit-identical on all 200 steps** (CPU) |
| Expert balance | max/mean ≤ 1.5, none dead | ✓ 2.27 early, then 1.1–1.4 from step 80; 0 dead throughout |
| Language shares | match the mixture | ✓ 23.1 / 16.4 / 14.2 / 14.2 / 14.2 / 14.1 / 3.8% |
| fp16 stability | no overflow streaks | **not tested:** the CPU runs are fp32 |
| MoE overhead | ≤ 30% | not valid here: the machine was busy and the models are tiny |
| Expert specialisation | | none yet: router entropy stays at 0.99 of the maximum |

**Two findings to act on**

1. **Hinglish learns far more slowly** (1.86 against 0.45–0.70 for the others), most likely because the 4-epoch cap holds it to 3.8% of batches (about 61 of 1,600). This is the case the worst-language mixture search exists for. On real speech Hinglish shares sounds with Hindi and English, so the gap should be smaller.
2. **The upcycling recipe in AR1 does not start out equal to the dense layer.** It does so only if the router picks exactly one copy of every slice. A free top-4 over 32 experts can pick two copies of one slice and none of another. Fix: route top-1 inside each of 4 groups of 8 copies, so every slice is always present at step 0.

## What changes next

1. T4 run of the ~50M size for fp16 and throughput. Needs a Kaggle account and the Hub repositories from IN1.
2. Grouped routing in the MoE, if AR1 keeps MoE.
3. Mixture search and OPUS once pilot tokens exist.

**T4-hours used:** 0
