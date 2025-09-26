<script>
  import { getContext, onMount } from 'svelte';
  import { get } from 'svelte/store';
  import {
    BATTLE_REVIEW_CONTEXT_KEY,
    createDefaultTimelineFilters
  } from '../../systems/battleReview/state.js';

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
    reducedMotion,
    displayParty,
    displayFoes,
    currentTab,
    eventsStatus,
    loadEvents
  } = context;

  const FILTER_ID_PATTERN = /[^a-z0-9._:-]/gi;
  const MIN_ZOOM = 5;

  let chartEl;
  let chartWidth = 0;
  const chartHeight = 220;

  onMount(() => {
    if (get(eventsStatus) === 'idle') {
      loadEvents();
    }
    if (!chartEl) return undefined;
    chartWidth = chartEl.clientWidth;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chartWidth = entry.contentRect.width;
      }
    });
    observer.observe(chartEl);
    return () => observer.disconnect();
  });

  $: filters = $timelineFilters;
  $: projection = $timeline;
  $: metricsOptions = $timelineMetrics;
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
  $: reducedAnimations = (filters?.respectMotion ?? true) && $reducedMotion;
  $: areaPath = buildAreaPath(projection?.buckets ?? [], projection?.maxValue ?? 0, chartWidth, chartHeight, 'total');
  $: focusPath = buildLinePath(projection?.buckets ?? [], projection?.maxValue ?? 0, chartWidth, chartHeight, 'focus');
  $: cursorX = computeCursorX($timelineCursor?.time, projection?.start, projection?.end, chartWidth);
  $: summaryMetric = metricsOptions.find((option) => option.id === filters.metric) || metricsOptions[0];
  $: summaryTotal = formatAmount(projection?.totalAmount ?? 0);
  $: cursorLabel = formatSeconds($timelineCursor?.time ?? projection?.start ?? 0);

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

  function buildAreaPath(buckets, maxValue, width, height, key) {
    if (!Array.isArray(buckets) || !buckets.length || !width || !height) return '';
    const safeMax = maxValue > 0 ? maxValue : 1;
    if (buckets.every((bucket) => !bucket || !bucket[key])) {
      return `M0,${height} L${width},${height} L${width},${height} Z`;
    }
    const step = buckets.length > 1 ? width / (buckets.length - 1) : 0;
    let path = '';
    for (let index = 0; index < buckets.length; index += 1) {
      const value = Math.max(0, Number(buckets[index]?.[key] ?? 0));
      const x = step * index;
      const y = height - (value / safeMax) * height;
      path += `${index === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)} `;
    }
    path += `L${width.toFixed(2)},${height.toFixed(2)} L0,${height.toFixed(2)} Z`;
    return path;
  }

  function buildLinePath(buckets, maxValue, width, height, key) {
    if (!Array.isArray(buckets) || !buckets.length || !width || !height) return '';
    const safeMax = maxValue > 0 ? maxValue : 1;
    if (safeMax <= 0) return '';
    const step = buckets.length > 1 ? width / (buckets.length - 1) : 0;
    let path = '';
    let hasValue = false;
    for (let index = 0; index < buckets.length; index += 1) {
      const value = Math.max(0, Number(buckets[index]?.[key] ?? 0));
      if (value > 0) {
        hasValue = true;
      }
      const x = step * index;
      const y = height - (value / safeMax) * height;
      path += `${index === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)} `;
    }
    return hasValue ? path : '';
  }

  function computeCursorX(time, start, end, width) {
    if (!Number.isFinite(time) || !Number.isFinite(start) || !Number.isFinite(end) || width <= 0 || end <= start) {
      return 0;
    }
    const ratio = Math.min(Math.max((time - start) / (end - start), 0), 1);
    return ratio * width;
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
      setTimelineCursor({ time: projection.start });
    }
  }

  function handleChartPointer(event) {
    if (!projection || !chartEl) return;
    const rect = chartEl.getBoundingClientRect();
    if (rect.width <= 0 || !Number.isFinite(projection.start) || !Number.isFinite(projection.end)) {
      return;
    }
    const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
    const time = projection.start + (projection.end - projection.start) * ratio;
    setTimelineCursor({ time });
  }

  function handleHighlightSelect(item) {
    if (!item) return;
    setTimelineCursor({ time: item.time, eventId: item.id });
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

  <div class="window-controls" aria-label="Timeline zoom controls">
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

  {#if projection?.hasData}
  <div
      class="chart-wrapper"
      class:reduced-motion={reducedAnimations}
      bind:this={chartEl}
      on:pointermove={handleChartPointer}
      on:pointerdown={handleChartPointer}
    >
      <svg viewBox={`0 0 ${Math.max(chartWidth, 1)} ${chartHeight}`} preserveAspectRatio="none" role="img" aria-label="Timeline graph">
        {#if areaPath}
          <path class="series-total" d={areaPath} />
        {/if}
        {#if focusPath}
          <path class="series-focus" d={focusPath} />
        {/if}
        <line class="cursor-line" x1={cursorX} x2={cursorX} y1="0" y2={chartHeight} />
      </svg>
      <div class="chart-meta">
        <span>T+{cursorLabel}</span>
        <span>{summaryMetric?.label ?? 'Total'}: {summaryTotal}</span>
      </div>
    </div>

    <div class="timeline-highlights" aria-live="polite">
      {#if projection.focusId}
        <h4>{focusLabel} ability highlights</h4>
        {#if projection.highlightEvents.length}
          <ul>
            {#each projection.highlightEvents as item (item.id)}
              <li>
                <button
                  type="button"
                  class:active={item.id === $timelineCursor?.eventId}
                  on:click={() => handleHighlightSelect(item)}
                >
                  <span class="highlight-time">T+{formatSeconds(item.time)}</span>
                  <span class="highlight-label">{item.label}</span>
                  <span class="highlight-amount">{formatAmount(item.amount)}</span>
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

  .control-group {
    display: flex;
    align-items: center;
    gap: 0.45rem;
  }

  .control-group label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(148, 163, 184, 0.85);
  }

  .control-group input[type='range'] {
    width: 160px;
  }

  .control-value {
    font-weight: 600;
    color: #f8fafc;
  }

  .reset-window {
    padding: 0.35rem 0.65rem;
    border: 1px solid rgba(148, 163, 184, 0.45);
    background: rgba(15, 23, 42, 0.5);
    color: #e2e8f0;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .reset-window:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .reset-window:not(:disabled):hover,
  .reset-window:not(:disabled):focus-visible {
    background: rgba(56, 189, 248, 0.25);
    border-color: rgba(125, 211, 252, 0.65);
  }

  .chart-wrapper {
    position: relative;
    border: 1px solid rgba(30, 64, 175, 0.45);
    background: rgba(15, 23, 42, 0.45);
    padding: 0.75rem;
  }

  .chart-wrapper svg {
    width: 100%;
    height: 220px;
  }

  .chart-wrapper.reduced-motion svg {
    transition: none;
  }

  .series-total {
    fill: rgba(56, 189, 248, 0.28);
    stroke: rgba(56, 189, 248, 0.55);
    stroke-width: 1.5;
  }

  .series-focus {
    fill: none;
    stroke: rgba(249, 115, 22, 0.9);
    stroke-width: 2;
  }

  .cursor-line {
    stroke: rgba(226, 232, 240, 0.65);
    stroke-width: 1;
    stroke-dasharray: 3 4;
  }

  .chart-meta {
    margin-top: 0.5rem;
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    color: rgba(226, 232, 240, 0.85);
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
    grid-template-columns: 80px minmax(0, 1fr) 80px;
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
  }
</style>
