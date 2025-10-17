import { describe, expect, test } from 'vitest';

import { formatRewardPreview, normalizeRewardPreview } from '../src/lib/utils/rewardPreviewFormatter.js';

describe('normalizeRewardPreview', () => {
  test('returns empty structure for invalid input', () => {
    const result = normalizeRewardPreview(null);
    expect(result).toEqual({ summary: null, stats: [], triggers: [] });
  });

  test('normalises summary, stats, and triggers', () => {
    const preview = {
      summary: '  Massive power boost  ',
      stats: [
        {
          stat: 'atk',
          mode: 'percent',
          amount: '12',
          total_amount: '24',
          previous_total: '12',
          stacks: 2,
          target: 'party'
        },
        null,
        { stat: '', amount: 5 }
      ],
      triggers: [
        { event: 'on_turn_start', description: 'Gain 1 energy.' },
        { event: '' }
      ]
    };

    const result = normalizeRewardPreview(preview);
    expect(result.summary).toBe('Massive power boost');
    expect(result.stats).toHaveLength(1);
    expect(result.stats[0]).toMatchObject({
      stat: 'atk',
      mode: 'percent',
      amount: 12,
      total_amount: 24,
      previous_total: 12,
      stacks: 2,
      target: 'party'
    });
    expect(result.triggers).toEqual([
      { event: 'on_turn_start', description: 'Gain 1 energy.' }
    ]);
  });
});

describe('formatRewardPreview', () => {
  test('formats fallback summary and stat deltas', () => {
    const preview = {
      summary: null,
      stats: [
        {
          stat: 'atk',
          mode: 'percent',
          amount: 12,
          total_amount: 24,
          previous_total: 12,
          stacks: 2,
          target: 'party'
        }
      ],
      triggers: [
        { event: 'on_turn_start', description: 'Gain 1 energy.' }
      ]
    };

    const formatted = formatRewardPreview(preview, { fallbackSummary: 'Boost attack output.' });
    expect(formatted.summary).toBe('Boost attack output.');
    expect(formatted.hasContent).toBe(true);
    expect(formatted.stats).toHaveLength(1);
    expect(formatted.stats[0]).toMatchObject({
      label: 'Attack',
      change: '+24% to Party'
    });
    expect(formatted.stats[0].details).toEqual(['Per stack +12%', 'Stacks 2', 'Previously +12%']);
    expect(formatted.triggers).toEqual([
      { id: 'on_turn_start-0', event: 'On Turn Start', description: 'Gain 1 energy.' }
    ]);
  });

  test('omits stats with unparseable values and preserves trigger text', () => {
    const preview = {
      summary: 'Applies a multiplier',
      stats: [
        {
          stat: 'damage_multiplier',
          mode: 'multiplier',
          amount: null,
          total_amount: 1.5,
          stacks: 1,
          target: 'foe'
        },
        {
          stat: 'invalid'
        }
      ],
      triggers: [
        { event: 'on_dot_tick' }
      ]
    };

    const formatted = formatRewardPreview(preview);
    expect(formatted.summary).toBe('Applies a multiplier');
    expect(formatted.stats).toHaveLength(1);
    expect(formatted.stats[0]).toMatchObject({
      label: 'Damage Multiplier',
      change: '×1.5 to Foes'
    });
    expect(formatted.triggers).toEqual([
      { id: 'on_dot_tick-0', event: 'On Dot Tick', description: null }
    ]);
  });
});
