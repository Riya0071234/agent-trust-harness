# Agent trust harness

A small, reproducible harness for measuring what trust infrastructure adds when AI agents trade, against two baselines: published human behaviour, and agents without the infrastructure. It plays a one-shot investment exchange between two model-played agents, with and without signed, code-enforced commitments (Experiment 1) and signed credentials about the other party (Experiment 2).

The infrastructure is simulated: an escrow holds an Ed25519 key that stands in for the key a TEE would hold, and the signatures and checks are real. The same interface could later point at a real TEE attestation or an MPC computation.

**Status:** pilot. See `PREREG.md` for the hypotheses, sample sizes and analysis, fixed before any model was run, and `results/` for what came out.

## How it works

| File | Job |
|---|---|
| `config.yaml` | Model IDs, prices, temperature, games per cell, analysis settings |
| `prompts/` | One file per role and arm; hashed into the manifest |
| `engine.py` | Game rules, payoffs, arms, tools, the turn sequence |
| `escrow.py` | Signing and verifying commitments and credentials (Ed25519) |
| `agents.py` | Anthropic adapter with tool calls, retries and a spend cap; a scripted mock for tests |
| `run.py` | Runs the grid unattended, resumes after a crash, writes one JSONL line per game |
| `analyze.py` | The pre-registered analysis; labels every hypothesis positive, null or inconclusive |
| `audit.py` | Recomputes every metric from the raw transcripts and signatures, without importing the engine |
| `data/` | Human baseline from Johnson and Mislin (2011): 150 studies that tripled the amount sent |
| `tests/` | Payoffs, signatures, prompt-length balance, an end-to-end mock run, and checks that the audit catches tampering |

## Run it

```bash
pip install -r requirements.txt
python -m pytest -q tests                                   # no API key needed
python run.py --mock --out results/mock --games-per-cell 4  # free dry run; never report as results

export ANTHROPIC_API_KEY=...                                # real run: pin model IDs and prices in config.yaml first
python run.py --out results/pilot --games-per-cell 20
python analyze.py results/pilot
python audit.py results/pilot                               # must print AUDIT PASS before results are reported
```

If a run stops (crash or spend cap), run the same command again; finished games are skipped.

## Limits

Self-play with two models from one vendor; the principal type is assigned by prompt; the hardware is simulated; the human data are a published benchmark, not a randomised arm. `PREREG.md` lists these and what a pilot of this size can and cannot show.
