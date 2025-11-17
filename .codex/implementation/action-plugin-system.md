# Action Plugin System Implementation

## Overview

The action plugin system provides a modular, plugin-based architecture for all combat actions in the Midori AI AutoFighter battle system. This document describes the implemented components and how to use them.

## Architecture

### Core Components

#### 1. ActionBase (`plugins/actions/_base.py`)

Abstract base class for all action plugins. Defines the standard interface and policy enforcement.

**Key Features:**
- Metadata: `id`, `name`, `description`, `action_type`, `tags`
- Targeting rules: `TargetingRules` dataclass for scope, side, target count
- Cost breakdown: `ActionCostBreakdown` for resource deductions
- Cooldown management: `cooldown_turns` for turn-based restrictions
- Animation plan: `ActionAnimationPlan` for pacing integration

**Required Methods:**
- `execute()`: Abstract method that implements the action effect
- `can_execute()`: Validates prerequisites (cooldowns, costs, targeting)
- `run()`: Wrapper that enforces policies and deducts costs
- `get_valid_targets()`: Returns eligible targets based on targeting rules

#### 2. ActionResult (`plugins/actions/result.py`)

Structured return value from action execution containing:
- `success`: Boolean indicating if action succeeded
- `damage_dealt`: Dict mapping target IDs to damage amounts
- `healing_done`: Dict mapping target IDs to healing amounts
- `effects_applied/removed`: Lists of status effect changes
- `messages`: Combat log entries
- `animations`: Animation triggers for the UI
- `metadata`: Action-specific data for analytics

#### 3. BattleContext (`plugins/actions/context.py`)

Runtime context provided to actions during execution:
- Current turn state (`turn`, `phase`, `actor`)
- Party composition (`allies`, `enemies`)
- System references (`action_registry`, `passive_registry`, `event_bus`)
- Helper methods:
  - `apply_damage()`: Damage through the standard pipeline
  - `apply_healing()`: Healing with overheal support
  - `spend_resource()`: Resource deduction
  - `emit_action_event()`: Event bus integration
  - `allies_of()/enemies_of()`: Team lookup
  - `effect_manager_for()`: Effect manager access

#### 4. ActionRegistry (`plugins/actions/registry.py`)

Central registry for action plugin management:
- **Registration**: `register_action(action_class)` for plugin discovery
- **Instantiation**: `instantiate(action_id)` creates action instances
- **Lookup**: `get_actions_by_type()`, `get_character_actions()`
- **Cooldowns**: `is_available()`, `start_cooldown()`, `advance_cooldowns()`
- **Per-actor state**: Cooldown tracking, character loadouts

## Implemented Actions

### BasicAttackAction (`plugins/actions/normal/basic_attack.py`)

The standard normal attack available to all combatants.

**Specifications:**
- ID: `normal.basic_attack`
- Type: `ActionType.NORMAL`
- Cost: 1 action point
- Cooldown: None
- Tags: `("normal_attack",)`

**Behavior:**
1. Prepares attack metadata for tracking
2. Applies damage based on actor's ATK stat
3. Emits events: `hit_landed`, `action_used`
4. Triggers passive effects via registry
5. Applies DoT effects if applicable
6. Supports multi-hit/spread through damage types (partial)

## Usage Examples

### Creating a Custom Action Plugin

```python
from dataclasses import dataclass
from plugins.actions import ActionBase, ActionType, ActionResult

@dataclass(kw_only=True, slots=True)
class FireballAction(ActionBase):
    plugin_type = "action"
    id: str = "special.fireball"
    name: str = "Fireball"
    description: str = "Hurl a ball of flame at your enemy"
    action_type: ActionType = ActionType.SPECIAL
    cooldown_turns: int = 3
    
    async def execute(self, actor, targets, context):
        result = ActionResult(success=True)
        
        target = targets[0]
        damage = await context.apply_damage(
            actor,
            target,
            float(getattr(actor, "atk", 0)) * 1.5,  # 50% more damage
            metadata={"action_name": self.name}
        )
        
        target_id = str(getattr(target, "id", id(target)))
        result.damage_dealt[target_id] = damage
        result.messages.append(f"{actor.id} casts Fireball on {target.id}!")
        
        return result
```

### Using an Action in Battle

```python
from plugins.actions.registry import ActionRegistry
from plugins.actions.context import BattleContext

# Get the registry and instantiate an action
registry = ActionRegistry()
registry.register_action(BasicAttackAction)
action = registry.instantiate("normal.basic_attack")

# Create battle context
context = BattleContext(
    turn=1,
    run_id="battle_001",
    phase="player",
    actor=player,
    allies=[player],
    enemies=[enemy],
    action_registry=registry,
    passive_registry=passive_registry,
    effect_managers={},
)

# Execute the action
if await action.can_execute(player, [enemy], context):
    result = await action.run(player, [enemy], context)
    print(f"Damage dealt: {result.damage_dealt}")
```

### Registering Character-Specific Actions

```python
registry = ActionRegistry()
registry.register_action(BasicAttackAction)
registry.register_action(FireballAction)
registry.register_action(HealingTouchAction)

# Assign actions to a character
registry.register_character_actions(
    "luna",
    ["normal.basic_attack", "special.fireball"]
)

# Get character's available actions
luna_actions = registry.get_character_actions("luna")
```

## Testing

Comprehensive test coverage includes:

### BattleContext Tests (`tests/test_action_context.py`)
- Damage application with and without metadata
- Healing with overheal support
- Resource spending (action points, ultimate charge)
- Team lookup (allies/enemies)
- Effect manager caching

### BasicAttackAction Tests (`tests/test_action_basic_attack.py`)
- Metadata validation
- Execution prerequisites (can_execute checks)
- Damage dealing and HP reduction
- Cost deduction (action points)
- Metadata tracking
- Target filtering

### ActionRegistry Tests (`tests/test_action_registry.py`)
- Action registration and validation
- Duplicate detection
- Instantiation and lookup
- Cooldown tracking and advancement
- Shared cooldown tags
- Character action assignments

**Test Coverage: 31 tests, 100% passing**

## Integration Status

### Completed
- ✅ Action plugin base classes and interfaces
- ✅ BattleContext helper methods
- ✅ BasicAttackAction implementation
- ✅ ActionRegistry with cooldown management
- ✅ Comprehensive test suite

### Pending
- ⏳ Turn loop integration (wiring into execute_player_phase/execute_foe_phase)
- ⏳ Action registry initialization in app startup
- ⏳ Full multi-hit/spread support
- ⏳ Migration of character-specific abilities
- ⏳ Ultimate actions
- ⏳ Passive action plugins

## Design Decisions

### String IDs vs Object References

ActionResult uses string IDs (not Stats objects) for dictionary keys because:
1. Stats objects are not hashable
2. Serialization to JSON/database requires string keys
3. Simpler to work with in UI and logging

### Dataclass vs Regular Class

Actions use `@dataclass` because:
1. Automatic `__init__`, `__repr__`, `__eq__`
2. Default values for optional fields
3. Slots for memory efficiency
4. Type hints enforced

### Registry Instantiation

Registry instantiates actions on registration to read dataclass field values:
- Class-level access returns descriptors, not values
- Instance creation validates all required fields
- Ensures plugins are well-formed before battle starts

## Known Limitations

1. **Spread Mechanics**: Full spread/multi-target support requires turn loop integration to access target selection helpers
2. **Animation Timing**: Animation data is collected but not yet consumed by pacing system
3. **Event Bus**: Events are emitted but some subscribers may not be fully wired up yet
4. **Summon Integration**: Summon spawning actions need access to SummonManager

## Future Work

See task files in `.codex/tasks/wip/`:
- `GOAL-action-plugin-system.md`: Overall goal and migration strategy
- `9a56e7d1-action-plugin-architecture-design.md`: Architecture design (complete)
- `4afe1e97-action-plugin-loader-implementation.md`: Plugin loader integration
- `b60f5a58-normal-attack-plugin-extraction.md`: Turn loop integration

## References

- Task Goal: `.codex/tasks/wip/GOAL-action-plugin-system.md`
- Battle Logic Research: Research findings in goal file
- Plugin System: `backend/plugins/plugin_loader.py`
- Stats & Damage: `backend/autofighter/stats.py`
- Turn Loop: `backend/autofighter/rooms/battle/turn_loop/`
