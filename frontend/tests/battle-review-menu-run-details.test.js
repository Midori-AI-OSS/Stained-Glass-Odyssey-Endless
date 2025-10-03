import { describe, expect, test } from 'bun:test';

import { deriveFightsFromRunDetails } from '../src/lib/components/battle-review/battleReviewMenuHelpers.js';

describe('deriveFightsFromRunDetails', () => {
  test('creates fight entries from battles array', () => {
    const details = {
      battles: [
        { battle_index: 1, battle_name: 'Opening Gambit' },
        { battle_index: 2, room_name: 'Courtyard Clash' },
      ],
    };

    const fights = deriveFightsFromRunDetails(details);

    expect(fights.map((fight) => fight.battleIndex)).toEqual([1, 2]);
    expect(fights.map((fight) => fight.label)).toEqual([
      'Opening Gambit',
      'Courtyard Clash',
    ]);
  });

  test('honors legacy battle_summaries payloads', () => {
    const details = {
      battle_summaries: [
        { battleIndex: '3', roomType: 'Elite Duel' },
      ],
    };

    const fights = deriveFightsFromRunDetails(details);

    expect(fights.length).toBe(1);
    expect(fights[0].battleIndex).toBe(3);
    expect(fights[0].label).toBe('Elite Duel');
  });

  test('returns an empty array when no battles are present', () => {
    expect(deriveFightsFromRunDetails({ battles: [] })).toEqual([]);
    expect(deriveFightsFromRunDetails(null)).toEqual([]);
  });
});
