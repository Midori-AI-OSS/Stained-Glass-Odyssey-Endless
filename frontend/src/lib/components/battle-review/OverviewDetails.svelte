<script>
  import { Sparkles, Coins } from 'lucide-svelte';
  import { effectTooltips, fmt } from './utils.js';

  export let detailSections = [];
  export let resources = [];
  export let effectApplications = [];
</script>

{#each detailSections as section}
  {#if section.entries.length > 0}
    <div class="detail-section">
      <div class="detail-title">
        <svelte:component this={section.icon} size={16} />
        {section.title}
      </div>
      <div class="detail-grid">
        {#each section.entries as entry}
          <div class="detail-item">
            <span class="detail-name">{entry.entity}</span>
            <span class="detail-stats">{entry.label}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
{/each}

{#if resources.length > 0}
  <div class="detail-section">
    <div class="detail-title">
      <Coins size={16} />
      Resource Usage
    </div>
    <div class="detail-grid">
      {#each resources as row}
        <div class="detail-item">
          <span class="detail-name">{row.entity}</span>
          <span class="detail-stats">{row.label}</span>
        </div>
      {/each}
    </div>
  </div>
{/if}

{#if effectApplications.length > 0}
  <div class="detail-section">
    <div class="detail-title">
      <Sparkles size={16} />
      Effect Applications
    </div>
    <div class="detail-grid">
      {#each effectApplications as entry}
        <div class="detail-item">
          <span class="detail-name">{entry.name}</span>
          <span class="detail-stats">×{entry.count}</span>
          <div class="effect-tooltip">{effectTooltips[entry.name] || `Effect applied ${entry.count} time${entry.count !== 1 ? 's' : ''}`}</div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<style>
  .detail-section {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
    background: rgba(15, 23, 42, 0.3);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.18);
  }

  .detail-title {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: rgba(226, 232, 240, 0.95);
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.5rem;
  }

  .detail-item {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    background: rgba(15, 23, 42, 0.45);
    border-radius: 8px;
    padding: 0.4rem 0.6rem;
    font-size: 0.75rem;
    border: 1px solid rgba(148, 163, 184, 0.18);
  }

  .detail-name {
    font-weight: 600;
    color: #f8fafc;
  }

  .detail-stats {
    color: rgba(226, 232, 240, 0.75);
  }

  .effect-tooltip {
    font-size: 0.7rem;
    color: rgba(226, 232, 240, 0.8);
  }
</style>
