# Goal: Action Plugin System

## Status Update (2025-11-22 - AUDITED)

**Tasks Status:**
- ⚠️ Task 4afe1e97: Action Plugin Loader Implementation - **PARTIALLY COMPLETE** (auto-discovery missing)
- ✅ Task b60f5a58: Normal Attack Plugin Extraction - **COMPLETE** (turn loop integrated)
- ✅ Turn Loop Integration: Action plugins now wired into player and foe turn loops

**Implementation Status:**
- Core infrastructure complete: ActionBase, ActionRegistry, BattleContext, ActionResult
- BasicAttackAction fully implemented with 52 unit tests passing (was 31, now includes all action tests)
- Turn loop integration complete with 5 integration tests passing
- Action plugin system is now live and executing in battles
- Documentation updated (`.codex/implementation/action-plugin-system.md`)
- ⚠️ **AUTO-DISCOVERY SYSTEM NOT IMPLEMENTED** - actions must be manually registered

**Audit Findings (2025-11-22):**
- Task 4afe1e97 requires additional work: auto-discovery via PluginLoader, utils.py, app.py integration
- Task b60f5a58 is complete despite outdated "pending" markers
- 52 action tests passing, 6 turn loop test infrastructure issues (unrelated to action system)
- See `.codex/audit/3a990fd2-action-system-audit.md` for full audit report

**PRs:**
- copilot/implement-action-system-tasks (commits e6ba123, 470716f) - Infrastructure
- copilot/update-action-system-tasks (commit 3baa207) - Turn loop integration
- copilot/audit-action-system-tasks - Audit findings and task status updates

**Next Phase:** 
1. Complete auto-discovery system (task 4afe1e97)
2. Character ability migration and ultimate action plugins

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

## Success Criteria (Updated by Auditor 2025-11-22)

- [x] Action plugin base class exists with clear interface
- [ ] **Action plugin loader integrated with existing plugin system** (manual registration only, NOT via PluginLoader)
- [x] Normal attack extracted to standalone plugin and wired into turn loop
- [ ] At least 3 character abilities converted to plugins (future work)
- [x] All existing action tests pass (52 tests passing, no regressions in action system)
- [x] Documentation updated
- [x] No hardcoded action execution in turn loop files (replaced with plugin execution)

**Partial Completion Note:** Core functionality works but auto-discovery system not implemented. See audit report for details.

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
**Investigated by:** GitHub Copilot (Coder Mode)  
**Date:** 2025-11-22  
**Findings:**
- The effect system consists of three main components: `EffectManager` (`autofighter/effects.py`), `StatEffect` dataclass (`autofighter/stat_effect.py`), and plugin-based DoT/HoT implementations in `backend/plugins/dots/` and `backend/plugins/hots/`.
- `EffectManager` owns all temporary stat modifications and status applications for a single `Stats` object. It provides `apply_effect()` to add new effects, `remove_effect()` to clear them, `tick_effects()` to process duration counters, and `on_action()` to gate actions when stun/freeze is active.
- `StatEffect` is a simple dataclass with `name`, `stat_modifiers` dict, `duration` counter (-1 for permanent, >0 for temporary), and `source` identifier. Effects apply their modifiers directly to `Stats.mods` dict during `apply_effect()` and remove them during cleanup.
- DoT/HoT plugins (`backend/plugins/dots/*.py`, `backend/plugins/hots/*.py`) follow the standard plugin pattern with `plugin_type = "dot"` or `"hot"`. Each defines damage/healing formulas, duration, application conditions, and visual effects. Examples include `bleed.py`, `blazing_torment.py`, `frozen_wound.py` for DoTs and healing equivalents for HoTs.
- The `EffectManager.maybe_inflict_dot()` helper applies DoT effects based on `effect_hit_rate` vs `effect_resistance` rolls. It creates the DoT plugin instance, applies it via `Stats.mods`, and emits BUS events (`dot_applied`, `hot_applied`) for UI/logging.
- Diminishing returns are calculated in `effects.py:calculate_diminishing_returns()` using stat-specific thresholds and scaling factors. This prevents buff stacking from becoming exponentially overpowered. Current thresholds: HP at 500, ATK/DEF/SPD at 100, mitigation/vitality at 0.01, etc.
- **Action Plugin Integration**: Plugins must call `context.effect_manager_for(target).apply_effect()` to add status effects, never mutate `Stats.mods` directly. DoT application should flow through `maybe_inflict_dot()` or equivalent helpers so resistance checks and event emissions remain consistent. Action results must populate `ActionResult.effects_applied` with tuples of `(target, effect_name)` for combat log accuracy.
- **Key Workflow**: Action executes → calls `context.effect_manager_for(target).apply_effect(StatEffect(...))` → EffectManager updates `target.mods` → turn loop calls `effect_manager.tick_effects()` at turn end → expired effects are removed and `effects_removed` events emitted.

#### Component: Event Bus Mapping
**Investigated by:** GitHub Copilot (Coder Mode)  
**Date:** 2025-11-22  
**Findings:**
- The event bus (`backend/plugins/event_bus.py`) provides both synchronous (`BUS.send()`) and asynchronous (`BUS.emit_async()`, `BUS.emit_batched_async()`) event emission with performance monitoring, error isolation, and cooperative yielding to prevent frame drops.
- Core battle events currently emitted by turn loop and Stats include:
  - **Turn lifecycle**: `turn_start`, `turn_end`, `action_used`, `target_acquired`, `extra_turn`
  - **Damage/healing**: `before_attack`, `hit_landed`, `damage_dealt`, `damage_taken`, `dodge`, `heal_received`, `overkill`
  - **Status effects**: `dot_applied`, `hot_applied`, `effect_expired`, `stun`, `freeze`
  - **Summons**: `summon_created`, `entity_defeat`, `luna_sword_hit` (character-specific)
  - **Animation markers**: `animation_start`, `animation_end`
  - **Battle flow**: `battle_start`, `battle_end`, `ultimate_start`, `ultimate_end`
- High-frequency events (`damage_dealt`, `damage_taken`, `hit_landed`, `heal_received`) are automatically batched when emission rate exceeds the pacing threshold (`_SOFT_YIELD_THRESHOLD = 0.004s`). Batched emissions collect events for one frame (~16ms at 60fps) before notifying subscribers, reducing overhead in multi-hit attacks.
- Event subscribers use `BUS.accept(event_name, obj, callback)` to register handlers and `BUS.ignore(event_name, obj)` to unregister. The bus uses weak references for object subscribers to prevent memory leaks when entities despawn.
- Cooperative yielding is enforced via `_cooperative_pause()` which yields control after `_HARD_YIELD_THRESHOLD` (20ms) or when cumulative time since last yield exceeds the soft threshold. This prevents turn loop stalls during heavy event processing (e.g., Luna sword chains triggering 20+ passives).
- Event metrics are tracked via `EventMetrics` class: counts per event, timing distributions, slow event detection (>16ms), and error counts. Stats can be retrieved via `BUS._metrics.get_stats()` for performance debugging.
- **Action Plugin Integration**: Plugins must emit at minimum `action_used`, `hit_landed`, and `damage_dealt`/`heal_received` events so existing passive subscribers, combat logs, and UI overlays continue to function. Use `context.emit_action_event()` wrapper which handles async semantics and batching automatically. For multi-target actions, emit one `hit_landed` per target with the same `attack_sequence` metadata so analytics can correlate spread damage correctly.

#### Component: Animation and Timing System
**Investigated by:** GitHub Copilot (Coder Mode)  
**Date:** 2025-11-22  
**Findings:**
- Battle pacing is controlled by `backend/autofighter/rooms/battle/pacing.py` which defines global timing constants: `TURN_PACING` (default 0.5s), `YIELD_DELAY` (TURN_PACING/500), and derived multipliers for cooperative yielding.
- `TURN_PACING` can be dynamically adjusted via options table (`OptionKey.TURN_PACING`) and applied using `set_turn_pacing(value)` which recalculates dependent constants. Minimum pacing is `_MIN_TURN_PACING = 0.05s` to prevent zero-delay battles that starve the event loop.
- Animation durations are calculated by `calc_animation_time(entity)` which reads `entity.animation_duration` or falls back to `DEFAULT_ANIMATION_PER_TARGET = 0.2s`. Multi-hit animations use `compute_multi_hit_timing()` (referenced but not fully shown in pacing.py) to stagger impact pauses across targets.
- The `_EXTRA_TURNS` dictionary tracks per-entity extra turn counters granted by skills/passives. `_grant_extra_turn(entity)` increments the counter and notifies the visual queue (`_VISUAL_QUEUE: ActionQueue`) for UI updates. Turn loop checks this dict before advancing to the next combatant.
- Visual queue integration: The `_VISUAL_QUEUE` object (optional, set from turn loop) receives `grant_extra_turn()` and `clear_extra_turns_for()` notifications to animate action bar shifts. When an entity despawns, `clear_extra_turns_for()` removes its pacing entries to prevent stale references.
- Turn loop timing flow: `pace_sleep(duration)` wraps `asyncio.sleep(TURN_PACING * duration)` and is called after every significant action (target selection, damage application, effect ticks) to maintain consistent battle rhythm. `_pace(entity, action_type)` (not shown in snippet) handles variable timing based on entity speed and action complexity.
- **Animation Events**: The turn loop emits `animation_start`/`animation_end` BUS events with `actor`, `action_name`, and `duration` metadata so frontend can trigger visual effects. Events are fired before and after `pace_sleep()` calls to bookend each action's animation window.
- **Action Plugin Integration**: Plugins populate `ActionResult.animations` with `AnimationTrigger` dicts containing `name`, `duration`, and optional `per_target` overrides. Turn loop consumes this list after action execution to schedule `animation_start`/`end` events and compute pacing delays via `pace_sleep(sum(anim.duration for anim in result.animations))`. For multi-target actions, the `per_target` field specifies individual timing (e.g., Wind spread uses 0.1s per extra target).

#### Component: Edge Cases and Special Mechanics
**Investigated by:** GitHub Copilot (Coder Mode)  
**Date:** 2025-11-22  
**Findings:**
- **Summon attacks**: Summons (e.g., Luna swords) are tracked in `Stats` objects within the party list. They attack using the same turn loop flow as regular characters but rely on custom passives (e.g., `_LunaSwordCoordinator` in `luna.py`) to synchronize behavior with the summoner. Action plugins must support summons as valid `actor` entities.
- **Reflect/Counter mechanics**: Currently implemented via passive triggers on `damage_taken` events. Passives like `counter_attack` or `reflect_damage` subscribe to `damage_taken`, calculate retaliation damage, and call `attacker.apply_damage()` directly. This bypasses the action system entirely. Future work should migrate reflects/counters to instantiate action plugins (e.g., `special.counter_strike`) for consistency.
- **Status prevention**: Stun, freeze, and other disabling effects are gated in `EffectManager.on_action()` which returns `False` when a disabling effect is active. Turn loop checks this before allowing an entity to act. Action plugins must respect `context.effect_manager_for(actor).on_action()` as a precondition in `can_execute()`.
- **Zero-damage actions**: Heal-only actions, buffs, and debuffs may deal no damage. `ActionResult.damage_dealt` should remain empty while `healing_done` and `effects_applied` are populated. Turn loop must not assume every action emits `damage_dealt` events; check `result.success` and result contents before triggering downstream logic.
- **Overkill handling**: When target HP drops below 0, `Stats.apply_damage()` emits `overkill` event with excess damage amount. This triggers credit assignment (`credit_if_dead()` in turn loop) and potentially passives that react to killing blows. Action plugins using `context.apply_damage()` automatically get overkill tracking; custom damage paths must emit the event manually.
- **Multi-phase actions**: Some abilities (e.g., Luna ultimate) execute multiple attacks in sequence with retargeting. Current implementation hardcodes the multi-attack loop within character methods or damage type hooks (Wind spread). Action plugins should support retargeting by calling `self.get_valid_targets()` mid-execution and validating new targets before each hit.
- **Cost-free actions**: Passives and reactive abilities have zero action point cost but still flow through the action system. `ActionCostBreakdown` defaults to `action_points=1`; zero-cost actions must explicitly set `action_points=0`. Turn loop must not decrement actor's action points when cost is zero.
- **Ultimate gating**: The turn loop currently checks `stats.ultimate_ready` flag before allowing ultimate execution. This flag is set when `ultimate_charge >= 100`. Action plugins with `action_type=ActionType.ULTIMATE` must integrate with this system: `ActionCostBreakdown.resources["ultimate_charge"]` should be set to 100, and `can_execute()` should verify the `ultimate_ready` flag.
- **Save compatibility**: Action IDs (e.g., `"normal.basic_attack"`) must remain stable across versions since they may be serialized in save files (character loadouts, cooldown state). Renaming an action ID requires migration logic to remap old IDs to new ones during save load.

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
