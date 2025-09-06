# Task 4A: Frontend Router Client

## Overview

This task replaces the complex backend discovery system in the frontend with a simple router client that communicates exclusively with the router service, eliminating the need for the frontend to discover backend services directly.

## Goals

- Create a simple HTTP client for router communication
- Replace backend discovery logic with router-based communication
- Maintain existing frontend API contracts
- Add proper error handling and retry logic
- Implement connection health monitoring

## Prerequisites

- Task 1A, 1B, 1C (Router Service) must be completed
- Router service running on port 59000
- Backend service accessible through router

## Implementation

### Step 1: Router Client Implementation

**File**: `frontend/src/lib/api/RouterClient.js`
```javascript
/**
 * Router client for centralized API communication
 */

export class RouterClient {
    constructor(baseURL = 'http://localhost:59000') {
        this.baseURL = baseURL;
        this.timeout = 30000; // 30 seconds
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1 second
        
        // Connection state
        this.isConnected = false;
        this.lastHealthCheck = null;
        this.healthCheckInterval = null;
        
        // Start health monitoring
        this.startHealthMonitoring();
    }
    
    /**
     * Make HTTP request with retry logic
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            timeout: this.timeout,
            ...options
        };
        
        let lastError = null;
        
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                console.log(`API Request (attempt ${attempt}): ${config.method} ${url}`);
                
                const response = await fetch(url, config);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                this.isConnected = true;
                
                return data;
                
            } catch (error) {
                console.warn(`API request failed (attempt ${attempt}):`, error.message);
                lastError = error;
                this.isConnected = false;
                
                // Don't retry on certain errors
                if (error.message.includes('400') || error.message.includes('401') || error.message.includes('403')) {
                    break;
                }
                
                // Wait before retry (except on last attempt)
                if (attempt < this.retryAttempts) {
                    await this.delay(this.retryDelay * attempt);
                }
            }
        }
        
        throw new Error(`API request failed after ${this.retryAttempts} attempts: ${lastError.message}`);
    }
    
    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return await this.request(url, {
            method: 'GET'
        });
    }
    
    /**
     * POST request
     */
    async post(endpoint, data = null) {
        return await this.request(endpoint, {
            method: 'POST',
            body: data ? JSON.stringify(data) : null
        });
    }
    
    /**
     * PUT request
     */
    async put(endpoint, data = null) {
        return await this.request(endpoint, {
            method: 'PUT',
            body: data ? JSON.stringify(data) : null
        });
    }
    
    /**
     * DELETE request
     */
    async delete(endpoint) {
        return await this.request(endpoint, {
            method: 'DELETE'
        });
    }
    
    /**
     * Check router and backend health
     */
    async checkHealth() {
        try {
            // Check router health
            const routerHealth = await this.get('/health');
            
            // Check detailed health (includes backend status)
            const detailedHealth = await this.get('/health/detailed');
            
            this.lastHealthCheck = new Date();
            this.isConnected = true;
            
            return {
                router: routerHealth,
                detailed: detailedHealth,
                timestamp: this.lastHealthCheck.toISOString()
            };
            
        } catch (error) {
            console.error('Health check failed:', error.message);
            this.isConnected = false;
            throw error;
        }
    }
    
    /**
     * Start periodic health monitoring
     */
    startHealthMonitoring(interval = 30000) {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
        }
        
        this.healthCheckInterval = setInterval(async () => {
            try {
                await this.checkHealth();
                console.log('Health check passed');
            } catch (error) {
                console.warn('Background health check failed:', error.message);
            }
        }, interval);
        
        // Initial health check
        this.checkHealth().catch(error => {
            console.warn('Initial health check failed:', error.message);
        });
    }
    
    /**
     * Stop health monitoring
     */
    stopHealthMonitoring() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
        }
    }
    
    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            lastHealthCheck: this.lastHealthCheck,
            baseURL: this.baseURL
        };
    }
    
    /**
     * Utility: delay function
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Clean up resources
     */
    destroy() {
        this.stopHealthMonitoring();
    }
}

// Global router client instance
export const routerClient = new RouterClient();
```

### Step 2: Game API Client

**File**: `frontend/src/lib/api/GameAPI.js`
```javascript
/**
 * Game API client using router
 */

import { routerClient } from './RouterClient.js';

export class GameAPI {
    constructor() {
        this.client = routerClient;
    }
    
    /**
     * Create new game session
     */
    async createSession(sessionId = null) {
        const data = sessionId ? { session_id: sessionId } : {};
        return await this.client.post('/api/game/session', data);
    }
    
    /**
     * Start new game run
     */
    async startRun(sessionId, party, mapConfig) {
        return await this.client.post(`/api/game/session/${sessionId}/run`, {
            party,
            map: mapConfig
        });
    }
    
    /**
     * Get game run details
     */
    async getRun(sessionId, runId) {
        return await this.client.get(`/api/game/session/${sessionId}/run/${runId}`);
    }
    
    /**
     * List recent game runs
     */
    async listRuns(page = 1, pageSize = 10) {
        return await this.client.get('/api/game/runs', { page, page_size: pageSize });
    }
    
    /**
     * Get owned players
     */
    async getOwnedPlayers() {
        return await this.client.get('/api/game/players/owned');
    }
    
    /**
     * Add owned player
     */
    async addOwnedPlayer(playerId, playerData = null) {
        const data = playerData ? { player_data: playerData } : {};
        return await this.client.post(`/api/game/players/${playerId}/own`, data);
    }
    
    /**
     * Get player upgrade points
     */
    async getUpgradePoints(playerId) {
        return await this.client.get(`/api/game/players/${playerId}/upgrades`);
    }
    
    /**
     * Update player upgrade points
     */
    async updateUpgradePoints(playerId, pointsDelta, statUpgrades = {}) {
        return await this.client.post(`/api/game/players/${playerId}/upgrades`, {
            points_delta: pointsDelta,
            stat_upgrades: statUpgrades
        });
    }
    
    /**
     * Perform gacha roll
     */
    async performGachaRoll(playerId = 'default', rollType = 'standard') {
        return await this.client.post('/api/game/gacha/roll', {
            player_id: playerId,
            type: rollType
        });
    }
    
    /**
     * Get gacha items
     */
    async getGachaItems(limit = 50) {
        return await this.client.get('/api/game/gacha/items', { limit });
    }
    
    /**
     * Get service health status
     */
    async getHealthStatus() {
        return await this.client.checkHealth();
    }
}

// Global game API instance
export const gameAPI = new GameAPI();
```

### Step 3: Replace Backend Discovery

**File**: `frontend/src/lib/api/BackendClient.js` (replace existing)
```javascript
/**
 * Legacy backend client - now proxies through router
 * Maintains API compatibility while using router
 */

import { routerClient } from './RouterClient.js';

export class BackendClient {
    constructor() {
        this.client = routerClient;
        console.log('BackendClient: Using router-based communication');
    }
    
    /**
     * Legacy method: discover backend
     * Now just checks router health
     */
    async discoverBackend() {
        try {
            await this.client.checkHealth();
            return {
                success: true,
                url: this.client.baseURL,
                method: 'router'
            };
        } catch (error) {
            console.error('Backend discovery failed:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Legacy method: check backend connection
     */
    async checkConnection() {
        try {
            const health = await this.client.get('/api/');
            return health.status === 'ok' || health.flavor === 'default';
        } catch (error) {
            console.warn('Backend connection check failed:', error.message);
            return false;
        }
    }
    
    /**
     * Legacy method: get backend status
     */
    async getStatus() {
        try {
            return await this.client.get('/api/');
        } catch (error) {
            console.error('Failed to get backend status:', error.message);
            return { status: 'error', message: error.message };
        }
    }
    
    /**
     * Legacy method: make API request
     * Routes through router now
     */
    async makeRequest(endpoint, options = {}) {
        // Ensure endpoint starts with /api if it's a backend call
        if (!endpoint.startsWith('/api/') && !endpoint.startsWith('/health')) {
            endpoint = '/api' + (endpoint.startsWith('/') ? '' : '/') + endpoint;
        }
        
        return await this.client.request(endpoint, options);
    }
    
    /**
     * Legacy method: GET request
     */
    async get(endpoint, params = {}) {
        if (!endpoint.startsWith('/api/') && !endpoint.startsWith('/health')) {
            endpoint = '/api' + (endpoint.startsWith('/') ? '' : '/') + endpoint;
        }
        return await this.client.get(endpoint, params);
    }
    
    /**
     * Legacy method: POST request
     */
    async post(endpoint, data = null) {
        if (!endpoint.startsWith('/api/') && !endpoint.startsWith('/health')) {
            endpoint = '/api' + (endpoint.startsWith('/') ? '' : '/') + endpoint;
        }
        return await this.client.post(endpoint, data);
    }
    
    /**
     * Get connection info for debugging
     */
    getConnectionInfo() {
        return {
            type: 'router',
            url: this.client.baseURL,
            status: this.client.getConnectionStatus()
        };
    }
}

// Global backend client instance (for compatibility)
export const backendClient = new BackendClient();
```

### Step 4: Connection Status Component

**File**: `frontend/src/lib/components/ConnectionStatus.svelte`
```svelte
<script>
    import { onMount, onDestroy } from 'svelte';
    import { routerClient } from '../api/RouterClient.js';
    
    let connectionStatus = {
        connected: false,
        lastHealthCheck: null,
        baseURL: 'unknown'
    };
    
    let healthData = null;
    let statusInterval = null;
    
    onMount(() => {
        updateStatus();
        
        // Update status every 5 seconds
        statusInterval = setInterval(updateStatus, 5000);
    });
    
    onDestroy(() => {
        if (statusInterval) {
            clearInterval(statusInterval);
        }
    });
    
    async function updateStatus() {
        connectionStatus = routerClient.getConnectionStatus();
        
        try {
            healthData = await routerClient.checkHealth();
        } catch (error) {
            healthData = null;
        }
    }
    
    function getStatusClass() {
        if (!connectionStatus.connected) return 'status-error';
        if (healthData?.detailed?.status === 'healthy') return 'status-success';
        if (healthData?.detailed?.status === 'degraded') return 'status-warning';
        return 'status-unknown';
    }
    
    function getStatusText() {
        if (!connectionStatus.connected) return 'Disconnected';
        if (healthData?.detailed?.status === 'healthy') return 'Connected';
        if (healthData?.detailed?.status === 'degraded') return 'Degraded';
        return 'Unknown';
    }
</script>

<div class="connection-status {getStatusClass()}">
    <div class="status-indicator"></div>
    <div class="status-info">
        <div class="status-text">{getStatusText()}</div>
        <div class="status-details">
            <small>Router: {connectionStatus.baseURL}</small>
            {#if healthData?.detailed?.services?.backend}
                <small>Backend: {healthData.detailed.services.backend.healthy ? 'Healthy' : 'Unhealthy'}</small>
            {/if}
            {#if connectionStatus.lastHealthCheck}
                <small>Last check: {new Date(connectionStatus.lastHealthCheck).toLocaleTimeString()}</small>
            {/if}
        </div>
    </div>
</div>

<style>
    .connection-status {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 0.9em;
        margin: 8px 0;
    }
    
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        flex-shrink: 0;
    }
    
    .status-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    
    .status-text {
        font-weight: 500;
    }
    
    .status-details {
        display: flex;
        flex-direction: column;
        gap: 1px;
    }
    
    .status-details small {
        opacity: 0.8;
        font-size: 0.8em;
    }
    
    /* Status colors */
    .status-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-success .status-indicator {
        background-color: #28a745;
    }
    
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .status-warning .status-indicator {
        background-color: #ffc107;
    }
    
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .status-error .status-indicator {
        background-color: #dc3545;
    }
    
    .status-unknown {
        background-color: #e2e3e5;
        color: #383d41;
        border: 1px solid #d6d8db;
    }
    
    .status-unknown .status-indicator {
        background-color: #6c757d;
    }
</style>
```

### Step 5: Updated App Configuration

**File**: `frontend/src/lib/config.js` (update existing)
```javascript
/**
 * Updated application configuration for router-based communication
 */

export const config = {
    // Router service configuration
    router: {
        baseURL: process.env.NODE_ENV === 'production' 
            ? 'http://localhost:59000'  // Production router URL
            : 'http://localhost:59000', // Development router URL
        timeout: 30000,
        retryAttempts: 3,
        healthCheckInterval: 30000
    },
    
    // Legacy backend config (deprecated - use router instead)
    backend: {
        // These are now ignored - keeping for compatibility
        discoveryPorts: [59002],
        discoveryTimeout: 5000,
        fallbackURL: 'http://localhost:59002'
    },
    
    // Game configuration
    game: {
        defaultSessionTimeout: 600000, // 10 minutes
        autosaveInterval: 30000,       // 30 seconds
        maxRetries: 3
    },
    
    // UI configuration
    ui: {
        showConnectionStatus: true,
        showDebugInfo: process.env.NODE_ENV !== 'production',
        theme: 'default'
    },
    
    // API configuration
    api: {
        requestTimeout: 30000,
        retryDelay: 1000,
        maxRetries: 3
    }
};

// Environment-specific overrides
if (process.env.NODE_ENV === 'development') {
    config.ui.showDebugInfo = true;
    config.router.healthCheckInterval = 10000; // More frequent in dev
}

export default config;
```

### Step 6: Integration Example

**File**: `frontend/src/routes/+page.svelte` (update existing)
```svelte
<script>
    import { onMount } from 'svelte';
    import { gameAPI } from '../lib/api/GameAPI.js';
    import ConnectionStatus from '../lib/components/ConnectionStatus.svelte';
    import config from '../lib/config.js';
    
    let gameSession = null;
    let ownedPlayers = [];
    let recentRuns = [];
    let loading = false;
    let error = null;
    
    onMount(async () => {
        await initializeApp();
    });
    
    async function initializeApp() {
        loading = true;
        error = null;
        
        try {
            // Create game session
            const sessionResponse = await gameAPI.createSession();
            gameSession = sessionResponse.data;
            
            // Load owned players
            const playersResponse = await gameAPI.getOwnedPlayers();
            ownedPlayers = playersResponse.data.players;
            
            // Load recent runs
            const runsResponse = await gameAPI.listRuns(1, 5);
            recentRuns = runsResponse.data;
            
            console.log('App initialized successfully');
            
        } catch (err) {
            console.error('App initialization failed:', err);
            error = err.message;
        } finally {
            loading = false;
        }
    }
    
    async function startNewRun() {
        if (!gameSession) {
            error = 'No game session available';
            return;
        }
        
        try {
            const party = { player1: { name: 'Test Player', level: 1 } };
            const mapConfig = { level: 1, area: 'starter' };
            
            const response = await gameAPI.startRun(gameSession.session_id, party, mapConfig);
            console.log('Started new run:', response.data);
            
            // Refresh recent runs
            const runsResponse = await gameAPI.listRuns(1, 5);
            recentRuns = runsResponse.data;
            
        } catch (err) {
            console.error('Failed to start run:', err);
            error = err.message;
        }
    }
    
    async function performGachaRoll() {
        try {
            const response = await gameAPI.performGachaRoll('player1', 'standard');
            console.log('Gacha roll result:', response.data);
            alert(`Gacha roll completed! Got ${response.data.items.length} items.`);
            
        } catch (err) {
            console.error('Gacha roll failed:', err);
            error = err.message;
        }
    }
</script>

<svelte:head>
    <title>AutoFighter - Router Integration</title>
</svelte:head>

<div class="app">
    <header>
        <h1>AutoFighter</h1>
        <p>Router-based Communication</p>
    </header>
    
    {#if config.ui.showConnectionStatus}
        <ConnectionStatus />
    {/if}
    
    {#if loading}
        <div class="loading">
            <p>Loading...</p>
        </div>
    {:else if error}
        <div class="error">
            <p>Error: {error}</p>
            <button on:click={initializeApp}>Retry</button>
        </div>
    {:else}
        <main>
            <section class="game-info">
                <h2>Game Session</h2>
                {#if gameSession}
                    <p>Session ID: {gameSession.session_id}</p>
                    <button on:click={startNewRun}>Start New Run</button>
                {:else}
                    <p>No active session</p>
                {/if}
            </section>
            
            <section class="owned-players">
                <h2>Owned Players ({ownedPlayers.length})</h2>
                {#if ownedPlayers.length > 0}
                    <ul>
                        {#each ownedPlayers as player}
                            <li>{player}</li>
                        {/each}
                    </ul>
                {:else}
                    <p>No owned players</p>
                {/if}
            </section>
            
            <section class="recent-runs">
                <h2>Recent Runs</h2>
                {#if recentRuns.length > 0}
                    <ul>
                        {#each recentRuns as run}
                            <li>
                                Run {run.id} - {new Date(run.updated_at).toLocaleString()}
                            </li>
                        {/each}
                    </ul>
                {:else}
                    <p>No recent runs</p>
                {/if}
            </section>
            
            <section class="actions">
                <h2>Actions</h2>
                <button on:click={performGachaRoll}>Perform Gacha Roll</button>
            </section>
        </main>
    {/if}
</div>

<style>
    .app {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        font-family: Arial, sans-serif;
    }
    
    header {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .loading, .error {
        text-align: center;
        padding: 20px;
        margin: 20px 0;
    }
    
    .error {
        background-color: #f8d7da;
        color: #721c24;
        border-radius: 4px;
    }
    
    section {
        margin: 20px 0;
        padding: 15px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    
    button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        margin: 5px;
    }
    
    button:hover {
        background-color: #0056b3;
    }
    
    ul {
        list-style-type: none;
        padding: 0;
    }
    
    li {
        padding: 5px 0;
        border-bottom: 1px solid #eee;
    }
</style>
```

## Validation Criteria

### Success Criteria
1. **Router Communication**: Frontend communicates exclusively with router service
2. **API Compatibility**: Existing frontend functionality works unchanged
3. **Error Handling**: Network errors are handled gracefully with retry logic
4. **Health Monitoring**: Connection status is monitored and displayed
5. **Performance**: Response times are acceptable through router proxy

### Validation Commands
```bash
# Start router service (ensure it's running)
cd router
uv run uvicorn app:app --host 0.0.0.0 --port 59000

# Start frontend development server
cd frontend
bun run dev

# Test router communication directly
curl http://localhost:59000/health
curl http://localhost:59000/api/

# Access frontend application
open http://localhost:59001
```

### Expected Results
- Frontend starts successfully and connects to router
- Connection status shows "Connected" with green indicator
- All game functionality works through router
- Backend discovery system is no longer used
- Network errors show retry attempts in console
- Health monitoring updates every 30 seconds

## Notes

- Router client handles all HTTP communication centrally
- Legacy backend client maintained for compatibility but routes through router
- Connection status component provides visual feedback
- Retry logic handles temporary network issues
- Health monitoring detects service availability automatically
- Frontend no longer needs to know about backend ports or discovery