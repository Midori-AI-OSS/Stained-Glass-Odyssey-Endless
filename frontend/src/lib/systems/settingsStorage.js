const SETTINGS_KEY = 'autofighter_settings';

export function loadSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return {};
    const data = JSON.parse(raw);
    if (data.framerate !== undefined) data.framerate = Number(data.framerate);
    if (data.reducedMotion !== undefined) data.reducedMotion = Boolean(data.reducedMotion);
    if (data.lrmModel !== undefined) data.lrmModel = String(data.lrmModel);
    if (data.showActionValues !== undefined) data.showActionValues = Boolean(data.showActionValues);
    if (data.fullIdleMode !== undefined) data.fullIdleMode = Boolean(data.fullIdleMode);
    return data;
  } catch {
    return {};
  }
}

export function saveSettings(settings) {
  try {
    const current = loadSettings();
    const merged = { ...current, ...settings };
    if (merged.fullIdleMode !== undefined) merged.fullIdleMode = Boolean(merged.fullIdleMode);
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(merged));
  } catch {
    // ignore write errors
  }
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
