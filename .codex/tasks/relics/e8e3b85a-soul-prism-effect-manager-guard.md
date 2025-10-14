# Task: Harden Soul Prism Revival Flow Against Missing Effect Managers

## Background
`SoulPrism` iterates over fallen allies at battle end, removing any lingering relic modifiers before reviving them. The implementation assumes every ally exposes `member.effect_manager` and tries to iterate `member.effect_manager.mods` before checking whether an effect manager exists. If an ally never received an `EffectManager` (for example, a fresh recruit who died before any buffs landed), the code raises an `AttributeError`, preventing the relic from reviving anyone.

See the direct access in `backend/plugins/relics/soul_prism.py` lines 43-55.【F:backend/plugins/relics/soul_prism.py†L43-L66】

## Objectives
1. Guard all interactions with `member.effect_manager` inside `SoulPrism` so that allies without one are handled safely (e.g., lazily instantiate an `EffectManager` before removal/creation of modifiers).
2. Make sure the cleanup branch that prunes existing modifiers continues to work for allies who already had an effect manager.
3. Add a regression test covering a fallen ally who lacks `effect_manager` at battle end to confirm revival proceeds without raising.
4. Update any relevant documentation to clarify the revival behavior if needed.

## Acceptance Criteria
- `SoulPrism` revives allies reliably even when they lacked an `EffectManager` prior to the relic trigger.
- Unit tests capture the previously crashing scenario.
- Existing functionality (max HP penalty, defense/mitigation buffs, telemetry) remains intact.
- Documentation references stay accurate.

## Implementation Summary
- Moved effect_manager existence check BEFORE attempting to access mods
- Effect manager is now instantiated before looking for existing modifiers
- Added comprehensive tests in `tests/test_soul_prism.py`:
  - Test revival of ally without effect_manager (regression case)
  - Test revival of ally with existing effect_manager
  - Test that living allies are not affected

ready for review
