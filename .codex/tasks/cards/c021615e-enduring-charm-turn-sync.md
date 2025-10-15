# Rework Enduring Charm's low-HP buff cleanup

## Summary
Enduring Charm mirrors Vital Core's low-HP vitality buff but still uses a hard-coded 20-second timer to remove `active_boosts`. This wall-clock delay can desynchronise with turn-based battles, preventing the buff from re-triggering when it should or lingering across fights.

## Details
* The card tracks `active_boosts` and schedules `loop.call_later(20, _remove_boost)` to clear entries after two turns.【F:backend/plugins/cards/enduring_charm.py†L23-L74】
* Because the timer is wall-clock based, quick battles may finish before the timer fires, leaving `active_boosts` populated and blocking reapplication in the next combat.
* Conversely, long encounters risk the boost re-enabling late (or not at all) if combat pacing differs from the 20-second assumption.

## Requirements
- Replace the wall-clock cleanup with logic tied to the modifier lifecycle (e.g., remove from `active_boosts` when the 2-turn stat buff expires, on `battle_end`, or via event callbacks).
- Ensure the vitality bonus can reapply promptly once the effect expires or a new battle begins.
- Add regression coverage showing the boost re-triggers correctly across rapid and prolonged fights without relying on `call_later`.

ready for review

requesting review from the Task Master
