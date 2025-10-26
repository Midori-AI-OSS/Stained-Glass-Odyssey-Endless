# Flux Paradox Engine: LadyFireAndIce 4★ stance cycling

## Summary
Current 4★ rewards hand out brute-force tempo (Overclock), revives (Iron Resolve), or repeat strikes (Arcane Repeater) but none lean into elemental stance play despite LadyFireAndIce anchoring the roster's dual-mode identity.【F:backend/plugins/cards/overclock.py†L15-L83】【F:backend/plugins/cards/iron_resolve.py†L9-L52】【F:backend/plugins/cards/arcane_repeater.py†L11-L58】【F:backend/plugins/characters/lady_fire_and_ice.py†L11-L21】 Introducing a card that rotates Fire/Ice boons each turn would unlock hybrid teams without overshadowing existing raw DPS options.

## Details
* Build **Flux Paradox Engine** as a 4★ card that grants +240% Effect Hit Rate and +240% Effect Resistance, underscoring its control-focused stance swaps rather than straight damage.【F:backend/plugins/characters/lady_fire_and_ice.py†L11-L21】
* Track a battle-wide `mode` flag that flips each global `turn_start`: Fire stance on odd turns, Ice stance on even. In Fire stance, the first damaging action each ally performs that turn should apply one stack of `Blazing Torment` to its target; in Ice stance, the first damaging action applies one stack of `Cold Wound` and grants the attacker +12% mitigation for 1 turn. Reset per-ally triggers every turn so multi-attack characters can still benefit once per stance.【F:.codex/implementation/damage-healing.md†L7-L26】【F:.codex/implementation/stats-and-effects.md†L33-L63】
* Emit telemetry identifying the stance, triggering ally, and applied effects so testers can confirm swaps in combat logs.

## Requirements
- Implement `backend/plugins/cards/flux_paradox_engine.py` with stat boosts, stance state machine, per-ally triggers, and proper cleanup. Lean on existing event subscriptions (turn_start, damage_dealt) to avoid polling loops.
- Extend backend tests to cover both stances, ensuring stacks flip correctly across turns and mitigation buffs expire after one round.
- Provide a rich `about` string inside the new plugin so the in-game inventory surfaces the stance loop without relying on `.codex` summaries.

## Audit notes (Auditor)
- Verified the implementation in `backend/plugins/cards/flux_paradox_engine.py` applies the alternating Fire/Ice stance logic and emits telemetry as described.
- Confirmed the accompanying tests in `backend/tests/test_flux_paradox_engine.py` cover stance rotation and single-trigger-per-turn behaviour, and reproduced the suite locally with `uv run pytest tests/test_flux_paradox_engine.py`.
- Mitigation buff duration is not asserted in the new tests—acceptance criteria call for confirming the one-turn expiry, so additional coverage is still required.

more work needed — please add an assertion that the mitigation buff expires after the following turn before resubmitting.
