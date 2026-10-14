import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HAVE_BASELINE = (ROOT / "data" / "human_baseline_johnson_mislin_2011.csv").exists()


def sh(*args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)


def test_mock_run_analyze_audit(tmp_path):
    out = tmp_path / "mock"
    r = sh("run.py", "--mock", "--out", str(out), "--games-per-cell", "6")
    assert r.returncode == 0, r.stderr
    games = [json.loads(l) for l in (out / "games.jsonl").read_text().splitlines()]
    assert len(games) == 6 * 2 * 9            # 9 arms, 2 models
    assert {g["game"]["arm"] for g in games} == {"A0", "C1", "C2", "C3", "C4", "D1", "D2", "D3", "D4"}
    # every typed cell is balanced 50/50 between principal types
    c3 = [g for g in games if g["game"]["arm"] == "C3" and g["game"]["model_label"] == "small"]
    assert sum(g["game"]["trustee_type"] == "fair" for g in c3) == 3
    if HAVE_BASELINE:
        r = sh("analyze.py", str(out))
        assert r.returncode == 0, r.stderr
        assert (out / "results.md").exists() and (out / "hypotheses.csv").exists()
    r = sh("audit.py", str(out))
    assert r.returncode == 0 and "AUDIT PASS" in r.stdout, r.stdout


def test_resume_skips_finished_games(tmp_path):
    out = tmp_path / "mock"
    sh("run.py", "--mock", "--out", str(out), "--games-per-cell", "2")
    n1 = len((out / "games.jsonl").read_text().splitlines())
    r = sh("run.py", "--mock", "--out", str(out), "--games-per-cell", "2")
    assert "0 to run" in r.stdout
    assert len((out / "games.jsonl").read_text().splitlines()) == n1


def test_audit_catches_tampering(tmp_path):
    out = tmp_path / "mock"
    sh("run.py", "--mock", "--out", str(out), "--games-per-cell", "3")
    lines = (out / "games.jsonl").read_text().splitlines()
    rec = json.loads(lines[0])
    rec["outcome"]["sent"] += 1 if rec["outcome"]["sent"] < 10 else -1     # edit a stored metric
    lines[0] = json.dumps(rec)
    (out / "games.jsonl").write_text("\n".join(lines) + "\n")
    r = sh("audit.py", str(out))
    assert r.returncode == 1 and "AUDIT FAIL" in r.stdout


def test_audit_catches_forged_signature(tmp_path):
    out = tmp_path / "mock"
    sh("run.py", "--mock", "--out", str(out), "--games-per-cell", "4")
    lines = (out / "games.jsonl").read_text().splitlines()
    for i, l in enumerate(lines):
        rec = json.loads(l)
        if rec["game"]["arm"] == "C3" and rec["return"]["source"] == "escrow_auto":
            rec["pre_play"]["signature"] = rec["pre_play"]["signature"][:-2] + ("00" if rec["pre_play"]["signature"][-2:] != "00" else "ff")
            lines[i] = json.dumps(rec)
            break
    (out / "games.jsonl").write_text("\n".join(lines) + "\n")
    r = sh("audit.py", str(out))
    assert r.returncode == 1
