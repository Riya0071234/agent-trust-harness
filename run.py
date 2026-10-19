"""run.py - run the experiment grid unattended, resume after a crash, write JSONL transcripts.

Usage:
  python run.py --smoke --models claude --out results/smoke_claude       # 2 games per arm; prints cost and the size to run
  python run.py --out results/claude --models claude --games-per-cell 80  # real run (needs ANTHROPIC_API_KEY)
  python run.py --out results/openai --models openai --games-per-cell 80  # real run (needs OPENAI_API_KEY)
  python run.py --mock --out results/mock_x --games-per-cell 4            # scripted stand-in, free

Each finished game is one line of <out>/games.jsonl. Re-running the same command skips games
already on disk, so a crash or a spend-cap stop loses at most the games in flight.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import yaml

from agents import AnthropicAgent, Budget, BudgetExceeded, MockAgent, OpenAIAgent
from engine import ARMS, load_prompts, play_game, prompt_hashes

SIZES = (160, 80, 40, 20)       # candidate games per cell, largest first
SAFETY = 0.70                   # a size is chosen only if its projected cost is within 70% of the cap


def build_games(cfg: dict, exps: list[int], n_per_cell: int, model_labels: list[str]) -> list[dict]:
    games = []
    for exp in exps:
        for arm in cfg["experiments"][exp]:
            for label in model_labels:
                for idx in range(n_per_cell):
                    gid = f"E{exp}-{arm}-{label}-{idx:03d}"
                    seed = int(hashlib.sha256(f"{cfg['seed']}-{gid}".encode()).hexdigest()[:12], 16)
                    # typed arms alternate fair / self_interested so every cell is balanced 50/50
                    ptype = ("fair" if idx % 2 == 0 else "self_interested") if ARMS[arm]["typed"] else "none"
                    games.append({"game_id": gid, "exp": exp, "arm": arm, "model_label": label,
                                  "idx": idx, "trustee_type": ptype, "seed": seed})
    return games


def git_commit(root: Path | None = None) -> str | None:
    """HEAD of the repository holding this code. A copy without .git (a zip) ships a GIT_COMMIT file
    naming the commit it was built from."""
    root = root or Path(__file__).parent
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                              cwd=root).stdout.strip()
    except Exception:
        f = root / "GIT_COMMIT"
        return f.read_text().strip() if f.exists() else None


def make_agent(m: dict, cfg: dict, budget: Budget):
    if m["provider"] == "anthropic":
        return AnthropicAgent(m["id"], cfg["temperature"], cfg["max_tokens"], budget)
    if m["provider"] == "openai":
        return OpenAIAgent(m["id"], cfg["temperature"], cfg["max_tokens"], budget, m.get("reasoning_effort"))
    sys.exit(f"unknown provider {m['provider']!r}")


GAME_LOGIC_FILES = ("engine.py", "escrow.py", "agents.py")


def code_hashes() -> dict[str, str]:
    root = Path(__file__).parent
    return {f: hashlib.sha256((root / f).read_bytes()).hexdigest()[:16] for f in GAME_LOGIC_FILES}


def append_line(path: Path, line: str, tries: int = 6) -> None:
    """Append one line. A sync client (OneDrive) can lock the file for a moment, so a refused open is
    retried a few times instead of ending the run. A refused open writes nothing, so no line is half-written."""
    for attempt in range(tries):
        try:
            with path.open("a") as f:
                f.write(line)
            return
        except PermissionError:
            if attempt == tries - 1:
                raise
            time.sleep(0.5 * (attempt + 1))


def restore_spend(records: list[dict], budgets: dict) -> None:
    """Add the token cost of games already on disk to each model's budget, so the cap and the
    manifest's spend are cumulative across resumes rather than per session."""
    for rec in records:
        b = budgets.get(rec["game"]["model_label"])
        if b is not None:
            b.add(rec["usage"]["input_tokens"], rec["usage"]["output_tokens"])


def resume_problems(old: dict, new: dict, cfg: dict, labels: list[str]) -> list[str]:
    """Reasons a run directory must not be resumed: games played under different prompts, game
    rules or model settings would silently be mixed with the new ones."""
    problems = []
    if old.get("prompt_hashes") != new["prompt_hashes"]:
        problems.append("the prompts differ from those used for the games already on disk")
    oc = old.get("config", {})
    for k in ("seed", "temperature", "max_tokens"):
        if oc.get(k) != cfg[k]:
            problems.append(f"config {k} differs ({oc.get(k)!r} on disk, {cfg[k]!r} now)")
    old_models = {m["label"]: m for m in oc.get("models", [])}
    new_models = {m["label"]: m for m in cfg["models"]}
    for label in labels:
        o, n = old_models.get(label), new_models[label]
        if o is not None:
            for k in ("id", "reasoning_effort"):
                if o.get(k) != n.get(k):
                    problems.append(f"model {label}: {k} differs ({o.get(k)!r} on disk, {n.get(k)!r} now)")
    oh = old.get("code_hashes")
    if oh:   # older manifests predate code hashes; the rules files must be identical, the adapter may change
        for f in ("engine.py", "escrow.py"):
            if oh.get(f) != new["code_hashes"][f]:
                problems.append(f"{f} differs from the version that played the games already on disk")
    return problems


def projected_cost(cost_per_game: float, n_per_cell: int, n_arms: int) -> float:
    """Cost of a full grid of n_per_cell games in each of n_arms arms for one model."""
    return cost_per_game * n_arms * n_per_cell


async def main_async(args):
    cfg = yaml.safe_load(Path(args.config).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prompts = load_prompts("prompts")
    n = 2 if args.smoke else (args.games_per_cell or cfg["games_per_cell"])
    exps = [1, 2]

    wanted = set(args.models.split(",")) if args.models else {m["label"] for m in cfg["models"]}
    models = [m for m in cfg["models"] if m["label"] in wanted]
    if not models:
        sys.exit(f"no models match --models {args.models}")
    budgets, agents, model_ids = {}, {}, {}
    for m in models:
        cap = args.max_spend if args.max_spend is not None else m["max_spend_usd"]
        budgets[m["label"]] = Budget(cap, m["price_in"], m["price_out"])
        if args.mock:
            agents[m["label"]], model_ids[m["label"]] = MockAgent(seed=cfg["seed"]), "mock"
        else:
            agents[m["label"]] = make_agent(m, cfg, budgets[m["label"]])
            model_ids[m["label"]] = m["id"]

    games = build_games(cfg, exps, n, list(agents))
    games_path = out / "games.jsonl"
    done, existing = set(), []
    if games_path.exists():
        existing = [json.loads(line) for line in games_path.read_text().splitlines() if line.strip()]
        done = {r["game"]["game_id"] for r in existing}
    todo = [g for g in games if g["game_id"] not in done]

    manifest_path = out / "manifest.json"
    manifest = {
        "run_started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mock": args.mock, "smoke": args.smoke, "games_per_cell": n, "experiments": exps,
        "model_ids": model_ids, "providers": {m["label"]: m["provider"] for m in models},
        "config": cfg, "prompt_hashes": prompt_hashes(prompts), "git_commit": git_commit(),
        "code_hashes": code_hashes(),
        "python": platform.python_version(), "planned_games": len(games),
    }
    manifest["git_commits"] = [manifest["git_commit"]] if manifest["git_commit"] else []
    if manifest_path.exists():   # keep the original start time; log resumes
        old = json.loads(manifest_path.read_text())
        problems = resume_problems(old, manifest, cfg, list(agents))
        if problems:
            sys.exit("Refusing to resume " + str(out) + ":\n  - " + "\n  - ".join(problems)
                     + "\nStart a new --out directory, or restore the earlier files.")
        manifest["run_started_utc"] = old["run_started_utc"]
        manifest["resumed_utc"] = old.get("resumed_utc", []) + [time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())]
        prev = old.get("git_commits") or ([old["git_commit"]] if old.get("git_commit") else [])
        manifest["git_commits"] = prev + [c for c in manifest["git_commits"] if c not in prev]
    restore_spend(existing, budgets)
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"{len(games)} planned, {len(done)} already done, {len(todo)} to run.", flush=True)
    for label, b in budgets.items():
        print(f"  {label}: {model_ids[label]}, cap ${b.cap:.2f}, already spent ${b.spent:.4f}", flush=True)
    sem = asyncio.Semaphore(args.concurrency or cfg["concurrency"])
    lock = asyncio.Lock()
    stats = {"done": 0, "aborted": 0}
    stopped: set[str] = set()
    per_model_done = {label: 0 for label in agents}

    async def worker(game):
        label = game["model_label"]
        async with sem:
            if label in stopped:
                return
            try:
                rec = await play_game(game, agents[label], prompts)
            except BudgetExceeded as e:
                stopped.add(label)
                print(f"STOP {label}: {e}", flush=True)
                return
            rec["game"]["model_id"] = model_ids[label]
            async with lock:
                append_line(games_path, json.dumps(rec) + "\n")
                stats["done"] += 1
                stats["aborted"] += 1 if rec["aborted"] else 0
                per_model_done[label] += 1
                if stats["done"] % 10 == 0 or stats["done"] == len(todo):
                    spend = ", ".join(f"{k} ${b.spent:.2f}" for k, b in budgets.items())
                    print(f"{stats['done']}/{len(todo)} games, {stats['aborted']} aborted, spend: {spend}", flush=True)

    await asyncio.gather(*(worker(g) for g in todo))

    manifest["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["spend_usd"] = {k: round(b.spent, 4) for k, b in budgets.items()}
    manifest["stopped_by_cap"] = sorted(stopped)
    for label, a in agents.items():   # parameters a model rejected and the code dropped
        dropped = sorted(getattr(a, "drop", set()) | ({"temperature"} if getattr(a, "send_temperature", True) is False else set()))
        if dropped:
            manifest.setdefault("dropped_parameters", {})[label] = dropped
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Finished. {stats['done']} games written ({stats['aborted']} aborted). Spend: "
          + ", ".join(f"{k} ${b.spent:.4f}" for k, b in budgets.items()), flush=True)
    if stopped:
        print(f"Stopped by spend cap: {', '.join(sorted(stopped))}. Run the same command again to resume.", flush=True)

    if args.smoke and not args.mock:
        print("\nSmoke test: size to run (largest size whose projected cost is within "
              f"{int(SAFETY * 100)}% of the cap)", flush=True)
        for label, b in budgets.items():
            n_label = per_model_done[label] + sum(1 for r in existing if r["game"]["model_label"] == label)
            if n_label == 0:
                print(f"  {label}: no games finished", flush=True)
                continue
            cost_per_game = b.spent / n_label       # spend and game count both cumulative
            n_arms = sum(len(v) for v in cfg["experiments"].values())
            choice = next((size for size in SIZES
                           if projected_cost(cost_per_game, size, n_arms) <= SAFETY * b.cap), None)
            print(f"  {label}: ${cost_per_game:.4f} per game -> games per cell: "
                  f"{choice or 'none fits; lower the size or raise the cap'}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", default=None, help="comma-separated labels from config.yaml (default: all)")
    ap.add_argument("--games-per-cell", type=int, default=None)
    ap.add_argument("--max-spend", type=float, default=None, help="override each model's cap")
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--smoke", action="store_true", help="2 games per arm; data are discarded; prints the size to run")
    ap.add_argument("--mock", action="store_true", help="scripted stand-in; never report as model results")
    asyncio.run(main_async(ap.parse_args()))
