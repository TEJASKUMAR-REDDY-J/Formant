"""Evaluation metrics with one definition each (EV1; 06-evaluation/metric-spec.md)."""
import hashlib
import random
import re
import unicodedata
from collections import defaultdict

# Nukta letters have precomposed and combining spellings that NFC does not unify; decompose, so both spellings match.
_NUKTA = {chr(c): unicodedata.normalize("NFD", chr(c)) for c in [*range(0x0958, 0x0960), 0x09DC, 0x09DD, 0x09DF, 0x0929, 0x0931, 0x0934]}
_JOINERS = dict.fromkeys(map(ord, "​‌‍﻿⁠"))


def normalise(text):
    """NFC; nukta forms unified; zero-width characters dropped; Indic digits to 0-9; case folded; punctuation to spaces."""
    t = unicodedata.normalize("NFC", text).translate(_JOINERS)
    t = "".join(_NUKTA.get(ch, ch) for ch in t)
    t = "".join(str(unicodedata.digit(ch)) if unicodedata.category(ch) == "Nd" else ch for ch in t).casefold()
    t = "".join(" " if unicodedata.category(ch)[0] in "PSZC" else ch for ch in t)
    return re.sub(r"\s+", " ", t).strip()


def edits(ref, hyp):
    """Levenshtein distance between two sequences."""
    if len(ref) < len(hyp):
        ref, hyp = hyp, ref
    row = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        diag, row[0] = row[0], i
        for j, h in enumerate(hyp, 1):
            diag, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, diag + (r != h))
    return row[-1]


def cer_counts(ref, hyp):
    """(edits, reference characters). Spaces are not scored: Indic word boundaries are written inconsistently."""
    r, h = (normalise(x).replace(" ", "") for x in (ref, hyp))
    return edits(r, h), len(r)


def wer_counts(ref, hyp):
    r, h = normalise(ref).split(), normalise(hyp).split()
    return edits(r, h), len(r)


def rate(counts):
    """Corpus rate: total edits / total reference length (not a mean of per-utterance rates)."""
    n = sum(c for _, c in counts)
    if not n:
        raise ValueError("empty reference set")
    return sum(e for e, _ in counts) / n


def bootstrap(items, stat, n=1000, level=0.95, seed=0, groups=None):
    """(value, low, high). Resample speakers, not clips, when `groups` is given: clips of one speaker are not independent."""
    rng = random.Random(seed)
    if groups is None:
        units = [[x] for x in items]
    else:
        by = defaultdict(list)
        for x, g in zip(items, groups, strict=True):
            by[g].append(x)
        units = list(by.values())
    vals = sorted(stat([x for u in rng.choices(units, k=len(units)) for x in u]) for _ in range(n))
    lo = (1 - level) / 2
    return stat(items), vals[int(lo * (n - 1))], vals[int(round((1 - lo) * (n - 1)))]


# --- turn taking. Times in seconds. Segments are (start, end) of speech on each channel. ---

def turns(user, agent, user_turn_ends, window=3.0):
    """user_turn_ends: times where the user really finished a turn (annotated). Returns metrics for one session.

    takeover: the agent starts speaking within `window` after a real turn end, before the user speaks again.
    latency: that start minus the turn end. false_takeover: the agent starts inside a user turn, not at its end,
    and talks over the user for more than 1 s (a shorter overlap is a backchannel)."""
    ends = sorted(user_turn_ends)
    lat, n_ok = [], 0
    for e in ends:
        nxt = min([s for s, _ in user if s > e + 1e-6], default=float("inf"))
        starts = [s for s, _ in agent if e - 0.2 <= s <= min(e + window, nxt)]      # up to 200 ms early still counts as on time
        if starts:
            n_ok += 1
            lat.append(max(0.0, min(starts) - e))
    false = back = 0
    for s, t in agent:
        over = sum(max(0.0, min(t, b) - max(s, a)) for a, b in user if a < s)        # overlap with speech that was already running
        if any(abs(s - e) <= 0.2 for e in ends) or over <= 0.05:
            continue
        if over > 1.0:
            false += 1
        else:
            back += 1
    return {"turn_ends": len(ends), "takeovers": n_ok, "latencies": lat, "false_takeovers": false, "backchannels": back}


def barge_in(user, agent, stop_within=0.3):
    """For each user onset while the agent is speaking: how long until the agent is silent. Backchannel-length user
    speech (under 0.7 s) is not a barge-in. Returns {"stops": [...], "within": share stopped in time}."""
    stops = []
    for a, b in user:
        if b - a < 0.7:
            continue
        for s, t in agent:
            if s < a < t:
                stops.append(t - a)
    return {"stops": stops, "within": sum(x <= stop_within for x in stops) / len(stops) if stops else None}


def percentile(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


# --- test speakers ---

def select_speakers(rows, per_lang=24, seed="formant-ev1-v1", min_minutes=2.0):
    """rows: dicts with speaker, lang, gender, age_group, region, minutes. Deterministic, balanced hold-out.

    Round-robin over (gender, age group, region) strata, strata in rarest-first order; inside a stratum the order is a
    keyed hash, so adding speakers later never reshuffles the ones already chosen at the same rank.
    Returns {lang: [speaker, ...]}; raises if a language cannot supply enough."""
    out = {}
    key = lambda s: hashlib.sha256(f"{seed}/{s}".encode()).hexdigest()
    for lang in sorted({r["lang"] for r in rows}):
        agg = {}
        for r in rows:
            if r["lang"] == lang:
                a = agg.setdefault(r["speaker"], {"strata": (r["gender"], r["age_group"], r["region"]), "min": 0.0})
                a["min"] += r["minutes"]
        strata = defaultdict(list)
        for sp, a in agg.items():
            if a["min"] >= min_minutes:
                strata[a["strata"]].append(sp)
        for v in strata.values():
            v.sort(key=key)
        order = sorted(strata, key=lambda s: (len(strata[s]), str(s)))
        pick = []
        for depth in range(max(map(len, strata.values()), default=0)):
            # Alternate genders within a round so a truncated last round stays balanced.
            for s in sorted(order, key=lambda s: (sum(1 for p in pick if agg[p]["strata"][0] == s[0]), len(strata[s]), str(s))):
                if depth < len(strata[s]) and len(pick) < per_lang:
                    pick.append(strata[s][depth])
        if len(pick) < per_lang:
            raise ValueError(f"{lang}: only {len(pick)} eligible speakers, need {per_lang}")
        out[lang] = sorted(pick)
    return out


def freeze(lists):
    """Canonical JSON payload and its hash, for eval/test-speakers-v1.json."""
    import json
    body = json.dumps(lists, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return body, hashlib.sha256(body.encode()).hexdigest()
