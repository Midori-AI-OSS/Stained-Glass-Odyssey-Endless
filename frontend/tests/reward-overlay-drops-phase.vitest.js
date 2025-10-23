import { afterEach, beforeAll, beforeEach, describe, expect, test } from 'vitest';
import { tick } from 'svelte';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.DEV = false;

let cleanup;
let render;
let RewardOverlay;
let updateRewardProgression;
let resetRewardProgression;
let rewardPhaseController;
let rewardTelemetryEventName;

beforeAll(async () => {
  ({ cleanup, render } = await import('@testing-library/svelte'));
  RewardOverlay = (await import('../src/lib/components/RewardOverlay.svelte')).default;
  ({
    updateRewardProgression,
    resetRewardProgression,
    rewardPhaseController
  } = await import('../src/lib/systems/overlayState.js'));
  ({ rewardTelemetryEventName } = await import('../src/lib/systems/rewardTelemetry.js'));
});

beforeEach(() => {
  resetRewardProgression?.();
});

afterEach(() => {
  cleanup();
});

describe('RewardOverlay drops phase flow', () => {
  test('hides later phase controls until drops complete and emits telemetry', async () => {
    updateRewardProgression({
      available: ['drops', 'cards'],
      completed: [],
      current_step: 'drops'
    });

    const { container } = render(RewardOverlay, {
      props: {
        cards: [
          {
            id: 'radiant-beam',
            name: 'Radiant Beam',
            stars: 4
          }
        ],
        relics: [],
        items: [
          {
            id: 'upgrade-core',
            name: 'Upgrade Core',
            stars: 3,
            count: 2
          }
        ],
        gold: 45,
        awaitingLoot: false,
        awaitingNext: true,
        sfxVolume: 5,
        reducedMotion: true
      }
    });

    await tick();

    expect(container.querySelector('.drops-row')).not.toBeNull();
    expect(container.querySelector('button[aria-label^="Select card"]')).toBeNull();

    const telemetryEvents = [];
    const listener = (event) => telemetryEvents.push(event?.detail);
    window.addEventListener(rewardTelemetryEventName, listener);

    rewardPhaseController.advance();
    await tick();

    expect(container.querySelector('.drops-row')).toBeNull();
    expect(container.querySelector('button[aria-label^="Select card"]')).not.toBeNull();
    expect(telemetryEvents.some((payload) => payload?.kind === 'drops-complete')).toBe(true);

    window.removeEventListener(rewardTelemetryEventName, listener);
  });
});
