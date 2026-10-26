"""
Mutation system - adds random modifiers to game encounters.
Part of the "Roguelike Chaos Expansion".
"""
import random
from typing import List, Dict, Any, Optional
from actions.base import Action
from utils.result_types import NoneResult
from utils.registry import register
from localization import t

class Mutation:
    """Base class for all gameplay mutations."""
    def __init__(self, id_str: str, name_key: str, desc_key: str):
        self.id_str = id_str
        self.name_key = name_key
        self.desc_key = desc_key

    def apply_to_enemies(self, enemies: List[Any]):
        """Apply mutation effects to enemies."""
        pass

    def apply_to_player(self, player: Any):
        """Apply persistent player-side effects.

        Mutations are deliberately stateful modifiers rather than relics, so the
        default is a no-op and individual mutations only opt into what they need.
        """
        pass

    def get_reward_multiplier(self) -> float:
        """Get reward multiplier for this mutation."""
        return 1.0

    def get_extra_relics(self) -> int:
        """Get number of extra relics awarded."""
        return 0

    @property
    def name(self) -> str:
        return t(self.name_key, default=self.id_str)

    @property
    def description(self) -> str:
        return t(self.desc_key, default="")

class ThickSkinMutation(Mutation):
    """Enemies have more HP but drop more relics."""
    def __init__(self):
        super().__init__("THICK_SKIN", "mutations.thick_skin.name", "mutations.thick_skin.desc")

    def apply_to_enemies(self, enemies: List[Any]):
        for enemy in enemies:
            enemy.max_hp = int(enemy.max_hp * 1.5)
            enemy.hp = enemy.max_hp

    def get_extra_relics(self) -> int:
        return 1

class FranticMutation(Mutation):
    """Enemies start with Strength but drop more gold."""
    def __init__(self):
        super().__init__("FRANTIC", "mutations.frantic.name", "mutations.frantic.desc")

    def apply_to_enemies(self, enemies: List[Any]):
        from powers.definitions.strength import StrengthPower
        for enemy in enemies:
            enemy.add_power(StrengthPower(amount=2))

    def get_reward_multiplier(self) -> float:
        return 2.0

class BlindingMutation(Mutation):
    """Player is weakened but gets a rare card choice."""
    def __init__(self):
        super().__init__("BLINDING", "mutations.blinding.name", "mutations.blinding.desc")

    def apply_to_player(self, player: Any):
        from powers.definitions.weak import WeakPower
        player.add_power(WeakPower(amount=2))
    
    # Logic handled in victory handler

# --- Cursed Relics (Roguelike Expansion) ---

class CursedRelic(Mutation):
    """A powerful relic with a significant drawback."""
    def __init__(self, id_str: str, name_key: str, desc_key: str):
        super().__init__(id_str, name_key, desc_key)

class DarkEnergyMutation(CursedRelic):
    """Gain 1 Energy per turn, but lose 2 Max HP every floor."""
    def __init__(self):
        super().__init__("DARK_ENERGY", "mutations.dark_energy.name", "mutations.dark_energy.desc")

    def apply_to_player(self, player: Any):
        # The player energy setter caps at max_energy, so increase the cap first.
        if not hasattr(player, "flags"):
            player.flags = {}
        player.max_energy += 1
        player.energy = player.max_energy
        player.flags["cursed_energy"] = True

class BloodSacrificeMutation(CursedRelic):
    """Gain 2 Strength at start of combat, but take 3 damage every turn."""
    def __init__(self):
        super().__init__("BLOOD_SACRIFICE", "mutations.blood_sacrifice.name", "mutations.blood_sacrifice.desc")

    def apply_to_player(self, player: Any):
        if not hasattr(player, "flags"):
            player.flags = {}
        player.flags["blood_sacrifice"] = True

class GreedMutation(CursedRelic):
    """Gain 50% more gold, but cards cost 1 more in shop."""
    def __init__(self):
        super().__init__("GREED_CURSE", "mutations.greed.name", "mutations.greed.desc")

    def apply_to_player(self, player: Any):
        if not hasattr(player, "flags"):
            player.flags = {}
        player.flags["cursed_greed"] = True

def get_cursed_relic_options(count: int = 3) -> List[CursedRelic]:
    """Get a list of cursed relic options for the Cursed Chest."""
    all_cursed = [DarkEnergyMutation(), BloodSacrificeMutation(), GreedMutation()]
    return random.sample(all_cursed, min(count, len(all_cursed)))

def get_random_elite_mutation() -> Optional[Mutation]:
    """Get a random mutation for an Elite room."""
    mutations = [ThickSkinMutation(), FranticMutation(), BlindingMutation()]
    return random.choice(mutations) if random.random() < 0.4 else None

@register("action")
class ApplyMutationAction(Action):
    """Permanently apply a mutation/cursed relic to the player."""
    def __init__(self, mutation: Mutation):
        self.mutation = mutation

    def execute(self) -> NoneResult:
        from engine.game_state import game_state
        if game_state.player:
            # Add to player's active mutations list (need to ensure this exists)
            if not hasattr(game_state.player, "active_mutations"):
                game_state.player.active_mutations = []
            
            game_state.player.active_mutations.append(self.mutation)
            # Keep a single instance in the run state so its effect survives rooms.
            self.mutation.apply_to_player(game_state.player)
            print(f"[Chaos] Applied Mutation: {self.mutation.name}")
        return NoneResult()
