# Results: cross_openai_buys

Sources: results/cross_openai_buys.
Run started 2026-10-19T10:06:12Z. Models: {"claude": "claude-haiku-5-5", "openai": "gpt-6-luna"}. Games per cell: 160. Mock run: False. Spend: claude $0.40, openai $0.23.

Effects are differences in joint efficiency, in percentage points, averaged over models with equal weight. Interval: 95% percentile bootstrap, 5000 resamples. Smallest effect of interest: 10 points. Label rule: positive = interval excludes zero in the predicted direction; null = interval inside +/-10; otherwise inconclusive. 'supported' says whether the pre-registered prediction held, which for a null-predicted hypothesis (H3b, G3b) means the interval lies inside +/-10 (label null, or positive with a small difference).

## Hypotheses

| id | description | predicted | est | lo | hi | p_tost | label | supported | small | label_comprehension_only |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Infrastructure effect: C3 - C1 | C3 > C1 | 64.2 | 62.7 | 65.4 | 1.000 | positive | yes | False | positive |
| H2 | Claim only: C2 - C1 | either direction | -2.5 | -3.9 | -1.3 | 0.000 | positive | no direction predicted | True | positive |
| H3a | Verification matters: C3 - C4 | C3 > C4 | 66.7 | 66.7 | 66.7 | 1.000 | positive | yes | False | positive |
| H3b | Failed verification is discounted: C4 - C1 | C4 ~ C1 (null predicted) | -2.5 | -3.8 | -1.3 | 0.000 | positive | yes (equivalent within +/-smallest effect; small non-zero difference) | True | positive |
| H4 | Agents vs humans, no infrastructure: A0 - humans | two-sided, no direction | -34.4 | -35.7 | -33.0 | 1.000 | positive | no direction predicted | False | positive |
| H4b | AI advantage vs humans: C3 - humans | C3 > humans | 32.3 | 31.0 | 33.6 | 1.000 | positive | yes | False | positive |
| G1 | Verified credentials: D3 - D1 | D3 > D1 | 30.2 | 24.8 | 35.6 | 1.000 | positive | yes | False | positive |
| G2 | Unsigned credential: D2 - D1 | either direction | -3.1 | -4.8 | -1.7 | 0.000 | positive | no direction predicted | True | positive |
| G3a | Verification matters: D3 - D4 | D3 > D4 | 33.3 | 28.3 | 38.8 | 1.000 | positive | yes | False | positive |
| G3b | Failed verification is discounted: D4 - D1 | D4 ~ D1 (null predicted) | -3.1 | -4.8 | -1.7 | 0.000 | positive | yes (equivalent within +/-smallest effect; small non-zero difference) | True | positive |
| G4 | Credentials improve discrimination: (fair - self-interested) gap in D3 minus D1 | gap larger in D3 | 66.4 | 63.3 | 69.7 | 1.000 | positive | yes | False | positive |

## AI advantage, in the role's two senses

- Versus agents without infrastructure: H1 (C3 - C1) in Experiment 1, G1 (D3 - D1) in Experiment 2.
- Versus humans: H4b (C3 - humans). The human baseline is 148 published studies that tripled the amount sent (with a valid mean share); it is a benchmark, not a randomised arm.
- Decomposition: H4 (A0 - humans) is what agents do differently from humans with no infrastructure; H1 is what the infrastructure adds. Both are reported so an agent effect is not credited to the infrastructure.

## Cells

| arm | model | games | aborted | malformed_outputs | mean_eff_pts | mean_sent | mean_sender_pay | mba_rate | exploit_rate | mean_return_share | mean_stated_share_pct | mean_promise_gap_pts | verify_rate | comprehension_ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.92 |
| C1 | openai>claude | 160 | 0 | 32 | 35.8 | 0.38 | 10.22 | 0.15 | 0.00 | 0.54 | n/a | n/a | 0.00 | 0.95 |
| C2 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 27.5 | n/a | 0.00 | 0.91 |
| C3 | openai>claude | 160 | 0 | 0 | 100.0 | 10.00 | 11.79 | 1.00 | 0.00 | 0.39 | 39.6 | 0.00 | 1.00 | 0.91 |
| C4 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | 24.1 | n/a | 1.00 | 0.85 |
| D1 | openai>claude | 160 | 0 | 34 | 36.5 | 0.47 | 10.21 | 0.12 | 0.00 | 0.49 | n/a | n/a | 0.00 | 0.88 |
| D2 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.00 | 0.79 |
| D3 | openai>claude | 160 | 0 | 0 | 66.7 | 5.00 | 12.50 | 0.50 | 0.00 | 0.50 | n/a | n/a | 0.99 | 0.88 |
| D4 | openai>claude | 160 | 0 | 0 | 33.3 | 0.00 | 10.00 | 0.00 | 0.00 | n/a | n/a | n/a | 0.98 | 0.84 |

## Verification (H5, G4)

| arm | n | verify_rate | mean_eff_verifiers | n_verifiers | mean_eff_non_verifiers | n_non_verifiers |
|---|---|---|---|---|---|---|
| C3 | 160 | 1.00 | 100.0 | 160 | n/a | 0 |
| C4 | 160 | 1.00 | 33.3 | 160 | n/a | 0 |
| D3 | 160 | 0.99 | 66.9 | 159 | 33.3 | 1 |
| D4 | 160 | 0.98 | 33.3 | 157 | 33.3 | 3 |

## Did senders tell fair from self-interested trustees? (descriptive)

| arm | sent_to_fair | sent_to_self_interested | gap | n_fair | n_self |
|---|---|---|---|---|---|
| C1 | 0.68 | 0.07 | 0.60 | 80 | 80 |
| C2 | 0.00 | 0.00 | 0.00 | 80 | 80 |
| C3 | 10.00 | 10.00 | 0.00 | 80 | 80 |
| C4 | 0.00 | 0.00 | 0.00 | 80 | 80 |
| D1 | 0.49 | 0.45 | 0.04 | 80 | 80 |
| D2 | 0.00 | 0.00 | 0.00 | 80 | 80 |
| D3 | 10.00 | 0.00 | 10.00 | 80 | 80 |
| D4 | 0.00 | 0.00 | 0.00 | 80 | 80 |

## Human baseline

| studies | mean_efficiency_pts | sd_across_studies |
|---|---|---|
| 148 | 67.7 | 8.3 |
