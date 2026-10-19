# Results

Raw transcripts and analysis for every run reported in the top-level README. Each run folder holds `games.jsonl` (one game per line: every model call with its system prompt, messages and tool calls, the signed artifact, the outcome) and `manifest.json` (config, prompt hashes, code hashes, git commit, models, spend, start and finish times). Analysis folders hold `cells.csv`, `hypotheses.csv` and `results.md`.

| Folder | What it is | Games |
|---|---|---|
| `claude`, `openai` | Experiments 1-2, self-play, one model per folder (Haiku 5.5; gpt-6-luna) | 1,440 each |
| `combined`, `by_model` | Analysis of the two self-play runs, pooled and per model | |
| `cross_claude_buys`, `cross_openai_buys` | Experiment 3, cross-vendor, both directions | 1,440 each |
| `cross_combined` | Analysis of Experiment 3, pooled | |
| `stronger_claude_sonnet`, `stronger_openai_sol` | Experiment 4, stronger-model check, five arms | 90 and 200 |
| `stronger_*_analysis` | Analysis of Experiment 4 | |

Check any run yourself: `python audit.py results/cross_claude_buys results/cross_openai_buys --cells results/cross_combined` recomputes every number from the raw transcripts and checks each arm's invariants (it prints `AUDIT PASS` or lists the mismatches).

Smoke-test and mock runs are not included; they were discarded by design. The model alias was recorded but not the version string the API returned; see "Model versions" in the top-level README.
