# Add 3★ "Command Beacon" relic for party-wide speed coordination

## Summary
Ship a rare relic that redistributes speed each turn so slower allies keep pace with the squad at a modest HP cost to the pace-setter. "Command Beacon" should highlight tactical turn-order play: the fastest ally sacrifices a sliver of health so everyone else gains a temporary SPD boost.

## Details
- Use the standard relic plugin base to manage stat modifiers and bus subscriptions so stacking behaves like existing rare relics.【F:backend/plugins/relics/_base.py†L39-L155】
- SPD is computed via the stats layer; leverage the `spd` property and `create_stat_buff` helpers to apply temporary bonuses without mutating base stats.【F:backend/autofighter/stats.py†L447-L456】
- Turn lifecycle hooks (`turn_start`, `turn_end`, `battle_end`) are already handled by other relics, providing a template for applying and clearing per-turn buffs safely.【F:backend/plugins/relics/travelers_charm.py†L105-L119】
- Update docs enumerating 3★ relics so contributors understand Command Beacon’s trade-off compared to Greed Engine, Stellar Compass, and Echoing Drum.【F:.codex/implementation/relic-inventory.md†L30-L33】

## Requirements
- Add a `CommandBeacon` relic under `backend/plugins/relics/` that:
  - On each `turn_start`, identifies the ally with the highest current SPD.
  - Applies a temporary SPD buff (e.g., +15% per stack) to every other ally for that turn, using the effect manager to expire it on `turn_end`/`battle_end`.
  - Applies a small self-damage pulse (e.g., 3% Max HP per stack) to the pace-setter to represent the strain of coordinating the team.
  - Emits `relic_effect` events summarizing which allies gained SPD and how much HP was sacrificed for battle logs.
- Ensure multiple stacks scale both the SPD bonus and the HP cost multiplicatively rather than linearly to stay consistent with other relics.
- Add tests covering single- and multi-stack cases, verifying SPD changes revert after the turn and HP loss scales correctly.【F:backend/tests/test_relic_effects.py†L24-L116】
- Document the relic in `.codex/implementation/relic-inventory.md` and update planning references for 3★ relic design coverage.

## Validation
- `uv run pytest backend/tests/test_relic_effects.py::test_command_beacon_*`
- `uv run pytest backend/tests/test_relic_effects_advanced.py`

## Documentation
- `.codex/implementation/relic-inventory.md`
- `.codex/planning/archive/bd48a561-relic-plan.md`
