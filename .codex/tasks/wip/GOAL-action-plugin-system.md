# Goal: Action Plugin System

## Recommended Execution Order

**IMPORTANT**: Tasks should be executed in this specific order to ensure proper foundation and dependencies:

1. **Research First** (`fd656d56-battle-logic-research-documentation.md`) - Document battle logic findings in this goal file
2. **Design Second** (`9a56e7d1-action-plugin-architecture-design.md`) - Create architecture based on research findings
3. **Loader Third** (`4afe1e97-action-plugin-loader-implementation.md`) - Build infrastructure for action plugins
4. **Normal Attack Last** (`b60f5a58-normal-attack-plugin-extraction.md`) - Migrate first action as proof-of-concept

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

## Success Criteria

- [ ] Action plugin base class exists with clear interface
- [ ] Action plugin loader integrated with existing plugin system
- [ ] Normal attack extracted to standalone plugin
- [ ] At least 3 character abilities converted to plugins
- [ ] All existing tests pass
- [ ] Documentation updated
- [ ] No hardcoded action execution in turn loop files

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
**Investigated by:** [Your Name]  
**Date:** [YYYY-MM-DD]  
**Findings:**
- [Document your discoveries about how actions are currently executed]
- [Note any dependencies or integration points]
- [Identify potential refactoring challenges]

#### Component: Damage Type Integration
**Investigated by:** [Your Name]  
**Date:** [YYYY-MM-DD]  
**Findings:**
- [How do damage types currently interact with actions?]
- [What hooks are available?]
- [How should action plugins integrate with damage types?]

#### Component: Multi-Hit/AOE Actions
**Investigated by:** [Your Name]  
**Date:** [YYYY-MM-DD]  
**Findings:**
- [How are multi-target actions currently handled?]
- [How does spread damage work?]
- [What changes needed for action plugins?]

#### Component: Character Special Abilities
**Investigated by:** [Your Name]  
**Date:** [YYYY-MM-DD]  
**Findings:**
- [Survey of existing character abilities]
- [Common patterns identified]
- [Extraction strategy]

#### Component: Passive System Integration
**Investigated by:** [Your Name]  
**Date:** [YYYY-MM-DD]  
**Findings:**
- [How do current passives work?]
- [Should passives be action plugins or separate?]
- [Event subscription strategy]

#### Component: Testing Strategy
**Investigated by:** [Your Name]  
**Date:** [YYYY-MM-DD]  
**Findings:**
- [What tests exist for combat system?]
- [What new tests needed for action plugins?]
- [How to ensure backward compatibility?]

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
