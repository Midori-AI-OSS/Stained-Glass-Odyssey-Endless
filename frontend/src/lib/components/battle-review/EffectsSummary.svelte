<script>
  import { Sparkles, Shield, CreditCard } from 'lucide-svelte';
  import { effectTooltips } from './utils.js';

  export let relicEffects = {};
  export let cardEffects = {};

  function sortedEntries(effects) {
    return Object.entries(effects || {})
      .sort((a, b) => (b[1] || 0) - (a[1] || 0));
  }
</script>

<div class="effects-summary">
  <div class="effects-header">
    <Sparkles size={18} />
    Full Overview
  </div>
  <div class="effects-grid">
    {#if Object.keys(relicEffects || {}).length > 0}
      <div class="effects-column">
        <div class="effects-column-title">
          <Shield size={16} />
          Relic Effects
        </div>
        {#each sortedEntries(relicEffects) as [name, count]}
          <div class="effect-item">
            <span class="effect-name">{name}</span>
            <span class="effect-count">×{count}</span>
          </div>
        {/each}
      </div>
    {/if}
    {#if Object.keys(cardEffects || {}).length > 0}
      <div class="effects-column">
        <div class="effects-column-title">
          <CreditCard size={16} />
          Card Effects
        </div>
        {#each sortedEntries(cardEffects) as [name, count]}
          <div class="effect-item">
            <span class="effect-name">{name}</span>
            <span class="effect-count">×{count}</span>
            <div class="effect-tooltip">{effectTooltips[name] || `Card effect triggered ${count} time${count !== 1 ? 's' : ''}`}</div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .effects-summary {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .effects-header {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    font-weight: 600;
    color: #fdf2f8;
  }

  .effects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .effects-column {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    background: rgba(15, 23, 42, 0.3);
    border-radius: 10px;
    padding: 0.75rem;
    border: 1px solid rgba(59, 130, 246, 0.2);
  }

  .effects-column-title {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: #bae6fd;
  }

  .effect-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
    background: rgba(59, 130, 246, 0.12);
    border-radius: 6px;
    padding: 0.35rem 0.5rem;
    border: 1px solid rgba(59, 130, 246, 0.25);
  }

  .effect-name {
    font-weight: 600;
  }

  .effect-count {
    font-size: 0.7rem;
    color: rgba(226, 232, 240, 0.8);
  }

  .effect-tooltip {
    font-size: 0.7rem;
    color: rgba(226, 232, 240, 0.8);
  }
</style>
