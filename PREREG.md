# Pre-registration: verifiable commitments and credentials in an agent trust game (pilot)

**Author:** Riya Pal. **Drafted with:** Claude. **Status:** frozen by the git commit that contains this file; that commit's timestamp must precede every `games.jsonl` it governs. Anything changed afterwards goes in the deviations log at the bottom, with the reason.

## Question

When AI agents trade, how much of any gain from "trust infrastructure" is due to the infrastructure, and how much is simply what agents do differently from humans? This follows the two baselines in the CCTI definition of AI advantage: (a) a human-only baseline, and (b) agents operating without the infrastructure.

## Design

One-shot, anonymous investment exchange, framed as a buyer prepaying an unfamiliar supplier. The words "trust game" never appear in a prompt.

- The **sender** (buyer) holds 10 points and prepays a whole number 0 to 10. The trustee receives 3 points per point prepaid.
- The **trustee** (supplier) returns 0 up to everything received. Sender payoff = 10 - sent + returned. Trustee payoff = 3 x sent - returned. Joint payoff = 10 + 2 x sent, so **efficiency = (10 + 2 x sent) / 30** depends only on how much is sent.
- In every arm except A0 the trustee represents a principal that is either *fair* (wants an outcome good for both sides) or *self_interested* (wants the most points). Types alternate by game index, so every cell is exactly 50/50. The sender is told the 50/50 split but not which type it faces.
- Each role is played by a model in **self-play**: one model plays both sides of a game.
- Before play, each role answers two payoff questions in a separate call (the comprehension check).

### Experiment 1: verifiable commitments

| Arm | Trustee's pre-play move | What enforces the return |
|---|---|---|
| A0 | none; no principal type | nothing |
| C1 | one free-text message, unsigned | nothing |
| C2 | states a return percentage labelled "committed", unsigned | nothing |
| C3 | commits to a return percentage; the escrow signs it; the sender can call `verify_commitment` | the game pays the committed share itself |
| C4 | as C3, but the signature fails verification | nothing; the trustee chooses the return |

### Experiment 2: verifiable credentials

| Arm | Trustee's pre-play move | Sender's check |
|---|---|---|
| D1 | one free-text message, unsigned | none |
| D2 | presents a credential naming its principal's type (or none), unsigned | none |
| D3 | presents a credential (or none); an issuer signs it only if it matches the true type; a mismatching claim gets an invalid signature | `verify_credential` |
| D4 | as D3, but every signature fails verification | `verify_credential` |

Returns in Experiment 2 are always voluntary. A self-interested trustee that claims to be "fair" in D3 is caught by the signature check; in D2 it is not.

The escrow and issuer are an Ed25519 key per game. The signatures and verification are real cryptography; the trusted hardware is simulated. Same-length neutral paragraphs are used in A0, C1, C2, D1 and D2 so that prompt length does not differ from the infrastructure arms (checked by `tests/test_engine.py`).

## Models and runs

Two Claude models from different size tiers, pinned to dated model IDs in `config.yaml` in a commit made before the first real run. There is no OpenAI or other-vendor arm in this pilot. Temperature 1.0; the API offers no seed, so exact replication of model output is not possible and the transcripts are the record. The run date, SDK version, prompt hashes and git commit go into `manifest.json`.

A **smoke test** of at most one game per arm per model checks parsing and token use. Its data are discarded. Prompts may be corrected in response to malformed outputs only, and each such change is logged below.

**Pilot size:** 20 games per cell, 9 arms x 2 models = 360 games. **Full study (not yet run):** 160 per cell, with this analysis code frozen.

**Spend cap:** a hard cap in code. If it is reached, unfinished games are discarded and the run can resume; the cap and total spend are in the manifest.

## Measures

Efficiency (primary), send share, mutually beneficial agreement (sent > 0 and returned >= sent), return share, exploitation (sent > 0 and returned < sent), verification (whether the sender called the verify tool), comprehension (both roles answered both questions correctly), stated-versus-actual return (C2, C3, C4).

## Hypotheses

The smallest effect of interest is **10 points of efficiency**. Effects are differences in mean efficiency, averaged over models with equal weight.

Experiment 1
- **H1 (primary):** efficiency is higher in C3 than in C1.
- **H2:** C2 minus C1, either direction.
- **H3a:** C3 higher than C4. **H3b:** C4 is not different from C1 (null predicted).
- **H4:** A0 compared with humans, two-sided, no direction predicted.
- **H4b:** C3 higher than humans (the human-baseline sense of AI advantage).
- **H5 (descriptive):** how often senders verify in C3 and C4, and efficiency for verifiers versus non-verifiers. This comparison is observational.

Experiment 2
- **G1 (primary):** D3 higher than D1. **G2:** D2 minus D1, either direction.
- **G3a:** D3 higher than D4. **G3b:** D4 is not different from D1 (null predicted).
- **G4 (descriptive):** points sent to fair versus self-interested trustees in each arm, and verification rates in D3 and D4.

**Human baseline.** From Johnson and Mislin's (2011) meta-analysis data: the 150 studies in which the amount sent was tripled. Study-level mean send share converts to efficiency as (1 + 2p) / 3. It is a published benchmark, not a randomised arm; the studies used real money, other populations and other framings, and shares are compared, not points.

## Analysis

`analyze.py`, run unchanged on every dataset.

1. Per-model, per-arm resampling bootstrap, 5,000 resamples, seed 7. The pooled effect is the mean over models of the per-model difference. Human comparisons resample studies as well as games.
2. Each hypothesis reports the effect, a 95% percentile interval, and TOST p-values against +/-10 points.
3. **Labels:** *positive* if the interval excludes zero in the predicted direction (either direction when none is predicted); otherwise *null* if the interval lies inside +/-10 points; otherwise *inconclusive*. A separate "supported" column says whether the pre-registered prediction held; for H3b and G3b that means the label is *null*. One table lists every hypothesis, whatever its label.
4. **Secondary:** the same table on games where both roles passed the comprehension check.
5. **Failures:** a call that produces more than two malformed outputs (no tool call, or invalid values) aborts its game. Aborted games are excluded from effects and counted per cell. No other game is excluded.
6. **Audit:** results are reported only if `audit.py` passes, i.e. every metric recomputes from the raw transcripts and signatures.

## What the pilot can and cannot show

If the standard deviation of efficiency is about 20 points (a send-share SD of 0.30), each arm pools to about 40 games, which detects differences of roughly 12 points at 80% power. Showing equivalence within +/-10 points needs about 50 games per arm at 80% power; 40 is close but short, so most *null* labels in the pilot will come out *inconclusive* unless the observed spread is smaller than assumed. The pilot therefore shows whether the pipeline works and which way the effects point. It supports no claim of equivalence, and the labels it produces are exploratory. The 160-per-cell study is the confirmatory one.

(Correction to the design document: it states that 15 points corresponds to d = 0.5 and that equivalence needs about 155 games per cell. With an efficiency SD of 20 points, d = 0.5 is 10 points, which needs about 64 games per cell, and equivalence within +/-10 needs about 50. The 160 per cell planned for the full study is kept as it also supports narrower margins and per-model estimates.)

## Known limitations

- Self-play only; the same model sees both roles' rules. Cross-model pairs are a later experiment.
- The trustee's principal type is assigned by prompt, not a real hidden preference.
- Comprehension checks test the payoff rules, not whether an agent understands enforcement. Verification behaviour is recorded separately.
- The infrastructure is simulated (Ed25519 signatures, no TEE or MPC). The interface is intended to point at real attestation later.
- Two models from one vendor, one prompt wording, one run date. Prompt sensitivity is not tested here.
- Models may recall trust-game results from training; the neutral framing reduces but does not remove this.

## Deviations log

(empty)
