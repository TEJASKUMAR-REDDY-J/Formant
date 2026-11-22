"""TK1: what each text tokenizer costs our languages, and how much of its vocabulary they can ever use.

Needs only tokenizer.json files (Qwen3 11 MB, Sarvam 34 MB), no corpus and no model weights.

    python 02-tokenizer/scripts/vocab_audit.py --cache F:/tools/hf

Script audit: a token is kept if every character is in a script we serve, or is script-neutral (digits, punctuation,
spaces), or is a raw UTF-8 fragment (needed to spell rare characters), or is a special token. This is an upper bound
on what is needed: frequency-based trimming on a corpus cuts further (TK2).
"""
import argparse
import json
import pathlib
import statistics
import unicodedata

from tokenizers import Tokenizer

HERE = pathlib.Path(__file__).resolve().parents[1]
REPOS = {"Qwen3": "Qwen__Qwen3-0.6B", "Sarvam 30B": "sarvamai__sarvam-30b"}
OURS = {"LATIN", "DEVANAGARI", "BENGALI", "TAMIL", "TELUGU"}
INDIC = {"GUJARATI", "GURMUKHI", "KANNADA", "MALAYALAM", "ORIYA", "OL", "MEETEI", "SINHALA"}


def byte_decoder():
    """GPT-2's printable-character <-> byte table, used by byte-level BPE vocabularies."""
    bs = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
    cs, n = bs[:], 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return {chr(c): b for b, c in zip(bs, cs)}


BYTES = byte_decoder()


def surface(tok, byte_level):
    """Token string -> text, or None if it is an incomplete UTF-8 fragment."""
    if byte_level:
        try:
            return bytes(BYTES[c] for c in tok).decode("utf-8")
        except KeyError:
            return tok
        except UnicodeDecodeError:
            return None
    if tok.startswith("<0x") and tok.endswith(">") and len(tok) == 6:
        return None
    return tok.replace("\u2581", " ")


def classify(text):
    if text is None:
        return "byte fragment"
    seen = set()
    for ch in text:
        if unicodedata.category(ch)[0] in "LM":
            try:
                name = unicodedata.name(ch).split()[0]
            except ValueError:
                return "other script"
            if name == "COMBINING":
                continue
            seen.add(name)
    if not seen:
        return "neutral"
    if seen <= {"LATIN"}:
        # Latin covers English and romanised Hindi; letters with diacritics are mostly other European languages.
        return "Latin (ASCII)" if text.isascii() else "Latin (accented)"
    if seen <= OURS:
        return "our Indic scripts"
    if seen <= OURS | INDIC:
        return "other Indic scripts"
    return "other script"


KEEP = {"byte fragment", "neutral", "Latin (ASCII)", "our Indic scripts", "special"}


def audit(path):
    j = json.loads(path.read_text(encoding="utf-8"))
    vocab = j["model"]["vocab"]
    toks = vocab if isinstance(vocab, dict) else {t: i for i, (t, _) in enumerate(vocab)}
    special = {a["content"] for a in j.get("added_tokens", [])}
    byte_level = "ByteLevel" in json.dumps([j.get("pre_tokenizer"), j.get("decoder")])
    counts = {}
    for t in toks:
        c = "special" if t in special else classify(surface(t, byte_level))
        counts[c] = counts.get(c, 0) + 1
    counts["special"] = counts.get("special", 0) + len(special - set(toks))
    return counts


def fertility(path, rows):
    tk = Tokenizer.from_file(str(path))
    out = {}
    for lang in sorted({r["lang"] for r in rows}):
        texts = [r["prompt"] for r in rows if r["lang"] == lang]
        ratios = [len(tk.encode(x, add_special_tokens=False).ids) / len(x.split()) for x in texts]
        out[lang] = {"tokens_per_word": round(statistics.mean(ratios), 2), "max": round(max(ratios), 2), "n": len(texts)}
    return out


def demo():
    assert classify("नमस्ते") == "our Indic scripts" and classify("ગુજરાતી") == "other Indic scripts"
    assert classify(" the") == "Latin (ASCII)" and classify("é") == "Latin (accented)" and classify("漢") == "other script"
    assert classify("123!") == "neutral" and classify(surface("<0xE0>", False)) == "byte fragment"
    assert surface("Ġthe", True) == " the" and surface("à¤", True) is None


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--cache", required=True)
    a.add_argument("--words-per-second", type=float, default=2.5, help="assumed speaking rate until DA1 measures it")
    args = a.parse_args()
    demo()
    rows = [json.loads(x) for x in (HERE / "configs/sample-sentences.jsonl").read_text(encoding="utf-8").splitlines()]
    res = {}
    for name, d in REPOS.items():
        p = pathlib.Path(args.cache) / d / "tokenizer.json"
        c = audit(p)
        kept, total = sum(v for k, v in c.items() if k in KEEP), sum(c.values())
        f = fertility(p, rows)
        res[name] = {"vocabulary": total, "kept_by_script": kept, "by_class": dict(sorted(c.items(), key=lambda kv: -kv[1])), "fertility": f}
        print(f"\n{name}: {total:,} tokens, {kept:,} kept by script ({kept / total:.0%})")
        for k, v in res[name]["by_class"].items():
            print(f"   {k:22s}{v:9,}{'' if k in KEEP else '   dropped'}")
        for g, v in f.items():
            tps = v["tokens_per_word"] * args.words_per_second
            print(f"   {g:6s} {v['tokens_per_word']:5.2f} tokens/word (max {v['max']:.2f}, n={v['n']})  ~{tps:4.1f} tokens/s of 12.5 slots/s{'  OVER 2 per word' if v['tokens_per_word'] > 2 else ''}")
    (HERE / "reports").mkdir(exist_ok=True)
    (HERE / "reports" / "vocab-audit.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
