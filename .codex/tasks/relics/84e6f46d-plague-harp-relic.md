# Add 3★ Plague Harp relic for DoT propagation with backlash

## Summary
Create **Plague Harp**, a 3★ relic that weaponizes the party’s damage-over-time effects. Whenever a party-inflicted DoT ticks on a foe, the relic should echo that rot into another enemy while the caster pays a small health tithe, reinforcing the high-risk, high-reward identity of mid-tier relics.

## Details
* Subscribe to the global `dot_tick` bus event so the relic can react every time a damage-over-time effect resolves, using the existing emission point in `DamageOverTime.tick` as your trigger reference.【F:backend/autofighter/effects.py†L260-L291】
* Only trigger when the attacker is a party member and the target is a foe. Track active foes similar to Rusty Buckle so you always have a valid secondary target, falling back to the original foe if only one remains.【F:backend/plugins/relics/rusty_buckle.py†L98-L203】
* Spawn an `Aftertaste` effect against a random eligible foe equal to 40% of the ticking DoT’s damage per Plague Harp stack (round down, minimum 1). Use the existing Aftertaste helper so damage types randomize correctly.【F:backend/plugins/effects/aftertaste.py†L1-L124】 Emit telemetry describing the echo.
* Charge the original attacker a health tithe to balance the power: inflict self-damage equal to 2% of their Max HP per Plague Harp stack using the cost-damage helper that bypasses shields.【F:backend/plugins/relics/greed_engine.py†L57-L68】 Emit a second `relic_effect` event summarizing the backlash.
* Store all state on the party object and clean it up on `battle_end` so streaks and foe caches never leak between encounters.

## Requirements
- Add the `PlagueHarp` relic under `backend/plugins/relics/` with `stars = 3`, handling foe tracking, Aftertaste propagation, and self-damage backfire as specified.
- Ensure the relic gracefully handles edge cases: single remaining foe, attacker already defeated, and simultaneous multiple DoTs ticking in the same frame.
- Write automated tests verifying DoT propagation sizing, self-damage scaling, random-target selection stability, and cleanup after battles.
- Update relic documentation to record Plague Harp’s DoT echo and health tithe behavior.【F:.codex/implementation/relic-system.md†L1-L16】
