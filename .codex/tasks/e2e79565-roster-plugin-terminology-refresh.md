Coder, consolidate combatant plugins under a neutral "characters" namespace and retire the dedicated foes folder.

## Context
- Designers report confusion about why playable fighters live in `plugins/players` while adversaries live in `plugins/foes`, even though both inherit from similar base classes and share asset hooks.
- Gameplay planning wants a single entry point for modders who are adding new combatants regardless of allegiance.
- The roster reference in `.codex/implementation/player-foe-reference.md` and various loader utilities still talk about "players" vs. "foes" as folder names, so documentation and imports must be updated together.

## Requirements
- Replace the `backend/plugins/players` directory with a neutral name such as `characters` (coordinate the final label with design) and migrate all imports, plugin discovery, and registry wiring to the new path.
- Remove the top-level `backend/plugins/foes` package by folding any remaining foe-only helpers into the unified characters namespace or another appropriate module; ensure existing foe subclasses continue to register correctly.
- Update plugin loader logic, registry discovery, and any hard-coded file-system scans so they no longer assume separate `players`/`foes` folders.
- Refactor documentation, especially `.codex/implementation/player-foe-reference.md` and contributor guides in `.codex/instructions/`, to explain the new terminology and directory layout.
- Run backend unit tests and any plugin discovery smoke tests to confirm no regressions in battle generation or roster loading.
- Provide migration notes in the task PR describing how modders should update their custom plugins to the new folder structure.

## Notes
- Coordinate with any in-flight tasks touching asset registry or battle review features so terminology changes stay consistent across docs and UI strings.
