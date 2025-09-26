# Plugin System

Describes how plugins are discovered, categorized, and connected to the event bus.

## Loader Flow
- `PluginLoader` scans each directory recursively for Python files, skipping `__init__.py` and importing the rest【F:backend/plugins/plugin_loader.py†L24-L38】
- After loading, any categories listed as required but missing raise a runtime error【F:plugins/plugin_loader.py†L40-L48】
- Classes defining `plugin_type` are registered under that category and assigned the event bus when provided【F:plugins/plugin_loader.py†L67-L74】
- Base classes are registered alongside concrete plugins; discovery code such as the foe catalog filters them out when building spawn templates【F:backend/autofighter/rooms/foes/catalog.py†L50-L98】

## Plugin Categories
The following categories are bundled:

- **Characters** – controllable and hostile combatants such as `Player` or `SlimeFoe`【F:backend/plugins/characters/player.py†L1-L24】【F:backend/plugins/characters/__init__.py†L66-L101】
- **Passives** – always-on effects like `AttackUp`【F:backend/plugins/passives/attack_up.py†L1-L16】
- **DoTs** – damage-over-time effects such as `Bleed`【F:plugins/dots/bleed.py†L4-L15】
- **HoTs** – healing-over-time effects such as `Regeneration`【F:plugins/hots/regeneration.py†L4-L9】
- **Weapons** – attack implementations such as `SampleWeapon`【F:plugins/weapons/sample_weapon.py†L4-L8】
- **Cards** – stat-boosting rewards like `MicroBlade`【F:backend/plugins/cards/a_micro_blade.py†L1-L12】
- **Relics** – run-limited party buffs such as `BentDagger`【F:backend/plugins/relics/bent_dagger.py†L1-L9】
- **Rooms** – scene definitions such as `SampleRoom`【F:plugins/rooms/sample_room.py†L1-L3】

## Plugin Class Requirements
- `plugin_type` – category string used by the loader when registering the class【F:plugins/plugin_loader.py†L67-L72】
- `id` *(optional)* – unique identifier; defaults to the class name【F:plugins/plugin_loader.py†L70-L72】
- Category-specific methods (`attack`, `apply`, `tick`, etc.) invoked by game systems
- Passive plugins expose stack metadata with `stack_display`:
  - `spinner` for single-stack or always-active effects (`max_stacks == 1`)
  - `pips` for passives without a stack limit or with a `max_stacks` cap of five or fewer
  - `number` for passives with a numeric `max_stacks` cap above five
- During discovery the loader injects the event bus as `bus` on each class【F:plugins/plugin_loader.py†L67-L74】

## Event Bus Integration
`PluginLoader` assigns an `EventBus` instance to each plugin, letting them emit and subscribe to events without relying on a global messenger【F:plugins/event_bus.py†L13-L41】【F:plugins/plugin_loader.py†L67-L74】
All emissions sleep for 0.002 s after each callback to keep the loop fair.

## Adding New Plugin Types
1. Create a new subfolder under `plugins/` for the category.
2. Define classes with a unique `plugin_type` string and optional `id`.
3. Call `PluginLoader.discover` on the new directory and access the category via `get_plugins`.
4. Update `required` when constructing `PluginLoader` if the game should fail when the category is missing.

## Adding a Plugin
1. Copy a template from `plugins/templates/` into the desired category folder.
2. Implement the class with `plugin_type` and optional `id`.
3. Write category-specific behaviour.
4. Run `discover`; import failures are logged and reported without stopping other plugins【F:plugins/plugin_loader.py†L28-L44】.
