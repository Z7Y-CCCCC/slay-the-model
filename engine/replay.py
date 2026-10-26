"""Replay code helpers for sharing run setup."""

from __future__ import annotations

import base64
import json
from datetime import date
from typing import Dict, Any


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64_decode(token: str) -> bytes:
    padding = "=" * ((4 - len(token) % 4) % 4)
    return base64.urlsafe_b64decode((token + padding).encode("ascii"))


def encode_replay_code(settings: Dict[str, Any]) -> str:
    payload = json.dumps(settings, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _b64_encode(payload)


def decode_replay_code(code: str) -> Dict[str, Any]:
    raw = _b64_decode(code)
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Replay payload is invalid.")
    return data


def build_replay_settings_from_state(game_state) -> Dict[str, Any]:
    return {
        "seed": int(game_state.config.seed),
        "character": str(game_state.config.character),
        "ascension": int(game_state.ascension),
        "mode": str(game_state.config.mode),
        "daily": bool(getattr(game_state, "daily_mode", False)),
        "day": date.today().isoformat(),
        "v": 1,
    }


def apply_replay_settings(game_state, settings: Dict[str, Any]):
    if "seed" in settings:
        game_state.config.seed = int(settings["seed"])
    if "character" in settings:
        game_state.config.character = str(settings["character"])
    if "ascension" in settings:
        game_state.config.ascension = int(settings["ascension"])
        game_state.ascension = int(settings["ascension"])
    if "mode" in settings and settings["mode"] in {"human", "ai", "debug"}:
        game_state.config.mode = settings["mode"]
    if "daily" in settings:
        game_state.daily_mode = bool(settings["daily"])
