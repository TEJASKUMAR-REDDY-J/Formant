# PF1 · Baselines

**Status:** in progress. The talker step and the memory bandwidth are measured on the real laptop, **but never on a quiet machine:** other jobs were using 17–100% of the CPU throughout. Every sheet is therefore saved as `contended-run.json`, and `baseline-v1.json` does not exist yet. Not measured: the codec decoder, the thinker, real models, 30-minute thermals, the T4 numbers.

## What was done

- [`bench_talker.py`](../scripts/bench_talker.py): one 80 ms talker step as an OpenVINO graph of AR1's exact shapes, with random weights. Nothing was downloaded: speed depends on shapes, not on weight values. Left out: RoPE, embeddings, the turn-state head, depth decoder and codec.
- [`run_baselines.py`](../scripts/run_baselines.py): the whole sheet. It refuses a busy or battery-powered machine, takes wall time and device time in separate runs (profiling adds tens of ms), and never lets a forced run become the baseline.

Machine: i3-10110U, UHD Graphics with **23** execution units (the plan said 24), 24 GB, Windows 11, OpenVINO 2026.4.1, on mains.

## How it was checked

Every configuration ran twice, interleaved. Device time repeats within 6% for the dense talkers, 5% for the MoE on the GPU; CPU numbers vary much more and are not used.

## Result

28 layers unless marked, int8 routed experts unless marked, on the iGPU, with other work running. Wall time is p50 / p95 over the two runs; kernel time is the device's own.

| Talker step | Kernel ms | Wall p50 ms | Wall p95 ms |
|---|---|---|---|
| Dense, int8 body | 40.3, 38.6 | 55.0, 74.0 | 59.3, 104.5 |
| Dense, int4 body | 46.9, 47.8 | 63.4, 57.3 | 73.1, 65.4 |
| MoE, int8 experts | **141.3, 134.0** | **164.3, 139.9** | 174.8, 160.9 |
| Dense, int8, 16 layers | 24.4, 24.9 | 31.9, 28.1 | 38.5, 34.7 |
| MoE, fp16 experts, 16 layers | 50.5, 49.8 | 57.0, 59.5 | 62.8, 78.8 |

- **MoE against dense: 3.5× in kernel time, 1.9–3.0× in wall time** at 28 layers (int8 experts), 2.0× with fp16 experts at 16 layers. The rule in the plan was ≤ 1.3×. **Not met.** The MoE alone already exceeds the 80 ms frame.
- **The dense talker alone takes 47–61 ms of wall time** (p50) in an earlier, quieter run without profiling: 47.9 ms int8, 60.8 ms int4. The depth decoder and codec still have to fit in the same frame. **That is not proven either way yet.**
- **int8 is faster than int4 on this iGPU,** so it is limited by compute, not bandwidth, when alone.
- **Memory bandwidth:** copy 18–20 GB/s, read 14–20 GB/s with 1–4 threads. The plan's 20.8 GB/s copy figure is right for the best case.
- **MoE on the CPU is worse still** (2 threads): 181–276 ms of kernel time.

**A caveat on the iGPU timings.** OpenVINO's graphics compiler rejected some kernels on this driver (errors in `kernel.errors.txt` at compile time: "CISA routine … intersects") and used fallbacks. A newer Intel graphics driver could change the numbers in either direction.

## What changes next

1. Run `python 08-performance/scripts/run_baselines.py` on a quiet machine, on mains. It takes about 15 minutes.
2. Add the depth decoder and codec once TK1 chooses a codec; then repeat with the thinker running (PF4).
3. Update the Intel graphics driver and compare.
4. T4 throughput, when Kaggle is set up.

**T4-hours used:** 0
