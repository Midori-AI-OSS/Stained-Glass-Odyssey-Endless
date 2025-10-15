# Add 1★ "Field Rations" relic for post-battle recovery

## Summary
Design and implement a new 1★ relic that rewards survival by topping the party off between encounters. "Field Rations" should provide a light heal and a burst of ultimate charge to all allies after each battle, reinforcing sustain-heavy runs without overpowering in-combat effects.

## Details
- Leverage the existing relic plugin framework so the new relic stacks multiplicatively with other stat modifiers and can subscribe to battle events for its triggers.【F:backend/plugins/relics/_base.py†L39-L155】
- Ensure the relic remains part of the 1★ reward pool and shows up in catalogs alongside other low-star relics by registering it through the existing loader and metadata routes.【F:backend/autofighter/relics.py†L27-L43】【F:backend/routes/catalog.py†L40-L62】
- Update repository docs so the 1★ relic roster reflects the new option and contributors understand its intended role in post-battle sustain loops.【F:.codex/implementation/relic-inventory.md†L12-L22】

## Requirements
- Create a `FieldRations` relic plugin under `backend/plugins/relics/` that:
  - Grants each party member a heal equal to ~2–3% Max HP per stack when `battle_end` fires.
  - Adds a small amount of ultimate charge (e.g., +1 per stack) to each ally after that heal, respecting the existing cap logic.【F:backend/autofighter/stats.py†L680-L704】
  - Cleans up any subscriptions or temporary state between encounters to avoid stacking extra heals on future fights.
- Extend relic selection/tests so the new relic can be drawn at 1★ and covered by automated checks (unit test validating the heal + charge behavior when multiple stacks are owned).【F:backend/tests/test_relic_effects.py†L24-L116】
- Document the relic in `.codex/implementation/relic-inventory.md` with a concise description and note any stacking nuances.
- Update any planning or reference material that enumerates relics (e.g., relic plans, reward docs) so Field Rations appears with other 1★ entries.

## Validation
- `uv run pytest backend/tests/test_relic_effects.py::test_field_rations_*`
- `uv run pytest backend/tests/test_relic_awards.py`

## Documentation
- `.codex/implementation/relic-inventory.md`
- Related relic design notes under `.codex/docs/relics/` if needed
