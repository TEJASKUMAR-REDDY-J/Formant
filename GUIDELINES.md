# Guidelines

How we work on Formant. Short on purpose; if a rule gets in the way, change it here.

## 1. Where the work lives

- All work happens in `F:\formant` (or your own clone on your F drive). Nothing on C or D: no data, no checkpoints, no virtual environments.
- Large files live on the Hugging Face Hub, never in git: audio, codec tokens, checkpoints, GGUF and OpenVINO exports, notebook outputs.
- Secrets (Hub and Kaggle tokens) go in environment variables or Kaggle secrets. Never in a file in this repo.

## 2. The plan is the contract

- `site/plan-data.js` is the single source of truth for scope, phases, dependencies and status. The board (`site/plan.html`) and every folder README come from it.
- After editing it, regenerate your own folder's README: `node 10-infrastructure/scripts/gen-readmes.js`, then commit only `<NN-section>/README.md`.
- The section pages under `site/sections/` are not in git. Vercel builds them on every deploy; to see them locally run `node 10-infrastructure/scripts/gen-sections.js`.
- Every piece of work belongs to a phase ID such as `DA2` or `TR3`. If it has no ID, it is not in v0.1; add it to the backlog instead.
- Status values: `todo`, `doing`, `done`, `cut`. A phase is `done` only when its "Done when" line is true and its report exists.

## 3. Weekly rhythm

Each phase is one week, and all twelve sections work on the same phase number at the same time.

- **Monday:** start phase *n*. Each owner checks that everything listed under "Needs" from phase *n−1* is done. If something is missing, say so on day one.
- **Wednesday:** handoff check for same-week needs (shown as `~XX1`). The upstream owner shares early output: a sample shard, a draft spec, a first number.
- **Friday:** demo. Each owner shows their phase against its "Done when" line, sets the status in `plan-data.js`, writes `reports/<ID>.md`, and opens the `sec/<folder>` → `main` PR. After the merges, every section branch syncs from `main`.

## 4. Folders and ownership

- One owner per folder. The owner reviews every change in it.
- A folder talks to others only through what its README lists under "Takes in" and "Hands over": paths on the Hub, file formats, spec documents. Changing a handover means telling the folders that consume it.
- Code shared by two or more folders lives in `src/formant/`, with its tests in `tests/` (`python -m pytest`). `formant` is a namespace package: no `__init__.py`, so sections can add modules without touching the same file.
- Subfolders inside a section: `configs/`, `scripts/`, `notebooks/`, `plans/`, `reports/`. Create them only when needed.
- Each phase gets `plans/<ID>.md` before it starts (what, how, SOTA picks, efficiency, day-by-day) and `reports/<ID>.md` when it ends.

## 5. Git: one branch per section

```
feature branch ──PR──▶ sec/<folder> ──PR at phase end──▶ main ──sync──▶ every sec/* branch
da2-voice-set          sec/01-data                       (Vercel deploys main)
```

**Branches**

- `main` is what is released and what Vercel serves. It only changes through a section PR (below). Nobody pushes to it directly.
- Each section has one long-lived branch named after its folder:

  `sec/01-data`, `sec/02-tokenizer`, `sec/03-architecture`, `sec/04-training`, `sec/05-post-training`, `sec/06-evaluation`, `sec/07-quantization`, `sec/08-performance`, `sec/09-serving`, `sec/10-infrastructure`, `sec/11-monitoring`, `sec/12-release`.
- Every change starts on a short-lived feature branch cut from its section branch and named `<phase-id>-<slug>`, for example `da2-voice-set` or `tr1-smoke`.

**Pull requests**

1. **Feature → section.**
   - Open a PR from the feature branch into `sec/<folder>`; the section owner reviews it.
   - Squash-merge it, then delete the feature branch.
   - Small PRs; one phase can take several.
2. **Section → main.**
   - When the section's phase is done (its "Done when" line is true and `reports/<ID>.md` exists, normally at the Friday demo), open one PR from `sec/<folder>` into `main`, titled `<ID> → main`.
   - Merge it with a merge commit, so each phase stays visible in `main`'s history.
3. **Sync.**
   - After anything lands on `main`, every section branch merges `main` back in (`git merge origin/main`) and pushes.
   - No PR is needed, because only reviewed work comes from `main`.
   - Resolve conflicts on the section branch, never on `main`.

**Shared files**

| File or folder | Changed through |
|---|---|
| Anything inside `<NN-section>/` | That section's branch |
| `site/`, `GUIDELINES.md`, `README.md`, `.github/`, `10-infrastructure/scripts/` | `sec/10-infrastructure` |
| `site/plan-data.js` | Any section, but only its own cells and scope; statuses change at the Friday demo |
| `src/formant/` (shared code) | The section that needs it first; later changes through `sec/10-infrastructure` |

After editing `site/plan-data.js`, regenerate and commit your own folder's README in the same PR (section 2). Section pages are built by Vercel and never committed: when every section committed the same generated index, every pair of section PRs conflicted.

**Writing**

- **PR description:** the phase ID, what changed, how it was checked, and whether "Done when" is now true. The template in `.github/pull_request_template.md` asks for exactly this.
- **Commit messages:** short and imperative, for example `Add SNR gate to data filters`.
- **Notebooks:** clear outputs before committing.
- **Optional protection:** turn on branch protection for `main` and `sec/*` in the GitHub settings: require a PR, no force-pushes.

## 6. Data rules

- Every shard has a manifest row with: `id, source, licence, lang, speaker_id, split, duration_s, snr_db, lid_score, cer_agree, tokenizer, filter_version`.
- A source without a licence tag in the RL1 ledger is not used.
- Test speakers (from EV1) never appear in training data. The data pipeline checks this, not people.
- Personal information is masked before anything is stored.
- Synthetic data is labelled as synthetic in its manifest.

## 7. Training and other runs

- Every run has a config file in git, a seed, a data manifest version, a tokenizer hash and the commit it ran from.
- Run names: `<phase-id>-<yyyymmdd>-<slug>`, for example `tr2-20261201-pretrain`.
- Checkpoint to the Hub every 30–45 minutes; Kaggle sessions end after 12 hours.
- Train in fp16 on T4s (no bf16) and log the loss scale.
- Every run logs the standard metric set from `11-monitoring`.

## 8. Compute

- One Kaggle account per person. Never several accounts held by one person: it breaks Kaggle's terms and risks losing all of them.
- Record T4-hours used in the phase report.
- Ask in the team channel before starting any job over 20 T4-hours.

## 9. Results

- Numbers come from the `06-evaluation` harness, not from ad hoc scripts.
- Always label a number as a **target** or a **result**.
- Each phase report (`reports/<ID>.md`) has four parts: what was done, how it was checked, the result, what changes next.

## 10. Release and licences

- Nothing becomes public without a licence tag in the RL1 ledger.
- No voice is cloned or fine-tuned without a clear licence or written consent.
- Releases include model cards with limitations, and data cards for every dataset used.

## 11. Website

- Vercel serves `site/` from `main` (set by `vercel.json` at the repo root): no build step, clean URLs on. Branches get preview links.
- Update `plan-data.js` statuses on Friday so the public board stays current.

## 12. Writing

- Plain words, numbers with units, and no claims without a source or a measurement.
