import random
from collections import Counter

import pytest

from formant.evalkit import barge_in, bootstrap, cer_counts, edits, freeze, normalise, percentile, rate, select_speakers, turns, wer_counts


def test_normalise_unifies_spellings():
    assert normalise("क़लम") == normalise("क़लम")                        # precomposed vs combining nukta
    assert normalise("ড়") == normalise("ড়")
    assert normalise("१२३ रुपये!") == "123 रुपये" and normalise("௧௨") == "12"
    assert normalise("क्‍ष") == normalise("क्ष")                          # zero-width joiner
    assert normalise("  Hello,   WORLD। ") == "hello world"


def test_edits_and_rates():
    assert edits("kitten", "sitting") == 3 and edits("", "abc") == 3 and edits("abc", "abc") == 0
    assert cer_counts("नमस्ते दुनिया", "नमस्तेदुनिया") == (0, 12)               # spacing is not scored
    assert wer_counts("a b c", "a x c d") == (2, 3)
    assert rate([(1, 10), (0, 90)]) == 0.01                                    # corpus rate, not the mean of 10% and 0%
    with pytest.raises(ValueError):
        rate([(0, 0)])


def test_bootstrap_by_speaker_is_wider_and_reproducible():
    rng = random.Random(1)
    items, spk = [], []
    for s in range(12):                                                        # error depends on the speaker
        p = rng.choice([0.02, 0.3])
        for _ in range(30):
            items.append((sum(rng.random() < p for _ in range(20)), 20)); spk.append(s)
    v, lo, hi = bootstrap(items, rate, n=400, groups=spk)
    _, lo2, hi2 = bootstrap(items, rate, n=400)
    assert lo < v < hi and (hi - lo) > 1.5 * (hi2 - lo2)
    assert bootstrap(items, rate, n=100) == bootstrap(items, rate, n=100)


def test_turns():
    user = [(0, 2), (6, 7), (10, 16)]
    agent = [(2.3, 5), (7.1, 9), (12.0, 12.4), (13.0, 15.5)]                   # two replies, one backchannel, one talk-over
    r = turns(user, agent, [2, 7, 16])
    assert (r["takeovers"], r["false_takeovers"], r["backchannels"]) == (2, 1, 1)
    assert r["latencies"] == pytest.approx([0.3, 0.1])
    assert turns([(0, 2), (2.5, 4)], [(3.0, 3.2)], [2])["takeovers"] == 0      # the user went on first
    assert turns([(0, 2)], [(1.9, 3)], [2])["latencies"] == [0.0]              # slightly early is on time


def test_barge_in():
    r = barge_in([(1, 3), (6, 6.3), (9, 12)], [(0, 1.2), (5, 8), (8.5, 10.0)])
    assert r["stops"] == pytest.approx([0.2, 1.0]) and r["within"] == 0.5       # 6-6.3 is a backchannel, not a barge-in
    assert barge_in([(1, 3)], [(4, 5)])["within"] is None
    assert percentile([1, 2, 3, 4], 50) == 2.5 and percentile([], 50) is None


def people(n, lang="hi", seed=0):
    r = random.Random(seed)
    return [dict(speaker=f"{lang}{i}", lang=lang, gender=r.choice(["f", "m", "m"]), age_group=r.choice(["18-30", "30-45", "45+"]),
                 region=r.choice("ABCD"), minutes=r.uniform(1, 9)) for i in range(n)]


def test_speaker_selection():
    rows = people(400) + people(300, "ta", 1)
    a = select_speakers(rows)
    assert set(map(len, a.values())) == {24} and a == select_speakers(list(reversed(rows)))     # order of rows is irrelevant
    g = Counter(r["gender"] for r in rows if r["speaker"] in a["hi"])
    assert abs(g["f"] - g["m"]) <= 4, g                                        # pool is 1:2, selection is near 1:1
    assert len({(r["age_group"], r["region"]) for r in rows if r["speaker"] in a["hi"]}) >= 8
    short = {r["speaker"] for r in rows if r["minutes"] < 2}
    assert not short & set(a["hi"])
    with pytest.raises(ValueError):
        select_speakers(people(10))
    assert freeze(a)[1] == freeze(select_speakers(rows))[1]
