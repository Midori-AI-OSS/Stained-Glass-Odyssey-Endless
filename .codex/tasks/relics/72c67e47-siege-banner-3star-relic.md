# Siege Banner: attrition-focused 3★ relic

## Summary
Our 3★ relics reward economy (Greed Engine), crit scaling (Stellar Compass), or first-attack repeats (Echoing Drum). None lean into attrition battles where the party methodically removes foes and wants the fight to snowball defensively afterward. A 3★ option that softens enemy defenses upfront while paying off on every kill would diversify mid-tier relic drafting.【F:.codex/implementation/relic-inventory.md†L24-L35】【F:.codex/planning/archive/bd48a561-relic-plan.md†L45-L55】

## Details
* Introduce **Siege Banner**: on `battle_start`, inflict a 2-turn DEF debuff (~15% per stack) on all enemies. Each time a foe dies, the party gains a permanent stacking buff (≈+4% ATK and +4% DEF per stack) for the rest of the combat, reinforcing long fights.
* Use `battle_start` subscriptions to loop through active enemies and apply stat modifiers through their effect managers. Follow patterns from Traveler's Charm and Echoing Drum for enemy iteration / cleanup, ensuring modifiers are removed once fights end.【F:backend/plugins/relics/travelers_charm.py†L23-L86】【F:backend/plugins/relics/echoing_drum.py†L24-L118】
* Track death events via `damage_taken` and guard against double triggers from overkill, similar to Bent Dagger's kill handling. Emit telemetry describing both the initial debuff and each stacking buff increment.【F:backend/plugins/relics/bent_dagger.py†L23-L58】

## Requirements
- Implement `backend/plugins/relics/siege_banner.py` with helper cleanup and `describe(stacks)` copy that explains the opening debuff and per-kill scaling.
- Add focused tests validating: enemy debuff application on battle start, stacking buffs per kill (including multiple stacks), and cleanup after battle end. Extend `backend/tests/test_relic_effects_advanced.py` or create a new suite.
- Update `.codex/implementation/relic-inventory.md` and the archival relic design plan with Siege Banner's final tuning.【F:.codex/implementation/relic-inventory.md†L24-L41】【F:.codex/planning/archive/bd48a561-relic-plan.md†L45-L60】
- Provide a placeholder icon under `frontend/src/lib/assets/relics/3star/` and confirm it loads via the existing asset registry globs.【F:frontend/src/lib/systems/assetRegistry.js†L174-L1353】
- Document any notable pacing math (e.g., kill stack percentages) in `.codex/docs/relics/` if future balancing is expected.
