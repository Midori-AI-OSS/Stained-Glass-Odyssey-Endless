# Core Architecture

1. Implement a lightweight backend core without legacy imports.
2. Route events through the internal `EventBus` and async tasks while keeping loops light for low-end hardware.
3. Replace direct rendering with data-only responses consumed by the web frontend.
4. Rebuild the plugin loader and APIs so new player, weapon, passive, DoT, and HoT plugins mirror current concepts without reusing legacy code and expose a mod interface.
   - Add tests verifying discovery of modules under `mods/` to catch empty packages.
5. Add a scene manager capable of swapping menus, gameplay states, and overlays.
   - Handle exceptions gracefully and recover from failed scene loads.
6. Organize source under the `autofighter` and `plugins` packages with submodules (`rooms/`, `gacha/`, `saves/`).
7. Define a `Stats` dataclass holding core attributes; share between players and foes.
8. Provide an `EventBus` so plugins can subscribe and emit without engine imports.
