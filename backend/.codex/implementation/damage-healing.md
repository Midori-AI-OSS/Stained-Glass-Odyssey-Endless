# Damage and Healing Timing Notes

## Multi-hit attack pacing

Recent changes introduced dedicated helpers for pacing additional hits so
multi-target abilities no longer resolve in a single frame. The helpers work
hand-in-hand with the main turn loop so animation events, combat logs, and
frontend timelines stay synchronised.

### Timeline breakdown

* `autofighter.rooms.battle.pacing.compute_multi_hit_timing(actor, hits)` splits
  the duration returned by `calc_animation_time` into three parts:
  1. **`base_wait`** — the leading segment that should elapse between
     `animation_start` and the first hit. This value already excludes the
     per-target pacing delay and is therefore safe to feed straight into
     `pace_sleep(base_wait / TURN_PACING)`.
  2. **`per_duration`** — the resolved `animation_per_target` (with invalid or
     missing numbers coerced to `TURN_PACING`). Spread handlers pass this forward
     so every additional hit in the sequence uses the same pacing budget, even
     if the actor modifies their stats mid-turn.
  3. **`total_duration`** — the full animation length that is broadcast through
     `animation_start`/`animation_end` BUS events and later reused by
     `impact_pause` when no explicit animation plays.

* `autofighter.rooms.battle.pacing.pace_per_target(actor, duration=per)` then
  yields for `per_duration` between each extra hit. The helper returns the raw
  multiplier fed into `pace_sleep`, which makes it trivial for tests to confirm
  the correct pacing without incurring real delays.

### Implementation playbook

* Normal attacks that trigger spread damage (e.g., `_handle_wind_spread`) and
  damage-type ultimates await `pace_per_target` before every follow-up hit. Do
  this **before** recomputing hit metadata so `attack_sequence` increments match
  the visual pacing. When an ability can fan out to dozens of enemies (for
  example Lightning's ultimate against summon-heavy encounters), track the
  cumulative pacing budget and fall back to a lightweight `pace_sleep` once the
  sum approaches `TURN_TIMEOUT_SECONDS`. This keeps the total awaited time below
  the per-turn timeout while still yielding frequently enough for cooperative
  scheduling.
* Skip the pacing call when a candidate target is already defeated—otherwise the
  loop spends unnecessary time waiting for a hit that will be skipped. After the
  delay, re-check the target's HP because another effect may have removed the
  foe while the actor was waiting.
* Feed the `per_duration` returned by `compute_multi_hit_timing` into any helper
  that schedules additional hits so the spread behaviour and the primary action
  operate off the same timing contract.
* Reuse the `base_wait` segment to align BUS events (`animation_start`/
  `animation_end`) with the visual animation. The default player turn loop
  demonstrates this by awaiting `pace_sleep(base_wait / TURN_PACING)` between
  the main hit and `animation_end`. Effects that rapidly enqueue many DoTs
  should now batch their pacing into a single `pace_sleep(YIELD_MULTIPLIER)`
  once the DoTs are applied instead of yielding after each addition.

### Testing and instrumentation

* Regression tests should monkeypatch `autofighter.rooms.battle.pacing.
  pace_sleep` and capture the multiplier produced by `pace_per_target`. See
  `backend/tests/test_damage_type_pacing.py` for examples that assert Wind,
  Fire, Light, and other damage types honour `animation_per_target` when
  emitting multi-hit sequences.
* When crafting manual test scenarios, tail the battle log: distinct `hit_landed`
  events should now arrive with perceptible spacing, and the frontend timeline
  should render the staggered impacts without compressing them into a single
  frame.
