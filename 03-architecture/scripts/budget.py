"""AR1: parameters and bytes per 80 ms frame for a talker spec.

    python 03-architecture/scripts/budget.py                         # every spec in configs/
    python 03-architecture/scripts/budget.py configs/talker-moe.json
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parents[1]
HZ = 12.5


def budget(c):
    d, L, b = c["d"], c["layers"], {k: v / 8 for k, v in c["bits"].items()}
    heads, kvh, hd = c["q_heads"], c["kv_heads"], c["head_dim"]
    attn = L * (2 * d * heads * hd + 2 * d * kvh * hd)
    moe = c.get("moe")
    dense_layers = L if not moe else moe["first_dense"]
    ffn_dense = dense_layers * 3 * d * c["ffn"]
    out = {"attention": (attn, attn, "attn"), "dense FFN": (ffn_dense, ffn_dense, "ffn")}
    if moe:
        n = L - dense_layers
        shared, expert = 3 * d * moe["shared"], 3 * d * moe["routed"]
        out["shared experts"] = (n * shared,) * 2 + ("ffn",)
        out["routed experts"] = (n * moe["experts"] * expert, n * moe["top_k"] * expert, "experts")
        out["routers"] = (n * d * moe["experts"],) * 2 + ("router",)
        if n:
            active = moe["shared"] + moe["top_k"] * moe["routed"]
            assert active <= c["ffn"], f"active FFN width {active} is wider than the dense {c['ffn']}"
    out["text head"] = (c["text_vocab"] * d,) * 2 + ("head",)
    tables = c["streams"] * c["codebooks"] * c["code_vocab"] * d
    out["embedding tables"] = (tables, 0, "embed")                     # lookups: a few rows per frame
    dep = c.get("depth")
    if dep:
        dd = dep["d"]
        layer = 4 * dd * dd + 3 * dd * dep["ffn"]
        body = dep["layers"] * layer
        per_cb = c["codebooks"] * (d * dd + dd * c["code_vocab"])        # in-projection and output head per codebook
        out["depth decoder"] = (body + per_cb + c["codebooks"] * c["code_vocab"] * dd, body * c["codebooks"] + per_cb, "depth")
    rows = {k: {"params_m": t / 1e6, "ram_mb": t * b[w] / 1e6, "read_mb": r * b[w] / 1e6} for k, (t, r, w) in out.items()}
    kv_col = 2 * kvh * hd * b["kv"]                                     # one layer, one frame
    g = c["global_layers"]
    kv = (L - g) * c["window"] * kv_col + g * c["global_window"] * kv_col
    rows["KV cache"] = {"params_m": 0, "ram_mb": kv / 1e6, "read_mb": kv / 1e6}
    return rows


def report(c):
    rows = budget(c)
    dep = rows.get("depth decoder", {"read_mb": 0, "params_m": 0})
    total = {k: sum(r[k] for r in rows.values()) for k in ("params_m", "ram_mb", "read_mb")}
    talker = total["read_mb"] - dep["read_mb"]
    print(f"\n{c['name']}")
    print(f"  {'part':18s}{'params M':>10s}{'RAM MB':>9s}{'MB/frame':>10s}{'GB/s':>7s}")
    for k, r in rows.items():
        print(f"  {k:18s}{r['params_m']:10.1f}{r['ram_mb']:9.1f}{r['read_mb']:10.1f}{r['read_mb'] * HZ / 1e3:7.2f}")
    print(f"  {'total':18s}{total['params_m']:10.1f}{total['ram_mb']:9.1f}{total['read_mb']:10.1f}{total['read_mb'] * HZ / 1e3:7.2f}")
    print(f"  talker {talker * HZ / 1e3:.2f} of {c['talker_share_gbs']} GB/s: {'fits' if talker * HZ / 1e3 <= c['talker_share_gbs'] else 'OVER'};"
          f" depth decoder {dep['read_mb'] * HZ / 1e3:.2f} of {c['depth_share_gbs']} GB/s; RAM {total['ram_mb'] / 1e3:.2f} GB")
    return talker * HZ / 1e3


def demo():
    """The dense spec must reproduce Qwen3-0.6B's published parameter count (tied head counted twice on the Hub)."""
    c = json.loads((HERE / "configs" / "talker-dense.json").read_text())
    r = budget({**c, "text_vocab": 151936})
    body = r["attention"]["params_m"] + r["dense FFN"]["params_m"]
    assert abs(body + 2 * r["text head"]["params_m"] - 751.632384) < 0.2, (body, r["text head"]["params_m"])
    m = json.loads((HERE / "configs" / "talker-moe.json").read_text())
    assert abs(budget(m)["attention"]["read_mb"] - budget(c)["attention"]["read_mb"]) < 1e-9


if __name__ == "__main__":
    demo()
    files = [pathlib.Path(f) for f in sys.argv[1:]] or sorted((HERE / "configs").glob("talker-*.json"))
    for f in files:
        report(json.loads(f.read_text()))
