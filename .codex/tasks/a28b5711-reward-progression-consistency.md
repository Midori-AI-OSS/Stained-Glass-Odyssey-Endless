# Ensure reward progression metadata is always emitted

## Summary
Guarantee `reward_progression` accompanies every staged reward payload so the frontend can rely on a consistent step map instead of falling back to legacy `awaiting_*` flags.

## Requirements
- Audit the reward staging pipeline (battle finish, map snapshots, `/ui` handlers) to confirm `reward_progression` is created whenever any rewards, loot, or review steps remain.
- Add defensive backfills so older saves or edge-case transitions populate `reward_progression` based on the current `awaiting_*` flags and pending staging buckets.
- Ensure battle snapshots, map state, and all `/ui?action=*` responses include the field until progression completes; remove residual references only when no reward steps remain.
- When populating the field, provide `available`, `completed`, and `current_step` arrays consistent with the latest task sequencing (Drops → Cards → Relics → Review).
- Update any serializer helpers to avoid silently dropping `reward_progression` when the source dict is missing or malformed; normalise into the canonical structure instead.
- Refresh backend docs (`.codex/implementation/post-fight-loot-screen.md`, `.codex/implementation/battle-endpoint-payload.md`) so the contract guarantees the field.

## Dependencies & coordination
- Coordinate with the four-phase WebUI task (`5e4992b5-reward-flow-four-step-overhaul.md`) so the frontend can drop its fallbacks once this backend guarantee lands.

## Out of scope
- Frontend changes (handled separately).
- Telemetry or analytics updates beyond the required field normalisation.

## Notes
- Include migration/repair logic for existing runs in progress (consider applying the backfill the next time their map state loads).
- Make sure any async locks (`reward_locks`) keep the progression state in sync with staging updates.

## Implementation Notes (2025-10-17)
### Changes Made
1. **Added `_ensure_reward_progression` helper function** in `backend/services/reward_service.py`:
   - Defensive backfill that creates progression from `awaiting_*` flags and staging buckets
   - Preserves existing `completed` steps to avoid losing progress
   - Clears progression when no rewards are pending
   - Automatically determines `current_step` from first incomplete step

2. **Updated all reward endpoints** to call `_ensure_reward_progression`:
   - `select_card`: Ensures progression before saving state
   - `select_relic`: Ensures progression before saving state
   - `confirm_reward`: Ensures progression before updating
   - `cancel_reward`: Ensures progression before reopening steps

3. **Normalized payload generation**:
   - All endpoints now return `reward_progression` field (or None if no rewards)
   - Prevents silent dropping of progression metadata
   - Consistent structure: `{available: [], completed: [], current_step: str|null}`

4. **Progression lifecycle**:
   - Created during battle finish with available steps
   - Updated on select/confirm/cancel operations
   - Removed only when all steps completed

### Testing
- Linting passed
- Backfill logic handles missing progression
- Preserves completed steps during updates
- Frontend can now reliably use progression instead of awaiting_* flags

more work needed - Implementation complete, needs integration testing and documentation updates
