# Task: Normalize Luna's Base Passive

## Background
`backend/plugins/passives/normal/luna_lunar_reservoir.py` currently contains the baseline implementation for Luna Midori's passive. To keep encounters functioning while tier folders were empty, glitched and prime-specific boosts (charge multipliers, sword charge injections, Prime-only self-healing, etc.) were hard-coded directly into the normal plugin. The Task Master guidance for this folder demands that normal-tier passives stay clean and tag-agnostic so that boss/glitched/prime folders can layer their own modifiers. Now that we are ready to build tier variants, Luna's default passive needs to shed those embedded conditionals and document the simpler baseline behaviour.

## Problem
- `_charge_multiplier`, `_sword_charge_amount`, and `_apply_prime_healing` branch on `"glitched"` and `"prime"` rank substrings even though those tags should be handled by separate passives.
- The passive exposes Prime-only healing any time Luna's rank contains `"prime"`, so normal encounters receive effects that do not belong to the baseline kit.
- Because the class internally tracks swords for every tag, tier variants cannot override behaviours cleanly—the normal version keeps re-registering swords and hard-resetting action cadence.

## Dependencies / Order
- **Start here.** This cleanup unblocks every other Luna passive task. Do not tackle the glitched, prime, or boss variants until this normalization work is merged.
- **Task Master note:** future reviewers should only adjust this blocking note when confirming the dependency state; avoid reshuffling steps elsewhere in the file.

## Requested Changes
1. Refactor `LunaLunarReservoir` so the normal plugin:
   - Grants the intended baseline charge economy (1 per action, 64 per ultimate, standard sword hits) without detecting `"glitched"` or `"prime"` in the rank string.
   - Removes `_is_glitched_nonboss`, `_is_prime`, `_charge_multiplier`, `_sword_charge_amount`, and `_apply_prime_healing` logic that references tier tags. Keep any helpers that remain relevant to the base kit, but move tier-specific pieces into a reusable mixin/helper module that tier variants can import.
2. Document in the module docstring and/or `get_description()` that this file now defines the canonical normal behaviour and intentionally omits tier boosts.
3. Update any references (e.g., `_LunaSwordCoordinator` in `backend/plugins/characters/luna.py`) if they depend on the removed helpers so that sword registration continues to work without tier hooks.
4. Ensure the passive registry still reports the same metadata (`plugin_type`, `id`, triggers, etc.) so existing saves or scripts do not break.
5. Add or adjust targeted unit coverage (smoke test or focused async test) proving that:
   - Normal Luna gains consistent charge when acting/using the ultimate.
   - Sword hits no longer multiply charge or heal based on tier tags.
6. Record the behavioural change in `.codex/implementation/player-foe-reference.md` so the roster documentation mirrors the new baseline description.

## Acceptance Criteria
- `backend/plugins/passives/normal/luna_lunar_reservoir.py` contains no conditional logic keyed on `rank` strings or tier keywords.
- Running the passive registry and Luna's character plugin shows the same baseline output as before (actions double every 25 charge, overflow buffs above 2000) without glitched/prime side effects.
- Tests confirm Luna's normal passive neither heals nor scales beyond its baseline when her `rank` is manually set to values containing `"glitched"` or `"prime"`.
- Documentation reflects that tier adjustments now live in their dedicated passives, and the normal plugin description matches the updated behaviour.
