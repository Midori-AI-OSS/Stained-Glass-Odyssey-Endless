import { describe, expect, test } from 'bun:test';
import {
  parseBattleReviewSearchParams,
  buildBattleReviewSearchParams,
  buildBattleReviewLink
} from '../src/lib/systems/battleReview/urlState.js';

describe('battle review URL state helpers', () => {
  test('parses parameters and sanitizes values', () => {
    const params = new URLSearchParams(
      'battle=4&tab=hero!!&filters=crit,dot,,crit&compare=a,b,c&pins=pin1:100,pin2&window=3.1:9.9'
    );
    const state = parseBattleReviewSearchParams(params);
    expect(state.battleIndex).toBe(4);
    expect(state.tab).toBe('hero');
    expect(state.filters).toEqual(['crit', 'dot']);
    expect(state.comparison).toEqual(['a', 'b', 'c']);
    expect(state.pins).toEqual(['pin1:100', 'pin2']);
    expect(state.window).toEqual({ start: 3.1, end: 9.9 });
  });

  test('serializes state while omitting defaults', () => {
    const params = buildBattleReviewSearchParams({
      battleIndex: 3,
      tab: 'overview',
      filters: ['crit'],
      comparison: [],
      pins: ['pinA'],
      window: { start: 12.3456, end: 18.9999 }
    });
    expect(params.get('battle')).toBe('3');
    expect(params.get('tab')).toBeNull();
    expect(params.get('filters')).toBe('crit');
    expect(params.get('compare')).toBeNull();
    expect(params.get('pins')).toBe('pinA');
    expect(params.get('window')).toBe('12.346:19');
  });

  test('builds shareable links with encoded run id', () => {
    const link = buildBattleReviewLink('Run 42', { battleIndex: 2, tab: 'hero' }, { origin: 'https://example.com' });
    expect(link).toBe('https://example.com/logs/Run42?battle=2&tab=hero');
  });
});
