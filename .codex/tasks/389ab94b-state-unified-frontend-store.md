# STATE-001: Implement Single Frontend State Store

## Objective
Replace the complex frontend state management scattered across multiple files and components with a single, reactive state store that mirrors the backend's unified state. This will eliminate manual state synchronization, reduce bugs, and simplify component logic.

## Acceptance Criteria
- [ ] New `frontend/src/lib/store.js` with single reactive state store
- [ ] Automatic state updates when backend actions complete
- [ ] Elimination of manual state tracking in components (runId, currentIndex, etc.)
- [ ] Reactive UI updates when state changes
- [ ] State persistence in localStorage for offline resilience
- [ ] Full TypeScript/JSDoc type definitions
- [ ] Zero state management logic in route components

## Implementation Details

### Store Architecture
```javascript
import { writable, derived } from 'svelte/store';

// Single source of truth for all app state
export const appState = writable({
    ui_mode: 'menu',
    game_state: null,
    available_actions: [],
    live_data: {},
    connection_status: 'connected'
});

// Derived stores for specific UI concerns
export const currentRun = derived(appState, $state => $state.game_state?.run);
export const playerData = derived(appState, $state => $state.game_state?.player_data);
export const battleState = derived(appState, $state => $state.live_data?.battle_snapshot);
export const uiMode = derived(appState, $state => $state.ui_mode);
```

### State Management Functions
```javascript
// Core state operations
export async function refreshState() {
    const state = await api.getState();
    appState.set(state);
}

export async function performAction(action, params) {
    const result = await api.sendAction(action, params);
    if (result.success) {
        // Automatically refresh state after successful actions
        await refreshState();
    }
    return result;
}

export function subscribeToUpdates() {
    // Real-time updates (future task)
    return api.subscribe(newState => appState.set(newState));
}
```

### Local Storage Integration
```javascript
// Persist critical state across sessions
function saveState(state) {
    const persistedData = {
        last_run_id: state.game_state?.run?.id,
        player_preferences: state.game_state?.meta?.settings,
        timestamp: Date.now()
    };
    localStorage.setItem('autofighter_state', JSON.stringify(persistedData));
}

function loadPersistedState() {
    // Restore basic state for offline resilience
    const saved = localStorage.getItem('autofighter_state');
    if (saved) {
        try {
            return JSON.parse(saved);
        } catch (e) {
            console.warn('Failed to parse persisted state:', e);
        }
    }
    return null;
}
```

## Testing Requirements

### Unit Tests
- [ ] Test store creation and initialization
- [ ] Test derived store calculations
- [ ] Test state persistence and restoration
- [ ] Test action integration with state updates
- [ ] Test error handling in state operations

### Integration Tests
- [ ] Test state synchronization with backend
- [ ] Test reactive UI updates
- [ ] Test localStorage persistence across page reloads
- [ ] Test concurrent state updates

### Component Tests
- [ ] Test components using new store pattern
- [ ] Test component reactivity to state changes
- [ ] Test component actions triggering state updates

## Dependencies
- **CLIENT-001**: Requires unified API client
- **API-001**: Requires backend unified state service
- Current Svelte store system and component architecture

## Risk Assessment

### Potential Issues
1. **Performance**: Reactive updates causing excessive re-renders
   - *Mitigation*: Use derived stores and careful component design
2. **State consistency**: Race conditions between actions and state updates
   - *Mitigation*: Serialize state updates, implement proper loading states
3. **Breaking existing components**: Major change to state management pattern
   - *Mitigation*: Gradual migration with backward compatibility

### Rollback Plan
- Implement alongside existing state management
- Use feature flag to enable/disable new store
- Can revert individual components to old patterns

## Estimated Effort
**Medium** (3-4 days)
- Store implementation and API integration: 2 days
- Component migration pattern and examples: 1 day
- Testing and localStorage integration: 1 day

## Implementation Strategy

### Phase 1: Core Store
```javascript
// Basic store setup
const initialState = {
    ui_mode: 'loading',
    game_state: null,
    available_actions: [],
    live_data: {},
    connection_status: 'connecting'
};

export const appState = writable(initialState);
```

### Phase 2: Action Integration
```javascript
// Connect actions to automatic state updates
export const actions = {
    async startRun(party, damageType) {
        const result = await api.sendAction('start_run', { party, damage_type: damageType });
        if (result.success) {
            await refreshState(); // Auto-update state
        }
        return result;
    },
    
    async advanceRoom() {
        const result = await api.sendAction('advance_room', {});
        if (result.success) {
            await refreshState();
        }
        return result;
    }
    // ... etc for all actions
};
```

### Phase 3: Component Migration Pattern
```svelte
<!-- OLD PATTERN -->
<script>
    import { getMap, advanceRoom } from '$lib/systems/api.js';
    
    let runId = '';
    let currentIndex = 0;
    let roomData = null;
    
    async function handleAdvance() {
        await advanceRoom(runId);
        // Manual state refresh
        const data = await getMap(runId);
        currentIndex = data.current_state.current_index;
        roomData = data.current_state.room_data;
    }
</script>

<!-- NEW PATTERN -->
<script>
    import { appState, actions } from '$lib/store.js';
    
    $: currentRun = $appState.game_state?.run;
    $: roomData = $appState.current_state?.room_data;
    
    async function handleAdvance() {
        await actions.advanceRoom(); // State updates automatically
    }
</script>
```

## Benefits

### For Developers
- Single source of truth for all state
- Automatic UI updates, no manual synchronization
- Type-safe state access with JSDoc
- Simplified component logic

### For Users
- Consistent state across page reloads
- Better error handling and recovery
- Faster UI updates with optimistic updates
- More reliable offline behavior

### For System
- Reduced complexity and bug surface area
- Better performance with targeted updates
- Easier debugging with centralized state
- Foundation for real-time features

## Migration Checklist
- [ ] Create new store with current state structure
- [ ] Implement action integration pattern
- [ ] Add localStorage persistence
- [ ] Create component migration examples
- [ ] Update route components to use new store
- [ ] Remove manual state management from components
- [ ] Update tests to use new store pattern
- [ ] Remove deprecated state management code