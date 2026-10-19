# Results: cross_combined

Sources: results/cross_claude_buys, results/cross_openai_buys.
Run started 2026-10-19T09:34:16Z. Models: {"claude": "claude-haiku-5-5", "openai": "gpt-6-luna"}. Games per cell: 160. Mock run: False. Spend: claude $0.40, openai $0.23.

Effects are differences in joint efficiency, in percentage points, averaged over models with equal weight. Interval: 95% percentile bootstrap, 5000 resamples. Smallest effect of interest: 10 points. Label rule: positive = interval excludes zero in the predicted direction; null = interval inside +/-10; otherwise inconclusive. 'supported' says whether the pre-registered prediction held, which for a null-predicted hypothesis (H3b, G3b) means the interval lies inside +/-10 (label null, or positive with a small difference).

## Hypotheses

| id | description | predicted | est | lo | hi | p_tost | label | supported | small | label_comprehension_only |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Infrastructure effect: C3 - C1 | C3 > C1 | 40.6 | 37.1 | 43.9 | 1.000 | positive | yes | False | positive |
| H2 | Claim only: C2 - C1 | either direction | 17.7 | 14.8 | 20.4 | 1.000 | positive | no direction predicted | False | positive |
| H3a | Verification matters: C3 - C4 | C3 > C4 | 51.9 | 49.4 | 54.4 | 1.000 | positive | yes | False | positive |
| H3b | Failed verification is discounted: C4 - C1 | C4 ~ C1 (null predicted) | -11.3 | -13.4 | -9.1 | 0.882 | positive | no (differs) | False | positive |
| H4 | Agents vs humans, no infrastructure: A0 - humans | two-sided, no direction | -34.4 | -35.7 | -33.1 | 1.000 | positive | no direction predicted | False | positive |
| H4b | AI advantage vs humans: C3 - humans | C3 > humans | 17.5 | 14.6 | 20.4 | 1.000 | positive | yes | False | positive |
| G1 | Verified credentials: D3 - D1 | D3 > D1 | 24.2 | 20.1 | 28.3 | 1.000 | positive | yes | False | positive |
| G2 | Unsigned credential: D2 - D1 | either direction | 1.7 | -0.7 | 4.1 | 0.000 | null | no direction predicted | False | null |
| G3a | Verification matters: D3 - D4 | D3 > D4 | 32.9 | 29.2 | 36.5 | 1.000 | positive | yes | False | positive |
| G3b | Failed verification is discounted: D4 - D1 | D4 ~ D1 (null predicted) | -8.6 | -10.6 | -6.7 | 0.084 | positive | no (differs) | False | positive |
| G4 | Credentials improve discrimination: (fair - self-interested) gap in D3 minus D1 | gap larger in D3 | 55.3 | 51.6 | 58.8 | 1.000 | positive | yes | False | positive |

## AI advantage, in the role's two senses

- Versus agents without infrastructure: H1 (C3 - C1) in Experiment 1, G1 (D3 - D1) in Experiment 2.
- Versus humans: H4b (C3 - humans). The human baseline is 148 published studies that tripled the amount sent (with a valid mean share); it is a benchmark, not a randomised arm.
- Decomposition: H4 (A0 - humans) is what agents do differently from humans with no infrastructure; H1 is what the infrastructure adds. Both are reported so an agent effect is not credited to the infrastructure.

## Cells

| arm | model | games | aborted | malformed_outputs | mean_eff_pts | mean_sent | mean_sender_pay | mba_rate | exploit_rate | mean_return_share | mean_stated_share_pct | mean_promise_gap_pts | verify_rate | comprehension_ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | claude>openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.91 |
| A0 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.92 |
| C1 | claude>openai | 160 | 0 | 0 | 53.4 | 3.01 | 15.22 | 0.48 | 0.01 | 0.91 | n/a | n/a | 0.00 | 0.88 |
| C1 | openai>claude | 160 | 0 | 32 | 35.8 | 0.38 | 10.22 | 0.15 | 0.00 | 0.54 | n/a | n/a | 0.00 | 0.95 |
| C2 | claude>openai | 160 | 0 | 0 | 91.2 | 8.69 | 19.41 | 0.87 | 0.00 | 0.69 | 60.3 | 0.00 | 0.00 | 0.89 |
| C2 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 27.5 | n/a | 0.00 | 0.91 |
| C3 | claude>openai | 160 | 0 | 0 | 70.4 | 5.56 | 13.28 | 0.56 | 0.00 | 0.53 | 29.5 | 0.00 | 1.00 | 0.91 |
| C3 | openai>claude | 160 | 0 | 0 | 100.0 | 10.00 | 11.79 | 1.00 | 0.00 | 0.39 | 39.6 | 0.00 | 1.00 | 0.91 |
| C4 | claude>openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 47.2 | n/a | 1.00 | 0.93 |
| C4 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 24.1 | n/a | 1.00 | 0.85 |
| D1 | claude>openai | 160 | 0 | 0 | 47.6 | 2.14 | 13.66 | 0.41 | 0.00 | 0.90 | n/a | n/a | 0.00 | 0.88 |
| D1 | openai>claude | 160 | 0 | 34 | 36.5 | 0.47 | 10.21 | 0.12 | 0.00 | 0.49 | n/a | n/a | 0.00 | 0.88 |
| D2 | claude>openai | 160 | 0 | 0 | 54.2 | 3.12 | 14.01 | 0.59 | 0.00 | 0.76 | n/a | n/a | 0.00 | 0.93 |
| D2 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.79 |
| D3 | claude>openai | 160 | 0 | 0 | 65.8 | 4.88 | 16.84 | 0.49 | 0.00 | 0.80 | n/a | n/a | 0.74 | 0.89 |
| D3 | openai>claude | 160 | 0 | 0 | 66.7 | 5.00 | 12.50 | 0.50 | 0.00 | 0.50 | n/a | n/a | 0.99 | 0.88 |
| D4 | claude>openai | 160 | 0 | 0 | 33.5 | 0.02 | 10.02 | 0.01 | 0.00 | 0.67 | n/a | n/a | 0.85 | 0.96 |
| D4 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.98 | 0.84 |

## Verification (H5, G4)

| arm | n | verify_rate | mean_eff_verifiers | n_verifiers | mean_eff_non_verifiers | n_non_verifiers |
|---|---|---|---|---|---|---|
| C3 | 320 | 1.00 | 85.2 | 320 | n/a | 0 |
| C4 | 320 | 1.00 | 33.3 | 320 | n/a | 0 |
| D3 | 320 | 0.87 | 71.2 | 278 | 33.3 | 42 |
| D4 | 320 | 0.92 | 33.4 | 293 | 33.3 | 27 |

## Did senders tell fair from self-interested trustees? (descriptive)

| arm | sent_to_fair | sent_to_self_interested | gap | n_fair | n_self |
|---|---|---|---|---|---|
| C1 | 2.73 | 0.66 | 2.06 | 160 | 160 |
| C2 | 5.00 | 3.69 | 1.31 | 160 | 160 |
| C3 | 10.00 | 5.56 | 4.44 | 160 | 160 |
| C4 | 0.00 | 0.00 | 0.00 | 160 | 160 |
| D1 | 2.09 | 0.51 | 1.58 | 160 | 160 |
| D2 | 2.66 | 0.47 | 2.19 | 160 | 160 |
| D3 | 9.88 | 0.00 | 9.88 | 160 | 160 |
| D4 | 0.02 | 0.00 | 0.02 | 160 | 160 |

## Human baseline

| studies | mean_efficiency_pts | sd_across_studies |
|---|---|---|
| 148 | 67.7 | 8.3 |
