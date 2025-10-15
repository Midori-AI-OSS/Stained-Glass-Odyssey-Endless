# Flux Paradox Engine: LadyFireAndIce 4★ stance cycling

## Summary
Current 4★ rewards hand out brute-force tempo (Overclock), revives (Iron Resolve), or repeat strikes (Arcane Repeater) but none lean into elemental stance play despite LadyFireAndIce anchoring the roster's dual-mode identity.【F:.codex/implementation/card-inventory.md†L63-L66】【F:.codex/planning/archive/726d03ae-card-plan.md†L61-L64】【F:.codex/implementation/player-foe-reference.md†L59-L60】 Introducing a card that rotates Fire/Ice boons each turn would unlock hybrid teams without overshadowing existing raw DPS options.

## Details
* Build **Flux Paradox Engine** as a 4★ card that grants +240% Effect Hit Rate and +240% Effect Resistance, underscoring its control-focused stance swaps rather than straight damage.【F:.codex/implementation/card-inventory.md†L63-L66】【F:.codex/implementation/player-foe-reference.md†L59-L60】
* Track a battle-wide `mode` flag that flips each global `turn_start`: Fire stance on odd turns, Ice stance on even. In Fire stance, the first damaging action each ally performs that turn should apply one stack of `Blazing Torment` to its target; in Ice stance, the first damaging action applies one stack of `Cold Wound` and grants the attacker +12% mitigation for 1 turn. Reset per-ally triggers every turn so multi-attack characters can still benefit once per stance.【F:.codex/implementation/damage-healing.md†L7-L26】【F:.codex/implementation/stats-and-effects.md†L33-L63】
* Emit telemetry identifying the stance, triggering ally, and applied effects so testers can confirm swaps in combat logs.

## Requirements
- Implement `backend/plugins/cards/flux_paradox_engine.py` with stat boosts, stance state machine, per-ally triggers, and proper cleanup. Lean on existing event subscriptions (turn_start, damage_dealt) to avoid polling loops.
- Extend backend tests to cover both stances, ensuring stacks flip correctly across turns and mitigation buffs expire after one round.
- Update `.codex/implementation/card-inventory.md` and the archived card plan with the stance-cycling description and numerical tuning.【F:.codex/implementation/card-inventory.md†L63-L69】【F:.codex/planning/archive/726d03ae-card-plan.md†L61-L69】
- Provide `fluxparadoxengine.png` in `frontend/src/lib/assets/cards/Art/` and verify reward previews pick up the asset.
