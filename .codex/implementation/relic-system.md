# Relic System

Relics grant bonuses for the duration of a run, applying at run start and during battles.
New runs begin without relics or cards.
Each relic is implemented as a plugin under `plugins/relics/`, allowing new relics
to be added without touching core modules. Awarding the same relic multiple times stacks its effects for that run.

Each relic plugin exposes an `about` string and a `describe(stacks)` method so the
UI can show stack-aware, number-rich descriptions.

Plugins that subscribe to `BUS` events must unregister their handlers on
`battle_end` to avoid lingering callbacks between encounters.

## Testing
- `uv run pytest backend/tests/test_relic_awards.py`
- `uv run pytest backend/tests/test_relic_effects.py`
- `uv run pytest backend/tests/test_relic_effects_advanced.py`
