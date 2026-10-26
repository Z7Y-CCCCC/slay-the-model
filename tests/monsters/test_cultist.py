"""
Test suite for Cultist enemy - Common enemy with Ritual+Attack pattern.

Cultist:
- HP range: 40-44
- Intentions: Ritual (first turn), then Attack
- Common enemy type
"""

import unittest
from enemies.act1.cultist import Cultist
from enemies.act1.cultist_intentions import CultistRitualIntention, CultistAttackIntention
from tests.test_combat_utils import CombatTestHelper


class TestCultist(unittest.TestCase):
    """Test Cultist enemy mechanics"""

    def setUp(self):
        """Set up test fixtures"""
        self.helper = CombatTestHelper()

    def tearDown(self):
        """Clean up after tests"""
        self.helper._reset_game_state()

    def test_cultist_basic_properties(self):
        """Test Cultist has correct basic properties"""
        from utils.types import EnemyType
        
        cultist = Cultist()
        
        # Check name
        self.assertEqual(cultist.idstr, "Cultist")
        
        # Check HP range
        self.assertGreaterEqual(cultist.hp, 48)
        self.assertLessEqual(cultist.hp, 54)
        self.assertEqual(cultist.hp, cultist.max_hp)
        
        # Check type
        self.assertEqual(cultist.enemy_type, EnemyType.NORMAL)

    def test_cultist_has_intentions(self):
        """Test Cultist has registered intentions"""
        cultist = Cultist()
        
        # Check intentions are registered
        self.assertIn("ritual", cultist.intentions)
        self.assertIn("attack", cultist.intentions)
        
        # Check intention types
        self.assertIsInstance(cultist.intentions["ritual"], CultistRitualIntention)
        self.assertIsInstance(cultist.intentions["attack"], CultistAttackIntention)

    def test_cultist_hp_in_range(self):
        """Test Cultist HP is always within expected range"""
        # Create multiple Cultists to test HP range
        hps = []
        for i in range(10):
            cultist = Cultist()
            hps.append(cultist.hp)
        
        # All HPs should be 48-54
        for hp in hps:
            self.assertGreaterEqual(hp, 48)
            self.assertLessEqual(hp, 54)


if __name__ == '__main__':
    unittest.main()
