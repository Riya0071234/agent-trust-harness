# Agent trust harness

A small, reproducible harness for measuring what trust infrastructure adds when AI agents trade, against two baselines: published human behaviour, and agents without the infrastructure. It plays a one-shot investment exchange between two model-played agents, with and without signed, code-enforced commitments (Experiment 1) and signed credentials about the other party (Experiment 2).

The infrastructure is simulated: an escrow holds an Ed25519 key that stands in for the key a TEE would hold, and the signatures and checks are real. The same interface could later point at a real TEE attestation or an MPC computation.

`PREREG.md` holds the hypotheses, sample-size rule and analysis, committed before any model was run (Experiments 1 and 2; Experiments 3 and 4 were registered later, after the first results, and say so). The commit times are from local git history and were first published on 2026-10-19, after the data; they cannot be checked independently of the author. `results/` holds what came out.

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
| `figures.py` | Rebuilds every chart and descriptive table in the write-up from the raw games |
| `audit.py` | Recomputes every metric from the raw transcripts and signatures, without importing the engine |
| `data/` | Where the human baseline goes; see `data/README.md` |
| `scripts/` | `reproduce.sh` (rebuild everything, no key), `probe_sol.py` (API probe), `windows/` (double-click run scripts) |
| `tests/` | Payoffs, signatures, prompt-length balance, adapters against fake clients, an end-to-end mock run, and checks that the audit catches tampering |

## Reproduce the results (no API key)

```bash
pip install -r requirements.txt        # pinned versions used for the reported runs
python -m pytest -q tests              # 58 tests
bash scripts/reproduce.sh              # every analysis, audit (must print AUDIT PASS) and figure
```

`analyze.py` also needs the human-baseline table, which is not redistributed (see `data/README.md`); without it the script keeps the committed analyses and still runs every audit and figure. GitHub Actions runs the tests and `reproduce.sh` on every push.

## Run new games (needs API keys)

```bash
export ANTHROPIC_API_KEY=...   OPENAI_API_KEY=...
python run.py --smoke --models claude --out results/smoke_claude                          # 2 games per arm, prints cost per game
python run.py --models claude --out results/claude --games-per-cell 160                   # Experiments 1-2, self-play
python run.py --models openai --out results/openai --games-per-cell 160
python run.py --pair "claude>openai" --out results/cross_claude_buys --games-per-cell 160 --max-spend 0.9   # Experiment 3
python run.py --pair "openai>claude" --out results/cross_openai_buys --games-per-cell 160 --max-spend 0.9
python run.py --models claude_sonnet --arms A0,C1,C3,D1,D3 --out results/stronger_claude_sonnet --games-per-cell 18   # Experiment 4
python run.py --models openai_sol --arms A0,C1,C3,D1,D3 --out results/stronger_openai_sol --games-per-cell 40
```

Quote the pair: in Windows `cmd` a bare `>` redirects output. On Windows, run `scripts\windows\setup_windows.bat` once (Python 3.12), then the matching `run_*.bat`. If a run stops (crash or spend cap), run the same command again; finished games are skipped, and a resume refuses to mix games played under different prompts, code or settings. `--mock` plays a scripted stand-in for free; never report its numbers. The stronger models never run unless named.

## Results at a glance

All numbers are recomputed from the raw transcripts by `audit.py` (AUDIT PASS on every run below, 0 mismatches). Efficiency is in points out of 100 and depends only on how much the buyer sends; 95% bootstrap intervals; H1 is C3 minus C1 (verified commitment against free-text promise) and G1 is D3 minus D1 (verified credential against free-text message). Full tables are in `results/analysis/*/results.md`; charts and descriptive tables in `results/analysis/figures/`.

| Run (folder) | Games | H1 | G1 |
|---|---|---|---|
| Self-play, cheap models, pooled (`results/analysis/selfplay`) | 2,880 | +31.0 [27.4, 34.7] | +15.9 [12.0, 19.8] |
| Cross-vendor, both directions, pooled (`results/analysis/cross`) | 2,880 | +40.6 [37.1, 43.9] | +24.2 [20.1, 28.3] |
| Stronger model, Claude Sonnet 5.5 (`results/analysis/stronger_sonnet`) | 90 | +62.2 [57.0, 66.7] | +27.4 [11.1, 43.3] |
| Stronger model, gpt-6.1-sol (`results/analysis/stronger_sol`) | 200 | +65.2 [62.2, 66.7] | +32.5 [21.7, 43.3] |

What held: verifiable infrastructure raises cooperation in every model, vendor pairing and tier; both stronger models land exactly on the game-theory prediction in C3 (100) and D3 (66.7) (`theory.py`). What did not hold, and is reported as such: a corrupted signature is not treated like no signature (the pre-registered H3b and G3b predictions failed: it is read as a warning); an unsigned credential has no effect (G2 null); the agents-versus-humans comparison depends on the model (without infrastructure the cheap models and gpt-6.1-sol send nothing, Sonnet matches the human mean, and with a verified commitment the advantage over humans ranges from about +1 to +32 points by model and pairing).

## What the descriptive checks show

`figures.py` writes these to `results/analysis/figures/`:

- **Manipulation check (`manipulation_check.csv`, `fig4`).** Suppliers told to act for a self-interested owner returned almost as much as fair ones when they chose the return: 44% versus 51% of the tripled amount for Haiku suppliers in self-play, 77% versus 80% for Luna suppliers in cross-vendor play, and every unsigned commitment that was followed by a prepayment (227 games) was kept. All of these are above the one-third a buyer needs to break even. The theory benchmark assumes self-interested suppliers return nothing, so buyers who sent nothing acted on the stated risk, not on how these suppliers behaved.
- **Measured spread (`measured_sd.csv`).** Games are close to all-or-nothing, so the standard deviation of efficiency within an arm ranges from 0 to about 33 points (pooled within-arm SD 12 to 22 by setting), against the 20 assumed in the power note. Cells where every game ended the same way have zero-width intervals; read those as "no variation observed", not as precision.
- **Comprehension (`comprehension.csv`).** Both roles passed the payoff check in 79% of gpt-6-luna self-play games and 88% to 100% elsewhere. Restricting to games where both passed leaves every hypothesis label unchanged (`label_comprehension_only` in `hypotheses.csv`).
- **Verification (`verification.csv`).** Every buyer called the verify tool in C3 and C4. In D3, buyers that did not verify always sent nothing.

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
- The self-interested instruction barely lowered what suppliers returned (see the manipulation check above), so the risk the buyers reacted to was mostly stated, not realised.
- A0 has no principal type, so its buyer is not told that half of suppliers are self-interested; A0 against C1 changes more than the message.
- Each game is one offer, one decision and one return: no negotiation or repeated rounds. Agents were never asked for a stated probability, and are not told where they run.
- The pre-registration's commit times come from local git and were first published after the data.

`PREREG.md` lists these and what the study can and cannot show.

## What to build next

1. Replace the simulated hardware with a real attested enclave or a zero-knowledge or multi-party proof for the verification step, behind the same `verify_commitment` and `verify_credential` tools, so that arms stay comparable. This needs access to CCTI-style infrastructure.
2. The information-exchange variant: one agent holds private information, a code-based check settles whether a claim about it is true or false without revealing it, and payment is in tokens or access rather than points.
3. Repeated play and reputation (Berg et al.): how much agents know about each other and about past transactions, and whether scarcity or risk framing changes who breaks trust, as in Akerlof's market for lemons.
4. A matched Sonnet-versus-gpt-6.1-sol cross-vendor grid at equal reasoning settings, pinned snapshots, and more model families and sizes, so that vendor and capability effects can be separated.
5. A leakage and security measurement: does the agent reveal private data to its counterpart, and can an adversarial supplier forge or replay a signature?
6. Prompt-wording sensitivity and a matched human arm or published human data for the same framing.
7. A standing, versioned results register in which null results and failed predictions are kept as visible as positive ones.
8. Multi-turn negotiation with offers and counter-offers, combined with repeated play.
9. Elicit each agent's stated probability that its counterpart is fair, to check calibration, and tell some agents that they and their counterpart run inside attested hardware.
10. Register the next study on OSF before collecting data, so its timestamps are independent of the author.

## Licence

MIT, see `LICENSE`.
