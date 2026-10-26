from datetime import date

from engine.daily_challenge import (
    format_daily_leaderboard,
    get_daily_seed,
    record_daily_result,
)
from engine.replay import decode_replay_code, encode_replay_code


def test_daily_seed_is_deterministic_per_day():
    day_a = date(2026, 3, 2)
    day_b = date(2026, 3, 3)
    assert get_daily_seed(day_a) == get_daily_seed(day_a)
    assert get_daily_seed(day_a) != get_daily_seed(day_b)


def test_replay_code_roundtrip():
    payload = {
        "seed": 123456,
        "character": "Ironclad",
        "ascension": 5,
        "mode": "human",
        "daily": False,
        "day": "2026-03-02",
        "v": 1,
    }
    code = encode_replay_code(payload)
    assert decode_replay_code(code) == payload


def test_daily_leaderboard_record_and_sort(tmp_path):
    leaderboard_path = tmp_path / "leaderboard.json"

    record_daily_result(
        {
            "day": "2026-03-02",
            "won": False,
            "floor": 12,
            "character": "Ironclad",
            "challenge_tokens": 0,
            "hp_left": 0,
        },
        path=str(leaderboard_path),
    )
    record_daily_result(
        {
            "day": "2026-03-02",
            "won": True,
            "floor": 12,
            "character": "Ironclad",
            "challenge_tokens": 1,
            "hp_left": 20,
        },
        path=str(leaderboard_path),
    )

    board_text = format_daily_leaderboard(
        day="2026-03-02",
        path=str(leaderboard_path),
    )
    lines = board_text.splitlines()
    assert lines[1].startswith("1. Ironclad | WIN")
