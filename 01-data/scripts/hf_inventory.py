"""Build 01-data/sources/hf_datasets.csv: candidate Hugging Face datasets for Formant.

Curated fields (category, use, priority, reported hours, notes) live in SOURCES below.
Licence, gating and sizes are read live from the public Hub API, so re-running this
script refreshes them. No login needed; gated repos still report size.

    python 01-data/scripts/hf_inventory.py
"""
import csv, json, pathlib, re, urllib.parse, urllib.request

API = "https://huggingface.co/api/datasets/"
OUT = pathlib.Path(__file__).resolve().parents[1] / "sources" / "hf_datasets.csv"

# Language folders we care about, mapped to ISO codes.
LANG = {"hindi": "hi", "hi": "hi", "hin": "hi", "hi_in": "hi",
        "bengali": "bn", "bn": "bn", "ben": "bn", "bn_in": "bn",
        "marathi": "mr", "mr": "mr", "mar": "mr", "mr_in": "mr",
        "tamil": "ta", "ta": "ta", "tam": "ta", "ta_in": "ta",
        "telugu": "te", "te": "te", "tel": "te", "te_in": "te",
        "english": "en", "en": "en", "eng": "en", "en_us": "en"}

# id, subfolder holding language dirs ("" = repo root, None = single-language or no split),
# category, languages, use in Formant, priority, reported hours (whole dataset), notes
SOURCES = [
    # --- Voice set: clean single-speaker speech ---
    ("ai4bharat/indicvoices_r", "", "speech-tts", "hi bn mr ta te +17", "DA2 voice set (cleanest natural speech), TK1 codec tests", "P1",
     "1,704 h (22 langs, 9-175 h each)", "TTS-quality subset of IndicVoices; 10,496 speakers."),
    ("ai4bharat/IndicVoices", "", "speech-natural", "hi bn mr ta te +17", "DA2 voice set; DA1 conversation timing from its conversational part", "P1",
     "23.7k h collected, 11.2k h transcribed (22 langs)", "Read 8%, extempore 76%, conversational 16%. Main source of real Indian conversation."),
    ("ai4bharat/Kathbath", "", "speech-read", "hi bn mr ta te +7", "DA2 voice set (read speech)", "P1",
     "1,684 h (12 langs)", "Human-labelled read speech."),
    ("ai4bharat/Rasa", "", "speech-tts-expressive", "hi bn mr ta te +4", "PT3 voice-lock candidates; expressive prosody", "P1",
     "≥ 20 h per speaker", "Expressive studio TTS speech; check per-speaker licence notes before voice lock."),
    ("ai4bharat/NPTEL", "", "speech-english-indian", "en (Indian accent) + indic text", "DA2 Indian-accented English (En-Indic folder = English lectures)", "P1",
     "44.4k h (whole BhasaAnuvaad collection)", "Lecture speech; use the En-Indic part for Indian English. Single-speaker, long-form, some room echo."),
    ("SPRINGLab/IndicTTS-English", None, "speech-tts", "en (Indian accent)", "DA2 Indian English, clean studio", "P2",
     "", "IIT Madras Indic TTS English. No licence on the card: confirm before use (RL1)."),
    ("SPRINGLab/IndicTTS-Hindi", None, "speech-tts", "hi", "DA2 clean studio Hindi; SV1 cascade voice", "P2",
     "~10.3 h", "No licence on the card: confirm before use (RL1)."),
    ("SPRINGLab/IndicTTS_Bengali", None, "speech-tts", "bn", "DA2 clean studio Bengali", "P2", "", "CC-BY-4.0 on the card."),
    ("SPRINGLab/IndicTTS_Tamil", None, "speech-tts", "ta", "DA2 clean studio Tamil", "P2", "", "CC-BY-4.0 on the card."),
    ("SPRINGLab/IndicTTS_Telugu", None, "speech-tts", "te", "DA2 clean studio Telugu", "P2", "", "No licence on the card: confirm before use (RL1)."),
    # --- More natural / found speech ---
    ("ai4bharat/Shrutilipi", "", "speech-news", "hi bn mr ta te +7", "DA2 top-up (broadcast news)", "P2",
     "6,400+ h (12 langs)", "All India Radio news; formal style, mixed audio quality. Hindi-heavy."),
    ("ARTPARK-IISc/Vaani-transcription-part", "audio", "speech-spontaneous", "hi bn mr ta te en +80", "DA2 spontaneous, dialect-diverse speech", "P2",
     "2,122 h transcribed (86 langs)", "Image-prompted spontaneous speech, phone-quality; good for robustness."),
    ("ARTPARK-IISc/Vaani", "audio", "speech-spontaneous", "hi bn mr ta te en +100", "Pseudo-label pool only if transcribed part is not enough", "P3",
     "~31.3k h (mostly untranscribed)", "7.2 TB total; Hindi alone 1.7 TB. Pull selected districts only."),
    ("shiprocket-ai/nirantar", "", "speech-natural", "hi bn mr ta te +", "DA2 top-up", "P3",
     "", "Manual approval gate. Check this is the AI4Bharat Nirantar release and its provenance before use."),
    ("SPRINGLab/Hindi-1482Hrs", None, "speech-read", "hi", "DA2 Hindi top-up", "P3",
     "~1,482 h (from name)", "No licence on the card: confirm before use (RL1)."),
    ("SPRINGLab/SPRING_INX_Bengali_R1", None, "speech-asr", "bn", "DA2 Bengali top-up", "P3", "", "No licence on the card; R2 also exists."),
    ("SPRINGLab/SPRING_INX_Marathi_R1", None, "speech-asr", "mr", "DA2 Marathi top-up", "P3", "", "No licence on the card; R2 also exists."),
    ("SPRINGLab/SPRING_INX_Tamil_R1", None, "speech-asr", "ta", "DA2 Tamil top-up", "P3", "", "No licence on the card; R2 also exists."),
    ("fsicoli/common_voice_22_0", "audio", "speech-read", "hi bn mr ta te en +", "DA2 top-up; more speakers", "P3",
     "", "Community mirror of Mozilla Common Voice 22 (CC0). Official distribution moved off the Hub; verify against Mozilla's release."),
    # --- Code-mixed ---
    ("dianavdavidson/MUCS-Hinglish", None, "speech-codemixed", "hi-en", "DA2 Hinglish speech; EV Hinglish test", "P1",
     "89.9 h train + 5.2 h test", "Community mirror of MUCS 2021 Hindi-English. Confirm original licence."),
    ("krutrim-ai-labs/IndicST", "", "speech-asr-ast", "hi bn mr ta te en +", "Reference manifests (built from 14 public sets)", "P3",
     "10.8k h train + 1.1k h eval", "Krutrim licence ('other'); mostly re-packages sources already listed."),
    # --- Conversation / duplex ---
    ("pengyizhou/seamless-interaction-audio-only", None, "speech-dyadic", "en", "DA1 English turn-taking statistics; TR3 English duplex", "P2",
     "audio of ~4,000 h", "Audio-only copy of Meta Seamless Interaction. CC-BY-NC: research use only, cannot ship in commercial weights."),
    ("facebook/seamless-interaction", None, "video-dyadic", "en", "Source of the audio-only copy; do not pull (video)", "X",
     "4,000+ h", "25.6 TB with video. CC-BY-NC."),
    ("amphion/Emilia-Dataset", "Emilia-YODAS", "speech-spontaneous", "en zh de fr ja ko", "English spontaneous speech subset if NPTEL + Svarah-style data fall short", "P3",
     "215k h (Emilia 101k + YODAS 114k)", "Emilia-YODAS part is CC-BY-4.0; the original Emilia part is CC-BY-NC. Pull a few hundred hours of EN at most."),
    # --- Evaluation only (never train) ---
    ("google/fleurs", "data", "eval-speech", "hi bn mr ta te en +96", "EV1 test sets; TK1 codec round-trip", "EVAL",
     "~10 h per language", "Read speech, standard benchmark."),
    ("ai4bharat/Svarah", None, "eval-speech", "en (Indian accent)", "EV Indian English test", "EVAL", "9.6 h, 117 speakers", "No licence on the card: check terms."),
    ("ai4bharat/Lahaja", None, "eval-speech", "hi (accents)", "EV Hindi accent test", "EVAL", "12.5 h, 132 speakers", "MIT."),
    ("ARTPARK-IISc/Vaani-Benchmark-V1.0", "", "eval-speech", "multi", "EV dialect robustness", "EVAL", "", "CC-BY-4.0."),
    # --- Text ---
    ("ai4bharat/sangraha", "verified", "text-pretrain", "hi bn mr ta te en +16", "TK2 Indic vocabulary merges; thinker text", "P1",
     "", "Verified web + PDF text. Pull only the six language folders listed."),
    ("ai4bharat/indic-align", None, "text-instruct", "hi bn mr ta te +", "PT2 thinker spoken-style tuning", "P2", "", "Instruction and safety data."),
    ("Abhishekcr448/Hinglish-Everyday-Conversations-1M", None, "text-dialogue", "hi-en (romanised)", "DA2 seed scripts for Hinglish synthetic dialogues", "P2",
     "", "Synthetic text, MIT. Quality spot-check needed."),
    ("ai4bharat/IN22-Conv", None, "eval-text", "hi bn mr ta te en +16", "EV conversational translation check for the thinker", "EVAL", "", "Small benchmark."),
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
        name = e["path"].split("/")[-1].lower()
        code = LANG.get(name) or ("en" if name == "en-indic" else None)
        if e.get("type") == "directory" and code:
            out[code] = out.get(code, 0) + size(repo, e["path"])
    return out


def main():
    rows = []
    for repo, sub, cat, langs, use, prio, hours, notes in SOURCES:
        meta = get(urllib.parse.quote(repo, safe="/") + "?expand[]=gated&expand[]=cardData&expand[]=tags")
        card, tags = meta.get("cardData") or {}, meta.get("tags") or []
        lic = card.get("license") or [t.split(":", 1)[1] for t in tags if t.startswith("license:")]
        lic = ",".join(lic) if isinstance(lic, list) else lic
        total = size(repo)
        per = lang_sizes(repo, sub) if sub is not None else {}
        ours = sum(per.values()) if per else total
        rows.append({
            "hf_id": repo,
            "url": "https://huggingface.co/datasets/" + repo,
            "category": cat,
            "languages": langs,
            "use_in_formant": use,
            "priority": prio,
            "licence": lic or "none on card",
            "commercial_ok": "no" if "nc" in (lic or "").lower() else ("check" if not lic or lic == "other" else "yes"),
            "gated": {"auto": "yes (click to accept)", "manual": "yes (manual approval)"}.get(meta.get("gated"), "no"),
            "total_size_gb": round(total / 1e9, 1),
            "our_languages_size_gb": round(ours / 1e9, 1),
            "size_by_language_gb": "; ".join(f"{k}:{v / 1e9:.1f}" for k, v in sorted(per.items())) or "",
            "hours_reported": hours,
            "notes": notes,
        })
        print(f"{repo:55s} {rows[-1]['licence']:14s} {rows[-1]['total_size_gb']:>9} GB  ours {rows[-1]['our_languages_size_gb']:>8} GB")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for p in ("P1", "P2", "P3", "EVAL"):
        gb = sum(r["our_languages_size_gb"] for r in rows if r["priority"] == p)
        print(f"{p}: {sum(r['priority'] == p for r in rows)} datasets, {gb:,.1f} GB in our languages")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
