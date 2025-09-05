# Task 04: Frontend Communication Simplification

## Objective
Simplify the frontend to communicate only with the router service, removing complex backend discovery and standardizing all API interactions.

## Requirements

### 1. Remove Backend Discovery
- Replace `backendDiscovery.js` with simple router configuration
- Remove environment-based API base detection
- Single configuration point for router endpoint

### 2. Standardize API Communication
- Update all API calls to use router service
- Implement consistent error handling
- Add request/response interceptors
- Support for standardized response format

### 3. Configuration Simplification
- Environment-based router endpoint
- Remove hardcoded port discovery
- Graceful fallback handling

## Implementation Tasks

### Task 4.1: Replace Backend Discovery
**File**: `frontend/src/lib/systems/routerClient.js` (Replace `backendDiscovery.js`)
```javascript
/**
 * Router client for simplified service communication
 * Replaces the complex backend discovery system
 */

let ROUTER_BASE = null;

/**
 * Get router service base URL
 * @returns {Promise<string>} Router base URL
 */
export async function getRouterBase() {
  if (ROUTER_BASE) {
    return ROUTER_BASE;
  }

  // Check environment variable first
  const envBase = import.meta.env?.VITE_ROUTER_BASE;
  if (envBase) {
    ROUTER_BASE = envBase;
    return ROUTER_BASE;
  }

  // Default to standard router port in Docker Compose
  ROUTER_BASE = 'http://localhost:59000';
  return ROUTER_BASE;
}

/**
 * Reset router discovery (for testing)
 */
export function resetRouterDiscovery() {
  ROUTER_BASE = null;
}

/**
 * Get cached router base URL
 * @returns {string|null} Cached router base URL
 */
export function getCachedRouterBase() {
  return ROUTER_BASE;
}

/**
 * Test router connectivity
 * @returns {Promise<boolean>} True if router is reachable
 */
export async function testRouterConnectivity() {
  try {
    const routerBase = await getRouterBase();
    const response = await fetch(`${routerBase}/health/`, { 
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      cache: 'no-store'
    });
    
    return response.ok;
  } catch {
    return false;
  }
}
```

### Task 4.2: Standardized API Client
**File**: `frontend/src/lib/systems/apiClient.js` (Replace `api.js`)
```javascript
/**
 * Standardized API client for router communication
 * Replaces the mixed API communication patterns
 */

import { openOverlay } from './OverlayController.js';
import { getRouterBase } from './routerClient.js';

// API client configuration
const API_CONFIG = {
  timeout: 30000,
  retries: 3,
  retryDelay: 1000
};

/**
 * Standardized response format interface
 * @typedef {Object} ApiResponse
 * @property {string} status - Response status ('ok', 'error')
 * @property {string} message - Response message
 * @property {*} data - Response data
 * @property {string} timestamp - Response timestamp
 */

/**
 * Enhanced fetch with retry logic and standardized error handling
 * @param {string} endpoint - API endpoint (relative to router)
 * @param {Object} options - Fetch options
 * @param {Function} parser - Response parser function
 * @returns {Promise<*>} Parsed response
 */
async function apiRequest(endpoint, options = {}, parser = (r) => r.json()) {
  const routerBase = await getRouterBase();
  
  // Normalize endpoint
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${routerBase}/api${normalizedEndpoint}`;
  
  // Default options
  const requestOptions = {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers
    },
    timeout: API_CONFIG.timeout,
    ...options
  };

  let lastError;
  
  // Retry logic
  for (let attempt = 1; attempt <= API_CONFIG.retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), requestOptions.timeout);
      
      const response = await fetch(url, {
        ...requestOptions,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await handleErrorResponse(response);
        throw new ApiError(errorData.message, response.status, errorData);
      }
      
      const data = await parser(response);
      
      // Handle standardized response format
      if (data && typeof data === 'object' && 'status' in data) {
        if (data.status === 'error') {
          throw new ApiError(data.message, response.status, data);
        }
        return data.data || data; // Return data field if present, otherwise full response
      }
      
      return data;
      
    } catch (error) {
      lastError = error;
      
      // Don't retry on certain errors
      if (error instanceof ApiError && error.status < 500) {
        break;
      }
      
      // Don't retry on last attempt
      if (attempt === API_CONFIG.retries) {
        break;
      }
      
      // Wait before retry
      await new Promise(resolve => setTimeout(resolve, API_CONFIG.retryDelay * attempt));
    }
  }
  
  // Handle final error
  if (!options.noOverlay) {
    const errorMessage = lastError?.message || 'API request failed';
    const errorDetails = lastError?.details || { url, attempts: API_CONFIG.retries };
    
    openOverlay('error', { 
      message: errorMessage, 
      traceback: JSON.stringify(errorDetails, null, 2) 
    });
  }
  
  throw lastError;
}

/**
 * Handle error responses with consistent format
 * @param {Response} response - Fetch response
 * @returns {Promise<Object>} Error data
 */
async function handleErrorResponse(response) {
  try {
    const errorData = await response.json();
    
    // Handle standardized error format
    if (errorData && typeof errorData === 'object') {
      return {
        message: errorData.message || `HTTP ${response.status}`,
        details: errorData.details || errorData,
        status: errorData.status || 'error'
      };
    }
    
    return { message: `HTTP ${response.status}`, details: errorData };
  } catch {
    return { message: `HTTP ${response.status} - ${response.statusText}` };
  }
}

/**
 * Custom API error class
 */
class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

// ============================================================================
// SPECIFIC API METHODS (Updated from original api.js)
// ============================================================================

/**
 * Get backend service status through router
 * @returns {Promise<Object>} Backend status
 */
export async function getBackendStatus() {
  try {
    const routerBase = await getRouterBase();
    const response = await fetch(`${routerBase}/api/`, { 
      cache: 'no-store', 
      headers: { 'Accept': 'application/json' }
    });
    
    if (!response.ok) {
      throw new Error(`Backend status check failed: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    // Show backend connectivity overlay
    const routerBase = await getRouterBase();
    openOverlay('backend-not-ready', { 
      apiBase: routerBase, 
      message: error?.message || 'Backend unavailable' 
    });
    throw error;
  }
}

/**
 * Get backend flavor through router
 * @returns {Promise<string>} Backend flavor
 */
export async function getBackendFlavor() {
  const status = await getBackendStatus();
  return status.flavor || 'unknown';
}

/**
 * Health check through router
 * @returns {Promise<Object>} Health status
 */
export async function getBackendHealth() {
  const routerBase = await getRouterBase();
  
  try {
    const networkStart = performance.now();
    const response = await fetch(`${routerBase}/health/`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      cache: 'no-store'
    });
    
    const networkTime = performance.now() - networkStart;
    
    if (response.ok) {
      const data = await response.json();
      return {
        status: data.status || 'ok',
        ping_ms: networkTime,
        details: data
      };
    } else {
      return { status: 'error', ping_ms: networkTime };
    }
  } catch {
    return { status: 'error', ping_ms: null };
  }
}

// ============================================================================
// GAME API METHODS (Updated to use router)
// ============================================================================

export async function getPlayers() {
  return apiRequest('/players', { cache: 'no-store' });
}

export async function getGacha() {
  return apiRequest('/gacha', { cache: 'no-store' });
}

export async function pullGacha(count = 1) {
  return apiRequest('/gacha/pull', {
    method: 'POST',
    body: JSON.stringify({ count })
  });
}

export async function setAutoCraft(enabled) {
  return apiRequest('/gacha/auto-craft', {
    method: 'POST',
    body: JSON.stringify({ enabled })
  });
}

export async function craftItems() {
  return apiRequest('/gacha/craft', {
    method: 'POST'
  });
}

export async function getPlayerConfig() {
  return apiRequest('/player/editor', { cache: 'no-store' });
}

export async function savePlayerConfig(config) {
  return apiRequest('/player/editor', {
    method: 'PUT',
    body: JSON.stringify(config)
  });
}

export async function endRun(runId) {
  return apiRequest(`/run/${runId}`, {
    method: 'DELETE'
  }, (r) => r.ok);
}

export async function endAllRuns() {
  return apiRequest('/runs', {
    method: 'DELETE'
  }, (r) => r.ok);
}

export async function wipeData() {
  return apiRequest('/save/wipe', { method: 'POST' });
}

export async function exportSave() {
  return apiRequest('/save/backup', {
    cache: 'no-store'
  }, (r) => r.blob());
}

export async function importSave(file) {
  return apiRequest('/save/restore', {
    method: 'POST',
    headers: {
      // Remove Content-Type to let browser set boundary for multipart
      'Content-Type': undefined
    },
    body: await file.arrayBuffer()
  });
}

export async function getLrmConfig() {
  return apiRequest('/config/lrm', { cache: 'no-store' });
}

export async function setLrmModel(model) {
  return apiRequest('/config/lrm', {
    method: 'POST',
    body: JSON.stringify({ model })
  });
}

export async function testLrmModel(prompt) {
  return apiRequest('/config/lrm/test', {
    method: 'POST',
    body: JSON.stringify({ prompt })
  });
}

export async function getCardCatalog() {
  const response = await apiRequest('/catalog/cards', { 
    cache: 'no-store', 
    noOverlay: true 
  });
  return response.cards || [];
}

export async function getRelicCatalog() {
  const response = await apiRequest('/catalog/relics', { 
    cache: 'no-store', 
    noOverlay: true 
  });
  return response.relics || [];
}

export async function getUpgrade(id) {
  return apiRequest(`/players/${id}/upgrade`, { cache: 'no-store' });
}

export async function upgradeCharacter(id, starLevel, itemCount = 1) {
  return apiRequest(`/players/${id}/upgrade`, {
    method: 'POST',
    body: JSON.stringify({ star_level: starLevel, item_count: itemCount })
  });
}

export async function upgradeStat(id, points, statName = 'atk') {
  return apiRequest(`/players/${id}/upgrade-stat`, {
    method: 'POST',
    body: JSON.stringify({ points, stat_name: statName })
  });
}

// Export the enhanced API error class for external use
export { ApiError };
```

### Task 4.3: Update Frontend Configuration
**File**: `frontend/.env.example` (Update existing)
```env
# Router Configuration
VITE_ROUTER_BASE=http://localhost:59000

# Development Settings
VITE_DEV_MODE=true
VITE_LOG_LEVEL=info

# Feature Flags
VITE_ENABLE_DEBUG=false
```

**File**: `frontend/vite.config.js` (Update existing)
```javascript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 59001,
    host: '0.0.0.0',
    // Remove proxy configuration since we use router
  },
  build: {
    outDir: 'build',
    emptyOutDir: true,
    sourcemap: true
  },
  define: {
    // Make environment variables available
    __ROUTER_BASE__: JSON.stringify(process.env.VITE_ROUTER_BASE || 'http://localhost:59000')
  }
});
```

### Task 4.4: Update Components to Use New API Client
**File**: `frontend/src/lib/systems/migration_guide.md`
```markdown
# Frontend API Migration Guide

## Import Changes

### Before:
```javascript
import { getBackendFlavor, getPlayers } from './api.js';
import { getApiBase } from './backendDiscovery.js';
```

### After:
```javascript
import { getBackendFlavor, getPlayers } from './apiClient.js';
import { getRouterBase } from './routerClient.js';
```

## Usage Changes

### Before:
```javascript
// Complex backend discovery
const apiBase = await getApiBase();
const response = await fetch(`${apiBase}/players`);
```

### After:
```javascript
// Simple router-based API call
const players = await getPlayers();
```

## Error Handling

### Before:
```javascript
try {
  const data = await getPlayers();
} catch (error) {
  // Manual error handling
  console.error('API error:', error);
}
```

### After:
```javascript
try {
  const data = await getPlayers();
  // Automatic error overlay display
} catch (error) {
  // Error overlay already shown automatically
  // Only handle specific business logic here
}
```

## Configuration

### Before:
```javascript
// Environment variable VITE_API_BASE
// Fallback to backend discovery
```

### After:
```javascript
// Environment variable VITE_ROUTER_BASE
// Simple fallback to localhost:59000
```
```

### Task 4.5: Update Svelte Components
**File**: `frontend/src/routes/+layout.svelte` (Update existing)
```svelte
<script>
  // Update imports
  import { getBackendHealth } from '$lib/systems/apiClient.js';
  import { testRouterConnectivity } from '$lib/systems/routerClient.js';
  
  // ... existing code ...
  
  // Update connectivity check
  async function checkConnectivity() {
    try {
      const isRouterConnected = await testRouterConnectivity();
      if (!isRouterConnected) {
        console.warn('Router service not reachable');
        return;
      }
      
      const health = await getBackendHealth();
      console.log('Backend health:', health);
    } catch (error) {
      console.error('Connectivity check failed:', error);
    }
  }
  
  // ... rest of component ...
</script>
```

**File**: `frontend/src/routes/+page.svelte` (Update existing)
```svelte
<script>
  // Update imports to use new API client
  import { getBackendFlavor, getPlayers, getGacha } from '$lib/systems/apiClient.js';
  
  // ... existing code will automatically work with new API client ...
</script>
```

### Task 4.6: Remove Old Files
Create a script to safely remove old files after migration:

**File**: `frontend/cleanup_migration.sh`
```bash
#!/bin/bash
# Cleanup script for frontend migration

echo "🧹 Cleaning up old frontend files..."

# Backup old files before removal
mkdir -p backup/old-api-system
cp src/lib/systems/api.js backup/old-api-system/ 2>/dev/null || echo "api.js not found"
cp src/lib/systems/backendDiscovery.js backup/old-api-system/ 2>/dev/null || echo "backendDiscovery.js not found"

# Remove old files
rm -f src/lib/systems/api.js
rm -f src/lib/systems/backendDiscovery.js

# Update any remaining imports
echo "🔍 Checking for remaining old imports..."
grep -r "from.*api\.js" src/ && echo "❌ Found old api.js imports - manual update needed"
grep -r "from.*backendDiscovery\.js" src/ && echo "❌ Found old backendDiscovery.js imports - manual update needed"

echo "✅ Cleanup complete"
```

### Task 4.7: Frontend Validation Script
**File**: `frontend/validate_frontend_migration.js`
```javascript
#!/usr/bin/env node
/**
 * Validate frontend migration to router-based communication
 */

import { execSync } from 'child_process';
import { existsSync, readFileSync } from 'fs';
import path from 'path';

async function validateFrontend() {
  console.log('🔍 Validating frontend migration...');
  
  // Check required files exist
  console.log('  📁 Checking file structure...');
  const requiredFiles = [
    'src/lib/systems/apiClient.js',
    'src/lib/systems/routerClient.js'
  ];
  
  for (const file of requiredFiles) {
    if (existsSync(file)) {
      console.log(`    ✓ ${file} exists`);
    } else {
      console.log(`    ❌ ${file} missing`);
      return false;
    }
  }
  
  // Check old files are removed
  console.log('  🗑️  Checking old files removed...');
  const oldFiles = [
    'src/lib/systems/api.js',
    'src/lib/systems/backendDiscovery.js'
  ];
  
  for (const file of oldFiles) {
    if (!existsSync(file)) {
      console.log(`    ✓ ${file} removed`);
    } else {
      console.log(`    ⚠️  ${file} still exists - should be removed`);
    }
  }
  
  // Check for old import patterns
  console.log('  🔍 Checking for old import patterns...');
  try {
    const grepResult = execSync(
      "grep -r \"from.*api\\.js\\|from.*backendDiscovery\\.js\" src/ || true", 
      { encoding: 'utf8' }
    );
    
    if (grepResult.trim()) {
      console.log('    ❌ Found old imports:');
      console.log(grepResult);
      return false;
    } else {
      console.log('    ✓ No old import patterns found');
    }
  } catch (error) {
    console.log('    ⚠️  Could not check imports:', error.message);
  }
  
  // Build frontend to check for errors
  console.log('  🔨 Testing frontend build...');
  try {
    execSync('bun run build', { stdio: 'pipe' });
    console.log('    ✓ Frontend builds successfully');
  } catch (error) {
    console.log('    ❌ Frontend build failed');
    console.log(error.stdout?.toString() || error.message);
    return false;
  }
  
  // Test development server start
  console.log('  🚀 Testing development server...');
  try {
    // Start dev server in background and test
    const devProcess = execSync('timeout 10 bun run dev', { stdio: 'pipe' });
    console.log('    ✓ Development server starts successfully');
  } catch (error) {
    // Timeout is expected, check if it's a real error
    if (error.status === 124) { // timeout exit code
      console.log('    ✓ Development server starts successfully');
    } else {
      console.log('    ❌ Development server failed to start');
      console.log(error.stdout?.toString() || error.message);
      return false;
    }
  }
  
  console.log('✅ Frontend migration validation passed!');
  return true;
}

// Run validation
const result = await validateFrontend();
process.exit(result ? 0 : 1);
```

### Task 4.8: Updated Package Configuration
**File**: `frontend/package.json` (Update scripts)
```json
{
  "scripts": {
    "dev": "vite dev --host 0.0.0.0 --port 59001",
    "build": "vite build",
    "preview": "vite preview --host 0.0.0.0 --port 59001",
    "check": "svelte-kit sync && svelte-check --tsconfig ./jsconfig.json",
    "check:watch": "svelte-kit sync && svelte-check --tsconfig ./jsconfig.json --watch",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "validate": "node validate_frontend_migration.js",
    "cleanup": "bash cleanup_migration.sh"
  }
}
```

## Testing Commands

```bash
# Install dependencies
cd frontend
bun install

# Clean up old files
bun run cleanup

# Validate migration
bun run validate

# Test build
bun run build

# Test development server
bun run dev

# Run linting
bun run lint:fix
```

## Completion Criteria

- [ ] Old `api.js` and `backendDiscovery.js` files removed
- [ ] New `apiClient.js` and `routerClient.js` implemented
- [ ] All Svelte components updated to use new API client
- [ ] Frontend builds without errors
- [ ] Development server starts successfully
- [ ] All API calls route through router service
- [ ] Environment configuration simplified
- [ ] Validation script passes all tests

## Notes for Task Master Review

- Simplified communication reduces complexity and debugging overhead
- Standardized error handling improves user experience
- Router-based architecture enables service monitoring and load balancing
- Configuration reduction minimizes deployment complexity
- Automatic retry logic improves reliability

**Next Task**: After completion and review, proceed to `task-05-docker-configuration.md`