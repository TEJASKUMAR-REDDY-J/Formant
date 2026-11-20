# PT1 · Thinker baseline — week 1 plan

**Goal:** score Sarvam 30B, at the QZ1 quantisation, on Indic knowledge and on **spoken-style** replies, and write the style spec the thinker must follow.
**Done when:** baseline scores and the style spec are published.
**Needs:** ~EV1 (metric definitions). **GPU:** none (Kaggle T4s run the same GGUF through llama.cpp's CUDA build).

## What "spoken style" means: the spec draft

1. **Answer first.** The first clause carries the answer and has ≤ 8 words, so the talker can start speaking after a few tokens.
2. **≤ 3 short sentences** unless the user asks for more.
3. **No markdown, lists, emoji, URLs or symbols.** Numbers, dates, currency (₹) and units are written as words in the reply's script.
4. **Reply in the user's language.** Code-mix only when the user does, or when asked (Hinglish in Latin or Devanagari script, following the user).
5. **Natural fillers are allowed only at the start,** and only when the plan is late (PT4 trains this).
6. **No thinking traces.** Thinking/reasoning mode is off; any reasoning stays inside the model's hidden state.

## Test set

| Part | Size | Measures |
|---|---|---|
| MILU (Indic multi-domain multiple choice) | 300 questions per language for hi, bn, mr, ta, te, en | Knowledge, and that quantisation did no damage |
| Spoken prompts written by the team | 100 per language + 100 Hinglish, everyday topics from IndicVoices conversations | Style compliance and helpfulness |
| Long-number / date / money prompts | 30 per language | Spoken-number rule |

## Scoring

- **Automatic:**
  - language match (IndicLID);
  - sentence count;
  - markdown or symbol present;
  - digits present;
  - first-clause length;
  - tokens to the end of the first clause (latency).
- **Judge:**
  - pairwise helpfulness against a reference reply, judged by a strong open model run on 2× T4;
  - plus 20 replies per language rated by a native speaker.
- **Speed (with PF1):**
  - time to first token with a **cached system prompt**;
  - tokens per second on the i3.

## Efficiency

- **Prompt-only first.** If a short system prompt (≤ 150 tokens) with 3 examples reaches ≥ 90% style compliance, PT2's QLoRA shrinks to a polish, or is cut.
- **The system prompt's KV is cached once** (llama.cpp prompt cache), so each turn pre-fills only the user's words, which matters on 2 cores.
- **Score the actual quantised GGUF, not fp16.** That is what ships.

## Week

| Day | Work |
|---|---|
| Mon | Write spoken prompts with native speakers; MILU sample |
| Tue | Baseline runs (no style prompt) on Kaggle |
| Wed | Style prompt v1; rerun; compliance checks from EV1 |
| Thu | Judge and native-speaker ratings; i3 timing with PF1 |
| Fri | `reports/PT1.md` (scores, compliance, latency) + `style-spec.md`; decide PT2's size |

## Risks

- **Sarvam 30B's licence or chat template is unclear.** RL1 checks the licence; the template comes from the GGUF metadata.
- **Quantisation hurts one language badly.** Flag it to QZ1 the same day.
