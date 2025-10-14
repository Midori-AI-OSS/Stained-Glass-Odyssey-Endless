# Fix Farsight Scope trigger event

## Summary
Farsight Scope listens for a `before_attack` BUS event that is never emitted during real combat. As a result, the card's +6% crit rate bonus for low-HP targets never activates outside of unit tests.

## Details
* The card subscribes to `before_attack` inside `FarsightScope.apply()` and only grants the temporary buff from that callback.【F:backend/plugins/cards/farsight_scope.py†L22-L71】
* Combat flow around damage application emits `dodge`, `hit_landed`, and other events, but there is no `before_attack` emission anywhere in the runtime battle loop.【F:backend/autofighter/stats.py†L780-L820】
* A unit test fakes the missing event (`tests/test_farsight_scope.py`), so the failure does not surface during testing.

This leaves the card functionally inert in real matches.

## Requirements
- Update the backend so the Farsight Scope effect can trigger during actual battles.
  - Either emit the missing `before_attack` event at an appropriate point in the combat sequence, **or** adjust the card to hook into an existing event that occurs before damage is resolved while still satisfying the design intent (granting the bonus before an attack is resolved).
- Ensure the temporary crit buff still cleans up correctly after the acting unit uses its action.
- Add or update automated coverage to prove the fix (e.g., integration test that runs a real battle frame and confirms the buff applies when a target is under 50% HP).
- Document any combat event changes (if added) in the relevant `.codex/implementation` docs.
ready for review
