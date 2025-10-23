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

  test('applies selected styling before confirmation in the relic flow', async () => {
    updateRewardProgression(afterCardsProgression());

    const selectHandler = vi.fn();

    const { component, container } = render(RewardOverlay, {
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

    component.$on('select', (event) => {
      if (event.detail?.type === 'relic') {
        selectHandler(event.detail);
      }
    });

    const secondRelicButton = container.querySelector(
      'button[aria-label="Select relic Second Relic"]'
    );
    expect(secondRelicButton).not.toBeNull();
    if (!secondRelicButton) return;

    await fireEvent.click(secondRelicButton);
    await tick();

    expect(selectHandler).not.toHaveBeenCalled();
    const shell = secondRelicButton.closest('.curio-shell');
    expect(shell).not.toBeNull();
    expect(shell?.classList.contains('selected')).toBe(true);
    expect(shell?.classList.contains('confirmable')).toBe(false);
    expect(shell?.dataset.reducedMotion).toBe('false');
  });

  test('keeps staged relic in the main grid while awaiting confirmation', async () => {
    updateRewardProgression({
      available: ['relics', 'battle_review'],
      completed: [],
      current_step: 'relics'
    });

    const stagedRelic = { id: 'guardian-talisman', name: 'Guardian Talisman' };

    const { container, getByLabelText } = render(RewardOverlay, {
      props: {
        ...baseProps,
        relics: [],
        stagedRelics: [stagedRelic],
        awaitingRelic: true
      }
    });

    await tick();

    expect(container.querySelector('.staged-block')).toBeNull();
    const relicButton = getByLabelText('Select relic Guardian Talisman');
    expect(relicButton).not.toBeNull();
    if (!relicButton) return;

    await fireEvent.click(relicButton);
    await tick();

    const stagedShell = relicButton.closest('.curio-shell');
    expect(stagedShell).not.toBeNull();
    expect(stagedShell?.classList.contains('selected')).toBe(true);
  });

  test('keeps relic grid visible and routes confirmation through Advance controls', async () => {
    updateRewardProgression({
      available: ['cards', 'relics', 'battle_review'],
      completed: ['cards'],
      current_step: 'relics'
    });

    const relicPool = [
      { id: 'moon-charm', name: 'Moon Charm' },
      { id: 'sun-charm', name: 'Sun Charm' }
    ];

    const { container, getByText } = render(RewardOverlay, {
      props: {
        ...baseProps,
        relics: relicPool,
        stagedRelics: [relicPool[0]],
        awaitingRelic: true
      }
    });

    await tick();

    const relicHeading = getByText('Choose a Relic');
    expect(relicHeading).not.toBeNull();

    const relicGrid = relicHeading?.nextElementSibling;
    expect(relicGrid).not.toBeNull();
    expect(relicGrid?.classList.contains('choices')).toBe(true);
    expect(relicGrid?.querySelectorAll('.curio-shell').length ?? 0).toBeGreaterThan(0);

    expect(container.querySelector('.confirm-panel')).toBeNull();

    const advancePanel = container.querySelector('.advance-panel');
    expect(advancePanel).not.toBeNull();
    expect(advancePanel?.classList.contains('confirm-mode')).toBe(true);

    const helper = advancePanel?.querySelector('.advance-helper');
    expect(helper?.textContent?.trim()).toMatch(/Advance confirms/i);

    const advanceButton = advancePanel?.querySelector('button.advance-button');
    expect(advanceButton).not.toBeNull();
    expect(advanceButton?.dataset.mode).toBe('confirm-relic');
    expect(advanceButton?.getAttribute('aria-label') ?? '').toContain('Confirm Relic');
  });

  test('requires a second click on the highlighted relic to confirm', async () => {
    updateRewardProgression({
      available: ['relics'],
      completed: [],
      current_step: 'relics'
    });

    const stagedRelic = { id: 'echo-charm', name: 'Echo Charm' };

    const selectHandler = vi.fn();
    const { component, getByLabelText } = render(RewardOverlay, {
      props: {
        ...baseProps,
        relics: [],
        stagedRelics: [stagedRelic],
        awaitingRelic: true
      }
    });

    component.$on('select', (event) => {
      if (event.detail?.type === 'relic') {
        selectHandler(event.detail);
      }
    });

    const relicButton = getByLabelText('Select relic Echo Charm');
    await fireEvent.click(relicButton);
    await tick();

    expect(selectHandler).not.toHaveBeenCalled();
    const shell = relicButton.closest('.curio-shell');
    expect(shell).not.toBeNull();
    expect(shell?.classList.contains('selected')).toBe(true);

    await fireEvent.click(relicButton);
    await tick();

    expect(selectHandler).toHaveBeenCalledTimes(1);
    expect(selectHandler.mock.calls[0][0]?.id).toBe('echo-charm');
  });

  test('highlights the first available relic after staged selection clears', async () => {
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

    component.$set({
      stagedRelics: [],
      awaitingRelic: false,
      relics: [
        { id: 'renewed-stone', name: 'Renewed Stone' },
        { id: 'ember-core', name: 'Ember Core' }
      ]
    });

    await tick();
    await tick();

    const firstChoiceShell = container.querySelector('.curio-shell.selected');
    expect(firstChoiceShell).not.toBeNull();
    expect(firstChoiceShell?.querySelector('[aria-label="Select relic Renewed Stone"]')).not.toBeNull();
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
