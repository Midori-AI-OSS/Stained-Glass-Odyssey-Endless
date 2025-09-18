<script>
  import CurioChoice from './CurioChoice.svelte';
  import CardArt from './CardArt.svelte';
  import { onMount } from 'svelte';
  import { getCardCatalog, getRelicCatalog, getGacha } from '../systems/api.js';
  import { stackItems, formatName } from '../systems/craftingUtils.js';
  export let cards = [];
  export let relics = [];
  let materials = {};
  let selectedMaterial = null;
  const count = (arr) => {
    const map = {};
    for (const id of arr) {
      map[id] = (map[id] || 0) + 1;
    }
    return Object.entries(map);
  };

  // Catalog metadata maps for richer display
  let cardMeta = {};
  let relicMeta = {};
  let metaReady = false;

  const rawIconModules = import.meta.glob('../assets/items/*/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  });
  const iconModules = Object.fromEntries(
    Object.entries(rawIconModules).map(([path, src]) => [path, new URL(src, import.meta.url).href])
  );
  const fallbackIcon = new URL('../assets/items/generic/generic1.png', import.meta.url).href;
  const starColors = {
    1: '#808080',
    2: '#1E90FF',
    3: '#228B22',
    4: '#800080',
    5: '#FF3B30',
    6: '#FFD700',
    fallback: '#708090'
  };

  function onIconError(event) {
    event.target.src = fallbackIcon;
  }

  function getIcon(key) {
    const [rawElement, rawRank] = String(key).split('_');
    const element = String(rawElement || '').toLowerCase();
    const rank = String(rawRank || '').replace(/[^0-9]/g, '') || '1';
    const rankPath = `../assets/items/${element}/${rank}.png`;
    if (iconModules[rankPath]) return iconModules[rankPath];
    const elementPrefix = `../assets/items/${element}/`;
    const elementKeys = Object.keys(iconModules).filter((p) => p.startsWith(elementPrefix));
    const genericRankPath = `${elementPrefix}generic${rank}.png`;
    if (iconModules[genericRankPath]) return iconModules[genericRankPath];
    if (elementKeys.length > 0) return iconModules[elementKeys[0]];
    const genericPath = `../assets/items/generic/generic${rank}.png`;
    return iconModules[genericPath] || fallbackIcon;
  }

  function getStarColor(key) {
    const k = String(key || '');
    // Extract first number group anywhere (handles formats like "fire_3", "fire_generic3", etc.)
    const m = k.match(/(\d+)/);
    const n = m ? parseInt(m[1], 10) : NaN;
    const rank = Number.isFinite(n) ? Math.max(1, Math.min(n, 6)) : 1;
    return starColors[rank] || starColors.fallback;
  }

  onMount(async () => {
    try {
      const [cards, relics, gacha] = await Promise.all([
        getCardCatalog(),
        getRelicCatalog(),
        getGacha()
      ]);
      cardMeta = Object.fromEntries(cards.map(c => [c.id, c]));
      relicMeta = Object.fromEntries(relics.map(r => [r.id, r]));
      materials = stackItems(gacha.items);
    } catch (e) {
      // Silently ignore; components will fallback to id-only display
    }
    metaReady = true;
  });

  // Helpers to resolve stars and names safely
  const cardStars = (id) => (cardMeta?.[id]?.stars ?? 1) | 0;
  const relicStars = (id) => (relicMeta?.[id]?.stars ?? 1) | 0;
  const cardName = (id) => String(cardMeta?.[id]?.name || id);
  const relicName = (id) => String(relicMeta?.[id]?.name || id);

  // Sort order: Cards section first (already rendered first), then Relics.
  // Within each section: sort by star rank descending, then by name A→Z for stability.
  $: cardIdsUnique = Array.from(new Set(cards || []));
  $: sortedCardIds = [...cardIdsUnique].sort((a, b) => {
    const s = cardStars(b) - cardStars(a);
    if (s !== 0) return s;
    return cardName(a).localeCompare(cardName(b));
  });

  $: relicEntries = count(relics || []); // [id, qty]
  $: sortedRelicEntries = [...relicEntries].sort((a, b) => {
    const [idA] = a; const [idB] = b;
    const s = relicStars(idB) - relicStars(idA);
    if (s !== 0) return s;
    return relicName(idA).localeCompare(relicName(idB));
  });
</script>

<div class="inv-root" data-testid="inventory-panel">
  {#if metaReady && cards.length}
    <h3>Cards</h3>
    <div class="cards-grid">
      {#each sortedCardIds as id}
        {#key id}
          <CardArt entry={{ id, name: cardName(id), stars: cardStars(id), about: (cardMeta[id]?.about || '') }} type="card" />
        {/key}
      {/each}
    </div>
  {/if}
  {#if metaReady && relics.length}
    <h3>Relics</h3>
    <div class="relics-grid">
      {#each sortedRelicEntries as [id, qty]}
        {#key id}
          <div class="relic-cell">
            <CurioChoice entry={{ id, name: relicName(id), stars: relicStars(id), about: (relicMeta[id]?.about || '') }} />
            <span class="qty">x{qty}</span>
          </div>
        {/key}
      {/each}
    </div>
  {/if}
  {#if metaReady && Object.keys(materials).length}
    <h3>Upgrade Materials</h3>
    <div class="materials-section">
      <div class="materials-grid" data-testid="materials-grid">
        {#each Object.entries(materials) as [key, value]}
          <button
            class="grid-item"
            style={`--star-color: ${getStarColor(key)}`}
            on:click={() => (selectedMaterial = key)}
            title={formatName(key)}
          >
            <img
              class="item-icon"
              src={getIcon(key)}
              alt={key}
              on:error={onIconError}
            />
            <span class="badge">{value}</span>
          </button>
        {/each}
      </div>
      <div class="detail">
        {#if selectedMaterial}
          <img
            class="detail-icon"
            style={`--star-color: ${getStarColor(selectedMaterial)}`}
            src={getIcon(selectedMaterial)}
            alt={selectedMaterial}
            on:error={onIconError}
          />
          <div class="detail-name">{formatName(selectedMaterial)}</div>
          <div class="detail-count">x{materials[selectedMaterial]}</div>
        {:else}
          <p class="placeholder">Select a material</p>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .inv-root { display:flex; flex-direction:column; gap:0.5rem; }
  .grid { display:flex; flex-wrap:wrap; gap:0.5rem; }
  .cards-grid {
    display: grid;
    /* Fixed track width prevents extra horizontal padding inside cells */
    grid-template-columns: repeat(auto-fill, 280px);
    column-gap: 4px;
    row-gap: 6px;
    align-items: start;
    justify-content: center;
    justify-items: start;
  }
  .relics-grid {
    display: grid;
    /* Match CardArt default width; add breathing room */
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.25rem;
    align-items: start;
    justify-items: center;
  }
  /* Inventory is read-only; disable relic button clicks within this panel */
  .relics-grid :global(.curio) { pointer-events: none; }
  .relic-cell { display:flex; flex-direction:column; align-items:center; font-size:0.85rem; }
  .qty { margin-top: 0.25rem; opacity: 0.9; }
  .materials-section {
    display: grid;
    grid-template-columns: 1fr 220px;
    gap: 0.75rem;
    align-items: start;
  }
  .materials-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(48px, 1fr));
    gap: 0.5rem;
  }
  .grid-item {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    aspect-ratio: 1 / 1;
    background: transparent;
    border: none;
    padding: 0;
    cursor: pointer;
  }
  .item-icon {
    width: 100%;
    height: 100%;
    object-fit: contain;
    border: 2px solid var(--star-color, #708090);
    box-shadow: 0 0 0 1px var(--star-color, #708090);
    background: var(--star-color, #000);
  }
  .badge {
    position: absolute;
    right: 2px;
    bottom: 2px;
    background: rgba(0,0,0,0.75);
    color: #fff;
    border: 1px solid #fff;
    padding: 0 0.25rem;
    font-size: 0.7rem;
    line-height: 1.1rem;
  }
  .detail {
    border: 2px solid #fff;
    padding: 0.5rem;
    text-align: center;
    min-height: 80px;
  }
  .detail-icon {
    width: 64px;
    height: 64px;
    border: 2px solid var(--star-color, #708090);
    box-shadow: 0 0 0 1px var(--star-color, #708090);
    margin-bottom: 0.25rem;
    background: var(--star-color, #000);
  }
  .detail-name { font-size: 0.9rem; margin-bottom: 0.15rem; }
  .detail-count { font-size: 0.8rem; color: #ddd; }
  .placeholder { font-size: 0.8rem; color: #ccc; }
</style>
