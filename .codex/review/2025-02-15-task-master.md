# Task Master Review – 2025-02-15

## Kboshi Flux Cycle HoT rework
- ✅ `apply()` now persists stacks per entity, clears buffs via `remove_effect_by_source`, and scrubs HoTs through the new `EffectManager.remove_hots` helper so the first-battle bonus is truly per-run.【F:backend/plugins/passives/normal/kboshi_flux_cycle.py†L35-L130】
- ✅ Regression tests cover HoT application, cleanup on element switches, and stack-scaling healing to prevent regressions.【F:backend/tests/test_kboshi_flux_cycle.py†L1-L160】
- 🟢 Task approved and task file removed.

## Lady of Fire – Infernal Momentum
- ✅ Self-damage events now flow through `apply()` when `attacker` is `None`, invoking `on_self_damage` to add a 2-turn HoT while counterattacks still attach the DoT retaliation via the effect manager.【F:backend/plugins/passives/normal/lady_of_fire_infernal_momentum.py†L23-L102】
- ✅ Tests exercise attacker burns, self-damage healing (with and without a pre-existing effect manager), and burn scaling, so the regression suite enforces the runtime paths we flagged earlier.【F:backend/tests/test_lady_of_fire_infernal_momentum.py†L1-L193】
- 🟢 Task approved and task file removed.

## Lady Fire & Ice – Duality Engine
- ✅ Flux stacks now grant HoTs through the proper API, clear potency buffs with `remove_effect_by_name`, and debuff foes when stacks are consumed, matching the design intent.【F:backend/plugins/passives/normal/lady_fire_and_ice_duality_engine.py†L27-L147】
- ✅ New automated coverage verifies HoT application, automatic `EffectManager` creation, and stack-scaling heals to guard against future regressions.【F:backend/tests/test_lady_fire_and_ice_duality_engine.py†L1-L166】
- 🟢 Task approved and task file removed.
