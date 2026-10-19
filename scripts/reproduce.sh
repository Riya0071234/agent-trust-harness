#!/usr/bin/env bash
# Rebuild every analysis, audit and figure from the raw games in results/. No API key needed.
# analyze.py also needs data/human_baseline_johnson_mislin_2011.csv (see data/README.md);
# without it, the analyses are skipped and the audit and figures still run.
set -euo pipefail
cd "$(dirname "$0")/.."
A=results/analysis
if [ -f data/human_baseline_johnson_mislin_2011.csv ]; then
  python analyze.py results/claude results/openai --out $A/selfplay
  python analyze.py results/claude --out $A/selfplay_haiku
  python analyze.py results/openai --out $A/selfplay_luna
  python analyze.py results/cross_claude_buys results/cross_openai_buys --out $A/cross
  python analyze.py results/stronger_claude_sonnet --out $A/stronger_sonnet
  python analyze.py results/stronger_openai_sol --out $A/stronger_sol
else
  echo "Human baseline file not found: skipping analyze.py, using the committed analyses."
fi
python audit.py results/claude results/openai --cells $A/selfplay
python audit.py results/claude --cells $A/selfplay_haiku
python audit.py results/openai --cells $A/selfplay_luna
python audit.py results/cross_claude_buys results/cross_openai_buys --cells $A/cross
python audit.py results/stronger_claude_sonnet --cells $A/stronger_sonnet
python audit.py results/stronger_openai_sol --cells $A/stronger_sol
python theory.py --cells $A/selfplay/cells.csv
python figures.py
echo "Done: every audit above must say AUDIT PASS."
