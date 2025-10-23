# Add 4★ Blood Debt Tithe relic for escalating loot and foe power

## Summary
Design **Blood Debt Tithe**, a 4★ relic that trades harder enemies for accelerating rare-drop growth. Every defeated foe should increase the party’s rare drop rate for the rest of the run, but future encounters begin with foes empowered proportionally to the number of sacrifices already collected.

## Details
* Listen for `entity_defeat` and only count genuine foe deaths. Track defeated foe IDs in a per-battle set so duplicates from multiple defeat emissions don’t inflate the total, then roll the unique count into a persistent counter on the party when the fight ends.【F:backend/autofighter/rooms/battle/events.py†L61-L83】【F:backend/autofighter/stats.py†L935-L935】
* Increase `party.rdr` by 0.2 percentage points per Blood Debt Tithe stack for each new foe defeat, mirroring how Greed Engine mutates the run-wide rare drop rate.【F:backend/plugins/relics/greed_engine.py†L23-L39】 Persist the cumulative total on the party so the bonus survives future battles.
* Before each battle, apply a scaling buff to foes based on the stored defeat count: subscribe to `battle_start`, filter foe entities, and add a permanent combat modifier that grants +3% ATK and +2% SPD per stored defeat per relic stack (multiplicative with other buffs). Use the same foe-buff pattern as Null Lantern and remove modifiers cleanly after the encounter ends.【F:backend/plugins/relics/null_lantern.py†L37-L118】
* Emit `relic_effect` telemetry when kills are banked and when foe buffs are applied so combat logs communicate the current tithe level.
* Reset only per-battle bookkeeping (`seen_foes`, temporary modifiers) on `battle_end`; the accumulated defeat counter and `rdr` boost should persist for the run.

## Requirements
- Implement the `BloodDebtTithe` relic plugin (`stars = 4`) under `backend/plugins/relics/` handling foe defeat tracking, run-wide `rdr` growth, foe buff application, and cleanup as described.
- Add regression-safe tests covering: duplicate defeat suppression, `rdr` accumulation between battles, foe buff scaling math, and teardown of buffs after combat.
- Document the relic trade-off in the relic system reference so players understand the reward-for-risk loop.【F:.codex/implementation/relic-system.md†L1-L16】
