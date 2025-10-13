# Task: Implement Real Healing for Duality Engine Stack Consumption

## Background
`LadyFireAndIceDualityEngine` should heal allies and debuff foes whenever the character reuses the same element twice. The current implementation creates a `StatEffect` with an `"hp"` modifier to simulate a HoT.

## Problem
`StatEffect` modifiers feed into `_calculate_stat_modifier`, which does not understand `"hp"`. Adding the effect therefore does nothing; no healing occurs and the UI does not reflect a HoT. The code also directly manipulates `_active_effects` to clear potency stacks. See `backend/plugins/passives/normal/lady_fire_and_ice_duality_engine.py` lines 85-121.

## Requested Changes
- Replace the fake HoT with real healing over time using `EffectManager.add_hot` (or the appropriate helper) so stacks produce visible healing.
- Avoid manual mutation of `_active_effects`; rely on `remove_effect_by_name` or other supported APIs when clearing potency bonuses.
- Confirm foe mitigation debuffs still apply when stacks are consumed.
- Add coverage that builds flux stacks, consumes them, and verifies healing ticks plus mitigation debuffs actually occur.

## Acceptance Criteria
- Consuming Flux stacks produces tangible healing through the battle healing system and debuffs enemies as described.
- Internal state cleanup uses supported effect APIs (no direct `_active_effects` surgery).
- Automated tests exercise the stack gain/consumption path.
