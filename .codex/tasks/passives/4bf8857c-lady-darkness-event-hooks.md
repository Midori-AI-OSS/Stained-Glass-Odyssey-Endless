# Task: Wire Eclipsing Veil Into DoT & Debuff Events

## Background
`LadyDarknessEclipsingVeil` is designed to siphon healing on every DoT tick and grant permanent attack bonuses when she resists debuffs. The passive defines `on_dot_tick` and `on_debuff_resist` helpers, but the core `apply()` body only drops stat effects.

## Problem
No event subscriptions exist for the passive, and `PassiveRegistry` never calls these helpers by default. As a result, the siphon HoT and resist-based attack buffs never fire. See `backend/plugins/passives/normal/lady_darkness_eclipsing_veil.py` lines 24-75 alongside the lack of any `BUS.subscribe` calls.

## Requested Changes
- Subscribe to the relevant battle bus events (e.g., `dot_tick`, `debuff_resisted` or whichever signal the combat system emits) when the passive initializes, and clean up the handlers on defeat/battle end.
- Ensure `on_dot_tick` receives the actual DoT damage value and applies healing through the standard heal pipeline.
- Verify debuff resistance events propagate to the passive and correctly stack the +5% attack bonus.
- Add targeted tests demonstrating healing triggers on DoT ticks and attack bonuses appear after resisting debuffs.

## Acceptance Criteria
- Lady Darkness passively heals when any DoT ticks on the battlefield and gains stacking attack buffs when she resists debuffs.
- Event subscriptions are cleaned up to avoid leaks when battles end.
- Automated tests cover both the DoT siphon and resist bonus flows.
