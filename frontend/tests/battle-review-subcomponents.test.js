import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

const damageGraphs = readFileSync(join(import.meta.dir, '../src/lib/components/battle-review/DamageGraphs.svelte'), 'utf8');
const rewardList = readFileSync(join(import.meta.dir, '../src/lib/components/battle-review/RewardList.svelte'), 'utf8');
const reviewOverlay = readFileSync(join(import.meta.dir, '../src/lib/components/battle-review/ReviewOverlay.svelte'), 'utf8');

describe('battle review subcomponents', () => {
  test('DamageGraphs renders rows', () => {
    expect(damageGraphs).toContain('damage-graphs');
  });
  test('RewardList uses reward components', () => {
    expect(rewardList).toContain('RewardCard');
    expect(rewardList).toContain('CurioChoice');
  });
  test('ReviewOverlay composes parts', () => {
    expect(reviewOverlay).toContain('DamageGraphs');
    expect(reviewOverlay).toContain('RewardList');
  });
});
