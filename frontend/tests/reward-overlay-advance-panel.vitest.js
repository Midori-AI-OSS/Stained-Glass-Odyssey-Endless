import { afterEach, beforeAll, beforeEach, describe, expect, test, vi } from 'vitest';
import { tick } from 'svelte';

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
  vi.useRealTimers();
  resetRewardProgression?.();
});

afterEach(() => {
  cleanup?.();
  vi.useRealTimers();
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

describe('reward overlay advance panel', () => {
  test('manual advance dispatches events and advances the controller', async () => {
    updateRewardProgression({
      available: ['drops', 'cards'],
      completed: [],
      current_step: 'drops'
    });

    const { component, container } = renderOverlay();
    const advances = [];
    component.$on('advance', (event) => advances.push(event.detail));

    const button = container.querySelector('.advance-button');
    expect(button).not.toBeNull();
    if (!button) return;

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
    vi.useFakeTimers();
    updateRewardProgression({
      available: ['drops', 'cards'],
      completed: [],
      current_step: 'drops'
    });

    const { component, container } = renderOverlay();
    const advances = [];
    component.$on('advance', (event) => advances.push(event.detail));

    const status = container.querySelector('.advance-status');
    expect(status?.textContent ?? '').toMatch(/Auto in/);

    vi.advanceTimersByTime(10000);
    await tick();

    expect(advances.length).toBeGreaterThan(0);
    expect(advances[0]?.reason).toBe('auto');
    expect(rewardPhaseController.getSnapshot().current).toBe('cards');
    vi.useRealTimers();
  });

  test('countdown pauses when new choices arrive and resumes when cleared', async () => {
    vi.useFakeTimers();
    updateRewardProgression({
      available: ['drops', 'cards', 'relics'],
      completed: ['drops'],
      current_step: 'cards'
    });

    const { component, container } = renderOverlay({ cards: [] });
    const readStatus = () => container.querySelector('.advance-status')?.textContent ?? '';

    await tick();
    expect(readStatus()).toMatch(/Auto in/);

    component.$set({ cards: [{ id: 'luminous-surge', name: 'Luminous Surge' }] });
    await tick();
    expect(readStatus()).toMatch(/Complete this step/);

    vi.advanceTimersByTime(12000);
    await tick();
    expect(rewardPhaseController.getSnapshot().current).toBe('cards');

    component.$set({ cards: [] });
    await tick();
    expect(readStatus()).toMatch(/Auto in/);

    vi.advanceTimersByTime(10000);
    await tick();
    expect(rewardPhaseController.getSnapshot().current).toBe('relics');
    vi.useRealTimers();
  });
});
