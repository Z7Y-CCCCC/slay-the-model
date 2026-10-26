"""Pytest shared configuration for stable test environment."""

import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.game_config import GameConfig
from localization import set_language


@pytest.fixture(autouse=True)
def force_english_localization(monkeypatch):
    """Keep test outputs stable regardless of local config language."""
    original_load = GameConfig.load

    def load_with_english(config_path):
        config = original_load(config_path)
        config.language = "en"
        return config

    monkeypatch.setattr(GameConfig, "load", staticmethod(load_with_english))
    set_language("en")
    yield
    set_language("en")
