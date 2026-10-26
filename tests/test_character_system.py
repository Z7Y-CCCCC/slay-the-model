"""Tests for character configuration and player factory behavior."""

import pytest

from player.player_factory import create_player, list_characters


def test_list_characters():
    characters = list_characters()
    assert len(characters) > 0


def test_create_ironclad():
    player = create_player("Ironclad")

    relic_names = [r.__class__.__name__ for r in player.relics]

    assert player.character == "Ironclad"
    assert player.max_hp == 80
    assert player.energy == 3
    assert player.gold == 99
    assert player.namespace == "ironclad"
    assert player.base_draw_count == 5
    assert len(player.card_manager.deck) == 10
    assert len(player.relics) == 1
    assert "BurningBlood" in relic_names


def test_create_silent():
    try:
        player = create_player("Silent")
    except ValueError as exc:
        if "may not be fully implemented" in str(exc):
            pytest.skip("Silent character cards are not fully implemented yet")
        raise

    assert player.character == "Silent"
    assert player.max_hp == 70
    assert player.energy == 3
    assert player.gold == 99
    assert player.namespace == "silent"
    assert player.base_draw_count == 5
    assert len(player.card_manager.deck) == 10
    assert len(player.relics) == 1


@pytest.mark.parametrize("character_name", ["Ironclad", "ironclad", "IRONCLAD"])
def test_case_insensitive(character_name):
    player = create_player(character_name)
    assert player.character == "Ironclad"


def test_unknown_character():
    with pytest.raises(ValueError):
        create_player("NonExistentCharacter")
