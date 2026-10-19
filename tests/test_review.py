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
IDS = {"claude": "claude-haiku-5-5", "openai": "gpt-6-luna"}


def rec(*calls):
    """A game record whose calls are (model id, input tokens, output tokens)."""
    return {"game": {"model_label": "x"},
            "calls": [{"model": m, "usage": {"input_tokens": i, "output_tokens": o}} for m, i, o in calls]}


def test_restore_spend_makes_the_cap_cumulative():
    b = {"claude": Budget(5.0, 0.10, 0.50), "openai": Budget(5.0, 0.10, 0.50)}
    restore_spend([rec((IDS["claude"], 1_000_000, 0), (IDS["claude"], 0, 2_000_000)), rec((IDS["openai"], 1_000_000, 0))], b, IDS)
    assert b["claude"].spent == pytest.approx(0.10 + 1.00)
    assert b["openai"].spent == pytest.approx(0.10)
    restore_spend([rec(("some-other-model", 1, 1))], b, IDS)    # a model not being run is ignored
    assert b["claude"].spent == pytest.approx(1.10)


def test_restore_spend_splits_a_cross_vendor_game_between_the_two_models():
    b = {"claude": Budget(5.0, 0.10, 0.50), "openai": Budget(5.0, 0.10, 0.50)}
    restore_spend([rec((IDS["claude"], 1_000_000, 0), (IDS["openai"], 0, 1_000_000))], b, IDS)
    assert b["claude"].spent == pytest.approx(0.10) and b["openai"].spent == pytest.approx(0.50)


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


def test_append_line_retries_a_locked_file(tmp_path, monkeypatch):
    import run as runmod
    p = tmp_path / "games.jsonl"
    real_open, calls = Path.open, {"n": 0}

    def flaky(self, *a, **k):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise PermissionError("locked by sync client")
        return real_open(self, *a, **k)

    monkeypatch.setattr(Path, "open", flaky)
    monkeypatch.setattr(runmod.time, "sleep", lambda s: None)
    runmod.append_line(p, "one\n")
    opens = calls["n"]                                      # read_text below also goes through the patched open
    assert opens == 3                                       # two refusals, then success
    assert p.read_text() == "one\n"
    calls["n"] = -100                                       # permanently locked: the error is raised
    with pytest.raises(PermissionError):
        runmod.append_line(p, "two\n", tries=3)


def test_batch_files_use_windows_line_endings():
    for name in ("setup_windows.bat", "run_openai.bat"):
        raw = (ROOT / name).read_bytes()
        assert b"\r\n" in raw and raw.count(b"\n") == raw.count(b"\r\n"), name
        assert b"--models openai" in raw or name == "setup_windows.bat"


# ------------------------------------------------------------------ cross-vendor pairs
class Spy:
    """Wraps a scripted agent and records which roles it was asked to play."""
    def __init__(self, inner, name):
        self.inner, self.name, self.roles = inner, name, []
        self.model_id, self.budget = name, inner.budget

    async def act(self, system, user, tools, terminal, execute, validate, ctx):
        self.roles.append(ctx["role"])
        return await self.inner.act(system, user, tools, terminal, execute, validate, ctx)


def play(agent, arm="C3", idx=0):
    import asyncio
    from engine import load_prompts, play_game
    game = {"game_id": f"T-{arm}-{idx}", "exp": 1, "arm": arm, "model_label": "t", "idx": idx,
            "trustee_type": "none" if arm == "A0" else ("fair" if idx % 2 == 0 else "self_interested"), "seed": 5}
    return asyncio.run(play_game(game, agent, load_prompts(ROOT / "prompts")))


def test_each_role_is_played_by_its_own_model():
    from agents import MockAgent
    for arm in ("A0", "C1", "C3", "C4", "D3"):
        buyer, supplier = Spy(MockAgent(1), "buyer-model"), Spy(MockAgent(2), "supplier-model")
        rec_ = play({"sender": buyer, "trustee": supplier}, arm)
        assert rec_["outcome"] is not None
        assert set(buyer.roles) == {"sender"} and set(supplier.roles) <= {"trustee"} and supplier.roles


def test_self_play_is_unchanged_by_the_cross_vendor_option():
    """One shared agent passed as before and the same agent passed for both roles give the same game.
    (Signatures are excluded: every game draws a fresh random signing key.)"""
    from agents import MockAgent
    def core(r):
        pre = {k: v for k, v in r["pre_play"].items() if k not in ("signature", "payload")}
        return r["outcome"], pre, r["comprehension"], r["return"]
    for arm in ("A0", "C1", "C2", "C3", "C4", "D2", "D3", "D4"):
        for idx in (0, 1):
            plain = play(MockAgent(7), arm, idx)
            shared = MockAgent(7)
            as_pair = play({"sender": shared, "trustee": shared}, arm, idx)
            assert core(plain) == core(as_pair), (arm, idx)


def test_pair_option_runs_audits_and_analyses(tmp_path):
    dirs = []
    for pair in ("claude>openai", "openai>claude"):
        out = tmp_path / pair.replace(">", "_to_")
        r = sh("run.py", "--mock", "--pair", pair, "--out", str(out), "--games-per-cell", "4")
        assert r.returncode == 0, r.stderr
        recs = read(out)
        assert {g["game"]["model_label"] for g in recs} == {pair} and len(recs) == 4 * 9
        assert json.loads((out / "manifest.json").read_text())["pair"] == pair
        dirs.append(str(out))
    assert sh("audit.py", *dirs, "--cells", str(tmp_path / "none")).returncode == 0
    if HAVE_BASELINE:
        r = sh("analyze.py", *dirs, "--out", str(tmp_path / "combined"))
        assert r.returncode == 0, r.stderr
        cells = pd.read_csv(tmp_path / "combined" / "cells.csv")
        assert set(cells["model"]) == {"claude>openai", "openai>claude"}


def test_pair_option_rejects_bad_input_and_a_changed_pairing(tmp_path):
    assert sh("run.py", "--mock", "--pair", "claude>claude", "--out", str(tmp_path / "a")).returncode != 0
    assert sh("run.py", "--mock", "--pair", "claude>openai", "--models", "claude", "--out", str(tmp_path / "b")).returncode != 0
    out = tmp_path / "c"
    assert sh("run.py", "--mock", "--pair", "claude>openai", "--out", str(out), "--games-per-cell", "2").returncode == 0
    r = sh("run.py", "--mock", "--pair", "openai>claude", "--out", str(out), "--games-per-cell", "2")
    assert r.returncode != 0 and "pairing differs" in (r.stderr + r.stdout)


def test_cross_script_quotes_the_pairing_and_uses_windows_line_endings():
    raw = (ROOT / "run_cross.bat").read_bytes()
    assert raw.count(b"\n") == raw.count(b"\r\n")
    text = raw.decode()
    assert '--pair "claude>openai"' in text and '--pair "openai>claude"' in text
    assert "--pair claude>" not in text and "--pair openai>" not in text     # an unquoted > would redirect output


def test_stronger_models_never_run_by_default_and_arms_subset_works(tmp_path):
    out = tmp_path / "default"
    assert sh("run.py", "--mock", "--out", str(out), "--games-per-cell", "2").returncode == 0
    assert {g["game"]["model_label"] for g in read(out)} == {"claude", "openai"}      # sensitivity models are opt-in
    out = tmp_path / "subset"
    r = sh("run.py", "--mock", "--models", "claude_sonnet", "--arms", "A0,C1,C3,D1,D3", "--out", str(out), "--games-per-cell", "4")
    assert r.returncode == 0, r.stderr
    recs = read(out)
    assert {g["game"]["arm"] for g in recs} == {"A0", "C1", "C3", "D1", "D3"} and len(recs) == 5 * 4
    assert {g["game"]["model_label"] for g in recs} == {"claude_sonnet"}
    assert sh("audit.py", str(out), "--cells", str(tmp_path / "none")).returncode == 0
    assert sh("run.py", "--mock", "--models", "claude_sonnet", "--arms", "A0,C1", "--out", str(out), "--games-per-cell", "4").returncode != 0
    assert sh("run.py", "--mock", "--arms", "Z9", "--out", str(tmp_path / "z")).returncode != 0
    if HAVE_BASELINE:     # arms that were not played give n/a, not a crash
        r = sh("analyze.py", str(out), "--out", str(tmp_path / "an"))
        assert r.returncode == 0, r.stderr
        h = pd.read_csv(tmp_path / "an" / "hypotheses.csv").set_index("id")
        assert h.loc["H1", "label"] in ("positive", "null", "inconclusive")
        assert pd.isna(h.loc["H3a", "label"]) or h.loc["H3a", "label"] == "n/a"      # pandas reads the string n/a as NaN


def test_stronger_model_config_matches_the_pricing_page():
    import yaml
    m = {x["label"]: x for x in yaml.safe_load((ROOT / "config.yaml").read_text())["models"]}
    assert (m["claude_sonnet"]["id"], m["claude_sonnet"]["price_in"], m["claude_sonnet"]["price_out"]) == ("claude-sonnet-5-5", 2.0, 10.0)
    assert (m["openai_sol"]["id"], m["openai_sol"]["price_in"], m["openai_sol"]["price_out"]) == ("gpt-6.1-sol", 2.0, 10.0)
    assert m["claude_sonnet"]["sensitivity"] and m["openai_sol"]["sensitivity"]


def test_theory_table_values():
    from theory import predictions
    t = {r["arm"]: r for r in predictions()}
    for arm in ("A0", "C1", "C2", "C4", "D1", "D2", "D4"):
        assert t[arm]["sent"] == 0 and abs(t[arm]["eff"] - 100 / 3) < 1e-9
    assert t["C3"]["sent"] == 10 and t["C3"]["eff"] == 100
    assert t["D3"]["sent"] == 5 and abs(t["D3"]["eff"] - 200 / 3) < 1e-9
    assert [r["arm"] for r in predictions()] == ["A0", "C1", "C2", "C3", "C4", "D1", "D2", "D3", "D4"]


def test_every_bat_file_uses_windows_line_endings_and_quotes_pairs():
    for f in ROOT.glob("*.bat"):
        raw = f.read_bytes()
        assert raw.count(b"\n") == raw.count(b"\r\n"), f.name
    text = (ROOT / "run_stronger_openai.bat").read_text()
    assert "--arms A0,C1,C3,D1,D3" in text and "--models openai_sol" in text and "--games-per-cell 40" in text


def test_anthropic_adapter_falls_back_to_auto_tool_choice_even_under_concurrency():
    import asyncio
    from types import SimpleNamespace
    from agents import AnthropicAgent

    seen = []

    class Bad(Exception):
        pass

    class Resp:
        content, stop_reason = [], "end_turn"
        usage = SimpleNamespace(input_tokens=1, output_tokens=1)

    async def create(**kw):
        seen.append(kw["tool_choice"]["type"])
        if kw["tool_choice"]["type"] in ("any", "tool"):
            await asyncio.sleep(0.01)
            raise Bad('tool_choice: type "tool" and "any" are not supported for this model.')
        return Resp()

    a = AnthropicAgent("m", 1.0, 100, Budget(1, 1, 1), api_key="k")
    a._anthropic = SimpleNamespace(BadRequestError=Bad)
    a.client = SimpleNamespace(messages=SimpleNamespace(create=create))

    async def go():
        return await asyncio.gather(*[a._complete("s", [], [], None) for _ in range(3)])      # three calls in flight at once
    asyncio.run(go())
    assert a.auto_choice and seen.count("auto") == 3


# ---- Responses API adapter (gpt-6.1-sol) ----
class _RespClient:
    class BadRequestError(Exception):
        pass

    def __init__(self, script):
        from types import SimpleNamespace as NS
        self.script, self.seen = list(script), []
        self.responses = NS(create=self._create)

    async def _create(self, **kw):
        self.seen.append(kw)
        r = self.script.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def _r(calls=(), text=None, pin=100, pout=50):
    from types import SimpleNamespace as NS
    import json as _j
    out = []
    if text:
        out.append(NS(type="message", content=[NS(type="output_text", text=text)]))
    out.append(NS(type="reasoning", summary=[]))
    for i, (n, a) in enumerate(calls):
        out.append(NS(type="function_call", call_id=f"c{i}", name=n, arguments=_j.dumps(a)))
    return NS(output=out, status="completed", usage=NS(input_tokens=pin, output_tokens=pout))


def _resp_agent(client):
    from agents import OpenAIResponsesAgent, Budget
    return OpenAIResponsesAgent("gpt-6.1-sol", 1.0, 4000, Budget(5.0, 2.0, 10.0), "low", client=client)


def test_responses_adapter_translates_and_returns_the_terminal_input():
    import asyncio, json as _j
    from engine import TOOLS, validate_input
    c = _RespClient([_r([("verify_commitment", {})]), _r([("submit_transfer", {"amount": 6, "rationale": "x"})])])
    tools = [TOOLS["verify_commitment"], TOOLS["submit_transfer"]]
    ex = lambda n, i: _j.dumps({"signature_valid": True})
    r = asyncio.run(_resp_agent(c).act("SYS", "USER", tools, "submit_transfer", ex, lambda n, i: validate_input(n, i), {}))
    assert r["input"]["amount"] == 6 and not r["aborted"]
    first, second = c.seen
    assert first["instructions"] == "SYS" and first["input"] == [{"role": "user", "content": "USER"}]
    assert first["tool_choice"] == "required" and first["reasoning"] == {"effort": "low"}
    assert "temperature" not in first and first["max_output_tokens"] == 4000
    assert first["tools"][0]["type"] == "function" and first["tools"][0]["name"] == "verify_commitment"
    assert second["input"][1] == {"type": "function_call", "call_id": "c0", "name": "verify_commitment", "arguments": "{}"}
    assert second["input"][2]["type"] == "function_call_output" and second["input"][2]["call_id"] == "c0"
    assert r["usage"]["output_tokens"] == 100


def test_responses_adapter_falls_back_to_auto_tool_choice_and_drops_rejected_params():
    import asyncio
    from engine import TOOLS
    bad = _RespClient.BadRequestError
    c = _RespClient([bad("Invalid value for tool_choice"), bad("Unsupported parameter: parallel_tool_calls"),
                     _r([("submit_transfer", {"amount": 1, "rationale": "x"})])])
    a = _resp_agent(c)
    asyncio.run(a.act("S", "U", [TOOLS["submit_transfer"]], "submit_transfer", None, None, {}))
    assert c.seen[-1]["tool_choice"] == "auto" and "parallel_tool_calls" not in c.seen[-1]
    assert a.auto_choice and "parallel_tool_calls" in a.drop


def test_sol_is_configured_for_the_responses_api_and_selected_by_make_agent():
    import yaml, run
    from agents import OpenAIResponsesAgent, OpenAIAgent, Budget
    cfg = yaml.safe_load(open("config.yaml"))
    sol = next(m for m in cfg["models"] if m["label"] == "openai_sol")
    assert sol["api"] == "responses" and sol["reasoning_effort"] == "low" and sol["max_tokens"] == 4000
    import os; os.environ.setdefault("OPENAI_API_KEY", "test")
    assert isinstance(run.make_agent(sol, cfg, Budget(1, 2, 10)), OpenAIResponsesAgent)
    luna = next(m for m in cfg["models"] if m["label"] == "openai")
    a = run.make_agent(luna, cfg, Budget(1, .1, .5))
    assert type(a) is OpenAIAgent and a.max_tokens == cfg["max_tokens"]


def test_returned_model_version_is_stored_per_call_and_collected():
    import asyncio
    from engine import TOOLS
    r = _r([("submit_transfer", {"amount": 3, "rationale": "x"})])
    r.model = "gpt-6.1-sol-2026-09-30"          # what the vendor's API reports back
    a = _resp_agent(_RespClient([r]))
    out = asyncio.run(a.act("S", "U", [TOOLS["submit_transfer"]], "submit_transfer", None, None, {}))
    assert out["calls"][0]["model_returned"] == "gpt-6.1-sol-2026-09-30"
    assert out["calls"][0]["model"] == "gpt-6.1-sol"            # the requested alias is kept too
    assert a.seen_models == {"gpt-6.1-sol-2026-09-30"}
    # an API that returns no model string leaves the field empty instead of failing
    a2 = _resp_agent(_RespClient([_r([("submit_transfer", {"amount": 3, "rationale": "x"})])]))
    out2 = asyncio.run(a2.act("S", "U", [TOOLS["submit_transfer"]], "submit_transfer", None, None, {}))
    assert out2["calls"][0]["model_returned"] is None
