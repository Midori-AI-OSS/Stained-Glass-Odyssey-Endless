// Handle test environment where $app/environment is not available
let browserPromise = null;
let browserValue = null;

async function getBrowser() {
  if (browserValue !== null) {
    return browserValue;
  }
  
  if (!browserPromise) {
    browserPromise = (async () => {
      try {
        const appEnv = await import('$app/environment');
        browserValue = appEnv.browser;
      } catch {
        // In test environment, assume we're not in a browser
        browserValue = false;
      }
      return browserValue;
    })();
  }
  
  return browserPromise;
}

let cached = null;

export async function getApiBase() {
  if (cached) {
    return cached;
  }

  const envBase = import.meta.env && import.meta.env.VITE_API_BASE;
  if (envBase) {
    cached = envBase;
    return cached;
  }

  const browser = await getBrowser();
  if (browser) {
    // Keep checking until the dev server exposes /api-base
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    let attempt = 0;
     
    while (true) {
      try {
        const res = await fetch('/api-base', { cache: 'no-store' });
        if (res.ok) {
          cached = await res.text();
          return cached;
        }
      } catch {}

      attempt += 1;
      const waitMs = Math.min(2000, 500 + attempt * 250);
      await sleep(waitMs);
    }
  }

  cached = 'http://localhost:59002';
  return cached;
}

export function resetDiscovery() {
  cached = null;
}

export function getCachedApiBase() {
  return cached;
}
