import threading
import time

import pytest

from formant.cascade import Cascade, clauses, first_audio_budget, percentiles


def stream(text, n=3):
    return (text[i:i + n] for i in range(0, len(text), n))


@pytest.mark.parametrize("n", [1, 2, 3, 7, 1000])
def test_clauses_do_not_depend_on_how_text_arrives(n):
    s = "हाँ, कल बारिश होगी। छाता साथ रख लेना, वरना भीग जाओगे।"
    assert list(clauses(stream(s, n))) == ["हाँ, कल बारिश होगी।", "छाता साथ रख लेना,", "वरना भीग जाओगे।"]


def test_clause_rules():
    assert list(clauses(stream("Dr. Rao is in. Come at five."))) == ["Dr. Rao is in.", "Come at five."]
    assert list(clauses(stream("It weighs 3.5 kilos. Fine."))) == ["It weighs 3.5 kilos.", "Fine."]
    out = list(clauses(stream("one two three four five six seven eight nine ten eleven. Twelve")))
    assert out == ["one two three four five six seven eight", "nine ten eleven.", "Twelve"]      # only the first is cut early
    assert list(clauses(stream("   "))) == [] and list(clauses(iter(["no punctuation"]))) == ["no punctuation"]
    s = "One, two three four, five. Six seven eight nine ten."
    assert " ".join(clauses(stream(s))) == s                                                      # nothing is lost


def make(delay=0.0, reply="Yes, it will rain tomorrow. Take an umbrella. Stay dry.", **kw):
    played = []

    def thinker(_):
        for p in stream(reply, 4):
            time.sleep(delay)
            yield p

    def tts(c):
        for i in range(3):
            time.sleep(delay)
            yield f"{c}#{i}"
    return Cascade(lambda a: "q", kw.get("thinker", thinker), kw.get("tts", tts), played.append), played


def test_streams_before_the_reply_is_finished():
    c, played = make(delay=0.01)
    t = c.run(b"")
    assert t.reply[0] == "Yes, it will rain tomorrow." and len(played) == 3 * len(t.reply)
    assert t.asr_done <= t.first_token <= t.first_clause <= t.first_audio < 0.75 * t.done
    assert percentiles(c.log, "first_audio")[50] == t.first_audio


def test_barge_in_stops_everything_quickly():
    c, played = make(delay=0.03, reply="word " * 400 + ".")
    threading.Timer(0.6, c.stop).start()
    t0 = time.perf_counter()
    t = c.run(b"")
    took = time.perf_counter() - t0
    assert t.stopped and took < 0.6 + 0.3, took
    n = len(played)
    time.sleep(0.15)
    assert len(played) == n                                                                       # nothing plays afterwards
    c.thinker = lambda _: iter(["Fine."])
    assert not c.run(b"").stopped                                                                 # and the next turn works


def test_a_failing_stage_raises_instead_of_hanging():
    def bad(_):
        yield "Yes, this starts. "
        raise RuntimeError("thinker died")
    c, played = make(thinker=bad)
    with pytest.raises(RuntimeError, match="thinker died"):
        c.run(b"")


def test_budget():
    assert first_audio_budget(1.4, 1e9) == pytest.approx(0.95)
    assert first_audio_budget(1.4, 3) > 4 and first_audio_budget(1.4, 12) < 2
