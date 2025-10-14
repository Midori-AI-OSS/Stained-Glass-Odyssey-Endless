# Task: Restore Lady Echo's Consecutive Hit Tracking

## Background
The `LadyEchoResonantStatic` passive is supposed to scale party crit rate when Lady Echo chains hits on the same foe. The plugin relies on tracking consecutive hits and stacking bonuses via `on_hit_target`.

## Problem
`PassiveRegistry` only calls special hooks named `on_hit_landed` for hit events. `LadyEchoResonantStatic` implements `on_hit_target` instead, so the tracking branch never executes and the party crit stacks stay at zero. Only the base DoT-scaling buff in `apply()` ever runs. See `backend/plugins/passives/normal/lady_echo_resonant_static.py` lines 18-100.

## Requested Changes
- Update the passive to respond to the actual hook emitted by `PassiveRegistry` (either rename to `on_hit_landed` or provide an adapter that delegates to the existing logic).
- Ensure the helper receives damage/target context just like other passives (e.g., compare with `lady_lightning_stormsurge`).
- Add regression coverage proving that consecutive hits on the same enemy now increment `get_party_crit_stacks` and that switching targets resets the stacks.

## Acceptance Criteria
- Automated tests cover the crit stack growth and reset behavior for Lady Echo's passive.
- No regressions to the existing DoT scaling effect (chain bonus should still apply based on DoTs present).
- Documentation or in-file docstring updated if behavior notes change.
ready for review
