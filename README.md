# Agent trust harness

A small, reproducible harness for measuring what trust infrastructure adds when AI agents trade, against two baselines: published human behaviour, and agents without the infrastructure. It plays a one-shot investment exchange between two model-played agents, with and without signed, code-enforced commitments (Experiment 1) and signed credentials about the other party (Experiment 2).

The infrastructure is simulated: an escrow holds an Ed25519 key that stands in for the key a TEE would hold, and the signatures and checks are real. The same interface could later point at a real TEE attestation or an MPC computation.

`PREREG.md` holds the hypotheses, sample-size rule and analysis, committed before any model was run. `results/` holds what came out.

## How it works

| File | Job |
|---|---|
| `config.yaml` | Models (one per vendor), prices, spend caps, temperature, analysis settings |
| `prompts/` | One file per role and arm; hashed into the manifest |
| `engine.py` | Game rules, payoffs, arms, tools, the turn sequence |
| `escrow.py` | Signing and verifying commitments and credentials (Ed25519) |
| `agents.py` | Anthropic and OpenAI adapters sharing one tool loop, with retries and a per-model spend cap; a scripted mock for tests |
| `run.py` | Runs the grid unattended, resumes after a crash, writes one JSONL line per game, has a smoke test |
| `analyze.py` | The pre-registered analysis; labels every hypothesis positive, null or inconclusive |
| `audit.py` | Recomputes every metric from the raw transcripts and signatures, without importing the engine |
| `data/` | Where the human baseline goes; see `data/README.md` |
| `tests/` | Payoffs, signatures, prompt-length balance, adapters against fake clients, an end-to-end mock run, and checks that the audit catches tampering |

## Run it

```bash
pip install -r requirements.txt
python -m pytest -q tests                      # no API key needed

# 1. smoke test: 2 games per arm, prints cost per game and the size to run
export ANTHROPIC_API_KEY=...                   # or OPENAI_API_KEY=... for the openai model
python run.py --smoke --models claude --out results/smoke_claude

# 2. the run, at the size the smoke test recommends (the smaller of the two models' sizes)
python run.py --models claude --out results/claude --games-per-cell 160
python run.py --models openai --out results/openai --games-per-cell 160

# 3. analysis and audit over both runs
python analyze.py results/claude results/openai --out results/combined
python audit.py results/claude results/openai --cells results/combined     # must print AUDIT PASS
```

On Windows, double-click `setup_windows.bat` once (it needs Python 3.12), then `run_openai.bat`, which asks for the key and runs the OpenAI arm.

Cross-vendor pairs (one model buys, the other supplies; needs both keys): `python run.py --pair "claude>openai" --out results/cross_claude_buys --games-per-cell 160 --max-spend 0.9`, then the same with `"openai>claude"` into `results/cross_openai_buys`. Quote the pair: in Windows `cmd` a bare `>` redirects output. On Windows, `run_cross.bat` does both. Analyse with `python analyze.py results/cross_claude_buys results/cross_openai_buys --out results/cross_combined`.

If a run stops (crash or spend cap), run the same command again; finished games are skipped. `--mock` runs a scripted stand-in for free; never report its numbers.

## Limits

Self-play with two models; the principal type is assigned by prompt; the hardware is simulated; the human data are a published benchmark, not a randomised arm. `PREREG.md` lists these and what the study can and cannot show.

Stronger-model check (Experiment 4): `python run.py --models claude_sonnet --arms A0,C1,C3,D1,D3 --out results/stronger_claude_sonnet --games-per-cell 18` and `python run.py --models openai_sol --arms A0,C1,C3,D1,D3 --out results/stronger_openai_sol --games-per-cell 40` (on Windows, `run_stronger_openai.bat` runs the second). These models never run unless named. Theory benchmark next to the observed means: `python theory.py --cells results/combined/cells.csv`.
