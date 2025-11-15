# Task: Create Luna's Prime Passive Variant

## Background
Prime tags represent exalted foes, but Luna currently reuses her normal passive with hard-coded `rank` checks for `"prime"`. Once the normal file is cleaned up, those effects vanish entirely unless we introduce a proper prime plugin under `backend/plugins/passives/prime/`. We need a dedicated variant that captures Luna's “lunar reservoir overflowing into spacetime control” fantasy while staying modular with other tags.

## Problem
- There is no `backend/plugins/passives/prime/luna_lunar_reservoir.py`, so prime encounters cannot load bespoke mechanics.
- Prime-specific hooks (per-hit micro healing, massive charge multipliers) are stranded in the normal file, making it impossible to tune prime balance without affecting baseline gameplay.
- Documentation and encounter planners lack a canonical description or ID for Luna's prime behaviour.

## Dependencies / Order
- **Blocked by** `.codex/tasks/passives/normal/d7d772d6-luna-passive-normalization.md`. Base passive cleanup must land first so prime perks can move cleanly.
- Should be completed before boss-tier stacking work so the boss variant can reference the finalized prime mechanics.
- **Task Master note:** only update this dependency block during reviews when the order changes; leave the rest of the task history intact.

## Requested Changes
1. Implement a prime-tier passive module that:
   - Imports/reuses the normal `LunaLunarReservoir` but layers on exalted perks such as higher charge multipliers, enhanced overflow buffs, or the micro-healing previously seen in `_apply_prime_healing`.
   - Declares unique metadata (`id = "luna_lunar_reservoir_prime"` or similar) so the passive registry can distinguish it.
   - Adds thematic copy in `about()`/`describe()` explaining how Prime Luna manipulates reservoir energy.
2. Move Prime-only helpers (healing taps, 5× sword charge, extra action scaling) out of the normal passive and into this file or a shared mixin imported by both normal and tiered variants.
3. Guard the implementation so it can coexist with boss/glitched modifiers (e.g., skip double-registration of swords, expose hooks other tiers can call into).
4. Update `.codex/implementation/player-foe-reference.md` (and any other roster docs) to call out the prime variant and its signature mechanics.
5. Add coverage or a deterministic repro showing that forcing a Luna encounter to `rank = "prime"` loads the new passive and produces the expected healing/charge bonuses.

## Acceptance Criteria
- A concrete prime passive module exists under `backend/plugins/passives/prime/` with complete metadata and behaviour.
- Prime-only features are no longer present in the normal passive, but they remain available when the prime tag is applied.
- The passive registry exposes the new ID, and stacked tags (prime boss, prime glitched) operate without errors.
- Documentation and tests demonstrate Prime Luna's upgraded behaviour.
