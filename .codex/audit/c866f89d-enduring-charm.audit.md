# Audit – Enduring Charm turn sync (Task cards/c021615e)

## Scope Reviewed
- backend/plugins/cards/enduring_charm.py
- backend/tests/test_enduring_charm.py
- Historical review context in .codex/review/2025-02-15-task-audit.md

## Findings
### ✅ Requirements satisfied
1. **Lifecycle-driven cleanup** – The card now registers event handlers for `effect_expired`, `entity_defeat`, and `battle_end`, removing entries from `active_boosts` when the vitality modifier ends or the battle finishes. The wall-clock `loop.call_later` has been removed entirely, and low-HP checks run on `turn_start`/`damage_taken` to reapply when thresholds are met.【F:backend/plugins/cards/enduring_charm.py†L19-L105】
2. **Reapplication coverage** – Regression tests confirm the buff re-triggers immediately after the two-turn modifier expires and after a battle ends, without relying on timers. The tests manually tick the effect manager and simulate combat transitions to demonstrate the new behavior.【F:backend/tests/test_enduring_charm.py†L34-L138】

### ⚠️ Observations
- The helper re-checks all party members whenever damage is taken or a turn starts. This mirrors Vital Core’s pattern, but if combat profiling shows it’s hot, consider narrowing the triggers (e.g., track candidates that dipped below threshold). No blockers for merge.

## Verification
- `uv run pytest tests/test_enduring_charm.py`

## Recommendation
All acceptance criteria are met. I recommend Task Master approval.
