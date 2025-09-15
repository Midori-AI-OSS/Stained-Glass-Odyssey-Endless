<script>
  import { getMaterialIcon, onIconError } from '../../systems/materialAssetLoader.js';

  export let materials = [];
  export let select = () => {};
  export let selectedId = null;
</script>

<div class="materials-grid">
  {#each materials as [id, qty]}
    <button
      type="button"
      class="grid-item"
      class:selected={selectedId === id}
      on:click={() => select(id, 'material', qty)}
      aria-label={id}
    >
      <img class="item-icon" src={getMaterialIcon(id)} alt={id} on:error={onIconError} />
      <span class="item-quantity">×{qty}</span>
    </button>
  {/each}
</div>

<style>
  .materials-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 0.75rem;
    align-items: start;
  }

  .grid-item {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    aspect-ratio: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .grid-item:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(120, 180, 255, 0.5);
  }

  .grid-item.selected {
    background: rgba(120, 180, 255, 0.2);
    border-color: rgba(120, 180, 255, 0.7);
    box-shadow: 0 0 8px rgba(120, 180, 255, 0.3);
  }

  .item-icon {
    width: 100%;
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .item-quantity {
    font-size: 0.7rem;
    color: rgba(255, 255, 255, 0.88);
  }
</style>
