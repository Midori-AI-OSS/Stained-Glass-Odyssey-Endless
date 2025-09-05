# STATE-002: Remove Run ID Tracking and Complex Synchronization

## Objective
Eliminate all run ID tracking, polling mechanisms, and complex state synchronization from the frontend by leveraging the unified backend state service. This will complete the transition to a backend-managed state model where the frontend is purely reactive.

## Acceptance Criteria
- [ ] Zero run ID variables or tracking anywhere in frontend code
- [ ] Removal of all polling mechanisms and timers for state updates
- [ ] Elimination of manual state synchronization logic
- [ ] No localStorage management of game state (except user preferences)
- [ ] Simplified component lifecycle with automatic state management
- [ ] All state transitions handled by backend, frontend just displays current state
- [ ] Performance improvement from eliminated polling overhead

## Implementation Details

### Current Complex Patterns to Remove

#### Run ID Tracking:
```javascript
// REMOVE: Manual run ID management
let runId = '';
let currentIndex = 0;
let savedRunState = loadRunState();

if (savedRunState?.runId) {
    runId = savedRunState.runId;
    // Complex restoration logic...
}

function saveRunState() {
    localStorage.setItem('runState', JSON.stringify({
        runId: runId,
        currentIndex: currentIndex,
        // ... more manual state
    }));
}
```

#### Polling Mechanisms:
```javascript
// REMOVE: Manual polling and timers
let pollInterval;
let battlePollInterval;

function startPolling() {
    pollInterval = setInterval(async () => {
        try {
            const data = await getMap(runId);
            // Manual state synchronization...
        } catch (e) {
            // Complex error handling...
        }
    }, 1000);
}

function startBattlePoll() {
    battlePollInterval = setInterval(async () => {
        // Battle-specific polling...
    }, 500);
}
```

#### Complex State Synchronization:
```javascript
// REMOVE: Manual state coordination
async function syncWithBackend() {
    if (!saved?.runId) return;
    
    try {
        const data = await getMap(saved.runId);
        if (!data) {
            clearRunState();
            return;
        }
        
        // Complex manual synchronization
        runId = saved.runId;
        selectedParty = data.party || selectedParty;
        mapRooms = data.map.rooms || [];
        currentIndex = data.current_state.current_index || 0;
        currentRoomType = data.current_state.current_room_type || '';
        // ... many more manual assignments
    } catch (e) {
        // Complex error recovery...
    }
}
```

### Simplified Replacement Patterns

#### Automatic State Management:
```javascript
// NEW: Simple reactive state (no manual management)
import { appState } from '$lib/store.js';

// Everything comes from the store automatically
$: currentRun = $appState.game_state?.run;
$: currentRoom = currentRun?.current_state;
$: party = $appState.game_state?.party || [];

// No manual synchronization needed
```

#### Action-Based Updates:
```javascript
// NEW: Actions automatically update state
async function advanceRoom() {
    await actions.advanceRoom();
    // State updates automatically, no manual sync needed
}

async function startNewRun() {
    await actions.startRun(selectedParty, damageType);
    // Backend creates run, state updates automatically
}
```

#### Automatic State Restoration:
```javascript
// NEW: Backend manages active runs automatically
onMount(async () => {
    await store.refreshState();
    // Backend automatically provides current active run
    // No manual restoration logic needed
});
```

## Testing Requirements

### Functionality Tests
- [ ] All user workflows work without run ID tracking
- [ ] State persists correctly across page reloads (via backend)
- [ ] No loss of data during state transitions
- [ ] Error recovery works without complex sync logic

### Performance Tests
- [ ] Measure performance improvement from eliminated polling
- [ ] Test memory usage without polling timers
- [ ] Verify no memory leaks from removed interval/timeout logic
- [ ] Compare network traffic before/after (should be significantly reduced)

### Reliability Tests
- [ ] Test state consistency without manual synchronization
- [ ] Test error handling without complex recovery logic
- [ ] Test rapid user actions without race conditions
- [ ] Test offline/online transitions

## Dependencies
- **STATE-001**: Requires unified frontend store
- **CLIENT-001**: Requires unified API client
- **API-001**: Requires backend state service to manage runs automatically

## Risk Assessment

### Potential Issues
1. **State loss**: Removing localStorage run tracking might lose user progress
   - *Mitigation*: Backend maintains active runs, only remove frontend tracking
2. **Performance concerns**: Backend state service might be slower than local state
   - *Mitigation*: Backend state service optimized for performance, caching implemented
3. **Race conditions**: Multiple rapid actions without local state buffering
   - *Mitigation*: Action queuing and proper loading states in store

### Rollback Plan
- Keep simplified localStorage backup for critical user preferences
- Backend state service provides recovery for active runs
- Can temporarily re-add polling if real-time updates aren't sufficient

## Estimated Effort
**Medium** (3-4 days)
- Remove polling mechanisms: 1 day
- Eliminate run ID tracking: 1 day
- Simplify state synchronization: 1 day
- Testing and validation: 1 day

## Specific Removal Tasks

### File: `frontend/src/routes/+page.svelte`
```javascript
// REMOVE these variables and related logic:
- let runId = '';
- let currentIndex = 0;
- let mapRooms = [];
- let battleActive = false;
- let roomData = null;
- All polling interval variables
- All manual state restoration logic
- All saveRunState/loadRunState functions
```

### File: `frontend/src/lib/systems/runState.js`
```javascript
// REMOVE entire file - replaced by backend state management
- saveRunState()
- loadRunState() 
- clearRunState()
- All localStorage game state management
```

### File: `frontend/src/lib/systems/api.js`
```javascript
// REMOVE polling-related functions:
- pollUIState()
- startUIStatePoll()
- stopUIStatePoll()
- All interval/timeout management
```

### File: `frontend/src/lib/systems/uiApi.js`
```javascript
// REMOVE deprecated backward compatibility functions:
- getMap()
- getActiveRuns()
- All run ID parameter handling
```

## Replacement Implementation

### Simplified Component Pattern:
```svelte
<script>
    import { appState, actions } from '$lib/store.js';
    
    // Reactive state - no manual management
    $: currentRun = $appState.game_state?.run;
    $: uiMode = $appState.ui_mode;
    $: availableActions = $appState.available_actions;
    
    // Simple action handlers - no state tracking
    async function handleAction(actionType, params = {}) {
        await actions[actionType](params);
        // State updates automatically
    }
    
    onMount(() => {
        // Just refresh current state, no complex restoration
        store.refreshState();
    });
</script>

<!-- UI reacts to store state automatically -->
{#if uiMode === 'playing' && currentRun}
    <div>Current Room: {currentRun.current_state.current_index}</div>
    <button on:click={() => handleAction('advanceRoom')}>
        Advance Room
    </button>
{/if}
```

### Simplified State Persistence:
```javascript
// Only persist user preferences, not game state
function saveUserPreferences(preferences) {
    localStorage.setItem('user_preferences', JSON.stringify(preferences));
}

function loadUserPreferences() {
    try {
        return JSON.parse(localStorage.getItem('user_preferences') || '{}');
    } catch {
        return {};
    }
}

// Game state comes from backend automatically
```

## Performance Benefits

### Network Traffic Reduction:
- Eliminate continuous polling (1-2 requests/second → 0 background requests)
- Only make requests when user performs actions
- State updates on-demand rather than speculatively

### Memory Usage Reduction:
- No polling timers or intervals
- No duplicated state storage (frontend + localStorage)
- Simplified component state management

### CPU Usage Reduction:
- No continuous state synchronization logic
- No complex state comparison and merging
- Simplified reactive updates

## Success Metrics
- Zero polling timers in frontend code
- No run ID variables anywhere in frontend
- 80%+ reduction in background network requests
- Simplified component code with better maintainability
- No loss of user functionality or data persistence