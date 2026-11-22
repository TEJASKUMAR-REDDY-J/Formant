"""The one manifest schema shared by data, tokens and evaluation (IN1; 01-data/DATA_PLAN.md section 3)."""
import pyarrow as pa
import pyarrow.compute as pc

LANGS = ["hi", "en", "bn", "mr", "ta", "te", "hi-en"]
SPLITS = ["train", "dev", "test"]
S, F = pa.string(), pa.float32()
req = lambda name, t: pa.field(name, t, nullable=False)

SCHEMA = pa.schema([
    req("clip_id", S), req("source", S), req("source_commit", S),   # Hub repo and the 40-hex revision the clip came from
    req("licence", S), req("lang", S), pa.field("style", S),
    req("speaker", S),                                              # salted hash, never the source id
    req("split", S), req("duration_s", F),
    pa.field("lid", F), pa.field("snr_db", F), pa.field("dnsmos", F), pa.field("cer_agree", F),
    req("synthetic", pa.bool_()), req("kept", pa.bool_()), pa.field("drop_reason", S),
    pa.field("tokenizer", S),                                       # codec hash, once tokenised
    req("filter_version", S),
])


def validate(table, test_speakers=frozenset()):
    """Return a list of problems (empty = valid): types, nulls, vocabularies, ranges and test-speaker leakage."""
    if not table.schema.equals(SCHEMA):
        have, want = set(table.schema.names), set(SCHEMA.names)
        return [f"schema differs: missing {sorted(want - have)}, extra {sorted(have - want)}"
                + ("" if have != want else ", or types / order / nullability")]
    col = table.column
    bad = [f"{f.name}: {col(f.name).null_count} nulls" for f in SCHEMA if not f.nullable and col(f.name).null_count]
    count = lambda mask: pc.sum(pc.fill_null(mask, False)).as_py() or 0
    isin = lambda c, vals: pc.is_in(col(c), value_set=pa.array(vals, S))
    kept = col("kept")
    checks = {
        "lang not in the plan": pc.invert(isin("lang", LANGS)),
        "unknown split": pc.invert(isin("split", SPLITS)),
        "source_commit is not a 40-hex revision": pc.invert(pc.match_substring_regex(col("source_commit"), "^[0-9a-f]{40}$")),
        "duration outside 2-30 s in a kept clip": pc.and_(kept, pc.or_(pc.less(col("duration_s"), 2), pc.greater(col("duration_s"), 30))),
        "kept clip has a drop_reason": pc.and_(kept, pc.is_valid(col("drop_reason"))),
        "dropped clip has no drop_reason": pc.and_(pc.invert(kept), pc.is_null(col("drop_reason"))),
        "no licence on a kept clip": pc.and_(kept, pc.equal(pc.utf8_trim_whitespace(col("licence")), "")),
    }
    bad += [f"{name}: {k} rows" for name, m in checks.items() if (k := count(m))]
    dup = table.num_rows - pc.count_distinct(col("clip_id")).as_py()
    if dup:
        bad.append(f"duplicate clip_id: {dup} rows")
    if test_speakers:
        leak = count(pc.and_(isin("speaker", list(test_speakers)), pc.and_(kept, pc.not_equal(col("split"), "test"))))
        if leak:
            bad.append(f"test speaker in training data: {leak} rows")
    return bad
