# Task: Replace Dummy HP Effects in Infernal Momentum

## Background
`LadyOfFireInfernalMomentum` is intended to burn attackers after she takes damage and grant herself a HoT when she suffers self-inflicted fire drain.

## Problem
Both the burn and HoT rely on `StatEffect` modifiers targeting `"hp"`. The stats system ignores that key, so no damage or healing is applied. The passive therefore only grants the temporary attack boost while the reactive pieces never trigger. See `backend/plugins/passives/normal/lady_of_fire_infernal_momentum.py` lines 45-78.

## Requested Changes
- Implement proper damage-over-time application for the burn retaliation (e.g., via `EffectManager.maybe_inflict_dot` or direct `apply_damage`).
- Convert the self-damage HoT into a real heal-over-time effect through the established HoT pipeline.
- Ensure both effects respect existing mitigation/element rules where applicable.
- Add regression tests verifying attackers take burn damage and that self-inflicted drain grants a HoT tick.

## Acceptance Criteria
- Attacking Lady of Fire while the passive is active inflicts damage consistent with the description.
- Fire drain produces healing ticks that actually restore HP.
- Automated tests cover both retaliation and self-heal paths.

## Implementation Summary
- Replaced `{"hp": -burn_damage}` StatEffect with proper DamageOverTime using EffectManager.add_dot
- Replaced `{"hp": hot_amount}` StatEffect with proper HealingOverTime using EffectManager.add_hot
- Burn damage: 25% of incoming damage as 1-turn DoT
- Self-damage HoT: 50% of self-damage as 2-turn HoT
- Added comprehensive tests in `tests/test_lady_of_fire_infernal_momentum.py`:
  - Test burn retaliation is applied as DoT
  - Test burn works without effect_manager (creates one)
  - Test self-damage grants HoT
  - Test self-damage HoT works without effect_manager
  - Test burn damage scales with incoming damage

ready for review
requesting review from the Task Master

## Task Master Review (2025-10-14)
- `on_self_damage` is never invoked by the passive runtime—`PassiveRegistry` does not call that hook, so the new HoT will never fire in-game. We need either a subscription to the relevant BUS event or integration with an existing callback that runs when self-drain happens.【F:backend/plugins/passives/normal/lady_of_fire_infernal_momentum.py†L73-L94】【F:backend/autofighter/passives.py†L42-L120】
- Please update the implementation so the HoT path is actually reachable during gameplay before resubmitting.
