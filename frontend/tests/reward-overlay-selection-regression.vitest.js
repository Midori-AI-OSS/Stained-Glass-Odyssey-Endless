import { afterEach, beforeAll, describe, expect, test } from 'vitest';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.DEV = false;

let cleanup;
let fireEvent;
let render;
let RewardOverlay;
let resetRewardProgression;

beforeAll(async () => {
  ({ cleanup, fireEvent, render } = await import('@testing-library/svelte'));
  RewardOverlay = (await import('../src/lib/components/RewardOverlay.svelte')).default;
  ({ resetRewardProgression } = await import('../src/lib/systems/overlayState.js'));
});

const baseProps = Object.freeze({
  cards: [
    {
      id: 'radiant-beam',
      name: 'Radiant Beam',
      stars: 4
    }
  ],
  relics: [],
  items: [],
  gold: 0,
  partyStats: [],
  ended: false,
  nextRoom: '',
  fullIdleMode: false,
  sfxVolume: 5,
  reducedMotion: false
});

function renderOverlay(overrides = {}) {
  const props = { ...baseProps, ...overrides };
  return render(RewardOverlay, { props });
}

afterEach(() => {
  resetRewardProgression?.();
  cleanup();
});

describe('RewardOverlay selection regression', () => {
  test('keeps cards selectable when parent rejects the choice', async () => {
    const { component, container } = renderOverlay();

    component.$on('select', (event) => {
      setTimeout(() => {
        event.detail?.respond?.({ ok: false });
      });
    });

    const cardButton = container.querySelector('button[aria-label^="Select card"]');
    expect(cardButton).not.toBeNull();
    if (!cardButton) return;

    await fireEvent.click(cardButton);
    await new Promise((resolve) => setTimeout(resolve, 5));

    expect(container.querySelector('button[aria-label^="Select card"]')).not.toBeNull();
  });

  test('renders staged cards without confirm controls', async () => {
    const { container } = renderOverlay({
      cards: [],
      stagedCards: [{ id: 'radiant-beam', name: 'Radiant Beam', stars: 4 }],
      awaitingCard: true
    });

    expect(container.querySelector('.card-shell.confirmable')).toBeNull();
    expect(container.querySelector('button.card-confirm')).toBeNull();
    const stagedShell = container.querySelector('.card-shell.selected');
    expect(stagedShell).not.toBeNull();
  });

  test('re-dispatches select events for staged cards', async () => {
    const { component, container } = renderOverlay({
      cards: [],
      stagedCards: [{ id: 'radiant-beam', name: 'Radiant Beam', stars: 4 }],
      awaitingCard: true
    });

    let selectDetail = null;
    component.$on('select', (event) => {
      selectDetail = event.detail;
      event.detail?.respond?.({ ok: true });
    });

    const cardButton = container.querySelector('button[aria-label="Select card Radiant Beam"]');
    expect(cardButton).not.toBeNull();
    if (!cardButton) return;

    await fireEvent.click(cardButton);
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(selectDetail?.type).toBe('card');
    expect(selectDetail?.id).toBe('radiant-beam');
  });

  test('omits staged preview panels when cards are already confirmed', () => {
    const { container } = renderOverlay({
      cards: [],
      stagedCards: [
        {
          id: 'radiant-beam',
          name: 'Radiant Beam',
          stars: 4,
          about: 'Deal extra damage to all foes.',
          preview: {
            summary: 'Deal extra damage to all foes.',
            stats: [
              { stat: 'atk', mode: 'percent', amount: 12, total_amount: 12, stacks: 1, target: 'party' }
            ],
            triggers: [{ event: 'on_turn_start', description: 'Gain 1 energy.' }]
          }
        }
      ],
      awaitingCard: true
    });

    expect(container.querySelector('.preview-panel')).toBeNull();
  });

  test('renders staged relics without confirm or cancel controls', async () => {
    const { container } = renderOverlay({
      cards: [],
      stagedRelics: [{ id: 'lucky-charm', name: 'Lucky Charm' }],
      awaitingCard: false,
      awaitingRelic: true
    });

    expect(container.querySelector('.curio-shell.confirmable')).toBeNull();
    expect(container.querySelector('button.curio-confirm')).toBeNull();
    expect(container.querySelector('button.cancel-btn')).toBeNull();
  });

  test('re-dispatches select events for staged relics', async () => {
    const { component, container } = renderOverlay({
      cards: [],
      stagedRelics: [{ id: 'guardian-talisman', name: 'Guardian Talisman' }],
      awaitingRelic: true,
      awaitingCard: false
    });

    let selectDetail = null;
    component.$on('select', (event) => {
      selectDetail = event.detail;
      event.detail?.respond?.({ ok: true });
    });

    const relicButton = container.querySelector('button[aria-label="Select relic Guardian Talisman"]');
    expect(relicButton).not.toBeNull();
    if (!relicButton) return;

    await fireEvent.click(relicButton);
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(selectDetail?.type).toBe('relic');
    expect(selectDetail?.id).toBe('guardian-talisman');
  });

  test('shows the next-room automation button when confirmations are clear', async () => {
    const { container } = renderOverlay({
      cards: [],
      stagedCards: [],
      stagedRelics: [],
      awaitingCard: false,
      awaitingRelic: false,
      awaitingLoot: false,
      awaitingNext: true
    });

    const nextButton = container.querySelector('button.next-button.overlay');
    expect(nextButton).not.toBeNull();
  });

  test('hides the next-room automation button while loot confirmation is pending', async () => {
    const { container } = renderOverlay({
      cards: [],
      stagedCards: [],
      stagedRelics: [],
      awaitingCard: false,
      awaitingRelic: false,
      awaitingLoot: true,
      awaitingNext: true
    });

    const nextButton = container.querySelector('button.next-button.overlay');
    expect(nextButton).toBeNull();
  });
});
