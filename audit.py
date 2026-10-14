"""audit.py - recompute every metric from the raw transcripts alone.

It does not import engine.py. For each game it re-derives, from the logged tool calls and the
signatures, what was sent, what was returned, whether the commitment or credential verifies,
the payoffs, efficiency and the comprehension answers, and compares them with what run.py
stored. It then recomputes the per-cell mean efficiency and compares it with cells.csv.

Usage: python audit.py results/claude results/openai [--cells results/combined]
       (exit code 1 if anything differs; cells.csv is read from --cells, default: the run dir or results/combined)
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def sig_ok(pub_hex, payload, sig_hex) -> bool:
    if not sig_hex or payload is None:
        return False
    try:
        msg = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex)).verify(bytes.fromhex(sig_hex), msg)
        return True
    except (InvalidSignature, ValueError):
        return False


def last_tool_input(calls, role, phase, name):
    cs = [c for c in calls if c["role"] == role and c["phase"] == phase]
    if not cs:
        return None
    for b in cs[-1]["response"]:
        if b.get("type") == "tool_use" and b["name"] == name:
            return b["input"]
    return None


def count_tool_uses(calls, role, phase, names):
    n = 0
    for c in calls:
        if c["role"] == role and c["phase"] == phase:
            n += sum(1 for b in c["response"] if b.get("type") == "tool_use" and b["name"] in names)
    return n


def audit_game(r):
    errs = []
    if r["aborted"] or r["outcome"] is None:
        return None, errs
    calls, o, pre, pk = r["calls"], r["outcome"], r["pre_play"], r["public_key"]

    s_in = last_tool_input(calls, "sender", "decide", "submit_transfer")
    sent = s_in["amount"] if s_in else None
    if sent is None or not (0 <= sent <= 10):
        errs.append(f"sent not recoverable or out of range: {sent}")
        return None, errs

    # what is returned
    if r["return"]["source"] == "escrow_auto":
        share = pre["payload"]["share_percent"]
        valid = sig_ok(pk, pre["payload"], pre["signature"])
        if not valid:
            errs.append("escrow paid automatically on a commitment whose signature does not verify")
        returned = (3 * sent * share + 50) // 100
    elif r["return"]["source"] == "none":
        returned = 0
        if sent != 0:
            errs.append("return source 'none' but sent > 0")
    else:
        t_in = last_tool_input(calls, "trustee", "return", "submit_return")
        returned = t_in["amount"] if t_in else None
    if returned is None or not (0 <= returned <= 3 * sent):
        errs.append(f"returned not recoverable or out of range: {returned}")
        return None, errs

    sender_pay, trustee_pay = 10 - sent + returned, 3 * sent - returned
    eff = (10 + 2 * sent) / 30

    # verification, recomputed from the signature itself
    n_verify = count_tool_uses(calls, "sender", "decide", {"verify_commitment", "verify_credential"})
    if n_verify != len(r["sender"]["verify_calls"]):
        errs.append(f"verify call count {n_verify} != stored {len(r['sender']['verify_calls'])}")
    if r["sender"]["verify_calls"]:
        if pre["kind"] == "commitment":
            truth = sig_ok(pk, pre["payload"], pre["signature"])
        elif pre["kind"] == "credential" and pre["claimed_type"] != "none":
            truth = sig_ok(pk, pre["payload"], pre.get("signature"))
        else:
            truth = None
        if r["sender"]["verify_calls"][-1]["result"] != truth:
            errs.append(f"verify result {r['sender']['verify_calls'][-1]['result']} != recomputed {truth}")

    # comprehension
    comp_ok = True
    for role in ("sender", "trustee"):
        a = last_tool_input(calls, role, "check", "answer_checks")
        ok = bool(a and a["q1"] == 12 and a["q2"] == 11)
        if r["comprehension"][role]["correct"] != ok:
            errs.append(f"{role} comprehension flag differs")
        comp_ok = comp_ok and ok

    checks = {"sent": sent, "returned": returned, "sender_pay": sender_pay, "trustee_pay": trustee_pay,
              "efficiency": eff, "mutually_beneficial": sent > 0 and returned >= sent,
              "exploitation": sent > 0 and returned < sent, "verify_called": n_verify > 0,
              "comprehension_ok": comp_ok}
    for k, v in checks.items():
        if o[k] != v and not (isinstance(v, float) and abs(o[k] - v) < 1e-12):
            errs.append(f"{k}: stored {o[k]!r} != recomputed {v!r}")
    return {"eff": eff * 100}, errs


def main(run_dirs: list[str], cells_dir: str | None = None) -> int:
    runs = [Path(d) for d in run_dirs]
    recs = [json.loads(l) for d in runs for l in (d / "games.jsonl").read_text().splitlines() if l.strip()]
    run = Path(cells_dir) if cells_dir else (runs[0] if len(runs) == 1 else Path("results/combined"))
    bad, skipped, cell = 0, 0, defaultdict(list)
    for r in recs:
        res, errs = audit_game(r)
        if res is None and not errs:
            skipped += 1
            continue
        if errs:
            bad += 1
            print(f"MISMATCH {r['game']['game_id']}: " + "; ".join(errs))
        if res:
            cell[(r["game"]["arm"], r["game"]["model_label"])].append(res["eff"])
    # compare per-cell means with cells.csv if the analysis has been run
    cells_csv = run / "cells.csv"
    diffs = 0
    if cells_csv.exists():
        for row in csv.DictReader(cells_csv.read_text().splitlines()):
            vals = cell.get((row["arm"], row["model"]), [])
            mean = sum(vals) / len(vals) if vals else float("nan")
            if abs(mean - float(row["mean_eff_pts"])) > 1e-6:
                diffs += 1
                print(f"CELL MISMATCH {row['arm']}/{row['model']}: cells.csv {row['mean_eff_pts']} vs audit {mean:.6f}")
    total = len(recs)
    print(f"Audited {total} games ({skipped} aborted, skipped). Game mismatches: {bad}. Cell-mean mismatches: {diffs}.")
    print("AUDIT PASS" if bad == 0 and diffs == 0 else "AUDIT FAIL")
    return 0 if bad == 0 and diffs == 0 else 1


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--cells", default=None)
    a = ap.parse_args()
    sys.exit(main(a.run_dirs, a.cells))
