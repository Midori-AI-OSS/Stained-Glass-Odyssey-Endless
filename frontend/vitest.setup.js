import { beforeAll } from 'vitest';

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
});
