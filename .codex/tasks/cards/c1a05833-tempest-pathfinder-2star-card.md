# Tempest Pathfinder: LadyWind 2★ dodge rally

## Summary
Our 2★ line-up focuses on Critical Boost loops, global DEF pulses, or extra actions—none of the mid-tier rewards encourage dodge-centric squads even though evasion is a core defensive stat and LadyWind's passive thrives on crit-fueled slipstreams.【F:.codex/implementation/card-inventory.md†L49-L56】【F:.codex/planning/archive/726d03ae-card-plan.md†L47-L55】【F:.codex/implementation/player-foe-reference.md†L63-L65】【F:.codex/implementation/stats-and-effects.md†L6-L13】 Adding a card that turns crit bursts into temporary tailwinds diversifies defensive builds without stepping on Iron Guard's stacking armor niche.

## Details
* Ship **Tempest Pathfinder** as a 2★ card granting +55% Dodge Odds baseline so it anchors evasive parties alongside LadyWind or other crit hunters.【F:.codex/implementation/card-inventory.md†L49-L56】【F:.codex/implementation/player-foe-reference.md†L63-L65】
* Listen for `crit`/`damage_dealt` events: whenever an ally crits, pulse a 1-turn +12% dodge buff to the whole party and log who triggered it. Add a soft cooldown of one trigger per team turn to prevent permanent uptime while still rewarding rapid-fire crit comps.【F:.codex/implementation/stats-and-effects.md†L33-L63】
* Include action timeline telemetry (e.g., `card_effect` payload with triggering ally, crit damage, and remaining cooldown) for replay clarity.

## Requirements
- Implement `backend/plugins/cards/tempest_pathfinder.py` with the stat mod, crit listener, per-turn cooldown reset (hook into `turn_start`), and subscription cleanup mirroring other reactive cards.
- Expand tests so crit/no-crit branches are covered, including verifying the dodge buff expires after one turn and cooldown resets correctly for multi-turn fights.
- Document the new card in `.codex/implementation/card-inventory.md` and the card design plan, calling out the crit-triggered dodge rally.【F:.codex/implementation/card-inventory.md†L49-L66】【F:.codex/planning/archive/726d03ae-card-plan.md†L47-L64】
- Add `tempestpathfinder.png` under `frontend/src/lib/assets/cards/Art/` and confirm the reward selection UI renders it.
