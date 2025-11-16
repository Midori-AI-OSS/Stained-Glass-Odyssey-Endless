# Task: Normal Attack Plugin Extraction

**Status:** WIP  
**Priority:** High  
**Category:** Implementation  
**Goal File:** `.codex/tasks/wip/GOAL-action-plugin-system.md`

## Objective

Extract the hardcoded "Normal Attack" action from the battle turn loop and implement it as the first action plugin, serving as a reference implementation and proof-of-concept for the action plugin system.

## Background

Currently, normal attacks are hardcoded in two places:
1. **Player Turn**: `backend/autofighter/rooms/battle/turn_loop/player_turn.py:387-391`
2. **Foe Turn**: `backend/autofighter/rooms/battle/turn_loop/foe_turn.py:256`

Both directly call `apply_damage()` with the attacker's ATK stat. This task involves creating a reusable action plugin that can be used by both players and foes.

## Prerequisites

This task depends on:
- [ ] `9a56e7d1-action-plugin-architecture-design.md` - Action plugin architecture must be designed
- [ ] Action plugin base classes implemented (`ActionBase`, `ActionRegistry`, etc.)
- [ ] Integration points identified and documented

## Requirements

### 1. Create Normal Attack Plugin

**File:** `backend/plugins/actions/normal/basic_attack.py`

Implement a `NormalAttack` action plugin that:
- Extends `ActionBase`
- Implements the standard basic attack behavior
- Works for both player characters and foes
- Maintains all current functionality (damage, events, animations)
- Integrates with damage types
- Supports multi-hit mechanics (via damage type spread)

**Basic structure:**
```python
from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.actions._base import ActionBase
from plugins.actions.result import ActionResult
from plugins.actions.context import BattleContext

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class NormalAttack(ActionBase):
    """Standard basic attack action."""
    
    plugin_type = "action"
    id: str = "normal_attack"
    name: str = "Normal Attack"
    description: str = "A basic attack dealing damage based on ATK stat"
    action_type: str = "normal_attack"
    target_type: str = "single"
    max_targets: int = 1
    cost: int = 0
    
    async def can_execute(
        self, 
        actor: Stats, 
        targets: list[Stats], 
        context: BattleContext
    ) -> bool:
        """Normal attack can always be executed if actor is alive."""
        return getattr(actor, "hp", 0) > 0 and len(targets) > 0
    
    async def execute(
        self,
        actor: Stats,
        targets: list[Stats],
        context: BattleContext
    ) -> ActionResult:
        """Execute the normal attack."""
        # Implementation details here
        pass
    
    def get_valid_targets(
        self,
        actor: Stats,
        allies: list[Stats],
        enemies: list[Stats]
    ) -> list[Stats]:
        """Return all alive enemies."""
        return [e for e in enemies if getattr(e, "hp", 0) > 0]
```

### 2. Implement Action Execution Logic

The `execute()` method should:

1. **Validate target**:
   - Ensure target is alive
   - Check that target is valid for this action

2. **Prepare attack metadata**:
   - Call `prepare_action_attack_metadata(actor)` (from turn loop helpers)
   - Track attack sequence numbers

3. **Apply damage**:
   - Get actor's ATK stat
   - Call `target.apply_damage(actor.atk, attacker=actor, action_name="Normal Attack")`
   - Handle dodge (damage = 0)

4. **Emit events**:
   - `BUS.emit_async("action_used", actor, target, damage)`
   - `BUS.emit_async("hit_landed", ...)` if damage > 0
   - Animation events if needed

5. **Handle multi-hit/spread**:
   - Check if actor's damage type has `get_turn_spread()`
   - Process additional targets if spread exists
   - Track total targets hit

6. **Apply secondary effects**:
   - DoT application via `target_effect.maybe_inflict_dot()`
   - Trigger passive effects
   - Grant ultimate charge

7. **Create result**:
   - Populate `ActionResult` with all outcomes
   - Include damage dealt, targets hit, effects applied

### 3. Integration with Turn Loop

Modify turn loop files to use the action plugin:

**In `player_turn.py`:**
```python
# Replace lines 387-391
# Old:
# damage = await target_foe.apply_damage(
#     member.atk,
#     attacker=member,
#     action_name="Normal Attack",
# )

# New:
from plugins.actions.registry import get_action_registry

action_registry = get_action_registry()
normal_attack = action_registry.get_action("normal_attack")
action_context = BattleContext(
    turn=context.turn,
    actor=member,
    allies=context.combat_party.members,
    enemies=context.foes,
    registry=context.registry,
    # ... other context fields
)
result = await normal_attack.execute(member, [target_foe], action_context)
damage = result.damage_dealt.get(target_foe, 0)
```

**In `foe_turn.py`:**
Similar changes around line 256

### 4. Preserve Backward Compatibility

Ensure that:
- All existing events are still emitted in the same order
- Animation timing remains the same
- Damage calculation is identical
- DoT application works correctly
- Passive triggers still fire
- Ultimate charge is granted properly

### 5. Add Tests

**File:** `backend/tests/test_actions_normal_attack.py`

Create comprehensive tests:

```python
import pytest
from plugins.actions.normal.basic_attack import NormalAttack
from plugins.actions.context import BattleContext
# ... other imports


def test_normal_attack_basic_damage():
    """Test that normal attack deals expected damage."""
    # Setup actor and target
    # Execute action
    # Assert damage is correct
    pass


def test_normal_attack_crit():
    """Test critical hit mechanics."""
    pass


def test_normal_attack_dodge():
    """Test dodge mechanics."""
    pass


def test_normal_attack_events_emitted():
    """Test that all expected events are emitted."""
    pass


def test_normal_attack_with_damage_type():
    """Test interaction with damage types."""
    pass


def test_normal_attack_multi_target():
    """Test spread damage mechanics."""
    pass


@pytest.mark.asyncio
async def test_normal_attack_integration():
    """Integration test with real battle context."""
    pass
```

### 6. Update Documentation

Update the following files:
- `.codex/implementation/action-plugin-system.md` - Add normal attack example
- `.codex/implementation/battle-room.md` - Note the change in action execution
- `backend/plugins/actions/README.md` - Create if doesn't exist, explain action plugins

## Implementation Steps

1. **Create base infrastructure** (if not done by architecture task):
   - [ ] `backend/plugins/actions/_base.py`
   - [ ] `backend/plugins/actions/result.py`
   - [ ] `backend/plugins/actions/context.py`
   - [ ] `backend/plugins/actions/registry.py`

2. **Implement normal attack plugin**:
   - [ ] Create `backend/plugins/actions/normal/basic_attack.py`
   - [ ] Implement all required methods
   - [ ] Add docstrings and type hints

3. **Extract helper functions**:
   - [ ] Review what helpers are needed from turn loop
   - [ ] Create shared utilities in `backend/plugins/actions/utils.py`

4. **Modify turn loops**:
   - [ ] Update `player_turn.py` to use action plugin
   - [ ] Update `foe_turn.py` to use action plugin
   - [ ] Ensure feature parity

5. **Add tests**:
   - [ ] Write unit tests for normal attack plugin
   - [ ] Write integration tests
   - [ ] Verify all existing battle tests still pass

6. **Validate**:
   - [ ] Run full test suite
   - [ ] Run manual battle tests
   - [ ] Check animation playback
   - [ ] Verify damage numbers match previous behavior

7. **Document**:
   - [ ] Update implementation docs
   - [ ] Add code comments
   - [ ] Create usage examples

## Testing Strategy

### Unit Tests
- Test action plugin in isolation
- Mock battle context
- Verify correct values in ActionResult

### Integration Tests
- Test with real Stats objects
- Test with different damage types
- Test multi-hit scenarios
- Test with various passives active

### Regression Tests
- Run all existing battle tests
- Manually verify battles work correctly
- Check that save/load still works
- Verify network battle updates are correct

### Performance Tests
- Ensure no performance regression
- Measure action execution time
- Compare to hardcoded version

## Acceptance Criteria

- [ ] `NormalAttack` plugin implemented and functional
- [ ] Turn loops updated to use action plugin
- [ ] All events emitted correctly
- [ ] Animation system works
- [ ] Damage calculations match previous behavior exactly
- [ ] All existing tests pass
- [ ] New tests added and passing (minimum 8 tests)
- [ ] Code passes linting (`uvx ruff check`)
- [ ] Documentation updated
- [ ] Manual testing completed successfully

## Rollback Plan

If issues arise:
1. Revert turn loop changes
2. Keep action plugin code for future use
3. Document what went wrong in goal file
4. Revise architecture if needed

## Dependencies

- Action plugin architecture design completed
- Base classes implemented
- Registry system working

## Estimated Effort

- Implementation: 8-12 hours
- Testing: 4-6 hours
- Integration: 3-4 hours
- Documentation: 2-3 hours
- **Total: ~17-25 hours**

## Notes

- This is the critical first migration - take time to get it right
- The patterns established here will be used for all future action plugins
- Document any challenges encountered for future migrations
- Consider adding feature flag to switch between old/new implementation during testing
- Make sure to preserve combat logs exactly as they were
