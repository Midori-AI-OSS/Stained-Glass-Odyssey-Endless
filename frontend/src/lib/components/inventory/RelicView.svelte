<script>
  import CurioChoice from '../CurioChoice.svelte';

  export let relics = [];
  export let select = () => {};
  export let selectedId = null;
</script>

<div class="relics-grid">
  {#each relics as [entry, qty]}
    <button
      type="button"
      class="relic-cell"
      class:selected={selectedId === entry.id}
      on:click={() => select(entry.id, 'relic', qty)}
      aria-label={entry.name}
    >
      <div class="relic-wrap">
        <CurioChoice entry={entry} />
        {#if Number(qty) > 1}
          <span class="qty-badge">×{qty}</span>
        {/if}
      </div>
    </button>
  {/each}
</div>

<style>
  .relics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.25rem;
    align-items: start;
    justify-items: center;
  }

  .relic-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    padding: 0;
    border: none;
    background: none;
    cursor: pointer;
  }

  .relic-cell.selected {
    outline: 2px solid rgba(120, 180, 255, 0.6);
    outline-offset: 4px;
  }

  .relic-wrap { position: relative; }
  .qty-badge {
    position: absolute;
    top: 6px;
    right: 10px;
    background: rgba(0, 0, 0, 0.7);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 0 0.35rem;
    font-size: 0.8rem;
    line-height: 1.1rem;
    border-radius: 6px;
  }
</style>
