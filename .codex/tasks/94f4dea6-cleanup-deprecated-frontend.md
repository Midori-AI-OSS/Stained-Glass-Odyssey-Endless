# CLEANUP-002: Remove Deprecated Frontend Code and Simplify Architecture

## Objective
Complete the frontend simplification by removing all deprecated code patterns, unused components, and complex architecture that was replaced by the unified system. This final cleanup will result in a lean, maintainable frontend codebase optimized for the Docker Compose environment.

## Acceptance Criteria
- [ ] All deprecated components and utilities removed
- [ ] Complex overlay and state management patterns simplified
- [ ] Unused dependencies removed from package.json
- [ ] File structure optimized for simplified architecture
- [ ] Build size reduced through dependency and code cleanup
- [ ] All remaining code follows unified patterns consistently
- [ ] Performance improved through reduced bundle size and complexity

## Implementation Details

### File Structure Cleanup

#### Current Complex Structure:
```
frontend/src/lib/
├── systems/
│   ├── api.js (REMOVE)
│   ├── uiApi.js (REMOVE)
│   ├── backendDiscovery.js (REMOVE)
│   ├── runState.js (REMOVE)
│   ├── viewportState.js (REMOVE)
│   ├── OverlayController.js (SIMPLIFY)
│   ├── settingsStorage.js (SIMPLIFY)
│   └── logger.js (KEEP)
├── components/ (SIMPLIFY many)
├── battle/ (SIMPLIFY)
└── effects/ (REVIEW)
```

#### Simplified Target Structure:
```
frontend/src/lib/
├── api.js (NEW - unified client)
├── store.js (NEW - unified store)
├── realtime.js (NEW - WebSocket/SSE)
├── components/ (SIMPLIFIED)
├── overlays/ (SIMPLIFIED)
└── utils/ (ESSENTIAL only)
```

### Component Simplification

#### Complex Components to Simplify:

**Main Route Component (`+page.svelte`):**
```svelte
<!-- BEFORE: 1000+ lines with complex state management -->
<script>
  // Dozens of imports and state variables
  let runId = '';
  let currentIndex = 0;
  let mapRooms = [];
  let battleActive = false;
  let selectedParty = [];
  // ... 50+ more variables
  
  // Complex lifecycle and polling
  onMount(async () => {
    // 100+ lines of initialization logic
  });
  
  // Complex action handlers
  async function handleStart() {
    // 50+ lines of manual state management
  }
</script>

<!-- AFTER: ~200 lines with reactive patterns -->
<script>
  import { appState, actions } from '$lib/store.js';
  
  // Simple reactive state
  $: currentRun = $appState.game_state?.run;
  $: uiMode = $appState.ui_mode;
  $: availableActions = $appState.available_actions;
  
  // Simple lifecycle
  onMount(() => store.initialize());
  
  // Simple action handlers
  const handleAction = (type, params) => actions[type](params);
</script>
```

**Overlay System Simplification:**
```javascript
// BEFORE: Complex overlay controller with manual state passing
class OverlayController {
  constructor() {
    this.activeOverlays = [];
    this.overlayState = {};
    this.overlayData = {};
  }
  
  openOverlay(type, data) {
    // Complex state management and data passing
    // Manual synchronization with game state
    // Complex overlay stacking logic
  }
}

// AFTER: Simple reactive overlay system
export const overlayStore = writable({
  active: null,
  data: null
});

export function openOverlay(type, data = {}) {
  overlayStore.set({ active: type, data });
}

export function closeOverlay() {
  overlayStore.set({ active: null, data: null });
}
```

### Dependency Cleanup

#### Package.json Cleanup:
```json
{
  "dependencies": {
    // REMOVE unused packages:
    // - Complex state management libraries (if any)
    // - Unused UI libraries
    // - Legacy polyfills
    // - Unused utility libraries
    
    // KEEP essential packages:
    "@sveltejs/kit": "^2.0.0",
    "svelte": "^4.0.0",
    // Essential utilities only
  },
  "devDependencies": {
    // REMOVE unused dev tools
    // KEEP essential build tools
  }
}
```

#### Build Configuration Cleanup:
```javascript
// vite.config.js - optimize for simplified architecture
export default defineConfig({
  plugins: [sveltekit()],
  build: {
    // Remove unused chunks and optimize bundle
    rollupOptions: {
      output: {
        manualChunks: {
          // Simplified chunking strategy
          vendor: ['svelte'],
          game: ['$lib/store', '$lib/api']
        }
      }
    }
  }
});
```

### Specific Cleanup Tasks

#### Remove Complex State Management:
```javascript
// DELETE these files and patterns:
- frontend/src/lib/systems/runState.js
- frontend/src/lib/systems/viewportState.js
- Any custom store implementations
- Manual state persistence logic
- Complex state synchronization functions

// REPLACE with unified store patterns:
import { appState } from '$lib/store.js';
$: state = $appState; // Simple reactive access
```

#### Simplify Component Props:
```svelte
<!-- BEFORE: Complex prop drilling -->
<GameComponent 
  {runId}
  {currentIndex} 
  {mapRooms}
  {battleActive}
  {selectedParty}
  {roomData}
  bind:loading
  on:stateChange={handleStateChange}
  on:error={handleError}
/>

<!-- AFTER: No props needed, use store -->
<GameComponent />
<!-- Component gets all data from unified store -->
```

#### Remove Manual Event Handling:
```javascript
// REMOVE custom event buses and manual event handling
// REPLACE with simple action calls and reactive updates

// BEFORE:
eventBus.emit('battle-start', battleData);
eventBus.on('battle-end', handleBattleEnd);

// AFTER:
await actions.startBattle(); // State updates automatically
```

## Testing Requirements

### Cleanup Validation Tests
- [ ] All existing functionality works with simplified code
- [ ] Bundle size is significantly smaller
- [ ] Build time is faster
- [ ] Runtime performance is improved
- [ ] No memory leaks from removed code

### Code Quality Tests
- [ ] ESLint passes with no warnings
- [ ] TypeScript/JSDoc types are correct
- [ ] No unused imports or dead code
- [ ] No circular dependencies
- [ ] Consistent code patterns throughout

### Performance Tests
- [ ] Page load time comparison (before/after cleanup)
- [ ] Bundle size comparison
- [ ] Runtime memory usage comparison
- [ ] First meaningful paint time

## Dependencies
- **CLEANUP-001**: Backend cleanup should be complete first
- **All migration tasks**: Frontend must be fully migrated to unified system
- No existing functionality should depend on deprecated code

## Risk Assessment

### Potential Issues
1. **Breaking functionality**: Removing code that's still needed somewhere
   - *Mitigation*: Comprehensive testing, gradual removal, code analysis
2. **Performance regression**: Simplified code might miss optimizations
   - *Mitigation*: Performance testing, benchmarking, optimization analysis
3. **Developer experience**: Removing useful debugging or development tools
   - *Mitigation*: Identify essential tools, keep developer utilities

### Rollback Plan
- Git history allows reverting any cleanup changes
- Keep development branch with old code for reference
- Can selectively restore removed functionality if needed

## Estimated Effort
**Medium** (3-4 days)
- Component simplification: 2 days
- File structure cleanup: 1 day
- Testing and optimization: 1 day

## Detailed Cleanup Steps

### Day 1: Component Simplification
1. **Main Route Component**:
   - Remove all manual state variables
   - Replace with reactive store subscriptions
   - Simplify action handlers
   - Remove complex lifecycle logic

2. **Battle Components**:
   - Remove manual battle state tracking
   - Use live_data from store
   - Simplify component interactions

3. **Menu Components**:
   - Remove complex state passing
   - Use unified actions for all interactions
   - Simplify component hierarchy

### Day 2: File Structure and Systems
1. **Remove Systems Files**:
   ```bash
   rm frontend/src/lib/systems/api.js
   rm frontend/src/lib/systems/uiApi.js
   rm frontend/src/lib/systems/backendDiscovery.js
   rm frontend/src/lib/systems/runState.js
   rm frontend/src/lib/systems/viewportState.js
   ```

2. **Simplify Overlay System**:
   - Replace complex OverlayController with simple reactive stores
   - Remove manual overlay state management
   - Simplify overlay data passing

3. **Update All Imports**:
   ```bash
   # Find and replace all legacy imports
   find frontend/src -name "*.svelte" -o -name "*.js" | \
   xargs sed -i 's/from.*systems\/api/from $lib\/store/g'
   ```

### Day 3: Dependencies and Build Optimization
1. **Package Cleanup**:
   - Remove unused dependencies
   - Update remaining dependencies
   - Optimize bundle configuration

2. **Build Configuration**:
   - Simplify Vite configuration
   - Optimize chunk splitting
   - Remove unused build tools

3. **Performance Optimization**:
   - Tree shaking verification
   - Bundle analysis
   - Runtime optimization

## Success Metrics

### Code Reduction:
- 50%+ reduction in frontend codebase size
- 40%+ reduction in component complexity
- Elimination of duplicate code patterns

### Performance Improvements:
- 30%+ reduction in bundle size
- Faster build times
- Improved runtime performance
- Reduced memory usage

### Maintainability:
- Consistent code patterns throughout
- Simplified debugging and development
- Better code organization
- Reduced cognitive complexity

## Post-Cleanup Architecture

### Final Frontend Structure:
```
frontend/
├── src/
│   ├── lib/
│   │   ├── api.js (Unified API client)
│   │   ├── store.js (Unified state store)
│   │   ├── realtime.js (WebSocket/SSE)
│   │   └── components/ (Simplified components)
│   ├── routes/
│   │   └── +page.svelte (Simplified main component)
│   └── app.html
├── static/ (Static assets)
├── package.json (Cleaned dependencies)
└── vite.config.js (Optimized build)
```

### Code Pattern Consistency:
```svelte
<!-- Standard component pattern -->
<script>
  import { appState, actions } from '$lib/store.js';
  
  // Reactive state only
  $: gameData = $appState.game_state;
  $: uiMode = $appState.ui_mode;
  
  // Simple action handlers only
  const handleAction = (type, params) => actions[type](params);
</script>

<!-- Reactive UI -->
{#if gameData}
  <!-- Simple reactive rendering -->
{/if}
```

## Final Validation Checklist
- [ ] All deprecated code removed
- [ ] Consistent unified patterns throughout
- [ ] No legacy imports anywhere
- [ ] Bundle size optimized
- [ ] Performance improved
- [ ] All functionality preserved
- [ ] Documentation updated
- [ ] Development experience improved