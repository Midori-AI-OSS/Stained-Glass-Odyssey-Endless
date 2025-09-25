<script>
  import { getContext } from 'svelte';
  import { BATTLE_REVIEW_CONTEXT_KEY } from '../../systems/battleReview/state.js';

  const { eventsOpen, events, eventsStatus, toggleEvents, loadEvents } = getContext(BATTLE_REVIEW_CONTEXT_KEY);

  $: if ($eventsOpen && $eventsStatus === 'idle') {
    loadEvents();
  }
</script>

{#if $eventsOpen}
  <section class="events-drawer" aria-label="Battle event log">
    <header class="drawer-header">
      <h3>Battle Event Log</h3>
      <button type="button" class="close-btn" on:click={toggleEvents}>Close</button>
    </header>
    <div class="drawer-body">
      {#if $eventsStatus === 'loading'}
        <p class="drawer-message">Loading events…</p>
      {:else if !$events.length}
        <p class="drawer-message">No events available.</p>
      {:else}
        <ul class="events-list">
          {#each $events.slice(-200) as event, index}
            <li class="event-row">
              <span class="event-type">[{event.event_type || 'event'}]</span>
              <span class="event-text">
                {event.attacker_id || '—'} → {event.target_id || '—'}
                {#if event.amount != null}
                  ({event.amount})
                {/if}
                {#if event.damage_type}
                  [{event.damage_type}]
                {/if}
                {#if event.source_type}
                  {` {${event.source_type}}`}
                {/if}
              </span>
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
    max-height: 18rem;
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

  .event-row {
    display: flex;
    gap: 0.5rem;
    font-size: 0.76rem;
    color: rgba(226, 232, 240, 0.9);
    padding: 0.35rem 0.4rem;
    background: color-mix(in oklab, rgba(15, 23, 42, 0.75) 75%, transparent 25%);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 0;
  }

  .event-type {
    color: rgba(59, 130, 246, 0.9);
  }

  .event-text {
    flex: 1;
    word-break: break-word;
  }
</style>
