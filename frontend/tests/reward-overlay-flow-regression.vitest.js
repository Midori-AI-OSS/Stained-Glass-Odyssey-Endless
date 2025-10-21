import { afterEach, beforeAll, beforeEach, describe, expect, test } from 'vitest';
import { tick } from 'svelte';
import {
  afterCardsProgression,
  afterDropsProgression,
  afterRelicsProgression,
  fourPhaseProgression,
  skipCardsProgression
} from './__fixtures__/rewardProgressionPayloads.js';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.DEV = false;

let cleanup;
let fireEvent;
let render;
let RewardOverlay;
let advanceRewardPhase;
let resetRewardProgression;
let updateRewardProgression;

beforeAll(async () => {
  ({ cleanup, fireEvent, render } = await import('@testing-library/svelte'));
  RewardOverlay = (await import('../src/lib/components/RewardOverlay.svelte')).default;
  ({
    advanceRewardPhase,
    resetRewardProgression,
    updateRewardProgression
  } = await import('../src/lib/systems/overlayState.js'));
});

beforeEach(() => {
  resetRewardProgression?.();
});

afterEach(() => {
  cleanup?.();
});

describe('reward overlay multi-phase regression', () => {
  test('walks through the four-phase flow with confirm hooks', async () => {
    updateRewardProgression(fourPhaseProgression());

    const cards = [
      { id: 'radiant-beam', name: 'Radiant Beam', stars: 4 },
      { id: 'echo-strike', name: 'Echo Strike', stars: 5 }
    ];
    const relics = [
      { id: 'guardian-talisman', name: 'Guardian Talisman' },
      { id: 'vital-fuse', name: 'Vital Fuse' }
    ];
    const items = [
      { id: 'ancient-coin', ui: { label: 'Ancient Coin' }, amount: 1 }
    ];

    const advanceEvents = [];
    const confirmEvents = [];

    const { component, container } = render(RewardOverlay, {
      props: {
        cards,
        relics,
        items,
        gold: 10,
        awaitingLoot: false,
        awaitingCard: false,
        awaitingRelic: false,
        awaitingNext: false,
        stagedCards: [],
        stagedRelics: [],
        reducedMotion: true
      }
    });

    component.$on('advance', (event) => {
      advanceEvents.push(event.detail);
      advanceRewardPhase();
      if (event.detail?.target === 'cards') {
        updateRewardProgression(afterDropsProgression());
      } else if (event.detail?.target === 'relics') {
        updateRewardProgression(afterCardsProgression());
      } else if (event.detail?.target === 'battle_review') {
        updateRewardProgression(afterRelicsProgression());
      }
    });

    component.$on('confirm', (event) => {
      confirmEvents.push(event.detail);
      event.detail?.respond?.({ ok: true });
      if (event.detail?.type === 'card') {
        queueMicrotask(() => {
          component.$set({
            cards: [],
            stagedCards: [],
            awaitingCard: false,
            relics,
            stagedRelics: [relics[0]],
            awaitingRelic: true
          });
          updateRewardProgression(afterCardsProgression());
        });
      } else if (event.detail?.type === 'relic') {
        queueMicrotask(() => {
          component.$set({
            relics: [],
            stagedRelics: [],
            awaitingRelic: false,
            awaitingNext: true
          });
          updateRewardProgression(afterRelicsProgression());
        });
      }
    });

    await tick();
    await tick();

    expect(container.querySelector('.drops-row')).not.toBeNull();

    const advanceButton = container.querySelector('.advance-button');
    expect(advanceButton).toBeInstanceOf(HTMLButtonElement);
    if (!(advanceButton instanceof HTMLButtonElement)) {
      throw new Error('advance button missing');
    }

    await fireEvent.click(advanceButton);
    await tick();
    await tick();

    component.$set({
      cards,
      stagedCards: [cards[0]],
      awaitingCard: true
    });
    await tick();

    const cardConfirmButton = container.querySelector(
      '.card-shell.confirmable button.card-confirm'
    );
    expect(cardConfirmButton).toBeInstanceOf(HTMLButtonElement);
    if (cardConfirmButton instanceof HTMLButtonElement) {
      await fireEvent.click(cardConfirmButton);
    }

    await tick();
    await tick();

    expect(confirmEvents.some((detail) => detail?.type === 'card')).toBe(true);

    await tick();

    const relicConfirmButton = container.querySelector(
      '.curio-shell.confirmable button.curio-confirm'
    );
    expect(relicConfirmButton).toBeInstanceOf(HTMLButtonElement);
    if (relicConfirmButton instanceof HTMLButtonElement) {
      await fireEvent.click(relicConfirmButton);
    }

    await tick();
    await tick();

    expect(confirmEvents.some((detail) => detail?.type === 'relic')).toBe(true);

    await tick();

    const nextRoomButton = container.querySelector('button.next-button.overlay');
    expect(nextRoomButton).toBeInstanceOf(HTMLButtonElement);

    expect(advanceEvents.length).toBeGreaterThan(0);
    expect(advanceEvents[0]?.reason).toBe('manual');
    expect(advanceEvents[0]?.target).toBe('cards');
  });

  test('skipCardsProgression hides the card phase by default', async () => {
    updateRewardProgression(skipCardsProgression());

    const { container } = render(RewardOverlay, {
      props: {
        cards: [],
        relics: [
          { id: 'guardian-talisman', name: 'Guardian Talisman' }
        ],
        items: [],
        gold: 0,
        awaitingLoot: false,
        awaitingCard: false,
        awaitingRelic: false,
        awaitingNext: false,
        stagedCards: [],
        stagedRelics: [],
        reducedMotion: true
      }
    });

    await tick();

    expect(container.querySelector('.card-shell')).toBeNull();
    expect(container.querySelector('.curio-shell')).not.toBeNull();
  });
});
