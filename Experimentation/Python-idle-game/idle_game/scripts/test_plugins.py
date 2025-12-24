"""Test script to verify plugin loading works."""
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from idle_game.plugins.plugin_loader import PluginLoader


def main():
    """Test plugin loading."""
    plugins_path = Path(__file__).parent.parent / "plugins" / "characters"

    print(f"Loading plugins from: {plugins_path}")
    print(f"Path exists: {plugins_path.exists()}")

    if not plugins_path.exists():
        print("ERROR: Plugins directory does not exist!")
        return 1

    # Initialize plugin loader
    loader = PluginLoader()
    loader.discover(str(plugins_path))

    # Get character plugins
    character_plugins = loader.get_plugins("character")

    print(f"\nLoaded {len(character_plugins)} character plugins:")
    for plugin_id, plugin_class in sorted(character_plugins.items()):
        print(f"  - {plugin_id}: {plugin_class.__name__}")

    # Test instantiating one character
    if character_plugins:
        test_id = list(character_plugins.keys())[0]
        test_class = character_plugins[test_id]
        print(f"\nTesting instantiation of {test_id}...")
        try:
            instance = test_class()
            char_dict = instance.to_dict()
            print(f"  ID: {char_dict['id']}")
            print(f"  Name: {char_dict['name']}")
            print(f"  Type: {char_dict['char_type']}")
            print(f"  Rarity: {char_dict['gacha_rarity']}")
            print(f"  Damage Type: {char_dict['damage_type']}")
            print(f"  Max HP: {char_dict['base_stats']['max_hp']}")
            print("  ✓ Character instantiation successful!")
        except Exception as e:
            print(f"  ✗ Error instantiating character: {e}")
            import traceback
            traceback.print_exc()
            return 1

    print("\n✓ All plugin tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
