# API-002: Implement Unified Action Dispatcher

## Objective
Create a centralized action handling system that processes all user actions through a single endpoint with a consistent request/response format. This will replace the current mix of endpoint-specific handlers with a unified, extensible action system.

## Acceptance Criteria
- [ ] New `ActionDispatcher` class in `backend/services/action_service.py`
- [ ] Single method `dispatch_action(action, params)` handles all user actions
- [ ] Support for all current actions: start_run, advance_room, shop_buy, choose_card, etc.
- [ ] Consistent error handling and response format across all actions
- [ ] Action validation and parameter sanitization
- [ ] Full backward compatibility with existing action handlers
- [ ] Comprehensive test coverage for all supported actions

## Implementation Details

### Action Request Format
```python
{
    "action": str,     # Action type identifier
    "params": dict,    # Action-specific parameters
    "context": dict    # Optional context (user preferences, etc.)
}
```

### Action Response Format
```python
{
    "success": bool,
    "result": dict,      # Action-specific result data
    "state_changes": dict, # What changed in game state
    "next_actions": list,  # Available follow-up actions
    "errors": list       # Error details if success=false
}
```

### Supported Actions
1. **Game Flow**: start_run, advance_room, end_run
2. **Battle**: battle_snapshot, pause_combat, resume_combat
3. **Rooms**: shop_buy, shop_reroll, rest_action
4. **Rewards**: choose_card, choose_relic, acknowledge_loot  
5. **Player**: update_party, edit_player, upgrade_character
6. **Meta**: save_settings, gacha_pull, craft_items

### Architecture
```python
class ActionDispatcher:
    def __init__(self):
        self.handlers = {}  # action_name -> handler_function
        self._register_handlers()
    
    async def dispatch_action(self, action: str, params: dict) -> dict:
        # 1. Validate action and parameters
        # 2. Get current state context
        # 3. Execute action handler
        # 4. Return standardized response
        
    def register_handler(self, action: str, handler: callable):
        # Register new action handlers
        
    async def _execute_with_rollback(self, handler, params):
        # Execute action with automatic rollback on failure
```

### Integration Strategy
- Wrap existing service functions as action handlers
- Maintain existing service APIs for backward compatibility
- Add new unified endpoint that uses the dispatcher

## Testing Requirements

### Unit Tests
- [ ] Test action registration and dispatch mechanism
- [ ] Test parameter validation for each action type
- [ ] Test error handling and rollback functionality
- [ ] Test response format consistency
- [ ] Test unknown action handling

### Integration Tests
- [ ] Test all existing actions through new dispatcher
- [ ] Test action sequences (start_run -> advance_room -> etc.)
- [ ] Test concurrent action execution
- [ ] Test rollback scenarios on action failures

### Backward Compatibility Tests
- [ ] Verify existing endpoints still work
- [ ] Test that existing tests pass with new dispatcher
- [ ] Performance comparison with direct service calls

## Dependencies
- **API-001**: Relies on unified state service for state context
- Requires existing service layer (run_service, room_service, etc.)

## Risk Assessment

### Potential Issues
1. **Performance overhead**: Extra abstraction layer
   - *Mitigation*: Benchmark against direct service calls, optimize hot paths
2. **Action conflicts**: Concurrent actions causing inconsistent state
   - *Mitigation*: Implement action locking and transaction management
3. **Breaking existing functionality**: Changes to service integration
   - *Mitigation*: Maintain strict backward compatibility, comprehensive testing

### Rollback Plan
- Dispatcher is additive, existing endpoints remain functional
- Can disable unified endpoint and fall back to existing APIs
- No database schema changes required

## Estimated Effort
**Medium** (4-6 days)
- Action dispatcher core: 2 days
- Action handler registration: 2 days
- Testing and integration: 2 days

## Implementation Notes

### Phase 1: Core Infrastructure
- Build ActionDispatcher framework
- Implement 3-5 core actions as proof of concept
- Add comprehensive error handling

### Phase 2: Action Migration
- Register all existing actions as handlers
- Add parameter validation for each action
- Test backward compatibility

### Phase 3: Advanced Features
- Add action composition (multi-step actions)
- Implement action rollback mechanism
- Add action logging and metrics

## Example Usage
```python
# In route handler
dispatcher = ActionDispatcher()
result = await dispatcher.dispatch_action("start_run", {
    "party": ["player", "archer", "mage"],
    "damage_type": "fire",
    "pressure": 1
})

# Response
{
    "success": true,
    "result": {"run_id": "abc123", "map": {...}},
    "state_changes": {"current_run": "abc123"},
    "next_actions": ["advance_room", "end_run"],
    "errors": []
}
```