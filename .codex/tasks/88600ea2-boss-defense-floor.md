# Guarantee a 100 defense floor for spawned bosses

## Problem
Boss encounters generated through `autofighter.rooms.utils._build_foes` currently rely on the generic
`enforce_thresholds` clamps in `backend/autofighter/rooms/foes/scaling.py`. That logic only bumps defense
up to `2 + cumulative_rooms` (or a pressure-derived roll), so early floor bosses—especially on low
pressure—spawn with defense values in the single digits. This contradicts design expectations that
boss-tier enemies should always open with at least 100 defense so their mitigation pacing matches
the scripted movesets.

## Why this matters
* The floor boss opener feels trivial because the mitigation curve never ramps: testers have logged
  cases where a loop-one boss spawns with 6–12 defense, letting even green teams delete it in a single
  attack cycle.
* Several relics and dots (e.g., `abyssal_weakness`, `siege_banner`) assume a tankier baseline when
  calculating shred percentages; their tuning breaks down when the starting defense is effectively zero.
* Combat logs and balance docs (`backend/.codex/implementation/foe-scaling.md`) still describe a
  100-defense expectation, so the current behavior creates QA bugs and player confusion.

## Requirements
* Update the foe scaling pipeline so any foe with a boss rank (`"boss"`, `"prime boss"`,
  `"glitched boss"`, `"glitched prime boss"`) has its base defense set to **at least 100** after
  `apply_attribute_scaling` and before the final HP sync. `enforce_thresholds` is the likely hook, but
  mirror whatever stage best respects other modifiers.
* Ensure the new boss floor interacts correctly with pressure-based rolls—i.e., continue honoring
  higher pressure floors that would push defense above 100, but clamp any lower outputs up to 100.
* Add regression coverage under `backend/tests/` (e.g., expand `test_boss_room_single_foe.py` or add
  a new focused test) that spawns a floor boss at pressure 0 and asserts the resulting foe defense is
  `>= 100`.
* Update `backend/.codex/implementation/foe-scaling.md` (or the most appropriate scaling doc) to call
  out the guaranteed boss defense floor so documentation matches the new safeguards.

## Definition of done
* Floor boss spawns never report defense below 100 in manual or automated checks, even when
  `pressure == 0` and cumulative rooms are small.
* Unit/regression tests covering the boss defense floor pass locally.
* Foe scaling documentation references the boss defense clamp, keeping design notes aligned with
  implementation.

### Implementation notes (2025-02-15)
* Updated `backend/autofighter/rooms/foes/scaling.py::enforce_thresholds` to promote boss-ranked foes
  (`boss`, `prime boss`, `glitched boss`, `glitched prime boss`) to a minimum 100 defense floor while
  still honoring higher overrides and pressure rolls.
* Added `test_enforce_thresholds_clamps_boss_defense_floor` alongside the existing scaling tests to
  lock in the regression coverage for the new floor.
* Documented the guaranteed floor in `backend/.codex/implementation/foe-scaling.md` so the balancing
  notes match runtime behavior.
* Verified the focused backend suite with `uv run pytest tests/rooms/foes/test_scaling.py`.

ready for review
