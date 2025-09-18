<script>
  import { onMount } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  import { PackageOpen, Star, Users, RotateCcw, Info } from 'lucide-svelte';
  import MenuPanel from './MenuPanel.svelte';
  import { getGacha, pullGacha } from '../systems/api.js';
  import { browser, dev } from '$app/environment';
  import { openOverlay } from '../systems/OverlayController.js';
  
  const dispatch = createEventDispatcher();
  export let reducedMotion = false;

  // State management
  function safeLocalStorageGet(key) {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  }

  function safeLocalStorageSet(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch {}
  }

  let activeTab = 'standard';
  if (browser) {
    const saved = safeLocalStorageGet('pulls-active-banner');
    if (saved) {
      activeTab = saved;
    }
  }
  let pity = 0;
  let items = {};
  let loading = false;
  let banners = [];
  let featuredCharacters = [];
  
  onMount(async () => {
    await reloadData();
  });
  
  async function reloadData() {
    try {
      const data = await getGacha();
      pity = data.pity;
      items = data.items;
      banners = data.banners || [];
      featuredCharacters = data.featured_characters || [];
      
      ensureActiveTabValid();
    } catch (err) {
      console.error('Failed to load gacha data:', err);
    }
  }
  
  async function pull(count) {
    // Optimistic UI: lower visible tickets immediately for snappier feedback
    const prevTickets = Number(items?.ticket || 0);
    if (prevTickets >= count) {
      items = { ...items, ticket: prevTickets - count };
    }

    loading = true;
    try {
      const data = await pullGacha(count, activeTab);
      pity = Number(data?.pity || 0);
      // Force new object to ensure reactivity even if server omits zero-count keys
      items = { ...(data?.items || {}) };
      banners = data?.banners || [];
      featuredCharacters = data?.featured_characters || [];
      const results = data?.results || [];
      if (results.length) {
        openOverlay('pull-results', { results });
      }
      // Force-refresh from backend to ensure ticket count is authoritative
      try {
        const fresh = await getGacha();
        pity = Number(fresh?.pity || pity);
        items = { ...(fresh?.items || items) };
        banners = fresh?.banners || banners;
        featuredCharacters = fresh?.featured_characters || featuredCharacters;
      } catch {}
      ensureActiveTabValid();
    } catch (err) {
      // Revert optimistic change on failure
      if (prevTickets >= count) {
        items = { ...items, ticket: prevTickets };
      }
      if (dev || !browser) {
        const { error } = await import('$lib/systems/logger.js');
        error('pull failed', err);
      }
      openOverlay('error', { message: 'Not enough tickets', traceback: err?.stack || '' });
    }
    loading = false;
  }
  
  function close() {
    dispatch('close');
  }
  
  function switchTab(tabId) {
    activeTab = tabId;
    if (browser) {
      safeLocalStorageSet('pulls-active-banner', activeTab);
    }
  }

  function ensureActiveTabValid() {
    if (banners.length > 0 && !banners.find(b => b.id === activeTab)) {
      activeTab = banners[0].id;
      if (browser) {
        safeLocalStorageSet('pulls-active-banner', activeTab);
      }
    }
  }
  
  // Get current banner info
  $: currentBanner = banners.find(b => b.id === activeTab) || { name: 'Standard Warp', banner_type: 'standard' };
  $: featuredChar = featuredCharacters.find(c => c.banner_id === activeTab);
  
  // Banner timing helper
  function getBannerTimeInfo(banner) {
    if (banner.banner_type === 'standard') {
      return { status: 'permanent', text: 'Permanent' };
    }
    
    const now = Date.now() / 1000;
    const timeLeft = banner.end_time - now;
    
    if (timeLeft <= 0) {
      return { status: 'expired', text: 'Rotating Soon...' };
    }
    
    const days = Math.floor(timeLeft / 86400);
    const hours = Math.floor((timeLeft % 86400) / 3600);
    
    if (days > 0) {
      return { status: 'active', text: `${days}d ${hours}h remaining` };
    } else if (hours > 0) {
      return { status: 'ending', text: `${hours}h remaining` };
    } else {
      const minutes = Math.floor((timeLeft % 3600) / 60);
      return { status: 'ending', text: `${minutes}m remaining` };
    }
  }
  
  // Get star color for rarity display
  function getStarColor(rarity) {
    switch (rarity) {
      case 6: return '#FFD700'; // Gold
      case 5: return '#FF3B30'; // Red
      case 4: return '#800080'; // Purple
      case 3: return '#228B22'; // Green
      case 2: return '#1E90FF'; // Blue
      default: return '#808080'; // Gray
    }
  }

  // Resolve character portraits from assets (supports flat and nested folders)
  // Example paths supported:
  // - $lib/assets/characters/kboshi.png
  // - $lib/assets/characters/kboshi/kboshi.png
  import { getCharacterImage as resolveCharacterPortrait } from '$lib/systems/assetLoader.js';
  function getCharacterImage(characterId) {
    // Delegate to shared loader which supports nested folders and fallbacks
    return resolveCharacterPortrait(String(characterId || '').toLowerCase());
  }

  // Handle image loading errors
  function handleImageError(event) {
    // Hide the image and show the fallback icon
    event.target.style.display = 'none';
    event.target.nextElementSibling.style.display = 'flex';
  }
</script>

<MenuPanel data-testid="pulls-menu" class="warp-menu" {reducedMotion}>
  <!-- Header with tabs (matching Guidebook/Inventory styling) -->
  <div class="warp-header">
    <div class="tab-row">
      {#each banners as banner}
        <button 
          class="tab" 
          class:active={activeTab === banner.id}
          on:click={() => switchTab(banner.id)}
          title={banner.name}
        >
          {#if banner.banner_type === 'standard'}
            <svelte:component this={PackageOpen} class="tab-icon" size={18} />
          {:else}
            <svelte:component this={Star} class="tab-icon" size={18} />
          {/if}
          {banner.name}
        </button>
      {/each}
    </div>
    
    <div class="header-actions">
      <button
        class="info-btn"
        type="button"
        aria-label="Warp info"
        title="Warp info"
        on:click={() => openOverlay('warp-info')}
      >
        <svelte:component this={Info} size={16} aria-hidden="true" />
        <span class="info-label">Info</span>
      </button>
      <button class="reload-btn" on:click={reloadData} disabled={loading}>
        <svelte:component this={RotateCcw} size={16} />
        Refresh
      </button>
    </div>
  </div>

  <!-- Tab Content -->
  <div class="warp-content">
    <div class="banner-info">
      <div class="banner-title">
        <h3>{currentBanner.name}</h3>
        {#if currentBanner.banner_type === 'custom'}
          {@const timeInfo = getBannerTimeInfo(currentBanner)}
          <div class="banner-timing" class:ending={timeInfo.status === 'ending'} class:expired={timeInfo.status === 'expired'}>
            {timeInfo.text}
          </div>
        {/if}
      </div>
      <div class="banner-stats">
        <div class="stat">
          <span class="stat-label">Pity:</span>
          <span class="stat-value">{pity}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Tickets:</span>
          <span class="stat-value">{items.ticket || 0}</span>
        </div>
      </div>
    </div>

    {#if featuredChar}
      <div class="featured-character">
        <div class="char-header">
          <h4>Featured Character</h4>
          <div class="char-rarity" style="color: {getStarColor(featuredChar.gacha_rarity)}">
            {Array(featuredChar.gacha_rarity).fill('★').join('')}
          </div>
        </div>
        <div class="char-info">
          <div class="char-avatar">
            <img 
              src={getCharacterImage(featuredChar.id)} 
              alt={featuredChar.name}
              on:error={handleImageError}
              class="char-image"
            />
            <svelte:component this={Users} size={48} class="char-fallback" />
          </div>
          <div class="char-details">
            <h5>{featuredChar.name}</h5>
            <p class="char-description">{featuredChar.about}</p>
            <div class="char-meta">
              <span class="char-type">Type: {featuredChar.char_type}</span>
            </div>
          </div>
        </div>
      </div>
    {:else if currentBanner.banner_type === 'standard'}
      <div class="standard-info">
        <div class="info-header">
          <h4>Standard Warp</h4>
        </div>
        <p class="info-desc">
          Pull from the standard pool of characters and upgrade materials. 
          All available characters have equal rates.
        </p>
      </div>
    {/if}

    <div class="pull-actions">
      <button 
        class="pull-btn pull-1" 
        disabled={loading || (items.ticket || 0) < 1} 
        on:click={() => pull(1)}
      >
        <span class="pull-text">Pull ×1</span>
        <span class="pull-cost">1 Ticket</span>
      </button>
      <button 
        class="pull-btn pull-5" 
        disabled={loading || (items.ticket || 0) < 5} 
        on:click={() => pull(5)}
      >
        <span class="pull-text">Pull ×5</span>
        <span class="pull-cost">5 Tickets</span>
      </button>
      <button 
        class="pull-btn pull-10" 
        disabled={loading || (items.ticket || 0) < 10} 
        on:click={() => pull(10)}
      >
        <span class="pull-text">Pull ×10</span>
        <span class="pull-cost">10 Tickets</span>
      </button>
    </div>

    <div class="actions">
      <button class="close-btn" on:click={close}>Done</button>
    </div>
  </div>
</MenuPanel>

<style>
  .warp-menu {
    --glass-border: 1.5px solid rgba(0,0,0,0.6);
  }
  /* Header styling matching Guidebook/Inventory */
  .warp-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    background: rgba(255,255,255,0.05);
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

  .header-actions button {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.55rem 0.8rem;
    color: #fff;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.2);
    cursor: pointer;
    transition: all 0.15s ease;
    font-size: 0.9rem;
  }

  .header-actions button:hover {
    background: rgba(255,255,255,0.15);
    border-color: rgba(120,180,255,0.5);
  }

  .header-actions button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .info-btn {
    border-radius: 6px;
  }

  .info-label {
    font-weight: 500;
  }

  /* Content area */
  .warp-content {
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
  }

  .banner-info {
    margin-bottom: 1.5rem;
  }

  .banner-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .banner-info h3 {
    color: #fff;
    margin: 0;
    font-size: 1.5rem;
  }

  .banner-timing {
    color: rgba(120,180,255,0.9);
    font-size: 0.9rem;
    font-weight: 500;
    padding: 0.25rem 0.75rem;
    background: rgba(120,180,255,0.2);
    border: 1px solid rgba(120,180,255,0.3);
    border-radius: 16px;
  }

  .banner-timing.ending {
    color: rgba(255,165,0,0.9);
    background: rgba(255,165,0,0.2);
    border-color: rgba(255,165,0,0.3);
  }

  .banner-timing.expired {
    color: rgba(255,100,100,0.9);
    background: rgba(255,100,100,0.2);
    border-color: rgba(255,100,100,0.3);
  }

  .banner-stats {
    display: flex;
    gap: 2rem;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .stat-label {
    color: rgba(255,255,255,0.7);
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
  }

  .stat-value {
    color: #fff;
    font-size: 1.2rem;
    font-weight: 600;
  }

  /* Featured character section */
  .featured-character {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .char-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .char-header h4 {
    color: #fff;
    margin: 0;
    font-size: 1.2rem;
  }

  .char-rarity {
    font-size: 1.1rem;
    font-weight: 600;
  }

  .char-info {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
  }

  .char-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    background: rgba(255,255,255,0.1);
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.7);
    position: relative;
    overflow: hidden;
  }

  .char-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .char-fallback {
    display: none;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }

  .char-details {
    flex: 1;
  }

  .char-details h5 {
    color: #fff;
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
  }

  .char-description {
    color: rgba(255,255,255,0.8);
    margin: 0 0 0.75rem 0;
    line-height: 1.4;
    font-size: 0.95rem;
  }

  .char-meta {
    display: flex;
    gap: 1rem;
  }

  .char-type {
    color: rgba(120,180,255,0.8);
    font-size: 0.9rem;
  }

  /* Standard info section */
  .standard-info {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .info-header h4 {
    color: #fff;
    margin: 0 0 0.75rem 0;
    font-size: 1.2rem;
  }

  .info-desc {
    color: rgba(255,255,255,0.8);
    margin: 0;
    line-height: 1.4;
  }

  /* Pull buttons */
  .pull-actions {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
  }

  .pull-btn {
    flex: 1;
    min-width: 120px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    padding: 1rem;
    background: rgba(120,180,255,0.2);
    border: 2px solid rgba(120,180,255,0.5);
    color: #fff;
    cursor: pointer;
    transition: all 0.2s ease;
    border-radius: 8px;
  }

  .pull-btn:hover:not(:disabled) {
    background: rgba(120,180,255,0.3);
    border-color: rgba(120,180,255,0.7);
    transform: translateY(-2px);
  }

  .pull-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  .pull-text {
    font-size: 1rem;
    font-weight: 600;
  }

  .pull-cost {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.8);
  }

  /* Action buttons */
  .actions {
    display: flex;
    justify-content: center;
  }

  .close-btn {
    padding: 0.75rem 2rem;
    background: rgba(255,255,255,0.1);
    border: 2px solid rgba(255,255,255,0.3);
    color: #fff;
    cursor: pointer;
    transition: all 0.2s ease;
    border-radius: 8px;
    font-size: 1rem;
  }

  .close-btn:hover {
    background: rgba(255,255,255,0.15);
    border-color: rgba(255,255,255,0.5);
  }

  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .tab-row {
      justify-content: center;
    }
    
    .banner-stats {
      justify-content: center;
    }
    
    .char-info {
      flex-direction: column;
      text-align: center;
    }
    
    .pull-actions {
      flex-direction: column;
    }
  }
</style>
