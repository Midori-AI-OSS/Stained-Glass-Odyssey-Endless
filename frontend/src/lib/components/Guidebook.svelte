<script>
  import { onMount } from 'svelte';
  import { Zap, Sparkles, LayoutPanelTop, ShoppingCart, Cog, ScrollText, TrendingUp, Search, RotateCcw, Flame } from 'lucide-svelte';
  import { httpGet } from '$lib/systems/httpClient.js';

  // State management with localStorage persistence
  let activeTab = 'stats'; // Start with stats tab by default
  let searchQuery = '';
  let filteredResults = [];

  // Data arrays
  let damageTypes = [];
  let ultimates = [];
  let passives = [];
  let uiTips = [];
  let shopInfo = null;
  let mechs = [];
  let stats = null;
  let effects = null;

  async function loadStats() {
    const data = await httpGet('/guidebook/stats', { cache: 'no-store' }, true);
    stats = data || null;
  }
  async function loadDamage() {
    const data = await httpGet('/guidebook/damage-types', { cache: 'no-store' }, true);
    damageTypes = data?.damage_types || [];
  }
  async function loadUlts() {
    const data = await httpGet('/guidebook/ultimates', { cache: 'no-store' }, true);
    ultimates = data?.ultimates || [];
  }
  async function loadPassives() {
    const data = await httpGet('/guidebook/passives', { cache: 'no-store' }, true);
    passives = data?.passives || [];
  }
  async function loadUI() {
    const data = await httpGet('/guidebook/ui', { cache: 'no-store' }, true);
    uiTips = data?.tips || [];
  }
  async function loadShops() {
    const data = await httpGet('/guidebook/shops', { cache: 'no-store' }, true);
    shopInfo = data || null;
  }
  async function loadMechs() {
    const data = await httpGet('/guidebook/mechs', { cache: 'no-store' }, true);
    mechs = data?.mechanics || [];
  }
  async function loadEffects() {
    const data = await httpGet('/guidebook/effects', { cache: 'no-store' }, true);
    effects = data || null;
  }

  async function ensureTabLoaded(key) {
    if (key === 'stats' && !stats) await loadStats();
    if (key === 'damage' && damageTypes.length === 0) await loadDamage();
    if (key === 'ults' && ultimates.length === 0) await loadUlts();
    if (key === 'ui' && uiTips.length === 0) await loadUI();
    if (key === 'shops' && !shopInfo) await loadShops();
    if (key === 'mechs' && mechs.length === 0) await loadMechs();
    if (key === 'passives' && passives.length === 0) await loadPassives();
    if (key === 'effects' && !effects) await loadEffects();
  }

  // Load and save tab state from localStorage
  function loadTabState() {
    try {
      const saved = localStorage.getItem('guidebook-active-tab');
      if (saved && ['stats', 'damage', 'ults', 'ui', 'shops', 'mechs', 'passives', 'effects'].includes(saved)) {
        activeTab = saved;
      }
    } catch {}
  }

  function saveTabState() {
    try {
      localStorage.setItem('guidebook-active-tab', activeTab);
    } catch {}
  }

  // Search and filter functionality
  function performSearch() {
    if (!searchQuery.trim()) {
      filteredResults = [];
      return;
    }

    const query = searchQuery.toLowerCase();
    filteredResults = [];
    
    // Search through all data types
    damageTypes.forEach(item => {
      if (item.id?.toLowerCase().includes(query) || 
          item.description?.toLowerCase().includes(query) ||
          item.weakness?.toLowerCase().includes(query)) {
        filteredResults.push({...item, type: 'damage', tab: 'damage'});
      }
    });
    
    ultimates.forEach(item => {
      if (item.id?.toLowerCase().includes(query) || 
          item.description?.toLowerCase().includes(query)) {
        filteredResults.push({...item, type: 'ultimate', tab: 'ults'});
      }
    });
    
    passives.forEach(item => {
      if (item.id?.toLowerCase().includes(query) || 
          item.name?.toLowerCase().includes(query) ||
          item.description?.toLowerCase().includes(query)) {
        filteredResults.push({...item, type: 'passive', tab: 'passives'});
      }
    });

    if (stats?.stats) {
      stats.stats.forEach(item => {
        if (item.name?.toLowerCase().includes(query) || 
            item.description?.toLowerCase().includes(query)) {
          filteredResults.push({...item, type: 'stat', tab: 'stats'});
        }
      });
    }

    // Search effects
    if (effects?.combat_effects) {
      effects.combat_effects.forEach(item => {
        if (item.name?.toLowerCase().includes(query) || 
            item.description?.toLowerCase().includes(query) ||
            item.type?.toLowerCase().includes(query)) {
          filteredResults.push({...item, type: 'effect', tab: 'effects'});
        }
      });
    }
    if (effects?.dot_effects) {
      effects.dot_effects.forEach(item => {
        if (item.name?.toLowerCase().includes(query) || 
            item.description?.toLowerCase().includes(query) ||
            item.type?.toLowerCase().includes(query) ||
            item.element?.toLowerCase().includes(query)) {
          filteredResults.push({...item, type: 'effect', tab: 'effects'});
        }
      });
    }
  }

  // Switch tabs with state persistence
  async function switchTab(newTab) {
    activeTab = newTab;
    saveTabState();
    await ensureTabLoaded(newTab);
    searchQuery = ''; // Clear search when switching tabs
    filteredResults = [];
  }

  // Jump to specific tab from search results
  async function jumpToTab(tabName) {
    await switchTab(tabName);
  }

  onMount(async () => {
    loadTabState();
    await ensureTabLoaded(activeTab);
  });

  // Reactive search
  $: if (searchQuery !== undefined) performSearch();

  function colorStyle(rgb) {
    if (!rgb || !Array.isArray(rgb) || rgb.length !== 3) return '';
    const [r,g,b] = rgb;
    return `background: rgba(${r},${g},${b},0.35); border-color: rgba(${r},${g},${b},0.9);`;
  }
</script>

<div class="star-rail-guidebook">
  <!-- Header with tabs (matching Inventory component) -->
  <div class="guidebook-header">
    <div class="tab-row">
      <button 
        class="tab" 
        class:active={activeTab === 'stats'}
        on:click={() => switchTab('stats')}
        title="Character Stats"
      >
        <svelte:component this={TrendingUp} class="tab-icon" size={18} />
        Stats
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'damage'}
        on:click={() => switchTab('damage')}
        title="Damage Types"
      >
        <svelte:component this={Zap} class="tab-icon" size={18} />
        Elements
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'ults'}
        on:click={() => switchTab('ults')}
        title="Ultimate Abilities"
      >
        <svelte:component this={Sparkles} class="tab-icon" size={18} />
        Ultimates
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'passives'}
        on:click={() => switchTab('passives')}
        title="Passive Abilities"
      >
        <svelte:component this={ScrollText} class="tab-icon" size={18} />
        Passives
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'effects'}
        on:click={() => switchTab('effects')}
        title="Combat Effects & DoTs"
      >
        <svelte:component this={Flame} class="tab-icon" size={18} />
        Effects
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'mechs'}
        on:click={() => switchTab('mechs')}
        title="Game Mechanics"
      >
        <svelte:component this={Cog} class="tab-icon" size={18} />
        Mechanics
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'shops'}
        on:click={() => switchTab('shops')}
        title="Shop Information"
      >
        <svelte:component this={ShoppingCart} class="tab-icon" size={18} />
        Shops
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'ui'}
        on:click={() => switchTab('ui')}
        title="UI Tips"
      >
        <svelte:component this={LayoutPanelTop} class="tab-icon" size={18} />
        UI Tips
      </button>
    </div>
    
    <div class="header-actions">
      <div class="search-container">
        <input 
          type="text" 
          class="search-input"
          placeholder="Search guidebook..."
          bind:value={searchQuery}
        />
        <Search class="search-icon" size={16} />
      </div>
    </div>
  </div>

  <div class="guidebook-body">
    <!-- Search Results (when active) -->
    {#if searchQuery && filteredResults.length > 0}
      <div class="search-results">
        <h3>Search Results ({filteredResults.length})</h3>
        <div class="results-grid">
          {#each filteredResults as result}
            <div class="result-item" on:click={() => jumpToTab(result.tab)}>
              <div class="result-header">
                <span class="result-type">{result.type}</span>
                <span class="result-name">{result.name || result.id}</span>
              </div>
              <p class="result-desc">{result.description || ''}</p>
              <div class="result-actions">
                <button class="jump-btn" on:click|stopPropagation={() => jumpToTab(result.tab)}>
                  Go to {result.tab} →
                </button>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {:else if searchQuery && filteredResults.length === 0}
      <div class="no-results">
        <Search size={48} />
        <p>No results found for "{searchQuery}"</p>
      </div>
    {:else}
      <!-- Tab Content -->
      <div class="tab-content">
        {#if activeTab === 'stats'}
          <div class="stats-panel">
            {#if stats}
              <div class="stats-section">
                <h3>Character Statistics</h3>
                <div class="stats-grid">
                  {#each stats.stats as stat}
                    <div class="stat-card">
                      <div class="stat-header">
                        <h4>{stat.name}</h4>
                        <span class="stat-value">{stat.base_value}</span>
                      </div>
                      <p class="stat-desc">{stat.description}</p>
                      <div class="stat-scaling">Scaling: {stat.scaling}</div>
                    </div>
                  {/each}
                </div>
              </div>

              {#if stats.level_info}
                <div class="level-section">
                  <h3>Level System</h3>
                  <div class="level-card">
                    <p class="level-desc">{stats.level_info.description}</p>
                    <div class="level-benefits">
                      <strong>Benefits per level:</strong> {stats.level_info.benefits}
                    </div>
                    <div class="level-exp">
                      <strong>Experience:</strong> {stats.level_info.experience}
                    </div>
                  </div>
                </div>
              {/if}

              {#if stats.common_passives}
                <div class="common-passives-section">
                  <h3>Common Passive Effects</h3>
                  <div class="passives-grid">
                    {#each stats.common_passives as passive}
                      <div class="passive-card">
                        <div class="passive-header">
                          <h4>{passive.name}</h4>
                          <span class="passive-trigger">{passive.trigger}</span>
                        </div>
                        <p>{passive.description}</p>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            {/if}
          </div>
        {/if}
        {#if activeTab === 'damage'}
          <div class="damage-types-panel">
            <div class="resistance-wheel">
              <h3>Elemental Resistance Wheel</h3>
              <div class="wheel-diagram">
                <div class="wheel-info">
                  <p>Each element has strengths and weaknesses:</p>
                  <ul>
                    <li><strong>Fire</strong> → <em>Ice</em> (1.25x damage)</li>
                    <li><strong>Ice</strong> → <em>Fire</em> (1.25x damage)</li>
                    <li><strong>Lightning</strong> → <em>Wind</em> (1.25x damage)</li>
                    <li><strong>Wind</strong> → <em>Lightning</em> (1.25x damage)</li>
                    <li><strong>Light</strong> ↔ <em>Dark</em> (mutual weakness)</li>
                  </ul>
                  <p class="resistance-note">Same-type attacks deal 0.75x damage (resistance)</p>
                </div>
              </div>
            </div>
            
            <div class="elements-grid">
              {#each damageTypes as d}
                <div class="element-card" style={colorStyle(d.color)}>
                  <div class="element-header">
                    <h4 class="element-name">{d.id}</h4>
                    <div class="element-relationships">
                      {#if d.weakness}
                        <span class="weakness">Weak to {d.weakness}</span>
                      {/if}
                      {#if d.strong_against}
                        <span class="strength">Strong vs {d.strong_against}</span>
                      {/if}
                    </div>
                  </div>
                  <p class="element-desc">{d.description || ''}</p>
                  {#if d.damage_mod_weak || d.damage_mod_resist}
                    <div class="damage-mods">
                      {#if d.damage_mod_weak}<div class="mod-weak">{d.damage_mod_weak}</div>{/if}
                      {#if d.damage_mod_resist}<div class="mod-resist">{d.damage_mod_resist}</div>{/if}
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {:else if activeTab === 'ults'}
          <div class="ultimates-panel">
            <div class="ultimates-info">
              <h3>Ultimate Abilities</h3>
              <p>Each damage type has a unique ultimate ability. Characters inherit the ultimate of their selected damage type.</p>
            </div>
            <div class="ultimates-grid">
              {#each ultimates as u}
                <div class="ultimate-card">
                  <div class="ultimate-header">
                    <h4 class="ultimate-name">{u.id} Ultimate</h4>
                  </div>
                  <p class="ultimate-desc">{u.description || ''}</p>
                </div>
              {/each}
            </div>
          </div>
        {:else if activeTab === 'passives'}
          <div class="passives-panel">
            <div class="passives-info">
              <h3>Passive Abilities</h3>
              <p>Passive abilities trigger automatically under specific conditions and provide various benefits.</p>
            </div>
            <div class="passives-grid">
              {#each passives as p}
                <div class="passive-card">
                  <div class="passive-header">
                    <h4 class="passive-name">{p.name || p.id}</h4>
                    {#if p.trigger}
                      <span class="passive-trigger">Trigger: {p.trigger}</span>
                    {/if}
                  </div>
                  <p class="passive-desc">{p.description || ''}</p>
                  {#if p.amount !== null || p.stack_display}
                    <div class="passive-details">
                      {#if p.amount !== null}<span class="passive-amount">Amount: {p.amount}</span>{/if}
                      {#if p.stack_display}<span class="passive-stacks">Stacks: {p.stack_display}</span>{/if}
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {:else if activeTab === 'effects'}
          <div class="effects-panel">
            {#if effects}
              <div class="effects-info">
                <h3>Combat Effects & Status Effects</h3>
                <p>Various effects that can be applied during combat, including buffs, debuffs, and damage over time effects.</p>
              </div>
              
              {#if effects.combat_effects && effects.combat_effects.length > 0}
                <div class="effects-section">
                  <h4>Combat Effects</h4>
                  <div class="effects-grid">
                    {#each effects.combat_effects as effect}
                      <div class="effect-card">
                        <div class="effect-header">
                          <h5 class="effect-name">{effect.name}</h5>
                          <span class="effect-type">{effect.type}</span>
                        </div>
                        <p class="effect-desc">{effect.description}</p>
                        {#if effect.trigger}
                          <div class="effect-trigger">Trigger: {effect.trigger}</div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
              
              {#if effects.dot_effects && effects.dot_effects.length > 0}
                <div class="effects-section">
                  <h4>Damage Over Time & Debuffs</h4>
                  <div class="effects-grid">
                    {#each effects.dot_effects as dot}
                      <div class="effect-card">
                        <div class="effect-header">
                          <h5 class="effect-name">{dot.name}</h5>
                          <span class="effect-type">{dot.type}</span>
                          {#if dot.element}
                            <span class="effect-element">{dot.element}</span>
                          {/if}
                        </div>
                        <p class="effect-desc">{dot.description}</p>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            {:else}
              <div class="loading">Loading effects...</div>
            {/if}
          </div>
        {:else if activeTab === 'mechs'}
          <div class="mechanics-panel">
            <div class="mechanics-grid">
              {#each mechs as m}
                <div class="mechanic-card">
                  <div class="mechanic-header">
                    <h4 class="mechanic-name">{m.name}</h4>
                  </div>
                  <p class="mechanic-desc">{m.description}</p>
                </div>
              {/each}
            </div>
          </div>
        {:else if activeTab === 'shops'}
          <div class="shops-panel">
            {#if shopInfo}
              <div class="shop-overview">
                <h3>Shop System</h3>
                <div class="shop-basics">
                  <div class="shop-cost">
                    <strong>Reroll Cost:</strong> {shopInfo.reroll_cost} gold
                  </div>
                </div>
              </div>
              
              {#if shopInfo.pricing_explanation}
                <div class="pricing-section">
                  <h4>Pricing by Rarity</h4>
                  <div class="pricing-grid">
                    {#each Object.entries(shopInfo.pricing_explanation) as [stars, info]}
                      <div class="price-card star-{stars.split('_')[0]}">
                        <div class="price-header">
                          <span class="star-count">{'★'.repeat(parseInt(stars.split('_')[0]))}</span>
                        </div>
                        <p class="price-info">{info}</p>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
              
              {#if shopInfo.strategy_tips}
                <div class="strategy-section">
                  <h4>Strategy Tips</h4>
                  <ul class="strategy-list">
                    {#each shopInfo.strategy_tips as tip}
                      <li>{tip}</li>
                    {/each}
                  </ul>
                </div>
              {/if}
              
              {#if shopInfo.notes}
                <div class="notes-section">
                  <h4>Additional Notes</h4>
                  <ul class="notes-list">
                    {#each shopInfo.notes as note}
                      <li>{note}</li>
                    {/each}
                  </ul>
                </div>
              {/if}
            {/if}
          </div>
        {:else if activeTab === 'ui'}
          <div class="ui-panel">
            <div class="ui-grid">
              {#each uiTips as tip}
                <div class="ui-card">
                  <div class="ui-header">
                    <h4 class="ui-name">{tip.name}</h4>
                  </div>
                  <p class="ui-desc">{tip.description}</p>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .star-rail-guidebook {
    display: flex;
    flex-direction: column;
    height: 100%;
    max-height: 80vh;
    background: var(--glass-bg);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
  }

  .guidebook-header {
    padding: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .tab-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
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

  .header-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .search-container {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-input {
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    color: #fff;
    padding: 0.5rem 2.5rem 0.5rem 0.75rem;
    font-size: 0.9rem;
    min-width: 200px;
    transition: all 0.2s ease;
  }

  .search-input:focus {
    outline: none;
    border-color: rgba(120,180,255,0.5);
    background: rgba(255,255,255,0.15);
  }

  .search-input::placeholder {
    color: rgba(255,255,255,0.5);
  }

  .search-icon {
    position: absolute;
    right: 0.75rem;
    color: rgba(255,255,255,0.5);
    pointer-events: none;
  }

  .guidebook-body {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    min-height: 0;
  }

  .tab-content {
    height: 100%;
  }

  /* Search Results */
  .search-results h3 {
    color: #fff;
    margin-bottom: 1rem;
    font-size: 1.1rem;
  }

  .results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 0.75rem;
  }

  .result-item {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .result-item:hover {
    background: rgba(255,255,255,0.1);
    border-color: rgba(120,180,255,0.5);
  }

  .result-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .result-type {
    background: rgba(120,180,255,0.3);
    color: #fff;
    padding: 0.2rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    border-radius: 4px;
  }

  .result-name {
    color: #fff;
    font-weight: 600;
  }

  .result-desc {
    color: rgba(255,255,255,0.8);
    font-size: 0.9rem;
    line-height: 1.4;
    margin: 0 0 0.75rem 0;
  }

  .result-actions {
    display: flex;
    justify-content: flex-end;
  }

  .jump-btn {
    background: rgba(120,180,255,0.2);
    border: 1px solid rgba(120,180,255,0.5);
    color: #fff;
    padding: 0.4rem 0.8rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .jump-btn:hover {
    background: rgba(120,180,255,0.3);
  }

  .no-results {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 300px;
    color: rgba(255,255,255,0.5);
    text-align: center;
  }

  /* Stats Panel */
  .stats-panel h3 {
    color: #fff;
    margin-bottom: 1rem;
    font-size: 1.2rem;
  }

  .stats-section, .level-section, .common-passives-section {
    margin-bottom: 2rem;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.75rem;
  }

  .stat-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 1rem;
  }

  .stat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .stat-header h4 {
    color: #fff;
    font-size: 1rem;
    margin: 0;
  }

  .stat-value {
    color: rgba(120,180,255,0.8);
    font-weight: 600;
  }

  .stat-desc {
    color: rgba(255,255,255,0.8);
    font-size: 0.9rem;
    line-height: 1.4;
    margin: 0 0 0.75rem 0;
  }

  .stat-scaling {
    color: rgba(255,255,255,0.6);
    font-size: 0.8rem;
    font-style: italic;
  }

  .level-card, .passive-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 1rem;
  }

  .level-desc, .level-benefits, .level-exp {
    color: rgba(255,255,255,0.8);
    margin-bottom: 0.5rem;
  }

  .passives-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 0.75rem;
  }

  .passive-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .passive-header h4 {
    color: #fff;
    font-size: 0.95rem;
    margin: 0;
  }

  .passive-trigger {
    color: rgba(120,180,255,0.8);
    font-size: 0.8rem;
  }

  /* Elements Panel */
  .resistance-wheel {
    margin-bottom: 2rem;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 1.5rem;
  }

  .resistance-wheel h3 {
    color: #fff;
    margin-bottom: 1rem;
  }

  .wheel-info ul {
    list-style: none;
    padding: 0;
    margin: 0.5rem 0;
  }

  .wheel-info li {
    color: rgba(255,255,255,0.8);
    margin: 0.25rem 0;
    font-size: 0.9rem;
  }

  .resistance-note {
    color: rgba(255,255,255,0.6);
    font-style: italic;
    margin-top: 1rem;
  }

  .elements-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 0.75rem;
  }

  .element-card {
    border: 1px solid rgba(255,255,255,0.3);
    padding: 1rem;
    background: rgba(255,255,255,0.1);
  }

  .element-header {
    margin-bottom: 0.5rem;
  }

  .element-header h4 {
    color: #fff;
    margin: 0 0 0.25rem 0;
    font-size: 1.1rem;
  }

  .element-relationships {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .weakness, .strength {
    font-size: 0.8rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
  }

  .weakness {
    background: rgba(255,100,100,0.3);
    color: #ffaaaa;
  }

  .strength {
    background: rgba(100,255,100,0.3);
    color: #aaffaa;
  }

  .element-desc {
    color: rgba(255,255,255,0.8);
    font-size: 0.9rem;
    line-height: 1.4;
    margin: 0.75rem 0;
  }

  .damage-mods {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  .mod-weak, .mod-resist {
    font-size: 0.8rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
  }

  .mod-weak {
    background: rgba(255,200,100,0.3);
    color: #ffddaa;
  }

  .mod-resist {
    background: rgba(100,200,255,0.3);
    color: #aaddff;
  }

  /* Other Panels */
  .ultimates-panel h3, .passives-panel h3, .mechanics-panel h3, .shops-panel h3, .ui-panel h3 {
    color: #fff;
    margin-bottom: 1rem;
  }

  .ultimates-info, .passives-info {
    margin-bottom: 1.5rem;
    color: rgba(255,255,255,0.8);
  }

  .ultimates-grid, .passives-grid, .mechanics-grid, .ui-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.75rem;
  }

  .ultimate-card, .passive-card, .mechanic-card, .ui-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 1rem;
  }

  .ultimate-header h4, .passive-header h4, .mechanic-header h4, .ui-header h4 {
    color: #fff;
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
  }

  .ultimate-desc, .passive-desc, .mechanic-desc, .ui-desc {
    color: rgba(255,255,255,0.8);
    font-size: 0.9rem;
    line-height: 1.4;
    margin: 0;
  }

  .passive-details {
    margin-top: 0.5rem;
    display: flex;
    gap: 0.75rem;
  }

  .passive-amount, .passive-stacks {
    font-size: 0.8rem;
    color: rgba(120,180,255,0.8);
  }

  /* Shop Panel */
  .shop-overview {
    margin-bottom: 2rem;
  }

  .shop-basics {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 1rem;
    margin-top: 1rem;
  }

  .shop-cost {
    color: rgba(255,255,255,0.8);
    font-size: 1rem;
  }

  .pricing-section, .strategy-section, .notes-section {
    margin-bottom: 2rem;
  }

  .pricing-section h4, .strategy-section h4, .notes-section h4 {
    color: #fff;
    margin-bottom: 1rem;
  }

  .pricing-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.75rem;
  }

  .price-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 0.75rem;
  }

  .price-header {
    margin-bottom: 0.5rem;
  }

  .star-count {
    color: #ffd700;
    font-size: 1.1rem;
  }

  .price-info {
    color: rgba(255,255,255,0.8);
    font-size: 0.9rem;
    margin: 0;
  }

  .strategy-list, .notes-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .strategy-list li, .notes-list li {
    color: rgba(255,255,255,0.8);
    margin: 0.5rem 0;
    padding-left: 1rem;
    position: relative;
  }

  .strategy-list li::before, .notes-list li::before {
    content: "→";
    color: rgba(120,180,255,0.8);
    position: absolute;
    left: 0;
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .guidebook-header {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }
    
    .tab-row {
      justify-content: center;
    }
    
    .search-input {
      min-width: 150px;
    }
    
    .stats-grid, .elements-grid, .ultimates-grid, .passives-grid, .effects-grid, .mechanics-grid, .ui-grid, .pricing-grid {
      grid-template-columns: 1fr;
    }
  }

  /* Effects Panel Styles */
  .effects-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .effects-info {
    text-align: center;
    padding: 1rem;
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.1);
  }

  .effects-info h3 {
    margin: 0 0 0.5rem 0;
    color: var(--text-color);
    font-size: 1.5rem;
  }

  .effects-info p {
    margin: 0;
    color: var(--text-secondary);
    line-height: 1.4;
  }

  .effects-section {
    margin: 1rem 0;
  }

  .effects-section h4 {
    margin: 0 0 1rem 0;
    color: var(--text-color);
    font-size: 1.2rem;
    text-align: center;
    padding: 0.5rem;
    background: rgba(255,255,255,0.05);
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.1);
  }

  .effects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
  }

  .effect-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s ease;
  }

  .effect-card:hover {
    background: rgba(255,255,255,0.08);
    border-color: rgba(255,255,255,0.2);
    transform: translateY(-1px);
  }

  .effect-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .effect-name {
    margin: 0;
    color: var(--text-color);
    font-size: 1.1rem;
    font-weight: 600;
  }

  .effect-type {
    background: rgba(100,100,255,0.3);
    color: #a0a0ff;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
    border: 1px solid rgba(100,100,255,0.4);
  }

  .effect-element {
    background: rgba(255,180,0,0.3);
    color: #ffcc66;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
    border: 1px solid rgba(255,180,0,0.4);
  }

  .effect-desc {
    margin: 0;
    color: var(--text-secondary);
    line-height: 1.4;
    font-size: 0.95rem;
  }

  .effect-trigger {
    margin-top: 0.5rem;
    color: var(--text-color);
    font-size: 0.85rem;
    padding: 0.25rem 0.5rem;
    background: rgba(0,255,100,0.1);
    border-radius: 4px;
    border: 1px solid rgba(0,255,100,0.2);
  }
</style>

