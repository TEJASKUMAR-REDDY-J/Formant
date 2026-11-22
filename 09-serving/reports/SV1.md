# SV1 · Cascade floor

**Status:** in progress. The pipeline code is written and tested with stand-in stages. No model has been plugged in; that needs about 15 GB of weights, not yet downloaded.

## What was done

- [`src/formant/cascade.py`](../../src/formant/cascade.py): streaming recogniser → thinker → voice pipeline with a clause chunker, per-stage timestamps, and instant stop on barge-in.
- A latency budget that uses TK1's tokens per word and QZ1's tokens per second.

## How it was checked

`python -m pytest tests/test_cascade.py`, 10 tests:
- clauses come out the same however the text is cut into pieces, and no text is lost;
- "Dr." and "3.5" do not end a clause;
- speech starts before the reply is finished;
- a barge-in stops generation, synthesis and playback within 300 ms, nothing plays afterwards, and the next turn works;
- a stage that fails raises an error instead of hanging.

## Result

Calculated seconds from end of speech to first sound, with an 8-word first clause. Everything except the thinker uses the plan's targets (VAD 0.20, recogniser 0.15, pre-fill 0.30, voice 0.25, output 0.05).

| Thinker speed | 4.9 tok/s | 8 tok/s | 11.6 tok/s | 19 tok/s |
|---|---|---|---|---|
| English | 2.9 | 2.1 | 1.8 | 1.5 |
| Hindi | 3.2 | 2.4 | 1.9 | 1.5 |
| Bengali | 3.6 | 2.6 | 2.1 | 1.6 |
| Marathi | 4.2 | 2.9 | 2.3 | 1.8 |
| Tamil | 4.7 | 3.3 | 2.6 | 1.9 |
| Telugu | 4.3 | 3.0 | 2.4 | 1.8 |

11.6 and 19 tokens/s are QZ1's theoretical bounds with the whole memory bus, which the cascade can have because the talker is not running. Real speed will be lower.

**The ≤ 1.5 s p50 target is not reachable as written:** even the best theoretical case only touches it in English and Hindi. Options, cheapest first:

1. **Shorter first clause:** 4 words instead of 8 saves 0.3–1.0 s at 11.6 tok/s. PT1's style spec sets this number.
2. **Draft while the user is still talking,** from stable partial transcripts. It removes most of pre-fill and some of the first clause. It is already planned as AR3.
3. **A short spoken acknowledgement** ("हाँ…") while the thinker starts. It hides the wait rather than removing it.
4. **Trim the thinker's vocabulary** (QZ1): 11.6 → 19 tokens/s bound.

**Proposal:** restate the target as ≤ 2.0 s p50 in Hindi and English, reported per language, and revisit it after QZ1 measures real speed.

## What changes next

1. Confirm the downloads (IndicConformer, Kokoro, Indic Parler-TTS, the QZ1 thinker file). IndicConformer and Indic Parler-TTS are gated: accept their terms once on the Hub.
2. Microphone and speaker I/O, then time each real stage.

**T4-hours used:** 0
