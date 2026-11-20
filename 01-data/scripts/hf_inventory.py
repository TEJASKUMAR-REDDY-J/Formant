"""Build 01-data/sources/hf_datasets.csv: the Hugging Face datasets Formant keeps, and how small they get.

Curated fields live in SOURCES. Licence, gating, sizes, clip counts, metadata fields, last update and
downloads are read live from the public Hub API (no login; gated repos still report these).
Hours per language are estimated from bytes (dataset GB per hour); the DA1 pilot replaces them with
measured hours. Column meanings: 01-data/sources/README.md.

    python 01-data/scripts/hf_inventory.py
"""
import csv, json, pathlib, urllib.parse, urllib.request

API = "https://huggingface.co/api/datasets/"
OUT = pathlib.Path(__file__).resolve().parents[1] / "sources" / "hf_datasets.csv"

# Measured: 1 h of 6 s clips as Mimi codes (8 codebooks, 12.5 Hz, uint16) + transcript + speaker/gender/duration,
# Parquet zstd-9, with uniform random codes (worst case; real codes compress a little better). 12 codebooks: 0.79.
TOKEN_MB_PER_H = 0.54
PASS = 0.75  # assumed share of audio that survives the filters (language ID, SNR, length, CER); the pilot measures it
TARGET = {"hi": 800, "en": 400, "bn": 300, "mr": 300, "ta": 300, "te": 300}  # v0.1 hours kept, from the plan
ORDER = {  # which datasets fill each language's target, in order
    "hi": ["ai4bharat/indicvoices_r", "ai4bharat/IndicVoices", "ai4bharat/Kathbath", "ai4bharat/Shrutilipi"],
    "en": ["ai4bharat/NPTEL"],
    **{l: ["ai4bharat/indicvoices_r", "ai4bharat/IndicVoices", "ai4bharat/Kathbath"] for l in ("bn", "mr", "ta", "te")},
}
LANG = {"hindi": "hi", "hi": "hi", "hin": "hi", "hi_in": "hi",
        "bengali": "bn", "bn": "bn", "ben": "bn", "bn_in": "bn",
        "marathi": "mr", "mr": "mr", "mar": "mr", "mr_in": "mr",
        "tamil": "ta", "ta": "ta", "tam": "ta", "ta_in": "ta",
        "telugu": "te", "te": "te", "tel": "te", "te_in": "te",
        "english": "en", "en": "en", "eng": "en", "en_us": "en", "en-indic": "en", "en2indic": "en"}

# sub: folder holding language dirs ("" = repo root, None = single-language repo).
# hours: reported hours for the whole repo (used for GB per hour). keep_h: fixed hours kept instead of the
# ORDER allocation. keep_gb: fixed stored size (text, eval, timing tables). extra_gb: added to stored size.
S = lambda **k: k
SOURCES = [
    # --- P1: what v0.1 is built from ---
    S(id="ai4bharat/indicvoices_r", sub="", prio="P1", style="natural, studio-clean",
      what="TTS-quality cut of IndicVoices: natural speech re-recorded clean. 10,496 speakers, 22 languages.",
      use="Talker training speech (first pick); 10 h per language kept as FLAC for the codec decoder fine-tune (TK1)",
      hours=1704, extra_gb=6.0, rule="train split of our 5 languages; filters; tokens + 60 h FLAC 24 kHz mono"),
    S(id="ai4bharat/IndicVoices", sub="", prio="P1", style="read 8%, extempore 76%, conversation 16%",
      what="AI4Bharat's large natural-speech set from 16k+ speakers across districts. Hours on the Hub assumed = 11.2k transcribed (est.).",
      use="Talker training speech (bulk); real conversations for turn-timing statistics",
      hours=11200, rule="train split of our 5 languages; filters; tokens; timing table from the conversational part"),
    S(id="ai4bharat/Kathbath", sub="", prio="P1", style="read",
      what="Read sentences from 1,218 speakers in 12 languages, human-checked.",
      use="Talker training speech (read style, many speakers)",
      hours=1684, rule="train split of our 5 languages; filters; tokens"),
    S(id="ai4bharat/Rasa", sub="", prio="P1", style="expressive studio TTS",
      what="Studio TTS recordings with emotions and styles, ≥ 20 h per speaker.",
      use="Voice-lock candidates for the talker's own voice (PT3)",
      keep_h=100, by="hi, bn, mr, ta, te: 20 each", rule="20 h per language from 1-2 candidate voices; tokens"),
    S(id="ai4bharat/NPTEL", sub="", prio="P1", style="lectures",
      what="IIT lecture speech (BhasaAnuvaad). The En-Indic part is Indian-accented English, ~1.6M clips.",
      use="Indian-accented English for the talker",
      hours=None, rule="en2indic config only (English audio); filters; tokens; drop translation columns"),
    S(id="dianavdavidson/MUCS-Hinglish", sub=None, prio="P1", style="read, code-mixed",
      what="MUCS 2021 Hindi-English code-mixed speech (community mirror).",
      use="Hinglish talker speech; Hinglish test (its test split)",
      hours=95.1, keep_h=95.1 * PASS, by="hi-en:71", rule="all of it; test split kept apart for EV"),
    S(id="ai4bharat/sangraha", sub="verified", prio="P1", style="text",
      what="Verified Indic web + PDF text corpus, 22 languages.",
      use="Tokenizer vocabulary merges (TK2)",
      keep_gb=1.8, rule="300 MB of text per language (6 languages), deduplicated sample"),
    # --- P2: reserves (licence pending or only if P1 falls short) ---
    S(id="ai4bharat/Shrutilipi", sub="", prio="P2", style="broadcast news",
      what="All India Radio news bulletins with transcripts, 12 languages.",
      use="Hindi top-up only if P1 falls short", hours=6400, rule="Hindi only, as needed; tokens"),
    S(id="ARTPARK-IISc/Vaani-transcription-part", sub="audio", prio="P2", style="spontaneous, phone quality",
      what="Image-prompted spontaneous speech from many districts, transcribed part.",
      use="Robustness top-up (accents, noisy phones)", hours=2122, keep_h=0, rule="not in v0.1; dialect top-up later"),
    S(id="SPRINGLab/IndicTTS-English", sub=None, prio="P2", style="studio TTS",
      what="IIT Madras Indic TTS: Indian-accented English, studio.", use="Indian English top-up if RL1 clears the licence",
      keep_h=0, rule="only after RL1 confirms the licence"),
    S(id="SPRINGLab/IndicTTS-Hindi", sub=None, prio="P2", style="studio TTS",
      what="IIT Madras Indic TTS: Hindi, studio, ~10 h.", use="Cascade fallback voice (SV1) if RL1 clears the licence",
      keep_h=0, rule="only after RL1 confirms the licence"),
    S(id="SPRINGLab/IndicTTS_Bengali", sub=None, prio="P2", style="studio TTS",
      what="IIT Madras Indic TTS: Bengali, studio.", use="Cascade fallback voice (SV1)", keep_h=0, rule="only for SV1"),
    S(id="SPRINGLab/IndicTTS_Tamil", sub=None, prio="P2", style="studio TTS",
      what="IIT Madras Indic TTS: Tamil, studio.", use="Cascade fallback voice (SV1)", keep_h=0, rule="only for SV1"),
    S(id="SPRINGLab/IndicTTS_Telugu", sub=None, prio="P2", style="studio TTS",
      what="IIT Madras Indic TTS: Telugu, studio.", use="Cascade fallback voice (SV1) if RL1 clears the licence",
      keep_h=0, rule="only after RL1 confirms the licence"),
    S(id="pengyizhou/seamless-interaction-audio-only", sub=None, prio="P2", style="two-person conversation",
      what="Audio-only copy of Meta Seamless Interaction, ~4,000 h of English dyadic talk. Non-commercial.",
      use="English turn-timing statistics only (pauses, overlaps, backchannels); never trains shipped weights",
      hours=4000, keep_gb=0.1, rule="speech/silence timing table per speaker; no audio, no tokens"),
    S(id="ai4bharat/indic-align", sub=None, prio="P2", style="text",
      what="Indic instruction-tuning and safety data.", use="Thinker spoken-style tuning (PT2)",
      keep_gb=1.0, rule="our 5 languages + English, sampled"),
    S(id="Abhishekcr448/Hinglish-Everyday-Conversations-1M", sub=None, prio="P2", style="text dialogue",
      what="1M synthetic everyday Hinglish conversations (romanised).", use="Seed scripts for synthetic Hinglish dialogues (DA2)",
      keep_gb=0.2, rule="all, after a quality spot-check"),
    # --- EVAL: test only, never trained on ---
    S(id="google/fleurs", sub="data", prio="EVAL", style="read",
      what="Google's standard multilingual read-speech benchmark, 102 languages.", use="ASR / codec round-trip tests (EV1, TK1)",
      keep_gb=3.2, rule="test split of hi_in, bn_in, mr_in, ta_in, te_in, en_us, audio as-is"),
    S(id="ai4bharat/Svarah", sub=None, prio="EVAL", style="read + extempore",
      what="Indian-accented English benchmark, 117 speakers.", use="Indian English test", keep_gb=1.1, rule="all, audio as-is"),
    S(id="ai4bharat/Lahaja", sub=None, prio="EVAL", style="read + extempore",
      what="Hindi accent benchmark, 132 speakers from many regions.", use="Hindi accent test", keep_gb=1.4, rule="all, audio as-is"),
    S(id="ARTPARK-IISc/Vaani-Benchmark-V1.0", sub="", prio="EVAL", style="spontaneous",
      what="Vaani dialect benchmark.", use="Dialect robustness test", keep_gb=None, rule="our languages only, audio as-is"),
    S(id="ai4bharat/IN22-Conv", sub=None, prio="EVAL", style="text",
      what="Conversational translation benchmark, 22 languages.", use="Thinker conversation check", keep_gb=0.0, rule="all"),
]


def get(path):
    with urllib.request.urlopen(API + path, timeout=90) as r:
        return json.load(r)


def size(repo, sub=""):
    p = urllib.parse.quote(repo, safe="/") + "/treesize/main" + ("/" + urllib.parse.quote(sub) if sub else "")
    return get(p).get("size") or 0


def lang_sizes(repo, sub):
    tree = get(urllib.parse.quote(repo, safe="/") + "/tree/main" + ("/" + urllib.parse.quote(sub) if sub else ""))
    out = {}
    for e in tree:
        code = LANG.get(e["path"].split("/")[-1].lower())
        if e.get("type") == "directory" and code:
            out[code] = out.get(code, 0) + size(repo, e["path"])
    return out


def card_info(card):
    """Clip counts per language, split names and metadata fields from the card's dataset_info."""
    di = card.get("dataset_info") or []
    di = di if isinstance(di, list) else [di]
    clips, splits, fields = {}, set(), []
    for d in di:
        code = LANG.get((d.get("config_name") or "").split("/")[-1].lower())
        if len(di) > 1 and not code:
            continue
        for s in d.get("splits", []):
            splits.add(s["name"])
            clips[code or "all"] = clips.get(code or "all", 0) + s.get("num_examples", 0)
        fields = fields or [f["name"] for f in d.get("features", []) if f.get("dtype") != "audio" and "audio" not in f["name"]]
    return clips, sorted(splits), fields


def main():
    rows = {}
    for s in SOURCES:
        repo = s["id"]
        meta = get(urllib.parse.quote(repo, safe="/") + "?expand[]=gated&expand[]=cardData&expand[]=tags"
                   "&expand[]=lastModified&expand[]=downloads")
        card, tags = meta.get("cardData") or {}, meta.get("tags") or []
        lic = card.get("license") or [t.split(":", 1)[1] for t in tags if t.startswith("license:")]
        lic = ",".join(lic) if isinstance(lic, list) else lic
        total = size(repo)
        per = lang_sizes(repo, s["sub"]) if s["sub"] is not None else {}
        ours = sum(per.values()) if per else total
        gb_h = total / 1e9 / s["hours"] if s.get("hours") else None
        clips, splits, fields = card_info(card)
        rows[repo] = dict(s, lic=lic, meta=meta, total=total, per=per, ours=ours, gb_h=gb_h,
                          clips=clips, splits=splits, fields=fields, kept={})
        print(f"{repo:52s} {lic or 'none':12s} {total / 1e9:9.1f} GB  ours {ours / 1e9:8.1f} GB")

    # v0.1 allocation: walk each language's sources in order until its target hours are kept.
    for lang, need in TARGET.items():
        for repo in ORDER[lang]:
            r = rows[repo]
            have = r["per"].get(lang, 0) / 1e9 / r["gb_h"] * PASS if r["gb_h"] else float("inf")
            take = min(have, need)
            if take > 0:
                r["kept"][lang] = take
                need -= take

    out = []
    for r in rows.values():
        keep_h = r.get("keep_h", sum(r["kept"].values()))
        pull_gb = keep_h / PASS * r["gb_h"] if r["gb_h"] else None
        stored = r["keep_gb"] if "keep_gb" in r else keep_h * TOKEN_MB_PER_H / 1000 + r.get("extra_gb", 0)
        if stored is None:  # eval set kept as-is in our languages
            stored = r["ours"] / 1e9
        raw = r["ours"] / 1e9
        hours_ours = {k: v / 1e9 / r["gb_h"] for k, v in r["per"].items()} if r["gb_h"] and r["per"] else {}
        store_as = ("timing table" if r["style"].startswith("two-person") else "text, Parquet zstd" if "text" in r["style"]
                    else "audio as-is" if r["prio"] == "EVAL" else "codec tokens + transcript, Parquet zstd" if keep_h else "-")
        out.append({
            "priority": r["prio"],
            "dataset": r["id"],
            "what_it_is": r["what"],
            "style": r["style"],
            "used_for": r["use"],
            "licence": r["lic"] or "none on card",
            "commercial_use": "no" if "nc" in (r["lic"] or "").lower() else ("check" if not r["lic"] or r["lic"] == "other" else "yes"),
            "access": {"auto": "click to accept", "manual": "owner approval"}.get(r["meta"].get("gated"), "open"),
            "hours_reported": r.get("hours") or "",
            "hours_our_languages_est": round(sum(hours_ours.values())) if hours_ours else (round(r["hours"]) if r.get("hours") and not r["per"] else ""),
            "hours_by_language_est": "; ".join(f"{k}:{v:,.0f}" for k, v in sorted(hours_ours.items())),
            "clips_our_languages": sum(v for k, v in r["clips"].items()) or "",
            "raw_gb_our_languages": round(raw, 1),
            "raw_gb_by_language": "; ".join(f"{k}:{v / 1e9:.1f}" for k, v in sorted(r["per"].items())),
            "raw_mb_per_hour": round(r["gb_h"] * 1000) if r["gb_h"] else "",
            "v01_hours_kept": round(keep_h) if "tokens" in store_as else "",
            "v01_hours_kept_by_language": r.get("by") or "; ".join(f"{k}:{v:,.0f}" for k, v in sorted(r["kept"].items())),
            "v01_raw_gb_streamed": round(pull_gb, 1) if pull_gb else "",
            "v01_stored_as": store_as,
            "v01_stored_gb": round(stored, 2),
            "times_smaller_than_raw": f"{raw / stored:,.0f}x" if stored and raw / stored >= 2 else "",
            "keep_rule": r["rule"],
            "splits": " ".join(r["splits"]),
            "metadata_fields": " ".join(r["fields"]),
            "total_repo_gb": round(r["total"] / 1e9, 1),
            "last_updated": (r["meta"].get("lastModified") or "")[:10],
            "downloads_30d": r["meta"].get("downloads", ""),
            "url": "https://huggingface.co/datasets/" + r["id"],
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for p in ("P1", "P2", "EVAL"):
        rs = [o for o in out if o["priority"] == p]
        print(f"{p}: {len(rs)} datasets, raw {sum(o['raw_gb_our_languages'] for o in rs):,.1f} GB in our languages"
              f" -> stored {sum(o['v01_stored_gb'] for o in rs):,.2f} GB, {sum(o['v01_hours_kept'] or 0 for o in rs):,} h kept")
    print("streamed:", round(sum(o["v01_raw_gb_streamed"] or 0 for o in out)), "GB; wrote", OUT)


if __name__ == "__main__":
    main()
