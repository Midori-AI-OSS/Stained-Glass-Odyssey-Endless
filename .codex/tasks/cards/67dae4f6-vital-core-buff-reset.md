# Replace Vital Core's wall-clock cooldown

## Summary
Vital Core prevents reapplying its low-HP vitality buff by storing member IDs in `active_boosts` and scheduling a hard-coded 20-second timer to clear the set. This means:
- The boost may fail to reapply even after the 2-turn buff expires if the battle resolves faster than 20 seconds.
- Long battles may re-enable the buff late because the timer fires regardless of remaining duration.
- The logic depends on the event loop running and is detached from the actual turn system.

## Details
* The card adds a member ID to `active_boosts` when the party member drops below 30% HP and starts a `loop.call_later(20, ...)` callback to remove the ID later.【F:backend/plugins/cards/vital_core.py†L23-L68】
* Buff expiration is controlled by `create_stat_buff(..., turns=2)`, so the effect manager already knows when the modifier should end. The 20-second timer is redundant and desynchronised from the turn counter.

## Requirements
- Track the vitality boost using battle events or modifier callbacks rather than a fixed wall-clock delay (e.g., remove the entry when the stat modifier expires, on heal/turn checks, or at battle end).
- Ensure the buff can reapply promptly if a member dips below 30% HP again after the original buff duration.
- Avoid leaking tasks or depending on `call_later` so the logic stays deterministic under asyncio.
- Add automated coverage demonstrating that the buff re-applies after expiring and that no wall-clock assumptions remain.
