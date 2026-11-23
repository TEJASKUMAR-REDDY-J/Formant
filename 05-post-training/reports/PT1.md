# PT1 · Thinker baseline

**Status:** in progress. The style spec and its checker are done. No baseline score exists: it needs the thinker's weights and the MILU test set, and neither has been downloaded.

## What was done

- [`style-spec.md`](../style-spec.md): ten rules, seven of them checked automatically.
- [`src/formant/style.py`](../../src/formant/style.py): the checker and a per-language summary.
- [`prompts/spoken-v0.jsonl`](../prompts/spoken-v0.jsonl): 70 draft prompts, all waiting for native review.

## How it was checked

`python -m pytest tests/test_style.py`, 24 tests: nine good replies across the seven settings pass; thirteen bad ones fail for the right reason; the prompt file is complete and parallel across languages.

One test caught a real mistake in the first version: ordinary Hindi with two English words ("mobile recharge") was rejected by a 70% script threshold. It is now "at least half".

## Result

No thinker numbers yet.

## What changes next

1. Native speakers review the prompts and write the rest (100 per language).
2. Run the prompts through Sarvam 30B (Apache-2.0) on Kaggle with and without a style prompt, once QZ1 picks a file.
3. Decide whether PT2's fine-tuning is needed: not if a short system prompt reaches 90% compliance.
4. Settle the first-clause limit with SV1.

**T4-hours used:** 0
