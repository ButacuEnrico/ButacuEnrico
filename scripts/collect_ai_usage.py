"""Sum local AI usage into data/ai-usage.json. Runs on the Mac, not in CI.

Reads only token counters, timestamps and model names from:
  - Claude Code transcripts   ~/.claude/projects/**/*.jsonl
  - OpenAI Codex sessions     ~/.codex/{sessions,archived_sessions}/**/*.jsonl
Never reads or stores message content, prompts, file names or project names.

Usage: python3 scripts/collect_ai_usage.py
"""
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ai-usage.json"
HOME = Path.home()
# AI responses per local hour of day, both providers together
HOURS = [0] * 24


def tick_hour(stamp: str) -> None:
    try:
        HOURS[datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone().hour] += 1
    except ValueError:
        pass


def claude() -> dict:
    seen = set()
    daily = defaultdict(int)
    models = Counter()
    out_tokens = 0
    sessions = set()
    for path in (HOME / ".claude" / "projects").rglob("*.jsonl"):
        with open(path, "rb") as fh:
            for raw in fh:
                if b'"usage"' not in raw or b'"assistant"' not in raw:
                    continue
                try:
                    rec = json.loads(raw)
                except ValueError:
                    continue
                msg = rec.get("message") or {}
                usage = msg.get("usage")
                if rec.get("type") != "assistant" or not usage:
                    continue
                key = msg.get("id") or rec.get("uuid")
                if key in seen:  # streamed messages repeat the same usage
                    continue
                seen.add(key)
                total = sum(usage.get(k) or 0 for k in (
                    "input_tokens", "output_tokens",
                    "cache_creation_input_tokens", "cache_read_input_tokens"))
                if not total:
                    continue
                daily[rec.get("timestamp", "")[:10]] += total
                tick_hour(rec.get("timestamp", ""))
                out_tokens += usage.get("output_tokens") or 0
                model = msg.get("model") or ""
                if model and not model.startswith("<"):
                    models[model] += total
                sessions.add(rec.get("sessionId"))
    return summary(daily, out_tokens, len(sessions), models)


def codex() -> dict:
    daily = defaultdict(int)
    out_tokens = 0
    sessions = 0
    models = Counter()
    base = HOME / ".codex"
    for path in list((base / "sessions").rglob("*.jsonl")) + list((base / "archived_sessions").rglob("*.jsonl")):
        prev = 0
        model = ""
        last_out = 0
        counted = False
        with open(path, "rb") as fh:
            for raw in fh:
                if b'"model"' in raw and b'turn_context' in raw:
                    try:
                        model = json.loads(raw)["payload"].get("model") or model
                    except (ValueError, KeyError, AttributeError):
                        pass
                if b'"token_count"' not in raw:
                    continue
                try:
                    rec = json.loads(raw)
                    info = rec["payload"]["info"]
                except (ValueError, KeyError):
                    continue
                if not info:
                    continue
                tot = info["total_token_usage"]
                # cumulative per session: attribute each increase to its day
                delta = tot.get("total_tokens", 0) - prev
                if delta > 0:
                    daily[rec.get("timestamp", "")[:10]] += delta
                    tick_hour(rec.get("timestamp", ""))
                    if model:
                        models[model] += delta
                prev = tot.get("total_tokens", prev)
                last_out = tot.get("output_tokens", 0)
                counted = True
        out_tokens += last_out
        sessions += counted
    return summary(daily, out_tokens, sessions, models)


def summary(daily: dict, out_tokens: int, sessions: int, models: Counter) -> dict:
    daily = {d: n for d, n in daily.items() if len(d) == 10}
    today = date.today()
    year = [daily.get((today - timedelta(days=i)).isoformat(), 0) for i in range(370, -1, -1)]
    last30 = year[-30:]
    # only what the profile draws goes into the public file: no models, sessions or dates
    return {
        "year": year,
        "total_tokens": sum(daily.values()),
        "last30": last30,
    }


def main() -> None:
    data = {"updated": date.today().isoformat(), "claude": claude(), "openai": codex(), "hours": HOURS}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    for k in ("claude", "openai"):
        print(f"{k:7} {data[k]['total_tokens']:>15,} tokens")


if __name__ == "__main__":
    main()
