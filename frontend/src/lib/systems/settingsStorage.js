import { writable } from 'svelte/store';

const SETTINGS_KEY = 'autofighter_settings';
const SETTINGS_VERSION = 2;

// Create reactive stores for settings
export const motionStore = writable(null);
export const themeStore = writable(null);

// Theme definitions
export const THEMES = {
  default: {
    name: 'Default',
    accent: 'level-based', // special value to use level-based hue
    background: 'rotating'
  },
  solaris: {
    name: 'Solaris',
    accent: '#ffb347', // warm orange
    background: 'static'
  },
  nocturne: {
    name: 'Nocturne', 
    accent: '#9370db', // purple
    background: 'static'
  },
  custom: {
    name: 'Custom',
    accent: '#8ac',
    background: 'static'
  }
};

// Default settings structure
function getDefaultSettings() {
  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
  return {
    version: SETTINGS_VERSION,
    theme: {
      selected: 'default',
      customAccent: '#8ac',
      backgroundBehavior: 'rotating', // 'rotating', 'static', 'custom'
      customBackground: null
    },
    motion: {
      globalReducedMotion: prefersReducedMotion,
      disableFloatingDamage: false,
      disablePortraitGlows: false,
      simplifyOverlayTransitions: false,
      disableStarStorm: false
    },
    // Legacy settings for backward compatibility
    framerate: 60,
    reducedMotion: prefersReducedMotion,
    lrmModel: '',
    showActionValues: false,
    showTurnCounter: true,
    flashEnrageCounter: true,
    fullIdleMode: false,
    skipBattleReview: false,
    animationSpeed: 1.0
  };
}

// Migration logic
function migrateSettings(data) {
  if (!data.version || data.version < SETTINGS_VERSION) {
    console.log('Migrating settings from version', data.version || 1, 'to', SETTINGS_VERSION);
    
    // Migrate from v1 to v2: convert flat reducedMotion to hierarchical motion settings
    if (data.version !== SETTINGS_VERSION) {
      const defaults = getDefaultSettings();
      
      // Preserve existing settings
      const migrated = {
        ...defaults,
        ...data,
        version: SETTINGS_VERSION
      };
      
      // If we had an old reducedMotion setting, migrate it to the new structure
      if (data.reducedMotion !== undefined) {
        migrated.motion = {
          ...defaults.motion,
          globalReducedMotion: Boolean(data.reducedMotion),
          // When old reducedMotion was enabled, enable most motion reduction options
          disableFloatingDamage: Boolean(data.reducedMotion),
          disablePortraitGlows: Boolean(data.reducedMotion),
          simplifyOverlayTransitions: Boolean(data.reducedMotion),
          disableStarStorm: Boolean(data.reducedMotion)
        };
      }
      
      // Initialize theme settings if not present
      if (!data.theme) {
        migrated.theme = defaults.theme;
      }
      
      return migrated;
    }
  }
  
  return data;
}

export function loadSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) {
      const defaults = getDefaultSettings();
      // Initialize stores
      motionStore.set(defaults.motion);
      themeStore.set(defaults.theme);
      return defaults;
    }
    
    let data = JSON.parse(raw);
    
    // Apply migration
    data = migrateSettings(data);
    
    // Type coercion for legacy numeric/boolean fields
    if (data.framerate !== undefined) data.framerate = Number(data.framerate);
    if (data.reducedMotion !== undefined) data.reducedMotion = Boolean(data.reducedMotion);
    if (data.lrmModel !== undefined) data.lrmModel = String(data.lrmModel);
    if (data.showActionValues !== undefined) data.showActionValues = Boolean(data.showActionValues);
    if (data.showTurnCounter !== undefined) data.showTurnCounter = Boolean(data.showTurnCounter);
    if (data.flashEnrageCounter !== undefined) data.flashEnrageCounter = Boolean(data.flashEnrageCounter);
    if (data.fullIdleMode !== undefined) data.fullIdleMode = Boolean(data.fullIdleMode);
    if (data.skipBattleReview !== undefined) data.skipBattleReview = Boolean(data.skipBattleReview);
    if (data.animationSpeed !== undefined) {
      const numeric = Number(data.animationSpeed);
      if (Number.isFinite(numeric) && numeric > 0) {
        const clamped = Math.min(2, Math.max(0.1, numeric));
        data.animationSpeed = Math.round(clamped * 10) / 10;
      } else {
        delete data.animationSpeed;
      }
    }
    
    // Ensure motion settings exist
    const defaults = getDefaultSettings();

    if (!data.motion) {
      data.motion = defaults.motion;
    }

    // Ensure theme settings exist
    if (!data.theme) {
      data.theme = defaults.theme;
    }

    if (data.showTurnCounter === undefined) {
      data.showTurnCounter = defaults.showTurnCounter;
    }

    if (data.flashEnrageCounter === undefined) {
      data.flashEnrageCounter = defaults.flashEnrageCounter;
    }
    
    // Update stores
    motionStore.set(data.motion);
    themeStore.set(data.theme);
    
    return data;
  } catch {
    const defaults = getDefaultSettings();
    motionStore.set(defaults.motion);
    themeStore.set(defaults.theme);
    return defaults;
  }
}

export function saveSettings(settings) {
  try {
    const current = loadSettings();
    const merged = { ...current, ...settings };
    
    // Ensure version is set
    merged.version = SETTINGS_VERSION;
    
    // Legacy field validation
    if (merged.fullIdleMode !== undefined) merged.fullIdleMode = Boolean(merged.fullIdleMode);
    if (merged.showTurnCounter !== undefined) merged.showTurnCounter = Boolean(merged.showTurnCounter);
    if (merged.flashEnrageCounter !== undefined) merged.flashEnrageCounter = Boolean(merged.flashEnrageCounter);
    if (merged.skipBattleReview !== undefined) merged.skipBattleReview = Boolean(merged.skipBattleReview);
    if (merged.animationSpeed !== undefined) {
      const numeric = Number(merged.animationSpeed);
      if (Number.isFinite(numeric) && numeric > 0) {
        const clamped = Math.min(2, Math.max(0.1, numeric));
        merged.animationSpeed = Math.round(clamped * 10) / 10;
      } else {
        delete merged.animationSpeed;
      }
    }
    
    // Validate theme settings
    if (merged.theme) {
      if (merged.theme.selected && !THEMES[merged.theme.selected]) {
        merged.theme.selected = 'default';
      }
      if (merged.theme.backgroundBehavior && 
          !['rotating', 'static', 'custom'].includes(merged.theme.backgroundBehavior)) {
        merged.theme.backgroundBehavior = 'rotating';
      }
    }
    
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(merged));
    
    // Update stores when settings change
    if (merged.motion) {
      motionStore.set(merged.motion);
    }
    if (merged.theme) {
      themeStore.set(merged.theme);
    }
  } catch {
    // ignore write errors
  }
}

// Helper functions for accessing nested settings
export function getThemeSettings() {
  const settings = loadSettings();
  return settings.theme || getDefaultSettings().theme;
}

export function getMotionSettings() {
  const settings = loadSettings();
  return settings.motion || getDefaultSettings().motion;
}

export function updateThemeSettings(themeUpdates) {
  const current = loadSettings();
  const updatedTheme = { ...current.theme, ...themeUpdates };
  saveSettings({
    theme: updatedTheme
  });
  themeStore.set(updatedTheme);
}

export function updateMotionSettings(motionUpdates) {
  const current = loadSettings();
  const updatedMotion = { ...current.motion, ...motionUpdates };
  saveSettings({
    motion: updatedMotion,
    // Keep legacy reducedMotion in sync
    reducedMotion: updatedMotion.globalReducedMotion
  });
  motionStore.set(updatedMotion);
}

export function clearSettings() {
  try {
    localStorage.removeItem(SETTINGS_KEY);
  } catch {
    // ignore clear errors
  }
}

// Best‑effort client wipe: local/session storage, caches, SW, and IndexedDB
export async function clearAllClientData() {
  // Local + session storage
  try { localStorage.clear(); } catch { /* ignore */ }
  try { sessionStorage && sessionStorage.clear && sessionStorage.clear(); } catch { /* ignore */ }

  // CacheStorage
  try {
    if (typeof caches !== 'undefined' && caches?.keys) {
      const names = await caches.keys();
      await Promise.all(names.map((n) => caches.delete(n)));
    }
  } catch { /* ignore */ }

  // Service workers
  try {
    if (typeof navigator !== 'undefined' && navigator.serviceWorker?.getRegistrations) {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map((r) => r.unregister()));
    }
  } catch { /* ignore */ }

  // IndexedDB (supported in Chromium via indexedDB.databases())
  try {
    if (typeof indexedDB !== 'undefined' && indexedDB?.databases) {
      const dbs = await indexedDB.databases();
      await Promise.all(
        (dbs || [])
          .map((db) => db?.name)
          .filter(Boolean)
          .map(
            (name) =>
              new Promise((resolve) => {
                const req = indexedDB.deleteDatabase(name);
                req.onsuccess = req.onerror = req.onblocked = () => resolve();
              })
          )
      );
    }
  } catch { /* ignore */ }
}
