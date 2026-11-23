import pyarrow as pa

from formant.manifest import SCHEMA, validate

ROW = dict(clip_id="a", source="x/y", source_commit="0" * 40, licence="cc-by-4.0", lang="hi", style="read", speaker="s1",
           split="train", duration_s=5.0, lid=.99, snr_db=20., dnsmos=3., cer_agree=.05, synthetic=False, kept=True,
           drop_reason=None, tokenizer=None, filter_version="f1")


def T(*rows):
    return pa.Table.from_pylist([{**ROW, **r} for r in rows], schema=SCHEMA)


def test_valid():
    assert validate(T({}, {"clip_id": "b", "kept": False, "drop_reason": "snr"})) == []


def test_catches_each_problem():
    cases = {"lang": {"lang": "fr"}, "split": {"split": "val"}, "revision": {"source_commit": "main"},
             "duration": {"duration_s": 60.0}, "kept clip has": {"drop_reason": "x"}, "no drop_reason": {"kept": False},
             "no licence": {"licence": " "}}
    for word, change in cases.items():
        assert any(word in p for p in validate(T(change))), (word, validate(T(change)))
    assert any("duplicate" in p for p in validate(T({}, {})))
    assert any("test speaker" in p for p in validate(T({}), {"s1"}))
    assert validate(T({"split": "test"}), {"s1"}) == []
    assert any("schema" in p for p in validate(T({}).drop_columns(["lid"])))
