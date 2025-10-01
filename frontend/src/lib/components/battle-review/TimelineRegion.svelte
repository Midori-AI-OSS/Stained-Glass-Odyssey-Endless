<script>
  import { getContext, onMount } from 'svelte';
  import { get } from 'svelte/store';
  import {
    BATTLE_REVIEW_CONTEXT_KEY,
    createDefaultTimelineFilters
  } from '../../systems/battleReview/state.js';
  import TripleRingSpinner from '../TripleRingSpinner.svelte';

  const context = getContext(BATTLE_REVIEW_CONTEXT_KEY);
  const {
    timeline,
    timelineFilters,
    timelineMetrics,
    setTimelineFilters,
    timeWindow,
    setTimeWindow,
    timelineCursor,
    setTimelineCursor,
    displayParty,
    displayFoes,
    currentTab,
    eventsStatus,
    loadEvents,
    reducedMotion
  } = context;

  const FILTER_ID_PATTERN = /[^a-z0-9._:-]/gi;
  const MIN_ZOOM = 5;
  const CARD_LANE_COLOR = '#fb7185';
  const RELIC_LANE_COLOR = '#facc15';
  const OTHER_LANE_COLOR = '#94a3b8';

  const LANE_DEFINITIONS = [
    { id: 'damageDone', label: 'Damage Dealt', metric: 'damageDone' },
    { id: 'damageTaken', label: 'Damage Taken', metric: 'damageTaken' },
    { id: 'healing', label: 'Healing', metric: 'healing' },
    { id: 'mitigation', label: 'Mitigation', metric: 'mitigation' },
    { id: 'card', label: 'Card Plays', predicate: (event) => event?.action?.kind === 'card' },
    { id: 'relic', label: 'Relic Triggers', predicate: (event) => event?.action?.kind === 'relic' },
    { id: 'other', label: 'Other Events', fallback: true }
  ];

  let timelineEl;

  onMount(() => {
    if (get(eventsStatus) === 'idle') {
      loadEvents();
    }
    if (!timelineEl) return undefined;
    const observer = new ResizeObserver(() => {
      // The cursor indicator relies on updated width for pointer interactions.
      // We do not need explicit assignments because we compute ratios, but the
      // observer keeps layout reactive when the panel size changes.
    });
    observer.observe(timelineEl);
    return () => observer.disconnect();
  });

  $: filters = $timelineFilters;
  $: projection = $timeline;
  $: metricsOptions = $timelineMetrics;
  $: metricColorMap = new Map(metricsOptions.map((option) => [option.id, option.color]));
  $: entityOptions = buildEntityOptions($displayParty, $displayFoes);
  $: sourceTypeOptions = buildValueOptions(projection?.catalog?.sourceTypes ?? []);
  $: eventTypeOptions = buildValueOptions(projection?.catalog?.eventTypes ?? []);
  $: focusLabel = $currentTab?.id === 'overview' ? 'Overview' : $currentTab?.label ?? 'Entity';
  $: domainStart = projection?.domain?.start ?? 0;
  $: domainEnd = projection?.domain?.end ?? domainStart;
  $: domainSpan = Math.max(domainEnd - domainStart, 0);
  $: windowStart = $timeWindow?.start ?? projection?.start ?? domainStart;
  $: windowEnd = $timeWindow?.end ?? projection?.end ?? domainEnd;
  $: windowSpan = Math.max(windowEnd - windowStart, 0);
  $: zoomPercent = domainSpan > 0 ? Math.round((windowSpan / domainSpan) * 100) : 100;
  $: clampedZoom = Math.min(Math.max(zoomPercent || 100, MIN_ZOOM), 100);
  $: offsetPercent = domainSpan > 0 ? Math.round(((windowStart - domainStart) / domainSpan) * 100) : 0;
  $: clampedOffset = Math.min(Math.max(offsetPercent || 0, 0), 100);
  $: offsetMax = Math.max(0, 100 - clampedZoom);
  $: summaryMetric = metricsOptions.find((option) => option.id === filters.metric) || metricsOptions[0];
  $: summaryTotal = formatAmount(projection?.totalAmount ?? 0);
  $: eventCount = projection?.eventCount ?? projection?.events?.length ?? 0;
  $: cursorPercent = computePercent($timelineCursor?.time, projection?.start, projection?.end);
  $: cursorLeft = `${cursorPercent}%`;
  $: axisTicks = buildAxisTicks(projection?.start, projection?.end);
  $: lanePalette = { card: CARD_LANE_COLOR, relic: RELIC_LANE_COLOR, other: OTHER_LANE_COLOR };
  $: lanes = buildTimelineLanes(
    projection?.events ?? [],
    projection?.start,
    projection?.end,
    filters.metric,
    metricColorMap,
    lanePalette
  );

  function filterKey(value) {
    if (value == null) return '';
    return String(value).replace(FILTER_ID_PATTERN, '').slice(0, 64);
  }

  function buildEntityOptions(party = [], foes = []) {
    const out = [];
    for (const member of party ?? []) {
      if (!member?.id) continue;
      out.push({
        value: filterKey(member.id),
        label: member.name || member.id,
        group: 'Allies'
      });
    }
    for (const foe of foes ?? []) {
      if (!foe?.id) continue;
      out.push({
        value: filterKey(foe.id),
        label: foe.name || foe.id,
        group: 'Foes'
      });
    }
    return out;
  }

  function buildValueOptions(list) {
    return list.map((entry) => ({ value: filterKey(entry), label: entry || '—' }));
  }

  function buildTimelineLanes(events, start, end, activeMetricId, metricColors, laneColors) {
    const defs = LANE_DEFINITIONS.map((def) => ({ ...def, events: [] }));
    const byId = new Map(defs.map((def) => [def.id, def]));
    if (!Array.isArray(events) || !events.length || !Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
      return defs;
    }
    const span = Math.max(end - start, 0.0001);
    for (const event of events) {
      let placed = false;
      for (const def of LANE_DEFINITIONS) {
        let matches = false;
        if (def.metric) {
          matches = Array.isArray(event.metrics) && event.metrics.includes(def.metric);
        } else if (typeof def.predicate === 'function') {
          matches = def.predicate(event);
        }
        if (!matches) continue;
        placed = true;
        const lane = byId.get(def.id);
        if (!lane) continue;
        lane.events.push(
          makeLaneEvent(event, start, span, def.id, def.metric, activeMetricId, metricColors, laneColors)
        );
      }
      if (!placed) {
        const fallbackLane = byId.get('other');
        if (fallbackLane) {
          fallbackLane.events.push(
            makeLaneEvent(event, start, span, 'other', null, activeMetricId, metricColors, laneColors)
          );
        }
      }
    }
    return defs;
  }

  function makeLaneEvent(event, start, span, laneId, laneMetricId, activeMetricId, metricColors, laneColors) {
    const ratio = Math.min(Math.max((event.time - start) / span, 0), 1);
    const color =
      (laneMetricId && metricColors.get(laneMetricId))
      || laneColors[laneId]
      || OTHER_LANE_COLOR;
    const amount = laneMetricId
      ? Number(event.metricTotals?.[laneMetricId] ?? 0)
      : Number(event.metricAmount ?? event.amount ?? 0);
    const hasAmount = Number.isFinite(amount) && amount !== 0;
    const primary = laneMetricId
      ? laneMetricId === activeMetricId && Number(event.metricTotals?.[laneMetricId] ?? 0) > 0
      : Boolean(activeMetricId && Number(event.metricTotals?.[activeMetricId] ?? 0) > 0);
    return {
      id: `${laneId}-${event.id}-${event.order}`,
      event,
      laneId,
      metricId: laneMetricId,
      position: ratio * 100,
      color,
      label: event.action?.summary || event.abilityName,
      amount: hasAmount ? amount : null,
      primary,
      kind: event.action?.kind || (laneMetricId ? 'metric' : 'event')
    };
  }

  function buildAxisTicks(start, end) {
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
      return [];
    }
    const span = end - start;
    const divisions = span < 6 ? 4 : 6;
    const step = span / divisions;
    const ticks = [];
    for (let index = 0; index <= divisions; index += 1) {
      const time = start + step * index;
      ticks.push({
        time,
        position: computePercent(time, start, end),
        label: formatSeconds(time)
      });
    }
    return ticks;
  }

  function computePercent(value, start, end) {
    if (!Number.isFinite(value) || !Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
      return 0;
    }
    return Math.min(Math.max((value - start) / (end - start), 0), 1) * 100;
  }

  function formatSeconds(value) {
    if (!Number.isFinite(value)) return '0.0s';
    return `${Math.max(0, value).toFixed(1)}s`;
  }

  function formatAmount(value) {
    if (!Number.isFinite(value)) return '0';
    return Math.round(value).toLocaleString();
  }

  function updateMetric(event) {
    const metric = event.currentTarget.value;
    setTimelineFilters((prev) => ({ ...prev, metric }));
  }

  function handleEntityChange(event) {
    const selected = Array.from(event.currentTarget.selectedOptions).map((option) => option.value);
    setTimelineFilters((prev) => ({ ...prev, entities: selected }));
  }

  function handleSourceChange(event) {
    const selected = Array.from(event.currentTarget.selectedOptions).map((option) => option.value);
    setTimelineFilters((prev) => ({ ...prev, sourceTypes: selected }));
  }

  function handleEventTypeChange(event) {
    const selected = Array.from(event.currentTarget.selectedOptions).map((option) => option.value);
    setTimelineFilters((prev) => ({ ...prev, eventTypes: selected }));
  }

  function toggleRespectMotion(event) {
    const checked = event.currentTarget.checked;
    setTimelineFilters((prev) => ({ ...prev, respectMotion: checked }));
  }

  function clearFilters() {
    setTimelineFilters(() => createDefaultTimelineFilters(filters?.respectMotion ?? true));
  }

  function handleZoomChange(event) {
    if (!projection) return;
    const sliderValue = Number(event.currentTarget.value);
    if (!Number.isFinite(sliderValue)) return;
    const span = Math.max(domainSpan, 0);
    if (!(span > 0)) return;
    const ratio = Math.min(Math.max(sliderValue, MIN_ZOOM), 100) / 100;
    const width = Math.max(span * ratio, Math.min(span, 1));
    let start = windowStart;
    let end = start + width;
    if (end > domainEnd) {
      end = domainEnd;
      start = end - width;
    }
    start = Math.max(domainStart, start);
    setTimeWindow({ start, end });
  }

  function handleOffsetChange(event) {
    if (!projection) return;
    const sliderValue = Number(event.currentTarget.value);
    if (!Number.isFinite(sliderValue)) return;
    const span = Math.max(domainSpan, 0);
    if (!(span > 0)) return;
    const width = Math.max(windowSpan, Math.min(span, 1));
    let start = domainStart + (span * Math.min(Math.max(sliderValue, 0), 100)) / 100;
    let end = start + width;
    if (end > domainEnd) {
      end = domainEnd;
      start = end - width;
    }
    start = Math.max(domainStart, start);
    setTimeWindow({ start, end });
  }

  function resetWindow() {
    setTimeWindow(null);
    if (Number.isFinite(projection?.start)) {
      setTimelineCursor({ time: projection.start, eventId: null });
    }
  }

  function handleTrackPointer(event) {
    if (!projection || !$timelineCursor || !event.currentTarget) return;
    const rect = event.currentTarget.getBoundingClientRect();
    if (rect.width <= 0 || !Number.isFinite(projection.start) || !Number.isFinite(projection.end)) {
      return;
    }
    const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
    const time = projection.start + (projection.end - projection.start) * ratio;
    setTimelineCursor({ time, eventId: null });
  }

  function handleEventFocus(item) {
    if (!item?.event) return;
    setTimelineCursor({ time: item.event.time, eventId: item.event.id });
  }

  function handleHighlightSelect(item) {
    if (!item) return;
    setTimelineCursor({ time: item.time, eventId: item.eventId ?? item.id });
  }

  function describeLaneEvent(item) {
    if (!item?.event) return 'Combat event';
    const pieces = [`T+${formatSeconds(item.event.time)}`];
    if (item.label) {
      pieces.push(item.label);
    }
    if (item.event.eventType) {
      pieces.push(item.event.eventType.replace(/_/g, ' '));
    }
    if (item.amount != null) {
      pieces.push(`${formatAmount(item.amount)} value`);
    }
    if (item.event.action?.kind) {
      pieces.push(item.event.action.kind);
    }
    return pieces.filter(Boolean).join(' • ');
  }

  function isFiltersPristine() {
    const defaultFilters = createDefaultTimelineFilters(filters?.respectMotion ?? true);
    return (
      filters.metric === defaultFilters.metric
      && (!filters.entities || filters.entities.length === 0)
      && (!filters.sourceTypes || filters.sourceTypes.length === 0)
      && (!filters.eventTypes || filters.eventTypes.length === 0)
    );
  }
</script>

<section class="timeline-region" aria-label="Battle timeline">
  <header class="timeline-header">
    <h3>Battle Timeline</h3>
    <div class="filters-row">
      <label class="filter-field">
        <span class="field-label">Metric</span>
        <select on:change={updateMetric} aria-label="Select timeline metric" value={filters.metric}>
          {#each metricsOptions as option (option.id)}
            <option value={option.id}>{option.label}</option>
          {/each}
        </select>
      </label>
      <label class="filter-field">
        <span class="field-label">Entities</span>
        <select multiple size="3" on:change={handleEntityChange} aria-label="Filter by entity">
          {#if !entityOptions.length}
            <option disabled>No entities</option>
          {:else}
            {#each entityOptions as option (option.value)}
              <option value={option.value} selected={filters.entities?.includes(option.value)}>
                {option.group === 'Foes' ? `⚔️ ${option.label}` : `🛡️ ${option.label}`}
              </option>
            {/each}
          {/if}
        </select>
      </label>
      <label class="filter-field">
        <span class="field-label">Ability type</span>
        <select multiple size="3" on:change={handleSourceChange} aria-label="Filter by ability type">
          {#if !sourceTypeOptions.length}
            <option disabled>No data</option>
          {:else}
            {#each sourceTypeOptions as option (option.value)}
              <option value={option.value} selected={filters.sourceTypes?.includes(option.value)}>{option.label}</option>
            {/each}
          {/if}
        </select>
      </label>
      <label class="filter-field">
        <span class="field-label">Event type</span>
        <select multiple size="3" on:change={handleEventTypeChange} aria-label="Filter by event type">
          {#if !eventTypeOptions.length}
            <option disabled>No data</option>
          {:else}
            {#each eventTypeOptions as option (option.value)}
              <option value={option.value} selected={filters.eventTypes?.includes(option.value)}>{option.label}</option>
            {/each}
          {/if}
        </select>
      </label>
      <label class="filter-toggle">
        <input type="checkbox" checked={filters?.respectMotion ?? true} on:change={toggleRespectMotion} />
        <span>Respect reduced motion</span>
      </label>
      <button type="button" class="reset-button" on:click={clearFilters} disabled={isFiltersPristine()}>
        Clear filters
      </button>
    </div>
  </header>

  <div class="window-controls" aria-label="Timeline window controls">
    <div class="control-group">
      <label for="timeline-zoom">Zoom</label>
      <input
        id="timeline-zoom"
        type="range"
        min={MIN_ZOOM}
        max="100"
        step="5"
        value={clampedZoom}
        on:input={handleZoomChange}
        aria-valuemin={MIN_ZOOM}
        aria-valuemax="100"
        aria-valuenow={clampedZoom}
      />
      <span class="control-value">{clampedZoom}%</span>
    </div>
    <div class="control-group">
      <label for="timeline-offset">Offset</label>
      <input
        id="timeline-offset"
        type="range"
        min="0"
        max={offsetMax}
        step="1"
        value={Math.min(clampedOffset, offsetMax)}
        on:input={handleOffsetChange}
        aria-valuemin="0"
        aria-valuemax={offsetMax}
        aria-valuenow={Math.min(clampedOffset, offsetMax)}
      />
      <span class="control-value">{Math.min(clampedOffset, offsetMax)}%</span>
    </div>
    <button type="button" class="reset-window" on:click={resetWindow} disabled={!$timeWindow}>
      Reset window
    </button>
  </div>

  {#if $eventsStatus === 'loading'}
    <div class="events-loading" role="status" aria-live="polite">
      <TripleRingSpinner reducedMotion={$reducedMotion} duration="1s" />
      <span>Loading events…</span>
    </div>
  {/if}

  {#if projection?.hasData}
    <div class="timeline-summary">
      <div class="summary-chip">
        <span>{summaryMetric?.label ?? 'Total'}</span>
        <strong>{summaryTotal}</strong>
      </div>
      <div class="summary-chip">
        <span>Events visible</span>
        <strong>{eventCount}</strong>
      </div>
      <div class="summary-chip">
        <span>Cursor</span>
        <strong>T+{formatSeconds($timelineCursor?.time ?? projection.start ?? 0)}</strong>
      </div>
    </div>

    <div class="timeline-surface" bind:this={timelineEl} role="group" aria-label="Timeline lanes">
      <div class="cursor-line" style={`left: ${cursorLeft};`} aria-hidden="true"></div>
      <div class="timeline-axis" aria-hidden="true">
        {#each axisTicks as tick (tick.time)}
          <span class="axis-tick" style={`left: ${tick.position}%`}>{tick.label}</span>
        {/each}
      </div>
      <div class="timeline-lanes">
        {#each lanes as lane (lane.id)}
          <div class="lane" data-lane={lane.id}>
            <span class="lane-label">{lane.label}</span>
            <div
              class="lane-track"
              data-empty={!lane.events.length}
              on:pointerdown={handleTrackPointer}
              on:click={handleTrackPointer}
            >
              {#if lane.events.length}
                {#each lane.events as item (item.id)}
                  <button
                    type="button"
                    class="lane-event"
                    class:primary={item.primary}
                    class:card={item.kind === 'card'}
                    class:relic={item.kind === 'relic'}
                    style={`left: ${item.position}%;`}
                    on:click|stopPropagation={() => handleEventFocus(item)}
                    aria-label={describeLaneEvent(item)}
                  >
                    <span class="marker" style={`background:${item.color};`}></span>
                    <span class="event-time">T+{formatSeconds(item.event.time)}</span>
                    <span class="event-label">{item.label}</span>
                    {#if item.amount != null}
                      <span class="event-amount">{formatAmount(item.amount)}</span>
                    {/if}
                  </button>
                {/each}
              {:else}
                <span class="lane-empty">No events</span>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>

    <div class="timeline-highlights" aria-live="polite">
      {#if projection.focusId}
        <h4>{focusLabel} highlights</h4>
        {#if projection.highlightEvents.length}
          <ul>
            {#each projection.highlightEvents as item (item.id)}
              <li>
                <button
                  type="button"
                  class:active={item.eventId === $timelineCursor?.eventId}
                  on:click={() => handleHighlightSelect(item)}
                >
                  <span class="highlight-time">T+{formatSeconds(item.time)}</span>
                  <span class="highlight-label">{item.label}</span>
                  <span class="highlight-kind">{item.kind ?? 'event'}</span>
                  <span class="highlight-amount">{formatAmount(item.amount ?? 0)}</span>
                </button>
              </li>
            {/each}
          </ul>
        {:else}
          <p class="empty-hint">No matching ability events in this window.</p>
        {/if}
      {:else}
        <h4>Ability highlights</h4>
        <p class="empty-hint">Select a party member or foe tab to see highlighted abilities.</p>
      {/if}
    </div>
  {:else}
    <p class="timeline-empty">Timeline will populate once combat events are recorded.</p>
  {/if}
</section>

<style>
  .timeline-region {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    background: rgba(15, 23, 42, 0.35);
    border: 1px solid rgba(30, 64, 175, 0.45);
    padding: 1.25rem;
    min-height: 22rem;
  }

  .timeline-header {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .timeline-header h3 {
    margin: 0;
    font-size: 0.95rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #bae6fd;
  }

  .filters-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.75rem;
  }

  .filter-field {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.78rem;
    color: rgba(226, 232, 240, 0.9);
  }

  .filter-field select {
    width: 100%;
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(148, 163, 184, 0.35);
    color: #e2e8f0;
    padding: 0.35rem 0.4rem;
    border-radius: 0;
  }

  .filter-field select:focus-visible {
    outline: 2px solid rgba(125, 211, 252, 0.85);
    outline-offset: 2px;
  }

  .field-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(148, 163, 184, 0.85);
  }

  .filter-toggle {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.78rem;
    color: rgba(226, 232, 240, 0.85);
  }

  .filter-toggle input {
    accent-color: rgba(56, 189, 248, 0.75);
  }

  .reset-button {
    align-self: flex-end;
    padding: 0.45rem 0.75rem;
    border: 1px solid rgba(148, 163, 184, 0.45);
    background: rgba(15, 23, 42, 0.65);
    color: #e0f2fe;
    font-size: 0.75rem;
    cursor: pointer;
    transition: background 0.2s ease, border-color 0.2s ease;
  }

  .reset-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .reset-button:not(:disabled):hover,
  .reset-button:not(:disabled):focus-visible {
    background: rgba(56, 189, 248, 0.25);
    border-color: rgba(125, 211, 252, 0.65);
    color: #f0f9ff;
  }

  .window-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;
    font-size: 0.78rem;
    color: rgba(226, 232, 240, 0.85);
  }

  .events-loading {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0.5rem 0 0;
    color: rgba(226, 232, 240, 0.85);
  }

  .events-loading span {
    font-size: 0.85rem;
  }

  .control-group {
    display: flex;
    align-items: center;
    gap: 0.45rem;
  }

  .control-group label {
    font-size: 0.75rem;
    color: rgba(203, 213, 225, 0.85);
  }

  .control-group input[type='range'] {
    accent-color: rgba(56, 189, 248, 0.75);
  }

  .control-value {
    font-variant-numeric: tabular-nums;
    color: rgba(148, 163, 184, 0.85);
  }

  .reset-window {
    padding: 0.45rem 0.75rem;
    border: 1px solid rgba(148, 163, 184, 0.45);
    background: rgba(15, 23, 42, 0.65);
    color: #e0f2fe;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .reset-window:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .timeline-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .summary-chip {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    padding: 0.5rem 0.75rem;
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(56, 189, 248, 0.35);
    min-width: 120px;
  }

  .summary-chip span {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(148, 163, 184, 0.85);
  }

  .summary-chip strong {
    font-size: 0.95rem;
    color: #f8fafc;
  }

  .timeline-surface {
    position: relative;
    border: 1px solid rgba(30, 64, 175, 0.45);
    background: rgba(15, 23, 42, 0.45);
    padding: 1rem 1rem 0.75rem;
    overflow: hidden;
  }

  .cursor-line {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 1px;
    background: rgba(241, 245, 249, 0.6);
    pointer-events: none;
  }

  .timeline-axis {
    position: relative;
    height: 1.5rem;
    margin-bottom: 0.5rem;
  }

  .axis-tick {
    position: absolute;
    top: 0;
    transform: translateX(-50%);
    font-size: 0.7rem;
    color: rgba(148, 163, 184, 0.85);
    font-variant-numeric: tabular-nums;
  }

  .timeline-lanes {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .lane {
    display: grid;
    grid-template-columns: 110px minmax(0, 1fr);
    gap: 0.75rem;
    align-items: center;
  }

  .lane-label {
    font-size: 0.75rem;
    color: rgba(226, 232, 240, 0.85);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .lane-track {
    position: relative;
    min-height: 52px;
    border: 1px dashed rgba(51, 65, 85, 0.65);
    background: rgba(15, 23, 42, 0.35);
    display: flex;
    align-items: center;
    padding: 0.4rem 0;
  }

  .lane-track[data-empty='true'] {
    justify-content: center;
    color: rgba(100, 116, 139, 0.8);
    font-size: 0.75rem;
  }

  .lane-empty {
    font-size: 0.75rem;
    color: rgba(100, 116, 139, 0.85);
  }

  .lane-event {
    position: absolute;
    transform: translateX(-50%);
    min-width: 160px;
    max-width: 220px;
    display: grid;
    grid-template-columns: 14px 70px minmax(0, 1fr) auto;
    gap: 0.4rem;
    align-items: center;
    padding: 0.35rem 0.45rem;
    border: 1px solid rgba(148, 163, 184, 0.45);
    background: rgba(15, 23, 42, 0.75);
    color: rgba(226, 232, 240, 0.9);
    font-size: 0.72rem;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.4);
  }

  .lane-event.primary {
    border-color: rgba(56, 189, 248, 0.85);
    background: rgba(56, 189, 248, 0.2);
  }

  .lane-event.card {
    border-color: rgba(251, 113, 133, 0.85);
  }

  .lane-event.relic {
    border-color: rgba(250, 204, 21, 0.8);
  }

  .lane-event:focus-visible,
  .lane-event:hover {
    border-color: rgba(125, 211, 252, 0.9);
    background: rgba(30, 64, 175, 0.55);
  }

  .marker {
    width: 10px;
    height: 10px;
    border-radius: 9999px;
    background: rgba(148, 163, 184, 0.8);
  }

  .event-time {
    font-variant-numeric: tabular-nums;
    color: rgba(148, 163, 184, 0.85);
  }

  .event-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .event-amount {
    justify-self: end;
    font-weight: 600;
    color: #f8fafc;
  }

  .timeline-highlights {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .timeline-highlights h4 {
    margin: 0;
    font-size: 0.85rem;
    color: #f1f5f9;
  }

  .timeline-highlights ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    max-height: 12rem;
    overflow-y: auto;
  }

  .timeline-highlights button {
    width: 100%;
    display: grid;
    grid-template-columns: 80px minmax(0, 1fr) 80px 70px;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.5rem;
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(148, 163, 184, 0.35);
    color: rgba(226, 232, 240, 0.9);
    font-size: 0.75rem;
    cursor: pointer;
    text-align: left;
  }

  .timeline-highlights button:hover,
  .timeline-highlights button:focus-visible,
  .timeline-highlights button.active {
    border-color: rgba(56, 189, 248, 0.65);
    background: rgba(56, 189, 248, 0.2);
    color: #f0f9ff;
  }

  .highlight-time {
    font-variant-numeric: tabular-nums;
    color: rgba(148, 163, 184, 0.85);
  }

  .highlight-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .highlight-kind {
    text-transform: capitalize;
    color: rgba(226, 232, 240, 0.85);
  }

  .highlight-amount {
    justify-self: end;
    font-weight: 600;
    color: #f8fafc;
  }

  .empty-hint {
    margin: 0;
    font-size: 0.78rem;
    color: rgba(148, 163, 184, 0.75);
  }

  .timeline-empty {
    margin: 0;
    padding: 2.5rem 0;
    text-align: center;
    color: rgba(148, 163, 184, 0.8);
    font-size: 0.85rem;
  }

  @media (max-width: 960px) {
    .filters-row {
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    }

    .lane {
      grid-template-columns: 1fr;
    }

    .lane-label {
      order: -1;
    }

    .lane-event {
      min-width: 140px;
      max-width: 180px;
      grid-template-columns: 12px 64px minmax(0, 1fr) auto;
    }
  }
</style>
