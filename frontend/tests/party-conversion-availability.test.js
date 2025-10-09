import { describe, expect, test } from 'bun:test';
import { mergeUpgradePayload, shouldRefreshRoster } from '../src/lib/components/upgradeCacheUtils.js';
import { formatMaterialQuantity } from '../src/lib/utils/upgradeFormatting.js';

describe('upgrade cache merging', () => {
  test('updates stat counts and remaining materials', () => {
    const previousData = {
      items: { light_1: 12 },
      stat_counts: { atk: 3 },
      next_costs: { atk: { item: 'light_1', units: 4, breakdown: { light_1: 4 } } },
      element: 'light'
    };

    const result = {
      stat_counts: { atk: 4 },
      next_costs: { atk: { item: 'light_1', units: 5, breakdown: { light_1: 5 } } },
      materials_remaining: 9,
      materials_remaining_units: 9,
      element: 'light'
    };

    const merged = mergeUpgradePayload(previousData, result);
    expect(merged.stat_counts.atk).toBe(4);
    expect(merged.next_costs.atk.units).toBe(5);
    expect(merged.next_costs.atk.breakdown).toEqual({ light_1: 5 });
    expect(merged.items.light_1).toBe(9);
    expect(merged.materials_remaining).toBe(9);
    expect(merged.materials_remaining_units).toBe(9);
    expect(shouldRefreshRoster(result)).toBe(true);
  });

  test('drops stale higher-tier entries when backend aggregates', () => {
    const previousData = {
      items: {
        light_1: 2,
        light_2: 4,
        light_3: 1,
        fire_3: 7,
      },
      element: 'light'
    };

    const result = {
      materials_remaining: 6,
      materials_remaining_units: 10,
      element: 'light'
    };

    const merged = mergeUpgradePayload(previousData, result);
    expect(merged.items).toEqual({ light_1: 6, fire_3: 7 });
    expect(merged.materials_remaining).toBe(6);
    expect(merged.materials_remaining_units).toBe(10);
  });

  test('formats material quantities for hover text', () => {
    expect(formatMaterialQuantity(3, 'fire_1')).toBe('3× Fire 1★');
    expect(formatMaterialQuantity(0, 'light_1')).toBe('0× Light 1★');
  });
});
