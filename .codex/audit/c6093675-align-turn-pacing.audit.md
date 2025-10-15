# Audit – Harmonize turn pacing defaults (adfe4d59)

## Summary
- Backend and frontend now share a 0.5 s default pacing constant, satisfying the alignment requirement. 【F:backend/autofighter/rooms/battle/pacing.py†L16-L57】【F:backend/routes/config.py†L21-L108】【F:frontend/src/lib/components/SettingsMenu.svelte†L25-L125】
- Intro banner pauses are capped and only triggered when a populated visual queue exists, replacing the previous `3 / TURN_PACING` sleep. 【F:backend/autofighter/rooms/battle/turn_loop/initialization.py†L117-L203】
- Regression coverage exercises the API defaults, intro pause helper, and frontend constant; however, no documentation update describes the new intro pacing policy, so the task is not ready to close. 【F:backend/tests/test_config_lrm.py†L63-L97】【F:backend/tests/test_turn_loop_initialization.py†L1-L116】【F:frontend/tests/settings-functionality-fixes.test.js†L1-L44】【5f64a8†L1-L2】

## Requirement review
1. **Align backend/API/UI defaults** – Complete. The backend constant, config route payload, and Svelte slider now share the same 0.5 default. 【F:backend/autofighter/rooms/battle/pacing.py†L16-L57】【F:backend/routes/config.py†L21-L108】【F:frontend/src/lib/components/SettingsMenu.svelte†L25-L125】
2. **Replace intro pause logic** – Complete. `_intro_pause_seconds` skips when no cinematic data is present, scales per combatant, and caps to 1.75 s before delegating to `pace_sleep`. 【F:backend/autofighter/rooms/battle/turn_loop/initialization.py†L117-L203】
3. **Regression coverage and documentation** – Partially complete. New backend/frontend tests assert the aligned defaults and intro pacing multiplier, but there is still no documentation entry explaining the revised intro pacing behavior in `.codex/implementation`. 【F:backend/tests/test_config_lrm.py†L63-L97】【F:backend/tests/test_turn_loop_initialization.py†L1-L116】【F:frontend/tests/settings-functionality-fixes.test.js†L1-L44】【5f64a8†L1-L2】

## Testing
- `uv run pytest tests/test_config_lrm.py tests/test_turn_loop_initialization.py` *(fails: Quart app raises `AttributeError` because `OptionKey` is missing `LRM_MODEL`/`TURN_PACING` attributes during request handling)* 【e49997†L1-L124】
