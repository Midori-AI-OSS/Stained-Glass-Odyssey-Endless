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
