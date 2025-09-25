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
    background: rgba(15, 23, 42, 0.7);
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.3);
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
    border: 1px solid rgba(248, 250, 252, 0.35);
    background: rgba(15, 23, 42, 0.8);
    color: #f8fafc;
    font-size: 0.75rem;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .close-btn:hover {
    background: rgba(59, 130, 246, 0.25);
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
  }

  .event-type {
    color: rgba(59, 130, 246, 0.9);
  }

  .event-text {
    flex: 1;
    word-break: break-word;
  }
</style>
