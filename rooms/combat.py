"""
Combat room implementation - manages Combat instance execution.
"""
from typing import TYPE_CHECKING, List

from actions.base import Action
from actions.display import DisplayTextAction
from utils.result_types import MultipleActionsResult, NoneResult
from actions.reward import AddGoldAction, AddRandomPotionAction, AddRandomRelicAction
from actions.card import AddRandomCardAction, ChooseAddRandomCardAction, ChooseObtainCardAction
from utils.result_types import GameStateResult
from engine.combat import Combat
from rooms.base import Room, BaseResult
from utils.registry import register
from utils.types import RoomType, RarityType, CardType, CombatType
from tui.print_utils import tui_print

@register("room")
class CombatRoom(Room):
    """Combat room - manages the creation and execution of Combat"""

    def __init__(self, enemies=None, room_type=RoomType.MONSTER, encounter_name: str = "", **kwargs):
        super().__init__(**kwargs)
        self.room_type = room_type
        self.enemies = enemies or []
        self.encounter_name = encounter_name  # Track encounter name for history
        self.combat = None
        self.mutation = None  # Current active mutation
    
    def init(self):
        """Initialize the combat instance"""
        from engine.game_state import game_state

        if (
            self.room_type == RoomType.ELITE
            and game_state.player is not None
        ):
            # Try to get a mutation for Elite fights (Chaos Expansion)
            from engine.mutations import get_random_elite_mutation
            self.mutation = get_random_elite_mutation()
            if self.mutation:
                self.mutation.apply_to_enemies(self.enemies)
                tui_print(
                    f"[Elite Affix] {self.mutation.name}: {self.mutation.description}"
                )

            for relic in game_state.player.relics:
                if getattr(relic, "idstr", None) == "PreservedInsect":
                    if hasattr(relic, "apply_elite_hp_reduction"):
                        relic.apply_elite_hp_reduction(self.enemies)
                    break

        # Determine combat type based on room type
        combat_type = CombatType.BOSS if self.room_type == RoomType.BOSS else CombatType.ELITE if self.room_type == RoomType.ELITE else CombatType.NORMAL
        
        self.combat = Combat(
            enemies=self.enemies,
            combat_type=combat_type,
            mutation=self.mutation,
        )
    
    def enter(self) -> BaseResult:
        """Enter combat room and execute combat"""
        from engine.game_state import game_state
        actions = []

        # Display room entry message
        if self.room_type == RoomType.BOSS:
            actions.append(DisplayTextAction(text_key="rooms.combat.boss_enter"))
        elif self.room_type == RoomType.ELITE:
            actions.append(DisplayTextAction(text_key="rooms.combat.elite_enter"))
        else:
            actions.append(DisplayTextAction(text_key="rooms.combat.enter"))

        # Execute combat
        assert self.combat is not None
        result = self.combat.start()
        
        # Handle combat result
        if result.state == "COMBAT_WIN":
            victory_actions = self._handle_victory()
            if victory_actions:
                actions.extend(victory_actions)
        # ESCAPE：没有reward
        
        if result.state == "GAME_LOSE":
            return result
        else:
            if actions:
                return MultipleActionsResult(actions)
            return NoneResult()
    
    def leave(self):
        """Leave the combat room"""
        super().leave()
        # Clean up combat state
        if self.combat:
            self.combat = None
    
    def _handle_victory(self) -> List['Action']:
        """Handle combat victory - add rewards"""
        from engine.game_state import game_state
        from actions.misc import _has_relic
        actions = []
        
        # Display victory message
        actions.append(DisplayTextAction(text_key="rooms.combat.victory"))

        # Increment normal encounter counter and track history (only for normal monsters, not elites/bosses)
        if self.room_type == RoomType.MONSTER:
            game_state.normal_encounters_fought += 1
            if self.encounter_name:
                game_state.encounter_history.append(self.encounter_name)

        # Track elite history
        if self.room_type == RoomType.ELITE:
            if self.encounter_name:
                game_state.elite_history.append(self.encounter_name)
            # Trigger elite victory hooks for relics (e.g., BlackStar)
            for relic in game_state.player.relics:
                elite_actions = relic.on_elite_victory(
                    player=game_state.player,
                    entities=[]
                )
                actions.extend(elite_actions)

        # Act 3/4 boss combats should not grant combat rewards.
        if (
            self.room_type == RoomType.BOSS
            and game_state.current_act in (3, 4)
        ):
            return actions

        # Calculate gold reward
        gold_amount = self._calculate_gold_reward()
        if gold_amount > 0:
            actions.append(AddGoldAction(amount=gold_amount))

        # Add card reward (non-boss)
        if self.room_type != RoomType.BOSS:
            reward_options = 1 if _has_relic("Busted Crown", game_state) else 3

            
            # Check for PrayerWheel - adds extra card reward for normal enemies
            combat_type_str = "normal" if self.combat.combat_type == CombatType.NORMAL else "elite"
            for relic in game_state.player.relics:
                if hasattr(relic, "modify_card_reward_count"):
                    reward_options = relic.modify_card_reward_count(reward_options, combat_type_str)
            
            # 3 choose 1, rarity determined by encounter type
            # 3 choose 1, rarity determined by encounter type
            # Chaos: Handle extra card reward if applicable (Blinding)
            obtain_count = 1
            if self.mutation and self.mutation.id_str == "BLINDING":
                obtain_count = 2

            actions.append(ChooseObtainCardAction(
                total=reward_options,
                namespace=game_state.player.namespace,
                encounter_type=combat_type_str,
                use_rolling_offset=True,
                allow_upgraded=True,
                count=obtain_count # Support multi-pick if blinding
            ))

            # Thick Skin is a meaningful risk/reward choice: the elite also
            # pays out an extra common relic when the fight is cleared.
            if self.mutation:
                for _ in range(self.mutation.get_extra_relics()):
                    actions.append(AddRandomRelicAction(rarity=RarityType.COMMON))
        else:  # boss - 3 rare cards
            actions.append(ChooseAddRandomCardAction(
                pile='deck',
                total=3,
                namespace=game_state.player.namespace,
                rarity=RarityType.RARE
            ))

        # Add potion reward with probability check
        # Base 40% chance, -10% after drop, +10% after no drop
        # White Beast Statue: always drop
        if _has_relic("White Beast Statue", game_state):
            # Always drop with White Beast Statue
            actions.append(AddRandomPotionAction(
                character=game_state.player.character
            ))
            game_state.potion_drop_chance = max(10, game_state.potion_drop_chance - 10)
        else:
            import random as rd
            if rd.randint(1, 100) <= game_state.potion_drop_chance:
                actions.append(AddRandomPotionAction(
                    character=game_state.player.character
                ))
                game_state.potion_drop_chance = max(10, game_state.potion_drop_chance - 10)
            else:
                game_state.potion_drop_chance = min(90, game_state.potion_drop_chance + 10)

        return actions
    
    def _calculate_gold_reward(self) -> int:
        """
        Calculate gold reward based on enemy difficulty.
        
        Returns:
            Gold amount to award
        
        Normal enemy gold with random fluctuation: 10-20
        Elite enemy gold with random fluctuation: 25-35
        Boss gold with random fluctuation: 95-105
        """
        import random as rd

        if self.room_type == RoomType.BOSS:
            return rd.randint(95, 105)
        elif self.room_type == RoomType.ELITE:
            return rd.randint(25, 35)
        else:
            gold = rd.randint(10, 20)
        
        # Scale for Mutation
        if self.mutation:
            gold = int(gold * self.mutation.get_reward_multiplier())
        return gold
