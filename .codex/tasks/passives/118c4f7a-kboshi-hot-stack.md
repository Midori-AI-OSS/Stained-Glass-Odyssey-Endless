# Task: Give Flux Cycle Its Promised HoT

## Background
`KboshiFluxCycle` awards a damage bonus and a "small HoT" whenever his element fails to change. The passive increments `_hot_stacks` and creates a stat effect named `kboshi_flux_cycle_hot_heal_*`.

## Problem
The effect contains an empty `stat_modifiers` dict, so nothing ever heals. There is no call to the HoT manager or healing APIs, making the advertised sustain nonexistent. See `backend/plugins/passives/normal/kboshi_flux_cycle.py` lines 90-111.

## Requested Changes
- Implement the HoT using `EffectManager.add_hot` (or an equivalent helper) tied to the current stack count so the heal matches the intended magnitude.
- Remove or refactor the placeholder `StatEffect` stub.
- Add tests confirming that when Kboshi fails to change elements he receives heal ticks, and that switching elements clears the HoT.

## Acceptance Criteria
- Flux Cycle produces visible healing during turns where the element does not change.
- Resetting stacks by changing elements cancels any pending HoT as expected.
- Automated tests cover both the healing and reset paths.

## Implementation Summary
- Replaced empty `StatEffect` with real `HealingOverTime` using `EffectManager.add_hot`
- HoT healing scales with stacks: 5% max HP per stack
- Element switching now properly clears active HoTs from effect manager
- Added comprehensive tests in `tests/test_kboshi_flux_cycle.py`:
  - Test HoT is granted on failed element switch
  - Test HoT is cleared when element successfully switches
  - Test HoT healing scales with stacks

## Task Master Review (2025-10-14)
- The new damage bonus stacks compute their value from `target.atk`, which already includes prior stack modifiers. Each failed switch therefore increases the next stack by 20% of the *buffed* attack instead of the base value, overshooting the intended per-stack bonus.【F:backend/plugins/passives/normal/kboshi_flux_cycle.py†L63-L82】
- Clearing stacks on a successful element change is implemented by mutating `_active_effects` directly. Prefer using `remove_effect_by_name`/`remove_effect_by_source` to avoid bypassing `Stats` bookkeeping and future hooks.【F:backend/plugins/passives/normal/kboshi_flux_cycle.py†L54-L75】
- Please address the stacking math (and clean removal path) before resubmitting.

## Coder Follow-up (2025-10-15)
- Damage bonus stacks now use the character's base attack (`get_base_stat('atk')`) so each increment applies the intended 20% bonus regardless of existing buffs.
- Stack cleanup leverages `remove_effect_by_source` and a new `EffectManager.remove_hots` helper to clear Flux Cycle HoTs without mutating private collections.

ready for review
requesting review from the Task Master
