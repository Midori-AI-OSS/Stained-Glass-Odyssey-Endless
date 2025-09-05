# CLEANUP-001: Remove Legacy API Endpoints and Code

## Objective
Systematically remove all legacy API endpoints, deprecated code, and complex communication patterns once the unified system is fully operational and tested. This will complete the simplification by eliminating technical debt and reducing maintenance burden.

## Acceptance Criteria
- [ ] All legacy API endpoints removed from backend routes
- [ ] Legacy frontend API files and imports completely eliminated
- [ ] Complex state synchronization logic removed
- [ ] Polling mechanisms and timers deleted
- [ ] Run ID tracking code eliminated
- [ ] Backward compatibility layer removed (after migration complete)
- [ ] Comprehensive testing to ensure no functionality lost
- [ ] Documentation updated to reflect simplified architecture

## Implementation Details

### Backend Cleanup Scope

#### Routes to Remove:
```python
# Files to delete or significantly simplify:
- backend/routes/ui.py (most endpoints, keep only unified ones)
- backend/routes/rewards.py (merge into unified action system)
- backend/routes/players.py (merge into unified state/action system)
- backend/routes/gacha.py (merge into unified system)

# Specific endpoints to remove:
- GET /map/{run_id}
- POST /run/{run_id}/next
- POST /rooms/{run_id}/shop
- POST /rooms/{run_id}/rest
- POST /rooms/{run_id}/battle
- GET /battles/{index}/summary
- GET /battles/{index}/events
- All run-specific endpoints
```

#### Legacy Service Patterns:
```python
# Remove from services:
- Complex run ID parameter passing
- Manual state synchronization logic
- Multiple response format variants
- Direct database access patterns that bypass unified service
- Redundant state loading functions
```

### Frontend Cleanup Scope

#### Files to Delete:
```javascript
// Complete file removal:
- frontend/src/lib/systems/api.js
- frontend/src/lib/systems/uiApi.js
- frontend/src/lib/systems/backendDiscovery.js
- frontend/src/lib/systems/runState.js
- frontend/src/lib/systems/viewportState.js (if not needed)

// Partial cleanup in remaining files:
- Remove legacy imports throughout components
- Remove manual state management code
- Remove polling and timer logic
- Remove run ID tracking variables
```

#### Component Simplification:
```svelte
<!-- REMOVE from all components: -->
<script>
  // Legacy API imports
  import { getMap, startRun, advanceRoom } from '$lib/systems/api.js';
  import { getUIState, sendAction } from '$lib/systems/uiApi.js';
  
  // Manual state tracking
  let runId = '';
  let currentIndex = 0;
  let mapRooms = [];
  let battleActive = false;
  
  // Complex state restoration
  async function syncWithBackend() { /* ... */ }
  
  // Polling logic
  let pollInterval;
  function startPolling() { /* ... */ }
  
  // Manual state management
  function saveRunState() { /* ... */ }
  function loadRunState() { /* ... */ }
</script>
```

### Cleanup Strategy by Phase

#### Phase 1: Backend Route Cleanup
```python
# Remove legacy routes systematically
# backend/app.py
app.register_blueprint(assets_bp)
app.register_blueprint(catalog_bp)
app.register_blueprint(config_bp)
app.register_blueprint(ui_bp)  # Simplified unified routes only
app.register_blueprint(performance_bp, url_prefix='/api/performance')
# REMOVED: gacha_bp, players_bp, rewards_bp (merged into unified system)

# Keep only essential endpoints:
# GET /api/state
# POST /api/action  
# GET /api/health
# WebSocket/SSE endpoints
```

#### Phase 2: Frontend File Cleanup
```bash
# Delete legacy API files
rm frontend/src/lib/systems/api.js
rm frontend/src/lib/systems/uiApi.js
rm frontend/src/lib/systems/backendDiscovery.js
rm frontend/src/lib/systems/runState.js

# Update imports throughout codebase
# Replace all legacy imports with unified store/api
```

#### Phase 3: Component Logic Cleanup
```svelte
<!-- Simplified component pattern -->
<script>
  import { appState, actions } from '$lib/store.js';
  
  // Only reactive state subscriptions
  $: currentRun = $appState.game_state?.run;
  $: uiMode = $appState.ui_mode;
  
  // Only simple action handlers
  async function handleAction(actionType, params = {}) {
    await actions[actionType](params);
  }
</script>
```

#### Phase 4: Remove Backward Compatibility
```python
# Remove compatibility layer once migration complete
# backend/compatibility/legacy_router.py - DELETE
# backend/routes/ui.py - Remove legacy endpoint mapping
# Remove feature flags for unified backend
```

## Testing Requirements

### Functionality Verification
- [ ] All existing E2E tests pass with cleaned up code
- [ ] No loss of user functionality after cleanup
- [ ] All user workflows continue to work
- [ ] Performance maintained or improved

### Code Quality Tests
- [ ] No dead code or unused imports remain
- [ ] No circular dependencies introduced
- [ ] All TypeScript/JSDoc types are correct
- [ ] Linting passes with no warnings

### Integration Tests
- [ ] Docker Compose deployment works with cleaned code
- [ ] Real-time features work without legacy code
- [ ] Error handling works with simplified architecture

## Dependencies
- **All previous tasks**: Cleanup can only happen after unified system is complete and stable
- **CLIENT-002**: Frontend components must be migrated before cleanup
- **API-003**: Backward compatibility can be removed after migration

## Risk Assessment

### Potential Issues
1. **Breaking existing functionality**: Removing code that's still needed
   - *Mitigation*: Comprehensive testing, gradual cleanup, feature flags
2. **Missing edge cases**: Legacy code might handle cases unified system doesn't
   - *Mitigation*: Thorough analysis of legacy code before removal
3. **Performance regression**: Legacy code might have optimizations
   - *Mitigation*: Performance testing throughout cleanup process

### Rollback Plan
- Use git to revert specific cleanup changes if issues arise
- Feature flags can temporarily re-enable legacy endpoints
- Keep backup branches of pre-cleanup code
- Gradual cleanup allows reverting individual pieces

## Estimated Effort
**Medium** (4-5 days)
- Backend route and service cleanup: 2 days
- Frontend file and component cleanup: 2 days
- Testing and validation: 1 day

## Detailed Cleanup Checklist

### Backend Cleanup:
- [ ] Remove `/map/{run_id}` endpoint and related functions
- [ ] Remove `/run/{run_id}/next` endpoint and logic
- [ ] Remove room-specific endpoints (shop, rest, battle)
- [ ] Remove battle summary/events endpoints
- [ ] Merge player endpoints into unified state/action system
- [ ] Merge gacha endpoints into unified action system
- [ ] Remove reward endpoints (merged into action system)
- [ ] Clean up service layer duplicate functions
- [ ] Remove unused imports and dependencies
- [ ] Update route registration in app.py

### Frontend Cleanup:
- [ ] Delete `api.js` file and all imports
- [ ] Delete `uiApi.js` file and all imports
- [ ] Delete `backendDiscovery.js` file and all imports
- [ ] Delete `runState.js` file and all imports
- [ ] Remove all run ID variables from components
- [ ] Remove all polling logic and timers
- [ ] Remove manual state synchronization functions
- [ ] Remove complex error handling (replaced by unified system)
- [ ] Update all component imports to use unified store
- [ ] Remove localStorage game state management

### Documentation Cleanup:
- [ ] Update API documentation to reflect unified endpoints
- [ ] Remove references to legacy endpoints
- [ ] Update component documentation
- [ ] Update Docker Compose documentation
- [ ] Update development setup documentation

## Code Analysis Before Cleanup

### Legacy Code Audit:
```bash
# Find all legacy API usage
grep -r "getMap\|startRun\|advanceRoom" frontend/src/
grep -r "/map/\|/run/\|/rooms/" backend/
grep -r "runId\|currentIndex" frontend/src/

# Find all polling logic
grep -r "setInterval\|setTimeout" frontend/src/
grep -r "pollInterval\|Poll" frontend/src/

# Find manual state management
grep -r "localStorage\|saveRunState\|loadRunState" frontend/src/
```

### Function Migration Map:
```javascript
// Legacy → Unified mapping
getMap(runId) → store.getState().game_state
startRun(party, type) → actions.startRun(party, type)
advanceRoom(runId) → actions.advanceRoom()
getPlayers() → store.getState().game_state.player_data
getBattleSnapshot(runId) → store.getState().live_data.battle_snapshot
```

## Success Metrics
- 60%+ reduction in total codebase size
- Elimination of all duplicate API patterns
- Zero legacy imports or dead code
- Improved maintainability and code clarity
- No loss of existing functionality
- Improved performance from simplified architecture

## Post-Cleanup Validation

### Architecture Verification:
- [ ] Only 4 main API endpoints exist (state, action, health, realtime)
- [ ] Single frontend API client handles all communication
- [ ] Single state store manages all frontend state
- [ ] No manual state synchronization anywhere
- [ ] No run ID tracking in frontend code
- [ ] No polling mechanisms (except fallback)

### Code Quality Metrics:
- [ ] Cyclomatic complexity reduced
- [ ] Code duplication eliminated
- [ ] Import dependency graph simplified
- [ ] Test coverage maintained or improved
- [ ] Documentation accuracy improved