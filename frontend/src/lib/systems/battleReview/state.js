import { derived, get, readable, writable } from 'svelte/store';
import { getBattleSummary, getBattleEvents } from '../uiApi.js';
import { buildBattleReviewSearchParams } from './urlState.js';

export const BATTLE_REVIEW_CONTEXT_KEY = Symbol('battle-review-context');

export const emptySummary = { damage_by_type: {} };

export const TIMELINE_METRICS = Object.freeze([
  {
    id: 'damageDone',
    label: 'Damage Done',
    color: '#f97316',
    eventTypes: new Set(['damage_dealt', 'dot_tick', 'critical_hit']),
    role: 'attacker'
  },
  {
    id: 'damageTaken',
    label: 'Damage Taken',
    color: '#38bdf8',
    eventTypes: new Set(['damage_taken']),
    role: 'target'
  },
  {
    id: 'healing',
    label: 'Healing',
    color: '#22c55e',
    eventTypes: new Set(['heal', 'hot_tick']),
    role: 'attacker'
  },
  {
    id: 'mitigation',
    label: 'Mitigation',
    color: '#c084fc',
    eventTypes: new Set(['shield_absorbed', 'temporary_hp_granted', 'healing_prevented']),
    role: 'target'
  }
]);

const TIMELINE_METRIC_LOOKUP = new Map(TIMELINE_METRICS.map((metric) => [metric.id, metric]));
const FILTER_ID_PATTERN = /[^a-z0-9._:-]/gi;

export function createDefaultTimelineFilters(respectReducedMotion = true) {
  return {
    metric: 'damageDone',
    entities: [],
    sourceTypes: [],
    eventTypes: [],
    respectMotion: Boolean(respectReducedMotion)
  };
}

function sanitizeFilterId(value) {
  if (value == null) return '';
  return String(value).replace(FILTER_ID_PATTERN, '').slice(0, 64);
}

function uniqueFilterList(values = []) {
  const seen = new Set();
  const out = [];
  const list = Array.isArray(values) ? values : [values];
  for (const value of list) {
    const id = sanitizeFilterId(value);
    if (!id || seen.has(id)) continue;
    seen.add(id);
    out.push(id);
  }
  return out;
}

function normalizeTimelineFilters(filters = {}, respectReducedMotion = true) {
  const defaults = createDefaultTimelineFilters(respectReducedMotion);
  const metricId = sanitizeFilterId(filters.metric);
  const metric = TIMELINE_METRIC_LOOKUP.has(metricId) ? metricId : defaults.metric;
  return {
    metric,
    entities: uniqueFilterList(filters.entities),
    sourceTypes: uniqueFilterList(filters.sourceTypes),
    eventTypes: uniqueFilterList(filters.eventTypes),
    respectMotion: filters.respectMotion === false ? false : defaults.respectMotion
  };
}

function encodeTimelineFilters(filters = createDefaultTimelineFilters(), { includeDefaults = false } = {}) {
  const normalized = normalizeTimelineFilters(filters, filters?.respectMotion ?? true);
  const tokens = [];
  if (includeDefaults || normalized.metric !== 'damageDone') {
    tokens.push(`metric:${sanitizeFilterId(normalized.metric)}`);
  }
  for (const id of normalized.entities) {
    tokens.push(`entity:${sanitizeFilterId(id)}`);
  }
  for (const id of normalized.sourceTypes) {
    tokens.push(`source:${sanitizeFilterId(id)}`);
  }
  for (const id of normalized.eventTypes) {
    tokens.push(`event:${sanitizeFilterId(id)}`);
  }
  if (!normalized.respectMotion) {
    tokens.push('motion:allow');
  } else if (includeDefaults) {
    tokens.push('motion:respect');
  }
  return tokens;
}

function decodeTimelineFilters(tokens, respectReducedMotion = true) {
  const defaults = createDefaultTimelineFilters(respectReducedMotion);
  if (!Array.isArray(tokens)) {
    return defaults;
  }
  const next = {
    metric: defaults.metric,
    entities: [],
    sourceTypes: [],
    eventTypes: [],
    respectMotion: defaults.respectMotion
  };
  for (const token of tokens) {
    if (typeof token !== 'string') continue;
    const [prefix, rawValue] = token.split(':', 2);
    if (prefix === 'motion') {
      next.respectMotion = rawValue === 'allow' ? false : true;
      continue;
    }
    const value = sanitizeFilterId(rawValue);
    if (!value) continue;
    if (prefix === 'metric' && TIMELINE_METRIC_LOOKUP.has(value)) {
      next.metric = value;
    } else if (prefix === 'entity') {
      next.entities.push(value);
    } else if (prefix === 'source') {
      next.sourceTypes.push(value);
    } else if (prefix === 'event') {
      next.eventTypes.push(value);
    }
  }
  return normalizeTimelineFilters(next, next.respectMotion);
}

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

function parseEventSeconds(event, index, ref) {
  if (!event) return index;
  const explicit = Number(event.time_seconds ?? event.timestamp ?? event.time);
  if (Number.isFinite(explicit)) {
    return explicit;
  }
  const rawTimestamp = event.timestamp || event.time;
  if (typeof rawTimestamp === 'string') {
    const ms = Date.parse(rawTimestamp);
    if (!Number.isNaN(ms)) {
      if (ref.base == null) {
        ref.base = ms;
      }
      return (ms - ref.base) / 1000;
    }
  }
  return index;
}

function resolveAbilityName(event) {
  if (!event) return 'event';
  const candidates = [
    event.source_name,
    event?.details?.action_name,
    event?.details?.name,
    event?.effect_details?.name,
    event.event_type
  ];
  for (const candidate of candidates) {
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim();
    }
  }
  return 'event';
}

function buildActionMetadata(event, abilityName) {
  if (!event) {
    return null;
  }

  const details = (event && typeof event.details === 'object' && event.details) || {};
  const effectDetails = (event && typeof event.effect_details === 'object' && event.effect_details) || {};
  const metadata = (event && typeof event.metadata === 'object' && event.metadata) || {};

  const stringCandidates = [
    details.action_type,
    details.source_type,
    effectDetails.source_type,
    event.source_type,
    metadata.source_type
  ];
  const sourceType = stringCandidates
    .map((value) => (typeof value === 'string' ? value.trim() : ''))
    .find((value) => value) || '';

  const cardId = details.card_id ?? details.cardId ?? effectDetails.card_id ?? metadata.card_id ?? null;
  const cardName = details.card_name ?? effectDetails.card_name ?? metadata.card_name ?? null;
  const relicId = details.relic_id ?? effectDetails.relic_id ?? metadata.relic_id ?? null;
  const relicName = details.relic_name ?? effectDetails.relic_name ?? metadata.relic_name ?? null;
  const abilityId = details.ability_id ?? effectDetails.ability_id ?? metadata.ability_id ?? null;

  const tagSet = new Set();
  if (
    cardId != null
    || (cardName && !relicName)
    || (typeof sourceType === 'string' && sourceType.toLowerCase().includes('card'))
  ) {
    tagSet.add('card');
  }
  if (
    relicId != null
    || (relicName && !cardName)
    || (typeof sourceType === 'string' && sourceType.toLowerCase().includes('relic'))
  ) {
    tagSet.add('relic');
  }
  if (details.trigger || details.trigger_type) {
    tagSet.add('trigger');
  }

  let kind = 'ability';
  if (tagSet.has('card')) {
    kind = 'card';
  } else if (tagSet.has('relic')) {
    kind = 'relic';
  } else if (sourceType) {
    kind = sourceType.toLowerCase();
  }

  const summaryParts = [];
  if (kind === 'card') {
    summaryParts.push(cardName || abilityName);
  } else if (kind === 'relic') {
    summaryParts.push(relicName || abilityName);
  } else if (abilityName) {
    summaryParts.push(abilityName);
  }
  if (details.trigger || details.trigger_type) {
    summaryParts.push(details.trigger || details.trigger_type);
  }
  if (details.status_name) {
    summaryParts.push(details.status_name);
  }

  const summary = summaryParts.filter(Boolean).join(' • ') || abilityName || '';
  const eventTypeName = typeof event.event_type === 'string' ? event.event_type.trim() : '';
  const normalizedSummary = summary.toLowerCase();
  const normalizedEventType = eventTypeName.toLowerCase();
  const isGenericSummary =
    !summary || normalizedSummary === 'event' || (normalizedEventType && normalizedSummary === normalizedEventType);
  const keySource = cardId ?? relicId ?? abilityId ?? summary;
  const actionKey = sanitizeFilterId(keySource).toLowerCase();

  const hasUsefulMetadata = Boolean(
    (sourceType && sourceType.toLowerCase() !== 'ability')
    || tagSet.size
    || cardId != null
    || cardName
    || relicId != null
    || relicName
    || abilityId != null
    || !isGenericSummary
  );

  if (!hasUsefulMetadata) {
    return null;
  }

  return {
    name: abilityName,
    kind,
    sourceType: sourceType || '',
    summary,
    card:
      cardId != null || cardName
        ? { id: cardId != null ? String(cardId) : null, name: cardName || abilityName }
        : null,
    relic:
      relicId != null || relicName
        ? { id: relicId != null ? String(relicId) : null, name: relicName || abilityName }
        : null,
    abilityId: abilityId != null ? String(abilityId) : null,
    tags: Array.from(tagSet),
    key: actionKey
  };
}

function buildMetricSlices(eventType, amount, attackerId, targetId) {
  const numericAmount = Number(amount);
  if (!Number.isFinite(numericAmount)) {
    return [];
  }
  const slices = [];
  for (const metric of TIMELINE_METRICS) {
    if (!metric.eventTypes.has(eventType)) continue;
    const entityId = metric.role === 'attacker' ? attackerId : metric.role === 'target' ? targetId : null;
    slices.push({
      metric: metric.id,
      amount: Math.max(0, numericAmount),
      entityId: entityId || null
    });
  }
  return slices;
}

function shapeTimelineEvents(list = []) {
  if (!Array.isArray(list) || !list.length) {
    return {
      events: [],
      domain: { start: 0, end: 0, span: 0 },
      catalog: { sourceTypes: [], eventTypes: [], abilityNames: [] }
    };
  }

  const baseRef = { base: null };
  const sourceTypes = new Set();
  const eventTypes = new Set();
  const abilityNames = new Set();

  const events = list
    .map((event, index) => {
      if (!event) return null;
      const eventType = typeof event.event_type === 'string' ? event.event_type : 'event';
      eventTypes.add(eventType);
      const attackerId = event.attacker_id || null;
      const targetId = event.target_id || null;
      const abilityName = resolveAbilityName(event);
      abilityNames.add(abilityName);
      const sourceType = event?.source_type || event?.details?.source_type || '';
      if (sourceType) {
        sourceTypes.add(String(sourceType));
      }
      const time = parseEventSeconds(event, index, baseRef);
      const slices = buildMetricSlices(eventType, event.amount, attackerId, targetId);
      const amount = Number(event.amount);
      const metricTotals = slices.reduce((acc, slice) => {
        if (!slice?.metric) return acc;
        const metricId = slice.metric;
        acc[metricId] = (acc[metricId] || 0) + (Number(slice.amount) || 0);
        return acc;
      }, {});
      const metrics = Object.keys(metricTotals);
      const action = buildActionMetadata(event, abilityName);
      return {
        id: `${event?.event_id ?? `${eventType}-${index}`}`,
        order: index,
        time: Number.isFinite(time) ? time : index,
        eventType,
        eventKey: sanitizeFilterId(eventType).toLowerCase(),
        amount: Number.isFinite(amount) ? amount : null,
        attacker: attackerId,
        target: targetId,
        sourceType: sourceType ? String(sourceType) : '',
        sourceKey: sanitizeFilterId(sourceType).toLowerCase(),
        abilityName,
        action,
        metricSlices: slices,
        metricTotals,
        metrics,
        raw: event
      };
    })
    .filter(Boolean)
    .sort((a, b) => (a.time - b.time) || (a.order - b.order));

  const start = events.length ? events[0].time : 0;
  const end = events.length ? events[events.length - 1].time : start;
  const span = Math.max(0, end - start);

  return {
    events,
    domain: { start, end, span },
    catalog: {
      sourceTypes: Array.from(sourceTypes).sort((a, b) => a.localeCompare(b)),
      eventTypes: Array.from(eventTypes).sort((a, b) => a.localeCompare(b)),
      abilityNames: Array.from(abilityNames).sort((a, b) => a.localeCompare(b))
    }
  };
}

function buildTimelineProjection(data, filters, window, currentTabId) {
  const domainStart = Number.isFinite(data?.domain?.start) ? data.domain.start : 0;
  const domainEnd = Number.isFinite(data?.domain?.end) ? data.domain.end : domainStart;
  const metric = TIMELINE_METRIC_LOOKUP.get(filters.metric) || TIMELINE_METRICS[0];
  const focusId = currentTabId && currentTabId !== 'overview' ? currentTabId : null;

  let rangeStart = Number.isFinite(window?.start) ? Math.max(window.start, domainStart) : domainStart;
  let rangeEnd = Number.isFinite(window?.end) ? Math.min(window.end, domainEnd) : domainEnd;
  if (rangeEnd <= rangeStart) {
    const fallbackSpan = Math.max(data?.domain?.span ?? 0, 1);
    rangeEnd = rangeStart + fallbackSpan;
  }

  const entityFilter = new Set((filters.entities || []).map((id) => sanitizeFilterId(id)));
  const sourceFilter = new Set((filters.sourceTypes || []).map((id) => sanitizeFilterId(id).toLowerCase()));
  const eventTypeFilter = new Set((filters.eventTypes || []).map((id) => sanitizeFilterId(id).toLowerCase()));

  const visibleEvents = [];
  const highlight = [];
  let totalAmount = 0;

  for (const event of data.events || []) {
    if (event.time < rangeStart || event.time > rangeEnd) continue;
    if (eventTypeFilter.size && !eventTypeFilter.has(event.eventKey)) continue;
    if (sourceFilter.size && !sourceFilter.has(event.sourceKey)) continue;
    if (entityFilter.size) {
      const involved = (event.attacker && entityFilter.has(sanitizeFilterId(event.attacker)))
        || (event.target && entityFilter.has(sanitizeFilterId(event.target)));
      if (!involved) continue;
    }
    const metricAmount = Math.max(0, Number(event.metricTotals?.[metric.id] ?? 0));
    const matchesMetric = metricAmount > 0;

    const enhancedEvent = {
      ...event,
      matchesMetric,
      metricAmount
    };

    visibleEvents.push(enhancedEvent);

    if (matchesMetric) {
      totalAmount += metricAmount;
    }

    if (focusId) {
      const focusMatch = event.metricSlices.some(
        (slice) => slice.metric === metric.id && slice.entityId === focusId
      );
      const actionMatch =
        Boolean(event.action?.kind && event.action.kind !== 'ability')
        && Boolean(event.attacker === focusId || event.target === focusId);
      if (focusMatch || actionMatch) {
        highlight.push({
          id: `${event.id}-${focusId}-${highlight.length}`,
          eventId: event.id,
          time: event.time,
          amount: metricAmount > 0 ? metricAmount : Number(event.amount) || 0,
          label: event.action?.summary || event.abilityName,
          sourceType: event.sourceType || event.action?.sourceType || '',
          eventType: event.eventType,
          kind: event.action?.kind || (matchesMetric ? 'metric' : 'event')
        });
      }
    }
  }

  highlight.sort((a, b) => (a.time - b.time) || a.id.localeCompare(b.id));

  return {
    metric,
    focusId,
    start: rangeStart,
    end: rangeEnd,
    span: rangeEnd - rangeStart,
    totalAmount,
    events: visibleEvents,
    filteredEvents: visibleEvents,
    highlightEvents: highlight.slice(0, 80),
    hasData: visibleEvents.length > 0,
    eventCount: visibleEvents.length,
    catalog: data.catalog || { sourceTypes: [], eventTypes: [], abilityNames: [] },
    domain: data.domain || { start: 0, end: 0, span: 0 }
  };
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

export function createBattleReviewState(initialProps = {}) {
  const props = writable({ ...defaultProps, ...initialProps });
  const summary = writable(initialProps.prefetchedSummary || emptySummary);
  const summaryStatus = writable(initialProps.prefetchedSummary ? 'ready' : 'idle');
  const events = writable([]);
  const eventsStatus = writable('idle');
  const eventsOpen = writable(false);
  const timelineFilters = writable(
    normalizeTimelineFilters(
      initialProps.timelineFilters || createDefaultTimelineFilters(Boolean(initialProps.reducedMotion)),
      Boolean(initialProps.reducedMotion)
    )
  );
  const comparisonSet = writable([]);
  const pinnedEvents = writable([]);
  const timeWindow = writable(null);
  const timelineCursor = writable({ time: 0, eventId: null });

  let lastKey = '';
  let currentToken = 0;

  async function loadSummary(battleIndex, runId) {
    const token = ++currentToken;
    summaryStatus.set('loading');
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    for (let attempt = 0; attempt < 10; attempt++) {
      try {
        const res = await getBattleSummary(battleIndex, runId);
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

  function resetViewState() {
    activeTab.set('overview');
    const defaultFilters = normalizeTimelineFilters(
      createDefaultTimelineFilters(Boolean(get(reducedMotion))),
      Boolean(get(reducedMotion))
    );
    timelineFilters.set(defaultFilters);
    comparisonSet.set([]);
    pinnedEvents.set([]);
    timeWindow.set(null);
    timelineCursor.set({ time: 0, eventId: null });
  }

  function handlePropsChange(value) {
    const key = value.runId && value.battleIndex > 0 ? `${value.runId}|${value.battleIndex}` : '';
    if (!key) {
      lastKey = '';
      summary.set(emptySummary);
      summaryStatus.set('idle');
      resetViewState();
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
      resetViewState();
      loadSummary(value.battleIndex, value.runId);
    }
  }

  let stop = props.subscribe(handlePropsChange);

  function updateProps(next) {
    props.update((prev) => ({ ...prev, ...next }));
  }

  async function loadEvents() {
    const { battleIndex, runId } = get(props);
    if (!battleIndex) return;
    eventsStatus.set('loading');
    try {
      const data = await getBattleEvents(battleIndex, runId);
      events.set(Array.isArray(data) ? data : []);
      eventsStatus.set('ready');
    } catch {
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

  const entityMetrics = derived([summary, currentTab], ([$summary, $current]) =>
    computeEntityMetrics($summary, $current?.id ?? 'overview')
  );
  const overviewTotals = derived(summary, ($summary) => aggregateDamageByType($summary));
  const overviewGrand = derived(overviewTotals, ($totals) => Object.values($totals || {}).reduce((acc, cur) => acc + (cur || 0), 0));

  const timelineData = derived(events, ($events) => shapeTimelineEvents($events));
  const timelineMetrics = readable(
    TIMELINE_METRICS.map((metric) => ({ id: metric.id, label: metric.label, color: metric.color }))
  );

  const timeline = derived(
    [timelineData, timelineFilters, timeWindow, currentTab],
    ([$data, $filters, $window, $current]) => buildTimelineProjection($data, $filters, $window, $current?.id ?? null)
  );

  const stopTimelineClamp = timeline.subscribe(($timeline) => {
    const start = Number.isFinite($timeline?.start) ? $timeline.start : 0;
    const end = Number.isFinite($timeline?.end) ? $timeline.end : start;
    timelineCursor.update((cursor) => {
      const nextTime = Number(cursor?.time);
      const clamped = Number.isFinite(nextTime) ? Math.min(Math.max(nextTime, start), end) : start;
      const eventId = cursor?.eventId != null && cursor.eventId !== '' ? String(cursor.eventId) : null;
      if (cursor && cursor.time === clamped && cursor.eventId === eventId) {
        return cursor;
      }
      return { time: clamped, eventId };
    });
  });

  function clampCursorTarget(target = {}) {
    const snapshot = get(timeline);
    const start = Number.isFinite(snapshot?.start) ? snapshot.start : 0;
    const end = Number.isFinite(snapshot?.end) ? snapshot.end : start;
    const nextTime = Number(target?.time);
    const clamped = Number.isFinite(nextTime) ? Math.min(Math.max(nextTime, start), end) : start;
    const eventId = target?.eventId != null && target.eventId !== '' ? String(target.eventId) : null;
    return { time: clamped, eventId };
  }

  function setTimelineCursor(value) {
    if (typeof value === 'function') {
      timelineCursor.update((prev) => clampCursorTarget(value(prev)));
      return;
    }
    timelineCursor.set(clampCursorTarget(value));
  }

  const resultSummary = derived(summary, ($summary) => ({
    result: $summary?.result || '—',
    duration: Number.isFinite($summary?.duration_seconds) ? Math.round($summary.duration_seconds) : null,
    eventCount: $summary?.event_count || ($summary?.events?.length || 0)
  }));

  function setTimelineFilters(value = {}) {
    if (typeof value === 'function') {
      timelineFilters.update((prev) => normalizeTimelineFilters(value(prev), Boolean(get(reducedMotion))));
      return;
    }
    if (Array.isArray(value)) {
      timelineFilters.set(decodeTimelineFilters(value, Boolean(get(reducedMotion))));
      return;
    }
    timelineFilters.set(normalizeTimelineFilters(value, Boolean(get(reducedMotion))));
  }

  function setComparisonSet(value = []) {
    comparisonSet.set(Array.isArray(value) ? [...value] : []);
  }

  function setPinnedEvents(value = []) {
    pinnedEvents.set(Array.isArray(value) ? [...value] : []);
  }

  function setTimeWindow(value = null) {
    if (value && typeof value === 'object') {
      const start = Number(value.start);
      const end = Number(value.end);
      if (Number.isFinite(start) && Number.isFinite(end)) {
        timeWindow.set({ start, end });
        return;
      }
    }
    timeWindow.set(null);
  }

  function applyViewState(state = {}) {
    if (!state || typeof state !== 'object') return;
    if (state.tab) {
      activeTab.set(state.tab);
    }
    if (Array.isArray(state.filters)) {
      setTimelineFilters(state.filters);
    }
    if (Array.isArray(state.comparison)) {
      setComparisonSet(state.comparison);
    }
    if (Array.isArray(state.pins)) {
      setPinnedEvents(state.pins);
    }
    if (state.window) {
      setTimeWindow(state.window);
    }
  }

  const shareableState = derived(
    [props, activeTab, timelineFilters, comparisonSet, pinnedEvents, timeWindow],
    ([$props, $activeTab, $filters, $comparison, $pins, $window]) => ({
      runId: $props.runId || '',
      battleIndex: Number.isFinite($props.battleIndex) ? $props.battleIndex : 0,
      tab: $activeTab || 'overview',
      filters: encodeTimelineFilters($filters),
      comparison: Array.isArray($comparison) ? [...$comparison] : [],
      pins: Array.isArray($pins) ? [...$pins] : [],
      window: $window && typeof $window === 'object' ? { ...$window } : null
    })
  );

  function toSearchParams() {
    return buildBattleReviewSearchParams(get(shareableState));
  }

  function destroy() {
    stop?.();
    stopTimelineClamp?.();
    events.set([]);
  }

  return {
    props,
    summary,
    summaryStatus,
    events,
    eventsStatus,
    eventsOpen,
    timelineFilters,
    timelineMetrics,
    comparisonSet,
    pinnedEvents,
    timeWindow,
    timelineCursor,
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
    shareableState,
    updateProps,
    loadEvents,
    toggleEvents,
    setEventsOpen,
    setTimelineFilters,
    setComparisonSet,
    setPinnedEvents,
    setTimeWindow,
    setTimelineCursor,
    applyViewState,
    toSearchParams,
    destroy
  };
}
