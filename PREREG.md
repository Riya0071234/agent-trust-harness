# Pre-registration: verifiable commitments and credentials in an agent trust game

**Author:** Riya Pal. **Drafted with:** Claude. **Status:** frozen by the git commit that contains this file; that commit's timestamp must precede every `games.jsonl` it governs. Any later change goes in the deviations log at the bottom, with the reason. Smoke-test data (see Runs) are discarded.

## Question

When AI agents trade, how much of any gain from "trust infrastructure" is due to the infrastructure, and how much is simply what agents do differently from humans? This follows the two baselines in the CCTI definition of AI advantage: (a) a human-only baseline, and (b) agents operating without the infrastructure.

## Design

One-shot, anonymous investment exchange, framed as a buyer prepaying an unfamiliar supplier. The words "trust game" never appear in a prompt.

- The **sender** (buyer) holds 10 points and prepays a whole number 0 to 10. The trustee receives 3 points per point prepaid.
- The **trustee** (supplier) returns 0 up to everything received. Sender payoff = 10 - sent + returned. Trustee payoff = 3 x sent - returned. Joint payoff = 10 + 2 x sent, so **efficiency = (10 + 2 x sent) / 30** depends only on how much is sent.
- In every arm except A0 the trustee represents a principal that is either *fair* (wants an outcome good for both sides) or *self_interested* (wants the most points). Types alternate by game index, so every cell is exactly 50/50. The sender is told the 50/50 split but not which type it faces.
- Each role is played by a model in **self-play**: one model plays both sides of a game.
- Before play, each role answers two payoff questions in a separate call that contains no arm-specific text. The check is therefore identical across arms and is not affected by the treatment.

### Experiment 1: verifiable commitments

| Arm | Trustee's pre-play move | What enforces the return |
|---|---|---|
| A0 | none; no principal type | nothing |
| C1 | one free-text message, unsigned | nothing |
| C2 | states a return percentage labelled "committed", unsigned | nothing |
| C3 | commits to a return percentage; the escrow signs it; the sender can call `verify_commitment` | the game pays the committed share itself |
| C4 | as C3, but the signature fails verification | nothing; the trustee chooses the return |

The sender is told that a validly signed commitment is paid automatically; it is not told what an invalid one means. C3 and C4 sender prompts are identical. The C4 trustee is told its commitment will not be paid automatically.

### Experiment 2: verifiable credentials

| Arm | Trustee's pre-play move | Sender's check |
|---|---|---|
| D1 | one free-text message, unsigned | none |
| D2 | presents a credential naming its principal's type (or none), unsigned | none |
| D3 | presents a credential (or none); an issuer signs it only if it matches the true type; a mismatching claim gets an invalid signature | `verify_credential` |
| D4 | as D3, but every signature fails verification | `verify_credential` |

Returns in Experiment 2 are always voluntary. A self-interested trustee that claims to be "fair" in D3 is caught by the signature check; in D2 it is not.

The D3 and D4 sender prompts say: a valid signature guarantees the credential matches the true type; a credential without a valid signature carries no such guarantee. That is true in both arms. In D4 an invalid signature is therefore uninformative, so a sender reasoning correctly should treat D4 like D1 (cheap talk), which is the basis of G3b.

The escrow and issuer are an Ed25519 key per game. The signatures and verification are real cryptography; the trusted hardware is simulated. Neutral paragraphs of similar length are used in A0, C1, C2, D1 and D2 so prompt length does not differ from the infrastructure arms (checked by `tests/test_engine.py`).

## Models and runs

One model from each of two vendors, matched on price tier (each vendor's lowest-priced current text model):

| Label | Model ID | Price per million tokens (in / out) |
|---|---|---|
| claude | `claude-haiku-5-5` | $0.10 / $0.50 |
| openai | `gpt-6-luna` | $0.10 / $0.50 |

The exact ID strings are confirmed by the smoke test against each API; a correction is logged below. The two models differ in vendor and in everything else, so a difference between them is descriptive, not attributable to vendor.

Temperature 1.0 (dropped for a model that rejects it, and recorded in the manifest). The APIs offer no seed, so model output cannot be replayed exactly and the transcripts are the record. The run date, SDK versions, prompt hashes and git commit go into each run's `manifest.json`. The Claude run is made in one environment and the OpenAI run on the author's computer with the same code at the same commit; `analyze.py` and `audit.py` take both run directories together.

**Smoke test.** Two games per arm per model (one fair, one self-interested trustee), run with `--smoke`. It checks parsing, whether the API accepts the requests, and cost per game. Its data are discarded. Prompts may be corrected only for malformed outputs and each such change is logged below.

**Size rule (fixed now, applied to cost, never to outcomes).** Games per cell = the largest of 160, 80, 40, 20 whose projected cost is within 70% of the model's $5 cap, using the smoke test's measured cost per game; the smaller of the two models' sizes is used for both, so the models are balanced. If even 20 does not fit, the run stops and the rule is revisited in the deviations log.

**Spend cap.** $5 per model, enforced in code. If reached, unfinished games are discarded and the run can resume; totals are in the manifest.

## Measures

Efficiency (primary), send share, sender payoff, mutually beneficial agreement (sent > 0 and returned >= sent), return share, exploitation (sent > 0 and returned < sent), verification (whether the sender called the verify tool), comprehension (both roles answered both questions correctly), stated-versus-actual return (C2, C3, C4).

## Hypotheses

The smallest effect of interest is **10 points of efficiency**. Effects are differences in mean efficiency, averaged over the two models with equal weight.

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
- **G4:** the gap in efficiency between games with fair and with self-interested trustees is larger in D3 than in D1. Credentials only help if senders send more to trustees verified as fair and less to the rest; average efficiency alone (G1) could move for other reasons, so G4 tests the mechanism.
- **G5 (descriptive):** verification rates in D3 and D4, and points sent to fair versus self-interested trustees in every arm.

**Human baseline.** From Johnson and Mislin's (2011) meta-analysis data (see `data/README.md`): the 150 studies in which the amount sent was tripled. Study-level mean send share converts to efficiency as (1 + 2p) / 3. It is a published benchmark, not a randomised arm; the studies used real money, other populations and other framings, and shares are compared, not points.

## Analysis

`analyze.py`, run unchanged on every dataset.

1. Per-model, per-arm resampling bootstrap, 5,000 resamples, seed 7. The pooled effect is the mean over models of the per-model difference. Human comparisons resample studies as well as games.
2. Each hypothesis reports the effect, a 95% percentile interval, and TOST p-values against +/-10 points.
3. **Labels:** *positive* if the interval excludes zero in the predicted direction (either direction when none is predicted); otherwise *null* if the interval lies inside +/-10 points; otherwise *inconclusive*. A separate "supported" column says whether the pre-registered prediction held; for H3b and G3b that means the label is *null*. One table lists every hypothesis, whatever its label.
4. **Multiplicity.** H1 and G1 are the primary tests. Every other interval is unadjusted and read as secondary; no hypothesis is dropped or promoted after the data are seen.
5. **Secondary:** the same table on games where both roles passed the comprehension check.
6. **Failures:** a call that produces more than two malformed outputs (no tool call, or invalid values) aborts its game. Aborted games are excluded from effects and counted per cell. No other game is excluded.
7. **Audit:** results are reported only if `audit.py` passes, i.e. every metric recomputes from the raw transcripts and signatures.

## What the study can and cannot show

If the standard deviation of efficiency is about 20 points (a send-share SD of 0.30), detecting a 10-point difference at 80% power needs about 64 games per arm, and showing equivalence within +/-10 points needs about 50. With two models pooled, a size of 20 games per cell gives about 40 per arm (detectable difference about 12 points, equivalence marginal); 40 gives 80 per arm; 80 gives 160 per arm; 160 gives 320 per arm (standard error about 1.6 points on a pooled difference). The measured SD replaces this assumption in the write-up.

Whatever the size, the inference is about these two models, these prompts and this one-shot game. Different models, wording or repeated play may behave differently.

(Correction to the design document: it states that 15 points corresponds to d = 0.5 and that equivalence needs about 155 games per cell. With an efficiency SD of 20 points, d = 0.5 is 10 points, needing about 64 per cell, and equivalence within +/-10 needs about 50.)

## Known limitations

- Self-play only; the same model sees both roles' rules. Cross-model pairs are a later experiment.
- The trustee's principal type is assigned by prompt, not a real hidden preference.
- In C4 and D4 the trustee is told the commitment or credential is signed while the signature is deliberately faulty; that fault is the manipulation.
- Comprehension checks test the payoff rules, not whether an agent understands enforcement. Verification behaviour is recorded separately.
- The infrastructure is simulated (Ed25519 signatures, no TEE or MPC). The interface is intended to point at real attestation later.
- One prompt wording per arm and one run date; prompt sensitivity is not tested here.
- Models may recall trust-game results from training; the neutral framing reduces but does not remove this.

## Deviations log

Revision 2, before any model run (supersedes the first commit of this file):
- The D3/D4 sender wording originally said a credential without a valid signature "was not signed by the issuer". Since the issuer signs only matching credentials, that sentence lets a sender infer that an unsigned or invalid credential is false, which makes D4 (where every signature fails) informative and contradicts the G3b prediction. Replaced by "a valid signature guarantees the credential matches; a credential without one carries no such guarantee", which is true in both arms.
- Added G4 (discrimination), since average efficiency does not show whether credentials are used to select trustees.
- Replaced the fixed pilot size and the earlier model pair by the two-vendor pair and the size rule above, after the author set a $5 budget per vendor.
- Added the multiplicity statement, the note that the comprehension check is arm-independent, and the vendor caveat.

Smoke-test findings, before any main run (no prompt changes):
- Anthropic SDK: `temperature` is no longer a named argument in the current SDK, so it is passed through `extra_body`; same value (1.0), same behaviour.
- `gpt-6-luna` rejects function tools on Chat Completions unless `reasoning_effort` is `none`. Config now sets `reasoning_effort: none` for the openai model, so it answers without extended reasoning. This is a setting difference between the two vendors' models (the Claude model runs with its default) and is stated in the write-up as a limitation.

Review of the design against the code, before analysing any main-run data (no prompt, engine, escrow or model-setting change; `git diff 20361f1 HEAD -- prompts engine.py escrow.py` is empty). At the time, 1,135 of the Claude run's 1,440 games existed, no analysis had been run on them, and the OpenAI run had not started. Each item supersedes the statement above it that it names.
- **Human baseline (supersedes "the 150 studies").** The table has 150 tripled-amount studies. One (paper_no 66) has no mean share, and one reports a mean share of 160% of the endowment, which is impossible and is a data-entry artefact. They are excluded, leaving 148. The rule depends on the human data only. Effect on the benchmark: mean efficiency 68.2 to 67.7 points. `analyze.py` prints the count it used.
- **Null predictions (supersedes "for H3b and G3b that means the label is *null*").** A null prediction means no difference as large as the smallest effect of interest, so it holds when the 95% interval lies inside +/-10 points, even if it also excludes zero. The label column is unchanged; only the "supported" column now reads "yes (equivalent ...; small non-zero difference)" in that case. Without this, a 3-point difference at 320 games per arm would have counted against a prediction of "no difference larger than 10 points".
- **Stated versus actual return** was listed under Measures but missing from the output. `cells.csv` and `results.md` now report the mean stated percentage and the mean promise gap (points actually returned minus points promised) for C2, C3 and C4.
- **Run bookkeeping.** The $5 cap was per session, because a resume restarted the counter at zero and the manifest's spend covered only the last session. Both are now cumulative, rebuilt from the token counts of the games on disk. A resume now stops if the prompts, `engine.py`, `escrow.py`, the model id, `reasoning_effort`, temperature, `max_tokens` or the seed differ from those that played the games already on disk. The manifest records every git commit used and a hash of each code file. The Claude run began at `20361f1` with the temperature fix from `6afae80` in the working tree, and continues at a later commit; the files that decide how a game is played are identical across those commits.
- **Audit.** `audit.py` now also checks each game against its arm's design: trustee type alternates by game index (none in A0); the artifact kind is the arm's; the logged message, percentage or credential equals what the trustee's tool call asked for; the commitment signature is valid in C3 and invalid in C4; a credential signature is valid in D3 only when the claim is true and invalid in D4; unsigned arms carry no signature; only C3 is paid by the game; only C3, C4, D3 and D4 have verify calls. All 1,135 Claude games pass.
- **Observation, no change.** Every malformed output so far is a first-draft trustee message over 300 characters in C1 (32 of 160 games) or D1 (39 of 160); the retry asked for a shorter message and no game was aborted. The write-up reports this.
- **Known wording tension, no change.** The sender base text says the supplier chooses the return; the C3 and C4 sender paragraph then says a validly signed commitment is paid by the game. The trustee text has "Unless the text below says otherwise"; the sender text does not. Prompts are frozen, so this is reported as a limitation.
- **Run robustness, no effect on any game.** Appending a finished game to `games.jsonl` is retried if a sync client briefly locks the file; the results report prints spend as text; the report's description of "supported" for null predictions matches the rule above. Windows `setup_windows.bat` and `run_openai.bat` run the same commands as the README.
