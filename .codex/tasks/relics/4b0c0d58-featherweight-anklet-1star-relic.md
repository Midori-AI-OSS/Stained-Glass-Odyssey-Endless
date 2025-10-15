# Featherweight Anklet: early tempo relic (1★)

## Summary
Our 1★ pool leans on sustain, mitigation, and incremental offense but lacks a relic that nudges turn tempo or early gauge pressure. Players who want fast openings must jump to higher-star options like Traveler's Charm or Timekeeper's Hourglass, leaving a pacing gap in the common pool.【F:.codex/implementation/relic-inventory.md†L9-L40】【F:.codex/planning/archive/bd48a561-relic-plan.md†L10-L37】

## Details
* Introduce **Featherweight Anklet**, a 1★ relic that grants a small permanent SPD multiplier (≈+2% per stack) and awards a short burst (+6% SPD per stack for 1 turn) the first time each ally acts in a battle. This mirrors the immediate impact of cards like quick buffs while staying inside 1★ power bounds.
* Use the existing `RelicBase` helpers for multiplicative stat adjustments and subscribe to `battle_start`/`action_used` events so each ally only receives the one-time burst per battle. Clear subscriptions on battle end just like other reactive relics.【F:backend/plugins/relics/lucky_button.py†L18-L61】【F:backend/plugins/relics/echo_bell.py†L34-L95】
* Emit rich `relic_effect` telemetry that reports which ally received the burst and how big the SPD swing was so battle logs capture the effect.【F:backend/plugins/relics/shiny_pebble.py†L29-L63】

## Requirements
- Add `backend/plugins/relics/featherweight_anklet.py` implementing the behavior above, including cleanup helpers and `describe(stacks)` copy that clarifies both the permanent SPD boost and the first-action burst.
- Extend backend tests to cover: permanent SPD stacking, single-trigger burst per ally per battle, and telemetry emission (asserting `relic_effect` payload). Reuse the async BUS fixtures already present in `backend/tests/test_relic_effects.py` or create a dedicated test module if easier.【F:backend/tests/test_relic_effects.py†L1-L420】
- Update `.codex/implementation/relic-inventory.md` and the archived relic plan to document Featherweight Anklet with the final numbers and behavior.【F:.codex/implementation/relic-inventory.md†L9-L47】【F:.codex/planning/archive/bd48a561-relic-plan.md†L10-L53】
- Provide a placeholder icon under `frontend/src/lib/assets/relics/1star/` (24×24 PNG) and ensure it resolves through the asset registry (no manual import needed thanks to globbing, but include the asset in git).【F:frontend/src/lib/systems/assetRegistry.js†L174-L1353】
- Add a release note blurb to `.codex/docs/relics/` if additional mechanical rationale is useful; otherwise ensure existing docs stay consistent.
