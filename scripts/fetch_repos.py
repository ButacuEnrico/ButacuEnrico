"""Save public repo facts for the profile cards into data/repos.json.

Uses the gh CLI (already logged in on the Mac). On any failure it keeps the
previous file, so a missed fetch never blanks the cards.

Usage: python3 scripts/fetch_repos.py
"""
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "repos.json"
USER = "ButacuEnrico"
WEEKS = 26
MAX_CARDS = 2


def gh(path: str, jq: str) -> str:
    return subprocess.run(["gh", "api", "--paginate", path, "--jq", jq],
                          check=True, capture_output=True, text=True, timeout=60).stdout


def main() -> None:
    try:
        rows = [json.loads(line) for line in gh(
            f"users/{USER}/repos?per_page=100&type=owner",
            ".[] | select(.fork | not) | select(.private | not) | "
            "{name, language, description, pushed_at, html_url}").splitlines()]
        rows = [r for r in rows if r["name"] != USER]
        rows.sort(key=lambda r: r["pushed_at"], reverse=True)
        cards = []
        for r in rows[:MAX_CARDS]:
            dates = [datetime.fromisoformat(d.replace("Z", "+00:00")) for d in gh(
                f"repos/{USER}/{r['name']}/commits?per_page=100", ".[].commit.author.date").split()]
            end = max(dates) if dates else datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
            weeks = [0] * WEEKS
            for d in dates:
                age = (end - d) // timedelta(weeks=1)
                if age < WEEKS:
                    weeks[WEEKS - 1 - age] += 1
            cards.append({**r, "commits": len(dates), "weeks": weeks})
    except (subprocess.SubprocessError, OSError, ValueError) as err:
        print(f"repos: kept previous data ({err.__class__.__name__})")
        return
    OUT.write_text(json.dumps(cards, indent=1))
    print("repos: " + ", ".join(f"{c['name']} ({c['commits']} commits)" for c in cards))


if __name__ == "__main__":
    main()
