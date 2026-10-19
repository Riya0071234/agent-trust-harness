# Results: stronger_sol

Sources: results/stronger_openai_sol.
Run started 2026-10-19T11:41:26Z. Models: {"openai_sol": "gpt-6.1-sol"}. Games per cell: 40. Mock run: False. Spend: openai_sol $1.21.

Effects are differences in joint efficiency, in percentage points, averaged over models with equal weight. Interval: 95% percentile bootstrap, 5000 resamples. Smallest effect of interest: 10 points. Label rule: positive = interval excludes zero in the predicted direction; null = interval inside +/-10; otherwise inconclusive. 'supported' says whether the pre-registered prediction held, which for a null-predicted hypothesis (H3b, G3b) means the interval lies inside +/-10 (label null, or positive with a small difference).

## Hypotheses

| id | description | predicted | est | lo | hi | p_tost | label | supported | small | label_comprehension_only |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Infrastructure effect: C3 - C1 | C3 > C1 | 65.2 | 62.2 | 66.7 | 1.000 | positive | yes | False | positive |
| H2 | Claim only: C2 - C1 | either direction | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| H3a | Verification matters: C3 - C4 | C3 > C4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| H3b | Failed verification is discounted: C4 - C1 | C4 ~ C1 (null predicted) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| H4 | Agents vs humans, no infrastructure: A0 - humans | two-sided, no direction | -34.4 | -35.7 | -33.0 | 1.000 | positive | no direction predicted | False | positive |
| H4b | AI advantage vs humans: C3 - humans | C3 > humans | 32.3 | 31.0 | 33.7 | 1.000 | positive | yes | False | positive |
| G1 | Verified credentials: D3 - D1 | D3 > D1 | 32.5 | 21.7 | 43.3 | 1.000 | positive | yes | False | positive |
| G2 | Unsigned credential: D2 - D1 | either direction | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| G3a | Verification matters: D3 - D4 | D3 > D4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| G3b | Failed verification is discounted: D4 - D1 | D4 ~ D1 (null predicted) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| G4 | Credentials improve discrimination: (fair - self-interested) gap in D3 minus D1 | gap larger in D3 | 65.0 | 61.7 | 66.7 | 1.000 | positive | yes | False | positive |

## AI advantage, in the role's two senses

- Versus agents without infrastructure: H1 (C3 - C1) in Experiment 1, G1 (D3 - D1) in Experiment 2.
- Versus humans: H4b (C3 - humans). The human baseline is 148 published studies that tripled the amount sent (with a valid mean share); it is a benchmark, not a randomised arm.
- Decomposition: H4 (A0 - humans) is what agents do differently from humans with no infrastructure; H1 is what the infrastructure adds. Both are reported so an agent effect is not credited to the infrastructure.

## Cells

| arm | model | games | aborted | malformed_outputs | mean_eff_pts | mean_sent | mean_sender_pay | mba_rate | exploit_rate | mean_return_share | mean_stated_share_pct | mean_promise_gap_pts | verify_rate | comprehension_ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | openai_sol | 40 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 1.00 |
| C1 | openai_sol | 40 | 0 | 0 | 34.8 | 0.23 | 10.22 | 0.03 | 0.00 | 0.67 | n/a | n/a | 0.00 | 1.00 |
| C3 | openai_sol | 40 | 0 | 0 | 100.0 | 10.00 | 12.50 | 1.00 | 0.00 | 0.42 | 42.0 | 0.00 | 1.00 | 1.00 |
| D1 | openai_sol | 40 | 0 | 0 | 34.2 | 0.12 | 10.12 | 0.03 | 0.00 | 0.67 | n/a | n/a | 0.00 | 1.00 |
| D3 | openai_sol | 40 | 0 | 0 | 66.7 | 5.00 | 12.50 | 0.50 | 0.00 | 0.50 | n/a | n/a | 0.50 | 1.00 |

## Verification (H5, G4)

| arm | n | verify_rate | mean_eff_verifiers | n_verifiers | mean_eff_non_verifiers | n_non_verifiers |
|---|---|---|---|---|---|---|
| C3 | 40 | 1.00 | 100.0 | 40 | n/a | 0 |
| D3 | 40 | 0.50 | 100.0 | 20 | 33.3 | 20 |

## Did senders tell fair from self-interested trustees? (descriptive)

| arm | sent_to_fair | sent_to_self_interested | gap | n_fair | n_self |
|---|---|---|---|---|---|
| C1 | 0.45 | 0.00 | 0.45 | 20 | 20 |
| C3 | 10.00 | 10.00 | 0.00 | 20 | 20 |
| D1 | 0.25 | 0.00 | 0.25 | 20 | 20 |
| D3 | 10.00 | 0.00 | 10.00 | 20 | 20 |

## Human baseline

| studies | mean_efficiency_pts | sd_across_studies |
|---|---|---|
| 148 | 67.7 | 8.3 |
