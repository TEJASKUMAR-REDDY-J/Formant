# SV1 · Cascade floor — week 1 plan

**Goal:** a working offline voice agent in all six languages by Friday: recogniser → thinker → TTS, push-to-talk, on the i3. It is the fallback the duplex system must beat, and the voice for Bengali, Marathi, Tamil and Telugu in v0.1.
**Done when:** ≤ 1.5 s p50 response latency on the i3.
**Needs:** ~PF1 (timings), ~QZ1 (thinker quant). **GPU:** none.

## Pipeline

| Stage | Pick | Runs on | Why |
|---|---|---|---|
| Voice activity | Silero VAD | CPU, < 1 ms per 30 ms chunk | Standard; end-of-speech in ~200 ms |
| Recogniser, Indic | IndicConformer (hybrid CTC/RNN-T; per-language large model, or the 600M multilingual if it keeps pace), ONNX/OpenVINO int8, CTC decoding | iGPU, which is free in cascade mode | MIT; trained on IndicVoices, so it handles code-mixing |
| Recogniser, English | Whisper-large-v3-turbo int8 if it keeps pace, else Moonshine-base | iGPU / CPU | Fast English on CPU |
| Thinker | Sarvam 30B, QZ1 setting, llama.cpp server, cached system prompt, streaming | CPU, 3 threads | v0.1 thinker |
| Voice, Hindi and English | Kokoro-82M (Apache-2.0, Hindi + English voices) | CPU | Faster than real time on CPU |
| Voice, bn / mr / ta / te | Indic Parler-TTS (Apache-2.0), OpenVINO int8, sentence-streamed | iGPU | Only open voice covering them; the iGPU is idle in cascade mode |

## Latency plan (p50 target 1.5 s)

| Step | Budget |
|---|---|
| Voice activity end-of-speech | 200 ms |
| Recogniser finalisation (decoding already ran while the user spoke) | 150 ms |
| Thinker first clause: pre-fill only the user turn, then ≤ 8 words (PT1 "answer first") | ~800 ms |
| TTS first audio chunk | ~250 ms |
| Audio out | ~50 ms |

## Efficiency

- **Stream everywhere.** The recogniser decodes during speech. The thinker streams tokens. The TTS speaks per clause, not per reply.
- **Incremental pre-fill.** Stable partial transcripts are pre-filled while the user is still talking (the AR3 idea, tried early here).
- **Hardware split.** The iGPU runs the recogniser and the Indic TTS; the CPU runs the thinker and Kokoro. They never fight over one device.
- **Text normalisation.** Spoken-number normalisation is done by the thinker (PT1), so no separate normaliser is needed.

## Watch (v0.2)

**A tiny-voca-style Indic voice.** tiny-voca (Nov 2026) is a 4.5M-parameter English TTS:
- trained only on synthetic speech;
- 70× faster than real time on 4 CPU threads;
- it cost $9.56 to train.

The same recipe, distilled from Indic Parler-TTS output, would give a CPU-only voice per language in about 20 MB.

## Week

| Day | Work |
|---|---|
| Mon | Audio I/O, Silero VAD, push-to-talk loop; recogniser timing on 6 languages |
| Tue | llama.cpp server with QZ1's draft quant; streaming bridge |
| Wed | Kokoro (hi, en) and Indic Parler-TTS on the iGPU (bn, mr, ta, te) |
| Thu | Latency logging per stage; incremental pre-fill; tune |
| Fri | Demo in all six languages; `reports/SV1.md` with p50/p95 per stage |

## Risks

- **Indic Parler-TTS is too slow on the UHD 620.** Fall back to sentence-level pre-synthesis while the thinker writes, and flag the tiny Indic voice for v0.2.
- **Kokoro's Hindi voice sounds off.** Use Indic Parler-TTS for Hindi as well.
