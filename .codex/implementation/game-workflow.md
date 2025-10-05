# Game workflow

This document describes the full runtime sequence of Midori AI AutoFighter and how player progress is persisted between runs.

## Package layout
Source code lives under the backend:

- `autofighter` – core game logic
- `plugins` – player and foe extensions
- `rooms` – battle, shop, and other endpoints
- `gacha` – pull logic and results presentation
- `saves` – load and save utilities

## Startup
- `PluginLoader` scans the `plugins/` directory to register available classes.
- `RoomManager` coordinates transitions between battle, shop, and other rooms for each run.
- The Quart app exposes endpoints that the web frontend calls to drive gameplay.
- `MapGenerator` creates 10-room floors seeded per run. By default a shop is reserved each floor, but run configuration `room_overrides` can disable or duplicate optional rooms. Pressure Level adds extra rooms and boss encounters, and chat rooms may appear after battle nodes without increasing the room count.
- Active runs persist across page reloads. The frontend caches `runId` and the next room in `localStorage`, verifies the ID via `/map/<run_id>` on startup, and resumes the current room if valid; invalid IDs are cleared.

## Run configuration metadata and start flow
- `GET /run/config` (see `backend/routes/ui.py`) returns the canonical metadata payload used by the frontend wizard. The response includes:
  - `run_types`: identifiers, labels, descriptions, default modifier presets, and allowed modifier ids. `standard` launches with zero pressure; `boss_rush` seeds pressure and foe buffs for a shorter, elite-heavy gauntlet.
  - `modifiers`: the full modifier catalog. Each entry exposes:
    - `stacking` rules (`minimum`, `step`, optional `maximum`, and defaults).
    - `effects` describing the per-stack math (e.g. foe HP +0.5× per stack, pressure encounter slot formula, etc.).
    - `diminishing_returns` metadata flagging which foe stats honour the shared diminishing curve.
    - `reward_bonuses` summarising EXP/RDR gains (foe-focused stacks grant +50% per stack; `character_stat_down` awards +5% on the first stack and +6% for each additional stack).
    - `preview` samples showing concrete numbers at representative stack counts so the wizard can echo the backend math verbatim.
  - A dedicated pressure tooltip block repeating the encounter, defense, elite-odds, and shop-tax math for hover text.
- `POST /run/start` and the `start_run` helper in `backend/services/run_service.py` now accept `run_type` and `modifiers` fields in addition to `party`, `damage_type`, and optional legacy `pressure` values. Incoming selections are validated against the metadata, normalised, and persisted inside each run record under `config`.
- The `/ui/action` `start_run` handler forwards the same payload shape so existing UI callers can adopt the wizard without switching endpoints.
- Reward calculations in `start_run` aggregate foe and player modifier bonuses:
  - Every foe-focused stack contributes +0.5 EXP/RDR (50%).
  - `character_stat_down` tracks the two-phase stat penalty (0.001× per stack until 500, then 0.000001×) while granting +5% EXP/RDR on the first stack and +6% for each additional stack (two stacks = 11%).
  - The final multipliers are included in the run snapshot and telemetry payload so downstream services and analytics can reason about the selected configuration.
- `start_run` serialises both the configuration snapshot and a condensed `RunModifierContext` into the persisted run state. Map nodes inherit the same context metadata hash so the shop, foe factory, and analytics pipelines can reconstruct the active modifiers without re-validating wizard input. The snapshot now stores a `derived_effects` block summarising foe strength score, spawn pressure, HP/speed multipliers, and shop multipliers for analytics.
- The modifier context applies the player stat penalty multiplier immediately to every party member, ensuring combat stats match the previewed difficulty adjustments. Derived foe stat multipliers, encounter slot bonuses, elite odds, shop multipliers, and pressure defense floors are cached for the map generator and foe factory. Encounter sizing consumes the spawn pressure metric so high-stack runs trade raw stats for fewer foes, and shop payloads surface active modifier summaries (and metadata hashes) to keep the frontend aligned with backend pricing math.
- `MapGenerator` hydrates nodes with the modifier context and honours configuration-driven overrides (for example, `room_overrides` disabling shops/rests) instead of relying on ad-hoc party attributes. Battle rooms inherit per-node `encounter_bonus`, elite/prime/glitched spawn percentages, and modifier metadata hashes so the foe factory can deterministically add extra combatants and enforce forced prime or glitched encounters.
- Shop rooms read the stored context to surface metadata hashes, price/tax multipliers, and encounter bonuses back to the client, keeping the UI and telemetry aligned with the selected run modifiers.
- Telemetry events (`log_run_start`, `log_menu_action`) embed the metadata snapshot, ensuring analytics retain the chosen run type, modifier stacks, and reward boosts.

## Player onboarding & menus
- A drifting color cloud fills the background while the camera stays fixed. The main menu presents an Arknights-style 2×3 grid of large Lucide icons with text labels for *New Run*, *Load Run*, *Edit Player*, *Options*, *Give Feedback*, and *Quit*. Icons show tooltips on hover, the focused option is highlighted for keyboard navigation, and the **Give Feedback** button launches a pre-filled GitHub issue in the user's browser. See [main-menu instructions](../instructions/main-menu.md) for layout details.
- A Player Creator offers body style, hair style, hair color, and accessory options while distributing 100 stat points as +1% increments. Sliders clamp allocations so totals cannot exceed the available points. Each selector and stat slider now includes a label with helper text shown on hover or keyboard focus. Spending 100 of each damage type's 4★ upgrade items adds one extra point, and remaining inventory is saved when confirming.
- Confirmed choices are saved to `player.json` and loaded for new runs. A Load Run menu lists available save files, and an Options screen shows Lucide icons with labels and tooltips for SFX volume, Music volume, Stat Screen refresh rate, and framerate controls.
- A Stat Screen scene displays grouped stats (core, offense, defense, vitality, advanced) and status lists for passives, DoTs, HoTs, damage types, and relic stacks, refreshing every few frames.
- Damage-over-time and healing-over-time effects are handled by an `EffectManager` that records active effect names on `Stats`, supports Bleed, Celestial Atrophy, Abyssal Corruption that spreads on death, Blazing Torment with extra ticks via an `on_action` hook, and Impact Echo repeating half the last hit.
- Selecting *New Run* launches the run setup wizard, which consumes the metadata above to collect the party, run type, and modifier stacks before dispatching `start_run`.
- Once configuration is confirmed the backend generates the map, applies reward multipliers to party members, and transitions to the first battle room. The loop pauses for 0.002 s between actions so the async server stays responsive.
- Shop Rooms sell upgrade items and cards with gold pricing, star ratings, floor-based inventory scaling, and reroll costs. Purchases add items to inventory, and class-level tracking ensures at least one appears per floor.
- Upgrade items convert into upgrade points via the `UpgradePanel`, letting any character spend points on stats through `/players/<id>/upgrade` and `/players/<id>/upgrade-stat`.
- Event Rooms present text prompts with selectable options that deterministically modify stats or inventory using seeded randomness. They may occur after battles without consuming the floor's room count.
 - Chat Rooms let players send a single message to an LLM character. Usage is limited to six chats per floor, and rooms should not spawn once the limit is reached.

## Wave preparation
- Before a wave begins, fighters level up and their updated state is written back to `lives/`.
- Foes are generated by combining adjectives and themed names, then modified by `foe_passive_builder.py`.

## Battle loop
- Waves play out automatically while fighters and foes exchange attacks.
- During combat, summaries append to `logs/<name>.txt`.
- When a fighter's HP reaches zero, `save_past_life` archives their data to `past_lives/<uuid>.pastlife` and deletes the active save.

## Run termination
- The game ends when all fighters have been defeated.
- The engine writes each fighter's final state to `lives/<name>.dat` (e.g., `lives/Ally.dat`) and exits—no manual action is required.
- On the next launch, surviving fighters or new ones resume from the data in `lives/`.
