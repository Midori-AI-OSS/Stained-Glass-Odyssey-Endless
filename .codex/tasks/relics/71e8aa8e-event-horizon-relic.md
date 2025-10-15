# Add 5★ Event Horizon relic for turn-start gravity pulses

## Summary
Ship **Event Horizon**, a 5★ relic that detonates a gravity pulse at the start of every ally turn. Each pulse should rip chunks of HP from every living foe while draining the acting ally, creating an all-or-nothing tempo engine worthy of top-tier relics.

## Details
* Subscribe to the global `turn_start` event; it fires for every combatant each time they begin a turn.【F:backend/autofighter/rooms/battle/turn_loop/player_turn.py†L226-L239】
* Maintain a cached list of current foes (populate it when `turn_start` fires for foes, similar to Rusty Buckle) so ally pulses always know whom to strike.【F:backend/plugins/relics/rusty_buckle.py†L98-L203】 Ignore pulses triggered by foes.
* When an ally begins a turn with positive HP, deal gravity damage to every tracked foe equal to 6% of that foe’s current HP per Event Horizon stack (minimum 1). Use `safe_async_task(target.apply_damage(..., attacker=ally))` so mitigation and on-hit hooks still apply, and emit telemetry summarizing the pulse for each foe.【F:backend/plugins/relics/omega_core.py†L34-L91】
* After the pulse, drain the acting ally for 3% of their Max HP per stack using `apply_cost_damage` so shields and mitigation cannot blunt the backlash.【F:backend/plugins/relics/greed_engine.py†L57-L68】 Emit a second `relic_effect` record for the self-damage.
* Clear the foe cache and unsubscribe on `battle_end` so no references leak between encounters.

## Requirements
- Implement the `EventHorizon` relic (`stars = 5`) under `backend/plugins/relics/` with turn-start pulses, foe tracking, telemetry, and self-drain as described.
- Ensure pulses handle extra turns (the event fires again) and gracefully skip if no foes are alive.
- Add unit tests covering AoE damage math, self-drain scaling, extra-turn handling, and per-battle cleanup.
- Update relic documentation with Event Horizon’s gravity pulse behavior so high-tier options are documented.【F:.codex/implementation/relic-system.md†L1-L16】
