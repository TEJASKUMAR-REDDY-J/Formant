"""Automatic checks of the spoken-style spec (PT1; 05-post-training/style-spec.md). Language identity is by script here:
it separates every language pair we serve except Hindi/Marathi and English/romanised Hinglish, which need a classifier."""
import re
import unicodedata

SCRIPTS = {"hi": "DEVANAGARI", "mr": "DEVANAGARI", "bn": "BENGALI", "ta": "TAMIL", "te": "TELUGU", "en": "LATIN"}
END = re.compile(r"(?<=[.!?।॥])[\"'”’)]*\s+")
CLAUSE = re.compile(r"[,;:—–।॥.!?]")
MARKDOWN = re.compile(r"(^|\n)\s*([-*•+]\s|\d+[.)]\s|#{1,6}\s|>\s)|\*\*|__|`|\[[^\]]+\]\(|\|.*\|")
URL = re.compile(r"https?://|www\.|\S+@\S+\.\S+")
THINK = re.compile(r"</?(think|reasoning|analysis)\b", re.I)
SYMBOLS = set("%₹$€£&@#=+×÷<>→←°/\\^~{}[]|_*")


def scripts(text):
    n = {}
    for ch in text:
        if ch.isalpha() or unicodedata.category(ch) in ("Mn", "Mc"):
            try:
                s = unicodedata.name(ch).split()[0]
            except ValueError:
                continue
            n[s] = n.get(s, 0) + 1
    total = sum(n.values()) or 1
    return {k: v / total for k, v in n.items()}


def sentences(text):
    return [s for s in END.split(text.strip()) if s.strip()]


def check(reply, lang, max_sentences=3, max_first_words=8):
    """lang: hi, en, bn, mr, ta, te or hi-en. Returns {"ok": bool, "problems": [...], "first_clause_words": n, "sentences": n}."""
    p, t = [], reply.strip()
    if not t:
        return {"ok": False, "problems": ["empty"], "first_clause_words": 0, "sentences": 0}
    if THINK.search(t):
        p.append("thinking trace")
    if MARKDOWN.search(t):
        p.append("markdown")
    if URL.search(t):
        p.append("url or email")
    if any(ch.isdigit() for ch in t):
        p.append("digits (numbers must be words)")
    if bad := sorted({c for c in t if c in SYMBOLS}):
        p.append(f"symbols {' '.join(bad)}")
    if any(unicodedata.category(c) in ("So", "Sk") or ord(c) >= 0x1F000 for c in t):
        p.append("emoji")
    ss = sentences(t)
    if len(ss) > max_sentences:
        p.append(f"{len(ss)} sentences (limit {max_sentences})")
    first = len([w for w in CLAUSE.split(t, maxsplit=1)[0].split() if any(c.isalpha() for c in w)])
    if first > max_first_words:
        p.append(f"first clause has {first} words (limit {max_first_words})")
    sc = scripts(t)
    if lang == "hi-en":
        if sc.get("DEVANAGARI", 0) + sc.get("LATIN", 0) < 0.95:
            p.append("not Hinglish script")
    elif (share := sc.get(SCRIPTS[lang], 0)) < (0.9 if lang == "en" else 0.5):      # English loanwords are normal in Indian speech
        p.append(f"only {share:.0%} in the {lang} script")
    return {"ok": not p, "problems": p, "first_clause_words": first, "sentences": len(ss)}


def summary(rows):
    """rows: (lang, check result) pairs -> {lang: {"n", "compliance", "top_problem"}}"""
    out = {}
    for lang in sorted({g for g, _ in rows}):
        rs = [r for g, r in rows if g == lang]
        probs = {}
        for r in rs:
            for x in r["problems"]:
                k = re.sub(r"\d+%?", "N", x.split("(")[0]).strip()
                probs[k] = probs.get(k, 0) + 1
        out[lang] = {"n": len(rs), "compliance": sum(r["ok"] for r in rs) / len(rs), "top_problem": max(probs, key=probs.get) if probs else None}
    return out
