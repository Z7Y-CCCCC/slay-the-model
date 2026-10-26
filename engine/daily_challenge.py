"""Daily challenge seed + local leaderboard helpers."""

from __future__ import annotations

from datetime import date
import hashlib
import json
import os
from typing import Dict, List, Any


_DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data")
)
DEFAULT_LEADERBOARD_PATH = os.path.join(_DATA_DIR, "daily_leaderboard.json")


def get_daily_label(day: date | None = None) -> str:
    target = day or date.today()
    return target.isoformat()


def get_daily_seed(day: date | None = None) -> int:
    """Generate a deterministic daily seed from date."""
    label = get_daily_label(day)
    digest = hashlib.sha256(f"slay-the-model:{label}".encode("utf-8")).hexdigest()
    # Keep in signed 32-bit range used by current seed flows.
    return int(digest[:8], 16) & 0x7FFFFFFF


def _ensure_data_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def load_leaderboard(path: str = DEFAULT_LEADERBOARD_PATH) -> Dict[str, List[Dict[str, Any]]]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _score_entry(entry: Dict[str, Any]) -> int:
    floor = int(entry.get("floor", 0))
    tokens = int(entry.get("challenge_tokens", 0))
    won = bool(entry.get("won", False))
    hp_left = int(entry.get("hp_left", 0))
    return floor * 100 + tokens * 25 + hp_left + (1000 if won else 0)


def record_daily_result(
    entry: Dict[str, Any],
    path: str = DEFAULT_LEADERBOARD_PATH,
) -> Dict[str, List[Dict[str, Any]]]:
    """Append result to local daily leaderboard and return updated board."""
    _ensure_data_dir()
    board = load_leaderboard(path)

    day = str(entry.get("day") or get_daily_label())
    day_rows = board.get(day, [])
    day_rows.append(entry)
    day_rows.sort(key=_score_entry, reverse=True)
    board[day] = day_rows[:50]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(board, f, ensure_ascii=False, indent=2)
    return board


def format_daily_leaderboard(
    day: str | None = None,
    limit: int = 10,
    path: str = DEFAULT_LEADERBOARD_PATH,
) -> str:
    board = load_leaderboard(path)
    target_day = day or get_daily_label()
    rows = board.get(target_day, [])
    if not rows:
        return f"Daily leaderboard ({target_day}) is empty."

    lines = [f"Daily leaderboard ({target_day})"]
    for idx, row in enumerate(rows[:limit], start=1):
        outcome = "WIN" if row.get("won") else "LOSE"
        character = row.get("character", "Unknown")
        floor = row.get("floor", 0)
        tokens = row.get("challenge_tokens", 0)
        score = _score_entry(row)
        lines.append(
            f"{idx}. {character} | {outcome} | floor {floor} | tokens {tokens} | score {score}"
        )
    return "\n".join(lines)
