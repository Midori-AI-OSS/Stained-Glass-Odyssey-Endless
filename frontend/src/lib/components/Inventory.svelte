<script>
  import { onMount } from 'svelte';
  import { CreditCard, Gem, Hammer, Box, RotateCcw } from 'lucide-svelte';
  import { getCardCatalog, getRelicCatalog, getGacha } from '../systems/api.js';
  import { stackItems, formatName } from '../systems/craftingUtils.js';
  import CardView from './inventory/CardView.svelte';
  import RelicView from './inventory/RelicView.svelte';
  import MaterialsPanel from './inventory/MaterialsPanel.svelte';
  import { getMaterialIcon, onIconError } from '../systems/materialAssetLoader.js';

  export let cards = [];
  export let relics = [];
  // Upgrade materials are loaded from gacha inventory (backend), not passed in
  let materials = {}; // key -> count

  // Current tab and selected item state (Upgrades first by default)
  let activeTab = 'materials';
  let selectedItem = null;
  
  // Catalog metadata
  let cardMeta = {};
  let relicMeta = {};
  let metaReady = false;

  onMount(async () => {
    try {
      const [cardList, relicList, gacha] = await Promise.all([
        getCardCatalog(),
        getRelicCatalog(),
        getGacha()
      ]);
      cardMeta = Object.fromEntries(cardList.map(c => [c.id, c]));
      relicMeta = Object.fromEntries(relicList.map(r => [r.id, r]));
      materials = stackItems(gacha?.items || {});
    } catch (e) {
      // Silently ignore; components will fallback to id-only display
    }
    metaReady = true;
  });

  async function reloadInventory() {
    try {
      const [cardList, relicList, gacha] = await Promise.all([
        getCardCatalog(),
        getRelicCatalog(),
        getGacha()
      ]);
      cardMeta = Object.fromEntries(cardList.map(c => [c.id, c]));
      relicMeta = Object.fromEntries(relicList.map(r => [r.id, r]));
      materials = stackItems(gacha?.items || {});
      // Clean up selection if item no longer present
      if (selectedItem) {
        const id = selectedItem.id;
        if (selectedItem.type === 'card' && !cardMeta[id]) selectedItem = null;
        if (selectedItem.type === 'relic' && !relicMeta[id]) selectedItem = null;
        if (selectedItem.type === 'material' && !(id in materials)) selectedItem = null;
      }
    } catch {}
  }

  // Helper functions
  const count = (arr) => {
    const map = {};
    for (const id of arr) {
      map[id] = (map[id] || 0) + 1;
    }
    return Object.entries(map);
  };

  const cardStars = (id) => (cardMeta?.[id]?.stars ?? 1) | 0;
  const relicStars = (id) => (relicMeta?.[id]?.stars ?? 1) | 0;
  const cardName = (id) => String(cardMeta?.[id]?.name || id);
  const relicName = (id) => String(relicMeta?.[id]?.name || id);
  const cardDesc = (id) => String(cardMeta?.[id]?.about || 'No description available.');
  const relicDesc = (id) => String(relicMeta?.[id]?.about || 'No description available.');

  // Processed data
  $: cardEntries = count(cards || []);
  $: relicEntries = count(relics || []);
  $: materialEntries = Object.entries(materials || {}); // [key, qty]

  $: sortedCardEntries = [...cardEntries].sort((a, b) => {
    const [idA] = a; const [idB] = b;
    const s = cardStars(idB) - cardStars(idA);
    if (s !== 0) return s;
    return cardName(idA).localeCompare(cardName(idB));
  });
  $: sortedCards = sortedCardEntries.map(([id, qty]) => [
    { id, name: cardName(id), stars: cardStars(id), about: cardDesc(id) },
    qty
  ]);

  $: sortedRelicEntries = [...relicEntries].sort((a, b) => {
    const [idA] = a; const [idB] = b;
    const s = relicStars(idB) - relicStars(idA);
    if (s !== 0) return s;
    return relicName(idA).localeCompare(relicName(idB));
  });
  $: sortedRelics = sortedRelicEntries.map(([id, qty]) => [
    { id, name: relicName(id), stars: relicStars(id), about: relicDesc(id) },
    qty
  ]);

  // Get total counts
  $: cardCount = cards?.length || 0;
  $: relicCount = relics?.length || 0;
  $: materialCount = (materialEntries || []).reduce((sum, [, qty]) => sum + (qty | 0), 0);

  // Star rating colors (match CardArt.svelte palette exactly)
  const getStarColor = (stars) => {
    switch (Number(stars) || 1) {
      case 6: return '#FFD700'; // Gold
      case 5: return '#FF3B30'; // Red
      case 4: return '#800080'; // Purple
      case 3: return '#228B22'; // Green
      case 2: return '#1E90FF'; // Blue
      default: return '#808080'; // Gray
    }
  };

  // Item selection
  const selectItem = (id, type, qty = 1) => {
    if (type === 'card') {
      selectedItem = {
        id,
        type: 'card',
        name: cardName(id),
        stars: cardStars(id),
        description: cardDesc(id),
        quantity: qty,
        meta: cardMeta[id]
      };
    } else if (type === 'relic') {
      selectedItem = {
        id,
        type: 'relic',
        name: relicName(id),
        stars: relicStars(id),
        description: relicDesc(id),
        quantity: qty,
        meta: relicMeta[id]
      };
    } else {
      // material
      selectedItem = {
        id,
        type: 'material',
        name: formatName(id),
        stars: parseInt(String(id).split('_')[1] || '1', 10),
        description: 'Upgrade material used for character enhancements.',
        quantity: qty,
        meta: null
      };
    }
  };
  // Utility: remove visual star glyphs from strings for text-only fields
  const stripStars = (s) => String(s || '').replace(/★+/g, '').replace(/\s{2,}/g, ' ').trim();

  // Set initial selection when data loads
  $: if (metaReady && !selectedItem) {
    if (activeTab === 'cards' && sortedCards.length > 0) {
      const [entry, qty] = sortedCards[0];
      selectItem(entry.id, 'card', qty);
    } else if (activeTab === 'relics' && sortedRelics.length > 0) {
      const [entry, qty] = sortedRelics[0];
      selectItem(entry.id, 'relic', qty);
    } else if (activeTab === 'materials' && materialEntries.length > 0) {
      const [id, qty] = materialEntries[0];
      selectItem(id, 'material', qty);
    }
  }

  // Switch tabs
  const switchTab = (tab) => {
    activeTab = tab;
    selectedItem = null;
    // Auto-select first item in new tab
    if (tab === 'cards' && sortedCards.length > 0) {
      const [entry, qty] = sortedCards[0];
      selectItem(entry.id, 'card', qty);
    } else if (tab === 'relics' && sortedRelics.length > 0) {
      const [entry, qty] = sortedRelics[0];
      selectItem(entry.id, 'relic', qty);
    } else if (tab === 'materials' && materialEntries.length > 0) {
      const [id, qty] = materialEntries[0];
      selectItem(id, 'material', qty);
    }
  };

  // Icons for materials
</script>

<div class="star-rail-inventory">
  <!-- Header with tabs -->
  <div class="inventory-header">
    <div class="tab-row">
      <button 
        class="tab" 
        class:active={activeTab === 'materials'}
        on:click={() => switchTab('materials')}
      >
        <svelte:component this={Hammer} class="tab-icon" size={18} />
        Upgrades ({materialCount})
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'cards'}
        on:click={() => switchTab('cards')}
      >
        <svelte:component this={CreditCard} class="tab-icon" size={18} />
        Cards ({cardCount})
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'relics'}
        on:click={() => switchTab('relics')}
      >
        <svelte:component this={Gem} class="tab-icon" size={18} />
        Relics ({relicCount})
      </button>
    </div>
    <div class="header-actions">
      <button class="reload-btn" on:click={reloadInventory} title="Reload inventory">
        <RotateCcw size={16} />
        Reload
      </button>
    </div>
  </div>

  <div class="inventory-body">
    <!-- Left side: Item grid -->
    <div class="item-grid-container">
      {#if activeTab === 'cards'}
        <CardView cards={sortedCards} select={selectItem} />
      {:else if activeTab === 'relics'}
        <RelicView relics={sortedRelics} select={selectItem} />
      {:else}
        <MaterialsPanel materials={materialEntries} select={selectItem} />
      {/if}
    </div>

    <!-- Right side: Detail panel -->
    <div class="detail-panel">
      {#if selectedItem}
          <div class="detail-header">
          <h3 class="item-name">{stripStars(selectedItem.name)}</h3>
          <div class="item-meta">
            <div class="item-stars-large" style="color: {getStarColor(selectedItem.stars)}">
              {'★'.repeat(selectedItem.stars)}
            </div>
            <div class="item-quantity-large">×{selectedItem.quantity}</div>
          </div>
        </div>
        
        <div class="detail-preview">
          {#if selectedItem.type === 'card'}
            <CardArt entry={{ 
              id: selectedItem.id, 
              name: stripStars(selectedItem.name), 
              stars: selectedItem.stars, 
              about: stripStars(selectedItem.description) 
            }} type="card" showTitle={false} showAbout={false} imageOnly={true} fluid={true} quiet={true} />
          {:else if selectedItem.type === 'relic'}
            <CardArt entry={{ 
              id: selectedItem.id, 
              name: stripStars(selectedItem.name), 
              stars: selectedItem.stars, 
              about: stripStars(selectedItem.description) 
            }} type="relic" roundIcon={false} showTitle={false} showAbout={false} imageOnly={true} fluid={true} quiet={true} />
          {:else}
            <div style="display:flex; align-items:center; justify-content:center; width:100%; height:100%;">
              <img src={getMaterialIcon(selectedItem.id)} alt={selectedItem.id} on:error={onIconError} style="max-width:100%; max-height:100%; object-fit:contain;" />
            </div>
          {/if}
        </div>

        <div class="detail-description">
          <h4>Description</h4>
          <p>{stripStars(selectedItem.description)}</p>
        </div>

        {#if selectedItem.meta}
          <div class="detail-stats">
            <h4>Details</h4>
            <div class="stats-grid">
              <div class="stat-row">
                <span class="stat-label">Type:</span>
                <span class="stat-value">{
                  selectedItem.type === 'card' ? 'Ability Card' : selectedItem.type === 'relic' ? 'Equipment Relic' : 'Upgrade Material'
                }</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">Rarity:</span>
                <span class="stat-value">{selectedItem.stars} Star</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">ID:</span>
                <span class="stat-value">{selectedItem.id}</span>
              </div>
            </div>
          </div>
        {/if}
      {:else}
        <div class="no-selection">
          <svelte:component this={Box} class="no-selection-icon" size={48} />
          <p>Select an item to view details</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .star-rail-inventory {
    --glass-border: 1.5px solid rgba(0,0,0,0.6);
    display: flex;
    flex-direction: column;
    height: 100%;
    max-height: 80vh;
    background: var(--glass-bg);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
  }

  .inventory-header {
    padding: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .tab-row {
    display: flex;
    gap: 0.5rem;
  }

  .tab {
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.7);
    padding: 0.75rem 1.25rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .tab.active {
    background: rgba(120,180,255,0.3);
    color: #fff;
    border-color: rgba(120,180,255,0.5);
  }

  .tab:hover:not(.active) {
    background: rgba(255,255,255,0.15);
  }

  .tab-icon {
    font-size: 1.1rem;
  }

  .inventory-body {
    display: flex;
    flex: 1;
    min-height: 0;
  }

  .header-actions { display:flex; align-items:center; }
  .reload-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.55rem 0.8rem;
    color: #fff;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.2);
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .reload-btn:hover { background: rgba(255,255,255,0.15); border-color: rgba(120,180,255,0.5); }
  .reload-btn:active { transform: translateY(1px); }

  .item-grid-container {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    border-right: 1px solid rgba(255,255,255,0.2);
  }

  .item-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 0.75rem;
    align-items: start;
  }

  /* Cards tab: show full CardArt cards in a responsive grid */
  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    /* Tighter spacing so cards sit closer together */
    gap: 0.25rem;
    align-items: start;
    /* Center items so visuals and click targets align consistently */
    justify-items: center;
  }
  .card-cell {
    position: relative;
    padding: 0;
    border: none;
    background: none;
    cursor: pointer;
  }
  .card-cell.selected { outline: 2px solid rgba(120,180,255,0.6); outline-offset: 2px; }
  .qty-badge {
    position: absolute;
    top: 6px;
    right: 10px;
    background: rgba(0,0,0,0.7);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.3);
    padding: 0 0.35rem;
    font-size: 0.8rem;
    line-height: 1.1rem;
    border-radius: 6px;
  }

  /* Relics tab: show CurioChoice with quantity */
  .relics-grid {
    display: grid;
    /* Match CardArt default width for relic tiles to avoid overflow */
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    /* Give relic tiles a bit more breathing room */
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
  .relic-cell.selected { outline: 2px solid rgba(120,180,255,0.6); outline-offset: 4px; }
  .relic-qty { font-size: 0.85rem; opacity: 0.9; }

  .grid-item {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
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
    background: rgba(255,255,255,0.1);
    border-color: rgba(120,180,255,0.5);
  }

  .grid-item.selected {
    background: rgba(120,180,255,0.2);
    border-color: rgba(120,180,255,0.7);
    box-shadow: 0 0 8px rgba(120,180,255,0.3);
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
    color: rgba(255,255,255,0.88);
    margin-top: 0.25rem;
    font-variant-numeric: tabular-nums;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Helvetica Neue, Arial, sans-serif;
    font-weight: 700;
    letter-spacing: 0.01em;
  }

  /* Materials use themed color backgrounds like cards/relics (whole tile filled) */
  .grid-item.material {
    background: color-mix(in oklab, var(--accent, #708090) 35%, black);
    border-color: color-mix(in oklab, var(--accent, #708090) 40%, transparent);
    box-shadow: none; /* reduce heavy outline ring */
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

  .item-stars {
    font-size: 0.6rem;
    margin-top: 0.2rem;
  }

  .detail-panel {
    width: 320px;
    padding: 1rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .detail-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .item-name {
    font-size: 1.2rem;
    font-weight: 600;
    color: #fff;
    margin: 0;
  }

  .item-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .item-stars-large {
    font-size: 1rem;
  }

  .item-quantity-large {
    font-size: 1rem;
    color: rgba(255,255,255,0.8);
    font-weight: 500;
  }

  .detail-preview {
    display: flex;
    align-items: stretch;
    justify-content: center;
    padding: 0;
    height: 320px;
    background: rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.1);
  }
  /* Ensure embedded CardArt fills the preview area */
  .detail-preview :global(.card-art) { width: 100%; height: 100%; flex: 1 1 auto; }

  .detail-description h4,
  .detail-stats h4 {
    font-size: 1rem;
    font-weight: 600;
    color: #fff;
    margin: 0 0 0.5rem 0;
  }

  .detail-description p {
    font-size: 0.9rem;
    line-height: 1.4;
    color: rgba(255,255,255,0.8);
    margin: 0;
  }

  .stats-grid {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.25rem 0;
  }

  .stat-label {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.7);
  }

  .stat-value {
    font-size: 0.85rem;
    color: #fff;
    font-weight: 500;
  }

  .no-selection {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: rgba(255,255,255,0.5);
    text-align: center;
  }

  .no-selection-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  @media (max-width: 768px) {
    .inventory-body {
      flex-direction: column;
    }
    
    .detail-panel {
      width: 100%;
      border-top: 1px solid rgba(255,255,255,0.2);
      border-right: none;
    }
    
    .item-grid-container {
      border-right: none;
    }
  }
</style>
