# Formant

An offline, full-duplex voice agent for Indian languages that runs on a budget laptop.

Formant listens and speaks at the same time, the way people do. A small **talker** (~0.6B) runs every 80 ms on the laptop's built-in graphics and owns the timing: when to speak, when to say "haan", when to stop because you cut in. A larger **thinker** (a mixture-of-experts LLM, Sarvam 30B for v0.1) runs on the CPU cores and decides what to say. Everything runs on one Intel i3-10110U with no GPU and no internet.

Named after formants: the resonances of the vocal tract that make each vowel sound like itself. Keeping them intact in every language, frame by frame, is what every part of this system is for.

## Status

**v0.1 in four weeks.** Full-duplex Hindi, English and Hinglish; Bengali, Marathi, Tamil and Telugu through the cascade fallback until v0.2.

- Code: https://github.com/TEJASKUMAR-REDDY-J/Formant
- Project site: `site/index.html`
- Plan board (phases, dependencies, status): `site/plan.html`
- Plan data, the single source of truth: `site/plan-data.js`

## How the repo is organised

Twelve sections run in parallel through four one-week phases. Each section owns one folder:

| Folder | Section | Owns |
|---|---|---|
| `01-data` | Data | sources, quality gates, synthetic dialogues, test sets |
| `02-tokenizer` | Tokenizer & embeddings | audio codec, text vocabulary, code tables |
| `03-architecture` | Architecture | talker, thinker, turn state, thinker–talker link |
| `04-training` | Training | talker pre-training and dialogue training |
| `05-post-training` | Post-training | thinker style, voice lock, coupled fine-tune |
| `06-evaluation` | Evaluation | metrics, harness, Indic-FDB benchmark |
| `07-quantization` | Quantization | GGUF and OpenVINO models for the laptop |
| `08-performance` | Performance | training speed and real-time speed |
| `09-serving` | Serving | the real-time program on the laptop |
| `10-infrastructure` | Infrastructure | Kaggle runner, Hub storage, export, repo tooling |
| `11-monitoring` | Monitoring | dashboards, alarms, probes, runtime telemetry |
| `12-release` | Release | licences, consent, cards, public releases |

`docs/` holds decisions and archived plans. Every folder README lists its scope, inputs, outputs and four phases.

Read [GUIDELINES.md](GUIDELINES.md) before your first commit.

## Hardware

- **Runs on:** Intel i3-10110U (2 cores), UHD 620 graphics, 24 GB DDR4, measured 20.8 GB/s memory copy.
- **Trains on:** Kaggle 2× T4 (fp16), checkpoints and data on the Hugging Face Hub.

## Website

The `site/` folder is a static site with no build step. `vercel.json` at the repo root tells Vercel to serve `site/`, so deploying is: import this repo at vercel.com/new and press Deploy. Every push to `main` redeploys; other branches get preview links.

To look at it locally: `python -m http.server 5178 --directory site`, then open http://localhost:5178.

## Licence

To be chosen in phase RL1 (see `12-release`). Model and data licences are tracked there.
