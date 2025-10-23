import { describe, expect, test } from 'vitest';

import { resolveRewardStagingPayload } from '../src/lib/utils/rewardStagingPayload.js';

describe('resolveRewardStagingPayload', () => {
  test('clears staged card bucket when confirm response omits updates', () => {
    const current = {
      cards: [
        {
          id: 'radiant-beam',
          preview: { label: 'Radiant Beam', rarity: 4 }
        }
      ],
      relics: [{ id: 'lucky-pendant' }],
      items: []
    };

    const resolved = resolveRewardStagingPayload({
      current,
      next: undefined,
      type: 'card',
      intent: 'confirm'
    });

    expect(resolved.cards).toEqual([]);
    expect(resolved.relics).toEqual(current.relics);
    expect(resolved.relics).not.toBe(current.relics);
  });

  test('clones incoming staging payloads from the server', () => {
    const next = {
      cards: [
        {
          id: 'aurora-strike',
          preview: { id: 'aurora-strike', label: 'Aurora Strike', stars: 3 }
        }
      ],
      relics: [],
      items: []
    };

    const resolved = resolveRewardStagingPayload({
      current: { cards: [], relics: [], items: [] },
      next,
      type: 'card',
      intent: 'select'
    });

    expect(resolved.cards).not.toBe(next.cards);
    expect(resolved.cards).toHaveLength(1);
    expect(resolved.cards[0]).not.toBe(next.cards[0]);
    expect(resolved.cards[0]).toMatchObject({ id: 'aurora-strike' });
    expect(resolved.cards[0]?.preview).not.toBe(next.cards[0]?.preview);
    expect(resolved.cards[0]?.preview).toMatchObject({ summary: null });
    expect(Array.isArray(resolved.cards[0]?.preview?.stats)).toBe(true);
  });
});
