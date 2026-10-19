# Results: selfplay_luna

Sources: results/openai.
Run started 2026-10-19T08:10:51Z. Models: {"openai": "gpt-6-luna"}. Games per cell: 160. Mock run: False. Spend: openai $0.37.

Effects are differences in joint efficiency, in percentage points, averaged over models with equal weight. Interval: 95% percentile bootstrap, 5000 resamples. Smallest effect of interest: 10 points. Label rule: positive = interval excludes zero in the predicted direction; null = interval inside +/-10; otherwise inconclusive. 'supported' says whether the pre-registered prediction held, which for a null-predicted hypothesis (H3b, G3b) means the interval lies inside +/-10 (label null, or positive with a small difference).

## Hypotheses

| id | description | predicted | est | lo | hi | p_tost | label | supported | small | label_comprehension_only |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Infrastructure effect: C3 - C1 | C3 > C1 | 35.2 | 30.2 | 40.5 | 1.000 | positive | yes | False | positive |
| H2 | Claim only: C2 - C1 | either direction | -0.2 | -0.4 | -0.0 | 0.000 | positive | no direction predicted | True | positive |
| H3a | Verification matters: C3 - C4 | C3 > C4 | 35.4 | 30.0 | 40.4 | 1.000 | positive | yes | False | positive |
| H3b | Failed verification is discounted: C4 - C1 | C4 ~ C1 (null predicted) | -0.2 | -0.4 | -0.0 | 0.000 | positive | yes (equivalent within +/-smallest effect; small non-zero difference) | True | positive |
| H4 | Agents vs humans, no infrastructure: A0 - humans | two-sided, no direction | -34.4 | -35.7 | -33.0 | 1.000 | positive | no direction predicted | False | positive |
| H4b | AI advantage vs humans: C3 - humans | C3 > humans | 1.1 | -4.2 | 6.4 | 0.001 | null | no (no effect beyond +/-smallest effect) | False | null |
| G1 | Verified credentials: D3 - D1 | D3 > D1 | 24.0 | 19.0 | 29.1 | 1.000 | positive | yes | False | positive |
| G2 | Unsigned credential: D2 - D1 | either direction | -0.6 | -1.5 | -0.0 | 0.000 | positive | no direction predicted | True | null |
| G3a | Verification matters: D3 - D4 | D3 > D4 | 24.6 | 19.6 | 29.6 | 1.000 | positive | yes | False | positive |
| G3b | Failed verification is discounted: D4 - D1 | D4 ~ D1 (null predicted) | -0.6 | -1.6 | -0.0 | 0.000 | positive | yes (equivalent within +/-smallest effect; small non-zero difference) | True | null |
| G4 | Credentials improve discrimination: (fair - self-interested) gap in D3 minus D1 | gap larger in D3 | 48.0 | 41.3 | 54.6 | 1.000 | positive | yes | False | positive |

## AI advantage, in the role's two senses

- Versus agents without infrastructure: H1 (C3 - C1) in Experiment 1, G1 (D3 - D1) in Experiment 2.
- Versus humans: H4b (C3 - humans). The human baseline is 148 published studies that tripled the amount sent (with a valid mean share); it is a benchmark, not a randomised arm.
- Decomposition: H4 (A0 - humans) is what agents do differently from humans with no infrastructure; H1 is what the infrastructure adds. Both are reported so an agent effect is not credited to the infrastructure.

## Cells

| arm | model | games | aborted | malformed_outputs | mean_eff_pts | mean_sent | mean_sender_pay | mba_rate | exploit_rate | mean_return_share | mean_stated_share_pct | mean_promise_gap_pts | verify_rate | comprehension_ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.84 |
| C1 | openai | 160 | 0 | 0 | 33.5 | 0.03 | 10.06 | 0.03 | 0.00 | 0.93 | n/a | n/a | 0.00 | 0.75 |
| C2 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 60.0 | n/a | 0.00 | 0.72 |
| C3 | openai | 160 | 0 | 0 | 68.8 | 5.31 | 13.56 | 0.53 | 0.00 | 0.56 | 29.6 | 0.00 | 1.00 | 0.72 |
| C4 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 60.6 | n/a | 1.00 | 0.79 |
| D1 | openai | 160 | 0 | 0 | 33.9 | 0.09 | 10.17 | 0.03 | 0.00 | 0.92 | n/a | n/a | 0.00 | 0.77 |
| D2 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.89 |
| D3 | openai | 160 | 0 | 0 | 57.9 | 3.69 | 15.12 | 0.37 | 0.00 | 0.80 | n/a | n/a | 0.67 | 0.78 |
| D4 | openai | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.76 | 0.83 |

## Verification (H5, G4)

| arm | n | verify_rate | mean_eff_verifiers | n_verifiers | mean_eff_non_verifiers | n_non_verifiers |
|---|---|---|---|---|---|---|
| C3 | 160 | 1.00 | 68.8 | 160 | n/a | 0 |
| C4 | 160 | 1.00 | 33.3 | 160 | n/a | 0 |
| D3 | 160 | 0.67 | 70.1 | 107 | 33.3 | 53 |
| D4 | 160 | 0.76 | 33.3 | 121 | 33.3 | 39 |

## Did senders tell fair from self-interested trustees? (descriptive)

| arm | sent_to_fair | sent_to_self_interested | gap | n_fair | n_self |
|---|---|---|---|---|---|
| C1 | 0.06 | 0.00 | 0.06 | 80 | 80 |
| C2 | 0.00 | 0.00 | 0.00 | 80 | 80 |
| C3 | 10.00 | 0.62 | 9.38 | 80 | 80 |
| C4 | 0.00 | 0.00 | 0.00 | 80 | 80 |
| D1 | 0.17 | 0.00 | 0.17 | 80 | 80 |
| D2 | 0.00 | 0.00 | 0.00 | 80 | 80 |
| D3 | 7.38 | 0.00 | 7.38 | 80 | 80 |
| D4 | 0.00 | 0.00 | 0.00 | 80 | 80 |

## Human baseline

| studies | mean_efficiency_pts | sd_across_studies |
|---|---|---|
| 148 | 67.7 | 8.3 |
