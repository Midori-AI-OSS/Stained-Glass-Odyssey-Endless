# Add 4★ "Entropy Mirror" relic that amplifies foes but inflicts recoil

## Summary
Deliver a high-risk relic that accelerates battles by juicing enemy damage while reflecting some of it back at them. "Entropy Mirror" should give all foes a sizable ATK boost at battle start, then cause them to suffer self-inflicted damage whenever they land hits, letting aggressive parties race opponents before the recoil overwhelms them.

## Details
- Build on the relic base class so multiplicative stacking, event subscriptions, and cleanup behave consistently with other epic relics.【F:backend/plugins/relics/_base.py†L39-L155】
- Enemy damage events flow through `apply_damage`, which emits `damage_dealt` for the attacker and exposes helper APIs for self-harm; use this hook to apply recoil that ignores mitigation via `apply_cost_damage`.【F:backend/autofighter/stats.py†L955-L990】
- Ensure documentation that lists 4★ relics reflects the new entry and contrasts its trade-offs with Null Lantern, Traveler's Charm, and Timekeeper's Hourglass.【F:.codex/implementation/relic-inventory.md†L33-L35】

## Requirements
- Create an `EntropyMirror` relic plugin that:
  - On `battle_start`, applies a multiplicative ATK buff (e.g., +30% per stack) to all foes present, using stat buffs or direct multipliers.
  - Subscribes to `damage_dealt` and, when the attacker is a foe, applies self-damage equal to a percentage of the damage dealt per stack using `apply_cost_damage` so mitigation and shields do not prevent the backlash.
  - Emits detailed `relic_effect` events for both the buff and each recoil tick to keep battle logs informative.
  - Cleans up subscriptions on `battle_end`.
- Update tests to cover foe buffing and recoil logic, including ensuring recoil cannot kill already-defeated enemies twice and that multiple stacks scale both effects correctly.【F:backend/tests/test_relic_effects.py†L24-L116】
- Document the relic in `.codex/implementation/relic-inventory.md` and align long-form relic design notes/plans with the new 4★ option.

## Validation
- `uv run pytest backend/tests/test_relic_effects.py::test_entropy_mirror_*`
- `uv run pytest backend/tests/test_rusty_buckle.py`

## Documentation
- `.codex/implementation/relic-inventory.md`
- `.codex/planning/archive/bd48a561-relic-plan.md`
