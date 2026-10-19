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

## Results at a glance

All numbers are recomputed from the raw transcripts by `audit.py` (AUDIT PASS on every run below, 0 mismatches). Efficiency is in points out of 100 and depends only on how much the buyer sends; 95% bootstrap intervals; H1 is C3 minus C1 (verified commitment against free-text promise) and G1 is D3 minus D1 (verified credential against free-text message). Full tables are in `results/*/results.md` and `hypotheses.csv`.

| Run (folder) | Games | H1 | G1 |
|---|---|---|---|
| Self-play, cheap models, pooled (`results/combined`) | 2,880 | +31.0 [27.4, 34.7] | +15.9 [12.0, 19.8] |
| Cross-vendor, both directions, pooled (`results/cross_combined`) | 2,880 | +40.6 [37.1, 43.9] | +24.2 [20.1, 28.3] |
| Stronger model, Claude Sonnet 5.5 (`results/stronger_claude_sonnet`) | 90 | +62.2 [57.0, 66.7] | +27.4 [11.1, 43.3] |
| Stronger model, gpt-6.1-sol (`results/stronger_openai_sol`) | 200 | +65.2 [62.2, 66.7] | +32.5 [21.7, 43.3] |

What held: verifiable infrastructure raises cooperation in every model, vendor pairing and tier; both stronger models land exactly on the game-theory prediction in C3 (100) and D3 (66.7) (`theory.py`). What did not hold, and is reported as such: a corrupted signature is not treated like no signature (the pre-registered H3b and G3b predictions failed: it is read as a warning); an unsigned credential has no effect (G2 null); the agents-versus-humans comparison depends on the model (without infrastructure the cheap models and gpt-6.1-sol send nothing, Sonnet matches the human mean, and with a verified commitment the advantage over humans ranges from about +1 to +32 points by model and pairing).

## Model versions

Requests name an alias, not a dated snapshot: `claude-haiku-5-5`, `claude-sonnet-5-5`, `gpt-6-luna`, `gpt-6.1-sol`. The 6,050 games reported above were all played on 2026-10-19, and the code at that time stored only the alias that was requested, not the exact version string the vendor's API reports back. That is a limitation of the existing data: a rerun later may reach a different snapshot. From commit "Record the model version each API returns" onward, every call stores `model_returned` in its transcript and the run manifest lists `model_versions_returned` per model. Use that field, and pass a dated snapshot ID in `config.yaml` where the vendor offers one, for any new run.

## Limits

- The trusted hardware is simulated. Ed25519 signatures are real, but the signer (escrow or issuer) stands in for an attested enclave or a multi-party computation; nothing here tests CCTI's actual infrastructure.
- Two vendors, one model per vendor and tier, one prompt wording, one run date. The principal type (fair or self-interested) is assigned by prompt.
- The models ran with different reasoning settings, which the study did not hold fixed: `gpt-6-luna` with reasoning off (Chat Completions), the Claude models with their default (no extended thinking), and `gpt-6.1-sol` with reasoning `low` through the Responses API (it always reasons and rejects `none`). Sonnet rejects forced tool use, so it ran with `auto` tool choice; sol is sent no temperature. Differences between vendors in the stronger-model check cannot be attributed to the vendor alone. `PREREG.md` logs each change.
- The stronger-model check is small (18 games per arm for Sonnet, 40 for gpt-6.1-sol).
- The human benchmark is the published trust-game meta-analysis (Johnson and Mislin 2011), not a matched human arm, and in a different framing. The study-level file is not redistributed (see `data/README.md`).
- Secondary hypotheses are not adjusted for multiple comparisons; H1 and G1 are the primary tests.
- Model aliases are not pinned snapshots, and the returned version was not recorded for the existing games (see Model versions).

`PREREG.md` lists these and what the study can and cannot show.

## What to build next

1. Replace the simulated hardware with a real attested enclave or a zero-knowledge or multi-party proof for the verification step, behind the same `verify_commitment` and `verify_credential` tools, so that arms stay comparable. This needs access to CCTI-style infrastructure.
2. The information-exchange variant: one agent holds private information, a code-based check settles whether a claim about it is true or false without revealing it, and payment is in tokens or access rather than points.
3. Repeated play and reputation (Berg et al.): how much agents know about each other and about past transactions, and whether scarcity or risk framing changes who breaks trust, as in Akerlof's market for lemons.
4. A matched Sonnet-versus-gpt-6.1-sol cross-vendor grid at equal reasoning settings, pinned snapshots, and more model families and sizes, so that vendor and capability effects can be separated.
5. A leakage and security measurement: does the agent reveal private data to its counterpart, and can an adversarial supplier forge or replay a signature?
6. Prompt-wording sensitivity and a matched human arm or published human data for the same framing.
7. A standing, versioned results register in which null results and failed predictions are kept as visible as positive ones.

## Licence

MIT, see `LICENSE`.

Stronger-model check (Experiment 4): `python run.py --models claude_sonnet --arms A0,C1,C3,D1,D3 --out results/stronger_claude_sonnet --games-per-cell 18` and `python run.py --models openai_sol --arms A0,C1,C3,D1,D3 --out results/stronger_openai_sol --games-per-cell 40` (on Windows, `run_stronger_openai.bat` runs the second). These models never run unless named. Theory benchmark next to the observed means: `python theory.py --cells results/combined/cells.csv`.
