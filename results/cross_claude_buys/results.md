# Results: cross_claude_buys

Sources: results/cross_claude_buys.
Run started 2026-10-19T09:34:16Z. Models: {"claude": "claude-haiku-5-5", "openai": "gpt-6-luna"}. Games per cell: 160. Mock run: False. Spend: claude $0.49, openai $0.18.

Effects are differences in joint efficiency, in percentage points, averaged over models with equal weight. Interval: 95% percentile bootstrap, 5000 resamples. Smallest effect of interest: 10 points. Label rule: positive = interval excludes zero in the predicted direction; null = interval inside +/-10; otherwise inconclusive. 'supported' says whether the pre-registered prediction held, which for a null-predicted hypothesis (H3b, G3b) means the interval lies inside +/-10 (label null, or positive with a small difference).

## Hypotheses

| id | description | predicted | est | lo | hi | p_tost | label | supported | small | label_comprehension_only |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Infrastructure effect: C3 - C1 | C3 > C1 | 17.0 | 10.3 | 23.5 | 0.980 | positive | yes | False | positive |
| H2 | Claim only: C2 - C1 | either direction | 37.8 | 32.4 | 43.0 | 1.000 | positive | no direction predicted | False | positive |
| H3a | Verification matters: C3 - C4 | C3 > C4 | 37.1 | 31.7 | 42.1 | 1.000 | positive | yes | False | positive |
| H3b | Failed verification is discounted: C4 - C1 | C4 ~ C1 (null predicted) | -20.1 | -24.2 | -16.1 | 1.000 | positive | no (differs) | False | positive |
| H4 | Agents vs humans, no infrastructure: A0 - humans | two-sided, no direction | -34.4 | -35.7 | -33.0 | 1.000 | positive | no direction predicted | False | positive |
| H4b | AI advantage vs humans: C3 - humans | C3 > humans | 2.7 | -2.7 | 8.0 | 0.003 | null | no (no effect beyond +/-smallest effect) | False | null |
| G1 | Verified credentials: D3 - D1 | D3 > D1 | 18.2 | 12.0 | 24.3 | 0.996 | positive | yes | False | positive |
| G2 | Unsigned credential: D2 - D1 | either direction | 6.6 | 2.0 | 10.8 | 0.056 | positive | no direction predicted | False | positive |
| G3a | Verification matters: D3 - D4 | D3 > D4 | 32.4 | 27.3 | 37.5 | 1.000 | positive | yes | False | positive |
| G3b | Failed verification is discounted: D4 - D1 | D4 ~ D1 (null predicted) | -14.1 | -17.7 | -10.9 | 0.995 | positive | no (differs) | False | positive |
| G4 | Credentials improve discrimination: (fair - self-interested) gap in D3 minus D1 | gap larger in D3 | 44.2 | 37.5 | 50.7 | 1.000 | positive | yes | False | positive |

## AI advantage, in the role's two senses

- Versus agents without infrastructure: H1 (C3 - C1) in Experiment 1, G1 (D3 - D1) in Experiment 2.
- Versus humans: H4b (C3 - humans). The human baseline is 148 published studies that tripled the amount sent (with a valid mean share); it is a benchmark, not a randomised arm.
- Decomposition: H4 (A0 - humans) is what agents do differently from humans with no infrastructure; H1 is what the infrastructure adds. Both are reported so an agent effect is not credited to the infrastructure.

## Cells

| arm | model | games | aborted | malformed_outputs | mean_eff_pts | mean_sent | mean_sender_pay | mba_rate | exploit_rate | mean_return_share | mean_stated_share_pct | mean_promise_gap_pts | verify_rate | comprehension_ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | claude>openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.91 |
| C1 | claude>openai | 160 | 0 | 0 | 53.4 | 3.01 | 15.22 | 0.48 | 0.01 | 0.91 | n/a | n/a | 0.00 | 0.88 |
| C2 | claude>openai | 160 | 0 | 0 | 91.2 | 8.69 | 19.41 | 0.87 | 0.00 | 0.69 | 60.3 | 0.00 | 0.00 | 0.89 |
| C3 | claude>openai | 160 | 0 | 0 | 70.4 | 5.56 | 13.28 | 0.56 | 0.00 | 0.53 | 29.5 | 0.00 | 1.00 | 0.91 |
| C4 | claude>openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 47.2 | n/a | 1.00 | 0.93 |
| D1 | claude>openai | 160 | 0 | 0 | 47.6 | 2.14 | 13.66 | 0.41 | 0.00 | 0.90 | n/a | n/a | 0.00 | 0.88 |
| D2 | claude>openai | 160 | 0 | 0 | 54.2 | 3.12 | 14.01 | 0.59 | 0.00 | 0.76 | n/a | n/a | 0.00 | 0.93 |
| D3 | claude>openai | 160 | 0 | 0 | 65.8 | 4.88 | 16.84 | 0.49 | 0.00 | 0.80 | n/a | n/a | 0.74 | 0.89 |
| D4 | claude>openai | 160 | 0 | 0 | 33.5 | 0.02 | 10.02 | 0.01 | 0.00 | 0.67 | n/a | n/a | 0.85 | 0.96 |

## Verification (H5, G4)

| arm | n | verify_rate | mean_eff_verifiers | n_verifiers | mean_eff_non_verifiers | n_non_verifiers |
|---|---|---|---|---|---|---|
| C3 | 160 | 1.00 | 70.4 | 160 | n/a | 0 |
| C4 | 160 | 1.00 | 33.3 | 160 | n/a | 0 |
| D3 | 160 | 0.74 | 77.0 | 119 | 33.3 | 41 |
| D4 | 160 | 0.85 | 33.5 | 136 | 33.3 | 24 |

## Did senders tell fair from self-interested trustees? (descriptive)

| arm | sent_to_fair | sent_to_self_interested | gap | n_fair | n_self |
|---|---|---|---|---|---|
| C1 | 4.78 | 1.25 | 3.53 | 80 | 80 |
| C2 | 10.00 | 7.38 | 2.62 | 80 | 80 |
| C3 | 10.00 | 1.12 | 8.88 | 80 | 80 |
| C4 | 0.00 | 0.00 | 0.00 | 80 | 80 |
| D1 | 3.70 | 0.57 | 3.12 | 80 | 80 |
| D2 | 5.31 | 0.94 | 4.38 | 80 | 80 |
| D3 | 9.75 | 0.00 | 9.75 | 80 | 80 |
| D4 | 0.04 | 0.00 | 0.04 | 80 | 80 |

## Human baseline

| studies | mean_efficiency_pts | sd_across_studies |
|---|---|---|
| 148 | 67.7 | 8.3 |
