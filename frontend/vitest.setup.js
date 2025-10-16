import { beforeAll } from 'vitest';
import 'svelte/internal/flags/legacy.js';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;

beforeAll(() => {
  globalThis.$app = {
    environment: {
      browser: false,
      dev: false,
      building: false,
      version: {}
    }
  };

  globalThis.$stores = {
    page: { subscribe: () => () => {} },
    navigating: { subscribe: () => () => {} },
    updated: { subscribe: () => () => {} }
  };

  if (typeof globalThis.fetch !== 'function') {
    globalThis.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  }

  if (typeof globalThis.requestAnimationFrame !== 'function') {
    globalThis.requestAnimationFrame = (callback) => setTimeout(callback, 0);
  }

  if (typeof globalThis.cancelAnimationFrame !== 'function') {
    globalThis.cancelAnimationFrame = (handle) => clearTimeout(handle);
  }
});
