import { beforeEach, describe, expect, test } from 'bun:test';
import {
  createRewardPhaseController,
  normalizeRewardProgression
} from '../src/lib/systems/rewardProgression.js';
import {
  fourPhaseProgression,
  singlePhaseProgression,
  skipCardsProgression
} from './__fixtures__/rewardProgressionPayloads.js';

describe('reward phase controller', () => {
  let controller;
  let logs;

  beforeEach(() => {
    logs = [];
    controller = createRewardPhaseController({
      logger: (...args) => {
        logs.push(args);
      }
    });
    controller.reset();
  });

  test('ingests canonical progression payloads', () => {
    const snapshot = controller.ingest(
      fourPhaseProgression({
        available: ['cards', 'drops', 'relics'],
        completed: ['drops'],
        current_step: 'cards'
      })
    );

    expect(snapshot.sequence).toEqual(['drops', 'cards', 'relics']);
    expect(snapshot.completed).toEqual(['drops']);
    expect(snapshot.current).toBe('cards');
    expect(snapshot.next).toBe('relics');
  });

  test('falls back to hinted phases when payload missing', () => {
    const snapshot = controller.ingest(null, {
      hints: { fallbackPhases: ['cards', 'battle_review'] }
    });

    expect(snapshot.sequence).toEqual(['cards', 'battle_review']);
    expect(snapshot.current).toBe('cards');
    expect(snapshot.next).toBe('battle_review');
  });

  test('advance completes the current phase and moves forward', () => {
    controller.ingest(fourPhaseProgression({ available: ['drops', 'cards', 'relics'] }));

    const advanced = controller.advance();
    expect(advanced.completed).toEqual(['drops']);
    expect(advanced.current).toBe('cards');
    expect(advanced.next).toBe('relics');
  });

  test('skipTo marks earlier phases completed and focuses the target', () => {
    controller.ingest(fourPhaseProgression({ available: ['drops', 'cards', 'relics'] }));

    const snapshot = controller.skipTo('relics');
    expect(snapshot.completed).toEqual(['drops', 'cards']);
    expect(snapshot.current).toBe('relics');
    expect(snapshot.next).toBeNull();
  });

  test('emits enter and exit events on phase transitions', () => {
    const enters = [];
    const exits = [];
    controller.on('enter', (detail) => enters.push(detail.phase));
    controller.on('exit', (detail) => exits.push(detail.phase));

    controller.ingest(fourPhaseProgression({ available: ['drops', 'cards', 'relics'] }));
    controller.advance();

    expect(exits).toEqual(['drops']);
    expect(enters).toContain('cards');
  });

  test('ingesting skipCardsProgression enters relics without logging warnings', () => {
    const snapshot = controller.ingest(skipCardsProgression());

    expect(snapshot.sequence).toEqual(['drops', 'relics', 'battle_review']);
    expect(snapshot.current).toBe('relics');
    expect(snapshot.next).toBe('battle_review');
    expect(logs).toEqual([]);
  });

  test('singlePhaseProgression advance completes the final phase', () => {
    controller.ingest(singlePhaseProgression());

    const advanced = controller.advance();
    expect(advanced.completed).toEqual(['battle_review']);
    expect(advanced.current).toBeNull();
  });
});

describe('normalizeRewardProgression', () => {
  test('orders phases according to the canonical sequence', () => {
    const snapshot = normalizeRewardProgression(
      fourPhaseProgression({ available: ['battle_review', 'drops'] }),
      { logger: () => {} }
    );

    expect(snapshot.sequence).toEqual(['drops', 'battle_review']);
    expect(snapshot.current).toBe('drops');
  });

  test('skipCardsProgression jumps directly to relics without diagnostics', () => {
    const snapshot = normalizeRewardProgression(skipCardsProgression(), { logger: () => {} });

    expect(snapshot.sequence).toEqual(['drops', 'relics', 'battle_review']);
    expect(snapshot.current).toBe('relics');
    expect(snapshot.diagnostics).toEqual([]);
  });

  test('singlePhaseProgression marks battle review as the only phase', () => {
    const snapshot = normalizeRewardProgression(singlePhaseProgression(), { logger: () => {} });

    expect(snapshot.sequence).toEqual(['battle_review']);
    expect(snapshot.current).toBe('battle_review');
    expect(snapshot.next).toBeNull();
  });
});
