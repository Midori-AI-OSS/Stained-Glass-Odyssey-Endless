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

    expect(
      selectEvents.some(
        (detail) => detail?.type === 'card' && detail?.id === 'first-card' && detail?.intent === 'select'
      )
    ).toBe(true);
    const highlighted = container.querySelector('.card-shell.selected');
    expect(highlighted).not.toBeNull();
    expect(
      highlighted?.querySelector('button[aria-label="Select card First Card"]')
    ).not.toBeNull();
  });

  test('keeps staged card in the main grid while awaiting confirmation', async () => {
    updateRewardProgression(fourPhaseProgression({ current_step: 'cards', completed: ['drops'] }));

    const stagedCard = {
      id: 'radiant-beam',
      name: 'Radiant Beam',
      stars: 4
    };

    const { container, getByLabelText } = render(RewardOverlay, {
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

    expect(container.querySelector('.staged-block')).toBeNull();
    const cardButton = getByLabelText('Select card Radiant Beam');
    expect(cardButton).not.toBeNull();
    if (!cardButton) return;

    await fireEvent.click(cardButton);
    await tick();

    const stagedShell = cardButton.closest('.card-shell');
    expect(stagedShell).not.toBeNull();
    expect(stagedShell?.classList.contains('selected')).toBe(true);
  });

  test('requires a second click on the highlighted card to confirm', async () => {
    updateRewardProgression(afterDropsProgression());

    const selectEvents = [];

    const { component, getByLabelText } = render(RewardOverlay, {
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

    component.$on('select', (event) => {
      if (event.detail?.type === 'card') {
        selectEvents.push(event.detail);
      }
    });

    const secondCardButton = getByLabelText('Select card Second Card');
    await fireEvent.click(secondCardButton);
    await tick();

    expect(selectEvents).toHaveLength(1);
    expect(selectEvents[0]?.intent).toBe('select');
    expect(selectEvents[0]?.id).toBe('second-card');
    const shell = secondCardButton.closest('.card-shell');
    expect(shell).not.toBeNull();
    expect(shell?.classList.contains('selected')).toBe(true);

    await fireEvent.click(secondCardButton);
    await tick();

    expect(selectEvents).toHaveLength(2);
    expect(selectEvents[1]?.intent).toBe('confirm');
    expect(selectEvents[1]?.id).toBe('second-card');
  });

  test('applies selected styling before confirmation in the card flow', async () => {
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
        reducedMotion: false
      }
    });

    component.$on('select', (event) => {
      if (event.detail?.type === 'card') {
        selectEvents.push(event.detail);
      }
    });

    const secondCardButton = container.querySelector(
      'button[aria-label="Select card Second Card"]'
    );
    expect(secondCardButton).not.toBeNull();
    if (!secondCardButton) return;

    await fireEvent.click(secondCardButton);
    await tick();

    expect(selectEvents).toHaveLength(1);
    expect(selectEvents[0]?.intent).toBe('select');
    const shell = secondCardButton.closest('.card-shell');
    expect(shell).not.toBeNull();
    expect(shell?.classList.contains('selected')).toBe(true);
    expect(shell?.dataset.reducedMotion).toBe('false');
  });
});
