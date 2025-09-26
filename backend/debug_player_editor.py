#!/usr/bin/env python3
"""
Player Editor Debug Script

This script helps verify that the player editor customization system is working correctly.
Run this script to test the player customization logic without needing the full backend.
"""

import os
import sys

# Add the backend directory to the path so we can import modules
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def test_customization_calculation():
    """Test the customization calculation logic."""
    print("=== Testing Player Customization Calculation ===")

    # User's reported settings: hp=60, attack=20, defense=20
    test_settings = {"hp": 60, "attack": 20, "defense": 20}

    # Calculate multipliers (same logic as _apply_player_customization)
    multipliers = {
        "max_hp_mult": 1 + test_settings.get("hp", 0) * 0.01,
        "atk_mult": 1 + test_settings.get("attack", 0) * 0.01,
        "defense_mult": 1 + test_settings.get("defense", 0) * 0.01,
    }

    # Base player stats (from plugins/characters/_base.py)
    base_stats = {
        "max_hp": 1000,
        "atk": 100,
        "defense": 50,
    }

    # Calculate expected final stats
    expected_stats = {
        "max_hp": int(base_stats["max_hp"] * multipliers["max_hp_mult"]),
        "atk": int(base_stats["atk"] * multipliers["atk_mult"]),
        "defense": int(base_stats["defense"] * multipliers["defense_mult"]),
    }

    print(f"User settings: {test_settings}")
    print(f"Base stats: {base_stats}")
    print(f"Calculated multipliers: {multipliers}")
    print(f"Expected final stats: {expected_stats}")

    # Check if multipliers would trigger early return
    all_one = all(v == 1 for v in multipliers.values())
    print(f"All multipliers are 1 (would cause early return): {all_one}")

    return expected_stats

def print_instructions():
    """Print instructions for the user on how to verify the system is working."""
    print("\n=== How to Verify Player Editor is Working ===")
    print()
    print("1. **Set your player customization:**")
    print("   - Use the player editor interface in the frontend")
    print("   - Or make a PUT request to /player/editor with your desired stats")
    print()
    print("2. **Check the backend logs:**")
    print("   - Look for debug messages starting with 'Updating player editor'")
    print("   - Look for 'Applying player customization' messages")
    print("   - Look for 'Player stats endpoint' messages")
    print()
    print("3. **Verify stats are applied:**")
    print("   - Make a GET request to /player/stats")
    print("   - Check the 'core' section for hp/max_hp")
    print("   - Check the 'offense' section for atk")
    print("   - Check the 'defense' section for defense")
    print()
    print("4. **Expected values for hp=60, attack=20, defense=20:**")
    expected = test_customization_calculation()
    print(f"   - max_hp should be: {expected['max_hp']}")
    print(f"   - atk should be: {expected['atk']}")
    print(f"   - defense should be: {expected['defense']}")
    print()
    print("5. **If stats don't match, check:**")
    print("   - Database permissions and corruption")
    print("   - Frontend is calling the correct backend endpoints")
    print("   - You're looking at backend stats, not legacy game stats")
    print("   - Browser cache - try hard refresh (Ctrl+F5)")

if __name__ == "__main__":
    print("Player Editor Debug Tool")
    print("=" * 50)

    test_customization_calculation()
    print_instructions()
