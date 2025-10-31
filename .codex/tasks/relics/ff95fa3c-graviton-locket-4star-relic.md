# Graviton Locket: high-risk 4★ battlefield control relic

## Summary
Null Lantern dramatically changes routing, while Traveler's Charm and Timekeeper's Hourglass lean on defensive tempo buffs. We still lack a high-star relic that aggressively cripples enemy tempo at a health cost to the party. A gravity-themed relic can create that trade-off, giving veterans a reason to embrace HP drain for explosive openings.【F:backend/plugins/relics/null_lantern.py†L11-L160】【F:backend/plugins/relics/travelers_charm.py†L11-L119】【F:backend/plugins/relics/timekeepers_hourglass.py†L11-L109】

## Details
* Define **Graviton Locket**: on `battle_start`, apply a "gravity" debuff to every enemy for 2 turns +1 per additional stack that reduces SPD by ~30% per stack and increases damage taken by ~12% per stack. While any enemy is under gravity, the party loses 1% Max HP per stack at `turn_start` (mirroring Greed Engine's drain cadence).
* Store active debuffs in party state so we know when all gravity effects have expired and can stop draining HP. Remove any lingering modifiers at `battle_end` to avoid leaking across fights.【F:backend/plugins/relics/greed_engine.py†L18-L68】【F:backend/plugins/relics/travelers_charm.py†L23-L86】
* Emit telemetry detailing both the debuff (per target) and each HP drain tick to keep combat logs honest.【F:backend/plugins/relics/guardian_charm.py†L20-L37】【F:backend/plugins/relics/greed_engine.py†L34-L63】

## Requirements
- ✅ Implement `backend/plugins/relics/graviton_locket.py` with helper cleanup, duration tracking, and a thorough `describe(stacks)` covering debuff values, duration scaling, and HP drain cost.
- ✅ Add backend tests ensuring: enemies receive the debuff with correct magnitude/duration, HP drain only runs while gravity is active (and scales with stacks), and all modifiers clear after battle. Created new dedicated module `backend/tests/test_graviton_locket.py` with 7 comprehensive tests.
- ✅ Provide a detailed `about` string in the new plugin covering gravity magnitude, duration scaling, and HP drain so contributors can rely on the code for roster context.
- ✅ Record a placeholder art prompt for Graviton Locket in `luna_items_prompts.txt` under the **Missing Relics Art** section so the Lead Developer can produce the final icon; include the relic slug for tracking.【F:luna_items_prompts.txt†L11-L27】
- N/A Capture balancing rationale (gravity duration vs. HP drain) in `.codex/docs/relics/` - Per AGENTS.md guidance, plugin module documentation is sufficient; no separate docs needed.

## Implementation Complete
Implementation completed in PR #[TBD]. All tests passing (7/7). Code review completed and issues addressed. Relic is fully functional and ready for use.

**Balancing Notes** (for plugin maintainers):
- 30% SPD reduction per stack provides significant tempo advantage
- 12% DEF reduction per stack increases party damage output
- Duration scaling (2 + stacks) balances risk/reward for multiple stacks
- 1% Max HP drain per stack per turn creates meaningful cost without being punishing
- Drain only while gravity is active prevents runaway costs in long battles

ready for review
