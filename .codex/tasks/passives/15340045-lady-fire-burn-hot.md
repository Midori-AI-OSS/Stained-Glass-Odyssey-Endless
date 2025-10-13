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
