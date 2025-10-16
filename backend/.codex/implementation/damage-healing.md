# Damage and Healing Timing Notes

## Multi-hit attack pacing

Recent changes introduced a dedicated helper for pacing additional hits so
multi-target abilities no longer resolve in a single frame.

* `autofighter.rooms.battle.pacing.pace_per_target(actor)` now sleeps for the
  actor's `animation_per_target` duration (falling back to `TURN_PACING` when an
  invalid or zero value is configured). The helper returns the multiplier passed
  to `pace_sleep`, making it easy for tests to assert the intended pacing.
* `autofighter.rooms.battle.pacing.compute_multi_hit_timing(actor, hits)` splits
  the total animation length reported by `calc_animation_time` into the base
  `animation_duration` segment and the per-target delays consumed by
  `pace_per_target`. The attack loop uses the base segment to drive
  `animation_start`/`animation_end` events while the helper spaces out each
  subsequent hit.
* Normal attacks that trigger spread damage (e.g., Wind spreads) and damage type
  ultimates now call `pace_per_target` instead of the previous
  `YIELD_MULTIPLIER` micro-sleep. This ensures observers see distinct hit timing
  in the log stream and on the frontend timeline.

When authoring new multi-hit behaviours, always:

1. Invoke `pace_per_target` before issuing each extra hit so the damage lands in
   a staggered sequence. Skip the call when the candidate target is invalid or
   already defeated to avoid compounding the pacing delay, and re-check the
   target's HP after the delay in case another effect removed it while waiting.
2. Reuse the `compute_multi_hit_timing` breakdown to avoid double-counting
   delays when emitting animation telemetry or calling `impact_pause`.
3. Update regression tests to monkeypatch `pace_sleep` if you need to observe
   the pacing multiplier without incurring real-world delays.
