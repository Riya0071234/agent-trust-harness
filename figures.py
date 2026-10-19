"""figures.py - every chart and descriptive table in the write-up, rebuilt from the raw games.

Reads only results/<run>/games.jsonl. Writes CSV tables and PNG charts to results/analysis/figures/.
No API key and no human-baseline file are needed (the human mean, 67.7, is printed by analyze.py and
is only drawn here as a reference line).

Usage: python figures.py [--out results/analysis/figures]

Per-cell intervals are 95% percentile bootstrap intervals of the cell mean, 5,000 resamples, seed 7,
the same settings analyze.py uses for differences. The effects chart reads analyze.py's hypotheses.csv.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
ARMS = ["A0", "C1", "C2", "C3", "C4", "D1", "D2", "D3", "D4"]
HUMAN_MEAN = 67.7          # analyze.py, 148 studies (Johnson and Mislin 2011)
RESAMPLES, SEED = 5000, 7

# (label, run directory, buyer model, supplier model)
SETTINGS = [
    ("Haiku, self-play", "claude", "Haiku", "Haiku"),
    ("Luna, self-play", "openai", "Luna", "Luna"),
    ("Haiku buys from Luna", "cross_claude_buys", "Haiku", "Luna"),
    ("Luna buys from Haiku", "cross_openai_buys", "Luna", "Haiku"),
    ("Claude Sonnet 5.5, self-play", "stronger_claude_sonnet", "Sonnet", "Sonnet"),
    ("gpt-6.1-sol, self-play", "stronger_openai_sol", "gpt-6.1-sol", "gpt-6.1-sol"),
]
# analysis directory -> label, for the primary-effects chart
EFFECTS = [("selfplay", "Cheap models, self-play"), ("cross", "Cheap models across vendors"),
           ("stronger_sonnet", "Claude Sonnet 5.5, self-play"), ("stronger_sol", "gpt-6.1-sol, self-play")]
VOLUNTARY = {"C1", "C2", "C4", "D1", "D2", "D3", "D4"}     # arms where the supplier chooses the return


def load(run: str) -> list[dict]:
    return [g for g in (json.loads(l) for l in open(ROOT / "results" / run / "games.jsonl")) if not g.get("aborted")]


def boot_ci(x, rng) -> tuple[float, float]:
    x = np.asarray(x, float)
    if len(x) == 0:
        return float("nan"), float("nan")
    means = x[rng.integers(0, len(x), (RESAMPLES, len(x)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def write(path: Path, rows: list[dict]):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def tables(out: Path) -> dict:
    rng = np.random.default_rng(SEED)
    T = {k: [] for k in ("arm_means", "sent_distribution", "sent_by_type", "manipulation_check",
                         "comprehension", "verification", "measured_sd")}
    for label, run, buyer, supplier in SETTINGS:
        games = load(run)
        by_arm = {a: [g for g in games if g["game"]["arm"] == a] for a in ARMS}
        within = []
        for arm, gs in by_arm.items():
            if not gs:
                continue
            eff = [100 * g["outcome"]["efficiency"] for g in gs]
            sent = [g["outcome"]["sent"] for g in gs]
            lo, hi = boot_ci(eff, rng)
            sd = float(np.std(eff, ddof=1)) if len(eff) > 1 else 0.0
            within.append((len(eff), sd))
            T["arm_means"].append(dict(setting=label, arm=arm, games=len(gs), mean_eff=round(np.mean(eff), 2),
                                       ci_lo=round(lo, 2), ci_hi=round(hi, 2), sd_eff=round(sd, 2)))
            T["sent_distribution"].append(dict(setting=label, arm=arm, games=len(gs), sent_0=sent.count(0),
                                               sent_1_to_9=sum(1 for s in sent if 0 < s < 10), sent_10=sent.count(10)))
            row = dict(setting=label, arm=arm)
            for t in ("fair", "self_interested"):
                s = [g["outcome"]["sent"] for g in gs if g["game"]["trustee_type"] == t]
                row[f"mean_sent_{t}"] = round(float(np.mean(s)), 2) if s else ""
            T["sent_by_type"].append(row)
            if arm in ("C3", "C4", "D3", "D4"):
                v = [g for g in gs if g["outcome"]["verify_called"]]
                nv = [g for g in gs if not g["outcome"]["verify_called"]]
                T["verification"].append(dict(setting=label, arm=arm, verify_rate=round(len(v) / len(gs), 3),
                                              mean_eff_verifiers=round(np.mean([100 * g["outcome"]["efficiency"] for g in v]), 1) if v else "",
                                              mean_eff_non_verifiers=round(np.mean([100 * g["outcome"]["efficiency"] for g in nv]), 1) if nv else "",
                                              non_verifiers=len(nv)))
        n = sum(k for k, _ in within)
        pooled = np.sqrt(sum((k - 1) * s * s for k, s in within) / max(1, n - len(within)))
        T["measured_sd"].append(dict(setting=label, arms=len(within), pooled_within_arm_sd=round(float(pooled), 1),
                                     max_arm_sd=round(max(s for _, s in within), 1),
                                     arms_with_zero_sd=sum(1 for _, s in within if s == 0)))
        # manipulation check: does the self-interested instruction lower what suppliers return?
        for t in ("fair", "self_interested"):
            share = [g["outcome"]["returned"] / (3 * g["outcome"]["sent"]) for g in games
                     if g["game"]["arm"] in VOLUNTARY and g["game"]["trustee_type"] == t and g["outcome"]["sent"] > 0]
            lo, hi = boot_ci(share, rng)
            T["manipulation_check"].append(dict(setting=label, supplier=supplier, supplier_type=t,
                                                games_with_prepayment=len(share),
                                                mean_return_share=round(float(np.mean(share)), 3) if share else "",
                                                ci_lo=round(lo, 3) if share else "", ci_hi=round(hi, 3) if share else ""))
        c2 = [g for g in games if g["game"]["arm"] == "C2" and g["outcome"]["sent"] > 0
              and g["outcome"]["promise_gap_points"] is not None]
        T["manipulation_check"].append(dict(setting=label, supplier=supplier, supplier_type="unsigned promises kept (C2)",
                                            games_with_prepayment=len(c2),
                                            mean_return_share=round(sum(abs(g["outcome"]["promise_gap_points"]) < 1e-9 for g in c2) / len(c2), 3) if c2 else "",
                                            ci_lo="", ci_hi=""))
        comp = [g["outcome"]["comprehension_ok"] for g in games]
        T["comprehension"].append(dict(setting=label, games=len(games), both_roles_passed=round(sum(comp) / len(comp), 3),
                                       buyer_passed=round(float(np.mean([g["comprehension"]["sender"]["correct"] for g in games])), 3),
                                       supplier_passed=round(float(np.mean([g["comprehension"]["trustee"]["correct"] for g in games])), 3)))
    for k, rows in T.items():
        write(out / f"{k}.csv", rows)
    return T


def charts(out: Path, T: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = ["#2f6fdb", "#e0703c", "#1fa37a", "#123a6b", "#8a5cc2", "#c94f7c"]

    # 1. mean efficiency by arm, cheap-model settings
    fig, ax = plt.subplots(figsize=(10, 4.6))
    cheap = [s for s in SETTINGS[:4]]
    for i, (label, *_ ) in enumerate(cheap):
        rows = [r for r in T["arm_means"] if r["setting"] == label]
        x = np.array([ARMS.index(r["arm"]) for r in rows]) + (i - 1.5) * 0.13
        m = np.array([r["mean_eff"] for r in rows])
        err = np.array([[r["mean_eff"] - r["ci_lo"] for r in rows], [r["ci_hi"] - r["mean_eff"] for r in rows]])
        ax.errorbar(x, m, yerr=err, fmt="o", color=colors[i], label=label, capsize=0, ms=5)
    ax.axhline(100 / 3, ls="--", color="grey", lw=1)
    ax.axhline(HUMAN_MEAN, ls="--", color="grey", lw=1)
    ax.text(8.45, 100 / 3 + 1, "nothing sent 33.3", fontsize=8, color="grey", ha="right")
    ax.text(8.45, HUMAN_MEAN + 1, f"human studies {HUMAN_MEAN}", fontsize=8, color="grey", ha="right")
    ax.set_xticks(range(len(ARMS)), ARMS)
    ax.set_ylim(20, 103)
    ax.set_ylabel("Mean efficiency (0 to 100)")
    ax.set_title("A valid signature lifts efficiency in every pairing; a corrupted one does not", loc="left")
    ax.legend(ncol=4, fontsize=8, frameon=False, loc="upper left", bbox_to_anchor=(0, -0.08))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "fig1_efficiency_by_arm.png", dpi=150)
    plt.close(fig)

    # 2. primary effects (H1, G1) from analyze.py
    rows = []
    for d, label in EFFECTS:
        h = {r["id"]: r for r in csv.DictReader(open(ROOT / "results" / "analysis" / d / "hypotheses.csv"))}
        for i, (hid, name) in enumerate((("H1", "Signed commitment vs free text (H1)"), ("G1", "Signed credential vs free text (G1)"))):
            rows.append((label, name, i, float(h[hid]["est"]), float(h[hid]["lo"]), float(h[hid]["hi"])))
    fig, ax = plt.subplots(figsize=(10, 4))
    labels = [l for _, l in EFFECTS]
    for label, name, i, est, lo, hi in rows:
        y = len(labels) - 1 - labels.index(label) + (0.15 if i == 0 else -0.15)
        ax.plot([lo, hi], [y, y], color=colors[i], lw=3, alpha=0.5)
        ax.plot(est, y, "o", color=colors[i], label=name if label == labels[0] else None)
        ax.text(hi + 1, y, f"+{est:.1f}", va="center", fontsize=8)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(range(len(labels)), labels[::-1])
    ax.set_xlabel("Efficiency points gained over the free-text arm (95% interval)")
    ax.set_title("A signed commitment or credential beat free text in every setting", loc="left")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "fig2_primary_effects.png", dpi=150)
    plt.close(fig)

    # 3. distribution of amounts sent, every game
    fig, axes = plt.subplots(3, 2, figsize=(10, 8.5))
    for ax, (label, *_ ) in zip(axes.flat, SETTINGS):
        rows = [r for r in T["sent_distribution"] if r["setting"] == label]
        x = np.arange(len(rows))
        b0 = np.array([r["sent_0"] / r["games"] for r in rows])
        b1 = np.array([r["sent_1_to_9"] / r["games"] for r in rows])
        b2 = np.array([r["sent_10"] / r["games"] for r in rows])
        ax.bar(x, b0, color="#d9d7d0", label="0 points")
        ax.bar(x, b1, bottom=b0, color="#9ec0ef", label="1 to 9 points")
        ax.bar(x, b2, bottom=b0 + b1, color="#2f6fdb", label="10 points")
        ax.set_xticks(x, [r["arm"] for r in rows], fontsize=8)
        ax.set_yticks([0, 1], ["0", "100%"], fontsize=8)
        ax.set_title(label, fontsize=9, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
    axes.flat[0].legend(fontsize=7, frameon=False, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.12))
    fig.suptitle("With a valid signature buyers send all or nothing; hedging appears only without one", x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(out / "fig3_amounts_sent.png", dpi=150)
    plt.close(fig)

    # 4. manipulation check
    rows = [r for r in T["manipulation_check"] if r["supplier_type"] in ("fair", "self_interested") and r["games_with_prepayment"]]
    fig, ax = plt.subplots(figsize=(10, 4))
    labels = list(dict.fromkeys(r["setting"] for r in rows))
    for r in rows:
        i = 0 if r["supplier_type"] == "fair" else 1
        y = len(labels) - 1 - labels.index(r["setting"]) + (0.15 if i == 0 else -0.15)
        ax.plot([r["ci_lo"], r["ci_hi"]], [y, y], color=colors[i], lw=3, alpha=0.5)
        ax.plot(r["mean_return_share"], y, "o", color=colors[i])
        ax.text(r["ci_hi"] + 0.01, y, f'n={r["games_with_prepayment"]}', va="center", fontsize=7)
    ax.plot([], [], "o", color=colors[0], label="Fair supplier")
    ax.plot([], [], "o", color=colors[1], label="Self-interested supplier")
    ax.axvline(1 / 3, ls="--", color="grey", lw=1)
    ax.text(1 / 3 + 0.01, -0.45, "buyer breaks even (1/3)", fontsize=8, color="grey")
    ax.set_yticks(range(len(labels)), labels[::-1], fontsize=8)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(-0.6, len(labels) - 0.5)
    ax.set_xlabel("Share of the tripled amount returned, voluntary-return arms, games with a prepayment")
    ax.set_title("Self-interested suppliers returned almost as much as fair ones", loc="left")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "fig4_manipulation_check.png", dpi=150)
    plt.close(fig)


def main(out: str):
    o = Path(out)
    o.mkdir(parents=True, exist_ok=True)
    T = tables(o)
    charts(o, T)
    for r in T["manipulation_check"]:
        print(r)
    for r in T["measured_sd"] + T["comprehension"]:
        print(r)
    print(f"Wrote tables and charts to {o}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results" / "analysis" / "figures"))
    main(ap.parse_args().out)
