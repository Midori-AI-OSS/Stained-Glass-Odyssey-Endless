# Task Audit – 2025-02-15

## Completed
- **67dae4f6 – Replace Vital Core's wall-clock cooldown**: Confirmed card now tracks active boosts by effect id, removes entries on effect expiry/defeat/battle end, and rechecks thresholds on damage or turn start. Automated regression `test_vital_core_reapplies_after_expiration` exercises the lifecycle. Requirements satisfied; task file removed.

## Outstanding
- **185897b3 – Trim EventBus cooperative sleeps**: `backend/plugins/event_bus.py` still enforces fixed 2 ms `asyncio.sleep` calls on batched dispatch (lines 217–237) and per subscriber (line 283). No adaptive pacing implemented yet.
- **64309131 – Cache battle setup modifiers**: `setup_battle` continues to clone party members and call `apply_cards`/`apply_relics` with full iteration every fight (`backend/autofighter/rooms/battle/setup.py` lines 70–125). No caching or incremental diffing present.
- **6f3d0a42 – Stage reward modifiers**: Reward service still appends card/relic ids directly and saves the party immediately (`backend/services/reward_service.py` lines 20–118). No staging/previews implemented.
- **cbd083cc – Expand snapshot history**: `_RECENT_EVENT_LIMIT` remains `6` in `backend/autofighter/rooms/battle/snapshots.py` (line 27). Retention strategy unchanged.
- **adfe4d59 – Harmonize turn pacing defaults**: Backend default remains `0.2` (`backend/autofighter/rooms/battle/pacing.py` line 11) while config API/UI still use `0.5` (`backend/routes/config.py` line 21). Intro delay logic untouched.
- **passives/4bf8857c – Lady Darkness event hooks**: Passive defines helpers but still lacks EventBus subscriptions in `backend/plugins/passives/normal/lady_darkness_eclipsing_veil.py` (entire module).
- **passives/6a3ea15b – Hilander bus cleanup**: `HilanderCriticalFerment` still omits defeat/battle-end cleanup of the `critical_hit` subscription (`backend/plugins/passives/normal/hilander_critical_ferment.py` lines 60–118).
- **passives/6b88213e – Lady Echo cleanup**: Static class dicts remain without defeat cleanup in `backend/plugins/passives/normal/lady_echo_resonant_static.py` (lines 10–90).
- **cards/c021615e – Enduring Charm turn sync**: Card continues to register a 20-second `call_later` to clear boosts (`backend/plugins/cards/enduring_charm.py` lines 31–56). Needs event-driven cleanup similar to Vital Core.
- **relics/1e2c2fc3 – Rusty Buckle threshold docs**: `_threshold_multiplier` lacks clarifying comments/docs in `backend/plugins/relics/rusty_buckle.py` (lines 180–214). Implementation unchanged.

## Next Steps
- Follow up with Coders to address outstanding combat pacing, reward staging, passive cleanup, and documentation tasks.
- Coordinate with UX on pacing defaults before adjusting intro delays.
