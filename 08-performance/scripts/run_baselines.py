"""PF1: the laptop baseline sheet. Refuses to run on a busy or battery-powered machine, because both change the answer.

    python 08-performance/scripts/run_baselines.py            # writes 08-performance/reports/baseline-v1.json
    python 08-performance/scripts/run_baselines.py --force    # run anyway: writes contended-run.json, never the baseline
"""
import argparse
import json
import pathlib
import platform
import subprocess
import sys
import time

import numpy as np
import psutil

HERE = pathlib.Path(__file__).resolve().parent
REPORTS = HERE.parent / "reports"
G, C = ["--device", "GPU"], ["--device", "CPU", "--threads", "2"]
DENSE8, DENSE4 = ["--kind", "dense", "--attn-bits", "8", "--ffn-bits", "8"], ["--kind", "dense", "--attn-bits", "4", "--ffn-bits", "4"]
MOE8, MOE16 = ["--kind", "moe", "--attn-bits", "8", "--ffn-bits", "8"], ["--kind", "moe", "--attn-bits", "8", "--ffn-bits", "8", "--expert-bits", "16"]
RUNS = [(n, a) for _ in range(2) for n, a in [                  # every run twice, interleaved, so drift shows up
    ("dense int8 GPU", DENSE8 + G), ("dense int4 GPU", DENSE4 + G), ("moe int8 experts GPU", MOE8 + G),
    ("moe fp16 experts GPU, 16 layers", MOE16 + G + ["--layers", "16"]), ("dense int8 GPU, 16 layers", DENSE8 + G + ["--layers", "16"]),
    ("dense int8 CPU", DENSE8 + C), ("moe int8 experts CPU", MOE8 + C)]]


def conditions():
    load = psutil.cpu_percent(interval=5)
    bat = psutil.sensors_battery()
    f = psutil.cpu_freq()
    return {"cpu_load_pct": load, "on_mains": bat.power_plugged if bat else None, "battery_pct": bat.percent if bat else None,
            "cpu_mhz": f.current if f else None, "free_ram_gb": round(psutil.virtual_memory().available / 1e9, 1),
            "time": time.strftime("%Y-%m-%d %H:%M"), "os": platform.platform()}


def bandwidth(mb=512, reps=8):
    """Single- and two-thread memory bandwidth. numpy releases the GIL in these loops."""
    import concurrent.futures as cf
    out = {}
    for threads in (1, 2, 4):
        a = [np.ones(mb * 1024 * 1024 // 8 // threads) for _ in range(threads)]
        b = [np.empty_like(x) for x in a]
        with cf.ThreadPoolExecutor(threads) as ex:
            best = {"copy": 0.0, "read": 0.0}
            for _ in range(reps):
                t = time.perf_counter(); list(ex.map(np.copyto, b, a)); dt = time.perf_counter() - t
                best["copy"] = max(best["copy"], 2 * sum(x.nbytes for x in a) / dt / 1e9)      # read + write
                t = time.perf_counter(); list(ex.map(np.max, a)); dt = time.perf_counter() - t
                best["read"] = max(best["read"], sum(x.nbytes for x in a) / dt / 1e9)
        out[f"{threads} threads"] = {k: round(v, 1) for k, v in best.items()}
    return out


def bench(args):
    p = subprocess.run([sys.executable, str(HERE / "bench_talker.py"), *args], capture_output=True, text=True)
    line = next((x for x in reversed(p.stdout.splitlines()) if x.startswith("{")), None)
    return json.loads(line) if line else {"error": ((p.stderr or "no output").strip().splitlines() or ["no output"])[-1][:200], "exit": p.returncode}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--force", action="store_true")
    a.add_argument("--steps", type=int, default=150)
    args = a.parse_args()
    before = conditions()
    quiet = before["cpu_load_pct"] < 15 and before["on_mains"] is not False
    if not quiet and not args.force:
        sys.exit(f"machine is not ready: CPU {before['cpu_load_pct']}% busy, on mains: {before['on_mains']}. "
                 "Close other work and plug in, or use --force.")
    runs = []
    for name, spec in RUNS:
        # Wall time and kernel time come from separate runs: profiling adds tens of ms of host time per step.
        r = {"name": name, **bench(spec + ["--steps", str(args.steps)])}
        if "error" not in r:
            k = bench(spec + ["--steps", "20", "--profile"])
            r.update({x: k.get(x) for x in ("kernel_ms", "profile_ms")})
            r.pop("profile", None)
        runs.append(r)
        print(f"{name:36s} " + (r["error"] if "error" in r else f"p50 {r['step_ms_p50']:7.1f} ms  p95 {r['step_ms_p95']:7.1f}  kernel {r['kernel_ms']}"), flush=True)
    sheet = {"valid": quiet, "before": before, "after": conditions(), "bandwidth_gb_s": bandwidth(), "talker_step": runs}
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / ("baseline-v1.json" if quiet else "contended-run.json")  # a busy run never becomes the baseline
    out.write_text(json.dumps(sheet, indent=1) + "\n")
    print("valid baseline" if quiet else "NOT a valid baseline (busy or on battery)", "->", out)


if __name__ == "__main__":
    main()
