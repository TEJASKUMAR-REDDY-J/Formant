"""The cascade: recogniser -> thinker -> voice, streamed, with a latency log and instant stop (SV1).

Stages are plain callables, so real models plug in later and tests run without any:
    asr(audio) -> text
    thinker(text) -> iterator of text pieces
    tts(clause) -> iterator of audio chunks
    play(chunk)
"""
import queue
import re
import threading
import time
from dataclasses import dataclass, field

STRONG = "।॥.!?…"
WEAK = ",;:—–"
_NOT_END = re.compile(r"(?:\b(?:dr|mr|mrs|ms|no|vs|rs|st)|\d)\.$", re.I)   # "Dr." and "3." do not end a clause


def clauses(pieces, first_max_words=8, min_words=3):
    """Group streamed text into speakable clauses. The first clause may be cut at `first_max_words` so speech starts
    early; later clauses end at punctuation. A clause is emitted only once the character after it has arrived,
    so "3." followed by "5" is never split."""
    buf, first = "", True
    for p in pieces:
        buf += p
        while True:
            cut = None
            for i, ch in enumerate(buf[:-1]):                          # the last character may still be mid-token
                if buf[i + 1].isspace():
                    head = buf[: i + 1]
                    n = len(head.split())
                    if (ch in STRONG and not _NOT_END.search(head)) or (ch in WEAK and n >= min_words) or \
                            (first and not ch.isspace() and n >= first_max_words):
                        cut = i + 1
                        break
            if cut is None:
                break
            yield buf[:cut].strip()
            buf, first = buf[cut:].lstrip(), False
    if buf.strip():
        yield buf.strip()


@dataclass
class Turn:
    """Timestamps in seconds from the end of the user's speech."""
    text: str = ""
    reply: list = field(default_factory=list)
    asr_done: float = None
    first_token: float = None
    first_clause: float = None
    first_audio: float = None
    done: float = None
    stopped: bool = False


class Cascade:
    def __init__(self, asr, thinker, tts, play, clock=time.perf_counter):
        self.asr, self.thinker, self.tts, self.play, self.clock = asr, thinker, tts, play, clock
        self._stop = threading.Event()
        self.log = []

    def stop(self):
        """Barge-in: nothing more is generated, synthesised or played. Safe from any thread."""
        self._stop.set()

    def run(self, audio):
        self._stop.clear()
        t, t0 = Turn(), self.clock()
        now = lambda: self.clock() - t0
        t.text = self.asr(audio)
        t.asr_done = now()
        q, failed = queue.Queue(), []

        def think():
            try:
                def pieces():
                    for p in self.thinker(t.text):
                        if self._stop.is_set():
                            return
                        if t.first_token is None:
                            t.first_token = now()
                        yield p
                for c in clauses(pieces()):
                    if t.first_clause is None:
                        t.first_clause = now()
                    q.put(c)
            except Exception as e:
                failed.append(e)
            finally:
                q.put(None)

        th = threading.Thread(target=think, daemon=True)
        th.start()
        while (c := q.get()) is not None and not self._stop.is_set():  # voice one clause while the next is being written
            t.reply.append(c)
            for chunk in self.tts(c):
                if self._stop.is_set():
                    break
                if t.first_audio is None:
                    t.first_audio = now()
                self.play(chunk)
        t.stopped = self._stop.is_set()
        th.join(timeout=5)
        t.done = now()
        self.log.append(t)
        if failed:
            raise failed[0]
        return t


def percentiles(turns, name, ps=(50, 95)):
    xs = sorted(v for t in turns if (v := getattr(t, name)) is not None)
    return {p: xs[min(len(xs) - 1, round((len(xs) - 1) * p / 100))] for p in ps} if xs else {}


def first_audio_budget(tokens_per_word, tokens_per_s, words=8, vad=0.2, asr=0.15, prefill=0.3, tts=0.25, out=0.05):
    """Seconds from end of speech to first sound, given the thinker's speed. Everything but the thinker is a target."""
    return vad + asr + prefill + words * tokens_per_word / tokens_per_s + tts + out
