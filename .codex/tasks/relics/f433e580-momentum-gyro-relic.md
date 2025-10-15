# Add 2★ Momentum Gyro relic for focused assault chains

## Summary
Introduce **Momentum Gyro**, a 2★ relic that rewards repeatedly striking the same foe. Allies should build stacking offensive momentum when they keep pressure on one target, while that target becomes more vulnerable for a short window. Swapping targets or whiffing attacks should reset the chain.

## Details
* Listen for the `action_used` combat event so both basic attacks and abilities extend the chain, using Echo Bell’s subscription pattern as a reference.【F:backend/plugins/relics/echo_bell.py†L96-L125】
* Track each attacker’s last successful target and consecutive hit count. When the same foe is hit again for positive damage, increase a per-attacker momentum stack (cap the streak at 5 by default to avoid runaway buffs). Reset the streak if damage is zero/negative or the target changes.
* Apply a short-lived self buff that grants +5% ATK per relic stack per momentum stack (multiplicative with existing relic bonuses) using the standard `EffectManager` / `create_stat_buff` pattern.【F:backend/plugins/relics/bent_dagger.py†L40-L50】 Emit `relic_effect` telemetry describing the current streak and buffed amount.
* Simultaneously apply a 1-turn mitigation debuff to the struck foe equal to 5% per relic stack per streak level (stacking multiplicatively if several allies focus the same enemy). Remove or refresh the debuff cleanly when the streak resets; reuse the modifier removal workflow other relics follow when their temporary buffs expire.【F:backend/plugins/relics/travelers_charm.py†L80-L118】
* Ensure all per-battle bookkeeping (`last_target`, `streaks`, active modifiers) is cleared on `battle_end`.

## Requirements
- Implement the `MomentumGyro` relic plugin under `backend/plugins/relics/` with `stars = 2`, storing attacker streak state safely on the party object and respecting the chain rules above.
- Emit structured `relic_effect` payloads for both the attacker buff and the foe debuff so combat logs and analytics can display the momentum flow.【F:backend/plugins/relics/bent_dagger.py†L40-L57】
- Add comprehensive unit tests that cover: streak growth/reset conditions, buff/debuff magnitude math across multiple relic stacks, debuff cleanup on battle end, and the 5-stack cap behavior.
- Document the relic and its focused assault mechanic in the relic system docs to keep player-facing references accurate.【F:.codex/implementation/relic-system.md†L1-L16】
