"""run.py - run the experiment grid unattended, resume after a crash, write JSONL transcripts.

Usage:
  python run.py --out results/pilot --games-per-cell 20            # real run (needs ANTHROPIC_API_KEY)
  python run.py --mock --out results/mock --games-per-cell 4        # scripted stand-in, free

Each finished game is one line of <out>/games.jsonl. Re-running the same command skips
games already on disk, so a crash or a spend-cap stop loses at most the games in flight.
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

from agents import AnthropicAgent, Budget, BudgetExceeded, MockAgent
from engine import ARMS, load_prompts, play_game, prompt_hashes


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


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


async def main_async(args):
    cfg = yaml.safe_load(Path(args.config).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prompts = load_prompts("prompts")
    n = args.games_per_cell or cfg["games_per_cell"]
    exps = [1, 2] if args.exp == "all" else [int(args.exp)]

    budget = Budget(args.max_spend or cfg["max_spend_usd"])
    agents, model_ids = {}, {}
    for m in cfg["models"]:
        if args.mock:
            agents[m["label"]] = MockAgent(seed=cfg["seed"])
            model_ids[m["label"]] = "mock"
        else:
            if None in (m["id"], m["price_in"], m["price_out"]):
                sys.exit(f"config.yaml: model '{m['label']}' needs id, price_in and price_out before a real run.")
            agents[m["label"]] = AnthropicAgent(m["id"], cfg["temperature"], cfg["max_tokens"], budget,
                                                m["price_in"], m["price_out"])
            model_ids[m["label"]] = m["id"]

    games = build_games(cfg, exps, n, list(agents))
    games_path = out / "games.jsonl"
    done = set()
    if games_path.exists():
        done = {json.loads(line)["game"]["game_id"] for line in games_path.read_text().splitlines() if line.strip()}
    todo = [g for g in games if g["game_id"] not in done]

    manifest_path = out / "manifest.json"
    manifest = {
        "run_started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mock": args.mock,
        "games_per_cell": n,
        "experiments": exps,
        "model_ids": model_ids,
        "config": cfg,
        "prompt_hashes": prompt_hashes(prompts),
        "git_commit": git_commit(),
        "python": platform.python_version(),
        "anthropic_sdk": __import__("anthropic").__version__ if not args.mock else None,
        "planned_games": len(games),
    }
    if manifest_path.exists():   # keep the original start time; log resumes
        old = json.loads(manifest_path.read_text())
        manifest["run_started_utc"] = old["run_started_utc"]
        manifest["resumed_utc"] = old.get("resumed_utc", []) + [time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())]
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"{len(games)} planned, {len(done)} already done, {len(todo)} to run. Cap ${budget.cap:.2f}.", flush=True)
    sem = asyncio.Semaphore(args.concurrency or cfg["concurrency"])
    lock = asyncio.Lock()
    stats = {"done": 0, "aborted": 0, "stopped": False}

    async def worker(game):
        async with sem:
            if stats["stopped"]:
                return
            try:
                rec = await play_game(game, agents[game["model_label"]], prompts)
            except BudgetExceeded as e:
                stats["stopped"] = True
                print(f"STOP: {e}", flush=True)
                return
            rec["game"]["model_id"] = model_ids[game["model_label"]]
            async with lock:
                with games_path.open("a") as f:
                    f.write(json.dumps(rec) + "\n")
                stats["done"] += 1
                stats["aborted"] += 1 if rec["aborted"] else 0
                if stats["done"] % 10 == 0 or stats["done"] == len(todo):
                    print(f"{stats['done']}/{len(todo)} games, {stats['aborted']} aborted, spend ${budget.spent:.2f}", flush=True)

    await asyncio.gather(*(worker(g) for g in todo))
    manifest["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["spend_usd"] = round(budget.spent, 4)
    manifest["stopped_by_cap"] = stats["stopped"]
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Finished. {stats['done']} games written, spend ${budget.spent:.2f}. Re-run the same command to resume." if stats["stopped"]
          else f"Finished. {stats['done']} games written, spend ${budget.spent:.2f}.", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", required=True)
    ap.add_argument("--exp", default="all", choices=["1", "2", "all"])
    ap.add_argument("--games-per-cell", type=int, default=None)
    ap.add_argument("--max-spend", type=float, default=None)
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--mock", action="store_true", help="scripted stand-in; never report as model results")
    asyncio.run(main_async(ap.parse_args()))
