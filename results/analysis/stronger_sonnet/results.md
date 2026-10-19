# Results: stronger_sonnet

Sources: results/stronger_claude_sonnet.
Run started 2026-10-19T09:13:44Z. Models: {"claude_sonnet": "claude-sonnet-5-5"}. Games per cell: 18. Mock run: False. Spend: claude_sonnet $1.64.

Effects are differences in joint efficiency, in percentage points, averaged over models with equal weight. Interval: 95% percentile bootstrap, 5000 resamples. Smallest effect of interest: 10 points. Label rule: positive = interval excludes zero in the predicted direction; null = interval inside +/-10; otherwise inconclusive. 'supported' says whether the pre-registered prediction held, which for a null-predicted hypothesis (H3b, G3b) means the interval lies inside +/-10 (label null, or positive with a small difference).

## Hypotheses

| id | description | predicted | est | lo | hi | p_tost | label | supported | small | label_comprehension_only |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Infrastructure effect: C3 - C1 | C3 > C1 | 62.2 | 57.0 | 66.7 | 1.000 | positive | yes | False | positive |
| H2 | Claim only: C2 - C1 | either direction | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| H3a | Verification matters: C3 - C4 | C3 > C4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| H3b | Failed verification is discounted: C4 - C1 | C4 ~ C1 (null predicted) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| H4 | Agents vs humans, no infrastructure: A0 - humans | two-sided, no direction | 0.1 | -1.9 | 3.0 | 0.000 | null | no direction predicted | False | null |
| H4b | AI advantage vs humans: C3 - humans | C3 > humans | 32.3 | 31.0 | 33.7 | 1.000 | positive | yes | False | positive |
| G1 | Verified credentials: D3 - D1 | D3 > D1 | 27.4 | 11.1 | 43.3 | 0.985 | positive | yes | False | positive |
| G2 | Unsigned credential: D2 - D1 | either direction | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| G3a | Verification matters: D3 - D4 | D3 > D4 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| G3b | Failed verification is discounted: D4 - D1 | D4 ~ D1 (null predicted) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| G4 | Credentials improve discrimination: (fair - self-interested) gap in D3 minus D1 | gap larger in D3 | 71.1 | 61.5 | 80.7 | 1.000 | positive | yes | False | positive |

## AI advantage, in the role's two senses

- Versus agents without infrastructure: H1 (C3 - C1) in Experiment 1, G1 (D3 - D1) in Experiment 2.
- Versus humans: H4b (C3 - humans). The human baseline is 148 published studies that tripled the amount sent (with a valid mean share); it is a benchmark, not a randomised arm.
- Decomposition: H4 (A0 - humans) is what agents do differently from humans with no infrastructure; H1 is what the infrastructure adds. Both are reported so an agent effect is not credited to the infrastructure.

## Cells

| arm | model | games | aborted | malformed_outputs | mean_eff_pts | mean_sent | mean_sender_pay | mba_rate | exploit_rate | mean_return_share | mean_stated_share_pct | mean_promise_gap_pts | verify_rate | comprehension_ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | claude_sonnet | 18 | 0 | 0 | 67.8 | 5.17 | 11.50 | 1.00 | 0.00 | 0.43 | n/a | n/a | 0.00 | 1.00 |
| C1 | claude_sonnet | 18 | 0 | 0 | 37.8 | 0.67 | 10.39 | 0.17 | 0.00 | 0.54 | n/a | n/a | 0.00 | 1.00 |
| C3 | claude_sonnet | 18 | 0 | 0 | 100.0 | 10.00 | 13.50 | 1.00 | 0.00 | 0.45 | 45.0 | 0.00 | 1.00 | 1.00 |
| D1 | claude_sonnet | 18 | 0 | 0 | 39.3 | 0.89 | 10.28 | 0.17 | 0.06 | 0.38 | n/a | n/a | 0.00 | 1.00 |
| D3 | claude_sonnet | 18 | 0 | 0 | 66.7 | 5.00 | 12.50 | 0.50 | 0.00 | 0.50 | n/a | n/a | 0.50 | 1.00 |

## Verification (H5, G4)

| arm | n | verify_rate | mean_eff_verifiers | n_verifiers | mean_eff_non_verifiers | n_non_verifiers |
|---|---|---|---|---|---|---|
| C3 | 18 | 1.00 | 100.0 | 18 | n/a | 0 |
| D3 | 18 | 0.50 | 100.0 | 9 | 33.3 | 9 |

## Did senders tell fair from self-interested trustees? (descriptive)

| arm | sent_to_fair | sent_to_self_interested | gap | n_fair | n_self |
|---|---|---|---|---|---|
| C1 | 0.33 | 1.00 | -0.67 | 9 | 9 |
| C3 | 10.00 | 10.00 | 0.00 | 9 | 9 |
| D1 | 0.56 | 1.22 | -0.67 | 9 | 9 |
| D3 | 10.00 | 0.00 | 10.00 | 9 | 9 |

## Human baseline

| studies | mean_efficiency_pts | sd_across_studies |
|---|---|---|
| 148 | 67.7 | 8.3 |
