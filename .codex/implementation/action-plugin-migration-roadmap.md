# Action Plugin Migration Roadmap

## Executive Summary
- Identified 12 combat actions that still live outside `ActionBase`/`ActionRegistry`: seven damage-type ultimates, three special (on-action) behaviors, and two summon-creation flows (Luna's swords and the `Phantom Ally` card). These live in `backend/plugins/damage_types/*`, `backend/autofighter/rooms/battle/turn_loop/player_turn.py`, and summoning helpers such as `backend/plugins/characters/luna.py:303`.
- Recommended migration order: start with the deterministic on-action behaviors (Light healing, Dark drain, Wind spread) so the turn loop starts delegating work to plugins, then move to the ultimates, and finally tackle summons/card actions that need `SummonManager` context.
- Rough effort: each ultimate or summon action is a medium-sized story (1-2 days) because it touches pacing, effect managers, and event hooks; the smaller on-action hooks are quicker (~half a day each).

## Detailed Findings

### 1. Combat Actions (HIGH PRIORITY)
- **Light ultimate (ally cleanse/heal + enemy defense debuff)** – `backend/plugins/damage_types/light.py:49`
  - Category: `ActionType.ULTIMATE`
  - Complexity: medium (multi-target heals + DoT removal + stat buff + event emissions via `autofighter.stats:BUS`).
  - Dependencies: `EffectManager` for cleanses, `StatEffect`/`create_stat_buff` for the defense debuff, and pacing helpers (`pace_per_target`).
  - Priority: high because all Light characters rely on this signature ultimate; migrating it unlocks plugging ultimates into the registry.
  - Rationale: centralizing the healing/cleanse/debuff choreography in a plugin makes it possible to reuse `BattleContext.apply_healing`/`damage` and reuse the registry's cooldown/cost handling instead of sprinkling side effects in the turn loop.

- **Dark ultimate (6x hits scaling with ally DoTs)** – `backend/plugins/damage_types/dark.py:88`
  - Category: `ActionType.ULTIMATE`
  - Complexity: medium-high due to stack counting, target selection (`select_aggro_target`), and repeated `apply_damage`/pacing.
  - Dependencies: `EffectManager` for DoT stack counting, `BUS.emit_async("damage")`, and stored `_pending_dark_bonus` logic in `Stats`.
  - Priority: high because the ability already manipulates combat metadata and interacts with `damage_type.on_damage` hooks.
  - Rationale: migrating this ultimate proves the action framework can handle multi-hit, multi-target ultimates with stat-based bonuses.

- **Wind ultimate (distributed flurry + temporary effect hit buff)** – `backend/plugins/damage_types/wind.py:86`
  - Category: `ActionType.ULTIMATE`
  - Complexity: high (hits calculated from `wind_ultimate_hits`, effect hit-rate buff, random target selection, DoT reapplication, and cleanup of `ActionManager` registries).
  - Dependencies: `EffectManager`, `create_stat_buff`, `BUS.emit_async`, and the `WindTurnSpread` helper that cooperates with the turn loop (`player_turn.py:735`).
  - Priority: high because Wind ulti is AoE and currently hardcoded in `player_turn`/`wind.py`.
  - Rationale: converting this unlocks respecting `ActionRegistry` pacing/cost logic for special multi-target ultimates.

- **Fire ultimate (AoE + Burn + drain stacks)** – `backend/plugins/damage_types/fire.py:44`
  - Category: `ActionType.ULTIMATE`
  - Complexity: medium (visit each foe, apply damage, seed DoTs, track per-turn drain stacks through `BUS` subscriptions).
  - Dependencies: `EffectManager` for DoT infliction, `autofighter.rooms.battle.pacing` helpers, `BUS` listeners that pollute global state (`_drain_stacks`, `_on_turn_start`).
  - Priority: medium-high because its drain stacks already add persistent hooks that need to survive plugin migration.
  - Rationale: migrating this ensures the registry can control DoT triggering without scattering `BUS.subscribe` calls across battle loop code.

- **Ice ultimate (six-wave ramping AoE)** – `backend/plugins/damage_types/ice.py:19`
  - Category: `ActionType.ULTIMATE`
  - Complexity: medium (targets each foe multiple times with increasing bonus); minimal external state.
  - Dependencies: `select_aggro_target`, `pace_per_target` for pacing.
  - Priority: medium because the wave logic is deterministic and a good way to prove multi-wave ultimates work.
  - Rationale: the plugin can express the ramping bonus and share cooldown/cost handling with other ultimates.

- **Lightning ultimate (AoE + random DoTs + Aftertaste stacks)** – `backend/plugins/damage_types/lightning.py:35`
  - Category: `ActionType.ULTIMATE`
  - Complexity: high (flexible pacing budget, random DoT spawning, and Aftertaste stack tracking via `BUS` subscriptions).
  - Dependencies: `TURN_PACING`, `YIELD_MULTIPLIER`, `DamageOverTime` creation, and the `Aftertaste` effect triggered via `BUS` events.
  - Priority: high due to the tangled asynchronous dependencies; migrating it early avoids replicating its subtleties in multiple places.
  - Rationale: the registry can centralize Aftertaste stack resets and unify multi-target pacing.

- **Generic ultimate (64 rapid hits + passive triggers)** – `backend/plugins/damage_types/generic.py:18`
  - Category: `ActionType.ULTIMATE`
  - Complexity: high (triggers `PassiveRegistry` events, respects `TURN_PACING`, runs 64 hits while emitting `hit_landed` and `action_taken`).
  - Dependencies: `PassiveRegistry`, `BUS`, and `ActionResult` metadata.
  - Priority: high because generic ult is the fallback and needs the most rigorous metadata tracking.
  - Rationale: migrating this ensures the registry can replay each hit while still informing passives.

- **Light `on_action` healing/flurry** – `backend/plugins/damage_types/light.py:21`
  - Category: `ActionType.SPECIAL` (invoked via `DamageTypeBase.on_action`).
  - Complexity: medium (heals allies under 25% HP, adds HoTs, uses pacing per target). 
  - Dependencies: `EffectManager`, `damage_effects.create_hot`, and `pace_per_target`.
  - Priority: high because it is wired into every Light normal action currently hardcoded inside `DamageTypeBase` hooks.
  - Rationale: converting it to a plugin lets the registry manage the heal logic and metadata instead of having it buried in `DamageTypeBase`.

- **Dark `on_action` drain-to-bonus** – `backend/plugins/damage_types/dark.py:18`
  - Category: `ActionType.SPECIAL`.
  - Complexity: medium due to ally drain, bonus scheduling via `BUS.subscribe`, and bonus cleanup.
  - Dependencies: `Stats.apply_cost_damage`, `BUS` for cleanup, and metadata stored on the attacker (`_pending_dark_bonus`).
  - Priority: high because every Dark attack currently doubles as a drain action.
  - Rationale: migrating it to an action plugin decouples the drain logic from the Stats class and lets `ActionRegistry` manage its metadata/costs.

- **Wind normal-action spread (Wind AoE)** – `backend/autofighter/rooms/battle/turn_loop/player_turn.py:760` + `backend/plugins/damage_types/wind.py:81`
  - Category: `ActionType.SPECIAL` with its own spread helper.
  - Complexity: medium-high (computes per-target damage scaling, loops extra foes, triggers hit logs and DoTs, needs pacing).
  - Dependencies: `BattleContext` for `context.foes`, `BUS.emit_async("hit_landed")`, and wind-specific helper `_handle_wind_spread`.
  - Priority: high because the spread helper is still executed inside the player turn loop, limiting portability.
  - Rationale: packaging the spread into a plugin makes the turn loop agnostic to the number of hits and centralizes Wind-specific metadata.

- **Luna sword summon creation** – `backend/plugins/characters/luna.py:303`
  - Category: `ActionType.SPECIAL` (summons are pseudo-attacks that add helpers to the party).
  - Complexity: high (creates `Summon` instances via `SummonManager.create_summon`, registers them with `_LunaSwordCoordinator`, syncs action counts, and registers cleanup hooks).
  - Dependencies: `SummonManager`, `EffectManager`, `weakref`, and `BattleContext` for action counts (via `helper.sync_actions_per_turn`).
  - Priority: high for boss/glitched Luna variants because their swords currently embed combat logic in `prepare_for_battle`.
  - Rationale: migrating Luna's sword spawn into an action plugin keeps summon creation, tagging, and per-turn behavior inside the registry instead of scatter across multiple helpers.

### 2. Card-Based Actions (MEDIUM PRIORITY)
- **Phantom Ally card (permanent phantom summon)** – `backend/plugins/cards/phantom_ally.py:24`
  - Category: `ActionType.ITEM`/special (card effect that spawns a summon).
  - Complexity: high (evaluates viability, manipulates temporary summon slots, uses `SummonManager.create_summon`, emits `card_effect` events, and registers cleanup on `battle_end`).
  - Dependencies: `CardBase.apply` for stat buffs (`plugins/cards/_base.py:54`), `SummonManager`, and `BUS` event bus for tracking summons.
  - Priority: medium because it is a card effect rather than default combat action, but migrating it enables a unified approach for card-activated summons.
  - Rationale: embedding the summon-creation logic in an action plugin allows the registry to enforce costs/delays and emit structured `ActionResult` metadata to the UI.

### 3. Auxiliary Systems / Exclusions
- **Summon manager & rooms**
  - The shop (`backend/autofighter/rooms/shop.py:265`) and chat (`backend/autofighter/rooms/chat.py:1`) resolve UI interactions and should stay outside the action plugin scope.
  - Summoning/liber actions triggered by cards or characters should run through plugins only while the underlying room logic keeps its current responsibilities (stock generation, reroll pricing, LLM chat). 
- **Effect/passive systems**
  - `EffectManager` + `StatEffect` (see `backend/autofighter/effects.py:1`) currently own buff/debuff/DoT application; migrating actions should continue to use these helpers (not replace them with action plugins).
  - Passives such as `Ally Overload` (`backend/plugins/passives/normal/ally_overload.py:15`) and `Becca Menagerie Bond` (`backend/plugins/passives/normal/becca_menagerie_bond.py:1`) manage charge counters, buff timing, and summon cleanup—these should remain passive plugins while relying on action plugins to emit the events they listen to.

## Migration Recommendations
- **Phase 1 – Quick wins (1–2 days each)**: Convert the deterministic on-action behaviors to action plugins: Light healing (`light.py:21`), Dark drain (`dark.py:18`), and Wind spread (`player_turn.py:760`). These make the turn loop look even more like a dispatcher and give the registry a chance to record metadata before tackling larger ultimates.
- **Phase 2 – Ultimates (medium complexity)**: Migrate each damage-type ultimate (`light.py:49`, `dark.py:88`, `wind.py:86`, `fire.py:44`, `ice.py:19`, `lightning.py:35`, `generic.py:18`). This step builds on Phase 1 because the turn loop will already route normal attacks through plugins; now the entire `damage_type.ultimate` call can be replaced with `ActionBase.execute` implementations.
- **Phase 3 – Summons and cards**: Introduce summon-aware actions for Luna's swords (`luna.py:303`) and `Phantom Ally` (`phantom_ally.py:24`). This phase also wires `SummonManager` into `BattleContext` (see `backend/autofighter/rooms/battle/turn_loop/initialization.py:220` and `backend/autofighter/rooms/battle/turn_loop/initialization.py:252`) so actions can spawn/remove entities safely. Once summon actions emit `summon_created`/`summon_removed` events, passives can react through the existing `BUS` hooks.

## Technical Considerations
- **Action infrastructure**: Leverage `ActionBase`/`ActionRegistry` to consolidate cost/cooldown/targeting logic (`backend/plugins/actions/_base.py:22-200` and `registry.py:16-133`). All new action plugins should call `BattleContext.apply_damage`/`apply_healing` so they reuse `Stats.apply_damage`'s mitigation, enrage, and passive hooks instead of replicating logic.
- **Battle context integration**: The turn loop already builds a `BattleContext` via `create_battle_context` (`backend/autofighter/rooms/battle/turn_loop/initialization.py:220`), but `summon_manager` is still `None` there (`backend/autofighter/rooms/battle/turn_loop/initialization.py:252`)—Phase 3 should wire the real `SummonManager` so summon/spawn actions can add/remove entities and honor pacing metadata.
- **Fallback safety**: `player_turn.py:387-418` and `foe_turn.py:240-320` include fallback logic that still calls `Stats.apply_damage` if an action plugin fails. Keep these fallbacks during migration so failures don't abort battles.
- **Effects/passive coordination**: New action plugins must continue to emit `BUS` events (`autofighter.stats:BUS`) because passives such as Ally Overload (`backend/plugins/passives/normal/ally_overload.py:15`) and Becca's Menagerie Bond (`backend/plugins/passives/normal/becca_menagerie_bond.py:1`) listen for `action_taken`, `hit_landed`, etc. Effects such as DoTs/buffs remain the responsibility of `EffectManager`/`StatEffect` (`backend/autofighter/effects.py:1`).
- **Testing strategy**: Extend the action-specific test suites referenced in `.codex/implementation/action-plugin-system.md:257` to cover the new behaviors (ultimates, summon creation, wind spread). Ensure `tests/test_action_turn_loop_integration.py` (as described in the existing doc) continues to pass after each migration phase.
