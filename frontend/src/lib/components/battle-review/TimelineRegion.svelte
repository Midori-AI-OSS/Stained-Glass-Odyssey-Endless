<script>
  import { getContext } from 'svelte';
  import { BATTLE_REVIEW_CONTEXT_KEY } from '../../systems/battleReview/state.js';

  const { timeline } = getContext(BATTLE_REVIEW_CONTEXT_KEY);
</script>

<section class="timeline-region" aria-label="Battle timeline">
  <header class="timeline-header">Battle Timeline</header>
  {#if $timeline.length}
    <ol class="timeline-track">
      {#each $timeline as event (event.id)}
        <li class="timeline-item">
          <div class="timeline-marker"></div>
          <div class="timeline-content">
            <div class="event-title">{event.label}</div>
            <div class="event-meta">
              {#if event.time !== null}
                <span class="meta-entry">T+{event.time}</span>
              {/if}
              {#if event.attacker}
                <span class="meta-entry">{event.attacker}</span>
              {/if}
              {#if event.target}
                <span class="meta-entry">→ {event.target}</span>
              {/if}
              {#if event.amount != null}
                <span class="meta-entry">{event.amount}</span>
              {/if}
              {#if event.damageType}
                <span class="meta-entry">[{event.damageType}]</span>
              {/if}
            </div>
          </div>
        </li>
      {/each}
    </ol>
  {:else}
    <p class="timeline-empty">Timeline will populate once combat events are recorded.</p>
  {/if}
</section>

<style>
  .timeline-region {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    background: rgba(15, 23, 42, 0.3);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(30, 64, 175, 0.35);
    min-height: 18rem;
  }

  .timeline-header {
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.82rem;
    color: #bae6fd;
  }

  .timeline-track {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 20rem;
    overflow-y: auto;
  }

  .timeline-item {
    display: grid;
    grid-template-columns: 18px 1fr;
    gap: 0.75rem;
    align-items: start;
  }

  .timeline-marker {
    width: 10px;
    height: 10px;
    background: #38bdf8;
    border-radius: 999px;
    margin-top: 0.35rem;
    box-shadow: 0 0 6px rgba(56, 189, 248, 0.75);
  }

  .timeline-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.35rem 0.5rem;
    background: rgba(2, 132, 199, 0.15);
    border-radius: 8px;
    border: 1px solid rgba(2, 132, 199, 0.3);
  }

  .event-title {
    font-weight: 600;
    font-size: 0.85rem;
    color: #f8fafc;
  }

  .event-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    font-size: 0.72rem;
    color: rgba(226, 232, 240, 0.85);
  }

  .meta-entry {
    padding: 0.1rem 0.35rem;
    background: rgba(15, 23, 42, 0.6);
    border-radius: 999px;
    border: 1px solid rgba(148, 163, 184, 0.3);
  }

  .timeline-empty {
    margin: 0;
    padding: 2rem 0;
    text-align: center;
    color: rgba(148, 163, 184, 0.8);
    font-size: 0.85rem;
  }
</style>
