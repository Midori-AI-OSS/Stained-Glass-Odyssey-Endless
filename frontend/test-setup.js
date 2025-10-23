// Test setup for bun test
// Mock SvelteKit modules that aren't available in test environment

import { beforeAll } from 'bun:test';
import { JSDOM } from 'jsdom';
import { state as svelteState } from 'svelte/internal/client';
import 'svelte/internal/flags/legacy';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.$state = svelteState;

beforeAll(() => {
  const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://localhost' });
  global.window = dom.window;
  global.document = dom.window.document;
  global.navigator = dom.window.navigator;
  global.HTMLElement = dom.window.HTMLElement;
  global.CustomEvent = dom.window.CustomEvent;
  global.requestAnimationFrame =
    dom.window.requestAnimationFrame || ((callback) => setTimeout(callback, 0));
  global.cancelAnimationFrame =
    dom.window.cancelAnimationFrame || ((handle) => clearTimeout(handle));

  process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
  global.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
  global.$state = svelteState;

  // Mock $app/environment
  global.$app = {
    environment: {
      browser: false,
      dev: false,
      building: false,
      version: {}
    }
  };

  // Mock $app/stores  
  global.$stores = {
    page: {
      subscribe: () => () => {}
    },
    navigating: {
      subscribe: () => () => {}
    },
    updated: {
      subscribe: () => () => {}
    }
  };

  // Mock $lib modules that might be problematic
  global.fetch = global.fetch || (() => Promise.resolve({ ok: true, json: () => Promise.resolve({}) }));
});