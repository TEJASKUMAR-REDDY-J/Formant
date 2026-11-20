/* Single source of truth for the Formant plan.
   plan.html renders this file; folder READMEs are generated from it.
   Edit here, then update the matching folder README.
   needs: "XX1" = must be done before this phase starts (earlier week);
          "~XX1" = same-week handoff, needs early output only.
   status: "todo" | "doing" | "done" | "cut" */
window.PLAN = {
  name: "Formant",
  version: "v9",
  updated: "2026-11-20",
  goal: "Formant v0.1 in four weeks: an offline voice agent on one i3 laptop that holds a full-duplex conversation in Hindi and Hinglish, with Bengali, Marathi, Tamil and Telugu answered through the cascade fallback until v0.2.",
  constraints: [
    "Runtime: Intel i3-10110U, 2 cores, UHD 620 graphics, 24 GB DDR4, measured 20.8 GB/s memory copy. No GPU, no cloud.",
    "Training: Kaggle 2× T4 (fp16 only, no bf16), 12-hour sessions, ~30 session-hours a week per account (~60 T4-hours).",
    "Every phase lasts one week. All twelve sections run in parallel, so each week has twelve deliverables.",
    "Work lives on the F drive (F:\\formant). Nothing on C or D."
  ],
  phases: [
    { n: 1, title: "Foundations", week: "Week 1", theme: "Decide and measure. Licences, pilot data, codec choice, specs, baselines, a working cascade demo, the repo and the site." },
    { n: 2, title: "Build", week: "Week 2", theme: "Pipelines at scale. Voice set and synthetic dialogues, frozen tokenizers, thinker tuning, the audio loop, the eval harness, training launched." },
    { n: 3, title: "Train", week: "Week 3", theme: "Models learn. Speech pre-training finishes, dialogue training, voice lock, first quantised talker running on the laptop." },
    { n: 4, title: "Ship", week: "Week 4", theme: "Put it together. Coupled agent, evaluation against baselines, quantised bundle, public v0.1 release." }
  ],
  sections: [
    {
      code: "DA", num: "01", folder: "01-data", name: "Data",
      means: "All audio and text the models learn from: licensed sources, quality gates, speaker splitting, conversation timing statistics, synthetic dialogues, thinker text and the held-out tests.",
      scope: ["~1.5–2k h single-speaker speech as codec tokens (Hindi ~800 h, 300 h each other language)", "≥ 200 h two-channel Hindi/Hinglish dialogue (synthetic + split real)", "Spoken-style Q&A text for the thinker", "Speaker-disjoint test sets"],
      out: ["5–10k h voice set and all-language dialogue (v0.2)", "Buying data or recording new conversations"],
      expect: ["Hindi is the strongest language; Tamil and Telugu have fewer clean hours", "Real two-party Indic conversation is scarce, so synthetic speech carries most of the duplex signal", "Data is the biggest schedule risk in week 2"],
      inputs: ["Licence ledger (12-release)", "Frozen codec (02-tokenizer)", "Test-speaker lists (06-evaluation)"],
      outputs: ["Token shards and manifests on the Hub → 04-training, 05-post-training", "Timing statistics → 03-architecture, 06-evaluation"],
      cells: [
        { id: "DA1", title: "Licences and pilot", goal: "Licence ledger per source. Run 10 h per language through every gate: language ID ≥ 0.9, SNR ≥ 15 dB, 2–30 s clips, two-recogniser CER agreement ≤ 15%, PII masking. Measure gaps, overlaps and backchannels on pilot conversations.", done: "Pilot manifest on the Hub; gate pass rate and cost per 1,000 h for each step; first timing statistics.", needs: ["~IN1", "~EV1", "~RL1"], gpu: "", status: "todo" },
        { id: "DA2", title: "Voice set and dialogues v0", goal: "Ingest ~1.5–2k h and tokenise with the chosen codec. Generate ≥ 200 h of Hindi/Hinglish two-channel dialogue: LLM-written scripts, open Indic TTS voices, DA1 timings. Split real conversations with the speaker splitter. Build the thinker's spoken-style text set.", done: "≥ 1.5k h of tokens and ≥ 200 h of dialogue on the Hub, every shard tagged with source, licence and tokenizer hash.", needs: ["DA1", "TK1", "EV1"], gpu: "60–80", status: "todo" },
        { id: "DA3", title: "Grow and check", goal: "Keep shards flowing into training runs; top up the weaker languages; native-speaker spot-check of 100 synthetic clips per language.", done: "Naturalness spot-check ≥ 3.5/5; hours report per language.", needs: ["DA2"], gpu: "20–30", status: "todo" },
        { id: "DA4", title: "Freeze and document", goal: "Freeze v0.1 splits; write data cards; publish the recipe (scripts and manifests, not audio).", done: "Data cards and recipe in the repo; someone else can rebuild the manifests.", needs: ["DA3", "RL3"], gpu: "", status: "todo" }
      ]
    },
    {
      code: "TK", num: "02", folder: "02-tokenizer", name: "Tokenizer & embeddings",
      merged: "Embedding is merged in here: it is the vocabulary and code tables these tokenizers feed, about two days of work on its own.",
      means: "The audio codec that turns speech into tokens and back, the text vocabulary for the talker's inner-monologue stream, and the embedding tables both feed.",
      scope: ["Codec bake-off: Mimi vs LiquidCodec vs NVIDIA's multilingual codec", "Trim and extend the text vocabulary (~40k tokens with Indic merges)", "Audio code tables for the user and own streams", "Decoder-only codec fine-tune if a language fails"],
      out: ["Training a codec from scratch", "Kronecker-factored tables (they save storage, not memory bandwidth)"],
      expect: ["Retroflex, aspirated and geminate consonants are where codecs lose detail", "Trimming Qwen3's 151,936-token output head to ~40k cuts its read from ~1.9 to ~0.5 GB/s, the cheapest speed win in the project", "Freezing the encoder and tuning only the decoder keeps every token already made valid"],
      inputs: ["Pilot clips (01-data)", "Bandwidth budget (08-performance)"],
      outputs: ["Versioned codec and text tokenizer → 01-data, 04-training, 07-quantization"],
      cells: [
        { id: "TK1", title: "Codec and vocabulary audit", goal: "Round-trip 50 clips per language through each codec: CER, speaker similarity, PESQ/STOI, plus decode speed on the UHD 620. Count tokens per word and per second for the Qwen3, Sarvam and Gemma tokenizers.", done: "Codec chosen by Friday with per-language numbers; fertility table.", needs: ["~DA1", "~PF1"], gpu: "2", status: "todo" },
        { id: "TK2", title: "Freeze tokenizers", goal: "Trim the vocabulary to the tokens Indic + English text uses, add Indic merges, initialise new rows as the mean of their old pieces; build audio code tables; short warm-up with the body frozen.", done: "Both tokenizers hashed and versioned; ≤ 2 text tokens per word in every language; Hindi text loss within 5% after warm-up.", needs: ["TK1", "AR1"], gpu: "5", status: "todo" },
        { id: "TK3", title: "Decoder fix if needed", goal: "Only if a language failed TK1: fine-tune the codec decoder on IndicVoices-R with the encoder frozen.", done: "Round-trip CER within 2 points of the original audio for every language, or no fix needed.", needs: ["TK1", "DA2"], gpu: "0–30", status: "todo" },
        { id: "TK4", title: "Tokenizer card", goal: "Publish both tokenizers with round-trip and fertility tables; list v0.2 vocabulary changes for more languages.", done: "Tokenizer card in the release.", needs: ["TK2", "TK3"], gpu: "", status: "todo" }
      ]
    },
    {
      code: "AR", num: "03", folder: "03-architecture", name: "Architecture",
      means: "The shape of every model and how they connect: the talker, its codebook head, the thinker, the turn-state signals and the thinker–talker link.",
      scope: ["Talker: Qwen3-0.6B over 80 ms frames, user + own audio streams, inner-monologue text", "Codebook head: depth transformer for RVQ codecs, parallel heads for FSQ codecs", "Thinker: Sarvam 30B (2.4B active) on the CPU", "Text-only thinker → talker coupling"],
      out: ["Hidden-state coupling adapters (v0.2)", "Course 120B slice as the thinker (v0.2, depends on the course run)"],
      expect: ["The talker shape is well trodden (Moshi pattern) and low risk", "Coupling is the novel part and the main design risk", "A 2B talker such as LFM3-Audio-2B would read ~1 GB every 80 ms at 4 bits, about 12.5 GB/s, which is too much for the i3's shared bus"],
      inputs: ["Measured budgets (08-performance)", "Codec choice (02-tokenizer)", "Thinker speed (07-quantization)"],
      outputs: ["Spec sheets and interface definitions → 04-training, 05-post-training, 09-serving"],
      cells: [
        { id: "AR1", title: "Talker spec", goal: "Fix layers, width, streams, acoustic delay, context (3–5 min, sliding window) and the codebook head for the chosen codec; bytes and FLOPs per frame. Review 2026 duplex-adaptation recipes (D2, Awaken) for initialisation.", done: "Spec sheet that fits the talker's 4.4 GB/s share.", needs: ["~PF1", "~TK1"], gpu: "", status: "todo" },
        { id: "AR2", title: "Thinker and turn state", goal: "Confirm Sarvam 30B at the QZ1 setting. Define the talker's turn-state outputs (end-of-turn, backchannel, barge-in), following plug-in turn detectors such as SoulX-Duplug and X2-Turn.", done: "Thinker fixed for v0.1: ≥ 5 tokens/s on the i3, fits ≤ 14 GB. Turn-state spec written.", needs: ["AR1", "QZ1", "PT1"], gpu: "", status: "todo" },
        { id: "AR3", title: "Coupling interface", goal: "Thinker streams its reply plan as text into the talker's monologue slot; turn-state goes back; the thinker drafts while the user is still talking. Compare with 2026 designs for linking duplex models to external LLMs (Context Spanning, MoshiRAG).", done: "Protocol spec and a working text-coupled loop on a T4.", needs: ["AR2", "TK2"], gpu: "", status: "todo" },
        { id: "AR4", title: "Review and v0.2 design", goal: "Use week-3 results to decide v0.2: adapters, five-language duplex, bigger voice set.", done: "Architecture note with v0.2 decisions.", needs: ["AR3", "TR3", "EV3"], gpu: "", status: "todo" }
      ]
    },
    {
      code: "TR", num: "04", folder: "04-training", name: "Training",
      merged: "New section: the first draft had post-training but no pre-training, which is the largest GPU cost.",
      means: "Pre-training the talker: smoke runs, speech pre-training on the voice set, two-stream dialogue training, robustness.",
      scope: ["Smoke runs on a small model", "0.6B speech pre-training on ~1.5–2k h, 2–3 epochs", "Hindi/Hinglish two-stream dialogue training", "Noise, crosstalk and echo robustness"],
      out: ["Training on 5–10k h (v0.2)", "Duplex training in all five languages (v0.2)"],
      expect: ["About 20–30 T4-hours per epoch on ~2k h at realistic T4 efficiency", "fp16 only, so loss scaling must be watched", "Expect intelligible Hindi speech with natural turn timing; voice quality below Sarvam's Bulbul"],
      inputs: ["Token shards (01-data)", "Frozen tokenizers (02-tokenizer)", "Runner (10-infrastructure)", "Dashboards (11-monitoring)"],
      outputs: ["Talker checkpoints on the Hub → 05-post-training, 07-quantization, 09-serving"],
      cells: [
        { id: "TR1", title: "Smoke runs", goal: "~50M talker on pilot or public codec tokens: check fp16 stability, loss per codebook, resume after a killed session.", done: "Loss falls on every codebook; resume reproduces the curve.", needs: ["~IN1", "~MO1"], gpu: "5", status: "todo" },
        { id: "TR2", title: "Launch pre-training", goal: "Initialise from Qwen3-0.6B with the frozen tables; stream shards as they land; DDP on 2× T4.", done: "Run passes 1 epoch with stable loss; checkpoint every 30–45 min on the Hub.", needs: ["TR1", "AR1", "~TK2", "~DA2", "~PF2"], gpu: "25–35", status: "todo" },
        { id: "TR3", title: "Finish pre-training, dialogue", goal: "Complete 2–3 epochs; then train both streams on Hindi/Hinglish dialogues (synthetic + split real).", done: "Probe CER ≤ 25% in all five languages; Hindi takeover rate ≥ 0.8 on held-out clips.", needs: ["TR2", "DA2", "TK2"], gpu: "60–100", status: "todo" },
        { id: "TR4", title: "Robustness", goal: "Add noise, far-field audio, crosstalk and echo-like leakage; pick the final checkpoint with evaluation.", done: "Noisy CER within 5 points of clean; final checkpoint tagged.", needs: ["TR3", "EV3"], gpu: "10", status: "todo" }
      ]
    },
    {
      code: "PT", num: "05", folder: "05-post-training", name: "Post-training",
      means: "Making trained models behave: spoken-style tuning for the thinker, one consistent voice for the talker, and the talker learning to voice the thinker's plan.",
      scope: ["Thinker QLoRA for spoken-style replies", "Voice lock on one licensed or consenting voice", "Coupled fine-tune (plan text → speech, natural fillers when late)", "Basic refusal behaviour"],
      out: ["Preference or RL tuning for timing (v0.2)", "500 h own-voice set (v0.2)"],
      expect: ["Thinker style tuning is routine and low risk", "Voice lock with ~50–100 h gives a stable voice, not an expressive one"],
      inputs: ["Thinker choice (03-architecture)", "Talker checkpoints (04-training)", "Thinker text (01-data)"],
      outputs: ["Tuned thinker and talker → 07-quantization, 09-serving"],
      cells: [
        { id: "PT1", title: "Thinker baseline", goal: "Score Sarvam 30B on Indic QA with spoken-style prompts; write the style spec: short replies, spoken numbers, code-mixing on request.", done: "Baseline scores and style spec.", needs: ["~EV1"], gpu: "", status: "todo" },
        { id: "PT2", title: "Thinker style tuning", goal: "QLoRA on 2× T4 with the spoken-style set.", done: "Replies under ~3 spoken sentences; Indic QA no worse than baseline.", needs: ["PT1", "~DA2", "~AR2"], gpu: "30–45", status: "todo" },
        { id: "PT3", title: "Voice lock", goal: "Fine-tune the talker on ~50–100 h of one voice with a clear licence or written consent.", done: "Speaker similarity ≥ 0.85 to the reference across languages.", needs: ["TR2", "DA2", "RL1"], gpu: "10–15", status: "todo" },
        { id: "PT4", title: "Coupled fine-tune", goal: "Teacher-force thinker plan text into the monologue slot; train fillers for late plans and stopping on barge-in.", done: "≥ 80% complete replies and p50 latency ≤ 400 ms on a GPU.", needs: ["TR3", "AR3", "PT2"], gpu: "15–25", status: "todo" }
      ]
    },
    {
      code: "EV", num: "06", folder: "06-evaluation", name: "Evaluation",
      means: "How we know it works: automatic metrics, Indic-FDB (our Indian-language full-duplex benchmark), small human panels and comparison with baselines.",
      scope: ["Metric spec and speaker-disjoint test sets", "One-command harness", "Indic-FDB v0 for Hindi/Hinglish", "Comparison with the cascade, Human-1 and a Sarvam cloud sample"],
      out: ["Full blind head-to-head against Sarvam with many raters (v0.2)"],
      expect: ["Automatic MOS predictors are not validated for Indian languages, so they only compare our own versions", "Panels of 2–3 raters per language give direction, not proof"],
      inputs: ["Test speakers (01-data)", "Builds to test (04, 07, 09)"],
      outputs: ["Scores and reports → every section; release numbers → 12-release"],
      cells: [
        { id: "EV1", title: "Metrics and test speakers", goal: "Define every metric; reserve test speakers per language before ingest; harness skeleton.", done: "Metric spec and frozen test-speaker lists.", needs: ["~DA1"], gpu: "", status: "todo" },
        { id: "EV2", title: "Harness and Indic-FDB scripts", goal: "CER from two recognisers, speaker similarity, relative MOS, turn-taking metrics, latency logs. Write Indic-FDB v0 scenarios (pauses, backchannels, barge-in, code-switching, noise) using the methods of Full-Duplex-Bench v3 and M3-DuplexBench.", done: "One command scores the cascade and any checkpoint.", needs: ["EV1", "SV1"], gpu: "5", status: "todo" },
        { id: "EV3", title: "Evaluate during training", goal: "Score probe checkpoints, the tuned thinker and each quantisation step.", done: "Weekly score sheet that TR4 and QZ4 decide on.", needs: ["EV2", "~MO3"], gpu: "5", status: "todo" },
        { id: "EV4", title: "Indic-FDB v0 run", goal: "Run the benchmark on the cascade, Formant duplex, Human-1 (Hindi) and a small Sarvam cloud sample; 2 native raters per language for naturalness.", done: "v0.1 results page with targets and results clearly labelled.", needs: ["EV3", "SV3", "~QZ4"], gpu: "10", status: "todo" }
      ]
    },
    {
      code: "QZ", num: "07", folder: "07-quantization", name: "Quantization",
      means: "Shrinking every model to fit the laptop's RAM and memory bandwidth, measuring the quality each step costs.",
      scope: ["Thinker GGUF sweep with Indic calibration", "Codec decoder in OpenVINO on the iGPU", "Talker int8 (int4 where it holds)", "Final quantised bundle"],
      out: ["Quantisation-aware training (only if a language drops too far)"],
      expect: ["Talker int8 is close to free; int4 may hurt audio", "Thinker at ~3.5 bits loses some quality; Indic calibration text matters"],
      inputs: ["Checkpoints (04, 05)", "Harness (06-evaluation)"],
      outputs: ["GGUF and OpenVINO files → 08-performance, 09-serving, 12-release"],
      cells: [
        { id: "QZ1", title: "Thinker sweep", goal: "Sarvam 30B at Q4_K_M, Q3_K_M and IQ3 with an Indic importance matrix; tokens/s on the i3 and Indic quality.", done: "Speed–quality curve; one setting chosen.", needs: ["~PF1", "~EV1"], gpu: "", status: "todo" },
        { id: "QZ2", title: "Codec on the iGPU", goal: "Export the chosen codec decoder to OpenVINO fp16; save fp16 reference outputs for every component.", done: "Decoder runs well inside one 80 ms frame on the UHD 620.", needs: ["TK1", "PF1"], gpu: "1", status: "todo" },
        { id: "QZ3", title: "Talker int8", goal: "NNCF int8 on the week-2 checkpoint (shapes are fixed); try int4.", done: "CER within 2 points of fp16 on the probe set.", needs: ["TR2", "QZ2", "~TR3"], gpu: "2", status: "todo" },
        { id: "QZ4", title: "Release bundle", goal: "Quantise the final talker and tuned thinker; run the full system against the references.", done: "Every language within 2 CER points of fp16; bundle tagged.", needs: ["QZ3", "~TR4", "~PT4"], gpu: "2", status: "todo" }
      ]
    },
    {
      code: "PF", num: "08", folder: "08-performance", name: "Performance",
      means: "Two things: training speed on T4s, and real-time speed on the i3 (80 ms frame deadline, thinker at ≥ 5 tokens/s).",
      scope: ["Baselines on both machines", "Training speed-ups", "Runtime speed for talker, codec and thinker", "Both models together, sustained"],
      out: ["EAGLE3-style draft head for the thinker (v0.2)"],
      expect: ["T4 has no FlashAttention-2, so use PyTorch SDPA; aim for 1.5–2× over the naive baseline", "The iGPU and CPU share one 20.8 GB/s bus; running both together is the real limit", "Heat and throttling show up in 30-minute runs"],
      inputs: ["Specs (03-architecture)", "Quantised models (07-quantization)"],
      outputs: ["Budgets and measurements → every section"],
      cells: [
        { id: "PF1", title: "Baselines", goal: "Bandwidth (done: 20.8 GB/s). OpenVINO step time for a 0.6B model on the UHD 620; llama.cpp tokens/s for Sarvam 30B; T4 training tokens/s for Qwen3-0.6B.", done: "Baseline sheet every later number is compared to.", needs: [], gpu: "2", status: "doing" },
        { id: "PF2", title: "Training speed", goal: "Sequence packing, SDPA, chunked cross-entropy, gradient checkpointing, DDP on 2× T4, 8-bit AdamW.", done: "≥ 1.5× PF1 tokens/s with an unchanged loss curve.", needs: ["TR1", "PF1"], gpu: "5", status: "todo" },
        { id: "PF3", title: "Runtime speed", goal: "Talker int8 on the iGPU with KV cache and static shapes; thinker thread pinning and incremental prefill.", done: "Talker + head + codec ≤ 60 ms per 80 ms frame; thinker ≥ 5 tokens/s.", needs: ["QZ2", "AR2", "~QZ3"], gpu: "", status: "todo" },
        { id: "PF4", title: "Sustained run", goal: "Both models live for 30 minutes; throttle the thinker to protect the frame deadline; record temperatures.", done: "< 1% missed frames over 30 minutes.", needs: ["PF3", "SV3"], gpu: "", status: "todo" }
      ]
    },
    {
      code: "SV", num: "09", folder: "09-serving", name: "Serving",
      means: "The real-time program on the laptop, not a server: audio in and out every 80 ms, echo cancellation, talker on the iGPU, thinker on the CPU.",
      scope: ["Cascade floor (recogniser → thinker → TTS), the fallback for all languages", "Duplex audio loop with WebRTC AEC3", "Talker in the loop with barge-in", "Coupled agent, one-command launch"],
      out: ["Windows installer and phone port (v0.2)"],
      expect: ["Echo is the biggest unknown: in full duplex the laptop hears its own speakers; demos fall back to a headset", "The cascade is the safety net and the baseline every later build must beat"],
      inputs: ["Quantised models (07)", "Runtime speed work (08)", "Coupling spec (03)"],
      outputs: ["The demo and the runtime → 06-evaluation, 12-release"],
      cells: [
        { id: "SV1", title: "Cascade floor", goal: "Offline recogniser (IndicConformer class) → Sarvam 30B in llama.cpp → open Indic TTS (Indic Parler-TTS or IndicF5), push-to-talk, all five languages.", done: "≤ 1.5 s p50 response latency on the i3.", needs: ["~PF1", "~QZ1"], gpu: "", status: "todo" },
        { id: "SV2", title: "Duplex audio loop", goal: "80 ms frame clock, mic and speaker I/O, WebRTC AEC3, codec decoder on the iGPU, replayed talker output to test the loop.", done: "Plays and listens at once on laptop speakers without hearing itself.", needs: ["SV1", "~QZ2"], gpu: "", status: "todo" },
        { id: "SV3", title: "Talker in the loop", goal: "int8 talker on the iGPU; barge-in stops speech within 300 ms; falls back to the cascade when frames are late.", done: "Live Hindi duplex conversation on the i3.", needs: ["SV2", "~QZ3", "~PF3"], gpu: "", status: "todo" },
        { id: "SV4", title: "Coupled agent", goal: "Thinker streams into the talker live; one command starts everything; 30-minute soak.", done: "Full offline conversation recorded for the release video.", needs: ["SV3", "~PT4", "~PF4"], gpu: "", status: "todo" }
      ]
    },
    {
      code: "IN", num: "10", folder: "10-infrastructure", name: "Infrastructure",
      means: "Kaggle, the Hugging Face Hub, the laptop and this repo working as one pipeline.",
      scope: ["Repo, environments, storage layout, Vercel site", "Resumable Kaggle runner and data jobs", "Export toolchain for the laptop", "Release pipeline"],
      out: ["Paid cloud, CI runners"],
      expect: ["Kaggle sessions end after 12 h and keep 20 GB of output, so the Hub is the real disk", "Resume logic decides whether long runs survive"],
      inputs: ["Everything"],
      outputs: ["Runner, layouts, export scripts → every section"],
      cells: [
        { id: "IN1", title: "Repo, storage, runner v0", goal: "This repo and guidelines; pinned Kaggle and laptop environments; private Hub repos for shards and checkpoints; manifest schema; checkpoint-and-resume runner.", done: "Fresh clone sets up both environments; a killed run resumes.", needs: [], gpu: "", status: "doing" },
        { id: "IN2", title: "Data jobs", goal: "GPU jobs for tokenising and pseudo-labelling, CPU jobs for filters, a job ledger.", done: "Every shard traceable to source, filter version and tokenizer hash.", needs: ["IN1"], gpu: "", status: "todo" },
        { id: "IN3", title: "Export toolchain", goal: "One command exports a checkpoint to OpenVINO IR and GGUF and benchmarks it on the laptop.", done: "Export + benchmark in one command.", needs: ["IN2", "QZ2"], gpu: "", status: "todo" },
        { id: "IN4", title: "Release pipeline", goal: "Push models to Hub repos, deploy the site, rebuild from a clean clone.", done: "Clean-clone rebuild works.", needs: ["IN3", "~RL4"], gpu: "", status: "todo" }
      ]
    },
    {
      code: "MO", num: "11", folder: "11-monitoring", name: "Monitoring",
      means: "Watching training, data and the live laptop runtime so problems show up in hours, not weeks.",
      scope: ["Training metrics", "Alarms and rollback", "Listening probes", "Runtime telemetry"],
      out: ["Paid monitoring tools"],
      expect: ["Codebook collapse and fp16 overflow are the two silent killers", "Free tiers (W&B or TensorBoard on the Hub) are enough"],
      inputs: ["Runs (04, 05)", "Harness (06)", "Runtime (09)"],
      outputs: ["Dashboards and alerts → every section"],
      cells: [
        { id: "MO1", title: "Training metrics", goal: "Loss per codebook, text loss, loss per language, grad norm, fp16 loss scale and overflows, tokens/s, memory.", done: "Every run logs the same metric set.", needs: ["~IN1"], gpu: "", status: "todo" },
        { id: "MO2", title: "Alarms", goal: "Auto-stop on NaN, loss spikes and falling codebook entropy; roll back to the last good checkpoint; data-gate pass-rate dashboard.", done: "A deliberately broken run is stopped automatically.", needs: ["MO1", "~TR2"], gpu: "", status: "todo" },
        { id: "MO3", title: "Listening probes", goal: "Every N steps generate 10 fixed prompts per language; auto CER and speaker similarity; audio on the dashboard.", done: "Probe trends visible for TR3.", needs: ["MO2", "EV2"], gpu: "", status: "todo" },
        { id: "MO4", title: "Runtime telemetry", goal: "Missed frames, latency p50/p95, CPU clock and temperature, leftover echo, logged for every demo session.", done: "Telemetry attached to the release demo.", needs: ["MO3", "SV3"], gpu: "", status: "todo" }
      ]
    },
    {
      code: "RL", num: "12", folder: "12-release", name: "Release",
      means: "What goes public and on what terms: licences, consent, cards, the site, and the v0.1 release.",
      scope: ["Licence and consent ledger from day one", "Public repo and Vercel site", "Model, data and benchmark cards", "v0.1: weights, tokenizers, recipe, Indic-FDB v0, demo"],
      out: ["Paper (v0.2)"],
      expect: ["Some sources may not allow sharing derived tokens; publish scripts and manifests, not audio", "The codec's and thinker's licences decide what ships together"],
      inputs: ["Results (06)", "Bundle (07)", "Data recipe (01)"],
      outputs: ["Public releases"],
      cells: [
        { id: "RL1", title: "Licences and consent", goal: "Ledger of every dataset and model licence (codec candidates included); voice consent; PII policy; project licence.", done: "Every source tagged train-only, shareable or excluded.", needs: [], gpu: "", status: "todo" },
        { id: "RL2", title: "Public site", goal: "Public repo; site and plan on Vercel; alpha video of the cascade.", done: "Site live; plan status visible to anyone.", needs: ["IN1", "SV1", "RL1"], gpu: "", status: "todo" },
        { id: "RL3", title: "Cards", goal: "Draft model, data and Indic-FDB cards with limitations.", done: "Cards reviewed by two teammates.", needs: ["RL2", "DA2", "EV2"], gpu: "", status: "todo" },
        { id: "RL4", title: "v0.1 release", goal: "Quantised talker, tokenizers, recipe, Indic-FDB v0, technical note, demo video.", done: "v0.1 tag; a stranger can run the demo.", needs: ["RL3", "~QZ4", "~EV4", "~DA4"], gpu: "", status: "todo" }
      ]
    }
  ],
  critical: ["DA1", "TK1", "DA2", "TK2", "TR2", "TR3", "TR4", "QZ4", "RL4"],
  sota: [
    { name: "LiquidCodec", who: "Liquid AI · Nov 2026", what: "~74M causal codec, 12.5 Hz, 12 FSQ groups, 24 kHz; trained on 107 languages; reported ~13× faster encoding and ~3× faster decoding than Mimi at matching quality.", use: "TK1 candidate. If chosen, the talker can predict its groups in parallel instead of with a depth transformer. Licence must be checked in RL1." },
    { name: "Mimi", who: "Kyutai", what: "12.5 Hz, 8 RVQ codebooks; the codec behind Moshi and most open duplex models.", use: "TK1 incumbent; the safest choice if LiquidCodec's licence or Indic quality fails." },
    { name: "LFM3-Audio-2B", who: "Liquid AI · 2026", what: "2B audio model that runs on laptops and phones; 18 speech languages, none Indian; LFM Open License.", use: "Reference only: as a talker it would need ~12.5 GB/s on the i3's bus. A laptop full-duplex fine-tune of it (Alba) is useful prior art." },
    { name: "Human-1", who: "Josh Talks · 2026", what: "Hindi full-duplex model trained on real conversations; open weights.", use: "Hindi baseline in EV4." },
    { name: "PersonaPlex, NemotronLabs VoiceChat", who: "NVIDIA · 2026", what: "7B and 11B open full-duplex models with voice/role control and tool calling.", use: "Post-training and tool-protocol references for v0.2." },
    { name: "SoulX-Duplug, X2-Turn", who: "2026", what: "Plug-in streaming turn-state predictors (0.6B and 4B).", use: "Design reference for the talker's turn-state head (AR2) and turn detection in the cascade (SV1)." },
    { name: "D2, Awaken", who: "2026", what: "Recipes that turn half-duplex backbones into full-duplex while keeping their abilities.", use: "AR1 initialisation review." },
    { name: "Context Spanning, MoshiRAG", who: "2026", what: "Ways for a duplex speech model to consult an external LLM while it talks.", use: "Closest prior art to the thinker–talker link (AR3)." },
    { name: "Full-Duplex-Bench v3, M3-DuplexBench, TurnBench", who: "2026", what: "Duplex benchmarks: tool use under disfluency, multilingual multi-turn, turn-taking dynamics.", use: "Methods for Indic-FDB v0 (EV2)." },
    { name: "Indic Parler-TTS, IndicF5, Chatterbox Indic LoRAs", who: "AI4Bharat and community", what: "Open Indic TTS: 20+ languages with described voices; voice cloning in ~11 languages.", use: "Synthetic dialogues (DA2) and the cascade's voice (SV1), subject to licences." },
    { name: "Sarvam 2026 stack", who: "Sarvam AI", what: "Saaras V4 recognition (22 languages), Bulbul V4 voices, Sarvam 30B and 105B open weights.", use: "Sarvam 30B is the v0.1 thinker; Sarvam's cloud stack is the comparison target." }
  ],
  backlog: [
    "Voice set 5–10k h and duplex training in all five languages",
    "Own voice from ≥ 500 h of one consenting speaker",
    "Hidden-state coupling adapters (~100M)",
    "Preference or RL tuning for turn timing",
    "Course 120B language slice as the thinker",
    "EAGLE3-style draft head for the thinker",
    "Blind head-to-head against Sarvam with many raters",
    "Windows installer; paper"
  ],
  risks: [
    ["Data in week 2", "Ingest, tokenising and synthetic dialogues all land in one week. Start downloads in week 1; cut to Hindi + one more language if late."],
    ["GPU budget", "v0.1 needs about 270–410 T4-hours; one account gives ~240 in four weeks. Plan on two teammates' accounts."],
    ["Codec on Indian languages", "Retroflex and aspirated sounds may smear. TK1 catches it in week 1; the fix is a decoder-only fine-tune that keeps tokens valid."],
    ["Echo on laptop speakers", "Full duplex hears itself. AEC3 in SV2; headset fallback for demos."],
    ["Shared memory bus", "iGPU and CPU share 20.8 GB/s. PF4 throttles the thinker to protect the talker's frame."],
    ["Coupling quality", "Text-only coupling first; fallback is the talker as a timing controller over the cascade's TTS."],
    ["Kaggle terms", "One account per person. Several accounts held by one person risk losing all of them."]
  ]
};
