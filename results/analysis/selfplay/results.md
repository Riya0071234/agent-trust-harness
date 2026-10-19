# Results: selfplay

Sources: results/claude, results/openai.
Run started 2026-10-19T06:34:44Z. Models: {"claude": "claude-haiku-5-5", "openai": "gpt-6-luna"}. Games per cell: 160. Mock run: False. Spend: claude $0.97, openai $0.37.

Effects are differences in joint efficiency, in percentage points, averaged over models with equal weight. Interval: 95% percentile bootstrap, 5000 resamples. Smallest effect of interest: 10 points. Label rule: positive = interval excludes zero in the predicted direction; null = interval inside +/-10; otherwise inconclusive. 'supported' says whether the pre-registered prediction held, which for a null-predicted hypothesis (H3b, G3b) means the interval lies inside +/-10 (label null, or positive with a small difference).

## Hypotheses

| id | description | predicted | est | lo | hi | p_tost | label | supported | small | label_comprehension_only |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Infrastructure effect: C3 - C1 | C3 > C1 | 31.0 | 27.4 | 34.7 | 1.000 | positive | yes | False | positive |
| H2 | Claim only: C2 - C1 | either direction | 4.0 | 1.0 | 7.0 | 0.000 | positive | no direction predicted | True | positive |
| H3a | Verification matters: C3 - C4 | C3 > C4 | 45.0 | 41.7 | 48.3 | 1.000 | positive | yes | False | positive |
| H3b | Failed verification is discounted: C4 - C1 | C4 ~ C1 (null predicted) | -14.0 | -15.5 | -12.4 | 1.000 | positive | no (differs) | False | positive |
| H4 | Agents vs humans, no infrastructure: A0 - humans | two-sided, no direction | -34.4 | -35.7 | -33.1 | 1.000 | positive | no direction predicted | False | positive |
| H4b | AI advantage vs humans: C3 - humans | C3 > humans | 10.6 | 7.1 | 14.2 | 0.641 | positive | yes | False | positive |
| G1 | Verified credentials: D3 - D1 | D3 > D1 | 15.9 | 12.0 | 19.8 | 0.999 | positive | yes | False | positive |
| G2 | Unsigned credential: D2 - D1 | either direction | -2.8 | -5.2 | -0.6 | 0.000 | positive | no direction predicted | True | positive |
| G3a | Verification matters: D3 - D4 | D3 > D4 | 28.8 | 25.2 | 32.4 | 1.000 | positive | yes | False | positive |
| G3b | Failed verification is discounted: D4 - D1 | D4 ~ D1 (null predicted) | -12.8 | -14.3 | -11.4 | 1.000 | positive | no (differs) | False | positive |
| G4 | Credentials improve discrimination: (fair - self-interested) gap in D3 minus D1 | gap larger in D3 | 57.3 | 53.0 | 61.6 | 1.000 | positive | yes | False | positive |

## AI advantage, in the role's two senses

- Versus agents without infrastructure: H1 (C3 - C1) in Experiment 1, G1 (D3 - D1) in Experiment 2.
- Versus humans: H4b (C3 - humans). The human baseline is 148 published studies that tripled the amount sent (with a valid mean share); it is a benchmark, not a randomised arm.
- Decomposition: H4 (A0 - humans) is what agents do differently from humans with no infrastructure; H1 is what the infrastructure adds. Both are reported so an agent effect is not credited to the infrastructure.

## Cells

| arm | model | games | aborted | malformed_outputs | mean_eff_pts | mean_sent | mean_sender_pay | mba_rate | exploit_rate | mean_return_share | mean_stated_share_pct | mean_promise_gap_pts | verify_rate | comprehension_ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 1.00 |
| A0 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.84 |
| C1 | claude | 160 | 0 | 32 | 61.0 | 4.16 | 11.66 | 0.68 | 0.03 | 0.47 | n/a | n/a | 0.00 | 1.00 |
| C1 | openai | 160 | 0 | 0 | 33.5 | 0.03 | 10.06 | 0.03 | 0.00 | 0.93 | n/a | n/a | 0.00 | 0.75 |
| C2 | claude | 160 | 0 | 0 | 69.2 | 5.39 | 12.91 | 0.55 | 0.00 | 0.51 | 28.1 | 0.00 | 0.00 | 1.00 |
| C2 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 60.0 | n/a | 0.00 | 0.72 |
| C3 | claude | 160 | 0 | 0 | 87.9 | 8.19 | 11.63 | 0.82 | 0.00 | 0.40 | 39.6 | 0.00 | 1.00 | 1.00 |
| C3 | openai | 160 | 0 | 0 | 68.8 | 5.31 | 13.56 | 0.53 | 0.00 | 0.56 | 29.6 | 0.00 | 1.00 | 0.72 |
| C4 | claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 23.4 | n/a | 1.00 | 1.00 |
| C4 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 60.6 | n/a | 1.00 | 0.79 |
| D1 | claude | 160 | 0 | 39 | 58.8 | 3.83 | 11.70 | 0.72 | 0.01 | 0.49 | n/a | n/a | 0.00 | 1.00 |
| D1 | openai | 160 | 0 | 0 | 33.9 | 0.09 | 10.17 | 0.03 | 0.00 | 0.92 | n/a | n/a | 0.00 | 0.77 |
| D2 | claude | 160 | 0 | 0 | 53.7 | 3.06 | 11.69 | 0.50 | 0.00 | 0.52 | n/a | n/a | 0.00 | 1.00 |
| D2 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.89 |
| D3 | claude | 160 | 0 | 0 | 66.7 | 5.00 | 12.50 | 0.50 | 0.00 | 0.50 | n/a | n/a | 0.98 | 1.00 |
| D3 | openai | 160 | 0 | 0 | 57.9 | 3.69 | 15.12 | 0.37 | 0.00 | 0.80 | n/a | n/a | 0.67 | 0.78 |
| D4 | claude | 160 | 0 | 0 | 33.7 | 0.06 | 10.03 | 0.01 | 0.00 | 0.47 | n/a | n/a | 0.96 | 1.00 |
| D4 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.76 | 0.83 |

## Verification (H5, G4)

| arm | n | verify_rate | mean_eff_verifiers | n_verifiers | mean_eff_non_verifiers | n_non_verifiers |
|---|---|---|---|---|---|---|
| C3 | 320 | 1.00 | 78.3 | 320 | n/a | 0 |
| C4 | 320 | 1.00 | 33.3 | 320 | n/a | 0 |
| D3 | 320 | 0.82 | 68.4 | 264 | 33.3 | 56 |
| D4 | 320 | 0.86 | 33.6 | 274 | 33.3 | 46 |

## Did senders tell fair from self-interested trustees? (descriptive)

| arm | sent_to_fair | sent_to_self_interested | gap | n_fair | n_self |
|---|---|---|---|---|---|
| C1 | 2.19 | 2.00 | 0.19 | 160 | 160 |
| C2 | 5.00 | 0.39 | 4.61 | 160 | 160 |
| C3 | 9.38 | 4.12 | 5.25 | 160 | 160 |
| C4 | 0.00 | 0.00 | 0.00 | 160 | 160 |
| D1 | 2.01 | 1.91 | 0.10 | 160 | 160 |
| D2 | 3.06 | 0.00 | 3.06 | 160 | 160 |
| D3 | 8.69 | 0.00 | 8.69 | 160 | 160 |
| D4 | 0.06 | 0.00 | 0.06 | 160 | 160 |

## Human baseline

| studies | mean_efficiency_pts | sd_across_studies |
|---|---|---|
| 148 | 67.7 | 8.3 |
