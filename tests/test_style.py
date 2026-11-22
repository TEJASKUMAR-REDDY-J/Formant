import json
import pathlib

import pytest

from formant.style import check, summary

ROOT = pathlib.Path(__file__).resolve().parents[1]

GOOD = [
    ("hi", "हाँ, कल बारिश होगी। छाता साथ रख लेना।"),
    ("en", "Yes, the shop is open. It closes at nine tonight."),
    ("bn", "হ্যাঁ, কাল বৃষ্টি হবে। ছাতা নিয়ে যেও।"),
    ("mr", "हो, उद्या पाऊस पडेल। छत्री घेऊन जा।"),
    ("ta", "ஆமாம், நாளைக்கு மழை வரும். குடை எடுத்துட்டு போங்க."),
    ("te", "అవును, రేపు వర్షం పడుతుంది. గొడుగు తీసుకెళ్ళండి."),
    ("hi-en", "Haan, meeting kal subah hai. Das baje office aa jana."),
    ("hi-en", "हाँ, meeting कल सुबह है।"),
    ("hi", "हाँ, आपका mobile recharge हो गया है, अब सब कुछ ठीक चल रहा है।"),
]
BAD = [
    ("en", "It costs 500 rupees.", "digits"), ("hi", "किराया ५०० रुपये है।", "digits"), ("en", "Sure! 🙂 Done.", "emoji"),
    ("en", "Here you go:\n- milk\n- bread", "markdown"), ("en", "Use **salt**.", "markdown"), ("en", "See https://x.com now.", "url"),
    ("en", "Fifty% off.", "symbols"), ("en", "One. Two. Three. Four.", "sentences"),
    ("en", "Well if you look at what the weather is doing tomorrow you may need one.", "first clause"),
    ("en", "<think>hm</think> Yes.", "thinking"), ("hi", "Yes, it will rain tomorrow.", "script"), ("en", "हाँ, बारिश होगी।", "script"),
    ("ta", "", "empty"),
]


@pytest.mark.parametrize("lang,text", GOOD)
def test_good(lang, text):
    assert check(text, lang)["problems"] == []


@pytest.mark.parametrize("lang,text,word", BAD)
def test_bad(lang, text, word):
    assert any(word in p for p in check(text, lang)["problems"]), check(text, lang)


def test_summary():
    s = summary([("en", check("Yes.", "en")), ("en", check("It is 5.", "en"))])
    assert s["en"]["compliance"] == 0.5 and "digits" in s["en"]["top_problem"]


def test_prompt_file_is_complete():
    rows = [json.loads(x) for x in (ROOT / "05-post-training/prompts/spoken-v0.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len({r["id"] for r in rows}) == len(rows)
    per = {g: [r for r in rows if r["lang"] == g] for g in ["hi", "en", "bn", "mr", "ta", "te", "hi-en"]}
    assert {len(v) for v in per.values()} == {10} and sum(map(len, per.values())) == len(rows)
    for rs in per.values():                                                   # the same ten situations in every language
        assert sorted(r["topic"] for r in rs) == sorted(r["topic"] for r in per["en"])
    assert all(r["native_reviewed"] is False for r in rows)
