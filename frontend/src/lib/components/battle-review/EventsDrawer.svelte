<script>
  import { getContext } from 'svelte';
  import { BATTLE_REVIEW_CONTEXT_KEY } from '../../systems/battleReview/state.js';

  const MAX_EVENTS = 250;
  const context = getContext(BATTLE_REVIEW_CONTEXT_KEY);
  const {
    eventsOpen,
    eventsStatus,
    toggleEvents,
    loadEvents,
    timeline,
    timelineCursor,
    setTimelineCursor
  } = context;

  $: if ($eventsOpen && $eventsStatus === 'idle') {
    loadEvents();
  }

  $: filteredEvents = ($timeline?.filteredEvents ?? []).slice(-MAX_EVENTS);
  $: emptyMessage = buildEmptyMessage($eventsStatus, filteredEvents, $timeline?.hasData ?? false);

  function buildEmptyMessage(status, events, hasData) {
    if (status === 'loading') return 'Loading events…';
    if (events.length) return '';
    if (!hasData) return 'No timeline data is available yet.';
    return 'No events matched the current filters.';
  }

  function formatSeconds(value) {
    if (!Number.isFinite(value)) return '0.0s';
    return `${Math.max(0, value).toFixed(1)}s`;
  }

  function formatAmount(value) {
    if (!Number.isFinite(value)) return null;
    return Math.round(value).toLocaleString();
  }

  function eventAmount(event) {
    const rawAmount = event?.amount ?? event?.raw?.amount;
    return formatAmount(rawAmount);
  }

  function formatEventLabel(event) {
    const raw = event?.raw || {};
    const type = event?.eventType || raw.event_type || 'event';
    const attacker = event?.attacker || raw.attacker_id || '—';
    const target = event?.target || raw.target_id || '—';
    return `${type} • ${attacker} → ${target}`;
  }

  function selectEvent(event) {
    if (!event) return;
    setTimelineCursor({ time: event.time, eventId: event.id });
  }
</script>

{#if $eventsOpen}
  <section class="events-drawer" aria-label="Battle event log">
    <header class="drawer-header">
      <h3>Battle Event Log</h3>
      <button type="button" class="close-btn" on:click={toggleEvents}>Close</button>
    </header>
    <div class="drawer-body">
      {#if emptyMessage}
        <p class="drawer-message">{emptyMessage}</p>
      {:else}
        <ul class="events-list">
          {#each filteredEvents as event (event.id)}
            <li>
              <button
                type="button"
                class:active={event.id === $timelineCursor?.eventId}
                on:click={() => selectEvent(event)}
              >
                <span class="event-time">T+{formatSeconds(event.time)}</span>
                <span class="event-text">{formatEventLabel(event)}</span>
                {@const amount = eventAmount(event)}
                {#if amount}
                  <span class="event-amount">{amount}</span>
                {/if}
              </button>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  </section>
{/if}

<style>
  .events-drawer {
    background: linear-gradient(0deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.04)), var(--glass-bg);
    border: var(--glass-border);
    box-shadow: var(--glass-shadow);
    backdrop-filter: var(--glass-filter);
    border-radius: 0;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 20rem;
  }

  .drawer-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .drawer-header h3 {
    margin: 0;
    font-size: 0.95rem;
    color: #f1f5f9;
  }

  .close-btn {
    margin-left: auto;
    appearance: none;
    border: 1px solid rgba(148, 163, 184, 0.55);
    background: color-mix(in oklab, var(--glass-bg) 82%, rgba(148, 163, 184, 0.35) 18%);
    color: #f8fafc;
    font-size: 0.75rem;
    padding: 0.25rem 0.7rem;
    border-radius: 0;
    cursor: pointer;
    transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
  }

  .close-btn:hover,
  .close-btn:focus-visible {
    background: color-mix(in oklab, rgba(56, 189, 248, 0.22) 45%, var(--glass-bg) 55%);
    border-color: rgba(125, 211, 252, 0.6);
    color: #e0f2fe;
  }

  .close-btn:focus-visible {
    outline: 2px solid rgba(125, 211, 252, 0.75);
    outline-offset: 2px;
  }

  .drawer-body {
    flex: 1;
    overflow-y: auto;
  }

  .drawer-message {
    margin: 0;
    text-align: center;
    color: rgba(226, 232, 240, 0.75);
    font-size: 0.85rem;
    padding: 1.5rem 0;
  }

  .events-list {
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .events-list li button {
    width: 100%;
    display: grid;
    grid-template-columns: 80px minmax(0, 1fr) 70px;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.5rem;
    font-size: 0.76rem;
    background: color-mix(in oklab, rgba(15, 23, 42, 0.75) 70%, transparent 30%);
    color: rgba(226, 232, 240, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.25);
    cursor: pointer;
  }

  .events-list li button:hover,
  .events-list li button:focus-visible,
  .events-list li button.active {
    border-color: rgba(125, 211, 252, 0.65);
    background: rgba(56, 189, 248, 0.2);
    color: #f0f9ff;
  }

  .event-time {
    font-variant-numeric: tabular-nums;
    color: rgba(148, 163, 184, 0.85);
  }

  .event-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .event-amount {
    justify-self: end;
    color: #f8fafc;
    font-weight: 600;
  }
</style>
