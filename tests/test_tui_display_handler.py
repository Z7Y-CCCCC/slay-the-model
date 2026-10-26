from rich.columns import Columns
from rich.panel import Panel

from tui.handlers.display_handler import DisplayHandler


class _ResolvedText:
    def __init__(self, value: str):
        self._value = value

    def resolve(self) -> str:
        return self._value


class _Localizable:
    def __init__(self, name: str):
        self.name = name

    def local(self, field: str):
        if field == "name":
            return _ResolvedText(self.name)
        raise KeyError(field)


class _DummyPower(_Localizable):
    def __init__(self, name: str, amount: int):
        super().__init__(name)
        self.amount = amount


class _DummyIntent:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = _ResolvedText(description)


class _DummyEnemy(_Localizable):
    def __init__(self):
        super().__init__("Test Enemy")
        self.hp = 22
        self.max_hp = 30
        self.block = 3
        self.current_intention = _DummyIntent("stab", "Attack for 6")
        self.powers = [_DummyPower("Strength", 2)]

    def is_dead(self) -> bool:
        return False


class _PlainEnemy:
    """Enemy without local()/resolve() to validate fallback code paths."""

    def __init__(self):
        self.name = "Plain Enemy"
        self.hp = 7
        self.max_hp = 10
        self.block = 0
        self.current_intention = None
        self.powers = []

    def is_dead(self) -> bool:
        return False


class _CardType:
    def __init__(self, name: str):
        self.name = name


class _DummyCard(_Localizable):
    def __init__(self, name: str, cost: int, card_type: str, desc: str):
        super().__init__(name)
        self.cost = cost
        self.card_type = _CardType(card_type)
        self.description = _ResolvedText(desc)


class _PlainCard:
    def __init__(self):
        self.cost = None
        self.card_type = None
        self.description = None


class _DummyCardManager:
    def __init__(self, hand):
        self._piles = {
            "hand": list(hand),
            "draw_pile": [],
            "discard_pile": [],
            "exhaust_pile": [],
        }

    def get_pile(self, name):
        return self._piles.get(name, [])


class _DummyPlayer:
    def __init__(self, hand):
        self.hp = 50
        self.max_hp = 70
        self.block = 0
        self.energy = 3
        self.max_energy = 3
        self.powers = [_DummyPower("Dexterity", 1)]
        self.card_manager = _DummyCardManager(hand)


class _DummyGameState:
    def __init__(self, hand):
        self.player = _DummyPlayer(hand)


class _DummyCombat:
    def __init__(self, enemies):
        self.enemies = enemies


class _DummyApp:
    def __init__(self):
        self.room_type = None
        self.content = None
        self.player_info_calls = 0

    def set_room_type(self, room_type: str):
        self.room_type = room_type

    def update_display_content(self, content):
        self.content = content

    def update_player_info(self, player, gs):
        self.player_info_calls += 1


def test_display_combat_renders_without_name_errors():
    app = _DummyApp()
    handler = DisplayHandler(app)
    gs = _DummyGameState([_DummyCard("Strike", 1, "ATTACK", "Deal 6 damage.")])
    combat = _DummyCombat([_DummyEnemy()])

    handler.display_combat(combat, gs)

    assert app.room_type == "CombatRoom"
    assert isinstance(app.content, list)
    assert any(isinstance(item, Panel) for item in app.content)
    assert any(isinstance(item, Columns) for item in app.content)
    assert app.player_info_calls == 1


def test_display_combat_fallback_paths_do_not_crash():
    app = _DummyApp()
    handler = DisplayHandler(app)
    gs = _DummyGameState([_PlainCard()])
    combat = _DummyCombat([_PlainEnemy()])

    handler.display_combat(combat, gs)

    assert app.room_type == "CombatRoom"
    assert isinstance(app.content, list)
    assert app.player_info_calls == 1


def test_display_combat_escapes_markup_sensitive_text():
    app = _DummyApp()
    handler = DisplayHandler(app)
    weird_card = _DummyCard("Strike [X]", 1, "ATTACK", "Deal [6] damage and apply [Weak].")
    gs = _DummyGameState([weird_card])
    enemy = _DummyEnemy()
    enemy.current_intention = _DummyIntent("attack", "Attack [for 6]")
    combat = _DummyCombat([enemy])

    handler.display_combat(combat, gs)

    assert app.room_type == "CombatRoom"
    assert isinstance(app.content, list)
