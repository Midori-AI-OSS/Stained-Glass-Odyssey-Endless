"""Test script to verify game state loads characters from plugins."""
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Mock Qt BEFORE importing anything that uses it
from unittest.mock import MagicMock


# Create proper mock classes
class MockQObject:
    def __init__(self, *args, **kwargs):
        pass

class MockSignal:
    def __init__(self, *args):
        pass
    def emit(self, *args):
        pass
    def connect(self, *args):
        pass

class MockQTimer:
    def __init__(self):
        self.timeout = MockSignal()
    def start(self, *args):
        pass

mock_qt_core = MagicMock()
mock_qt_core.QObject = MockQObject
mock_qt_core.Signal = MockSignal
mock_qt_core.QTimer = MockQTimer

sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtCore'] = mock_qt_core
sys.modules['PySide6.QtWidgets'] = MagicMock()

from idle_game.core.game_state import GameState


def main():
    """Test game state character loading."""
    print("Testing GameState character loading from plugins...")

    # Create game state
    game_state = GameState()

    # Load characters
    print("\nLoading characters...")

    # Check if plugins directory exists
    plugins_path = Path(__file__).parent.parent / "plugins" / "characters"
    print(f"Plugins path: {plugins_path}")
    print(f"Plugins path exists: {plugins_path.exists()}")

    game_state.load_characters()

    # Verify characters loaded
    print(f"Loaded {len(game_state.characters)} characters")

    if not game_state.characters:
        print("✗ ERROR: No characters loaded!")
        return 1

    # Display some character info
    print("\nFirst 5 characters:")
    for char in game_state.characters[:5]:
        print(f"  - {char['id']}: {char['name']} (Type: {char['char_type']}, Rarity: {char['gacha_rarity']})")
        print(f"    Damage Type: {char['damage_type']}")
        print(f"    Level: {char['runtime']['level']}, HP: {char['runtime']['hp']}/{char['runtime']['max_hp']}")

    # Verify character map
    print(f"\nCharacter map has {len(game_state.characters_map)} entries")

    # Test accessing a specific character
    if "ally" in game_state.characters_map:
        ally = game_state.characters_map["ally"]
        print("\nTest character 'ally':")
        print(f"  Name: {ally['name']}")
        print(f"  Type: {ally['char_type']}")
        print(f"  Base ATK: {ally['base_stats']['atk']}")
        print(f"  Base Defense: {ally['base_stats']['defense']}")

    print("\n✓ All game state tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
