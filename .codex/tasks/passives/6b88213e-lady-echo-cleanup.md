# Lady Echo passive cleanup

## Summary
The `LadyEchoResonantStatic` passive keeps class-level dictionaries of hit/crit
state but never clears them when Lady Echo leaves battle. This leaves stale
entries that can leak into later fights and never releases the `party_crit`
effect if the combatant is defeated while stacks remain.

## Details
* `backend/plugins/passives/normal/lady_echo_resonant_static.py` stores
  `_current_target`, `_consecutive_hits`, and `_party_crit_stacks` keyed by the
  entity id, but there is no `on_defeat`/`battle_end` hook to remove those
  entries or to strip the applied crit buff effect. 【F:backend/plugins/passives/normal/lady_echo_resonant_static.py†L22-L115】
* The passive registry will call an `on_defeat` hook when provided, so we can
  free state when the unit is knocked out. 【F:backend/autofighter/passives.py†L152-L172】

## Tasks
1. Add a defeat/battle-end cleanup path for `LadyEchoResonantStatic` that removes
   stored dictionary entries and strips the `party_crit` effect from the defeated
   unit.
2. Ensure any added cleanup is safe to call multiple times and does not raise if
   the dictionaries lack the key.
3. Cover the new behavior with a focused test (or extend an existing one) that
   asserts state is cleared after defeat.

## Definition of Done
* Lady Echo’s passive no longer retains state after defeat and the crit buff
  effect is removed.
* Tests exercising the cleanup pass.

ready for review
