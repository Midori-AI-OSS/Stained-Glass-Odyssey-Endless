<script>
  import { Swords } from 'lucide-svelte';
  import { fmt } from './utils.js';

  export let partyActions = {};
  export let foeActions = {};
</script>

{#if Object.keys(partyActions).length > 0 || Object.keys(foeActions).length > 0}
  <div class="entity-section">
    <h4 class="section-title">
      <Swords size={16} />
      Action Type Comparison
    </h4>
    <div class="action-columns">
      <div>
        <div class="column-title player">Player Party Actions</div>
        <div class="damage-breakdown">
          {#each Object.entries(partyActions).sort((a, b) => b[1] - a[1]) as [action, amount]}
            <div class="damage-item">
              <span class="damage-element">{action}</span>
              <span class="damage-amount">{fmt(amount)}</span>
            </div>
          {/each}
        </div>
      </div>
      <div>
        <div class="column-title foe">Foe Actions</div>
        <div class="damage-breakdown">
          {#each Object.entries(foeActions).sort((a, b) => b[1] - a[1]) as [action, amount]}
            <div class="damage-item">
              <span class="damage-element">{action}</span>
              <span class="damage-amount">{fmt(amount)}</span>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .entity-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    background: rgba(15, 23, 42, 0.35);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.18);
  }

  .section-title {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.95rem;
    font-weight: 600;
    color: #e2e8f0;
  }

  .action-columns {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
  }

  .column-title {
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .column-title.player {
    color: #4ade80;
  }

  .column-title.foe {
    color: #f87171;
  }

  .damage-breakdown {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.5rem;
  }

  .damage-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    font-size: 0.78rem;
  }
</style>
