# Add 1★ Copper Siphon relic for lifesteal turns

## Summary
Design and implement a new 1★ relic, **Copper Siphon**, that grants mild lifesteal whenever party members land damage. The relic should funnel a small percentage of dealt damage back to the attacker (overflow becomes shielding) and emit telemetry so combat logs surface the siphoned healing.

## Details
* Hook into the existing `action_used` event so the relic reacts to both basic attacks and ability damage, mirroring how Echo Bell listens for combat actions.【F:backend/plugins/relics/echo_bell.py†L96-L125】
* When an ally deals positive damage, heal them for 2% of the raw damage per Copper Siphon stack (minimum 1 HP). If the ally is at full HP, convert the excess into shields by enabling overheal before applying the heal so it flows into the shield pipeline.【F:backend/plugins/relics/threadbare_cloak.py†L21-L32】【F:backend/autofighter/stats.py†L1046-L1068】
* Emit a `relic_effect` event describing the siphoned amount, similar to how Bent Dagger reports its attack boosts, so downstream tooling can surface the effect in logs.【F:backend/plugins/relics/bent_dagger.py†L40-L57】
* Keep the relic stateless between battles; rely on battle-end cleanup only for subscription removal. No long-term party attributes should be mutated beyond the applied healing.

## Requirements
- Create a new `CopperSiphon` relic plugin under `backend/plugins/relics/` with `stars = 1`, appropriate `about`/`describe` strings, event subscriptions, and shield-aware lifesteal logic as outlined above.
- Ensure relic registration works with the existing loader (`backend/autofighter/relics.py`) without manual wiring and that repeated stacks scale multiplicatively as described.【F:backend/autofighter/relics.py†L10-L37】
- Add targeted unit tests (e.g., in `backend/tests/test_relic_effects.py`) covering: healing proportional to damage, overflow shielding when HP is full, stacking behavior, and event emission hooks.
- Update relic documentation to include Copper Siphon and note the lifesteal/shield interaction so docs stay in sync with gameplay.【F:.codex/implementation/relic-system.md†L1-L16】
