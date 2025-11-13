# Task: Author Luna's Boss-Tier Passive

## Background
Boss tags are layered onto foes at spawn time, but Luna currently lacks a dedicated boss-tier passive module inside `backend/plugins/passives/boss/`. Encounters flagged as `"boss"` or `"glitched boss"` therefore reuse the baseline passive, leaving climactic fights without unique pacing or counterplay. With the normal passive being simplified, we now need to design a boss modifier that expresses Luna's “clockmaker in a storm” fantasy while remaining compatible with other tags (glitched/prime) that may stack.

## Problem
- There is no `backend/plugins/passives/boss/luna_lunar_reservoir.py`, so the passive registry cannot attach a boss upgrade when Luna is spawned as a boss.
- Designers have no canonical place to describe boss-only enhancements such as accelerated charge spillover, sword splitting, or targeted debuffs.
- Without a boss plugin ID, we cannot selectively balance Luna boss encounters or write tests for them.

## Dependencies / Order
- **Blocked by** the base cleanup task `.codex/tasks/passives/normal/d7d772d6-luna-passive-normalization.md`.
- Should begin **after** the glitched (`4499b34b-luna-glitched-passive.md`) and prime (`91661353-luna-prime-passive.md`) variants so boss stacking rules can reference their finalized mechanics.
- **Task Master note:** limit edits in this section to dependency status updates during reviews; do not rewrite other parts of the task.

## Requested Changes
1. Add a boss-tier passive module under `backend/plugins/passives/boss/` (e.g., `luna_lunar_reservoir.py`) that either composes the normal passive or subclasses it to add:
   - Faster charge accumulation and/or higher overflow conversions tuned for boss difficulty.
   - A mechanic that pressures the player (e.g., periodic sword storms, time dilation debuffs) while fitting Luna's theme.
   - Metadata fields (`plugin_type`, `id`, `name`, `trigger`, etc.) clearly identifying it as the boss variant.
2. Ensure the boss modifier cooperates with other tags:
   - Check for existing glitched/prime helpers before modifying state so that combo tags (boss+glitched, boss+prime) remain stable.
   - Document how stacking behaves in a module docstring.
3. Update the character documentation entry for Luna (and any encounter notes in `.codex/implementation/player-foe-reference.md`) to mention the boss-tier behaviour.
4. Provide coverage or a focused integration test that forces a Luna encounter with `rank = "boss"` and proves the new passive loads and executes its unique effect.

## Acceptance Criteria
- A fully defined Luna boss passive file exists and registers without loader errors.
- Boss-only mechanics no longer live in the normal passive; they are isolated to the boss module.
- Stack interactions with glitched/prime tags are documented and do not throw runtime exceptions.
- Tests or reproducible scripts demonstrate the boss passive in action, and docs highlight the new behaviour.
