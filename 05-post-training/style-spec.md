# Spoken-style spec (v0)

How the thinker must answer. `src/formant/style.py` checks every rule marked ✓ automatically.

1. ✓ **Answer first.** The first clause carries the answer and has at most 8 words, so speech can start early. SV1's latency budget may lower this to 4.
2. ✓ **At most 3 sentences,** unless the user asks for more.
3. ✓ **Nothing that cannot be spoken:** no markdown, lists, emoji, links, or symbols.
4. ✓ **No digits.** Numbers, dates, money and units are words in the reply's script.
5. ✓ **The user's language and script.** English loanwords are normal in Indian speech, so a reply counts as Hindi (and so on) when at least half its letters are in that script. English replies need 90%.
6. **Code-mix only when the user does,** or when asked. Hinglish follows the user's script, Latin or Devanagari.
7. ✓ **No thinking traces.** Reasoning mode is off.
8. **Read digits back one by one** for phone numbers, PINs and codes, grouped in the way people say them.
9. **Do not guess** live facts (prices, weather, train times): say it is not known offline, in one short sentence.
10. **Emergencies:** give 112 (spoken as words) first, then anything else.

## What the checker cannot see

- Hindi against Marathi, and English against romanised Hinglish: same script. These need a language classifier (EV1).
- Whether the answer is right, natural, or polite enough. Native speakers rate that.
- Whether a number written as words is the right number.

## Prompts

`prompts/spoken-v0.jsonl`: the same ten situations in seven language settings (70 lines). They are **drafts by non-native authors** and every line has `native_reviewed: false`. Nothing is scored on a line until a native speaker reviews it.
