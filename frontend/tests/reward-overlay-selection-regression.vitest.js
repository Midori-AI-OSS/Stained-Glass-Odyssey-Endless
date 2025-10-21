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

  test('renders confirm controls for staged cards', async () => {
    const { component, container } = renderOverlay({
      cards: [],
      stagedCards: [{ id: 'radiant-beam', name: 'Radiant Beam', stars: 4 }],
      awaitingCard: true
    });

    let confirmDetail = null;
    component.$on('confirm', (event) => {
      confirmDetail = event.detail;
      event.detail?.respond?.({ ok: true });
    });

    const confirmButton = container.querySelector('.card-shell.confirmable button.card-confirm');
    expect(confirmButton).not.toBeNull();
    if (!confirmButton) return;

    await fireEvent.click(confirmButton);
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(confirmDetail?.type).toBe('card');
  });

  test('re-enables confirm button when the parent rejects the staged card', async () => {
    const { component, container } = renderOverlay({
      cards: [],
      stagedCards: [{ id: 'radiant-beam', name: 'Radiant Beam', stars: 4 }],
      awaitingCard: true
    });

    component.$on('confirm', (event) => {
      setTimeout(() => {
        event.detail?.respond?.({ ok: false });
      });
    });

    const confirmButton = container.querySelector('.card-shell.confirmable button.card-confirm');
    expect(confirmButton).not.toBeNull();
    if (!confirmButton) return;

    await fireEvent.click(confirmButton);
    expect(confirmButton.disabled).toBe(true);

    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(confirmButton.disabled).toBe(false);
  });

  test('renders staged reward previews when available', () => {
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

    const panel = container.querySelector('.preview-panel[data-type="card"]');
    expect(panel).not.toBeNull();
    expect(panel?.textContent).toMatch(/Attack/);
    expect(panel?.textContent).toMatch(/Triggers/);
  });

  test('dispatches cancel event for staged relics', async () => {
    const { component, container } = renderOverlay({
      cards: [],
      stagedRelics: [{ id: 'lucky-charm', name: 'Lucky Charm' }],
      awaitingCard: false,
      awaitingRelic: true
    });

    let cancelDetail = null;
    component.$on('cancel', (event) => {
      cancelDetail = event.detail;
      event.detail?.respond?.({ ok: true });
    });

    const cancelButton = container.querySelector('button.cancel-btn');
    expect(cancelButton).not.toBeNull();
    if (!cancelButton) return;

    await fireEvent.click(cancelButton);
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(cancelDetail?.type).toBe('relic');
  });

  test('prevents duplicate relic confirm dispatch while a request is pending', async () => {
    let confirmCount = 0;
    const { component, container } = renderOverlay({
      cards: [],
      stagedRelics: [{ id: 'guardian-talisman', name: 'Guardian Talisman' }],
      awaitingRelic: true,
      awaitingCard: false
    });

    component.$on('confirm', (event) => {
      confirmCount += 1;
      if (confirmCount === 1) {
        setTimeout(() => {
          event.detail?.respond?.({ ok: true });
        }, 5);
      }
    });

    const confirmButton = container.querySelector('.curio-shell.confirmable button.curio-confirm');
    expect(confirmButton).not.toBeNull();
    if (!confirmButton) return;

    await fireEvent.click(confirmButton);
    expect(confirmButton.disabled).toBe(true);

    await fireEvent.click(confirmButton);
    expect(confirmCount).toBe(1);

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(confirmButton.disabled).toBe(false);
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
