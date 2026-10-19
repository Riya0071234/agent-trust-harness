# Results: selfplay_haiku

Sources: results/claude.
Run started 2026-10-19T06:34:44Z. Models: {"claude": "claude-haiku-5-5"}. Games per cell: 160. Mock run: False. Spend: claude $0.97.

Effects are differences in joint efficiency, in percentage points, averaged over models with equal weight. Interval: 95% percentile bootstrap, 5000 resamples. Smallest effect of interest: 10 points. Label rule: positive = interval excludes zero in the predicted direction; null = interval inside +/-10; otherwise inconclusive. 'supported' says whether the pre-registered prediction held, which for a null-predicted hypothesis (H3b, G3b) means the interval lies inside +/-10 (label null, or positive with a small difference).

## Hypotheses

| id | description | predicted | est | lo | hi | p_tost | label | supported | small | label_comprehension_only |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Infrastructure effect: C3 - C1 | C3 > C1 | 26.9 | 21.7 | 31.8 | 1.000 | positive | yes | False | positive |
| H2 | Claim only: C2 - C1 | either direction | 8.2 | 2.0 | 14.2 | 0.276 | positive | no direction predicted | False | positive |
| H3a | Verification matters: C3 - C4 | C3 > C4 | 54.6 | 50.4 | 58.3 | 1.000 | positive | yes | False | positive |
| H3b | Failed verification is discounted: C4 - C1 | C4 ~ C1 (null predicted) | -27.7 | -31.0 | -24.7 | 1.000 | positive | no (differs) | False | positive |
| H4 | Agents vs humans, no infrastructure: A0 - humans | two-sided, no direction | -34.4 | -35.7 | -33.0 | 1.000 | positive | no direction predicted | False | positive |
| H4b | AI advantage vs humans: C3 - humans | C3 > humans | 20.2 | 16.0 | 24.2 | 1.000 | positive | yes | False | positive |
| G1 | Verified credentials: D3 - D1 | D3 > D1 | 7.8 | 2.0 | 13.7 | 0.237 | positive | yes | False | positive |
| G2 | Unsigned credential: D2 - D1 | either direction | -5.1 | -9.6 | -0.6 | 0.018 | positive | no direction predicted | True | positive |
| G3a | Verification matters: D3 - D4 | D3 > D4 | 32.9 | 27.9 | 38.1 | 1.000 | positive | yes | False | positive |
| G3b | Failed verification is discounted: D4 - D1 | D4 ~ D1 (null predicted) | -25.1 | -27.8 | -22.4 | 1.000 | positive | no (differs) | False | positive |
| G4 | Credentials improve discrimination: (fair - self-interested) gap in D3 minus D1 | gap larger in D3 | 66.5 | 61.1 | 72.1 | 1.000 | positive | yes | False | positive |

## AI advantage, in the role's two senses

- Versus agents without infrastructure: H1 (C3 - C1) in Experiment 1, G1 (D3 - D1) in Experiment 2.
- Versus humans: H4b (C3 - humans). The human baseline is 148 published studies that tripled the amount sent (with a valid mean share); it is a benchmark, not a randomised arm.
- Decomposition: H4 (A0 - humans) is what agents do differently from humans with no infrastructure; H1 is what the infrastructure adds. Both are reported so an agent effect is not credited to the infrastructure.

## Cells

| arm | model | games | aborted | malformed_outputs | mean_eff_pts | mean_sent | mean_sender_pay | mba_rate | exploit_rate | mean_return_share | mean_stated_share_pct | mean_promise_gap_pts | verify_rate | comprehension_ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 1.00 |
| C1 | claude | 160 | 0 | 32 | 61.0 | 4.16 | 11.66 | 0.68 | 0.03 | 0.47 | n/a | n/a | 0.00 | 1.00 |
| C2 | claude | 160 | 0 | 0 | 69.2 | 5.39 | 12.91 | 0.55 | 0.00 | 0.51 | 28.1 | 0.00 | 0.00 | 1.00 |
| C3 | claude | 160 | 0 | 0 | 87.9 | 8.19 | 11.63 | 0.82 | 0.00 | 0.40 | 39.6 | 0.00 | 1.00 | 1.00 |
| C4 | claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 23.4 | n/a | 1.00 | 1.00 |
| D1 | claude | 160 | 0 | 39 | 58.8 | 3.83 | 11.70 | 0.72 | 0.01 | 0.49 | n/a | n/a | 0.00 | 1.00 |
| D2 | claude | 160 | 0 | 0 | 53.7 | 3.06 | 11.69 | 0.50 | 0.00 | 0.52 | n/a | n/a | 0.00 | 1.00 |
| D3 | claude | 160 | 0 | 0 | 66.7 | 5.00 | 12.50 | 0.50 | 0.00 | 0.50 | n/a | n/a | 0.98 | 1.00 |
| D4 | claude | 160 | 0 | 0 | 33.7 | 0.06 | 10.03 | 0.01 | 0.00 | 0.47 | n/a | n/a | 0.96 | 1.00 |

## Verification (H5, G4)

| arm | n | verify_rate | mean_eff_verifiers | n_verifiers | mean_eff_non_verifiers | n_non_verifiers |
|---|---|---|---|---|---|---|
| C3 | 160 | 1.00 | 87.9 | 160 | n/a | 0 |
| C4 | 160 | 1.00 | 33.3 | 160 | n/a | 0 |
| D3 | 160 | 0.98 | 67.3 | 157 | 33.3 | 3 |
| D4 | 160 | 0.96 | 33.8 | 153 | 33.3 | 7 |

## Did senders tell fair from self-interested trustees? (descriptive)

| arm | sent_to_fair | sent_to_self_interested | gap | n_fair | n_self |
|---|---|---|---|---|---|
| C1 | 4.31 | 4.00 | 0.31 | 80 | 80 |
| C2 | 10.00 | 0.78 | 9.22 | 80 | 80 |
| C3 | 8.75 | 7.62 | 1.12 | 80 | 80 |
| C4 | 0.00 | 0.00 | 0.00 | 80 | 80 |
| D1 | 3.84 | 3.81 | 0.02 | 80 | 80 |
| D2 | 6.12 | 0.00 | 6.12 | 80 | 80 |
| D3 | 10.00 | 0.00 | 10.00 | 80 | 80 |
| D4 | 0.12 | 0.00 | 0.12 | 80 | 80 |

## Human baseline

| studies | mean_efficiency_pts | sd_across_studies |
|---|---|---|
| 148 | 67.7 | 8.3 |
