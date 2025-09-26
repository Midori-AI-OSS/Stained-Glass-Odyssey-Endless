<script>
  import { onMount, onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  import { browser } from '$app/environment';
  import { getApiBase } from '$lib/systems/backendDiscovery.js';
  import { battleActive } from '../systems/overlayState.js';

  let pingStatus = 'unknown'; // 'healthy', 'degraded', 'error', 'unknown'
  let pingTime = null;
  let isInCombat = false;
  let interval;
  let lastUpdateTime = 0;
  let pos = { top: '1.2rem', left: '1.2rem' };
  let apiBase = null;

  // Check if we're in combat by looking for battle-related elements or state
  function checkCombatState() {
    // Prefer the shared battleActive store, fall back to DOM hints when needed
    isInCombat = get(battleActive);

    if (typeof window !== 'undefined') {
      
      // Also check for battle-related DOM elements as fallback
      const battleElements = document.querySelectorAll('[data-battle-active], .battle-view, .battle-snapshot');
      if (battleElements.length > 0) {
        isInCombat = true;
      }
    }
  }

  async function checkBackendHealth() {
    if (!browser) return;
    
    try {
      // Get the current API base (will auto-discover if needed)
      if (!apiBase) {
        apiBase = await getApiBase();
      }
      
      const startTime = performance.now();
      // Use the discovered backend base
      const response = await fetch(`${apiBase}/performance/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });
      
      const endTime = performance.now();
      const networkPingTime = endTime - startTime;
      
      if (response.ok) {
        let data = null;
        try { data = await response.json(); } catch {}
        const status = (data && (data.status || (data.health && data.health.status))) || 'ok';
        pingStatus = status === 'ok' ? 'healthy' : (status === 'degraded' ? 'degraded' : 'error');
        // Use backend-reported ping if available, otherwise use network round-trip
        pingTime = (data && data.ping_ms) || networkPingTime;
        lastUpdateTime = Date.now();
      } else {
        pingStatus = 'error';
        pingTime = networkPingTime;
      }
    } catch (error) {
      pingStatus = 'error';
      pingTime = null;
      console.warn('Health check failed:', error.message);
    }
  }

  function getIndicatorSymbol() {
    checkCombatState();
    
    if (isInCombat) {
      // In combat: show ping time if available
      if (pingTime !== null) {
        return `${Math.round(pingTime)}ms`;
      }
      return '●'; // Solid dot when in combat but no ping data
    } else {
      // Out of combat: show +/- based on health
      return pingStatus === 'healthy' ? '+' : '-';
    }
  }

  function getIndicatorColor() {
    if (pingStatus === 'healthy') {
      return isInCombat ? '#00ff88' : '#00ff88'; // Green for healthy
    } else if (pingStatus === 'degraded') {
      return '#ffaa00'; // Orange for degraded
    } else if (pingStatus === 'error') {
      return '#ff4444'; // Red for error
    } else {
      return '#888888'; // Gray for unknown
    }
  }

  function getTooltipText() {
    checkCombatState();
    
    const baseStatus = pingStatus === 'healthy' ? 'Backend Healthy' :
                      pingStatus === 'degraded' ? 'Backend Degraded' :
                      pingStatus === 'error' ? 'Backend Error' : 'Backend Status Unknown';
    
    if (isInCombat && pingTime !== null) {
      return `${baseStatus}\nCombat Sync: ${Math.round(pingTime)}ms`;
    } else if (isInCombat) {
      return `${baseStatus}\nIn Combat`;
    } else {
      return baseStatus;
    }
  }

  onMount(() => {
    if (browser) {
      const updatePosition = () => {
        try {
          const nav = document.querySelector('.nav-wrapper .stained-glass-bar');
          if (nav) {
            const rect = nav.getBoundingClientRect();
            pos = {
              top: `${Math.max(12, Math.round(rect.top))}px`,
              left: `${Math.round(rect.right + 12)}px`,
            };
          } else {
            pos = { top: '1.2rem', left: '1.2rem' };
          }
        } catch {
          pos = { top: '1.2rem', left: '1.2rem' };
        }
      };

      // Initial placement next to top-left NavBar
      updatePosition();
      window.addEventListener('resize', updatePosition);

      // Initial check
      checkBackendHealth();
      
      // Set up periodic health checks every 2 seconds
      interval = setInterval(() => {
        checkBackendHealth();
      }, 2000);

      // Listen for battle state changes
      const handleBattleStateChange = () => {
        checkCombatState();
      };

      // Set up mutation observer to detect battle state changes
      const observer = new MutationObserver((...args) => {
        handleBattleStateChange(...args);
        updatePosition();
      });
      observer.observe(document.body, {
        attributes: true,
        attributeFilter: ['data-battle-active'],
        subtree: true
      });

      return () => {
        observer.disconnect();
        window.removeEventListener('resize', updatePosition);
      };
    }
  });

  onDestroy(() => {
    if (interval) {
      clearInterval(interval);
    }
  });

  // Check if the indicator is stale (no updates for >10 seconds)
  $: isStale = lastUpdateTime > 0 && (Date.now() - lastUpdateTime) > 10000;
</script>

<style>
  .ping-indicator {
    position: fixed;
    /* Positioned dynamically next to top-left NavBar */
    z-index: 10000;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    font-weight: bold;
    padding: 6px 10px;
    background: rgba(0, 0, 0, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    backdrop-filter: blur(4px);
    user-select: none;
    cursor: help;
    transition: all 0.2s ease;
    min-width: 24px;
    text-align: center;
  }

  .ping-indicator:hover {
    background: rgba(0, 0, 0, 0.95);
    border-color: rgba(255, 255, 255, 0.4);
    transform: scale(1.05);
  }

  .ping-indicator.stale {
    opacity: 0.5;
    animation: pulse 2s infinite;
  }

  .ping-indicator.combat {
    border-color: rgba(255, 255, 255, 0.6);
    box-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 0.8; }
  }
</style>

<div 
  class="ping-indicator" 
  class:stale={isStale}
  class:combat={isInCombat}
  style="color: {getIndicatorColor()}; top: {pos.top}; left: {pos.left}"
  title={getTooltipText()}
>
  {getIndicatorSymbol()}
</div>
