# API-001: Create Unified State Aggregation Service

## Objective
Create a centralized backend service that aggregates all game state (run data, player data, UI state, battle state) into a single, consistent response format. This service will be the foundation for simplifying frontend/backend communication.

## Acceptance Criteria
- [ ] New `StateService` class in `backend/services/state_service.py`
- [ ] Single method `get_complete_state()` that returns unified state object
- [ ] State includes: ui_mode, game_state, available_actions, live_data
- [ ] Performance: Complete state retrieval under 100ms
- [ ] Handles cases where no active run exists (menu mode)
- [ ] Comprehensive error handling with fallback states
- [ ] Full test coverage (unit and integration tests)

## Implementation Details

### State Structure
```python
{
    "ui_mode": str,  # "menu", "playing", "battle", "card_selection", etc.
    "game_state": {
        "run": {...},           # Current run data or null
        "party": [...],         # Current party members
        "player_data": {...},   # Player profile, owned characters
        "inventory": {...},     # Items, relics, cards
        "meta": {...}          # Settings, progress tracking
    },
    "available_actions": [...], # Valid actions for current state
    "live_data": {
        "battle_snapshot": {...}, # Real-time battle data
        "notifications": [...],   # Pending notifications
        "health": {...}          # Backend health metrics
    }
}
```

### Key Components
1. **State Aggregator**: Combines data from existing services
2. **UI Mode Detector**: Determines current UI state based on game state
3. **Action Validator**: Lists valid actions for current state
4. **Caching Layer**: Optimize repeated state requests

### Integration Points
- Reuse existing services: `run_service`, `player_service`, etc.
- Extend current `determine_ui_mode()` from `routes/ui.py`
- Integrate with battle snapshots and live data

## Testing Requirements

### Unit Tests
- [ ] Test state aggregation with various game states
- [ ] Test UI mode detection for all scenarios
- [ ] Test action validation logic
- [ ] Test error handling and fallback states
- [ ] Test performance with large datasets

### Integration Tests  
- [ ] Test with active runs and battles
- [ ] Test menu state with no active runs
- [ ] Test during state transitions (room advancement, etc.)
- [ ] Test concurrent access and caching

### Performance Tests
- [ ] Benchmark state retrieval time
- [ ] Test with multiple concurrent requests
- [ ] Memory usage analysis

## Dependencies
- None (foundational task)
- Builds on existing service architecture

## Risk Assessment

### Potential Issues
1. **Performance**: Aggregating all state might be slow
   - *Mitigation*: Implement caching and lazy loading
2. **Data consistency**: State changes during aggregation
   - *Mitigation*: Use database transactions and locking
3. **Breaking existing services**: Modifying shared services
   - *Mitigation*: Create new service, don't modify existing ones

### Rollback Plan
- Service is additive only, can be disabled without affecting existing APIs
- No changes to existing database schema or services

## Estimated Effort
**Medium** (3-5 days)
- New service implementation: 2 days
- Testing and optimization: 2 days  
- Documentation and review: 1 day

## Notes
This task is the foundation for all other API simplification tasks. The unified state service will be used by both the new unified API endpoints and can be incrementally adopted by existing endpoints.