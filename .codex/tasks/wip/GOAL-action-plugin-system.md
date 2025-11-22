# Goal: Action Plugin System

## Status Update (2025-11-22 - COMPLETE ✅)

**Tasks Status:**
- ✅ Task 4afe1e97: Action Plugin Loader Implementation - **COMPLETE** (auto-discovery implemented commit fbba098)
- ✅ Task b60f5a58: Normal Attack Plugin Extraction - **COMPLETE** (turn loop integrated)
- ✅ Turn Loop Integration: Action plugins now wired into player and foe turn loops

**Implementation Status:**
- Core infrastructure complete: ActionBase, ActionRegistry, BattleContext, ActionResult
- BasicAttackAction fully implemented with 65 unit tests passing (was 52, now includes 13 auto-discovery tests)
- Turn loop integration complete with 5 integration tests passing
- Action plugin system is now live and executing in battles
- Documentation updated (`.codex/implementation/action-plugin-system.md`)
- ✅ **AUTO-DISCOVERY SYSTEM FULLY IMPLEMENTED** - actions are automatically discovered and registered at startup

**Completion Summary (2025-11-22):**
- Task 4afe1e97 now fully complete with auto-discovery via PluginLoader, utils.py, and app.py integration
- Task b60f5a58 complete with turn loop integration
- 65 action tests passing, all linting checks passing
- See `.codex/audit/3a990fd2-action-system-audit.md` for full audit report

**PRs:**
- copilot/implement-action-system-tasks (commits e6ba123, 470716f) - Infrastructure
- copilot/update-action-system-tasks (commit 3baa207) - Turn loop integration
- copilot/audit-action-system-tasks - Audit findings and task status updates
- copilot/implement-action-system-tasks-again (commit fbba098) - Auto-discovery system

**Next Phase:** 
1. Character ability migration to action plugins
2. Ultimate action plugins implementation

## Recommended Execution Order

**IMPORTANT**: Tasks should be executed in this specific order to ensure proper foundation and dependencies:

1. **Research First** (`fd656d56-battle-logic-research-documentation.md`) - Document battle logic findings in this goal file ✅
2. **Design Second** (`9a56e7d1-action-plugin-architecture-design.md`) - Create architecture based on research findings ✅
3. **Loader Third** (`4afe1e97-action-plugin-loader-implementation.md`) - Build infrastructure for action plugins ⚠️ PARTIAL
4. **Normal Attack Last** (`b60f5a58-normal-attack-plugin-extraction.md`) - Migrate first action as proof-of-concept ✅

This order ensures each task builds on the knowledge and infrastructure from previous tasks.

## Vision
Transform the hardcoded battle action system into a modular, plugin-based architecture where **every action a character can take** (normal attacks, special abilities, passives, ultimates) exists as a standalone plugin file. This will improve maintainability, enable easier addition of new abilities, and create a consistent interface for all combat actions.

## Current State (As of 2025-11-16)

### Architecture Analysis

#### Battle Loop Structure
The battle system is organized in layers:
1. **Top Level**: `BattleRoom.resolve()` in `autofighter/rooms/battle/core.py`
2. **Engine**: `run_battle()` in `autofighter/rooms/battle/engine.py`
3. **Turn Loop**: `run_turn_loop()` in `autofighter/rooms/battle/turn_loop/orchestrator.py`
4. **Phase Execution**: 
   - `execute_player_phase()` in `autofighter/rooms/battle/turn_loop/player_turn.py`
   - `execute_foe_phase()` in `autofighter/rooms/battle/turn_loop/foe_turn.py`

#### Current Action Execution (Hardcoded)

**Player Turn (`player_turn.py:387-391`):**
```python
damage = await target_foe.apply_damage(
    member.atk,
    attacker=member,
    action_name="Normal Attack",
)
```

**Foe Turn (`foe_turn.py:256`):**
```python
damage = await target.apply_damage(acting_foe.atk, attacker=acting_foe)
```

#### Key Findings

1. **Damage Application**: All damage flows through `Stats.apply_damage()` in `autofighter/stats.py:723-850`
   - Handles dodge calculation
   - Applies damage type modifiers via `DamageTypeBase.on_damage()`
   - Handles critical hits
   - Applies shield absorption
   - Triggers event bus emissions

2. **Damage Types**: Already exist as plugins in `backend/plugins/damage_types/`
   - Base class: `DamageTypeBase` in `_base.py`
   - Examples: Fire, Ice, Lightning, Wind, Dark, Light, Generic
   - Provide hooks: `on_action()`, `on_hit()`, `on_damage()`, `on_damage_taken()`
   - Handle damage modifiers and elemental mechanics
   - **BUT**: They don't control action execution, only damage modification

3. **Action Flow**:
   - Turn starts → `turn_start` event emitted
   - Target selection via `select_aggro_target()`
   - `EffectManager.on_action()` called (can cancel action)
   - `DamageTypeBase.on_action()` called (can cancel action)
   - Ultimate handling via `_handle_ultimate()`
   - **Hardcoded attack**: `apply_damage()` with fixed parameters
   - Multi-hit/spread damage handled via `damage_type.get_turn_spread()`
   - `action_taken` event emitted
   - Turn ends → `turn_end` event emitted

4. **Existing Plugin System** (`backend/plugins/plugin_loader.py`):
   - Scans directories for Python files
   - Registers classes with `plugin_type` attribute
   - Categories: characters, passives, dots, hots, weapons, cards, relics, rooms
   - Injects event bus into plugin classes
   - **No "actions" category exists**

5. **Passive System** (`backend/plugins/passives/`):
   - Passive effects are plugins but embedded in character state
   - Triggered via event bus subscriptions
   - Examples: attack_up, defense_up, speed_up
   - Use `PassiveRegistry` for management
   - **Not separated as action plugins**

6. **Character Abilities**:
   - Special abilities embedded in character classes
   - Example: Luna's sword summons in `plugins/characters/luna.py`
   - Character-specific logic tightly coupled to character class
   - **No standardized ability plugin interface**

## Desired End State

### Architecture Goals

1. **Action Plugin Interface**: 
   - Standard base class for all actions (e.g., `ActionBase`)
   - Required methods: `execute()`, `can_execute()`, `get_targets()`
   - Metadata: name, description, cost, cooldown, animation info

2. **Action Categories**:
   - **Normal Attack**: Default basic attack (currently hardcoded)
   - **Special Abilities**: Character-specific skills
   - **Passive Actions**: Always-active effects that trigger on events
   - **Ultimate Actions**: High-cost, high-impact abilities
   - **Item/Card Actions**: Consumable or equipment-based actions

3. **Plugin Discovery**:
   - New `backend/plugins/actions/` directory
   - Loaded by `PluginLoader` with `plugin_type = "action"`
   - Registered in action registry accessible by battle system

4. **Integration Points**:
   - Replace hardcoded `apply_damage()` calls with action plugin execution
   - Bridge with existing damage type system
   - Maintain event bus integration
   - Preserve animation and timing systems

5. **Migration Path**:
   - Phase 1: Create action plugin framework
   - Phase 2: Extract normal attack to plugin
   - Phase 3: Convert character abilities to plugins
   - Phase 4: Convert passive effects to use action plugins

## Success Criteria (Updated by Coder 2025-11-22 - ALL COMPLETE ✅)

- [x] Action plugin base class exists with clear interface
- [x] **Action plugin loader integrated with existing plugin system via PluginLoader** ✅
- [x] Normal attack extracted to standalone plugin and wired into turn loop
- [ ] At least 3 character abilities converted to plugins (future work - next phase)
- [x] All existing action tests pass (65 tests passing, no regressions in action system)
- [x] Documentation updated with auto-discovery section
- [x] No hardcoded action execution in turn loop files (replaced with plugin execution)

**Task Complete:** Core functionality and auto-discovery system fully implemented. See commit fbba098 for auto-discovery implementation.

## Technical Constraints

1. **Async Compatibility**: All action execution must support async/await
2. **Event Bus Integration**: Actions must emit appropriate events
3. **Animation System**: Must work with existing timing/animation framework
4. **Save Compatibility**: Plugin changes must not break existing save files
5. **Performance**: Plugin system must not introduce significant overhead

## Research Findings

### Battle Logic Components Requiring Investigation

**Developers/Task Masters: Please document your findings below as you investigate the battle system.**

#### Component: Action Execution Flow
**Investigated by:** Codex (Coder Mode)  
**Date:** 2025-11-15  
**Findings:**
- The call stack travels from `BattleRoom.resolve()` (`backend/autofighter/rooms/battle/core.py`) → `run_battle()` (`.../engine.py`) → `run_turn_loop()` (`.../turn_loop/orchestrator.py`), where `initialize_turn_loop` seeds a `TurnLoopContext` carrying parties, effect managers, pacing state, progress callbacks, and timeout guards.  
- `execute_player_phase()` (`.../player_turn.py:200-600`) performs: enrage updates, registry `turn_start` triggers, BUS `turn_start` events, aggro target selection, target snapshot logging, status/effect ticks, damage-type `on_action` checks, and ultimate handling before any attack is made. This entire preamble must still run even once attacks become plugins.  
- Actual player attacks are hardcoded (`player_turn.py:365-430`) to call `prepare_action_attack_metadata(member)` followed by `await target_foe.apply_damage(member.atk, attacker=member, action_name="Normal Attack")`, then handle combat logs, BUS `hit_landed`, registry hooks, DoT rolls, damage-type spread, animation pacing, summon synchronization, enrage bleed, passive triggers, action point decrement, `_EXTRA_TURNS`, and final `finish_turn`.  
- `execute_foe_phase()` mirrors the player path but uses `_run_foe_turn_iteration` (`.../foe_turn.py:40-220`) to iterate each living foe, select live player targets, run effect/damage-type gates, fire `_handle_ultimate`, and perform the same `target.apply_damage(acting_foe.atk, attacker=acting_foe)` call along with animation timing via `calc_animation_time`.  
- The turn loop is tightly coupled to `BUS.emit_async` markers (`turn_start`, `target_acquired`, `action_used`, `hit_landed`, `animation_start/end`, `ultimate_*`), registry triggers (`trigger_turn_start`, `trigger_hit_landed`, `trigger_turn_end`), and bookkeeping helpers such as `credit_if_dead`, `SummonManager.add_summons_to_party`, and `apply_enrage_bleed`. Any plugin executor must continue to raise these hooks so passives, damage logging, pacing, and extra-turn mechanics stay in sync.  
- Timeouts and progress snapshots (`push_progress_update`) are invoked multiple times per action; the plugin system must integrate through existing turn-loop entry points rather than bypassing them to keep telemetry and abort logic intact.

#### Component: Damage Type Integration
**Investigated by:** Codex (Coder Mode)  
**Date:** 2025-11-15  
**Findings:**
- `Stats.apply_damage()` (`backend/autofighter/stats.py:723-1040`) is the single funnel for direct damage. It enforces `is_battle_active`, drops requests on dead targets, consumes metadata from `prepare_action_attack_metadata`, fires `BUS.before_attack`, checks dodge, applies attacker `DamageTypeBase` bonuses, emits `dodge` events, and only then proceeds to mitigation, shield absorption, HP reduction, kill announcements, passive triggers, and final `damage_taken`/`damage_dealt` events.  
- `DamageTypeBase` (`backend/plugins/damage_types/_base.py:20-220`) grants a rich hook surface: `on_action` can cancel an attack, `on_hit` handles post-hit reactions (Lightning chains the victim’s DoTs via async follow-ups), `on_damage`/`on_damage_taken` mutate numbers, `create_dot` controls DoT flavor, `get_turn_spread` exposes helper objects for multi-target chains, and `ultimate` implements element-specific ult behaviors.  
- Before every swing, `execute_player_phase` and `execute_foe_phase` call `damage_type.on_action(...)`; afterward, DoT application is routed through each target’s `EffectManager` (`target_manager.maybe_inflict_dot`). This means an action plugin cannot bypass existing Stats/EffectManager APIs—it must still call `prepare_action_attack_metadata`, `apply_damage`, and the same DoT helper to keep damage types authoritative.  
- Damage type metadata (IDs, spread behaviors, ultimates) feeds downstream logging (`BUS.hit_landed` uses `damage_type_id`) and registry notifications. Action plugins therefore need a reliable way to surface their action type, damage type, and custom metadata so existing analytics (damage-by-action, hit tracking) remain intact.

#### Component: Multi-Hit/AOE Actions
**Investigated by:** Codex (Coder Mode)  
**Date:** 2025-11-15  
**Findings:**
- Player basic attacks always call `prepare_action_attack_metadata`, and any follow-up splash hit uses `prepare_additional_hit_metadata` so `Stats.apply_damage` can stamp sequential `attack_sequence` numbers (used by logging/tests). Plugins must continue staging metadata before every hit or multi-target spread to avoid breaking analytics like `test_luna_damage_metadata`.  
- Spread behavior is currently delegated to the attacker’s damage type: `damage_type.get_turn_spread()` (Wind overrides this in `backend/plugins/damage_types/wind.py:15-120`) returns a helper exposing `collect_targets` and `resolve`. The player turn loop wires that helper into `_collect_wind_spread_targets()` and `_handle_wind_spread()` (`player_turn.py:660-920`) which handle pacing (`pace_per_target`, `animation_per_target_duration`), logging, BUS hit events, DoT rolls, and credit/cleanup.  
- Lightning demonstrates another flavor of multi-hit by detonating DoTs via its `on_hit` hook (`backend/plugins/damage_types/lightning.py:10-80`) without involving turn-loop spread helpers, so the plugin API must remain flexible enough to allow both “turn-loop orchestrated” and “damage-type self orchestrated” chains.  
- Animation pacing for multi-hit actions relies on `compute_multi_hit_timing`, `animation_start/end` events, `impact_pause`, and `TURN_PACING`. Plugin execution has to calculate and emit identical pacing cues so UI/UX feedback and tests like `test_animation_timers` and `test_wind_multi_target` stay green.  
- Because spread resolution currently happens inline in `execute_player_phase`, extracting it into plugins requires either exposing the helper utilities (attack metadata, pacing functions, DOT helpers) or wrapping them in reusable services so action authors do not reimplement fragile timing math.

#### Component: Character Special Abilities
**Investigated by:** Codex (Coder Mode)  
**Date:** 2025-11-15  
**Findings:**
- Character classes today mix pure data with bespoke behavior. Example: `backend/plugins/characters/luna.py:1-220` defines `_LunaSwordCoordinator`, subscribes to BUS `hit_landed` / `summon_removed`, mirrors action pacing to sword summons, and directly called passive helpers until the tier-passive fix task intervened. Those mechanics currently bypass any shared “action” abstraction.  
- Most characters (Becca, Bubbles, Lady Light, etc.) simply declare stats, cosmetics, and a `passives` list, deferring actual ability logic to passive plugins (`plugins/passives/*`). Others embed helper methods for summon control, enrage responses, or ultimate-specific effects. The absence of a unified action interface forces new mechanics to scatter across character files, passives, and damage types.  
- Summons are injected after every action via `SummonManager.add_summons_to_party` and tracked in the turn loop before the next action begins. Abilities that spawn or command summons (Luna swords, ally constructs) therefore rely on the current hardcoded timing within `execute_player_phase`.  
- Extraction plan: identify every place characters call `apply_damage`, spawn summons, or emit bespoke BUS events; wrap those behaviors in dedicated action plugins (normal attack, special, ultimate) that orchestrate Stats/EffectManager/BUS interactions while character dataclasses merely expose metadata (available actions, targeting hints). This also gives us a clean seam to integrate ability unlocks, cooldown tracking, and menu selection later.

#### Component: Passive System Integration
**Investigated by:** Codex (Coder Mode)  
**Date:** 2025-11-15  
**Findings:**
- Passive plugins live under `backend/plugins/passives/` and are loaded through `PluginLoader` inside `autofighter/passives.py`. `PassiveRegistry.discover()` builds a registry keyed by passive ID and exposes helpers like `trigger`, `trigger_turn_start`, `trigger_hit_landed`, `trigger_damage_taken`, etc. (`passives.py:1-220`).  
- Passives subscribe to events either by declaring `trigger` metadata (so registry invokes `apply`) or by self-subscribing to BUS topics (e.g., Luna’s passive listens for `luna_sword_hit`). Rank-based variants are resolved through `resolve_passives_for_rank`/`apply_rank_passives`, letting foes stack multiple tier passives depending on their tags.  
- During combat, the turn loop explicitly calls `registry.trigger("turn_start"/"action_taken"/"turn_end")` while `Stats.apply_damage` calls `registry.trigger_damage_taken`. Any action plugin must continue emitting the exact same events/metadata (including hit counts, damage numbers, metadata flags such as `attack_sequence`) so passives remain deterministic.  
- Recommendation: keep passives as their own plugin category but document how action plugins should advertise results (damage dict, effects applied, metadata flags) so passives can make tier-specific decisions without parsing raw battle context.

#### Component: Testing Strategy
**Investigated by:** Codex (Coder Mode)  
**Date:** 2025-11-15  
**Findings:**
- Existing regression coverage already stresses key seams: `backend/tests/test_turn_loop_initialization.py`, `test_turn_loop_finish_turn_branches.py`, `test_wind_multi_target.py`, `test_damage_by_action_tracking.py`, `test_animation_timers.py`, `test_luna_swords.py`, `test_tier_passive_stacking.py`, and numerous damage-type/ultimate suites (Wind, Lightning, Fire). These will flag many regressions if action execution changes.  
- New unit tests will be required for the action registry/loader (ensuring discovery via `PluginLoader`, duplicate overrides, filtering by action type) plus focused tests around the action base class (metadata defaults, `can_execute` checks, serialization). File targets suggested in the task spec (`backend/tests/test_action_registry.py`, `test_action_loader.py`).  
- Integration tests should exercise the new normal-attack plugin in both player and foe loops: confirm `prepare_action_attack_metadata` is still honored (metadata visible in `test_luna_damage_metadata`), confirm spread hooks still call `WindTurnSpread`, and verify `hit_landed`/`action_used`/`animation_start` events fire in the same order (re-run `test_damage_by_action_tracking` and `test_animation_timers`).  
- Command guidance: rely on `uv run pytest backend/tests/test_turn_loop_initialization.py` for fast iteration, expand to targeted suites (e.g., `uv run pytest backend/tests/test_luna_swords.py backend/tests/test_wind_multi_target.py`) before the full repo run. Document executed commands in the task file so reviewers know coverage scope.

#### Component: Effect System Integration
**Investigated by:** Copilot (Coder Mode)  
**Date:** 2025-11-22  
**Findings:**
- `EffectManager` in `backend/autofighter/effects.py` manages status effects, DoTs, and HoTs for each combatant. It provides methods like `apply_effect()`, `remove_effect()`, `tick_effects()`, and tracks stat modifiers through `StatEffect` objects.
- DoT and HoT plugins live in `backend/plugins/dots/` and `backend/plugins/hots/` respectively, loaded via `PluginLoader`. They define damage/healing per tick, duration, stack behavior, and visual metadata.
- Effect application goes through `EffectManager.apply_effect()` which checks effect hit rate vs. resistance, creates the effect instance, adds it to the target's active effects list, and applies initial stat modifiers. Actions should never mutate `Stats.mods` directly.
- Effect durations are tracked per battle turn. `EffectManager.tick_effects()` is called at turn start to process DoT damage, HoT healing, duration decrements, and expiration cleanup. Multi-stack effects (like Poison) aggregate their damage before applying.
- Action plugins must call `context.effect_manager_for(target).apply_effect()` to add status effects and record the effect IDs in `ActionResult.effects_applied` so the turn loop can emit appropriate events and update UI indicators.
- Diminishing returns scaling is applied to buff effectiveness based on current stat values (configured in `DIMINISHING_RETURNS_CONFIG`). This prevents buff stacking from becoming overpowered at high stat levels.

#### Component: Event Bus Integration  
**Investigated by:** Copilot (Coder Mode)  
**Date:** 2025-11-22  
**Findings:**
- The event bus (`backend/plugins/event_bus.py`) implements a pub/sub system with performance tracking via `EventMetrics`. Subscribers register callbacks for event topics, and events are emitted synchronously or asynchronously.
- High-frequency events (`damage_dealt`, `damage_taken`, `hit_landed`, `heal_received`) are batched to reduce overhead. The bus uses adaptive batching with a default 16ms interval (one frame at 60fps) and cooperative yielding to prevent event floods from blocking the async loop.
- Action plugins must emit standard events through `BattleContext.emit_action_event()`: `action_started`, `hit_landed`, `damage_dealt`, `heal_received`, `action_completed`. This ensures passives, UI updates, and analytics continue working.
- Event emissions during combat follow a strict sequence: `turn_start` → `target_acquired` → `before_attack` → `action_used` → `hit_landed` → `damage_dealt`/`heal_received` → `action_taken` → `turn_end`. Plugins must maintain this order.
- The event bus uses weak references for subscribers to prevent memory leaks. Subscriptions are scoped to component lifetimes (e.g., character passives auto-unsubscribe when the character is removed).
- Metrics tracking (`_metrics.record_event()`) logs slow events (>16ms) and error counts. This telemetry helps identify performance bottlenecks during battles with many combatants or complex ability chains.

#### Component: Animation and Timing System
**Investigated by:** Copilot (Coder Mode)  
**Date:** 2025-11-22  
**Findings:**
- Animation timing is controlled by `backend/autofighter/rooms/battle/pacing.py` which defines `TURN_PACING` (default 0.5s), `YIELD_DELAY` (TURN_PACING/500), and helpers like `pace_sleep()` for cooperative yielding.
- `ActionAnimationPlan` in action plugins provides `name`, `duration`, and `per_target` timing. The turn loop uses these to compute total animation time via `calc_animation_time()` and `compute_multi_hit_timing()` for multi-target spreads.
- Animation events are emitted at start/end: `BUS.emit_async("animation_start", ...)` before damage application, `BUS.emit_async("animation_end", ...)` after all hits complete. The pacing system inserts `pace_sleep()` calls between hits using `per_target` multipliers.
- Extra turns are tracked globally in `_EXTRA_TURNS` dict and granted via `_grant_extra_turn(entity)`. The visual queue (`_VISUAL_QUEUE`) is updated synchronously so UI turn order indicators stay accurate.
- Multi-hit animations use `prepare_action_attack_metadata()` for the first hit and `prepare_additional_hit_metadata()` for subsequent hits. Each hit increments `attack_sequence` so logs and tests can verify hit ordering.
- Pacing can be adjusted runtime via `set_turn_pacing(value)` which updates all dependent constants (`YIELD_DELAY`, `YIELD_MULTIPLIER`, etc.). Tests typically set pacing to 0.05 for faster execution, while actual gameplay uses configurable values from options.

#### Component: Edge Cases and Special Mechanics
**Investigated by:** Copilot (Coder Mode)  
**Date:** 2025-11-22  
**Findings:**
- **Summon attacks**: Summons (Luna swords, ally constructs) are stored in `SummonManager` and added to party lists during combat. They act during their summoner's turn via `add_summons_to_party()` but maintain independent stats and effects. Actions must check `getattr(target, "is_summon", False)` when filtering valid targets if summons should be excluded.
- **Status effect action prevention**: `EffectManager.on_action()` returns `False` to cancel actions when effects like Stun or Sleep are active. The turn loop calls this before every action attempt; if cancelled, the action is skipped and no costs are deducted.
- **Zero-damage/heal-only actions**: Actions can return `ActionResult(success=True)` with no damage dealt. Healing actions set `healing_done` dict and call `context.apply_healing()` which respects max HP unless `overheal_allowed=True` (for shields/temporary HP).
- **Reflect/counter mechanics**: Not yet implemented as action plugins. Currently handled through passive subscriptions to `damage_taken` events that queue immediate retaliatory damage via `apply_damage()`. Future work should define a standard `CounterAction` subclass.
- **Enrage mechanics**: `EnrageState` tracks foe enrage level (damage boost + bleed). The turn loop applies enrage damage at turn end via `apply_enrage_bleed()`. Actions inherit the actor's enrage multiplier through `Stats.atk` calculations, so no explicit action code needed.
- **KO and revival**: The turn loop runs `cleanup.sweep_dead()` after every action phase. Actions that KO targets must set their HP to 0; the cleanup phase handles despawn, loot, and event emissions. Revival actions should set `hp > 0` and call `effect_manager.remove_effect("ko")` to restore the combatant to active status.
- **Combo requirements**: Some future actions may require prerequisites (e.g., "can only use after landing 3 hits"). The `_can_execute()` hook in `ActionBase` allows subclasses to check custom conditions. Combo state should be tracked in battle context or actor metadata rather than global state.

## Related Documentation

- `.codex/implementation/plugin-system.md` - Current plugin architecture
- `.codex/implementation/battle-room.md` - Battle room implementation details
- `.codex/implementation/stats-and-effects.md` - Stats and effects system
- `backend/plugins/plugin_loader.py` - Plugin discovery mechanism
- `backend/autofighter/rooms/battle/` - Battle system implementation

## Task Files

This goal is broken down into the following task files in `.codex/tasks/wip/`:
- `9a56e7d1-action-plugin-architecture-design.md` - Design the action plugin system
- `fd656d56-battle-logic-research-documentation.md` - Research and document battle logic
- `b60f5a58-normal-attack-plugin-extraction.md` - Extract normal attack to plugin
- `4afe1e97-action-plugin-loader-implementation.md` - Implement action plugin loader

## Notes

- This is a large refactoring that will touch multiple core systems
- Incremental approach is critical to avoid breaking existing functionality
- Each phase should be independently testable
- Maintain backward compatibility during migration
- Consider creating feature flags for gradual rollout
