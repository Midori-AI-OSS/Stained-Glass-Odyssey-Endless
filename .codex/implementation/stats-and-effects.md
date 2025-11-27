# Stats and Effect Handling

Defines shared combat statistics and the manager that applies damage and healing over time.

## Stats Fields
The `Stats` dataclass stores core attributes for both players and foes:

- **Core:** `hp`, `max_hp`, `exp`, `level`, `exp_multiplier`, `actions_per_turn`
- **Offense:** `atk`, `crit_rate`, `crit_damage`, `effect_hit_rate`, `damage_type`
- **Defense:** `defense`, `mitigation`, `regain`, `dodge_odds`, `effect_resistance`
- **Vitality & Advanced:** `vitality`, `action_points`, `damage_taken`, `damage_dealt`, `kills`, `aggro`
- **Status Lists:** `passives`, `dots`, `hots`, `relics`
- **Party:** `gold`, `rdr` – run-wide currency and rare drop rate multiplier applied to gold, upgrade item counts, relic odds, pull ticket chances, and (at extreme values) can roll to raise relic and card star ranks
- **Ultimate:** `ultimate_charge`, `ultimate_ready` – charge builds with actions to power character ultimates. Ice characters gain additional charge whenever an ally acts via `handle_ally_action`.

`damage_type` is a `DamageType` plugin instance (default `Generic`). The helper
property `element_id` exposes the damage type's string identifier for
serialization and UI rendering. Characters with random damage types store their
first rolled element in the save database and reuse it on later loads so
elements stay consistent across sessions.

Experience feeds into `exp` and triggers a level-up when it meets or exceeds
`exp_to_level`. Characters below level 1000 gain experience at ten times the
normal rate to accelerate early progression. Level-ups increase core stats but
no longer restore HP, preserving damage taken.

Direct stat adjustments route through `adjust_stat_on_gain` and
`adjust_stat_on_loss`. These helpers make it possible for subclasses to
redirect bonuses or penalties to different attributes. `_on_level_up` iterates
through a `level_up_gains` map so plugins can remap growth by overriding the
dictionary or the adjust methods themselves.

`apply_damage()` and `apply_healing()` update `hp`, fire damage and healing hooks on the attacker and target damage types, and emit
global `damage_taken`, `damage_dealt`, `heal_received`, and `heal` events on the repository-wide event bus. Fire's `on_damage` hook multiplies outgoing damage by `1 + (1 - hp/max_hp)`, doubling attacks at zero HP.

## Modifiers
Stat changes may be applied in two ways:

- **Additive:** direct adjustments to integer fields like `hp`, `atk`, or `defense`.
- **Percentage:** float fields such as `crit_rate`, `crit_damage`, `effect_hit_rate`, `effect_resistance`, `vitality`, and `exp_multiplier` represent percentage modifiers.

Effects and passives mutate these fields directly. Percentage values are expressed as decimals (e.g., `0.05` for +5%).
Stat modifiers are applied through the `Stats.add_effect` API; direct legacy mutations are no longer supported.

### Player Customization
Player customization works differently from other stat modifiers. Instead of being applied as temporary effects or mods, customization values are applied directly to base stats during player instantiation. This permanent application prevents stat accumulation bugs while maintaining the intended customization experience. See `player-customization.md` for implementation details.

## EffectManager
`EffectManager` tracks `DamageOverTime` and `HealingOverTime` instances on a `Stats` object. Ticks call the target's damage type
hooks so plugins can modify dot damage or hot healing globally. Damage types may also create new DoT effects when they land
attacks via `maybe_inflict_dot`, which processes the attacker's `effect_hit_rate` in 100% chunks. Each loop subtracts the target's
`effect_resistance` and rolls for a stack using the remaining chance. Additional stacks are only attempted after a successful
roll, and the first stack always has at least a 1% chance even when resistance exceeds hit rate. Fire strikes apply the stackable Blazing Torment DoT, which gains an extra tick whenever the target acts.

- `add_dot(effect, max_stacks=None)` – registers a DoT. Effects with the same
  ID stack independently, but a `max_stacks` cap can limit simultaneous copies.
- `add_hot(effect)` – registers a HoT. Healing effects always accumulate and
  tick separately with no inherent stack limit.
- `tick(others=None)` – advances all effects, applying damage or healing and removing expired ones. DoT names are removed from `stats.dots` when finished. If `others` is provided, effects with `on_death` hooks may spread on target death.
- `on_action()` – triggers `on_action` hooks for effects that react when the target performs an action.

Active effect names are mirrored in the `Stats` lists (`dots`, `hots`) for UI display. Battle snapshots aggregate effect details from each fighter's `effect_manager`, grouping DoTs and HoTs by ID with entries exposing `id`, `name`, `damage` or `healing`, remaining `turns`, the source's ID, and stack counts. Passive IDs are similarly collapsed into `{id, stacks}` objects in the serialized snapshot.

## Buff & Debuff Plugins
Short-lived stat adjustments now use dedicated plugins under `backend/plugins/effects/buffs/` and `backend/plugins/effects/debuffs/`. Each plugin inherits from `BuffBase` or `DebuffBase` (`backend/plugins/effects/_base.py`) and produces a `StatEffect` when applied. The base class exposes helpers for naming stacks, overriding durations, and scaling modifiers at call time.

- Buffs cover common positive effects such as Attack Up, Defense Up, Speed Up, and crit modifiers.
- Debuffs provide matching reductions plus status effects like Blind and Vulnerability.

`BuffRegistry` and `DebuffRegistry` (`backend/autofighter/buffs.py`, `backend/autofighter/debuffs.py`) load these plugins via the shared `PluginLoader`. They expose helper methods to inspect available effects and apply them by ID with optional constructor overrides (`init_kwargs`) and stack metadata. This keeps discoverability on par with the DoT/HoT systems while remaining backwards-compatible with existing `StatEffect` call sites.

## Lightning Pop
Lightning attacks trigger an extra pass over the target's active DoTs. Each effect deals 25% of its damage immediately while leaving remaining turns and stack counts untouched.

## Critical Boost
Stackable effect granting +0.5% `crit_rate` and +5% `crit_damage` per stack. All stacks are removed when the affected unit takes damage.

## Aftertaste
The Aftertaste effect deals direct damage based on a small potency roll. Each hit
calculates `25 * random(0.1, 1.5)` and cards or relics may request multiple hits
by creating the plugin with a `hits` value. Every hit rolls independently.
