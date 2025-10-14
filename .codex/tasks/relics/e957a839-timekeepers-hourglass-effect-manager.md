# Task: Ensure Timekeeper's Hourglass Applies Speed Buffs to All Eligible Allies

## Background
`TimekeepersHourglass` currently skips allies that do not already have an `effect_manager` instance when handing out its per-turn speed buff. Because the relic calls `getattr(member, "effect_manager", None)` and simply `continue`s when it finds `None`, any party member who has not previously received a modifier (for example a freshly spawned ally or a unit without passive buffs) will never get the Timekeeper haste effect. This contradicts the relic description and makes the relic appear inert for parts of the party.

See the guard in the relic implementation: `backend/plugins/relics/timekeepers_hourglass.py` lines 57-84.【F:backend/plugins/relics/timekeepers_hourglass.py†L57-L84】

## Objectives
1. Update `TimekeepersHourglass` so it instantiates an `EffectManager` for allies lacking one before applying the speed modifier.
2. Ensure the cleanup path still removes any modifiers that were added through the relic to prevent leaks across battles.
3. Add regression coverage that demonstrates an ally without an `effect_manager` receives the buff after the fix.
4. Refresh any relevant documentation or developer notes if the behavior description changes.

## Acceptance Criteria
- Allies without a pre-existing `effect_manager` receive the Timekeeper speed buff when the relic procs.
- Unit tests cover the case where a brand-new ally is buffed successfully.
- No orphaned modifiers remain on party members after battle end.
- Documentation accurately reflects the corrected behavior.

## Implementation Summary
- Changed `continue` to instantiate EffectManager when missing
- Effect manager is now created before applying speed buff modifiers
- Added comprehensive tests in `tests/test_timekeepers_hourglass.py`:
  - Test buffing ally without effect_manager (regression case)
  - Test buffing ally with existing effect_manager
  - Test that dead allies are not buffed
  - Test that stacks increase the buff magnitude

ready for review
