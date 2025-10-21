import { afterEach, beforeAll, beforeEach, describe, expect, test, vi } from 'vitest';
import { tick } from 'svelte';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.DEV = false;

let cleanup;
let render;
let fireEvent;
let RewardOverlay;
let updateRewardProgression;
let resetRewardProgression;
let advanceRewardPhase;
let rewardPhaseController;

beforeAll(async () => {
  ({ cleanup, fireEvent, render } = await import('@testing-library/svelte'));
  RewardOverlay = (await import('../src/lib/components/RewardOverlay.svelte')).default;
  ({
    updateRewardProgression,
    resetRewardProgression,
    advanceRewardPhase,
    rewardPhaseController
  } = await import('../src/lib/systems/overlayState.js'));
});

beforeEach(() => {
  resetRewardProgression?.();
});

afterEach(() => {
  cleanup();
});

function seedDropsToCardsProgression() {
  updateRewardProgression({
    available: ['drops', 'cards'],
    completed: [],
    current_step: 'drops'
  });
}

describe('RewardOverlay loot acknowledgement flow', () => {
  test('advances from drops to cards after acknowledging loot exactly once', async () => {
    seedDropsToCardsProgression();

    const { component, container, getByRole } = render(RewardOverlay, {
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
        awaitingNext: false,
        sfxVolume: 5,
        reducedMotion: true
      }
    });

    await tick();

    expect(rewardPhaseController.getSnapshot().current).toBe('drops');
    expect(container.querySelector('.drops-row')).not.toBeNull();

    const acknowledgementCalls = [];
    const ackHandler = vi.fn(async () => {
      acknowledgementCalls.push(rewardPhaseController.getSnapshot().current);
      advanceRewardPhase();
      await tick();
      updateRewardProgression({
        available: ['drops', 'cards'],
        completed: ['drops'],
        current_step: 'cards'
      });
      await tick();
      acknowledgementCalls.push(rewardPhaseController.getSnapshot().current);
    });

    component.$on('lootAcknowledge', ackHandler);

    const nextButton = getByRole('button', { name: 'Next Room' });

    await fireEvent.click(nextButton);
    await tick();

    const snapshot = rewardPhaseController.getSnapshot();
    expect(snapshot.current).toBe('cards');
    expect(snapshot.completed).toContain('drops');
    expect(container.querySelector('.drops-row')).toBeNull();

    expect(ackHandler).toHaveBeenCalledTimes(1);
    expect(acknowledgementCalls).toEqual(['drops', 'cards']);

    if (nextButton.isConnected) {
      await fireEvent.click(nextButton);
    }

    expect(ackHandler).toHaveBeenCalledTimes(1);
    expect(nextButton.isConnected).toBe(false);
  });
});
