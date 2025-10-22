import { afterEach, beforeAll, beforeEach, describe, expect, test } from 'vitest';
import { tick } from 'svelte';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.DEV = false;

let cleanup;
let render;
let fireEvent;
let OverlayHost;
let rewardPhaseController;
let resetRewardProgression;

beforeAll(async () => {
  ({ cleanup, render, fireEvent } = await import('@testing-library/svelte'));
  OverlayHost = (await import('../src/lib/components/OverlayHost.svelte')).default;
  ({ rewardPhaseController, resetRewardProgression } = await import('../src/lib/systems/overlayState.js'));
});

beforeEach(() => {
  resetRewardProgression?.();
});

afterEach(() => {
  cleanup?.();
  resetRewardProgression?.();
});

function createBaseRoomData() {
  return {
    result: 'battle',
    loot: { items: [], gold: 0 },
    reward_progression: {
      available: ['drops', 'cards', 'relics', 'battle_review'],
      completed: ['drops'],
      current_step: 'cards'
    },
    reward_staging: { cards: [], relics: [], items: [] },
    card_choices: [
      {
        id: 'radiant-beam',
        name: 'Radiant Beam',
        stars: 4
      }
    ],
    relic_choices: [],
    awaiting_card: false,
    awaiting_relic: false,
    awaiting_loot: false,
    awaiting_next: false
  };
}

describe('Reward overlay confirmation flow', () => {
  test('double click confirms and closes the reward overlay', async () => {
    const stagedCard = { id: 'radiant-beam', name: 'Radiant Beam', stars: 4 };
    const baseRoomData = createBaseRoomData();
    let roomData = { ...baseRoomData };

    const stagePayload = {
      card_choices: [],
      awaiting_card: true,
      awaiting_relic: false,
      awaiting_loot: false,
      awaiting_next: false,
      next_room: 'shop',
      reward_staging: { cards: [stagedCard], relics: [], items: [] },
      reward_progression: {
        available: ['drops', 'cards', 'relics', 'battle_review'],
        completed: ['drops'],
        current_step: 'cards'
      }
    };

    const confirmPayload = {
      cards: ['radiant-beam'],
      awaiting_card: false,
      awaiting_relic: false,
      awaiting_loot: false,
      awaiting_next: true,
      next_room: 'shop',
      reward_staging: { cards: [], relics: [], items: [] },
      reward_progression: {
        available: ['drops', 'cards', 'relics', 'battle_review'],
        completed: ['drops', 'cards'],
        current_step: 'relics'
      }
    };

    const { component, queryByLabelText, queryByText } = render(OverlayHost, {
      props: {
        runId: 'test-run',
        roomData,
        selected: [],
        selectedParty: [],
        battleActive: false,
        shopProcessing: false,
        battleSnapshot: null,
        editorState: {},
        sfxVolume: 5,
        musicVolume: 5,
        voiceVolume: 5,
        framerate: 60,
        reducedMotion: true,
        showActionValues: false,
        showTurnCounter: true,
        flashEnrageCounter: true,
        fullIdleMode: false,
        skipBattleReview: false,
        animationSpeed: 1,
        backendFlavor: ''
      }
    });

    component.$on('rewardSelect', (event) => {
      const detail = event.detail || {};
      const respond = typeof detail.respond === 'function' ? detail.respond : null;
      const intent = typeof detail.intent === 'string' ? detail.intent : 'select';
      if (intent === 'select') {
        roomData = {
          ...roomData,
          ...stagePayload,
          reward_staging: stagePayload.reward_staging,
          card_choices: []
        };
        component.$set({ roomData });
        respond?.({ ok: true, intent, payload: stagePayload });
      } else if (intent === 'confirm') {
        roomData = {
          ...roomData,
          ...confirmPayload,
          reward_staging: confirmPayload.reward_staging,
          card_choices: []
        };
        component.$set({ roomData });
        respond?.({ ok: true, intent, payload: confirmPayload });
      }
    });

    const cardButton = queryByLabelText('Select card Radiant Beam');
    expect(cardButton).not.toBeNull();
    if (!cardButton) return;

    await fireEvent.click(cardButton);
    await tick();

    expect(queryByText('Confirm Card Radiant Beam?')).not.toBeNull();

    await fireEvent.click(cardButton);
    await tick();
    await tick();

    expect(queryByLabelText('Select card Radiant Beam')).toBeNull();
    expect(queryByText('Confirm Card Radiant Beam?')).toBeNull();

    const snapshot = rewardPhaseController.getSnapshot?.();
    expect(snapshot?.completed || []).toContain('cards');
    expect(snapshot?.current).not.toBe('cards');
  });

  test('advance button confirms a staged card when fallback activates', async () => {
    const stagedCard = { id: 'radiant-beam', name: 'Radiant Beam', stars: 4 };
    const baseRoomData = createBaseRoomData();
    let roomData = { ...baseRoomData };

    const stagePayload = {
      card_choices: [],
      awaiting_card: true,
      awaiting_relic: false,
      awaiting_loot: false,
      awaiting_next: false,
      next_room: 'shop',
      reward_staging: { cards: [stagedCard], relics: [], items: [] },
      reward_progression: {
        available: ['drops', 'cards', 'relics', 'battle_review'],
        completed: ['drops'],
        current_step: 'cards'
      }
    };

    const confirmPayload = {
      cards: ['radiant-beam'],
      awaiting_card: false,
      awaiting_relic: false,
      awaiting_loot: false,
      awaiting_next: true,
      next_room: 'shop',
      reward_staging: { cards: [], relics: [], items: [] },
      reward_progression: {
        available: ['drops', 'cards', 'relics', 'battle_review'],
        completed: ['drops', 'cards'],
        current_step: 'relics'
      }
    };

    const { component, container, queryByLabelText, queryByText } = render(OverlayHost, {
      props: {
        runId: 'test-run',
        roomData,
        selected: [],
        selectedParty: [],
        battleActive: false,
        shopProcessing: false,
        battleSnapshot: null,
        editorState: {},
        sfxVolume: 5,
        musicVolume: 5,
        voiceVolume: 5,
        framerate: 60,
        reducedMotion: true,
        showActionValues: false,
        showTurnCounter: true,
        flashEnrageCounter: true,
        fullIdleMode: false,
        skipBattleReview: false,
        animationSpeed: 1,
        backendFlavor: ''
      }
    });

    component.$on('rewardSelect', (event) => {
      const detail = event.detail || {};
      const respond = typeof detail.respond === 'function' ? detail.respond : null;
      const intent = typeof detail.intent === 'string' ? detail.intent : 'select';
      if (intent === 'select') {
        roomData = {
          ...roomData,
          ...stagePayload,
          reward_staging: stagePayload.reward_staging,
          card_choices: []
        };
        component.$set({ roomData });
        respond?.({ ok: true, intent, payload: stagePayload });
      } else if (intent === 'confirm') {
        roomData = {
          ...roomData,
          ...confirmPayload,
          reward_staging: confirmPayload.reward_staging,
          card_choices: []
        };
        component.$set({ roomData });
        respond?.({ ok: true, intent, payload: confirmPayload });
      }
    });

    const cardButton = queryByLabelText('Select card Radiant Beam');
    expect(cardButton).not.toBeNull();
    if (!cardButton) return;

    await fireEvent.click(cardButton);
    await tick();
    await tick();

    const advanceButton = container.querySelector('.advance-button');
    expect(advanceButton).toBeInstanceOf(HTMLButtonElement);
    if (!(advanceButton instanceof HTMLButtonElement)) return;

    expect(advanceButton.disabled).toBe(false);
    expect(advanceButton.dataset.mode).toBe('confirm-card');
    expect(advanceButton.getAttribute('aria-label') ?? '').toMatch(/Confirm Card/);

    const statusText = container.querySelector('.advance-status')?.textContent ?? '';
    expect(statusText).toMatch(/Use Advance to confirm/);
    expect(container.querySelector('.advance-helper')?.textContent ?? '').toMatch(/Advance confirms/i);

    await fireEvent.click(advanceButton);
    await tick();
    await tick();

    expect(queryByText('Confirm Card Radiant Beam?')).toBeNull();
    const snapshot = rewardPhaseController.getSnapshot?.();
    expect(snapshot?.completed || []).toContain('cards');
    expect(snapshot?.current).not.toBe('cards');
  });
});
