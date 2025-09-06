# Task 4B: Frontend UI Updates

## Overview

This task updates the frontend UI components to work seamlessly with the new router-based communication pattern, improving user experience with better error handling, loading states, and connection status indicators.

## Goals

- Update UI components to use new router-based API clients
- Improve error handling and user feedback
- Add loading states and progress indicators
- Create responsive design components
- Implement proper state management

## Prerequisites

- Task 4A (Frontend Router Client) must be completed
- Router client and GameAPI implemented
- Frontend development environment set up

## Implementation

### Step 1: Enhanced Error Handling Component

**File**: `frontend/src/lib/components/ErrorDisplay.svelte`
```svelte
<script>
    export let error = null;
    export let title = "Error";
    export let showRetry = true;
    export let onRetry = null;
    export let dismissible = true;
    export let onDismiss = null;
    
    let visible = true;
    
    function handleRetry() {
        if (onRetry) {
            onRetry();
        }
    }
    
    function handleDismiss() {
        visible = false;
        if (onDismiss) {
            onDismiss();
        }
    }
    
    function getErrorType(error) {
        if (!error) return 'unknown';
        
        const message = error.message || error.toString();
        
        if (message.includes('Network') || message.includes('fetch')) {
            return 'network';
        }
        if (message.includes('timeout')) {
            return 'timeout';
        }
        if (message.includes('401') || message.includes('403')) {
            return 'auth';
        }
        if (message.includes('404')) {
            return 'notfound';
        }
        if (message.includes('500')) {
            return 'server';
        }
        
        return 'generic';
    }
    
    function getErrorIcon(type) {
        switch (type) {
            case 'network': return '🌐';
            case 'timeout': return '⏱️';
            case 'auth': return '🔒';
            case 'notfound': return '❓';
            case 'server': return '🔧';
            default: return '⚠️';
        }
    }
    
    function getErrorMessage(error, type) {
        if (!error) return 'An unknown error occurred';
        
        const message = error.message || error.toString();
        
        switch (type) {
            case 'network':
                return 'Network connection failed. Please check your internet connection.';
            case 'timeout':
                return 'Request timed out. The server may be overloaded.';
            case 'auth':
                return 'Authentication failed. Please check your credentials.';
            case 'notfound':
                return 'The requested resource was not found.';
            case 'server':
                return 'Server error occurred. Please try again later.';
            default:
                return message;
        }
    }
    
    $: errorType = getErrorType(error);
    $: errorIcon = getErrorIcon(errorType);
    $: errorMessage = getErrorMessage(error, errorType);
</script>

{#if error && visible}
    <div class="error-display error-{errorType}">
        <div class="error-header">
            <span class="error-icon">{errorIcon}</span>
            <h3 class="error-title">{title}</h3>
            {#if dismissible}
                <button class="error-dismiss" on:click={handleDismiss}>&times;</button>
            {/if}
        </div>
        
        <div class="error-content">
            <p class="error-message">{errorMessage}</p>
            
            {#if showRetry && onRetry}
                <div class="error-actions">
                    <button class="retry-button" on:click={handleRetry}>
                        Try Again
                    </button>
                </div>
            {/if}
        </div>
    </div>
{/if}

<style>
    .error-display {
        border-radius: 8px;
        margin: 16px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
    
    .error-header {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        font-weight: 500;
    }
    
    .error-icon {
        font-size: 1.2em;
        margin-right: 8px;
    }
    
    .error-title {
        flex: 1;
        margin: 0;
        font-size: 1em;
        font-weight: 500;
    }
    
    .error-dismiss {
        background: none;
        border: none;
        font-size: 1.5em;
        cursor: pointer;
        opacity: 0.7;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .error-dismiss:hover {
        opacity: 1;
    }
    
    .error-content {
        padding: 0 16px 16px;
    }
    
    .error-message {
        margin: 0 0 12px 0;
        line-height: 1.4;
    }
    
    .error-actions {
        display: flex;
        gap: 8px;
    }
    
    .retry-button {
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.5);
        padding: 6px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9em;
    }
    
    .retry-button:hover {
        background-color: rgba(255, 255, 255, 1);
    }
    
    /* Error type specific styles */
    .error-network {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #0d47a1;
    }
    
    .error-timeout {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        color: #e65100;
    }
    
    .error-auth {
        background-color: #fce4ec;
        border-left: 4px solid #e91e63;
        color: #880e4f;
    }
    
    .error-notfound {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        color: #4a148c;
    }
    
    .error-server {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        color: #b71c1c;
    }
    
    .error-generic {
        background-color: #fff8e1;
        border-left: 4px solid #ffc107;
        color: #f57f17;
    }
</style>
```

### Step 2: Loading States Component

**File**: `frontend/src/lib/components/LoadingSpinner.svelte`
```svelte
<script>
    export let size = 'medium'; // small, medium, large
    export let message = '';
    export let overlay = false;
    export let color = '#007bff';
    
    function getSizeClass(size) {
        switch (size) {
            case 'small': return 'spinner-small';
            case 'large': return 'spinner-large';
            default: return 'spinner-medium';
        }
    }
</script>

<div class="loading-container" class:overlay>
    <div class="spinner-wrapper">
        <div class="spinner {getSizeClass(size)}" style="border-top-color: {color}"></div>
        {#if message}
            <p class="loading-message">{message}</p>
        {/if}
    </div>
</div>

<style>
    .loading-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    
    .loading-container.overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.8);
        z-index: 1000;
    }
    
    .spinner-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
    }
    
    .spinner {
        border: 3px solid #f3f3f3;
        border-top: 3px solid #007bff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    .spinner-small {
        width: 20px;
        height: 20px;
        border-width: 2px;
    }
    
    .spinner-medium {
        width: 32px;
        height: 32px;
    }
    
    .spinner-large {
        width: 48px;
        height: 48px;
        border-width: 4px;
    }
    
    .loading-message {
        margin: 0;
        color: #666;
        font-size: 0.9em;
        text-align: center;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
```

### Step 3: Game Session Manager Component

**File**: `frontend/src/lib/components/GameSession.svelte`
```svelte
<script>
    import { onMount, createEventDispatcher } from 'svelte';
    import { gameAPI } from '../api/GameAPI.js';
    import LoadingSpinner from './LoadingSpinner.svelte';
    import ErrorDisplay from './ErrorDisplay.svelte';
    
    const dispatch = createEventDispatcher();
    
    export let sessionId = null;
    
    let session = null;
    let loading = false;
    let error = null;
    let runs = [];
    let selectedRun = null;
    
    onMount(async () => {
        if (sessionId) {
            // Try to use existing session
            session = { session_id: sessionId };
        } else {
            await createNewSession();
        }
        
        await loadRecentRuns();
    });
    
    async function createNewSession() {
        loading = true;
        error = null;
        
        try {
            const response = await gameAPI.createSession();
            session = response.data;
            
            dispatch('sessionCreated', { session });
            
        } catch (err) {
            console.error('Failed to create session:', err);
            error = err;
        } finally {
            loading = false;
        }
    }
    
    async function startNewRun() {
        if (!session) return;
        
        loading = true;
        error = null;
        
        try {
            // Default party and map configuration
            const party = {
                player1: {
                    name: 'Default Player',
                    level: 1,
                    class: 'warrior'
                }
            };
            
            const mapConfig = {
                level: 1,
                area: 'starter_dungeon',
                difficulty: 'normal'
            };
            
            const response = await gameAPI.startRun(session.session_id, party, mapConfig);
            const newRun = response.data;
            
            // Add to runs list
            runs = [newRun, ...runs.slice(0, 9)]; // Keep last 10 runs
            selectedRun = newRun;
            
            dispatch('runStarted', { run: newRun });
            
        } catch (err) {
            console.error('Failed to start run:', err);
            error = err;
        } finally {
            loading = false;
        }
    }
    
    async function loadRecentRuns() {
        try {
            const response = await gameAPI.listRuns(1, 10);
            runs = response.data || [];
            
            if (runs.length > 0) {
                selectedRun = runs[0];
            }
            
        } catch (err) {
            console.warn('Failed to load recent runs:', err);
            // Don't show error for this, as it's not critical
        }
    }
    
    async function selectRun(run) {
        selectedRun = run;
        dispatch('runSelected', { run });
    }
    
    function handleRetry() {
        if (!session) {
            createNewSession();
        } else {
            loadRecentRuns();
        }
    }
</script>

<div class="game-session">
    <div class="session-header">
        <h2>Game Session</h2>
        {#if session}
            <div class="session-info">
                <span class="session-id">ID: {session.session_id.slice(0, 8)}...</span>
                <button class="start-run-btn" on:click={startNewRun} disabled={loading}>
                    {loading ? 'Starting...' : 'Start New Run'}
                </button>
            </div>
        {/if}
    </div>
    
    {#if loading && !session}
        <LoadingSpinner message="Creating game session..." />
    {:else if error}
        <ErrorDisplay {error} title="Session Error" onRetry={handleRetry} />
    {:else if session}
        <div class="session-content">
            <div class="runs-section">
                <h3>Recent Runs ({runs.length})</h3>
                
                {#if runs.length > 0}
                    <div class="runs-list">
                        {#each runs as run}
                            <div 
                                class="run-item" 
                                class:selected={selectedRun?.run_id === run.run_id}
                                on:click={() => selectRun(run)}
                                role="button"
                                tabindex="0"
                                on:keypress={(e) => e.key === 'Enter' && selectRun(run)}
                            >
                                <div class="run-header">
                                    <span class="run-id">Run {run.run_id?.slice(0, 8) || 'Unknown'}</span>
                                    <span class="run-date">{new Date(run.created_at || Date.now()).toLocaleDateString()}</span>
                                </div>
                                <div class="run-details">
                                    <span class="party-size">
                                        Party: {Object.keys(run.party || {}).length} members
                                    </span>
                                    <span class="map-info">
                                        Map: {run.map?.area || 'Unknown'}
                                    </span>
                                </div>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <div class="no-runs">
                        <p>No runs yet. Start your first adventure!</p>
                    </div>
                {/if}
            </div>
            
            {#if selectedRun}
                <div class="run-details-section">
                    <h3>Run Details</h3>
                    <div class="run-info">
                        <div class="info-group">
                            <label>Run ID:</label>
                            <span>{selectedRun.run_id}</span>
                        </div>
                        <div class="info-group">
                            <label>Created:</label>
                            <span>{new Date(selectedRun.created_at || Date.now()).toLocaleString()}</span>
                        </div>
                        <div class="info-group">
                            <label>Party:</label>
                            <span>{JSON.stringify(selectedRun.party, null, 2)}</span>
                        </div>
                        <div class="info-group">
                            <label>Map:</label>
                            <span>{JSON.stringify(selectedRun.map, null, 2)}</span>
                        </div>
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</div>

<style>
    .game-session {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
        background-color: #f9f9f9;
    }
    
    .session-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    
    .session-header h2 {
        margin: 0;
        color: #333;
    }
    
    .session-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .session-id {
        font-family: monospace;
        background-color: #e9ecef;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
    }
    
    .start-run-btn {
        background-color: #28a745;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 500;
    }
    
    .start-run-btn:hover:not(:disabled) {
        background-color: #218838;
    }
    
    .start-run-btn:disabled {
        background-color: #6c757d;
        cursor: not-allowed;
    }
    
    .session-content {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }
    
    .runs-section h3,
    .run-details-section h3 {
        margin: 0 0 12px 0;
        color: #495057;
    }
    
    .runs-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        max-height: 300px;
        overflow-y: auto;
    }
    
    .run-item {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 12px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .run-item:hover {
        border-color: #007bff;
        box-shadow: 0 2px 4px rgba(0, 123, 255, 0.1);
    }
    
    .run-item.selected {
        border-color: #007bff;
        background-color: #e7f3ff;
    }
    
    .run-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    
    .run-id {
        font-weight: 500;
        font-family: monospace;
    }
    
    .run-date {
        font-size: 0.85em;
        color: #6c757d;
    }
    
    .run-details {
        display: flex;
        flex-direction: column;
        gap: 2px;
        font-size: 0.85em;
        color: #6c757d;
    }
    
    .no-runs {
        text-align: center;
        padding: 20px;
        color: #6c757d;
        font-style: italic;
    }
    
    .run-info {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 12px;
    }
    
    .info-group {
        display: flex;
        margin-bottom: 8px;
        gap: 8px;
    }
    
    .info-group label {
        font-weight: 500;
        min-width: 80px;
        color: #495057;
    }
    
    .info-group span {
        flex: 1;
        word-break: break-all;
        font-family: monospace;
        font-size: 0.9em;
        white-space: pre-wrap;
    }
    
    @media (max-width: 768px) {
        .session-content {
            grid-template-columns: 1fr;
        }
        
        .session-header {
            flex-direction: column;
            gap: 12px;
            align-items: stretch;
        }
        
        .session-info {
            justify-content: space-between;
        }
    }
</style>
```

### Step 4: Gacha System Component

**File**: `frontend/src/lib/components/GachaSystem.svelte`
```svelte
<script>
    import { onMount, createEventDispatcher } from 'svelte';
    import { gameAPI } from '../api/GameAPI.js';
    import LoadingSpinner from './LoadingSpinner.svelte';
    import ErrorDisplay from './ErrorDisplay.svelte';
    
    const dispatch = createEventDispatcher();
    
    let gachaItems = [];
    let recentRolls = [];
    let loading = false;
    let rolling = false;
    let error = null;
    let selectedRollType = 'standard';
    let playerId = 'default';
    
    const rollTypes = [
        { id: 'standard', name: 'Standard Roll', cost: 100 },
        { id: 'premium', name: 'Premium Roll', cost: 300 },
        { id: 'event', name: 'Event Roll', cost: 500 }
    ];
    
    onMount(async () => {
        await loadGachaItems();
    });
    
    async function loadGachaItems() {
        loading = true;
        error = null;
        
        try {
            const response = await gameAPI.getGachaItems(20);
            gachaItems = response.data?.items || [];
            
        } catch (err) {
            console.error('Failed to load gacha items:', err);
            error = err;
        } finally {
            loading = false;
        }
    }
    
    async function performRoll() {
        rolling = true;
        error = null;
        
        try {
            const response = await gameAPI.performGachaRoll(playerId, selectedRollType);
            const rollResult = response.data;
            
            // Add to recent rolls
            recentRolls = [rollResult, ...recentRolls.slice(0, 4)]; // Keep last 5 rolls
            
            // Refresh gacha items
            await loadGachaItems();
            
            dispatch('rollCompleted', { result: rollResult });
            
        } catch (err) {
            console.error('Gacha roll failed:', err);
            error = err;
        } finally {
            rolling = false;
        }
    }
    
    function getItemRarityClass(starLevel) {
        if (starLevel >= 5) return 'rarity-legendary';
        if (starLevel >= 4) return 'rarity-epic';
        if (starLevel >= 3) return 'rarity-rare';
        if (starLevel >= 2) return 'rarity-uncommon';
        return 'rarity-common';
    }
    
    function getRarityName(starLevel) {
        if (starLevel >= 5) return 'Legendary';
        if (starLevel >= 4) return 'Epic';
        if (starLevel >= 3) return 'Rare';
        if (starLevel >= 2) return 'Uncommon';
        return 'Common';
    }
    
    function handleRetry() {
        loadGachaItems();
    }
</script>

<div class="gacha-system">
    <div class="gacha-header">
        <h2>Gacha System</h2>
        <div class="player-select">
            <label for="player-id">Player ID:</label>
            <input 
                id="player-id"
                type="text" 
                bind:value={playerId} 
                placeholder="Enter player ID"
                disabled={rolling}
            />
        </div>
    </div>
    
    <div class="gacha-content">
        <div class="roll-section">
            <h3>Perform Roll</h3>
            
            <div class="roll-types">
                {#each rollTypes as rollType}
                    <label class="roll-type-option">
                        <input 
                            type="radio" 
                            bind:group={selectedRollType} 
                            value={rollType.id}
                            disabled={rolling}
                        />
                        <span class="roll-type-info">
                            <span class="roll-name">{rollType.name}</span>
                            <span class="roll-cost">{rollType.cost} coins</span>
                        </span>
                    </label>
                {/each}
            </div>
            
            <button 
                class="roll-button" 
                on:click={performRoll} 
                disabled={rolling || !playerId.trim()}
            >
                {rolling ? 'Rolling...' : `Perform ${selectedRollType} Roll`}
            </button>
            
            {#if rolling}
                <LoadingSpinner size="small" message="Rolling for items..." />
            {/if}
        </div>
        
        {#if recentRolls.length > 0}
            <div class="recent-rolls">
                <h3>Recent Rolls</h3>
                <div class="rolls-list">
                    {#each recentRolls as roll}
                        <div class="roll-result">
                            <div class="roll-header">
                                <span class="roll-time">
                                    {new Date(roll.timestamp).toLocaleTimeString()}
                                </span>
                                <span class="items-count">
                                    {roll.items.length} items
                                </span>
                            </div>
                            <div class="roll-items">
                                {#each roll.items as item}
                                    <div class="item-badge {getItemRarityClass(item.star_level)}">
                                        <span class="item-name">{item.name || item.id}</span>
                                        <span class="item-stars">{'★'.repeat(item.star_level)}</span>
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}
    </div>
    
    <div class="items-section">
        <h3>Collected Items ({gachaItems.length})</h3>
        
        {#if loading}
            <LoadingSpinner message="Loading gacha items..." />
        {:else if error}
            <ErrorDisplay {error} title="Failed to Load Items" onRetry={handleRetry} />
        {:else if gachaItems.length > 0}
            <div class="items-grid">
                {#each gachaItems as item}
                    <div class="item-card {getItemRarityClass(item.star_level)}">
                        <div class="item-header">
                            <span class="item-type">{item.type}</span>
                            <span class="item-rarity">{getRarityName(item.star_level)}</span>
                        </div>
                        <div class="item-name">{item.item_id}</div>
                        <div class="item-stars">{'★'.repeat(item.star_level)}</div>
                        <div class="item-obtained">
                            {new Date(item.obtained_at).toLocaleDateString()}
                        </div>
                    </div>
                {/each}
            </div>
        {:else}
            <div class="no-items">
                <p>No items collected yet. Try performing a gacha roll!</p>
            </div>
        {/if}
    </div>
</div>

<style>
    .gacha-system {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
        background-color: #f8f9fa;
    }
    
    .gacha-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    
    .gacha-header h2 {
        margin: 0;
        color: #333;
    }
    
    .player-select {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .player-select input {
        padding: 4px 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 0.9em;
    }
    
    .gacha-content {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 24px;
    }
    
    .roll-section h3,
    .recent-rolls h3,
    .items-section h3 {
        margin: 0 0 12px 0;
        color: #495057;
    }
    
    .roll-types {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 16px;
    }
    
    .roll-type-option {
        display: flex;
        align-items: center;
        padding: 8px;
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        cursor: pointer;
    }
    
    .roll-type-option:hover {
        border-color: #007bff;
    }
    
    .roll-type-option input {
        margin-right: 8px;
    }
    
    .roll-type-info {
        display: flex;
        flex-direction: column;
    }
    
    .roll-name {
        font-weight: 500;
    }
    
    .roll-cost {
        font-size: 0.85em;
        color: #6c757d;
    }
    
    .roll-button {
        background-color: #ff6b35;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
        font-size: 1em;
        margin-bottom: 16px;
    }
    
    .roll-button:hover:not(:disabled) {
        background-color: #e55a2b;
    }
    
    .roll-button:disabled {
        background-color: #6c757d;
        cursor: not-allowed;
    }
    
    .rolls-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
        max-height: 300px;
        overflow-y: auto;
    }
    
    .roll-result {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 12px;
    }
    
    .roll-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 0.85em;
        color: #6c757d;
    }
    
    .roll-items {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
    }
    
    .item-badge {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 4px 6px;
        border-radius: 4px;
        font-size: 0.75em;
        min-width: 60px;
    }
    
    .item-badge .item-name {
        font-weight: 500;
        text-align: center;
    }
    
    .item-badge .item-stars {
        font-size: 0.8em;
    }
    
    .items-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 12px;
    }
    
    .item-card {
        background-color: white;
        border: 2px solid;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        transition: transform 0.2s;
    }
    
    .item-card:hover {
        transform: translateY(-2px);
    }
    
    .item-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 0.75em;
        text-transform: uppercase;
        font-weight: 500;
    }
    
    .item-name {
        font-weight: 500;
        margin-bottom: 4px;
        word-break: break-word;
    }
    
    .item-stars {
        margin-bottom: 8px;
        font-size: 1.1em;
    }
    
    .item-obtained {
        font-size: 0.75em;
        color: #6c757d;
    }
    
    .no-items {
        text-align: center;
        padding: 40px;
        color: #6c757d;
        font-style: italic;
    }
    
    /* Rarity colors */
    .rarity-common {
        border-color: #6c757d;
        background-color: #f8f9fa;
        color: #495057;
    }
    
    .rarity-uncommon {
        border-color: #28a745;
        background-color: #d4edda;
        color: #155724;
    }
    
    .rarity-rare {
        border-color: #007bff;
        background-color: #d1ecf1;
        color: #0c5460;
    }
    
    .rarity-epic {
        border-color: #6f42c1;
        background-color: #e2d9f3;
        color: #3d1a78;
    }
    
    .rarity-legendary {
        border-color: #fd7e14;
        background-color: #fff3cd;
        color: #856404;
    }
    
    @media (max-width: 768px) {
        .gacha-content {
            grid-template-columns: 1fr;
        }
        
        .gacha-header {
            flex-direction: column;
            gap: 12px;
            align-items: stretch;
        }
        
        .items-grid {
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        }
    }
</style>
```

## Validation Criteria

### Success Criteria
1. **UI Responsiveness**: Components work well on desktop and mobile devices
2. **Error Handling**: Clear error messages with appropriate retry mechanisms
3. **Loading States**: Visual feedback during API operations
4. **User Experience**: Intuitive interface with proper state management
5. **Router Integration**: All components use router-based API communication

### Validation Commands
```bash
# Start development environment
cd frontend
bun run dev

# Test components in browser
open http://localhost:59001

# Test error scenarios (stop backend/router)
# Verify error handling and retry functionality

# Test responsive design
# Resize browser window to mobile/tablet sizes
```

### Expected Results
- All UI components render correctly
- Loading spinners appear during API calls
- Error messages are clear and actionable
- Retry functionality works properly
- Mobile responsive design works well
- Gacha system shows proper item rarity colors
- Game session management is intuitive

## Notes

- Components use semantic HTML and proper accessibility attributes
- Error handling is context-aware with specific messaging
- Loading states prevent user confusion during operations
- Responsive design ensures mobile compatibility
- All API communication goes through router client
- State management is simplified but effective