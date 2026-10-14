"""analyze.py - the pre-registered analysis (see PREREG.md) and the labelled results table.

Usage: python analyze.py results/pilot

Writes <run>/results.md, <run>/hypotheses.csv and <run>/cells.csv. Every hypothesis gets an
effect size, a 95% bootstrap interval, TOST p-values against +/- the smallest effect of
interest, and a label: positive, null or inconclusive. Nothing is dropped for being null.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


# --------------------------------------------------------------------------- loading
def load_games(run_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    recs = [json.loads(l) for l in (run_dir / "games.jsonl").read_text().splitlines() if l.strip()]
    rows, all_rows = [], []
    for r in recs:
        g = r["game"]
        base = {"exp": g["exp"], "arm": g["arm"], "model": g["model_label"], "idx": g["idx"],
                "ptype": g["trustee_type"], "aborted": bool(r["aborted"]), "malformed": r["malformed"]}
        all_rows.append(base)
        o = r["outcome"]
        if o is None:
            continue
        rows.append({**base, "eff": o["efficiency"] * 100, "sent": o["sent"], "returned": o["returned"],
                     "mba": o["mutually_beneficial"], "exploit": o["exploitation"],
                     "return_share": o["return_share"], "verify_called": o["verify_called"],
                     "verify_result": o["verify_result"], "comp_ok": o["comprehension_ok"],
                     "promise_gap": o["promise_gap_points"], "stated_share": o["stated_share_percent"]})
    return pd.DataFrame(rows), pd.DataFrame(all_rows)


def human_efficiency(csv_path: Path) -> np.ndarray:
    """Study-level efficiency (points) from published trust-game means, tripled studies only."""
    if not Path(csv_path).exists():
        sys.exit(f"Human baseline not found at {csv_path}. See data/README.md for where to get it.")
    d = pd.read_csv(csv_path)
    d = d[d["rate_of_return"] == 3].dropna(subset=["ave_per_Sent"])
    p = d["ave_per_Sent"].to_numpy() / 100.0
    return (1 + 2 * p) / 3 * 100


# --------------------------------------------------------------------------- bootstrap
def groups(df: pd.DataFrame, arm: str, query: str | None = None) -> dict[str, np.ndarray]:
    d = df[df["arm"] == arm]
    if query:
        d = d.query(query)
    return {m: g["eff"].to_numpy() for m, g in d.groupby("model") if len(g) > 0}


def _pooled_boot(ga: dict, gb: dict, rng, B: int):
    """Mean over models of (mean(a) - mean(b)); each model-cell is resampled separately."""
    models = [m for m in ga if m in gb]
    if not models:
        return None, None
    est = np.mean([ga[m].mean() - gb[m].mean() for m in models])
    boots = np.zeros(B)
    for m in models:
        a, b = ga[m], gb[m]
        boots += a[rng.integers(0, len(a), (B, len(a)))].mean(1) - b[rng.integers(0, len(b), (B, len(b)))].mean(1)
    return est, boots / len(models)


def _vs_humans_boot(ga: dict, hum: np.ndarray, rng, B: int):
    models = list(ga)
    if not models:
        return None, None
    est = np.mean([ga[m].mean() for m in models]) - hum.mean()
    agent = np.zeros(B)
    for m in models:
        a = ga[m]
        agent += a[rng.integers(0, len(a), (B, len(a)))].mean(1)
    boots = agent / len(models) - hum[rng.integers(0, len(hum), (B, len(hum)))].mean(1)
    return est, boots


def label(est, boots, direction: int, delta: float, ci_level: float):
    """positive: interval excludes zero in the predicted direction (either, if direction == 0).
    null: interval sits inside +/- delta. Otherwise inconclusive."""
    if est is None:
        return {"label": "n/a", "est": None, "lo": None, "hi": None, "p_tost": None, "small": None}
    a = (1 - ci_level) / 2
    lo, hi = np.quantile(boots, [a, 1 - a])
    if direction > 0:
        pos = lo > 0
    elif direction < 0:
        pos = hi < 0
    else:
        pos = lo > 0 or hi < 0
    nul = lo > -delta and hi < delta
    p_tost = max(float(np.mean(boots <= -delta)), float(np.mean(boots >= delta)))
    lab = "positive" if pos else ("null" if nul else "inconclusive")
    return {"label": lab, "est": float(est), "lo": float(lo), "hi": float(hi), "p_tost": p_tost,
            "small": bool(pos and nul)}


# --------------------------------------------------------------------------- hypotheses
HYPOTHESES = [
    # id, description, predicted, kind, args, direction
    ("H1", "Infrastructure effect: C3 - C1", "C3 > C1", "pair", ("C3", "C1"), +1, "dir"),
    ("H2", "Claim only: C2 - C1", "either direction", "pair", ("C2", "C1"), 0, "none"),
    ("H3a", "Verification matters: C3 - C4", "C3 > C4", "pair", ("C3", "C4"), +1, "dir"),
    ("H3b", "Failed verification is discounted: C4 - C1", "C4 ~ C1 (null predicted)", "pair", ("C4", "C1"), 0, "null"),
    ("H4", "Agents vs humans, no infrastructure: A0 - humans", "two-sided, no direction", "human", ("A0",), 0, "none"),
    ("H4b", "AI advantage vs humans: C3 - humans", "C3 > humans", "human", ("C3",), +1, "dir"),
    ("G1", "Verified credentials: D3 - D1", "D3 > D1", "pair", ("D3", "D1"), +1, "dir"),
    ("G2", "Unsigned credential: D2 - D1", "either direction", "pair", ("D2", "D1"), 0, "none"),
    ("G3a", "Verification matters: D3 - D4", "D3 > D4", "pair", ("D3", "D4"), +1, "dir"),
    ("G3b", "Failed verification is discounted: D4 - D1", "D4 ~ D1 (null predicted)", "pair", ("D4", "D1"), 0, "null"),
]


def supported(res: dict, ptype: str, direction: int) -> str:
    """Whether the data support the pre-registered prediction, separate from the label."""
    if res["label"] == "n/a":
        return "n/a"
    if ptype == "none":
        return "no direction predicted"
    if ptype == "null":
        return {"null": "yes", "positive": "no (differs)", "inconclusive": "not determined"}[res["label"]]
    if res["label"] == "positive":
        return "yes"
    if (direction > 0 and res["hi"] < 0) or (direction < 0 and res["lo"] > 0):
        return "no (opposite direction)"
    if res["label"] == "null":
        return "no (no effect beyond +/-smallest effect)"
    return "not determined"


def run_hypotheses(df, hum, cfg, query=None):
    a = cfg["analysis"]
    rng = np.random.default_rng(a["bootstrap_seed"])
    B, delta, ci = a["bootstrap_resamples"], a["smallest_effect_points"], a["ci_level"]
    out = []
    for hid, desc, pred, kind, args, direction, ptype in HYPOTHESES:
        if kind == "pair":
            est, boots = _pooled_boot(groups(df, args[0], query), groups(df, args[1], query), rng, B)
        else:
            est, boots = _vs_humans_boot(groups(df, args[0], query), hum, rng, B)
        r = label(est, boots, direction, delta, ci)
        r.update({"id": hid, "description": desc, "predicted": pred, "supported": supported(r, ptype, direction)})
        out.append(r)
    return out


def verification_analysis(df, cfg):
    """H5 / G4: how often senders verify, and whether verifying changes the outcome."""
    rows = []
    for arm in ("C3", "C4", "D3", "D4"):
        d = df[df["arm"] == arm]
        if len(d):
            rows.append({"arm": arm, "n": len(d), "verify_rate": d["verify_called"].mean(),
                         "mean_eff_verifiers": d[d["verify_called"]]["eff"].mean() if d["verify_called"].any() else np.nan,
                         "n_verifiers": int(d["verify_called"].sum()),
                         "mean_eff_non_verifiers": d[~d["verify_called"]]["eff"].mean() if (~d["verify_called"]).any() else np.nan,
                         "n_non_verifiers": int((~d["verify_called"]).sum())})
    return pd.DataFrame(rows)


def discrimination(df):
    """Mean points prepaid to fair minus to self-interested trustees, per arm (G4, descriptive)."""
    rows = []
    for arm, d in df[df["ptype"] != "none"].groupby("arm"):
        f, s = d[d["ptype"] == "fair"]["sent"], d[d["ptype"] == "self_interested"]["sent"]
        if len(f) and len(s):
            rows.append({"arm": arm, "sent_to_fair": f.mean(), "sent_to_self_interested": s.mean(),
                         "gap": f.mean() - s.mean(), "n_fair": len(f), "n_self": len(s)})
    return pd.DataFrame(rows)


def cell_table(df, all_df):
    rows = []
    for (arm, model), d in df.groupby(["arm", "model"]):
        tot = all_df[(all_df["arm"] == arm) & (all_df["model"] == model)]
        rows.append({"arm": arm, "model": model, "games": len(tot), "aborted": int(tot["aborted"].sum()),
                     "malformed_outputs": int(tot["malformed"].sum()),
                     "mean_eff_pts": d["eff"].mean(), "mean_sent": d["sent"].mean(),
                     "mba_rate": d["mba"].mean(), "exploit_rate": d["exploit"].mean(),
                     "mean_return_share": d["return_share"].mean(),
                     "verify_rate": d["verify_called"].mean(), "comprehension_ok": d["comp_ok"].mean()})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- report
def fmt(x, nd=1):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def md_table(df: pd.DataFrame, floats: dict | None = None) -> str:
    floats = floats or {}
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append(fmt(v, floats.get(c, 2)))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(run_dir: str):
    run = Path(run_dir)
    manifest = json.loads((run / "manifest.json").read_text())
    cfg = manifest["config"]
    root = Path(__file__).parent
    df, all_df = load_games(run)
    hum = human_efficiency(root / cfg["analysis"]["human_baseline_csv"])

    primary = pd.DataFrame(run_hypotheses(df, hum, cfg))
    secondary = pd.DataFrame(run_hypotheses(df[df["comp_ok"]], hum, cfg, query=None)) if df["comp_ok"].any() else None
    cells = cell_table(df, all_df)

    h = primary[["id", "description", "predicted", "est", "lo", "hi", "p_tost", "label", "supported", "small"]].copy()
    if secondary is not None:
        h["label_comprehension_only"] = secondary["label"].to_numpy()
    h.to_csv(run / "hypotheses.csv", index=False)
    cells.to_csv(run / "cells.csv", index=False)

    delta = cfg["analysis"]["smallest_effect_points"]
    lines = [f"# Results: {run.name}", "",
             f"Run started {manifest['run_started_utc']}. Models: {json.dumps(manifest['model_ids'])}. "
             f"Games per cell: {manifest['games_per_cell']}. Mock run: {manifest['mock']}. "
             f"Spend: ${manifest.get('spend_usd', 'n/a')}.", ""]
    if manifest["mock"]:
        lines += ["**This was a mock run with a scripted stand-in. None of these numbers describe a model.**", ""]
    lines += [f"Effects are differences in joint efficiency, in percentage points, averaged over models with equal weight. "
              f"Interval: {int(cfg['analysis']['ci_level'] * 100)}% percentile bootstrap, {cfg['analysis']['bootstrap_resamples']} resamples. "
              f"Smallest effect of interest: {delta} points. Label rule: positive = interval excludes zero in the predicted "
              f"direction; null = interval inside +/-{delta}; otherwise inconclusive. 'supported' says whether the pre-registered "
              f"prediction held, which for a null-predicted hypothesis (H3b, G3b) means the label is null.", "",
              "## Hypotheses", "", md_table(h, {"est": 1, "lo": 1, "hi": 1, "p_tost": 3}), ""]
    lines += ["## AI advantage, in the role's two senses", "",
              "- Versus agents without infrastructure: H1 (C3 - C1) in Experiment 1, G1 (D3 - D1) in Experiment 2.",
              "- Versus humans: H4b (C3 - humans). The human baseline is 150 published studies that tripled the amount sent; "
              "it is a benchmark, not a randomised arm.",
              "- Decomposition: H4 (A0 - humans) is what agents do differently from humans with no infrastructure; H1 is what the "
              "infrastructure adds. Both are reported so an agent effect is not credited to the infrastructure.", ""]
    lines += ["## Cells", "", md_table(cells, {"mean_eff_pts": 1, "mean_sent": 2, "mba_rate": 2, "exploit_rate": 2,
                                                  "mean_return_share": 2, "verify_rate": 2, "comprehension_ok": 2}), ""]
    v = verification_analysis(df, cfg)
    if len(v):
        lines += ["## Verification (H5, G4)", "", md_table(v, {"verify_rate": 2, "mean_eff_verifiers": 1, "mean_eff_non_verifiers": 1}), ""]
    dsc = discrimination(df)
    if len(dsc):
        lines += ["## Did senders tell fair from self-interested trustees? (descriptive)", "",
                  md_table(dsc, {"sent_to_fair": 2, "sent_to_self_interested": 2, "gap": 2}), ""]
    human = pd.DataFrame([{"studies": len(hum), "mean_efficiency_pts": hum.mean(), "sd_across_studies": hum.std(ddof=1)}])
    lines += ["## Human baseline", "", md_table(human, {"mean_efficiency_pts": 1, "sd_across_studies": 1}), ""]
    (run / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
