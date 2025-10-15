# Add 2★ "Catalyst Vials" relic to reward allied DoT damage

## Summary
Create a mid-tier relic that turns existing damage-over-time builds into self-sustaining engines. "Catalyst Vials" should trigger whenever an ally's DoT ticks on an enemy, siphoning a portion of the damage back as healing and a temporary debuffing edge for the attacker.

## Details
- The DoT system already emits async `dot_tick` events with the attacker, target, and damage payload—hook the relic into this path so it reacts to every qualifying tick without duplicating effect code.【F:backend/autofighter/effects.py†L243-L291】
- Implement the relic as a standard plugin so it stacks correctly and appears in selection pools and catalog listings for 2★ relics.【F:backend/plugins/relics/_base.py†L39-L155】【F:backend/autofighter/relics.py†L27-L43】【F:backend/routes/catalog.py†L40-L62】
- Update documentation that enumerates relic abilities so the new DoT-sustain option is reflected in contributor references.【F:.codex/implementation/relic-inventory.md†L23-L32】

## Requirements
- Introduce `CatalystVials` under `backend/plugins/relics/` that:
  - Listens for `dot_tick` events, filtering for ticks where the attacker is a party member and the target is a foe.
  - Heals the attacker for a percentage of the tick damage per stack (e.g., 5%) and grants them a one-turn buff to `effect_hit_rate` to reinforce status-heavy teams. Use the effect manager helpers to add and expire the temporary buff cleanly.
  - Emits `relic_effect` telemetry with metadata describing healing done and bonus potency so battle logs stay informative.
  - Clears state on battle end so no stale references leak to future fights.
- Add focused tests verifying that one and multiple stacks properly convert DoT damage into healing/buffs and that non-party ticks are ignored.【F:backend/tests/test_relic_effects.py†L24-L116】
- Document the relic in `.codex/implementation/relic-inventory.md` and update planning artifacts that outline 2★ relic coverage.

## Validation
- `uv run pytest backend/tests/test_relic_effects.py::test_catalyst_vials_*`
- `uv run pytest backend/tests/test_relic_effects_advanced.py`

## Documentation
- `.codex/implementation/relic-inventory.md`
- `.codex/planning/archive/bd48a561-relic-plan.md`
