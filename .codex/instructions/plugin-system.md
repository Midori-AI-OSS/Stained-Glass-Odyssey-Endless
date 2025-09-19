# Plugin System

The game supports dynamic extensions loaded from the `plugins/` and `mods/`
directories at start-up. The `PluginLoader` traverses these directories and
imports Python modules with plugin classes.

## Directory Layout
```
plugins/
├── players/       # Player implementations
├── foes/          # Enemy implementations
├── passives/      # Passive abilities
├── dots/          # Damage-over-time effects
├── hots/          # Healing-over-time effects
├── weapons/       # Weapon behaviours
├── rooms/         # Room scenes
└── templates/     # Boilerplate files for new plugins
```

## Plugin Classes
Each plugin module should define one or more classes with:

- `plugin_type`: category string such as `player`, `passive`, `dot`, `hot`, or
  `weapon`.
- `id`: unique identifier used by the game. If omitted, the class name becomes
  the identifier.
- Required lifecycle methods like `build`, `apply`, `tick`, or `attack` depending
  on the category.

Modules that fail to import are skipped so a broken plugin does not stop the
discovery process.

## Character Behaviour Boundaries

> **Critical:** Combat behaviours, spawn weighting, and passive effects must live
> inside the character's plugin module or the passive plugin that owns the
> behaviour. Core battle utilities must stay character-agnostic—never add
> `if plugin.id == "luna"` style branches to shared managers.

- **Spawn weighting:** Override
  [`PlayerBase.get_spawn_weight`](../../backend/plugins/players/_base.py) or the
  equivalent foe hook instead of touching `foe_factory`. For example,
  [`backend/plugins/players/luna.py`](../../backend/plugins/players/luna.py)
  adjusts Luna's odds so her boss variant is six times more likely on every
  third floor, all without editing the room generator.
- **Battle preparation:** Use
  [`PlayerBase.prepare_for_battle`](../../backend/plugins/players/_base.py) or
  [`PlayerBase.apply_boss_scaling`](../../backend/plugins/players/_base.py) to
  expose special behaviour. Luna's plugin pre-allocates her astral swords from
  `prepare_for_battle` and raises their stats through `apply_boss_scaling` so
  bosses feel unique while the encounter runner stays generic.
- **Passive effects:** Attach stateful behaviour through the passive registry
  instead of hard-coding IDs in combat loops. The Lunar Reservoir passive at
  [`plugins/passives/normal/luna_lunar_reservoir.py`](../../backend/plugins/passives/normal/luna_lunar_reservoir.py)
  subscribes to `BUS` events and implements `apply`/`on_turn_end` hooks to track
  sword charge, demonstrating how to keep charge logic entirely inside the
  passive file.

By routing character-specific behaviour through these plugin hooks you make the
systems discoverable, keep the battle layer unaware of roster details, and avoid
regressions when new characters arrive.
 
## Event Bus
Plugins communicate through `EventBus` for decoupled messaging:

```
from plugins.event_bus import EventBus

bus = EventBus()
bus.subscribe("my-event", handler)
bus.emit("my-event", data)
```

## Loader Usage
```
from plugins.plugin_loader import PluginLoader

loader = PluginLoader(bus)
loader.discover("plugins")
loader.discover("mods")
players = loader.get_plugins("player")
```

When a bus is supplied, the loader assigns it to a `bus` attribute on each
registered plugin class.

Templates in `plugins/templates/` provide starting points for new plugins.

## Logging
Plugins must use the standard logging module instead of `print`.

```python
import logging

log = logging.getLogger(__name__)
```

Log messages are captured by the backend's buffered logger and written to `backend/logs/backend.log` roughly every 15 seconds. See `backend/.codex/implementation/logging.md` for more details and examples.

## Adding a New Plugin
1. Copy a template into the target category folder, e.g. `plugins/weapons/`.
2. Set `plugin_type` to match the category and provide a unique `id` string.
3. Implement any category-specific methods such as `attack`, `apply`, or `tick`.
4. Use `self.bus` to emit or subscribe to events after the loader injects the event bus.
5. Run `uv run pytest` to confirm the module imports cleanly—broken plugins are logged and skipped during discovery.

## Event Bus vs Passive Registry

The plugin ecosystem offers two primary coordination patterns:

- **Event bus** – A global asynchronous channel that batches messages and inserts brief sleeps between dispatch cycles to keep the event loop responsive. This decouples producers and consumers at the cost of global state and scheduling overhead.
- **Passive registry** – Each entity creates its own dispatcher that iterates over its equipped passives.

To align the registry with loop‑responsiveness guidelines, plan to insert a small delay such as `await asyncio.sleep(0.002)` inside long-running registry loops. This mirrors the event bus’s cooperative scheduling while retaining per-entity isolation.
