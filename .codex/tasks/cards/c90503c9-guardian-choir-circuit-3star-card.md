# Guardian Choir Circuit: Carly 3★ sustain anchor

## Summary
Every existing 3★ reward is offensive—either crit conversion, revival armor, or chain lightning—leaving no high-impact sustain card for runs that lean on healers like Carly and other Light specialists.【F:.codex/implementation/card-inventory.md†L58-L66】【F:.codex/planning/archive/726d03ae-card-plan.md†L56-L64】【F:.codex/implementation/player-foe-reference.md†L51-L52】 We need a premium support option that spreads Carly's guardian shields without duplicating Iron Resurgence's revive loop.

## Details
* Add **Guardian Choir Circuit** as a 3★ card granting +200% DEF and +150% Regain so teams that invest in healing get both sturdiness and stronger regen ticks.【F:.codex/implementation/card-inventory.md†L58-L66】【F:.codex/implementation/player-foe-reference.md†L51-L52】
* Hook into the `heal_received` event: whenever an ally is directly healed, funnel 15% of that heal into a shield on the lowest-HP teammate (including the target if still lowest) and apply a 1-turn +12% mitigation buff to the shield recipient. Limit to once per ally turn to prevent infinite loops from multi-hit heals.【F:.codex/implementation/damage-healing.md†L12-L37】【F:.codex/implementation/stats-and-effects.md†L33-L63】
* Surface telemetry noting the healer, heal amount, shield size, mitigation bonus, and which ally received the choir redirect for debugging.

## Requirements
- Implement `backend/plugins/cards/guardian_choir_circuit.py` with stat boosts, heal listener, per-turn throttling, and cleanup following the patterns in Balanced Diet and Guardian Shard.
- Write backend tests covering multi-target heals, overheal handling, and ensuring the mitigation buff and shield expire correctly between turns.
- Update `.codex/implementation/card-inventory.md` plus the archived card plan to document the new sustain-focused 3★ card.【F:.codex/implementation/card-inventory.md†L58-L69】【F:.codex/planning/archive/726d03ae-card-plan.md†L56-L69】
- Create `guardianchoircircuit.png` under `frontend/src/lib/assets/cards/Art/` so the reward picker displays the new option.
