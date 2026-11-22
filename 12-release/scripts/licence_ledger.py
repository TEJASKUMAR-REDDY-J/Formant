"""RL1: rebuild 12-release/licence-ledger.csv from live Hub metadata. Downloads no data and no weights.

    python 12-release/scripts/licence_ledger.py

A tag is only as good as the card: `confirmed` stays "no" until a person has read the licence text and filled in
who and when in CONFIRMED below. Not legal advice; anything unclear is excluded.
"""
import csv
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "12-release" / "licence-ledger.csv"
COLS = ["item", "kind", "role", "licence", "licence_source", "gated", "tag", "why", "confirmed", "revision", "checked"]

MODELS = [  # id, role
    ("Qwen/Qwen3-0.6B", "talker base"), ("sarvamai/sarvam-30b", "thinker"), ("sarvamai/sarvam-30b-gguf", "thinker, official quantised files"),
    ("kyutai/mimi", "codec candidate"), ("LiquidAI/Liquid-Codec", "codec candidate"),
    ("nvidia/nemo-nano-codec-22khz-0.6kbps-12.5fps", "codec candidate"), ("nvidia/nemo-nano-codec-22khz-1.78kbps-12.5fps", "codec candidate"),
    ("Qwen/Qwen3-TTS-Tokenizer-12Hz", "codec candidate"), ("ai4bharat/indic-conformer-600m-multilingual", "recogniser"),
    ("openai/whisper-large-v3-turbo", "recogniser (English, second opinion)"), ("UsefulSensors/moonshine-base", "recogniser (English)"),
    ("ai4bharat/indic-parler-tts", "voice"), ("ai4bharat/IndicF5", "voice"), ("hexgrad/Kokoro-82M", "voice"),
    ("n4ze3m/tiny-voca", "recipe reference"), ("microsoft/wavlm-large", "speaker-similarity metric"),
]
SOFTWARE = [  # not on the Hub: licence from the project's repository
    ("Silero VAD", "voice activity", "mit", "github.com/snakers4/silero-vad"), ("llama.cpp", "thinker runtime", "mit", "github.com/ggml-org/llama.cpp"),
    ("OpenVINO", "talker and codec runtime", "apache-2.0", "github.com/openvinotoolkit/openvino"), ("WebRTC AEC3", "echo cancellation", "bsd-3-clause", "webrtc.org"),
]
OPEN, ATTRIB = {"apache-2.0", "mit", "bsd-3-clause", "cc0-1.0"}, {"cc-by-4.0", "cc-by-3.0"}
NOTES = {
    "dianavdavidson/MUCS-Hinglish": ("train-only", "community mirror: the original MUCS 2021 terms are not confirmed"),
    "pengyizhou/seamless-interaction-audio-only": ("statistics-only", "non-commercial: timing statistics only, never trains released weights"),
    "LiquidAI/Liquid-Codec": ("excluded", "LFM licence 1.0: commercial use is conditional; read it before TK1 may choose this codec"),
    "nvidia/nemo-nano-codec-22khz-0.6kbps-12.5fps": ("excluded", "NVIDIA Open Model License: read it before TK1 may choose this codec"),
    "nvidia/nemo-nano-codec-22khz-1.78kbps-12.5fps": ("excluded", "NVIDIA Open Model License: read it before TK1 may choose this codec"),
}
CONFIRMED = {}  # item -> "name, yyyy-mm-dd" once a person has read the licence text


def tag(licence, kind, role):
    lic = (licence or "").lower()
    if not lic or lic in ("other", "unknown"):
        return "excluded", "no standard licence on the card"
    if "-nc" in lic:
        return "statistics-only", "non-commercial"
    if "EVAL" in role:
        return "evaluation-only", "test set: never trained on"
    if lic in OPEN:
        return "shareable", "permissive"
    if lic in ATTRIB:
        return "shareable", "attribution required in the model or data card"
    return "excluded", f"licence {lic} has not been reviewed"


def demo():
    assert tag("cc-by-nc-4.0", "dataset", "P2")[0] == "statistics-only" and tag(None, "model", "x")[0] == "excluded"
    assert tag("other", "model", "x")[0] == "excluded" and tag("cc-by-4.0", "dataset", "EVAL: x")[0] == "evaluation-only"
    assert tag("cc-by-sa-4.0", "dataset", "P1")[0] == "excluded", "share-alike must be reviewed, not waved through"


def get(kind, repo):
    u = f"https://huggingface.co/api/{kind}s/{repo}?expand[]=gated&expand[]=cardData&expand[]=sha"
    with urllib.request.urlopen(u, timeout=60) as r:
        return json.load(r)


def main():
    import time
    demo()
    today = time.strftime("%Y-%m-%d")
    data = [(r["dataset"], f"{r['priority']}: {r['used_for']}") for r in csv.DictReader(open(ROOT / "01-data/sources/hf_datasets.csv", encoding="utf-8"))]
    rows = []
    for kind, items in (("dataset", data), ("model", MODELS)):
        for repo, role in items:
            m = get(kind, repo)
            card = m.get("cardData") or {}
            lic = card.get("license")
            lic = ",".join(lic) if isinstance(lic, list) else lic
            shown = f"{lic} ({card['license_name']})" if card.get("license_name") else lic or "none on card"
            t, why = NOTES.get(repo) or tag(lic, kind, role)
            rows.append(dict(zip(COLS, [repo, kind, role, shown, "Hub card", {"auto": "click to accept", "manual": "owner approval"}.get(m.get("gated"), "open"),
                                        t, why, CONFIRMED.get(repo, "no"), (m.get("sha") or "")[:12], today])))
    for name, role, lic, src in SOFTWARE:
        t, why = tag(lic, "software", role)
        rows.append(dict(zip(COLS, [name, "software", role, lic, src, "open", t, why, CONFIRMED.get(name, "no"), "", today])))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(rows)
    n = {}
    for r in rows:
        n[(r["kind"], r["tag"])] = n.get((r["kind"], r["tag"]), 0) + 1
    for k in sorted(n):
        print(*k, n[k])
    print("excluded:", [r["item"] for r in rows if r["tag"] == "excluded"])


if __name__ == "__main__":
    main()
