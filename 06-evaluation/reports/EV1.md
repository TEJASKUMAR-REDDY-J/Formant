# EV1 · Metrics and test speakers

**Status:** in progress. Metrics are defined, coded and tested. **The test-speaker lists are not frozen:** choosing them needs speaker metadata from gated datasets, which waits for the data go-ahead. DA2 must not start before they are frozen.

## What was done

- [`metric-spec.md`](../metric-spec.md) and [`src/formant/evalkit.py`](../../src/formant/evalkit.py): normalisation, CER/WER, speaker-level bootstrap, turn-taking and barge-in metrics, deterministic test-speaker selection.

## How it was checked

`python -m pytest tests/test_evalkit.py`, 6 tests with hand-computed answers: nukta and joiner spellings match; corpus rate differs from the mean of rates; speaker-level intervals are at least 1.5× wider than clip-level ones when errors depend on the speaker; a scripted conversation gives the expected takeovers, backchannel and talk-over; the speaker selection is order-independent and turns a 1:2 gender pool into a near 1:1 list.

## Result

No model has been scored. The one-command harness and its suites (codec, duplex, thinker) are not written yet: they need audio and models to run against.

## What changes next

1. When data is allowed: read speaker metadata, freeze and hash the lists, hand them to DA2.
2. Replace the speaker-similarity model (no licence on the planned one).
3. Harness command and the smoke suite.

**T4-hours used:** 0
