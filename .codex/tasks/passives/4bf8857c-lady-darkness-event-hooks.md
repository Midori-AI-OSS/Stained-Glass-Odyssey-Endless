# Task: Wire Eclipsing Veil Into DoT & Debuff Events

## Background
`LadyDarknessEclipsingVeil` is designed to siphon healing on every DoT tick and grant permanent attack bonuses when she resists debuffs. The passive defines `on_dot_tick` and `on_debuff_resist` helpers, but the core `apply()` body only drops stat effects. For a refresher on how our DoT/debuff events are emitted, check the battle plug-in modules under `backend/plugins/`—particularly `backend/plugins/event_bus.py` for subscription patterns and the existing DoT definitions in `backend/plugins/dots/`.

## Problem
No event subscriptions exist for the passive, and `PassiveRegistry` never calls these helpers by default. As a result, the siphon HoT and resist-based attack buffs never fire. See `backend/plugins/passives/normal/lady_darkness_eclipsing_veil.py` lines 24-75 alongside the lack of any `BUS.subscribe` calls, then mirror the hook-up patterns used by other plug-ins inside `backend/plugins/passives/` when wiring the handlers.

### Event reference
- `DamageOverTime.tick` (`backend/autofighter/effects.py`) emits `BUS.emit_async("dot_tick", attacker_or_none, target, dmg, dot_name, metadata)` before damage is applied. `on_dot_tick` should subscribe to that signature and check whether either `attacker` or `target` belongs to Lady Darkness' party.
- Debuff resistance flows emit `effect_resisted` events (see `EffectManager.add_dot` and the various card/relic handlers). We do not currently fire a dedicated `debuff_resisted` signal, so subscribe to `effect_resisted` and filter by `target`/`details` instead of waiting for a nonexistent event.
- Follow cleanup patterns from passives like `lady_light_radiant_aegis` (stores teardown callbacks in class dictionaries and unsubscribes on `battle_end`).

## Requested Changes
- Subscribe to the relevant battle bus events (e.g., `dot_tick`, `debuff_resisted` or whichever signal the combat system emits) when the passive initializes, and clean up the handlers on defeat/battle end.
- Ensure `on_dot_tick` receives the actual DoT damage value and applies healing through the standard heal pipeline.
- Verify debuff resistance events propagate to the passive and correctly stack the +5% attack bonus.
- Add targeted tests demonstrating healing triggers on DoT ticks and attack bonuses appear after resisting debuffs.

### Implementation notes
- `apply()` already adds a permanent `StatEffect` for DoT duration; extend it so, after instantiating the effect, it resolves the owning `Stats` object, registers BUS callbacks, and stores teardown lambdas in a class-level dict keyed by `id(target)`. Use `BUS.unsubscribe` inside the teardown to avoid leaking handlers across battles.
- Tests can live alongside existing passive suites (`backend/tests/test_advanced_passive_behaviors.py` or a new dedicated file). Simulate DoT ticks via `await BUS.emit_async("dot_tick", attacker, target, dmg, "Bleed", {...})` and emit `effect_resisted` to confirm attack stacking works.

## Acceptance Criteria
- Lady Darkness passively heals when any DoT ticks on the battlefield and gains stacking attack buffs when she resists debuffs.
- Event subscriptions are cleaned up to avoid leaks when battles end.
- Automated tests cover both the DoT siphon and resist bonus flows.
