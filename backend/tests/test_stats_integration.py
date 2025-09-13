"""
Final integration test demonstrating the complete stats refactoring solution.

This test validates that the base stats vs runtime stats separation is working
correctly across all components of the system.
"""

import sys

sys.path.append('.')

from autofighter.effects import create_stat_buff
from autofighter.stat_effect import StatEffect
from autofighter.stats import Stats
from plugins.players._base import PlayerBase


def test_complete_stats_system():
    """Comprehensive test of the new stats system."""
    print('=== STATS REFACTORING INTEGRATION TEST ===\n')

    # Test 1: Basic Stats functionality
    print('1. Testing base Stats class:')
    stats = Stats()
    assert stats.get_base_stat("atk") == 200, "Base atk should be 200"
    assert stats.atk == 200, "Runtime atk should equal base initially"

    # Add effect
    effect = StatEffect('sword', {'atk': 25}, source='equipment')
    stats.add_effect(effect)
    assert stats.get_base_stat("atk") == 200, "Base atk should remain 200"
    assert stats.atk == 225, "Runtime atk should be base + effect"

    # Remove effect
    stats.remove_effect_by_name('sword')
    assert stats.atk == 200, "Runtime atk should return to base after removal"
    print('   ✓ Base vs runtime stats working correctly\n')

    # Test 2: PlayerBase functionality
    print('2. Testing PlayerBase class:')
    player = PlayerBase()

    # Test permanent base stat change (like leveling)
    original_base = player.get_base_stat('atk')
    player.modify_base_stat('atk', 10)
    assert player.get_base_stat('atk') == original_base + 10, "Base stat should be permanently modified"
    assert player.atk == original_base + 10, "Runtime should reflect base change"

    # Test temporary effect
    buff = StatEffect('battle_buff', {'atk': 15, 'max_hp': 50}, duration=3, source='spell')
    player.add_effect(buff)
    expected_atk = original_base + 10 + 15
    assert player.atk == expected_atk, f"Runtime atk should be {expected_atk}"
    assert player.get_base_stat('atk') == original_base + 10, "Base should not change from temporary effects"
    print('   ✓ Permanent vs temporary modifications working correctly\n')

    # Test 3: Effect system integration with StatModifier
    print('3. Testing StatModifier integration:')
    initial_effects = len(player.get_active_effects())
    modifier = create_stat_buff(player, name='weapon_enchant', atk=20, defense_mult=1.5)

    new_effects = len(player.get_active_effects())
    assert new_effects > initial_effects, "StatModifier should create effects"

    # Cleanup
    modifier.remove()
    player.remove_effect_by_name('battle_buff')
    final_atk = player.atk
    expected_final = original_base + 10  # Only permanent change should remain
    assert final_atk == expected_final, f"After cleanup, should have {expected_final} atk"
    print('   ✓ Effect cleanup working correctly\n')

    print('=== ALL INTEGRATION TESTS PASSED ===\n')
    print('🎉 STATS REFACTORING SUCCESSFULLY IMPLEMENTED! 🎉\n')

    return True


if __name__ == "__main__":
    test_complete_stats_system()
