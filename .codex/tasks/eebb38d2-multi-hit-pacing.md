# Smooth pacing for multi-hit attack sequences

## Summary
Coder, fix the battle pacing so multi-hit sequences (e.g., wind spreads and ultimates) respect each attacker's animation timings instead of firing in a single frame.

## Requirements
- Replace `YIELD_MULTIPLIER` micro-sleeps that run inside hit loops with a pacing helper that sleeps for the actor's `animation_per_target` (fallback to `TURN_PACING`) so every extra hit waits a meaningful amount of time before damage lands.
- Ensure the initial hit still respects `animation_duration`: integrate the new helper with the existing `animation_start`/`animation_end` events so the total wait time matches `calc_animation_time(actor, targets)` without double-counting.
- Update all battle paths that emit rapid-fire hit events, including `_handle_wind_spread` in `backend/autofighter/rooms/battle/turn_loop/player_turn.py` and Wind's ultimate in `backend/plugins/damage_types/wind.py`; audit other damage-type plugins for similar loops and move them to the new helper as needed.
- Add regression coverage that asserts the helper is invoked with a multiplier derived from `animation_per_target` when multiple hits occur (e.g., instrument `_handle_wind_spread` via monkeypatch to capture `pace_sleep` arguments).
- Document the new pacing behavior in `.codex/implementation/damage-healing.md` (or a more appropriate combat doc) so future contributors understand how multi-hit timing is calculated.

## Acceptance criteria
- Observing a battle with multi-hit attacks shows hits spaced by the configured animation timings rather than occurring simultaneously.
- Tests in `backend/tests/` verify multi-hit flows wait for non-trivial intervals, and existing animation timing tests continue to pass.

## Auditor notes (2025-02-15)
- Battle pacing helpers (`pace_per_target`, `compute_multi_hit_timing`) behave as expected and regression tests pass, but the documentation requirement was missed.
- `.codex/implementation/damage-healing.md` still lacks any explanation of the new multi-hit timing model—please document how per-target animation pacing is calculated.

## Coder notes (2025-02-16)
- Expanded `.codex/implementation/damage-healing.md` with timeline breakdown, implementation guidance, and testing tips covering the multi-hit pacing helpers.

## Auditor notes (2025-02-19)
- Re-ran `uv sync` and `uv run pytest tests/test_damage_type_pacing.py` to confirm the new regression coverage executes cleanly.
- Spot-checked `_handle_wind_spread` plus all multi-hit damage-type ultimates to verify they await `pace_per_target` before each additional strike and skip defeated targets without burning extra pacing budget.
- Confirmed `compute_multi_hit_timing` integrates with the turn loop so animation bus events use the resolved `base_wait`/`total_duration` while spread helpers share the same `per_duration` budget.
- Reviewed `.codex/implementation/damage-healing.md` to ensure the helper behavior and testing guidance are now documented for future contributors.

requesting review from the Task Master
