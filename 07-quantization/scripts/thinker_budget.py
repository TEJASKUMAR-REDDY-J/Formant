"""QZ1: what Sarvam 30B costs per token on this laptop, from its published config. Downloads nothing.

Every generated token reads: all attention weights, the 6 routed + 1 shared expert of each MoE layer, the first
dense layer, and the whole output head. Token rate on a bandwidth-bound CPU is then  bus share / bytes read.

    python 07-quantization/scripts/thinker_budget.py            # tables
    python 07-quantization/scripts/thinker_budget.py --live     # refresh GGUF file sizes from the Hub (metadata only)
"""
import argparse, json, pathlib, urllib.request

HERE = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((HERE / "configs" / "sarvam-30b.json").read_text())
SIZES = HERE / "configs" / "gguf-sizes.json"
# Bits per weight of llama.cpp tensor types (block layouts, so exact).
BPW = {"F16": 16, "Q8_0": 8.5, "Q6_K": 6.5625, "Q5_K": 5.5, "Q4_K": 4.5, "IQ4_XS": 4.25, "Q3_K": 3.4375,
       "IQ3_S": 3.4375, "IQ3_XXS": 3.0625, "Q2_K": 2.625, "IQ2_XXS": 2.0625}
SHARE_GBS, BUS_GBS, RAM_GB = 5.3, 20.8, 14.0   # thinker's share of the bus, measured copy bandwidth, thinker RAM budget


def parts(c, vocab=None):
    """Parameter counts: {name: (total, read per token)}."""
    d, L, kd = c["hidden_size"], c["num_hidden_layers"], c["first_k_dense_replace"]
    v = vocab or c["vocab_size"]
    q = d * c["num_attention_heads"] * c["head_dim"]
    kv = d * c["num_key_value_heads"] * c["head_dim"]
    attn = L * (2 * q + 2 * kv)                                   # q, o, k, v
    expert = 3 * d * c["moe_intermediate_size"]
    moe = L - kd
    return {
        "attention": (attn, attn),
        "dense layer": (kd * 3 * d * c["intermediate_size"],) * 2,
        "shared experts": (moe * c["num_shared_experts"] * expert,) * 2,
        "routed experts": (moe * c["num_experts"] * expert, moe * c["num_experts_per_tok"] * expert),
        "routers": (moe * d * c["num_experts"],) * 2,
        "output head": (v * d, v * d),
        "embedding": (v * d, d),                                  # one row per token
    }


def cost(c, bits, vocab=None):
    """bits: {part: type}. Returns (GB in RAM, GB read per token)."""
    gb = lambda n, t: n * BPW[t] / 8 / 1e9
    p = parts(c, vocab)
    pick = lambda name: bits.get(name, bits["routed experts"])
    return sum(gb(t, pick(k)) for k, (t, _) in p.items()), sum(gb(r, pick(k)) for k, (_, r) in p.items())


HI = {"attention": "Q6_K", "dense layer": "Q6_K", "shared experts": "Q6_K", "routers": "F16", "embedding": "Q4_K"}
RECIPES = [  # name, bits, vocabulary kept (None = all 262,144)
    ("uniform 4.5-bit (Q4_K), head Q6", {"routed experts": "Q4_K", "output head": "Q6_K"}, None),
    ("uniform IQ3_XXS, head Q6", {"routed experts": "IQ3_XXS", "output head": "Q6_K"}, None),
    ("mixed: experts IQ3_XXS, rest Q6, head Q6", {**HI, "routed experts": "IQ3_XXS", "output head": "Q6_K"}, None),
    ("mixed, head Q4", {**HI, "routed experts": "IQ3_XXS", "output head": "Q4_K"}, None),
    ("uniform IQ3_XXS, head + embedding cut by script to 186k, Q4", {"routed experts": "IQ3_XXS", "output head": "Q4_K", "embedding": "Q4_K"}, 186_088),  # TK1 vocab audit
    ("uniform IQ3_XXS, head + embedding trimmed to 80k, Q4", {"routed experts": "IQ3_XXS", "output head": "Q4_K", "embedding": "Q4_K"}, 80_000),
    ("mixed, trimmed to 80k, head Q4", {**HI, "routed experts": "IQ3_XXS", "output head": "Q4_K"}, 80_000),
    ("attention Q4, experts IQ3_XXS, trimmed to 80k, head Q4",
     {**HI, "attention": "Q4_K", "shared experts": "Q4_K", "dense layer": "Q4_K", "routed experts": "IQ3_XXS", "output head": "Q4_K"}, 80_000),
    ("experts Q2_K, rest Q4, trimmed to 80k, head Q4",
     {**HI, "attention": "Q4_K", "shared experts": "Q4_K", "dense layer": "Q4_K", "routed experts": "Q2_K", "output head": "Q4_K"}, 80_000),
]


def live_sizes():
    out = {}
    for repo in ("sarvamai/sarvam-30b-gguf", "Sumitc13/sarvam-30B-GGUF", "mradermacher/sarvam-30b-uncensored-i1-GGUF"):
        with urllib.request.urlopen(f"https://huggingface.co/api/models/{repo}/tree/main?recursive=1", timeout=60) as r:
            for f in json.load(r):
                if f["path"].endswith(".gguf") and "imatrix" not in f["path"]:
                    name = f["path"].split("-0000")[0].removesuffix(".gguf").split(".i1-")[-1].split("30b-")[-1].split("30B-")[-1]
                    out.setdefault(repo, {}).setdefault(name, 0)
                    out[repo][name] += f["size"]
    return out


def demo():
    p = parts(CFG)
    assert abs(sum(t for t, _ in p.values()) / CFG["_safetensors_params"] - 1) < 0.001, "config does not reproduce the published size"
    ram, read = cost(CFG, {"routed experts": "F16"})
    assert ram > 8 * read                                         # sparse: most weights are not read
    assert cost(CFG, {"routed experts": "IQ3_XXS", "output head": "Q4_K"}, 80_000)[1] < cost(CFG, {"routed experts": "IQ3_XXS", "output head": "Q4_K"})[1]


if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("--live", action="store_true"); args = a.parse_args()
    demo()
    if args.live:
        SIZES.write_text(json.dumps(live_sizes(), indent=1) + "\n")
    print("Parameters (millions): total / read per token")
    for k, (t, r) in parts(CFG).items():
        print(f"  {k:15s} {t / 1e6:9,.0f} {r / 1e6:9,.1f}")
    act = {k: r for k, (_, r) in parts(CFG).items()}
    print(f"  read per token {sum(act.values()) / 1e9:.2f}B, of which the output head is {act['output head'] / 1e9:.2f}B\n")
    print(f"{'recipe':58s} {'RAM GB':>7s} {'fits':>5s} {'GB/token':>9s} {'tok/s @' + str(SHARE_GBS):>11s} {'tok/s @' + str(BUS_GBS):>11s}")
    for name, bits, vocab in RECIPES:
        ram, read = cost(CFG, bits, vocab)
        print(f"{name:58s} {ram:7.1f} {'yes' if ram <= RAM_GB else 'no':>5s} {read:9.2f} {SHARE_GBS / read:11.1f} {BUS_GBS / read:11.1f}")
    print("\nPublished GGUF files (Hub metadata), bits per weight over 32.15B parameters:")
    for repo, files in json.loads(SIZES.read_text()).items():
        for n, b in sorted(files.items(), key=lambda kv: kv[1]):
            print(f"  {repo.split('/')[0]:12s} {n:12s} {b / 1e9:6.2f} GB  {b * 8 / CFG['_safetensors_params']:5.2f} bpw  {'fits 14 GB' if b / 1e9 <= RAM_GB else ''}")
