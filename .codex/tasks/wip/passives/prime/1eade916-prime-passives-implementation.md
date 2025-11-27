# Task: Flesh Out Prime Passive Variants

## Background
Prime tags are encounter modifiers—not a separate roster. When `backend/autofighter/rooms/foe_factory.py::build_encounter`
rolls the prime probability, it annotates the *spawned foe* (e.g., `foe.rank = "prime"` or `"prime boss"`) with no additional
setup. Because any foe template can become prime when it is the enemy, the modules in `backend/plugins/passives/prime/`
must be safe wrappers or upgrades that can sit on top of the base character. Unfortunately every module is still a two-line
stub with `pass` (e.g., `backend/plugins/passives/prime/kboshi_flux_cycle.py` lines 1-3). The passive registry therefore has
no prime entries, and any reference to a prime passive ID fails the moment the foe factory tags a character as prime. The only
way prime logic exists today is via ad-hoc checks inside normal passives (again see `luna_lunar_reservoir.py`, which multiplies
charge gain and healing whenever `"prime"` appears in the foe’s rank). Those hacks are the reason we need dedicated prime files.

## Problem
Without functional prime passives we cannot deliver the power spike or mechanical twists expected at that tier. The empty modules
also make it ambiguous whether prime passives should coexist with the base versions or replace them when the foe is tagged as prime.
That uncertainty blocks balance work and confuses anyone reading the spawn pipeline. It also keeps us stuck with hard-coded
prime branches in the base passive files for characters like Luna Midori, which defeats the purpose of having tiered passive directories.

## Requested Changes
- Define concrete prime passive classes in each module under `backend/plugins/passives/prime/`. Start from the normal versions but
  document and implement the upgrades that justify the prime tier (stronger effects, additional triggers, etc.), keeping in mind
  these classes wrap the same foes spawned elsewhere and therefore need to cooperate with the base stats/abilities.
- Ensure the new classes expose meaningful `describe()`/`get_description()` output so the UI can explain the enhancements.
- Add automated coverage (unit tests or snapshot checks) verifying that prime passives load through `PassiveRegistry` and apply their
  special rules without raising when `FoeFactory.build_encounter()` is forced to mark foes as prime.
- Document the upgrades directly in each plugin's `about`/`describe()` output so the UI and inventory surface the differences without extra `.codex` updates.
- As each prime variant lands, strip the duplicated prime-specific logic out of the matching normal passive (e.g., Luna’s charge
  multiplier) so new characters can rely purely on standalone prime modules.
- Maintain each passive’s narrative/mechanical theme—prime variants should read like exalted versions of that specific character,
  not generic “+damage” buffs.

## Acceptance Criteria
- The prime passive directory no longer contains raw placeholders; each file provides a usable passive class that can wrap any foe spawned via the factory.
- Loading the passive registry includes prime IDs, and tests confirm they can be instantiated and invoked.
- Prime passives demonstrate tier-appropriate enhancements compared to their normal counterparts.
- Plugin metadata (`about` strings or `describe()` output) clearly conveys the intent and behaviour of the prime-tier passives, including that these are foe modifiers layered onto existing characters.
- Normal passive files no longer contain hard-coded prime branches once the dedicated variant exists.

## Auditor Notes (2025-11-24) – Changes Required

1. **Spec contradicts the current codebase.** The Background/Problem sections state that every module in `backend/plugins/passives/prime/` is still a stub, yet the directory already contains concrete implementations for the full roster. Examples: `backend/plugins/passives/prime/luna_lunar_reservoir.py:1-118`, `backend/plugins/passives/prime/ally_overload.py:1-118`, and `backend/plugins/passives/prime/kboshi_flux_cycle.py:1-110` all define real subclasses with logic, metadata, and descriptions. Please audit the actual roster, document any remaining gaps, and rewrite the task so it targets work that still needs to happen instead of re-implementing files that already exist.
2. **Testing/registry requirements are already satisfied.** The task asks for coverage proving prime passives load through `PassiveRegistry`, but `backend/tests/test_prime_passives_registry.py:6-59` already asserts registration, instantiation, and the `apply_rank_passives` mapping. Similar smoke tests live in `backend/tests/test_tier_passives.py:31-73`. Update the Requested Changes/Acceptance Criteria to reflect the present test suite and call out any *additional* scenarios (if any) that still lack regression coverage.
3. **Normal-tier files no longer contain prime-only branches.** A repository search (`rg "prime" backend/plugins/passives/normal`) returns no hits, confirming that the earlier hacks (e.g., Luna’s reservoir) were already removed. If there are still specific files that need cleanup, list them explicitly; otherwise this acceptance criterion is misleading and should be rephrased to emphasize verifying the separation instead of demanding changes that already landed.

Because the specification no longer matches the repository’s state, this task has been moved back to `wip` until the brief is rewritten with accurate requirements for whatever work still needs to happen on prime passives (additional balance passes, missing variants, new documentation, etc.).
