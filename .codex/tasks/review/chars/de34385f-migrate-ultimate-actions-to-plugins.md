# Migrate Ultimate Actions to Action Plugins

## Task ID
`de34385f-migrate-ultimate-actions-to-plugins`

## Priority
High

## Status
REVIEW

## Description
Convert damage-type-based ultimate abilities from the current `damage_type.ultimate()` methods to action plugins. Ultimate abilities are currently implemented in damage type files (`backend/plugins/damage_types/*.py`), where each damage type defines its own `ultimate()` method. This migration will make ultimate abilities consistent with the new action plugin system while preserving the damage-type-specific implementations.

## Context
Currently, ultimate handling is split across two systems:
1. **Charge System** in `backend/autofighter/stats.py`: Tracks `ultimate_charge`, `ultimate_ready`, and capacity
2. **Ultimate Implementation** in damage type files: Each damage type has its own `ultimate()` method

Examples:
- **Light** (`light.py`): Heals allies to full, cleanses DoTs, debuffs enemies
- **Dark** (`dark.py`): Drains allies for DoT-scaled 6x strikes
- **Wind** (`wind.py`): AoE multi-hit attack distributed across all enemies
- **Fire** (`fire.py`): AoE with burn DoT application
- **Ice** (`ice.py`): 6 waves of ramping AoE (30% damage increase per target)
- **Lightning** (`lightning.py`): AoE with 10 random DoTs and Aftertaste stack buildup
- **Generic** (`generic.py`): 64 rapid strikes on single target (neutral element)

The turn loop calls `damage_type.ultimate(actor, allies, enemies)` when ultimate is ready.

## Current Implementation

### Ultimate System Components
1. **Charge System** (`backend/autofighter/stats.py`):
   - `ultimate_charge` - Current charge amount
   - `ultimate_ready` - Boolean indicating readiness
   - `ultimate_charge_capacity` - Maximum charge needed (default 15)
   - `add_ultimate_charge()` - Method to increment charge

2. **Ultimate Implementations** (in damage type files):
   - `backend/plugins/damage_types/_base.py` - Base `ultimate()` and `consume_ultimate()` methods
   - `backend/plugins/damage_types/light.py` - Light ultimate: Heal + cleanse DoTs + debuff enemies
   - `backend/plugins/damage_types/dark.py` - Dark ultimate: 6x strikes scaled by ally DoT stacks
   - `backend/plugins/damage_types/wind.py` - Wind ultimate: Multi-hit AoE distributed damage
   - `backend/plugins/damage_types/fire.py` - Fire ultimate: AoE with burn DoT infliction
   - `backend/plugins/damage_types/ice.py` - Ice ultimate: 6 waves of ramping AoE damage (30% increase per target)
   - `backend/plugins/damage_types/lightning.py` - Lightning ultimate: AoE with 10 random DoTs + Aftertaste stacks
   - `backend/plugins/damage_types/generic.py` - Generic ultimate: 64 rapid strikes on single target

3. **Turn Loop Handling** (`backend/autofighter/rooms/battle/turn_loop/player_turn.py`):
   - `_handle_ultimate()` function calls `damage_type.ultimate(actor, allies, enemies)`
   - Checks `ultimate_ready` flag before executing

4. **Damage Type Base**:
   - `async def ultimate(actor, allies, enemies)` - Override per damage type
   - `async def consume_ultimate(actor)` - Calls `actor.use_ultimate()` to consume charge

## Objectives
1. Create UltimateActionBase extending ActionBase with ultimate-specific behavior
2. Migrate each damage type's ultimate to a separate action plugin
3. Maintain damage-type-specific ultimate logic (Light heals, Dark drains, Wind AoE, etc.)
4. Integrate ultimate action plugins with turn loop ultimate handling
5. Ensure ultimate charge consumption and cooldown work correctly
6. Preserve existing ultimate charge mechanics
7. Keep damage type association (characters get ultimates based on their damage type)

## Implementation Steps

### Step 1: Create UltimateActionBase
Create `backend/plugins/actions/ultimate/_base.py`:
```python
from dataclasses import dataclass
from plugins.actions._base import ActionBase, ActionType

@dataclass(kw_only=True, slots=True)
class UltimateActionBase(ActionBase):
    """Base class for ultimate actions."""
    
    action_type: ActionType = ActionType.ULTIMATE
    ultimate_cost: int = 15  # Charge required to use
    
    async def can_execute(self, actor, targets, context):
        """Check if ultimate is charged and ready."""
        if not getattr(actor, 'ultimate_ready', False):
            return False
        return await super().can_execute(actor, targets, context)
    
    async def run(self, actor, targets, context):
        """Execute ultimate and consume charge."""
        result = await super().run(actor, targets, context)
        if result.success:
            actor.ultimate_charge = 0
            actor.ultimate_ready = False
        return result
```

### Step 2: Create Directory Structure
```bash
mkdir -p backend/plugins/actions/ultimate
touch backend/plugins/actions/ultimate/__init__.py
```

### Step 3: Migrate Damage Type Ultimates
For each damage type with an ultimate:

1. Create `backend/plugins/actions/ultimate/{damage_type}_ultimate.py`
2. Copy the logic from `damage_type.ultimate()` method
3. Implement as action plugin extending UltimateActionBase
4. Preserve all behavior (healing, DoTs, multi-hit, etc.)

Example: Light Ultimate (`backend/plugins/actions/ultimate/light_ultimate.py`):
```python
@dataclass(kw_only=True, slots=True)
class LightUltimate(UltimateActionBase):
    plugin_type = "action"
    id: str = "ultimate.light"
    name: str = "Radiant Salvation"
    description: str = "Heals allies to full, cleanses DoTs, debuffs enemies"
    damage_type_id: str = "Light"  # Which damage type this ultimate belongs to
    
    async def execute(self, actor, targets, context):
        # Implementation from light.py ultimate() method
        result = ActionResult(success=True)
        
        # Heal allies to full
        for ally in context.allies_of(actor):
            if ally.hp <= 0:
                continue
            missing = ally.max_hp - ally.hp
            if missing > 0:
                healing = await context.apply_healing(ally, missing, healer=actor)
                result.healing_done[ally.id] = healing
        
        # Debuff enemies
        for enemy in context.enemies_of(actor):
            if enemy.hp <= 0:
                continue
            # Apply defense down debuff...
            result.effects_applied.append(...)
        
        return result
```

Priority order:
- Light (heal/cleanse/debuff - supportive)
- Dark (drain/multi-strike - complex with DoT scaling)
- Wind (AoE multi-hit - distributed damage)
- Fire (AoE with DoT - straightforward)
- Ice (ramping AoE - 6 waves with 30% escalation)
- Lightning (AoE + random DoTs + Aftertaste - most complex)
- Generic (64 rapid strikes - high hit count, single target)

### Step 4: Update Turn Loop Integration
Modify `backend/autofighter/rooms/battle/turn_loop/player_turn.py`:
- Update `_handle_ultimate()` to:
  1. Get actor's damage type
  2. Look up ultimate action from ActionRegistry by damage type
  3. Execute via action plugin system instead of calling `damage_type.ultimate()`
- Map damage types to ultimate action IDs (e.g., "Light" → "ultimate.light")

### Step 5: Update Damage Type Classes
For each damage type file:
- Keep the `ultimate()` method for backward compatibility initially
- Add deprecation comment
- Eventually remove once action plugins are proven stable
- OR keep as fallback if action plugin not found

## Files to Modify

### New Files
- `backend/plugins/actions/ultimate/__init__.py`
- `backend/plugins/actions/ultimate/_base.py`
- `backend/plugins/actions/ultimate/light_ultimate.py`
- `backend/plugins/actions/ultimate/dark_ultimate.py`
- `backend/plugins/actions/ultimate/wind_ultimate.py`
- `backend/plugins/actions/ultimate/fire_ultimate.py`
- `backend/plugins/actions/ultimate/ice_ultimate.py`
- `backend/plugins/actions/ultimate/lightning_ultimate.py`
- `backend/plugins/actions/ultimate/generic_ultimate.py`

### Modified Files
- `backend/autofighter/rooms/battle/turn_loop/player_turn.py` - Update _handle_ultimate()
- `backend/plugins/actions/registry.py` - May need ultimate-specific registration
- `backend/plugins/damage_types/*.py` - Add deprecation notes to ultimate() methods

### Test Files
- `backend/tests/test_ultimate_actions.py` - New test file for ultimate plugins
- Update existing character tests if they test ultimates

## Acceptance Criteria
- [ ] UltimateActionBase class created with charge consumption logic
- [ ] Directory structure created for ultimate action plugins
- [ ] All 7 damage type ultimates migrated to action plugins (Light, Dark, Wind, Fire, Ice, Lightning, Generic)
- [ ] Turn loop integration updated to use ultimate action plugins
- [ ] Ultimate charge and readiness still work correctly
- [ ] Damage type association preserved (characters get ultimates based on damage type)
- [ ] Tests created for ultimate action plugins
- [ ] All existing tests still pass
- [ ] Linting passes (run `uv tool run ruff check backend --fix`)
- [ ] Documentation updated in `.codex/implementation/action-plugin-system.md`

## Testing Requirements

### Unit Tests
- Test UltimateActionBase can_execute() checks ultimate_ready
- Test ultimate charge consumption after execution
- Test each ultimate action plugin's execute() method
- Test ultimate action integration with ActionRegistry

### Integration Tests
- Test ultimate activation in battle context
- Test ultimate unavailable when charge < capacity
- Test ultimate ready flag set when charge reaches capacity
- Test turn loop properly executes ultimate actions

## Dependencies
- Existing action plugin system (ActionBase, ActionRegistry, BattleContext)
- Task `6c57b775-action-plugin-migration-analysis` (should identify which ultimates exist)

## References
- `.codex/implementation/action-plugin-system.md` - Action system documentation
- `backend/plugins/actions/_base.py` - Base action class
- `backend/autofighter/stats.py` - Ultimate charge system (lines 184-720)
- `backend/autofighter/rooms/battle/turn_loop/player_turn.py` - Current ultimate handling
- `backend/plugins/damage_types/_base.py` - Base damage type with ultimate() method
- `backend/plugins/damage_types/light.py` - Light ultimate implementation
- `backend/plugins/damage_types/dark.py` - Dark ultimate implementation
- `backend/plugins/damage_types/wind.py` - Wind ultimate implementation
- `backend/plugins/damage_types/fire.py` - Fire ultimate implementation

## Notes for Coder
- Start with 1-2 simple ultimates (Light, Fire) before tackling complex ones (Dark, Wind)
- Preserve existing ultimate charge mechanics exactly
- Each ultimate should be in its own file for maintainability
- Ultimates are damage-type-based, not character-based
- Characters inherit ultimates from their assigned damage type
- Consider creating tests that verify charge consumption and cooldown
- Ultimate actions should emit proper events for logging/analytics
- Keep the damage type mapping clear (damage_type.id → ultimate action ID)
- May want to create a registry method like `get_ultimate_for_damage_type(damage_type_id)`
