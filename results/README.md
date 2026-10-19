# Results

Raw runs sit at the top level of `results/`; everything derived from them sits under `results/analysis/`.

Each run folder holds `games.jsonl` (one game per line: every model call with its system prompt, messages and tool calls, the signed artifact, the outcome) and `manifest.json` (config, prompt hashes, code hashes, git commits, models, spend, start and finish times). Run folder names are the ones written into `PREREG.md`, so they are kept as they are.

| Folder | What it is | Games |
|---|---|---|
| `claude`, `openai` | Experiments 1-2, self-play (Claude Haiku 5.5; gpt-6-luna) | 1,440 each |
| `cross_claude_buys`, `cross_openai_buys` | Experiment 3, cross-vendor, both directions | 1,440 each |
| `stronger_claude_sonnet`, `stronger_openai_sol` | Experiment 4, stronger-model check, five arms | 90 and 200 |
| `analysis/selfplay`, `analysis/selfplay_haiku`, `analysis/selfplay_luna` | `analyze.py` output for Experiments 1-2, pooled and per model | |
| `analysis/cross` | Experiment 3, pooled over both directions | |
| `analysis/stronger_sonnet`, `analysis/stronger_sol` | Experiment 4 | |
| `analysis/figures` | `figures.py` output: every chart in the write-up and the descriptive tables | |

`bash scripts/reproduce.sh` rebuilds all of `analysis/` and prints `AUDIT PASS` for each audit. Smoke-test and mock runs are not included; they were discarded by design. The model alias was recorded but not the version string the API returned; see "Model versions" in the top-level README.
