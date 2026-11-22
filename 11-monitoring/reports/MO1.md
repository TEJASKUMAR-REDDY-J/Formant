# MO1 · Training metrics

**Status:** in progress. The metric set is coded, tested, and used by TR1's smoke runs. The Trackio dashboard is not set up: it needs a Hugging Face account and a private Space.

## What was done

- [`src/formant/metrics.py`](../../src/formant/metrics.py) and the frozen names in [`metric-set.md`](../metric-set.md).

## How it was checked

- `python -m pytest tests/test_metrics.py`, 4 tests with hand-computed values: masked losses per codebook and language; reporting and reset; code entropy spots a collapsed codebook; expert use per language, dead experts and load.
- Used in four TR1 smoke runs. The language shares it logged match the planned mixture, and it showed Hinglish learning more slowly than the other languages.

## Result

Every smoke run logs the same names. Cost of logging on a GPU is **not measured**.

## What changes next

1. `trackio_sink` against a real Space.
2. Check on a T4 that logging costs under 1% of step time.
3. MO2 alarms on these names.

**T4-hours used:** 0
