import { describe, expect, test } from 'bun:test';
import { mergeUpgradePayload, shouldRefreshRoster } from '../src/lib/components/upgradeCacheUtils.js';

function computeAvailableFour(items, selected, elementName) {
  const starSuffix = '_4';
  const elementKey = String(elementName || 'generic').toLowerCase();
  const entries = Object.entries(items || {});
  if (selected?.is_player) {
    return entries
      .filter(([key]) => key.endsWith(starSuffix))
      .reduce((acc, [, qty]) => acc + (Number(qty) || 0), 0);
  }
  const key = `${elementKey}${starSuffix}`;
  return Number(items?.[key]) || 0;
}

describe('upgrade cache merging', () => {
  test('immediately exposes updated four-star availability after conversion', () => {
    const previousData = {
      items: { light_4: 2 },
      total_points: 5,
      upgrade_points: 5
    };

    const result = {
      items: { light_4: 1 },
      total_points: 10,
      upgrade_points: 10
    };

    const merged = mergeUpgradePayload(previousData, result);
    expect(merged.items.light_4).toBe(1);
    expect(merged.total_points).toBe(10);
    expect(merged.upgrade_points).toBe(10);
    expect(shouldRefreshRoster(result)).toBe(false);

    const selected = { is_player: true };
    const available = computeAvailableFour(merged.items, selected, 'Light');
    expect(available).toBe(1);
    const canConvert = available >= 1;
    expect(canConvert).toBe(true);
  });
});
