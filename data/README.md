# Human baseline

`analyze.py` compares agents with published human trust-game behaviour. It expects the study-level table at
`data/human_baseline_johnson_mislin_2011.csv` (columns `paper_no, year, sender_endowment, ave_per_Sent, ave_per_returned, rate_of_return`).

That table comes from the meta-analysis of 161 published trust-game studies by Johnson and Mislin (2011), "Trust games: A meta-analysis",
Journal of Economic Psychology 32(5), and is distributed in the replication package of Johnson and Obradovich, "Measuring an artificial
intelligence language model's trust in humans using machine incentives" (file `johnson_mislin_appendix_trust_game_data.csv`).
The file is not redistributed here because the package does not state a licence. Download it from the authors' replication package
and place it at the path above.

Only the studies with `rate_of_return == 3` (the amount sent was tripled) are used, to match this game: 150 in the table, of which one has no mean share and one reports a mean share of 160% (impossible), so `analyze.py` uses 148. See the deviations log in `PREREG.md`.
