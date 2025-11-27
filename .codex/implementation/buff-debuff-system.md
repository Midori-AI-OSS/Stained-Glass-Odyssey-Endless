# Buff & Debuff Plugin System

Establishes a discoverable home for short-term stat effects so combat systems no longer rely on ad-hoc `StatEffect` construction.

## Layout

- `backend/plugins/effects/_base.py` – shared helpers for building `StatEffect` instances
- `backend/plugins/effects/buffs/` – positive modifiers (Attack Up, Defense Up, Speed Up, crit buffs)
- `backend/plugins/effects/debuffs/` – negative modifiers (Attack Down, Blind, Vulnerability, etc.)
- `backend/autofighter/buffs.py` – loader wrapper and runtime registry for buff plugins
- `backend/autofighter/debuffs.py` – loader wrapper and runtime registry for debuff plugins

Each plugin inherits from either `BuffBase` or `DebuffBase`. These classes are lightweight dataclasses that store the plugin `id`, display name, default duration, stack metadata, and the default `stat_modifiers` dictionary applied to the target.

## Base Class Capabilities

`StatEffectPlugin` (the parent of both bases) provides:

- `build_effect_name(stack_index=None, effect_name=None)` – deterministic naming so stacks can coexist by passing `stack_index`
- `build_effect(...)` – constructs a `StatEffect` using optional duration overrides, multiplier scaling, or modifier overrides
- `apply(...)` – async helper that builds the effect and calls `Stats.add_effect`

The following keyword arguments can be passed to `apply` (directly or via the registries):

| Argument      | Purpose |
|---------------|---------|
| `stack_index` | Append `_N` to the effect name so multiple stacks survive `Stats.add_effect` replacement behaviour |
| `effect_name` | Force a specific effect name, useful for unique relic buffs |
| `duration`    | Override the plugin's default turns (`-1` keeps effects permanent) |
| `source`      | Track the effect's origin string in `StatEffect.source` |
| `modifiers`   | Replace the default `stat_modifiers` dictionary |
| `multiplier`  | Scale every modifier by a constant factor |

## Registries

`BuffRegistry` and `DebuffRegistry` are thin wrappers around `PluginLoader` that keep a single loader instance in module scope. They expose:

- `all_buffs()` / `all_debuffs()` – copy of the loaded registry for inspection or UI display
- `register()` – manual overrides for tests or dynamically generated plugins
- `apply_buff()` / `apply_debuff()` – instantiate a plugin by ID, optionally passing constructor overrides via `init_kwargs`, and call `apply` with any stack metadata keyword args

The registries are used by `backend/routes/guidebook.py` to surface the roster of buffs/debuffs for the UI. Instantiating a registry only imports plugins once because the module-level loader cache is reused.

## Usage Example

```python
from autofighter.buffs import BuffRegistry

registry = BuffRegistry()
stats = get_active_player_stats()

# Apply an Attack Up buff with a custom magnitude for 1 turn and unique stack name.
await registry.apply_buff(
    "attack_up",
    stats,
    init_kwargs={"amount": 80.0, "duration": 1},
    stack_index=0,
    source="battle_card",
)
```

For debuffs the API mirrors the above but uses `apply_debuff`.

## Backward Compatibility

Existing systems can continue instantiating `StatEffect` directly. The plugin system acts as a discoverable catalog and optional helper layer. Call sites are free to migrate incrementally by switching to `BuffRegistry`/`DebuffRegistry` without altering the surrounding logic.
