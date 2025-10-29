import { describe, expect, test, vi } from 'vitest';
import {
  computeAutomationAction,
  hasLootAvailable,
  shouldUseLegacyAutomation
} from '../src/lib/utils/rewardAutomation.js';
import {
  RewardAutomationScheduler,
  resolveAutomationDelay,
  actionsEqual,
  __INTERNAL_DELAY_BOUNDS__
} from '../src/lib/utils/rewardAutomationScheduler.js';

function snapshotFor(phase, overrides = {}) {
  const sequence = ['drops', 'cards', 'relics', 'battle_review'];
  const index = sequence.indexOf(phase);
  const next = index >= 0 && index < sequence.length - 1 ? sequence[index + 1] : null;
  return {
    sequence,
    current: phase,
    next,
    diagnostics: [],
    ...overrides
  };
}

describe('reward automation helpers', () => {
  test('shouldUseLegacyAutomation flags empty sequences', () => {
    expect(shouldUseLegacyAutomation(null)).toBe(true);
    expect(shouldUseLegacyAutomation({ sequence: [] })).toBe(true);
    expect(
      shouldUseLegacyAutomation({
        sequence: ['drops'],
        current: 'drops',
        diagnostics: ['invalid']
      })
    ).toBe(true);
    expect(
      shouldUseLegacyAutomation({
        sequence: ['drops'],
        current: 'drops',
        diagnostics: []
      })
    ).toBe(false);
  });

  test('hasLootAvailable detects gold or items', () => {
    expect(hasLootAvailable(null)).toBe(false);
    expect(hasLootAvailable({ loot: {} })).toBe(false);
    expect(hasLootAvailable({ loot: { gold: 5 } })).toBe(true);
    expect(hasLootAvailable({ loot: { items: [{ id: 'ticket' }] } })).toBe(true);
  });

  test('selects first card when card choices exist', () => {
    const roomData = { card_choices: [{ id: 'a' }] };
    const action = computeAutomationAction({
      roomData,
      snapshot: snapshotFor('cards')
    });
    expect(action.type).toBe('select-card');
    expect(action.choice).toEqual({ id: 'a' });
  });

  test('confirms when awaiting card resolution with staged selection', () => {
    const roomData = {
      awaiting_card: true,
      reward_staging: { cards: [{ id: 'a' }] }
    };
    const action = computeAutomationAction({
      roomData,
      snapshot: snapshotFor('cards'),
      stagedCards: [{ id: 'a' }]
    });
    expect(action.type).toBe('confirm-card');
  });

  test('card automation progresses select, confirm, advance', () => {
    const snapshot = snapshotFor('cards');
    const cardChoice = { id: 'card-a' };

    const selectAction = computeAutomationAction({
      roomData: {
        awaiting_card: false,
        card_choices: [cardChoice],
        reward_staging: { cards: [] }
      },
      snapshot,
      stagedCards: []
    });
    expect(selectAction.type).toBe('select-card');
    expect(selectAction.choice).toEqual(cardChoice);

    const confirmAction = computeAutomationAction({
      roomData: {
        awaiting_card: true,
        card_choices: [],
        reward_staging: { cards: [cardChoice] }
      },
      snapshot,
      stagedCards: [cardChoice]
    });
    expect(confirmAction.type).toBe('confirm-card');

    const advanceAction = computeAutomationAction({
      roomData: {
        awaiting_card: false,
        card_choices: [],
        reward_staging: { cards: [] }
      },
      snapshot,
      stagedCards: []
    });
    expect(advanceAction.type).toBe('advance');
    expect(advanceAction.phase).toBe('cards');
  });

  test('relic automation progresses select, confirm, advance', () => {
    const snapshot = snapshotFor('relics');
    const relicChoice = { id: 'relic-a' };

    const selectAction = computeAutomationAction({
      roomData: {
        awaiting_card: false,
        awaiting_relic: false,
        relic_choices: [relicChoice],
        reward_staging: { relics: [] }
      },
      snapshot,
      stagedRelics: []
    });
    expect(selectAction.type).toBe('select-relic');
    expect(selectAction.choice).toEqual(relicChoice);

    const confirmAction = computeAutomationAction({
      roomData: {
        awaiting_card: false,
        awaiting_relic: true,
        relic_choices: [],
        reward_staging: { relics: [relicChoice] }
      },
      snapshot,
      stagedRelics: [relicChoice]
    });
    expect(confirmAction.type).toBe('confirm-relic');

    const advanceAction = computeAutomationAction({
      roomData: {
        awaiting_card: false,
        awaiting_relic: false,
        relic_choices: [],
        reward_staging: { relics: [] }
      },
      snapshot,
      stagedRelics: []
    });
    expect(advanceAction.type).toBe('advance');
    expect(advanceAction.phase).toBe('relics');
  });

  test('advances when card phase has no choices or staging', () => {
    const roomData = {
      card_choices: [],
      reward_staging: { cards: [] }
    };
    const action = computeAutomationAction({
      roomData,
      snapshot: snapshotFor('cards')
    });
    expect(action.type).toBe('advance');
    expect(action.phase).toBe('cards');
  });

  test('advances relic phase once staging clears', () => {
    const roomData = {
      awaiting_relic: false,
      relic_choices: [],
      reward_staging: { relics: [] }
    };
    const action = computeAutomationAction({
      roomData,
      snapshot: snapshotFor('relics'),
      stagedRelics: []
    });
    expect(action.type).toBe('advance');
    expect(action.phase).toBe('relics');
  });

  test('selects relic after cards complete', () => {
    const roomData = {
      awaiting_card: false,
      relic_choices: [{ id: 'relic-a' }]
    };
    const action = computeAutomationAction({
      roomData,
      snapshot: snapshotFor('relics')
    });
    expect(action.type).toBe('select-relic');
    expect(action.choice?.id).toBe('relic-a');
  });

  test('advances drops phase when loot remains', () => {
    const roomData = {
      awaiting_loot: true,
      loot: { gold: 10 }
    };
    const action = computeAutomationAction({
      roomData,
      snapshot: snapshotFor('drops')
    });
    expect(action.type).toBe('advance');
    expect(action.phase).toBe('drops');
  });

  test('advances battle review when awaiting next', () => {
    const roomData = { awaiting_next: true };
    const action = computeAutomationAction({
      roomData,
      snapshot: snapshotFor('battle_review')
    });
    expect(action.type).toBe('advance');
    expect(action.phase).toBe('battle_review');
  });

  test('acknowledges loot under legacy flow', () => {
    const roomData = { awaiting_loot: true };
    const action = computeAutomationAction({
      roomData,
      snapshot: null
    });
    expect(action.type).toBe('ack-loot');
  });

  test('advances to next room for shops when legacy handling is used', () => {
    const roomData = { result: 'shop' };
    const action = computeAutomationAction({
      roomData,
      snapshot: null
    });
    expect(action.type).toBe('next-room');
  });

  test('resolveAutomationDelay respects reduced motion toggles', () => {
    const action = { type: 'select-card', choice: { id: 'card-a' } };
    const normal = resolveAutomationDelay(action, { reducedMotion: false, random: () => 0 });
    const reduced = resolveAutomationDelay(action, { reducedMotion: true, random: () => 0 });
    expect(normal).toBe(__INTERNAL_DELAY_BOUNDS__['select-card'].normal[0]);
    expect(reduced).toBe(__INTERNAL_DELAY_BOUNDS__['select-card'].reduced[0]);
  });

  test('RewardAutomationScheduler waits before executing actions', async () => {
    vi.useFakeTimers();
    const scheduler = new RewardAutomationScheduler({
      getDelay: () => 500
    });
    const execute = vi.fn(async () => {});
    scheduler.schedule({ type: 'ack-loot' }, {
      execute,
      validate: () => true,
      onSettled: () => {}
    });
    expect(execute).not.toHaveBeenCalled();
    vi.advanceTimersByTime(499);
    await Promise.resolve();
    expect(execute).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    await Promise.resolve();
    expect(execute).toHaveBeenCalledTimes(1);
    scheduler.cancel();
    vi.useRealTimers();
  });

  test('RewardAutomationScheduler adapts delays when reduced motion changes', () => {
    let recordedDelay = null;
    const scheduler = new RewardAutomationScheduler({
      getDelay: (_action, { reducedMotion }) => (reducedMotion ? 150 : 720),
      setTimeoutFn: (_fn, delay) => {
        recordedDelay = delay;
        return {};
      },
      clearTimeoutFn: () => {}
    });
    const noop = async () => {};
    scheduler.schedule({ type: 'next-room' }, { execute: noop, validate: () => false });
    expect(recordedDelay).toBe(720);
    scheduler.cancel();
    scheduler.updateReducedMotion(true);
    scheduler.schedule({ type: 'next-room' }, { execute: noop, validate: () => false });
    expect(recordedDelay).toBe(150);
    scheduler.cancel();
  });

  test('Full Idle Mode automation confirms rewards and advances automatically', async () => {
    const cardChoice = { id: 'card-a' };
    const relicChoice = { id: 'relic-a' };
    let snapshot = snapshotFor('cards');
    let roomData = {
      result: 'battle',
      loot: { items: [], gold: 0 },
      awaiting_card: false,
      awaiting_relic: false,
      awaiting_next: false,
      card_choices: [cardChoice],
      relic_choices: [],
      reward_staging: { cards: [], relics: [], items: [] }
    };
    let stagedCards = [];
    let stagedRelics = [];
    const executed = [];

    const scheduler = new RewardAutomationScheduler({
      getDelay: () => 0,
      setTimeoutFn: (fn) => {
        let cancelled = false;
        queueMicrotask(() => {
          if (!cancelled) {
            fn();
          }
        });
        return {
          cancel() {
            cancelled = true;
          }
        };
      },
      clearTimeoutFn: (handle) => {
        handle?.cancel?.();
      }
    });

    function compute() {
      return computeAutomationAction({ roomData, snapshot, stagedCards, stagedRelics });
    }

    function maybeHandle() {
      const action = compute();
      if (!action || action.type === 'none') {
        return;
      }
      scheduler.schedule(action, {
        execute: async (pending) => {
          executed.push(pending.type);
          switch (pending.type) {
            case 'select-card': {
              stagedCards = [cardChoice];
              const currentStaging = roomData.reward_staging || { cards: [], relics: [], items: [] };
              roomData = {
                ...roomData,
                awaiting_card: true,
                card_choices: [],
                reward_staging: { ...currentStaging, cards: [...stagedCards] }
              };
              break;
            }
            case 'confirm-card': {
              stagedCards = [];
              const currentStaging = roomData.reward_staging || { cards: [], relics: [], items: [] };
              roomData = {
                ...roomData,
                awaiting_card: false,
                awaiting_next: true,
                reward_staging: { ...currentStaging, cards: [] }
              };
              break;
            }
            case 'select-relic': {
              stagedRelics = [relicChoice];
              const currentStaging = roomData.reward_staging || { cards: [], relics: [], items: [] };
              roomData = {
                ...roomData,
                awaiting_relic: true,
                relic_choices: [],
                reward_staging: { ...currentStaging, relics: [...stagedRelics] }
              };
              break;
            }
            case 'confirm-relic': {
              stagedRelics = [];
              const currentStaging = roomData.reward_staging || { cards: [], relics: [], items: [] };
              roomData = {
                ...roomData,
                awaiting_relic: false,
                awaiting_next: true,
                reward_staging: { ...currentStaging, relics: [] }
              };
              break;
            }
            case 'advance': {
              if (pending.phase === 'cards') {
                snapshot = snapshotFor('relics');
                const currentStaging = roomData.reward_staging || { cards: [], relics: [], items: [] };
                roomData = {
                  ...roomData,
                  awaiting_next: false,
                  awaiting_relic: false,
                  card_choices: [],
                  relic_choices: [relicChoice],
                  reward_staging: { ...currentStaging, cards: [], relics: [] }
                };
              } else if (pending.phase === 'relics') {
                snapshot = null;
                const currentStaging = roomData.reward_staging || { cards: [], relics: [], items: [] };
                roomData = {
                  ...roomData,
                  awaiting_next: false,
                  awaiting_relic: false,
                  relic_choices: [],
                  reward_staging: { ...currentStaging, cards: [], relics: [] }
                };
              }
              break;
            }
            default:
              break;
          }
        },
        validate: (pending) => {
          const next = compute();
          return Boolean(next) && actionsEqual(pending, next);
        },
        onSettled: () => {
          maybeHandle();
        }
      });
    }

    maybeHandle();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(executed).toEqual([
      'select-card',
      'confirm-card',
      'advance',
      'select-relic',
      'confirm-relic',
      'advance'
    ]);
    expect(scheduler.getPendingAction()).toBeNull();
  });

  test('actionsEqual treats confirm automation actions as type-only', () => {
    expect(actionsEqual({ type: 'confirm-card', phase: 'cards' }, { type: 'confirm-card' })).toBe(true);
    expect(actionsEqual({ type: 'confirm-relic', phase: 'relics' }, { type: 'confirm-card' })).toBe(false);
  });

  test('automation pauses battle review advances while combat is active', async () => {
    vi.useFakeTimers();
    try {
      let battleActive = true;
      const roomData = { awaiting_next: true };
      const snapshot = snapshotFor('battle_review');
      const action = computeAutomationAction({ roomData, snapshot });
      expect(action.type).toBe('advance');

      const scheduler = new RewardAutomationScheduler({
        getDelay: () => 0
      });
      const handleRewardAdvance = vi.fn(async () => {});
      const validate = vi.fn(() => !battleActive);

      scheduler.schedule(action, {
        execute: handleRewardAdvance,
        validate,
        onSettled: () => {}
      });

      expect(scheduler.getPendingAction()).toEqual(action);

      vi.runAllTimers();
      await Promise.resolve();

      expect(validate).toHaveBeenCalledTimes(1);
      expect(handleRewardAdvance).not.toHaveBeenCalled();
      expect(scheduler.getPendingAction()).toBeNull();

      // Simulate automation reset when combat starts.
      scheduler.cancel();

      battleActive = false;

      scheduler.schedule(action, {
        execute: handleRewardAdvance,
        validate,
        onSettled: () => {}
      });

      vi.runAllTimers();
      await Promise.resolve();

      expect(validate).toHaveBeenCalledTimes(2);
      expect(handleRewardAdvance).toHaveBeenCalledTimes(1);
      scheduler.cancel();
    } finally {
      vi.useRealTimers();
    }
  });
});
