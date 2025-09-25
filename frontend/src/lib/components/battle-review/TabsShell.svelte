<script>
  import { getContext } from 'svelte';
  import { Swords, User } from 'lucide-svelte';
  import LegacyFighterPortrait from '../battle/LegacyFighterPortrait.svelte';
  import TimelineRegion from './TimelineRegion.svelte';
  import EntityTableContainer from './EntityTableContainer.svelte';
  import { BATTLE_REVIEW_CONTEXT_KEY } from '../../systems/battleReview/state.js';

  const context = getContext(BATTLE_REVIEW_CONTEXT_KEY);
  const { availableTabs, activeTab, reducedMotion } = context;

  function selectTab(id) {
    activeTab.set(id);
  }
</script>

<div class="tabs-shell">
  <nav class="metric-tabs" aria-label="Battle review entities">
    {#each $availableTabs as tab (tab.id)}
      <button
        type="button"
        class="tab-chip"
        class:active={$activeTab === tab.id}
        on:click={() => selectTab(tab.id)}
        aria-label={tab.rank ? `${tab.label} — ${tab.rank}` : tab.label}
      >
        {#if tab.id === 'overview'}
          <Swords size={18} />
        {:else if tab.entity}
          <div class="portrait-chip">
            <LegacyFighterPortrait
              fighter={tab.entity}
              rankTag={tab.rank ?? tab.entity.rank}
              reducedMotion={$reducedMotion}
            />
          </div>
        {:else}
          <User size={18} />
        {/if}
        <span class="tab-label">{tab.label}</span>
      </button>
    {/each}
  </nav>

  <section class="timeline-first-grid">
    <TimelineRegion />
    <EntityTableContainer />
  </section>
</div>

<style>
  .tabs-shell {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    background: rgba(15, 23, 42, 0.45);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.2);
  }

  .metric-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
  }

  .tab-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.45rem 0.75rem;
    border-radius: 999px;
    border: 1px solid rgba(148, 163, 184, 0.4);
    background: rgba(15, 23, 42, 0.7);
    color: #cbd5f5;
    cursor: pointer;
    font-size: 0.82rem;
    transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
  }

  .tab-chip:hover,
  .tab-chip.active {
    background: rgba(56, 189, 248, 0.18);
    border-color: rgba(125, 211, 252, 0.65);
    color: #e0f2fe;
  }

  .tab-chip.active {
    transform: translateY(-2px);
  }

  .portrait-chip {
    --portrait-size: 2.75rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .portrait-chip :global(.portrait-wrap) {
    border-radius: 8px;
    overflow: hidden;
  }

  .tab-label {
    white-space: nowrap;
  }

  .timeline-first-grid {
    display: grid;
    grid-template-columns: minmax(0, 2.2fr) minmax(0, 3fr);
    gap: 1.25rem;
    align-items: stretch;
  }

  @media (max-width: 1200px) {
    .timeline-first-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
