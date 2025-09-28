import { describe, expect, test } from 'bun:test';
import { get } from 'svelte/store';
import { readFileSync } from 'fs';
import { join } from 'path';
import {
  createBattleReviewState,
  aggregateDamageByType
} from '../src/lib/systems/battleReview/state.js';

const tabsShell = readFileSync(join(import.meta.dir, '../src/lib/components/battle-review/TabsShell.svelte'), 'utf8');

function sampleSummary() {
  return {
    result: 'victory',
    duration_seconds: 42,
    party_members: ['hero'],
    foes: ['boss'],
    damage_by_type: {
      hero: { Fire: 1200, Ice: 300 },
      boss: { Dark: 900 }
    },
    damage_by_action: {
      hero: { 'Normal Attack': 600, 'Fire Ultimate': 900 },
      boss: { 'Dark Ultimate': 900 }
    },
    critical_hits: { hero: 4 },
    critical_damage: { hero: 320 },
    shield_absorbed: { hero: 120 },
    dot_damage: { hero: 55 },
    hot_healing: { hero: 35 },
    resources_spent: { hero: { Mana: 20 } },
    resources_gained: { hero: { Mana: 10 } },
    temporary_hp_granted: { hero: 15 },
    kills: { hero: 2 },
    dot_kills: { hero: 1 },
    ultimates_used: { hero: 1 },
    ultimate_failures: { hero: 0 },
    healing_prevented: { hero: 11 }
  };
}

describe('battle review store architecture', () => {
  test('derive tabs, metrics, and timeline entries', () => {
    const summary = sampleSummary();
    const state = createBattleReviewState({
      runId: 'run-01',
      battleIndex: 3,
      prefetchedSummary: summary,
      partyData: [{ id: 'hero', name: 'Hero Prime', element: 'Fire' }],
      foeData: [{ id: 'boss', name: 'Boss Omega', element: 'Dark', rank: 'S' }]
    });

    const tabs = get(state.availableTabs);
    expect(tabs.map((tab) => tab.id)).toEqual(['overview', 'hero', 'boss']);
    expect(tabs[1].entity.element).toBe('Fire');

    // Overview metrics should aggregate totals across entities.
    const overviewDamage = aggregateDamageByType(summary);
    expect(overviewDamage.Fire).toBe(1200);

    // Switching the active tab exposes entity-specific metrics.
    state.activeTab.set('hero');
    const heroMetrics = get(state.entityMetrics);
    expect(heroMetrics.damage.Fire).toBe(1200);
    expect(heroMetrics.actions['Fire Ultimate']).toBe(900);

    // Loading events should update the timeline projection.
    state.events.set([
      {
        event_id: 1,
        event_type: 'damage_dealt',
        attacker_id: 'hero',
        target_id: 'boss',
        amount: 500,
        timestamp: 1.2,
        details: { action_name: 'Normal Attack' }
      },
      {
        event_id: 2,
        event_type: 'damage_dealt',
        attacker_id: 'hero',
        target_id: 'boss',
        amount: 700,
        timestamp: 6.8,
        details: { action_name: 'Ultimate' }
      }
    ]);
    const timeline = get(state.timeline);
    expect(timeline.events).toHaveLength(2);
    expect(timeline.events[1].abilityName).toBe('Ultimate');
    expect(timeline.events[1].action.summary).toBe('Ultimate');

    state.destroy();
  });
});

describe('battle review shell layout', () => {
  test('tabs shell stacks timeline below metrics', () => {
    expect(tabsShell).toContain('content-stack');
    expect(tabsShell).toContain('timeline-wrapper');
    expect(tabsShell).toContain('<TimelineRegion />');
    expect(tabsShell).toContain('<EntityTableContainer />');
  });
});
