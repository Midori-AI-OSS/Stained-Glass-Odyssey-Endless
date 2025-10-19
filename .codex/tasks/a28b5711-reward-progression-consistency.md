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

## Audit (2025-02-15)
- Verified `runs.lifecycle.ensure_reward_progression` rebuilds and normalises the canonical progression structure based on staging buckets, awaiting flags, and battle review, and that map loads/saves now guarantee the field.
- Confirmed reward selection/confirmation flows mirror `reward_progression` into payloads and snapshots until steps finish, and documentation in backend/.codex/implementation now promises the contract.
- Setup backend env with `uv sync` and ran `uv run pytest tests/test_reward_staging_service_hooks.py tests/test_reward_staging_confirmation.py tests/test_reward_gate.py` (all passed).

## Coder verification (2025-02-19)
- `/ui?action=advance_room` now returns `reward_progression`, gating flags, and the next step indicator whenever the handler advances progression without moving rooms.
- Updated `.codex/implementation/post-fight-loot-screen.md` and `.codex/implementation/battle-endpoint-payload.md` to document the guarantee.
- Backend env synced with `uv sync`; ran `uv run pytest tests/test_reward_staging_service_hooks.py tests/test_reward_staging_confirmation.py tests/test_reward_gate.py` (pass).

ready for review
