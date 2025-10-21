import { afterEach, beforeAll, beforeEach, describe, expect, test, vi } from 'vitest';
import { tick } from 'svelte';
import { afterDropsProgression, fourPhaseProgression } from './__fixtures__/rewardProgressionPayloads.js';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.DEV = false;

let cleanup;
let render;
let fireEvent;
let RewardOverlay;
let updateRewardProgression;
let resetRewardProgression;

beforeAll(async () => {
  ({ cleanup, render, fireEvent } = await import('@testing-library/svelte'));
  RewardOverlay = (await import('../src/lib/components/RewardOverlay.svelte')).default;
  ({ updateRewardProgression, resetRewardProgression } = await import('../src/lib/systems/overlayState.js'));
});

beforeEach(() => {
  resetRewardProgression?.();
});

afterEach(() => {
  cleanup();
});

describe('RewardOverlay card phase interactions', () => {
  test('auto-selects the first card when entering the card phase', async () => {
    updateRewardProgression(afterDropsProgression());

    const selectEvents = [];
    const { component, container } = render(RewardOverlay, {
      props: {
        cards: [
          {
            id: 'first-card',
            name: 'First Card',
            stars: 3
          },
          {
            id: 'second-card',
            name: 'Second Card',
            stars: 2
          }
        ],
        relics: [],
        items: [],
        gold: 0,
        awaitingLoot: false,
        awaitingCard: false,
        awaitingRelic: false,
        awaitingNext: false,
        reducedMotion: true
      }
    });

    component.$on('select', (event) => selectEvents.push(event.detail));

    await tick();
    await tick();

    expect(selectEvents.some((detail) => detail?.type === 'card' && detail?.id === 'first-card')).toBe(true);
    const highlighted = container.querySelector('.card-shell.selected');
    expect(highlighted).not.toBeNull();
    expect(
      highlighted?.querySelector('button[aria-label="Select card First Card"]')
    ).not.toBeNull();
  });

  test('renders staged card without confirm controls', async () => {
    updateRewardProgression(fourPhaseProgression({ current_step: 'cards', completed: ['drops'] }));

    const stagedCard = {
      id: 'radiant-beam',
      name: 'Radiant Beam',
      stars: 4
    };

    const { container } = render(RewardOverlay, {
      props: {
        cards: [stagedCard],
        stagedCards: [stagedCard],
        awaitingCard: true,
        relics: [],
        items: [],
        awaitingLoot: false,
        awaitingRelic: false,
        awaitingNext: false,
        reducedMotion: false
      }
    });

    await tick();

    expect(container.querySelector('.card-shell.confirmable')).toBeNull();
    const confirmButton = container.querySelector('button.card-confirm');
    expect(confirmButton).toBeNull();
    const stagedShell = container.querySelector('.card-shell.selected');
    expect(stagedShell).not.toBeNull();
    expect(stagedShell?.dataset.reducedMotion).toBe('false');
  });

  test('re-dispatches select when clicking the staged card again', async () => {
    updateRewardProgression(fourPhaseProgression({ current_step: 'cards', completed: ['drops'] }));

    const stagedCard = {
      id: 'echo-strike',
      name: 'Echo Strike',
      stars: 5
    };

    const selectHandler = vi.fn();

    const { component, getByLabelText } = render(RewardOverlay, {
      props: {
        cards: [stagedCard],
        stagedCards: [stagedCard],
        awaitingCard: true,
        relics: [],
        items: [],
        awaitingLoot: false,
        awaitingRelic: false,
        awaitingNext: false,
        reducedMotion: true
      }
    });

    component.$on('select', (event) => {
      if (event.detail?.type === 'card') {
        selectHandler(event.detail);
      }
    });

    const cardButton = getByLabelText('Select card Echo Strike');
    await fireEvent.click(cardButton);
    await tick();

    expect(selectHandler).toHaveBeenCalledTimes(1);
    expect(selectHandler.mock.calls[0][0]?.id).toBe('echo-strike');
  });

  test('applies selected styling in the no-confirmation card flow', async () => {
    updateRewardProgression(afterDropsProgression());

    const { container } = render(RewardOverlay, {
      props: {
        cards: [
          {
            id: 'first-card',
            name: 'First Card',
            stars: 3
          },
          {
            id: 'second-card',
            name: 'Second Card',
            stars: 2
          }
        ],
        relics: [],
        items: [],
        gold: 0,
        awaitingLoot: false,
        awaitingCard: false,
        awaitingRelic: false,
        awaitingNext: false,
        reducedMotion: false
      }
    });

    const secondCardButton = container.querySelector(
      'button[aria-label="Select card Second Card"]'
    );
    expect(secondCardButton).not.toBeNull();
    if (!secondCardButton) return;

    await fireEvent.click(secondCardButton);
    await tick();

    const shell = secondCardButton.closest('.card-shell');
    expect(shell).not.toBeNull();
    expect(shell?.classList.contains('selected')).toBe(true);
    expect(shell?.classList.contains('confirmable')).toBe(false);
    expect(shell?.dataset.reducedMotion).toBe('false');
  });
});
