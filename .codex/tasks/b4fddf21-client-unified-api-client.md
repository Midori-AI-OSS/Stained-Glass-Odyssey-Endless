# CLIENT-001: Create Simplified Unified API Client

## Objective
Replace the current complex frontend API layer (multiple files: `api.js`, `uiApi.js`, `backendDiscovery.js`) with a single, simple client that uses the new unified backend endpoints. This will eliminate run ID tracking, multiple API patterns, and complex state synchronization on the frontend.

## Acceptance Criteria
- [ ] New single file `frontend/src/lib/api.js` replaces all existing API files
- [ ] Only 4 main methods: `getState()`, `sendAction()`, `getHealth()`, `subscribe()`
- [ ] No run ID tracking or state management in frontend API layer
- [ ] Automatic error handling with user-friendly notifications
- [ ] Built-in retry logic for network failures
- [ ] Full TypeScript/JSDoc type definitions
- [ ] Performance: API calls complete under 200ms in Docker environment

## Implementation Details

### Simplified API Interface
```javascript
class UnifiedApiClient {
    // Get complete current state
    async getState(): Promise<AppState>
    
    // Send user action
    async sendAction(action: string, params: object): Promise<ActionResult>
    
    // Health check for backend
    async getHealth(): Promise<HealthStatus>
    
    // Subscribe to real-time updates (future task)
    subscribe(callback: (state: AppState) => void): () => void
}
```

### Core Types
```javascript
/**
 * @typedef {Object} AppState
 * @property {string} ui_mode - Current UI mode (menu, playing, battle, etc.)
 * @property {Object} game_state - Complete game state
 * @property {string[]} available_actions - Valid actions for current state
 * @property {Object} live_data - Real-time data (battles, notifications)
 */

/**
 * @typedef {Object} ActionResult  
 * @property {boolean} success - Whether action succeeded
 * @property {Object} result - Action-specific result data
 * @property {Object} state_changes - What changed in game state
 * @property {string[]} next_actions - Available follow-up actions
 * @property {Object[]} errors - Error details if any
 */
```

### Network Layer
- Automatic backend discovery (simplified from current system)
- Built-in CORS handling for Docker Compose environment
- Request/response caching where appropriate
- Automatic retry with exponential backoff
- User-friendly error messages and notifications

### Migration Strategy
1. **Phase 1**: Create new API client alongside existing ones
2. **Phase 2**: Update components to use new client one by one
3. **Phase 3**: Remove old API files and imports

## Testing Requirements

### Unit Tests
- [ ] Test all API methods with mocked responses
- [ ] Test error handling and retry logic
- [ ] Test caching behavior
- [ ] Test type validation and parameter sanitization

### Integration Tests
- [ ] Test with actual backend in Docker environment
- [ ] Test network failure scenarios
- [ ] Test concurrent requests
- [ ] Test state consistency after actions

### E2E Tests
- [ ] Test complete user flows with new API
- [ ] Test error recovery scenarios
- [ ] Performance tests for typical usage patterns

## Dependencies
- **API-001**: Requires unified state service
- **API-002**: Requires unified action dispatcher
- Must work with existing frontend components during migration

## Risk Assessment

### Potential Issues
1. **Breaking existing components**: Changes to API interface
   - *Mitigation*: Maintain backward compatibility wrappers during migration
2. **Performance regression**: New abstraction layer
   - *Mitigation*: Benchmark against existing API, implement caching
3. **Docker networking issues**: Backend discovery in containers
   - *Mitigation*: Test thoroughly in Docker Compose environment

### Rollback Plan
- Keep existing API files until migration is complete
- Feature flag to switch between old and new API clients
- Can revert individual components to old API if needed

## Estimated Effort
**Medium** (3-4 days)
- Core API client implementation: 2 days
- Testing and error handling: 1 day
- Documentation and type definitions: 1 day

## Implementation Details

### File Structure Changes
```
frontend/src/lib/
├── api.js (NEW - unified client)
├── systems/
│   ├── api.js (DEPRECATED)
│   ├── uiApi.js (DEPRECATED)  
│   ├── backendDiscovery.js (DEPRECATED)
│   └── ...
```

### Key Simplifications
1. **No Run ID Management**: Backend tracks active run automatically
2. **No State Polling**: Single `getState()` call gets everything
3. **No Complex Discovery**: Simple environment-based configuration
4. **No Manual Error Handling**: Built into client with consistent UX

### Example Usage
```javascript
import { api } from '$lib/api.js';

// Get current state (replaces getMap, getActiveRuns, etc.)
const state = await api.getState();

// Send action (replaces all POST endpoints)
const result = await api.sendAction('start_run', {
    party: ['player', 'archer', 'mage'],
    damage_type: 'fire'
});

// Health check (simplified)
const health = await api.getHealth();
```

### Backward Compatibility Layer
During migration, provide wrapper functions:
```javascript
// Legacy API compatibility
export const getMap = (runId) => api.getState().then(s => s.game_state);
export const startRun = (party, damageType) => 
    api.sendAction('start_run', { party, damage_type: damageType });
```

## Integration Points
- Works with existing overlay system for error handling
- Integrates with current settings and state management
- Compatible with current component event patterns
- Supports current notification system

## Success Metrics
- Reduction in frontend API-related code by 60%+
- Elimination of run ID tracking throughout frontend
- Consistent error handling across all API interactions
- Improved developer experience with simpler API surface