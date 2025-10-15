# Audit – Harmonize turn pacing defaults (adfe4d59)

## Summary
- Backend and frontend now share a 0.5 s default pacing constant, satisfying the alignment requirement. 【F:backend/autofighter/rooms/battle/pacing.py†L16-L57】【F:backend/routes/config.py†L21-L108】【F:frontend/src/lib/components/SettingsMenu.svelte†L25-L125】
- Intro banner pauses are capped and only triggered when a populated visual queue exists, replacing the previous `3 / TURN_PACING` sleep. 【F:backend/autofighter/rooms/battle/turn_loop/initialization.py†L117-L203】
- Backend test scaffolding now defines the OptionKey values, exposes ModelName choices, and replaces heavyweight `runs`, `rich`, and logging dependencies so the config suite can import the app without real services. 【F:backend/tests/conftest.py†L170-L344】
- Battle room implementation notes document the shared 0.5 s pacing default and intro delay cap, and the task record has been escalated to the Task Master. 【F:.codex/implementation/battle-room.md†L1-L60】【F:.codex/tasks/adfe4d59-align-turn-pacing-defaults.md†L16-L17】

## Requirement review
1. **Align backend/API/UI defaults** – Complete. The backend constant, config route payload, and Svelte slider now share the same 0.5 default. 【F:backend/autofighter/rooms/battle/pacing.py†L16-L57】【F:backend/routes/config.py†L21-L108】【F:frontend/src/lib/components/SettingsMenu.svelte†L25-L125】
2. **Replace intro pause logic** – Complete. `_intro_pause_seconds` skips when no cinematic data is present, scales per combatant, and caps to 1.75 s before delegating to `pace_sleep`. 【F:backend/autofighter/rooms/battle/turn_loop/initialization.py†L117-L203】
3. **Regression coverage and documentation** – Complete. The backend tests run with the expanded stubs, the intro pacing behavior is documented for Battle Rooms, and the task log now requests Task Master review. 【F:backend/tests/conftest.py†L170-L344】【F:.codex/implementation/battle-room.md†L1-L60】【F:.codex/tasks/adfe4d59-align-turn-pacing-defaults.md†L16-L17】

## Testing
- `uv run pytest tests/test_config_lrm.py tests/test_turn_loop_initialization.py` 【37b5b2†L1-L4】
