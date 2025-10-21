import { afterEach, beforeAll, beforeEach, describe, expect, test, vi } from 'vitest';
import { tick } from 'svelte';
import { afterCardsProgression } from './__fixtures__/rewardProgressionPayloads.js';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.DEV = false;

let cleanup;
let fireEvent;
let render;
let RewardOverlay;
let updateRewardProgression;
let resetRewardProgression;

beforeAll(async () => {
  ({ cleanup, fireEvent, render } = await import('@testing-library/svelte'));
  RewardOverlay = (await import('../src/lib/components/RewardOverlay.svelte')).default;
  ({ updateRewardProgression, resetRewardProgression } = await import('../src/lib/systems/overlayState.js'));
});

beforeEach(() => {
  resetRewardProgression?.();
});

afterEach(() => {
  cleanup();
});

const baseProps = Object.freeze({
  cards: [],
  items: [],
  gold: 0,
  awaitingLoot: false,
  awaitingNext: false,
  awaitingCard: false,
  fullIdleMode: false,
  reducedMotion: true,
  sfxVolume: 5
});

describe('RewardOverlay relic phase interactions', () => {
  test('auto-selects the first relic when entering the relic phase', async () => {
    updateRewardProgression({
      available: ['drops', 'cards', 'relics'],
      completed: ['drops', 'cards'],
      current_step: 'relics'
    });

    const selectEvents = [];
    const { component, container } = render(RewardOverlay, {
      props: {
        ...baseProps,
        relics: [
          { id: 'first-relic', name: 'First Relic' },
          { id: 'second-relic', name: 'Second Relic' }
        ]
      }
    });

    component.$on('select', (event) => selectEvents.push(event.detail));

    await tick();
    await tick();

    expect(selectEvents.some((detail) => detail?.type === 'relic' && detail?.id === 'first-relic')).toBe(true);
    const highlighted = container.querySelector('.curio-shell.selected');
    expect(highlighted).not.toBeNull();
  });

  test('applies selected styling in the no-confirmation relic flow', async () => {
    updateRewardProgression(afterCardsProgression());

    const { container } = render(RewardOverlay, {
      props: {
        ...baseProps,
        relics: [
          { id: 'first-relic', name: 'First Relic' },
          { id: 'second-relic', name: 'Second Relic' }
        ],
        reducedMotion: false,
        awaitingRelic: false
      }
    });

    const secondRelicButton = container.querySelector(
      'button[aria-label="Select relic Second Relic"]'
    );
    expect(secondRelicButton).not.toBeNull();
    if (!secondRelicButton) return;

    await fireEvent.click(secondRelicButton);
    await tick();

    const shell = secondRelicButton.closest('.curio-shell');
    expect(shell).not.toBeNull();
    expect(shell?.classList.contains('selected')).toBe(true);
    expect(shell?.classList.contains('confirmable')).toBe(false);
    expect(shell?.dataset.reducedMotion).toBe('false');
  });

  test('shows on-tile confirm controls for the staged relic', async () => {
    updateRewardProgression({
      available: ['relics', 'battle_review'],
      completed: [],
      current_step: 'relics'
    });

    const stagedRelic = { id: 'guardian-talisman', name: 'Guardian Talisman' };

    const { container } = render(RewardOverlay, {
      props: {
        ...baseProps,
        relics: [],
        stagedRelics: [stagedRelic],
        awaitingRelic: true
      }
    });

    await tick();

    const confirmShell = container.querySelector('.curio-shell.confirmable');
    expect(confirmShell).not.toBeNull();
    expect(confirmShell?.querySelector('button.curio-confirm')).not.toBeNull();
    expect(confirmShell?.classList.contains('selected')).toBe(true);
  });

  test('dispatches confirm when clicking the staged relic again', async () => {
    updateRewardProgression({
      available: ['relics'],
      completed: [],
      current_step: 'relics'
    });

    const stagedRelic = { id: 'echo-charm', name: 'Echo Charm' };

    const { component, getByLabelText } = render(RewardOverlay, {
      props: {
        ...baseProps,
        relics: [],
        stagedRelics: [stagedRelic],
        awaitingRelic: true
      }
    });

    const confirmHandler = vi.fn();
    component.$on('confirm', (event) => {
      if (event.detail?.type === 'relic') {
        confirmHandler(event.detail);
      }
    });

    const relicButton = getByLabelText('Select relic Echo Charm');
    await fireEvent.click(relicButton);
    await tick();

    expect(confirmHandler).toHaveBeenCalledTimes(1);
    expect(confirmHandler.mock.calls[0][0]?.id).toBe('echo-charm');
  });

  test('refocuses the relic grid after confirmation resolves', async () => {
    updateRewardProgression({
      available: ['relics', 'battle_review'],
      completed: [],
      current_step: 'relics'
    });

    const stagedRelic = { id: 'focus-stone', name: 'Focus Stone' };

    const { component, container } = render(RewardOverlay, {
      props: {
        ...baseProps,
        relics: [],
        stagedRelics: [stagedRelic],
        awaitingRelic: true
      }
    });

    component.$on('confirm', (event) => {
      event.detail?.respond?.({ ok: true });
      component.$set({
        stagedRelics: [],
        awaitingRelic: false,
        relics: [
          { id: 'renewed-stone', name: 'Renewed Stone' },
          { id: 'ember-core', name: 'Ember Core' }
        ]
      });
    });

    const confirmButton = container.querySelector('.curio-shell.confirmable button.curio-confirm');
    expect(confirmButton).not.toBeNull();
    if (!confirmButton) return;

    confirmButton.focus();
    await fireEvent.click(confirmButton);

    await tick();
    await tick();

    const firstChoice = container.querySelector('.choices button[data-reward-relic]');
    expect(firstChoice).not.toBeNull();
    expect(document.activeElement).toBe(firstChoice);
  });

  test('clears relic highlight when the staged selection resets', async () => {
    updateRewardProgression({
      available: ['relics'],
      completed: [],
      current_step: 'relics'
    });

    const stagedRelic = { id: 'reset-charm', name: 'Reset Charm' };

    const { component, container } = render(RewardOverlay, {
      props: {
        ...baseProps,
        relics: [],
        stagedRelics: [stagedRelic],
        awaitingRelic: true
      }
    });

    await tick();

    component.$set({
      stagedRelics: [],
      awaitingRelic: false,
      relics: [
        { id: 'new-relic', name: 'New Relic' },
        { id: 'backup-relic', name: 'Backup Relic' }
      ]
    });

    await tick();
    await tick();

    expect(container.querySelector('.curio-shell.confirmable')).toBeNull();
    const highlightedChoice = container.querySelector('.choices .curio-shell.selected');
    expect(highlightedChoice).not.toBeNull();
    expect(highlightedChoice?.querySelector('button.curio-confirm')).toBeNull();
  });
});
