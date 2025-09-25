<script>
  import { getContext } from 'svelte';
  import OverviewPanel from './OverviewPanel.svelte';
  import EntityDetailPanel from './EntityDetailPanel.svelte';
  import StatsPanel from './StatsPanel.svelte';
  import { BATTLE_REVIEW_CONTEXT_KEY } from '../../systems/battleReview/state.js';

  const { currentTab } = getContext(BATTLE_REVIEW_CONTEXT_KEY);
</script>

<div class="entity-container">
  <section class="metrics-area">
    {#if $currentTab?.id === 'overview'}
      <OverviewPanel />
    {:else}
      <EntityDetailPanel />
    {/if}
  </section>
  <StatsPanel />
</div>

<style>
  .entity-container {
    display: grid;
    grid-template-columns: minmax(0, 3fr) minmax(220px, 1fr);
    gap: 1.5rem;
    align-items: start;
  }

  @media (max-width: 1100px) {
    .entity-container {
      grid-template-columns: 1fr;
    }
  }

  .metrics-area {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
</style>
