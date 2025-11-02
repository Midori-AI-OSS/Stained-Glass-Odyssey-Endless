# Eclipse Reactor Surge Balancing

Eclipse Reactor fills the remaining 5★ slot that rewards aggressive pacing by
converting ally HP directly into a short-lived overclock. The relic drains a
fixed chunk of health up front before pivoting into a sustained bleed, keeping
both halves of the effect easy to reason about during balancing discussions.

## Key Numbers
- **Opening sacrifice:** 18% Max HP per stack, applied on `battle_start` and
  clamped so allies can never drop below 1 HP. This mirrors Cataclysm Engine's
  use of `safe_async_task` for synchronous damage and keeps fragile parties from
  wiping instantly.
- **Surge window:** A flat **3-turn** buff regardless of stack count. Each stack
  increases the multipliers by +180% ATK, +180% SPD, and +60% crit damage
  (implemented with `bypass_diminishing=True` so the full values land even on
  capped crit builds).
- **Aftermath bleed:** Once the surge expires the relic inflicts 2% Max HP per
  stack each turn for the rest of the battle. The drain begins on the fourth
  `turn_start`, letting players enjoy exactly three empowered turns before the
  downside takes over.

## Stacking Behavior
- Stacks **do not** extend the surge duration; they only scale both the opening
  sacrifice and the multipliers. This keeps the relic predictable across single-
  and multi-stack runs while still giving higher stacks a noticeable risk bump.
- The state tracker rebuilds the modifier list on every `apply()` call so adding
  extra copies mid-run refreshes the surge values without duplicating hooks.

## Telemetry Hooks
- `initial_hp_drain`, `surge_activated`, `surge_expired`, and the ongoing
  `hp_drain` events surface the key trade-offs directly in battle logs. The
  payloads report stack count, percentage values, and the projected HP after the
  initial sacrifice so analysts can compare against Omega Core and Greed Engine
  runs.

## References
- `backend/plugins/relics/eclipse_reactor.py`
- Tests covering clamp, duration, drain transition, and cleanup live in
  `backend/tests/test_relic_effects_advanced.py`.
