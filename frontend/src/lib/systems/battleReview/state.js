import { derived, writable, get } from 'svelte/store';
import { getBattleSummary, getBattleEvents } from '../uiApi.js';

export const BATTLE_REVIEW_CONTEXT_KEY = Symbol('battle-review-context');

export const emptySummary = { damage_by_type: {} };

const defaultProps = {
  runId: '',
  battleIndex: 0,
  cards: [],
  relics: [],
  party: [],
  foes: [],
  partyData: [],
  foeData: [],
  reducedMotion: false,
  prefetchedSummary: null
};

function cloneEntity(entity) {
  if (!entity || typeof entity !== 'object') {
    const id = typeof entity === 'string' ? entity : '';
    return id ? { id } : null;
  }
  return { ...entity };
}

export function normalizeEntity(entity, summary = emptySummary) {
  if (!entity) return null;
  const base = cloneEntity(entity);
  if (!base) return null;
  const id = base.id || '';
  const totals = summary?.damage_by_type?.[id] || {};
  const element = base.element || primaryElementFromTotals(totals) || 'Generic';
  const hp = Number.isFinite(base.hp) ? base.hp : 1;
  const maxHp = Number.isFinite(base.max_hp) && base.max_hp > 0 ? base.max_hp : 1;
  return {
    ...base,
    id,
    element,
    hp,
    max_hp: maxHp,
    dots: Array.isArray(base.dots) ? base.dots : [],
    hots: Array.isArray(base.hots) ? base.hots : [],
    active_effects: Array.isArray(base.active_effects) ? base.active_effects : [],
    shields: Number.isFinite(base.shields) ? base.shields : 0
  };
}

function primaryElementFromTotals(totals) {
  const entries = Object.entries(totals || {});
  if (!entries.length) return 'Generic';
  return entries.sort((a, b) => (b[1] || 0) - (a[1] || 0))[0][0];
}

export function deriveDisplayParty(props, summary) {
  const fromProps = Array.isArray(props.partyData) && props.partyData.length
    ? props.partyData
    : Array.isArray(props.party) && props.party.length
      ? props.party.map((member) => (typeof member === 'object' ? { ...member } : { id: member }))
      : [];
  if (fromProps.length) {
    return fromProps.map((entity) => normalizeEntity(entity, summary)).filter(Boolean);
  }
  const fallback = Array.isArray(summary?.party_members) ? summary.party_members : [];
  return fallback.map((id) => normalizeEntity({ id }, summary)).filter(Boolean);
}

export function deriveDisplayFoes(props, summary) {
  const fromProps = Array.isArray(props.foeData) && props.foeData.length
    ? props.foeData
    : Array.isArray(props.foes) && props.foes.length
      ? props.foes.map((foe) => (typeof foe === 'object' ? { ...foe } : { id: foe }))
      : [];
  if (fromProps.length) {
    return fromProps.map((entity) => normalizeEntity(entity, summary)).filter(Boolean);
  }
  const fallback = Array.isArray(summary?.foes) ? summary.foes : [];
  return fallback.map((id) => normalizeEntity({ id }, summary)).filter(Boolean);
}

export function aggregateDamageByType(summary = emptySummary) {
  const totals = {};
  const by = summary?.damage_by_type || {};
  for (const types of Object.values(by)) {
    for (const [element, amount] of Object.entries(types || {})) {
      totals[element] = (totals[element] || 0) + (amount || 0);
    }
  }
  return totals;
}

export function aggregateActions(summary = emptySummary) {
  const totals = {};
  const byAction = summary?.damage_by_action || {};
  for (const actions of Object.values(byAction)) {
    for (const [action, amount] of Object.entries(actions || {})) {
      totals[action] = (totals[action] || 0) + (amount || 0);
    }
  }
  return totals;
}

function aggregateObjectTotals(obj) {
  return Object.values(obj || {}).reduce((acc, value) => acc + (value || 0), 0);
}

function aggregateNestedTotals(obj) {
  return Object.values(obj || {}).reduce((acc, inner) => {
    for (const [key, amount] of Object.entries(inner || {})) {
      acc[key] = (acc[key] || 0) + (amount || 0);
    }
    return acc;
  }, {});
}

export function computeEntityMetrics(summary = emptySummary, entityId = 'overview') {
  if (entityId === 'overview') {
    return {
      damage: aggregateDamageByType(summary),
      actions: aggregateActions(summary),
      criticals: aggregateObjectTotals(summary?.critical_hits || {}),
      criticalDamage: aggregateObjectTotals(summary?.critical_damage || {}),
      shieldAbsorbed: aggregateObjectTotals(summary?.shield_absorbed || {}),
      dotDamage: aggregateObjectTotals(summary?.dot_damage || {}),
      hotHealing: aggregateObjectTotals(summary?.hot_healing || {}),
      resourcesSpent: aggregateNestedTotals(summary?.resources_spent || {}),
      resourcesGained: aggregateNestedTotals(summary?.resources_gained || {}),
      tempHpGranted: aggregateObjectTotals(summary?.temporary_hp_granted || {}),
      kills: aggregateObjectTotals(summary?.kills || {}),
      dotKills: aggregateObjectTotals(summary?.dot_kills || {}),
      ultimatesUsed: aggregateObjectTotals(summary?.ultimates_used || {}),
      ultimateFailures: aggregateObjectTotals(summary?.ultimate_failures || {}),
      healingPrevented: aggregateObjectTotals(summary?.healing_prevented || {})
    };
  }

  return {
    damage: summary?.damage_by_type?.[entityId] || {},
    actions: summary?.damage_by_action?.[entityId] || {},
    criticals: summary?.critical_hits?.[entityId] || 0,
    criticalDamage: summary?.critical_damage?.[entityId] || 0,
    shieldAbsorbed: summary?.shield_absorbed?.[entityId] || 0,
    dotDamage: summary?.dot_damage?.[entityId] || 0,
    hotHealing: summary?.hot_healing?.[entityId] || 0,
    resourcesSpent: summary?.resources_spent?.[entityId] || {},
    resourcesGained: summary?.resources_gained?.[entityId] || {},
    tempHpGranted: summary?.temporary_hp_granted?.[entityId] || 0,
    kills: summary?.kills?.[entityId] || 0,
    dotKills: summary?.dot_kills?.[entityId] || 0,
    ultimatesUsed: summary?.ultimates_used?.[entityId] || 0,
    ultimateFailures: summary?.ultimate_failures?.[entityId] || 0,
    healingPrevented: summary?.healing_prevented?.[entityId] || 0
  };
}

export function buildAvailableTabs(partyList = [], foeList = []) {
  const tabs = [{ id: 'overview', label: 'Overview', type: 'overview' }];
  for (const member of partyList) {
    if (member?.id) {
      tabs.push({
        id: member.id,
        label: member.name || member.id,
        type: 'party',
        entity: member
      });
    }
  }
  for (const foe of foeList) {
    if (foe?.id) {
      tabs.push({
        id: foe.id,
        label: foe.name || foe.id,
        type: 'foe',
        entity: foe,
        rank: foe.rank || null
      });
    }
  }
  return tabs;
}

function computeOutgoingMap(list) {
  const map = new Map();
  const push = (sourceId, bucket, effect) => {
    if (!sourceId) return;
    const entry = map.get(sourceId) || { dots: [], hots: [], buffs: [] };
    entry[bucket].push(effect);
    map.set(sourceId, entry);
  };

  for (const entity of list) {
    const dots = Array.isArray(entity?.dots) ? entity.dots : [];
    const hots = Array.isArray(entity?.hots) ? entity.hots : [];
    const buffs = Array.isArray(entity?.active_effects) ? entity.active_effects : [];
    for (const dot of dots) push(dot.source, 'dots', dot);
    for (const hot of hots) push(hot.source, 'hots', hot);
    for (const buff of buffs) push(buff.source, 'buffs', buff);
  }
  return map;
}

function toTimelineEvent(event, index) {
  return {
    id: `${event?.event_id ?? index}`,
    label: event?.event_type || 'event',
    attacker: event?.attacker_id || null,
    target: event?.target_id || null,
    amount: event?.amount ?? null,
    damageType: event?.damage_type || null,
    sourceType: event?.source_type || null,
    time: event?.timestamp ?? event?.time_seconds ?? index
  };
}

export function createBattleReviewState(initialProps = {}) {
  const props = writable({ ...defaultProps, ...initialProps });
  const summary = writable(initialProps.prefetchedSummary || emptySummary);
  const summaryStatus = writable(initialProps.prefetchedSummary ? 'ready' : 'idle');
  const events = writable([]);
  const eventsStatus = writable('idle');
  const eventsOpen = writable(false);

  let lastKey = '';
  let currentToken = 0;

  async function loadSummary(battleIndex) {
    const token = ++currentToken;
    summaryStatus.set('loading');
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    for (let attempt = 0; attempt < 10; attempt++) {
      try {
        const res = await getBattleSummary(battleIndex);
        if (currentToken !== token) {
          return;
        }
        summary.set(res || emptySummary);
        summaryStatus.set('ready');
        return;
      } catch (err) {
        if (err?.status !== 404) {
          summaryStatus.set('error');
          return;
        }
      }
      await sleep(attempt < 5 ? 400 : 800);
    }
    if (currentToken === token) {
      summaryStatus.set('error');
    }
  }

  function handlePropsChange(value) {
    const key = value.runId && value.battleIndex > 0 ? `${value.runId}|${value.battleIndex}` : '';
    if (!key) {
      lastKey = '';
      summary.set(emptySummary);
      summaryStatus.set('idle');
      return;
    }
    if (value.prefetchedSummary) {
      summary.set(value.prefetchedSummary || emptySummary);
      summaryStatus.set('ready');
      lastKey = key;
      return;
    }
    if (key !== lastKey) {
      lastKey = key;
      summary.set(emptySummary);
      loadSummary(value.battleIndex);
    }
  }

  let stop = props.subscribe(handlePropsChange);

  function updateProps(next) {
    props.update((prev) => ({ ...prev, ...next }));
  }

  async function loadEvents() {
    const { battleIndex } = get(props);
    if (!battleIndex) return;
    eventsStatus.set('loading');
    try {
      const data = await getBattleEvents(battleIndex);
      events.set(Array.isArray(data) ? data : []);
      eventsStatus.set('ready');
    } catch (err) {
      eventsStatus.set('error');
    }
  }

  function setEventsOpen(value) {
    eventsOpen.set(Boolean(value));
  }

  function toggleEvents() {
    const shouldOpen = !get(eventsOpen);
    eventsOpen.set(shouldOpen);
    if (shouldOpen && get(eventsStatus) === 'idle') {
      loadEvents();
    }
  }

  const reducedMotion = derived(props, ($props) => Boolean($props.reducedMotion));
  const displayParty = derived([props, summary], ([$props, $summary]) => deriveDisplayParty($props, $summary));
  const displayFoes = derived([props, summary], ([$props, $summary]) => deriveDisplayFoes($props, $summary));
  const outgoingBySource = derived([displayParty, displayFoes], ([$party, $foes]) =>
    computeOutgoingMap([...$party, ...$foes])
  );

  const availableTabs = derived([displayParty, displayFoes], ([$party, $foes]) => buildAvailableTabs($party, $foes));

  const activeTab = writable('overview');

  const currentTab = derived([availableTabs, activeTab], ([$tabs, $active]) =>
    $tabs.find((tab) => tab.id === $active) || $tabs[0]
  );

  const entityMetrics = derived([summary, activeTab], ([$summary, $active]) => computeEntityMetrics($summary, $active));
  const overviewTotals = derived(summary, ($summary) => aggregateDamageByType($summary));
  const overviewGrand = derived(overviewTotals, ($totals) => Object.values($totals || {}).reduce((acc, cur) => acc + (cur || 0), 0));

  const timeline = derived(events, ($events) => {
    if (!Array.isArray($events) || !$events.length) return [];
    return $events.slice(-200).map(toTimelineEvent);
  });

  const resultSummary = derived(summary, ($summary) => ({
    result: $summary?.result || '—',
    duration: Number.isFinite($summary?.duration_seconds) ? Math.round($summary.duration_seconds) : null,
    eventCount: $summary?.event_count || ($summary?.events?.length || 0)
  }));

  function destroy() {
    stop?.();
    events.set([]);
  }

  return {
    props,
    summary,
    summaryStatus,
    events,
    eventsStatus,
    eventsOpen,
    reducedMotion,
    displayParty,
    displayFoes,
    outgoingBySource,
    availableTabs,
    activeTab,
    currentTab,
    entityMetrics,
    overviewTotals,
    overviewGrand,
    timeline,
    resultSummary,
    updateProps,
    loadEvents,
    toggleEvents,
    setEventsOpen,
    destroy
  };
}
