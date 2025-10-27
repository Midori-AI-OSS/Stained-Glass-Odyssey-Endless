<!--
  NavBar.svelte
  Displays top-left navigation controls and snapshot status.
  Emits high-level navigation events without managing run logic.
-->
<script>
  import { Diamond, Settings, Swords, ArrowLeft, Package, Eye } from 'lucide-svelte';
  import { createEventDispatcher } from 'svelte';
  import Spinner from './Spinner.svelte';

  export let battleActive = false;
  export let viewMode = 'main';
  export let snapshotLoading = false;
  export let runId = '';
  const dispatch = createEventDispatcher();

  let longPressTimer = null;
  let longPressTriggered = false;

  function handleHomePointerDown() {
    longPressTriggered = false;
    clearTimeout(longPressTimer);
    // Long-press after 800ms triggers force-next-room safety
    longPressTimer = setTimeout(() => {
      longPressTriggered = true;
      dispatch('forceNextRoom');
    }, 800);
  }

  function handleHomePointerUp() {
    clearTimeout(longPressTimer);
  }

  function handleHomeClick() {
    if (longPressTriggered) return; // suppress normal home on long-press
    dispatch('home');
  }
</script>

<div class="nav-wrapper">
  <div class="stained-glass-bar">
    {#if battleActive}
      <button class="icon-btn" title="Battle">
        <Swords size={22} color="#fff" />
      </button>
    {:else}
      <button class="icon-btn" title="Home"
        on:pointerdown={handleHomePointerDown}
        on:pointerup={handleHomePointerUp}
        on:mouseleave={handleHomePointerUp}
        on:click={handleHomeClick}
      >
        <Diamond size={22} color="#fff" />
      </button>
    {/if}
    {#if battleActive}
      <button class="icon-btn" title="Combat Viewer" on:click={() => dispatch('openCombatViewer')}>
        <Eye size={22} color="#fff" />
      </button>
    {/if}
    {#if runId}
      <button class="icon-btn" title="Inventory" on:click={() => dispatch('openInventory')}>
        <Package size={22} color="#fff" />
      </button>
    {/if}
    <!-- Player Editor button removed per design -->
    <button class="icon-btn" title="Settings" on:click={() => dispatch('settings')}>
      <Settings size={22} color="#fff" />
    </button>
    {#if viewMode !== 'main'}
      <button class="icon-btn" title="Back" on:click={() => dispatch('back')}>
        <ArrowLeft size={22} color="#fff" />
      </button>
    {/if}
  </div>
  <div class="snapshot-panel" class:active={snapshotLoading}>
    <Spinner style="color:#fff" size="1rem" thickness="2px" />
    <span>Syncing...</span>
  </div>
</div>

<style>
  .nav-wrapper { position: absolute; top: 1.2rem; left: 1.2rem; display: flex; gap: 0.5rem; z-index: 10; }
  .stained-glass-bar { display: flex; gap: 0.5rem; padding: 0.5rem 0.7rem; border-radius: 0; background: var(--glass-bg); box-shadow: var(--glass-shadow); border: var(--glass-border); backdrop-filter: var(--glass-filter); opacity: 0.99; }
  .icon-btn { background: rgba(255,255,255,0.10); border: none; border-radius: 0; width: 2.9rem; height: 2.9rem; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background 0.18s, box-shadow 0.18s; box-shadow: 0 1px 4px 0 rgba(0,40,120,0.10); }
  .icon-btn:hover { background: rgba(120,180,255,0.22); box-shadow: 0 2px 8px 0 rgba(0,40,120,0.18); }
  .icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .snapshot-panel { display: flex; align-items: center; gap: 0.4rem; padding: 0.5rem 0.7rem; border-radius: 0; background: var(--glass-bg); box-shadow: var(--glass-shadow); border: var(--glass-border); backdrop-filter: var(--glass-filter); opacity: 0; transition: opacity 0.2s; }
  .snapshot-panel.active { opacity: 0.99; }
</style>
