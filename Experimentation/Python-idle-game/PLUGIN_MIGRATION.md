# Plugin System Migration - Idle Game

## Overview
This document describes the migration of the idle game from JSON-based character data to a plugin-based system matching the backend architecture.

## Changes Made

### 1. Plugin Loader (`idle_game/plugins/plugin_loader.py`)
- Created a simplified version of the backend's plugin loader
- Discovers and registers plugins from a directory
- Uses Python's `importlib` to dynamically load plugin modules
- Maintains a registry of plugins by category

### 2. Character Base Class (`idle_game/plugins/characters/_base.py`)
- Created `IdleCharacter` dataclass as the base for all character plugins
- Provides standard attributes: id, name, stats, lore, etc.
- Includes `to_dict()` method to convert to the format expected by game state
- Simpler than backend's `PlayerBase` - no complex combat logic needed

### 3. Character Plugins (`idle_game/plugins/characters/*.py`)
- Generated 23 character plugins from backend character definitions
- Each plugin is a dataclass that inherits from `IdleCharacter`
- Contains all character data: stats, damage type, abilities, UI info
- Character data is now in Python code instead of JSON

### 4. Updated Game State (`idle_game/core/game_state.py`)
- Modified `load_characters()` to use plugin loader instead of JSON
- Added import for `PluginLoader`
- Plugin-based loading provides same data format as before
- Maintains backward compatibility with save files

### 5. Plugin Generator Script (`idle_game/scripts/generate_plugins.py`)
- Tool to generate idle game character plugins from backend plugins
- Parses backend character files using AST
- Extracts relevant data and generates simplified plugins
- Can be run to update plugins when backend characters change

### 6. Test Scripts
- `test_plugins.py` - Verifies plugin loading and instantiation
- `test_game_state.py` - Verifies game state loads characters correctly

## Benefits

1. **Single Source of Truth**: Character data defined once in plugins, not duplicated in JSON
2. **Type Safety**: Python dataclasses provide better type checking than JSON
3. **Maintainability**: Easier to update character data in structured Python files
4. **Consistency**: Matches backend architecture pattern
5. **No Build Step**: No need to run extract script to generate JSON

## Backward Compatibility

- Save files continue to work unchanged
- Character data format in memory remains the same
- UI code doesn't need any modifications
- All existing game features work as before

## Testing

All functionality has been verified:
- ✓ 23 character plugins load successfully
- ✓ Characters instantiate correctly with all data
- ✓ GameState loads characters from plugins
- ✓ Character stats, runtime data, and randomization work
- ✓ Portrait loading and path resolution work
- ✓ All linting checks pass

## Usage

The plugin system is transparent to most code:

```python
# Game state automatically loads from plugins
game_state = GameState()
game_state.load_characters()  # Loads from plugins now!

# Characters work exactly as before
chars = game_state.characters
char = game_state.characters_map["ally"]
```

## Future Enhancements

Possible future improvements:
1. Hot-reload plugins without restarting
2. User-created character plugins
3. Plugin validation and error reporting
4. Plugin dependencies and conflicts resolution

## Files Modified

- `idle_game/core/game_state.py` - Updated character loading
- `idle_game/plugins/` - New plugin system (30 new files)
- `idle_game/scripts/` - New plugin generator and tests

## Files No Longer Needed

- `idle_game/data/characters.json` - No longer used (if existed)
- `idle_game/scripts/extract_data.py` - Still exists but not needed for runtime

## Conclusion

The idle game now uses a modern plugin-based architecture for character data, matching the backend's design. This provides better maintainability, type safety, and consistency across the codebase while maintaining full backward compatibility.
