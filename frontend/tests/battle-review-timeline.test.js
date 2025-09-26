import { describe, expect, test } from 'bun:test';
import { get } from 'svelte/store';
import {
  createBattleReviewState
} from '../src/lib/systems/battleReview/state.js';

function buildState() {
  const summary = {
    result: 'victory',
    duration_seconds: 15,
    party_members: ['hero', 'healer'],
    foes: ['foe']
  };
  return createBattleReviewState({
    runId: 'run-1',
    battleIndex: 7,
    prefetchedSummary: summary,
    partyData: [
      { id: 'hero', name: 'Hero Prime' },
      { id: 'healer', name: 'Aria' }
    ],
    foeData: [{ id: 'foe', name: 'Training Dummy' }]
  });
}

describe('battle review timeline projection', () => {
  test('applies metric, entity, and source filters', () => {
    const state = buildState();
    state.events.set([
      { event_id: 1, event_type: 'damage_dealt', attacker_id: 'hero', target_id: 'foe', amount: 420, timestamp: 1 },
      { event_id: 2, event_type: 'damage_dealt', attacker_id: 'healer', target_id: 'foe', amount: 120, timestamp: 1.4 },
      { event_id: 3, event_type: 'heal', attacker_id: 'healer', target_id: 'hero', amount: 220, source_type: 'skill', timestamp: 2.6 },
      { event_id: 4, event_type: 'shield_absorbed', target_id: 'hero', amount: 160, source_type: 'barrier', timestamp: 3.2 }
    ]);

    state.setTimelineFilters({ metric: 'damageDone', entities: ['hero'] });
    const damageTimeline = get(state.timeline);
    expect(damageTimeline.filteredEvents.map((event) => event.attacker)).toEqual(['hero']);

    state.setTimelineFilters({ metric: 'healing', sourceTypes: ['skill'] });
    const healingTimeline = get(state.timeline);
    expect(healingTimeline.filteredEvents).toHaveLength(1);
    expect(healingTimeline.filteredEvents[0].eventType).toBe('heal');

    state.destroy();
  });

  test('focus entity highlights and shareable filters encode state', () => {
    const state = buildState();
    state.events.set([
      { event_id: 10, event_type: 'damage_dealt', attacker_id: 'hero', target_id: 'foe', amount: 500, source_type: 'ultimate', timestamp: 1.1 },
      { event_id: 11, event_type: 'damage_taken', attacker_id: 'foe', target_id: 'hero', amount: 300, timestamp: 1.3 },
      { event_id: 12, event_type: 'shield_absorbed', target_id: 'hero', amount: 90, timestamp: 2.7 }
    ]);

    state.activeTab.set('hero');
    state.setTimelineFilters({ metric: 'damageDone' });
    const projection = get(state.timeline);
    expect(projection.focusId).toBe('hero');
    expect(projection.highlightEvents).toHaveLength(1);

    state.setTimelineFilters({ metric: 'mitigation', eventTypes: ['shield_absorbed'], respectMotion: false });
    const shareable = get(state.shareableState);
    expect(shareable.filters).toContain('metric:mitigation');
    expect(shareable.filters).toContain('event:shield_absorbed');
    expect(shareable.filters).toContain('motion:allow');

    state.destroy();
  });

  test('timeline cursor clamps within active window', () => {
    const state = buildState();
    state.events.set([
      { event_id: 20, event_type: 'damage_dealt', attacker_id: 'hero', target_id: 'foe', amount: 200, timestamp: 0.5 },
      { event_id: 21, event_type: 'heal', attacker_id: 'healer', target_id: 'hero', amount: 150, timestamp: 4.2 }
    ]);

    state.setTimeWindow({ start: 0.5, end: 2 });
    state.setTimelineCursor({ time: 6 });
    expect(get(state.timelineCursor).time).toBeCloseTo(2, 5);

    state.setTimelineCursor({ time: -5 });
    expect(get(state.timelineCursor).time).toBeCloseTo(0.5, 5);

    state.destroy();
  });
});
