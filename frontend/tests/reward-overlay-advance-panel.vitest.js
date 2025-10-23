import { afterEach, beforeAll, beforeEach, describe, expect, test } from 'vitest';
import { tick } from 'svelte';
import {
  afterDropsProgression,
  fourPhaseProgression
} from './__fixtures__/rewardProgressionPayloads.js';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.DEV = false;

let cleanup;
let fireEvent;
let render;
let RewardOverlay;
let updateRewardProgression;
let resetRewardProgression;
let rewardPhaseController;

beforeAll(async () => {
  ({ cleanup, fireEvent, render } = await import('@testing-library/svelte'));
  RewardOverlay = (await import('../src/lib/components/RewardOverlay.svelte')).default;
  ({
    updateRewardProgression,
    resetRewardProgression,
    rewardPhaseController
  } = await import('../src/lib/systems/overlayState.js'));
});

beforeEach(() => {
  resetRewardProgression?.();
});

afterEach(() => {
  cleanup?.();
});

const baseProps = Object.freeze({
  cards: [],
  relics: [],
  items: [],
  gold: 0,
  awaitingCard: false,
  awaitingRelic: false,
  awaitingLoot: false,
  awaitingNext: false,
  stagedCards: [],
  stagedRelics: [],
  sfxVolume: 5,
  reducedMotion: true
});

function renderOverlay(overrides = {}) {
  return render(RewardOverlay, { props: { ...baseProps, ...overrides } });
}

async function withMockedTimers(run) {
  const originalNow = Date.now;
  const originalSetInterval = globalThis.setInterval;
  const originalClearInterval = globalThis.clearInterval;

  let currentNow = originalNow();
  const intervals = new Map();
  let nextIntervalId = 1;

  Date.now = () => currentNow;

  globalThis.setInterval = (callback) => {
    const id = nextIntervalId++;
    intervals.set(id, callback);
    return id;
  };

  globalThis.clearInterval = (id) => {
    intervals.delete(id);
  };

  const runIntervals = () => {
    for (const callback of Array.from(intervals.values())) {
      callback();
    }
  };

  const advanceMs = (ms) => {
    currentNow += ms;
    runIntervals();
  };

  try {
    await run({
      advanceMs,
      runIntervals,
      setNow(value) {
        currentNow = value;
        runIntervals();
      }
    });
  } finally {
    Date.now = originalNow;
    globalThis.setInterval = originalSetInterval;
    globalThis.clearInterval = originalClearInterval;
  }
}

describe('reward overlay advance panel', () => {
  test('manual advance dispatches events and advances the controller', async () => {
    updateRewardProgression(fourPhaseProgression());

    const { component, container } = renderOverlay();
    const advances = [];
    component.$on('advance', (event) => advances.push(event.detail));

    const button = container.querySelector('.advance-button');
    expect(button).toBeInstanceOf(HTMLButtonElement);
    if (!(button instanceof HTMLButtonElement)) {
      throw new Error('Advance button missing');
    }

    await fireEvent.click(button);
    await tick();

    const snapshot = rewardPhaseController.getSnapshot();
    expect(snapshot.current).toBe('cards');
    expect(advances.length).toBeGreaterThan(0);
    expect(advances[0]?.reason).toBe('manual');
    expect(advances[0]?.from).toBe('drops');
    expect(advances[0]?.target).toBe('cards');
  });

  test('auto countdown advances after 10 seconds when ready', async () => {
    updateRewardProgression(fourPhaseProgression());

    const { component, container } = renderOverlay();
    const advances = [];
    component.$on('advance', (event) => advances.push(event.detail));

    const status = container.querySelector('.advance-status');
    expect(status?.textContent ?? '').toMatch(/Auto in/);

    await withMockedTimers(async ({ advanceMs }) => {
      advanceMs(10000);
      await tick();
    });

    expect(advances.length).toBeGreaterThan(0);
    expect(advances[0]?.reason).toBe('auto');
    expect(rewardPhaseController.getSnapshot().current).toBe('cards');
  });

  test('countdown pauses when new choices arrive and resumes when cleared', async () => {
    updateRewardProgression(afterDropsProgression());

    const { component, container } = renderOverlay({ cards: [] });
    const readStatus = () => container.querySelector('.advance-status')?.textContent ?? '';

    await tick();
    expect(readStatus()).toMatch(/Auto in/);

    component.$set({ cards: [{ id: 'luminous-surge', name: 'Luminous Surge' }] });
    await tick();
    expect(readStatus()).toMatch(/Advance locked/);

    await withMockedTimers(async ({ advanceMs }) => {
      advanceMs(12000);
      await tick();
    });
    expect(rewardPhaseController.getSnapshot().current).toBe('cards');

    component.$set({ cards: [] });
    await tick();
    expect(readStatus()).toMatch(/Auto in/);

    await withMockedTimers(async ({ advanceMs }) => {
      advanceMs(10000);
      await tick();
    });
    expect(rewardPhaseController.getSnapshot().current).toBe('relics');
  });

  test('focuses advance button when a phase becomes ready', async () => {
    updateRewardProgression(fourPhaseProgression());

    const { container } = renderOverlay();
    await tick();
    await tick();

    const button = container.querySelector('.advance-button');
    expect(button).toBeInstanceOf(HTMLButtonElement);
    if (!(button instanceof HTMLButtonElement)) {
      throw new Error('Advance button missing');
    }
    expect(document.activeElement).toBe(button);
  });

  test('auto advance returns focus to overlay root', async () => {
    updateRewardProgression({
      available: ['drops', 'cards'],
      completed: [],
      current_step: 'drops'
    });

    const { container } = renderOverlay();
    await tick();
    await tick();

    const layout = container.querySelector('.layout');
    const button = container.querySelector('.advance-button');
    expect(layout).toBeInstanceOf(HTMLElement);
    expect(button).toBeInstanceOf(HTMLButtonElement);
    if (!(layout instanceof HTMLElement) || !(button instanceof HTMLButtonElement)) {
      throw new Error('Overlay layout or button missing');
    }
    expect(document.activeElement).toBe(button);

    await withMockedTimers(async ({ advanceMs }) => {
      advanceMs(10000);
      await tick();
    });

    expect(document.activeElement).toBe(layout);
  });

  test('enter key on overlay root triggers keyboard advance', async () => {
    updateRewardProgression({
      available: ['drops', 'cards'],
      completed: [],
      current_step: 'drops'
    });

    const { component, container } = renderOverlay();
    const advances = [];
    component.$on('advance', (event) => advances.push(event.detail));

    await tick();
    const layout = container.querySelector('.layout');
    expect(layout).toBeInstanceOf(HTMLElement);
    if (!(layout instanceof HTMLElement)) {
      throw new Error('Overlay layout missing');
    }

    layout.focus();
    await tick();

    await fireEvent.keyDown(layout, { key: 'Enter', code: 'Enter' });
    await tick();

    expect(advances.at(-1)?.reason).toBe('keyboard');
  });

  test('falls back to legacy overlay when progression diagnostics are present', async () => {
    const originalWarn = console.warn;
    const warnings = [];
    console.warn = (...args) => {
      warnings.push(args);
    };

    try {
      updateRewardProgression({});
      const { container } = renderOverlay({
        cards: [{ id: 'flare', name: 'Flare' }]
      });

      await tick();
      const fallbackNote = container.querySelector('.phase-note.warning');
      expect(fallbackNote?.textContent ?? '').toMatch(/legacy overlay/i);
      expect(container.querySelector('.advance-panel')).toBeNull();
      expect(warnings.length).toBeGreaterThan(0);
    } finally {
      console.warn = originalWarn;
    }
  });
});
