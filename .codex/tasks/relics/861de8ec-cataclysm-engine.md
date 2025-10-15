# Add 5★ "Cataclysm Engine" relic for mutually assured destruction runs

## Summary
Design an endgame relic that supercharges the party at a steep vitality cost. "Cataclysm Engine" should detonate at battle start, shredding HP from both sides, granting massive stat multipliers to allies, and continuing to drain HP each turn. The relic should feel as run-defining as Omega Core or Paradox Hourglass while enabling fast, high-damage clears for teams that can survive the attrition.

## Details
- Follow the existing relic plugin infrastructure so stacking, stat multipliers, and cleanup match other legendary relics.【F:backend/plugins/relics/_base.py†L39-L155】
- Use `apply_cost_damage` and similar helpers to inflict unavoidable HP loss on allies (and optionally foes) without conflicting with shields or mitigation, mirroring how Omega Core handles its drain.【F:backend/plugins/relics/omega_core.py†L80-L106】
- Update relic documentation covering 5★ effects so Cataclysm Engine sits alongside Paradox Hourglass, Soul Prism, and Omega Core in contributor references.【F:.codex/implementation/relic-inventory.md†L36-L38】

## Requirements
- Implement a `CataclysmEngine` plugin that:
  - On `battle_start`, applies large multiplicative buffs to ally core stats (ATK/DEF/SPD, etc.) and simultaneously deals an unavoidable HP blast (e.g., 15% Max HP per stack) to both allies and foes.
  - On each `turn_start`, continues draining ally HP (e.g., 5% per stack) while granting escalating bonuses such as Aftertaste hits or mitigation to offset the damage, ensuring stacking remains multiplicative.
  - Tracks and removes its stat modifiers when the battle ends to prevent lingering buffs.
  - Emits descriptive `relic_effect` events for the initial blast and each subsequent drain tick so battle logs and overlays communicate the risk/reward profile.
- Expand backend tests to cover initial detonation, per-turn drains, stacking behavior, and interaction with existing drain-heavy relics to prevent runaway double-counting.【F:backend/tests/test_relic_effects.py†L24-L116】
- Refresh `.codex/implementation/relic-inventory.md` and related planning notes to document the new 5★ relic.

## Validation
- `uv run pytest backend/tests/test_relic_effects.py::test_cataclysm_engine_*`
- `uv run pytest backend/tests/test_relic_effects_advanced.py`

## Documentation
- `.codex/implementation/relic-inventory.md`
- `.codex/planning/archive/bd48a561-relic-plan.md`
