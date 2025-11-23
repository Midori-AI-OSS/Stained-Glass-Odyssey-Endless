# Migrate Ultimate Actions to Action Plugins

## Task ID
`de34385f-migrate-ultimate-actions-to-plugins`

## Priority
High

## Status
WIP

## Description
Convert character ultimate abilities from hardcoded execution to action plugins. Ultimates are high-impact abilities that charge up during battle and can be triggered at key moments. This migration will make ultimate abilities consistent with the new action plugin system and enable easier creation of new ultimate abilities.

## Context
Currently, ultimate handling is partially implemented in the turn loop with `_handle_ultimate()` but the actual ultimate effects are embedded in character classes or handled through ad-hoc mechanisms. With the action plugin system in place (ActionBase, ActionRegistry, BattleContext), ultimates should become standardized action plugins.

## Current Implementation

### Ultimate System Components
1. **Charge System** (`backend/autofighter/stats.py`):
   - `ultimate_charge` - Current charge amount
   - `ultimate_ready` - Boolean indicating readiness
   - `ultimate_charge_capacity` - Maximum charge needed (default 15)
   - `add_ultimate_charge()` - Method to increment charge

2. **Turn Loop Handling** (`backend/autofighter/rooms/battle/turn_loop/player_turn.py`):
   - `_handle_ultimate()` function processes ultimate activation
   - Currently placeholder or basic implementation

3. **Character Definitions**:
   - Each character may have ultimate ability defined in their class
   - Implementation varies by character

## Objectives
1. Create UltimateActionBase extending ActionBase with ultimate-specific behavior
2. Migrate each character's ultimate to a separate action plugin
3. Integrate ultimate action plugins with turn loop ultimate handling
4. Ensure ultimate charge consumption and cooldown work correctly
5. Maintain existing ultimate charge mechanics

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

### Step 3: Migrate Character Ultimates
For each character with an ultimate:
1. Create `backend/plugins/actions/ultimate/{character_id}_ultimate.py`
2. Define ultimate as action plugin extending UltimateActionBase
3. Implement execute() method with character's unique ultimate effect
4. Add proper targeting rules and animation data

Example structure:
```python
@dataclass(kw_only=True, slots=True)
class LunaUltimate(UltimateActionBase):
    plugin_type = "action"
    id: str = "ultimate.luna"
    name: str = "Lunar Eclipse"
    description: str = "Luna's powerful ultimate attack"
    # ... implementation
```

### Step 4: Update Turn Loop Integration
Modify `backend/autofighter/rooms/battle/turn_loop/player_turn.py`:
- Update `_handle_ultimate()` to use ultimate action plugins
- Look up ultimate action from ActionRegistry
- Execute via action plugin system instead of hardcoded logic

### Step 5: Update Character Classes
Remove or deprecate hardcoded ultimate methods from character classes, keeping only:
- Ultimate charge capacity (can remain as character attribute)
- Ultimate animation preferences (if any)
- Reference to ultimate action plugin ID

## Files to Modify

### New Files
- `backend/plugins/actions/ultimate/__init__.py`
- `backend/plugins/actions/ultimate/_base.py`
- `backend/plugins/actions/ultimate/{character}_ultimate.py` (one per character)

### Modified Files
- `backend/autofighter/rooms/battle/turn_loop/player_turn.py` - Update _handle_ultimate()
- `backend/plugins/actions/registry.py` - May need ultimate-specific registration
- Character plugin files - Remove hardcoded ultimate methods

### Test Files
- `backend/tests/test_ultimate_actions.py` - New test file for ultimate plugins
- Update existing character tests if they test ultimates

## Acceptance Criteria
- [ ] UltimateActionBase class created with charge consumption logic
- [ ] Directory structure created for ultimate action plugins
- [ ] At least 3 character ultimates migrated to action plugins
- [ ] Turn loop integration updated to use ultimate action plugins
- [ ] Ultimate charge and readiness still work correctly
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

## Notes for Coder
- Start with 1-2 simple ultimates before tackling complex ones
- Preserve existing ultimate charge mechanics exactly
- Each ultimate should be in its own file for maintainability
- Consider creating tests that verify charge consumption and cooldown
- Ultimate actions should emit proper events for logging/analytics
- If a character doesn't have a clear ultimate defined yet, skip it for now
