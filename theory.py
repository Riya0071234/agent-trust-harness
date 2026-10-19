"""theory.py - the game-theory benchmark for each arm, derived by backward induction.

This is theory under stated assumptions, not data. It is printed next to the observed mean efficiency
so the reader can see how far each model is from what a rational buyer facing a rational supplier would do.

Assumptions (all stated in the output):
  * Points are risk-neutral payoffs. Efficiency = (10 + 2*sent)/30, so it depends only on what the buyer sends.
  * A self-interested supplier returns nothing whenever nothing forces it to (return is its last move).
  * A fair supplier returns the share FAIR_SHARE of the tripled amount (default 1/2 of 3*sent, i.e. 1.5 x sent,
    "an outcome that benefits both sides"). Any share above 1/3 leaves the buyer better off than keeping the point.
  * The buyer knows the prior: half of suppliers are fair (PRIOR_FAIR = 0.5), as the prompts state.
  * Cheap talk and unsigned claims are free for a self-interested supplier to copy, so they carry no information.
Usage: python theory.py [--cells results/combined/cells.csv]
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict

PRIOR_FAIR = 0.5
FAIR_SHARE = 0.5          # share of 3*sent a fair supplier returns
ENDOW, MULT = 10, 3


def efficiency(sent: float) -> float:
    return 100 * (ENDOW + (MULT - 1) * sent) / (ENDOW * MULT)


def best_send(expected_return_per_point: float) -> int:
    """Sending one point costs 1 and returns expected_return_per_point; risk-neutral, so all or nothing."""
    return ENDOW if expected_return_per_point > 1 else 0


def predictions() -> list[dict]:
    pooled = best_send(PRIOR_FAIR * MULT * FAIR_SHARE)          # cannot tell types apart
    to_fair = best_send(MULT * FAIR_SHARE)                      # buyer is sure the supplier is fair
    to_selfish = best_send(0.0)                                 # buyer is sure it is self-interested
    committed = best_send(MULT * (1 / 3 + 0.01))                # enforced share just above 1/3 already pays
    rows = [
        ("A0", "no types, no pre-play", pooled, "Only a self-interested supplier exists; it returns nothing, so the buyer sends nothing."),
        ("C1", "free-text message", pooled, "Cheap talk: a self-interested supplier writes the same promise, so it carries no information (babbling equilibrium)."),
        ("C2", "unsigned rule", pooled, "An unsigned rule binds nobody, so it is cheap talk."),
        ("C3", "escrow-signed commitment", committed, "The game pays the committed share; the cheapest commitment that induces full sending is just above 1/3, so both types commit and the buyer sends everything."),
        ("C4", "commitment, signature corrupted", pooled, "Nothing is enforced and the buyer can see the failure, so it is cheap talk."),
        ("D1", "free-text message", pooled, "As C1."),
        ("D2", "unsigned credential", pooled, "A self-interested supplier claims 'fair' for free."),
        ("D4", "credential, signature corrupted", pooled, "No credential verifies, so none can be trusted."),
    ]
    out = [{"arm": a, "what": w, "sent": s, "eff": efficiency(s), "why": y} for a, w, s, y in rows]
    # D3 is a mixture: verified-fair suppliers get everything, the rest get nothing.
    sent_d3 = PRIOR_FAIR * to_fair + (1 - PRIOR_FAIR) * to_selfish
    out.insert(7, {"arm": "D3", "what": "issuer-signed credential", "sent": sent_d3,
                   "eff": PRIOR_FAIR * efficiency(to_fair) + (1 - PRIOR_FAIR) * efficiency(to_selfish),
                   "why": "Only a true 'fair' credential can carry a valid signature, so the buyer sends everything to verified-fair "
                          "suppliers and nothing to the rest (average over the 50/50 mix of types)."})
    return out


def render(cells_csv: str | None) -> str:
    obs = defaultdict(dict)
    if cells_csv:
        for r in csv.DictReader(open(cells_csv)):
            obs[r["arm"]][r["model"]] = float(r["mean_eff_pts"])
    models = sorted({m for v in obs.values() for m in v})
    head = ["arm", "what the arm changes", "theory: points sent", "theory: efficiency (pts)"] + [f"observed: {m}" for m in models]
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in predictions():
        lines.append("| " + " | ".join([r["arm"], r["what"], f"{r['sent']:.1f}", f"{r['eff']:.1f}"]
                                         + [f"{obs[r['arm']][m]:.1f}" if m in obs[r["arm"]] else "-" for m in models]) + " |")
    notes = ["", "Assumptions: risk-neutral points; a self-interested supplier returns nothing when nothing forces it; a fair supplier returns "
             f"{FAIR_SHARE:.0%} of the tripled amount; the buyer knows half of suppliers are fair; efficiency = (10 + 2*sent)/30.",
             "Reading: the theory says only enforcement (C3) and verified types (D3) can lift efficiency above 33.3. Observed values above "
             "33.3 in the other arms are trust that theory does not predict; observed values below the theory in C3 or D3 are "
             "shortfalls from the rational benchmark.", "Why: " + " ".join(f"{r['arm']}: {r['why']}" for r in predictions())]
    return "\n".join(lines + notes)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", default=None, help="cells.csv from analyze.py to put observed values next to the theory")
    print(render(ap.parse_args().cells))
