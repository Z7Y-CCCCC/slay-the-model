"""
Base room definitions for new architecture.
Rooms use global action queue and lifecycle management.
"""
from actions.base import Action, ActionQueue
from actions.map_selection import SelectMapNodeAction
from utils.result_types import BaseResult
from localization import Localizable
from utils.types import RoomType


class Room(Localizable):
    """Base room class - represents a location where events occur
    
    Rooms use the global action queue for action management.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        
        # Control flag for leaving room
        self.should_leave = False
        
        # Room type tracking
        self.room_type = None
        
        # Action queue for room actions
        self.action_queue = ActionQueue()
    
    def init(self):
        """
        Initialize the room - called before enter().
        
        Subclasses should override this method to perform
        room-specific initialization (e.g., generating items, enemies).
        """
        pass
    
    def enter(self) -> BaseResult:
        """
        Enter room and execute room logic.

        This method should implement room's main logic loop,
        building and executing actions as needed.

        Returns:
            Execution result: NoneResult()/"DEATH"/"WIN"
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement enter()")
    
    def leave(self):
        """
        Leave room - perform cleanup.

        Called when player exits the room.
        Clears the global action queue and prepares for next room.
        """
        from engine.game_state import game_state
        
        # Clear global action queue
        game_state.action_queue.clear()

        # Clear event stack in game state
        game_state.event_stack.clear()

        # Reset leave flag
        self.should_leave = False

class MysteryRoom(Room):
    """
    A special room that transforms into another room type upon entry.
    Part of the "Roguelike Chaos Expansion".
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.room_type = RoomType.EVENT # Shows as Event on map
    
    def enter(self) -> BaseResult:
        import random
        from engine.game_state import game_state
        from rooms.combat import CombatRoom
        from rooms.shop import ShopRoom
        from rooms.treasure import TreasureRoom
        from rooms.rest import RestRoom
        
        # Weighted transformation
        roll = random.random()
        if roll < 0.10: # 10% Shop
            transformed_room = ShopRoom(**self.kwargs)
        elif roll < 0.20: # 10% Treasure
            transformed_room = TreasureRoom(**self.kwargs)
        elif roll < 0.35: # 15% Elite Combat
            transformed_room = CombatRoom(room_type=RoomType.ELITE, **self.kwargs)
        elif roll < 0.50: # 15% Rest
            transformed_room = RestRoom(**self.kwargs)
        else: # 50% Event
            from rooms.event import EventRoom
            transformed_room = EventRoom(**self.kwargs)
        
        print(f"[Chaos] Mystery Room transformed into {type(transformed_room).__name__}!")
        transformed_room.init()
        return transformed_room.enter()
