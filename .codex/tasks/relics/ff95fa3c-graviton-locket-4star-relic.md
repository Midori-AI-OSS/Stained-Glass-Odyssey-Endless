# Graviton Locket: high-risk 4★ battlefield control relic

## Summary
Null Lantern dramatically changes routing, while Traveler's Charm and Timekeeper's Hourglass lean on defensive tempo buffs. We still lack a high-star relic that aggressively cripples enemy tempo at a health cost to the party. A gravity-themed relic can create that trade-off, giving veterans a reason to embrace HP drain for explosive openings.【F:.codex/implementation/relic-inventory.md†L33-L40】【F:.codex/planning/archive/bd48a561-relic-plan.md†L47-L60】

## Details
* Define **Graviton Locket**: on `battle_start`, apply a "gravity" debuff to every enemy for 2 turns +1 per additional stack that reduces SPD by ~30% per stack and increases damage taken by ~12% per stack. While any enemy is under gravity, the party loses 1% Max HP per stack at `turn_start` (mirroring Greed Engine's drain cadence).
* Store active debuffs in party state so we know when all gravity effects have expired and can stop draining HP. Remove any lingering modifiers at `battle_end` to avoid leaking across fights.【F:backend/plugins/relics/greed_engine.py†L18-L68】【F:backend/plugins/relics/travelers_charm.py†L23-L86】
* Emit telemetry detailing both the debuff (per target) and each HP drain tick to keep combat logs honest.【F:backend/plugins/relics/guardian_charm.py†L20-L37】【F:backend/plugins/relics/greed_engine.py†L34-L63】

## Requirements
- Implement `backend/plugins/relics/graviton_locket.py` with helper cleanup, duration tracking, and a thorough `describe(stacks)` covering debuff values, duration scaling, and HP drain cost.
- Add backend tests ensuring: enemies receive the debuff with correct magnitude/duration, HP drain only runs while gravity is active (and scales with stacks), and all modifiers clear after battle. Extend `backend/tests/test_relic_effects_advanced.py` or create a new dedicated module.
- Update `.codex/implementation/relic-inventory.md` and the relic design plan to include Graviton Locket with final tuning notes.【F:.codex/implementation/relic-inventory.md†L33-L48】【F:.codex/planning/archive/bd48a561-relic-plan.md†L45-L65】
- Supply a placeholder icon in `frontend/src/lib/assets/relics/4star/` and verify the asset resolves through the registry globs.【F:frontend/src/lib/systems/assetRegistry.js†L174-L1353】
- Capture balancing rationale (gravity duration vs. HP drain) in `.codex/docs/relics/` so future tuning has a paper trail.
