"""Tests for the checks added in the pre-run review: human-baseline cleaning, the rule for null
predictions, stated-versus-actual return, cumulative spend, resume safety, and the audit's arm checks."""
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from analyze import human_efficiency, supported
from agents import Budget
from run import code_hashes, restore_spend, resume_problems

ROOT = Path(__file__).resolve().parent.parent
HAVE_BASELINE = (ROOT / "data" / "human_baseline_johnson_mislin_2011.csv").exists()


def sh(*args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)


def mock_run(tmp_path, n=4):
    out = tmp_path / "mock"
    r = sh("run.py", "--mock", "--out", str(out), "--games-per-cell", str(n))
    assert r.returncode == 0, r.stderr
    return out


def read(out):
    return [json.loads(l) for l in (out / "games.jsonl").read_text().splitlines()]


def write(out, recs):
    (out / "games.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")


# ------------------------------------------------------------------ human baseline
def test_human_baseline_drops_impossible_and_missing_shares(tmp_path):
    p = tmp_path / "h.csv"
    pd.DataFrame({"rate_of_return": [3, 3, 3, 3, 2],
                  "ave_per_Sent": [50.0, 160.0, None, 100.0, 40.0]}).to_csv(p, index=False)
    eff = human_efficiency(p)
    assert len(eff) == 2                                    # 160 (impossible) and NaN dropped; non-tripled study ignored
    assert sorted(eff.round(6)) == [round((1 + 2 * 0.5) / 3 * 100, 6), 100.0]


@pytest.mark.skipif(not HAVE_BASELINE, reason="human baseline file is not shipped in git")
def test_real_baseline_has_148_studies_all_valid():
    eff = human_efficiency(ROOT / "data" / "human_baseline_johnson_mislin_2011.csv")
    assert len(eff) == 148 and eff.max() <= 100


# ------------------------------------------------------------------ null predictions
def test_null_prediction_is_supported_by_equivalence():
    assert supported({"label": "null", "small": False, "lo": -3, "hi": 4}, "null", 0) == "yes"
    # interval excludes zero but sits inside +/-delta: equivalent, so the null prediction holds
    assert supported({"label": "positive", "small": True, "lo": 1, "hi": 5}, "null", 0).startswith("yes")
    # interval excludes zero and reaches beyond delta: a real difference
    assert supported({"label": "positive", "small": False, "lo": 4, "hi": 15}, "null", 0) == "no (differs)"
    assert supported({"label": "inconclusive", "small": False, "lo": -12, "hi": 8}, "null", 0) == "not determined"


# ------------------------------------------------------------------ stated versus actual return
def test_cells_report_stated_share_and_promise_gap(tmp_path):
    if not HAVE_BASELINE:
        pytest.skip("human baseline file is not shipped in git")
    out = mock_run(tmp_path, 6)
    assert sh("analyze.py", str(out)).returncode == 0
    cells = pd.read_csv(out / "cells.csv")
    assert {"mean_stated_share_pct", "mean_promise_gap_pts"} <= set(cells.columns)
    c3 = cells[cells["arm"] == "C3"]
    assert (c3["mean_promise_gap_pts"].abs() < 1e-9).all()  # the game pays what was committed
    assert cells[cells["arm"].isin(["A0", "C1", "D1"])]["mean_stated_share_pct"].isna().all()


# ------------------------------------------------------------------ spend and resume
def rec(label, tin, tout):
    return {"game": {"model_label": label}, "usage": {"input_tokens": tin, "output_tokens": tout}}


def test_restore_spend_makes_the_cap_cumulative():
    b = {"claude": Budget(5.0, 0.10, 0.50), "openai": Budget(5.0, 0.10, 0.50)}
    restore_spend([rec("claude", 1_000_000, 0), rec("claude", 0, 2_000_000), rec("openai", 1_000_000, 0)], b)
    assert b["claude"].spent == pytest.approx(0.10 + 1.00)
    assert b["openai"].spent == pytest.approx(0.10)
    restore_spend([rec("other", 1, 1)], b)                  # a model not being run is ignored
    assert b["claude"].spent == pytest.approx(1.10)


def manifest(tmp_path):
    out = mock_run(tmp_path, 2)
    return out, json.loads((out / "manifest.json").read_text())


def test_resume_refuses_changed_prompts(tmp_path):
    out, m = manifest(tmp_path)
    m["prompt_hashes"]["sender_base"] = "0" * 16
    (out / "manifest.json").write_text(json.dumps(m))
    r = sh("run.py", "--mock", "--out", str(out), "--games-per-cell", "2")
    assert r.returncode != 0 and "Refusing to resume" in (r.stderr + r.stdout) and "prompts" in (r.stderr + r.stdout)


def test_resume_refuses_changed_rules_and_settings(tmp_path):
    out, m = manifest(tmp_path)
    cfg = m["config"]
    new = {"prompt_hashes": m["prompt_hashes"], "code_hashes": code_hashes()}
    assert resume_problems(m, new, cfg, ["claude"]) == []   # same everything: fine
    bad_code = {**new, "code_hashes": {**new["code_hashes"], "engine.py": "f" * 16}}
    assert any("engine.py" in p for p in resume_problems(m, bad_code, cfg, ["claude"]))
    # agents.py may change between sessions (adapter fixes) without blocking a resume
    ok_adapter = {**new, "code_hashes": {**new["code_hashes"], "agents.py": "f" * 16}}
    assert resume_problems(m, ok_adapter, cfg, ["claude"]) == []
    assert any("temperature" in p for p in resume_problems(m, new, {**cfg, "temperature": 0.0}, ["claude"]))
    other = {**cfg, "models": [{**mm, "id": "some-other-model"} if mm["label"] == "claude" else mm for mm in cfg["models"]]}
    assert any("claude: id" in p for p in resume_problems(m, new, other, ["claude"]))


def test_manifest_records_commits_and_code_hashes(tmp_path):
    _, m = manifest(tmp_path)
    assert set(m["code_hashes"]) == {"engine.py", "escrow.py", "agents.py"}
    assert isinstance(m["git_commits"], list)


# ------------------------------------------------------------------ audit: the arm designs
def test_audit_flags_wrong_trustee_type(tmp_path):
    out = mock_run(tmp_path)
    recs = read(out)
    i = next(i for i, r in enumerate(recs) if r["game"]["arm"] == "C1" and r["game"]["idx"] == 0)
    recs[i]["game"]["trustee_type"] = "self_interested"     # idx 0 must be 'fair'
    write(out, recs)
    r = sh("audit.py", str(out))
    assert r.returncode == 1 and "design says 'fair'" in r.stdout


def test_audit_flags_a_valid_signature_in_the_broken_arm(tmp_path):
    out = mock_run(tmp_path)
    recs = read(out)
    i = next(i for i, r in enumerate(recs) if r["game"]["arm"] == "C3")
    recs[i]["game"]["arm"] = "C4"                           # a valid commitment cannot be a C4 game
    write(out, recs)
    r = sh("audit.py", str(out))
    assert r.returncode == 1 and "C4" in r.stdout


def test_audit_flags_a_signature_in_an_unsigned_arm(tmp_path):
    out = mock_run(tmp_path)
    recs = read(out)
    i, src = next((i, r) for i, r in enumerate(recs) if r["game"]["arm"] == "D3" and r["pre_play"].get("signature"))
    recs[i]["game"]["arm"] = "D2"
    write(out, recs)
    r = sh("audit.py", str(out))
    assert r.returncode == 1 and "unsigned arm carries a signature" in r.stdout


def test_audit_flags_artifact_that_differs_from_trustee_call(tmp_path):
    out = mock_run(tmp_path)
    recs = read(out)
    i = next(i for i, r in enumerate(recs) if r["game"]["arm"] == "C2")
    recs[i]["pre_play"]["share_percent"] = (recs[i]["pre_play"]["share_percent"] + 7) % 101
    write(out, recs)
    r = sh("audit.py", str(out))
    assert r.returncode == 1 and "differs from the trustee's call" in r.stdout


def test_git_commit_falls_back_to_the_shipped_file(tmp_path):
    from run import git_commit
    assert git_commit(tmp_path) is None                     # no repository, no file
    (tmp_path / "GIT_COMMIT").write_text("abc1234\n")
    assert git_commit(tmp_path) == "abc1234"
    if (ROOT / ".git").exists():                            # a zip copy has no repository to compare with
        assert git_commit(ROOT) == subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
