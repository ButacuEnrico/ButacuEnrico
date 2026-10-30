#!/bin/zsh
# Recount local AI usage, re-render hero.svg and push if anything changed.
# Run by hand or daily from launchd (LaunchAgent com.butacuenrico.profile, kept local: it holds this Mac's paths).
set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/collect_ai_usage.py
python3 scripts/fetch_repos.py
python3 scripts/render_hero.py
python3 scripts/render_extras.py

git add data/ai-usage.json data/repos.json README.md *.svg
if git diff --cached --quiet; then
  echo "no changes"
  exit 0
fi
git commit -q -m "chore: refresh AI usage $(date +%Y-%m-%d)"
git push -q
echo "pushed"
