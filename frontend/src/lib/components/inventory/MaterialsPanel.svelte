<script>
  import { getMaterialIcon, onIconError } from '../../systems/materialAssetLoader.js';

  export let materials = [];
  export let select = () => {};
  export let selectedId = null;

  // Star color palette (match CardArt/Inventory)
  const starColors = {
    1: '#808080', // gray
    2: '#1E90FF', // blue
    3: '#228B22', // green
    4: '#800080', // purple
    5: '#FF3B30', // red
    6: '#FFD700', // gold
    fallback: '#708090'
  };

  function getStarsFromId(id) {
    const m = String(id || '').match(/(\d+)/);
    const n = m ? parseInt(m[1], 10) : 1;
    return Math.max(1, Math.min(n || 1, 6));
  }

  function getStarColorFromId(id) {
    const stars = getStarsFromId(id);
    return starColors[stars] || starColors.fallback;
  }
</script>

<div class="materials-grid">
  {#each materials as [id, qty]}
    <button
      type="button"
      class="grid-item material"
      class:selected={selectedId === id}
      on:click={() => select(id, 'material', qty)}
      aria-label={id}
      style={`--accent:${getStarColorFromId(id)}`}
    >
      <div class="item-icon material">
        <img src={getMaterialIcon(id)} alt={id} on:error={onIconError} />
      </div>
      <span class="material-qty">×{qty}</span>
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

  /* Rank-colored tile like inventory overview */
  .grid-item.material {
    background: color-mix(in oklab, var(--accent, #708090) 35%, black);
    border-color: color-mix(in oklab, var(--accent, #708090) 40%, transparent);
    box-shadow: none;
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

  .item-icon.material {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
  }
  .item-icon.material img {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
  .material-qty {
    position: absolute;
    top: 4px;
    right: 6px;
    background: rgba(0,0,0,0.70);
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 0.72rem;
    line-height: 1.1rem;
    padding: 0 0.35rem;
    min-width: 1.25rem;
    text-align: right;
    font-variant-numeric: tabular-nums;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Helvetica Neue, Arial, sans-serif;
    font-weight: 700;
    letter-spacing: 0.01em;
  }
</style>
