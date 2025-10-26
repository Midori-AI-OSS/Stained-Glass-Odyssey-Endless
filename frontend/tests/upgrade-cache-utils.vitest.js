import { describe, expect, test } from 'vitest';

import { mergeUpgradePayload, simulateMaterialConsumption } from '../src/lib/components/upgradeCacheUtils.js';

describe('upgrade cache utilities', () => {
  test('simulateMaterialConsumption converts higher-tier shards when base stock is empty', () => {
    const inventory = {
      water_1: 0,
      water_2: 1
    };

    const outcome = simulateMaterialConsumption(inventory, 'water', 125);

    expect(outcome.fulfilled).toBe(true);
    expect(outcome.spentUnits).toBe(125);
    expect(outcome.consumed).toMatchObject({ water_2: 1 });
    expect(outcome.remaining.water_2).toBe(0);
    expect(outcome.remaining.water_1).toBe(0);
  });

  test('mergeUpgradePayload retains remaining higher-tier shards after spending', () => {
    const previous = {
      items: {
        water_1: 0,
        water_2: 3
      },
      stat_totals: {},
      stat_counts: {},
      next_costs: {},
      stat_upgrades: [],
      element: 'water'
    };

    const result = {
      element: 'water',
      materials_spent: 125,
      materials_remaining: 0,
      materials_remaining_units: 250
    };

    const merged = mergeUpgradePayload(previous, result);

    expect(merged.items.water_2).toBe(2);
    expect(merged.items.water_1).toBe(0);
    expect(merged.materials_remaining).toBe(0);
    expect(merged.materials_remaining_units).toBe(250);
  });
});
