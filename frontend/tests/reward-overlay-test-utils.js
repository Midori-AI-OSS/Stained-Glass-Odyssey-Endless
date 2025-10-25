import { tick } from 'svelte';

export async function flushOverlayTicks(count = 2) {
  for (let index = 0; index < count; index += 1) {
    await tick();
  }
}

export function getCardButton(container, name) {
  if (!container) return null;
  return container.querySelector(`button[aria-label="Select card ${name}"]`);
}

export function getRelicButton(container, name) {
  if (!container) return null;
  return container.querySelector(`button[aria-label="Select relic ${name}"]`);
}

export function trackSelectEvents(component) {
  const events = [];
  component?.$on?.('select', (event) => {
    events.push(event.detail);
  });
  return events;
}

export function buildStagedCard(id, name, overrides = {}) {
  return {
    id,
    name,
    preview: { summary: `${name} staged` },
    ...overrides
  };
}

export function buildStagedRelic(id, name, overrides = {}) {
  return {
    id,
    name,
    preview: { summary: `${name} staged` },
    ...overrides
  };
}

export function createRewardRoom(overrides = {}) {
  return {
    card_choices: [],
    relic_choices: [],
    reward_staging: { cards: [], relics: [], items: [] },
    loot: { gold: 0, items: [] },
    awaiting_card: false,
    awaiting_relic: false,
    awaiting_loot: false,
    awaiting_next: false,
    reward_progression: null,
    result: 'battle',
    battle_index: 1,
    ...overrides
  };
}

export async function withMockedAdvanceTimers(run) {
  const originalNow = Date.now;
  const originalSetInterval = globalThis.setInterval;
  const originalClearInterval = globalThis.clearInterval;

  let currentNow = originalNow();
  const intervals = new Map();
  let nextId = 1;

  Date.now = () => currentNow;
  globalThis.setInterval = (callback, interval) => {
    const id = nextId++;
    intervals.set(id, { callback, interval });
    return id;
  };
  globalThis.clearInterval = (id) => {
    intervals.delete(id);
  };

  const runIntervals = () => {
    for (const { callback } of intervals.values()) {
      try {
        callback();
      } catch (error) {
        // Surface timer errors to the test harness for easier debugging
        setTimeout(() => {
          throw error;
        });
      }
    }
  };

  const advanceMs = (ms) => {
    currentNow += ms;
    runIntervals();
  };

  try {
    await run({ advanceMs, runIntervals, setNow(value) { currentNow = value; runIntervals(); } });
  } finally {
    Date.now = originalNow;
    globalThis.setInterval = originalSetInterval;
    globalThis.clearInterval = originalClearInterval;
  }
}
