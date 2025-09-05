# CLIENT-002: Replace Legacy API Calls in Components

## Objective
Systematically migrate all frontend components from the current complex API patterns (direct service calls, run ID tracking, manual state management) to the new unified API client and state store. This will eliminate the majority of frontend complexity and complete the client-side simplification.

## Acceptance Criteria
- [ ] All components use unified API client instead of legacy api.js/uiApi.js
- [ ] Zero manual run ID tracking in any component
- [ ] All state access through unified store, not local component state
- [ ] Consistent error handling across all components using unified patterns
- [ ] No direct service calls or complex API logic in components
- [ ] All existing functionality preserved with simplified implementation
- [ ] Comprehensive testing of migrated components

## Implementation Details

### Migration Scope
**Files to Update:**
- `frontend/src/routes/+page.svelte` (main game component)
- `frontend/src/lib/components/` (all game UI components)
- `frontend/src/lib/systems/OverlayController.js` (overlay system)
- Any other files with direct API imports

**Legacy Patterns to Replace:**
```javascript
// OLD: Complex API imports and run tracking
import { getMap, startRun, advanceRoom } from '$lib/systems/api.js';
import { getUIState, sendAction } from '$lib/systems/uiApi.js';

let runId = '';
let currentIndex = 0;
let mapRooms = [];

async function handleStart() {
    const result = await startRun(selectedParty, damageType);
    runId = result.run_id;
    const mapData = await getMap(runId);
    currentIndex = mapData.current_state.current_index;
    mapRooms = mapData.map.rooms;
}

// NEW: Simple store-based pattern
import { appState, actions } from '$lib/store.js';

$: currentRun = $appState.game_state?.run;
$: mapRooms = currentRun?.map?.rooms || [];

async function handleStart() {
    await actions.startRun(selectedParty, damageType);
    // State updates automatically
}
```

### Component Migration Pattern

#### Before (Complex):
```svelte
<script>
    import { getMap, advanceRoom, getPlayers } from '$lib/systems/api.js';
    import { getUIState } from '$lib/systems/uiApi.js';
    
    let runId = '';
    let currentIndex = 0;
    let roomData = null;
    let players = [];
    let loading = false;
    
    onMount(async () => {
        players = await getPlayers();
        // Try to restore state
        if (saved?.runId) {
            try {
                const data = await getMap(saved.runId);
                runId = saved.runId;
                currentIndex = data.current_state.current_index;
                roomData = data.current_state.room_data;
            } catch (e) {
                // Handle error, clear saved state
            }
        }
    });
    
    async function handleAdvance() {
        loading = true;
        try {
            await advanceRoom(runId);
            const data = await getMap(runId);
            currentIndex = data.current_state.current_index;
            roomData = data.current_state.room_data;
        } catch (e) {
            // Handle error
        } finally {
            loading = false;
        }
    }
</script>

{#if loading}
    <div>Loading...</div>
{:else}
    <div>Room {currentIndex}: {roomData?.type}</div>
    <button on:click={handleAdvance}>Advance</button>
{/if}
```

#### After (Simple):
```svelte
<script>
    import { appState, actions } from '$lib/store.js';
    
    $: currentRun = $appState.game_state?.run;
    $: currentRoom = currentRun?.current_state;
    $: players = $appState.game_state?.player_data?.characters || [];
    $: isLoading = $appState.ui_mode === 'loading';
    
    async function handleAdvance() {
        await actions.advanceRoom();
        // State and UI update automatically
    }
</script>

{#if isLoading}
    <div>Loading...</div>
{:else if currentRoom}
    <div>Room {currentRoom.current_index}: {currentRoom.room_data?.type}</div>
    <button on:click={handleAdvance}>Advance</button>
{/if}
```

### Overlay System Integration
```javascript
// Update OverlayController.js to use unified store
import { appState } from '$lib/store.js';

export function openOverlay(type, data) {
    // Use store state instead of passed parameters
    const state = get(appState);
    
    switch (type) {
        case 'battle':
            data = { 
                ...data, 
                battleState: state.live_data.battle_snapshot,
                party: state.game_state.party
            };
            break;
        case 'inventory':
            data = {
                ...data,
                inventory: state.game_state.inventory,
                characters: state.game_state.player_data.characters
            };
            break;
    }
    
    // ... rest of overlay logic
}
```

## Testing Requirements

### Component Tests
- [ ] Test each migrated component in isolation
- [ ] Test state reactivity (store changes update UI)
- [ ] Test action handling (user interactions trigger correct store actions)
- [ ] Test error states and loading states
- [ ] Test component cleanup (no memory leaks)

### Integration Tests
- [ ] Test component interactions through store
- [ ] Test complex user flows (start run -> play -> battle -> rewards)
- [ ] Test navigation between different UI modes
- [ ] Test overlay system with unified store

### Regression Tests
- [ ] All existing E2E tests pass with migrated components
- [ ] No functionality lost during migration
- [ ] Performance comparison (before/after migration)
- [ ] Visual regression testing for UI consistency

## Dependencies
- **CLIENT-001**: Requires unified API client
- **STATE-001**: Requires unified frontend store
- **API-003**: Benefits from backward compatibility (for gradual migration)

## Risk Assessment

### Potential Issues
1. **Breaking user workflows**: Changes to component behavior
   - *Mitigation*: Thorough testing of all user paths, maintain exact functionality
2. **Performance regression**: Store reactivity causing excessive updates
   - *Mitigation*: Use derived stores, optimize reactive statements
3. **State synchronization bugs**: Components not updating when they should
   - *Mitigation*: Comprehensive reactive testing, clear state subscription patterns

### Rollback Plan
- Migrate components one at a time with feature flags
- Keep legacy API imports available during migration
- Can revert individual components if issues arise
- Git history allows full rollback if needed

## Estimated Effort
**Large** (6-8 days)
- Main route component migration: 2 days
- Individual component migration: 3 days
- Overlay system integration: 1 day
- Testing and debugging: 2 days

## Migration Strategy

### Phase 1: Main Route Component (`+page.svelte`)
- This is the largest and most complex component
- Contains most of the run management logic
- Migration will establish patterns for other components

### Phase 2: Battle and Game Components
- Components that handle active gameplay
- Complex state interactions and real-time updates
- Critical for user experience

### Phase 3: Menu and Settings Components
- Simpler components with less state complexity
- Good candidates for validating migration patterns
- Lower risk if issues arise

### Phase 4: Overlay Components
- Update overlay system to use unified store
- Migrate individual overlay components
- Test modal interactions and state passing

## Component-Specific Migration Notes

### Main Game Component (`+page.svelte`)
- **Complexity**: High - 1000+ lines with complex state management
- **Key Changes**: Remove all runId tracking, simplify state synchronization
- **Testing Priority**: Highest - core user experience

### Battle Components
- **Complexity**: Medium - real-time state updates
- **Key Changes**: Use live_data from store instead of direct API polling
- **Testing Priority**: High - critical gameplay functionality

### Menu Components
- **Complexity**: Low - mostly static with simple actions
- **Key Changes**: Use actions instead of direct API calls
- **Testing Priority**: Medium - important but straightforward

## Success Metrics
- 80%+ reduction in component code complexity
- Zero manual state synchronization in components
- All components use reactive store patterns
- Consistent error handling across all components
- Maintained or improved performance
- No loss of existing functionality

## Code Review Checklist
- [ ] No direct API imports in components
- [ ] No manual run ID or state tracking
- [ ] All state access through reactive store subscriptions
- [ ] All actions go through unified action system
- [ ] Consistent error handling patterns
- [ ] No memory leaks or subscription issues
- [ ] Clear and readable reactive statements