<script>
  import { createEventDispatcher, onDestroy } from 'svelte';
  import RewardCard from './RewardCard.svelte';
  import CurioChoice from './CurioChoice.svelte';

  export let cards = [];
  export let relics = [];
  export let items = [];
  export let gold = 0;
  export let partyStats = [];
  export let ended = false;
  export let nextRoom = '';
  export let fullIdleMode = false;
  export let sfxVolume = 5;
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  // Render immediately; CSS animations handle reveal on mount

  $: normalizedSfxVolume = (() => {
    const value = Number(sfxVolume);
    if (!Number.isFinite(value)) return 5;
    if (value < 0) return 0;
    if (value > 10) return 10;
    return value;
  })();
  $: iconQuiet = Boolean(reducedMotion || normalizedSfxVolume <= 0);
  $: revealDelay = (index) => (reducedMotion ? 0 : index * 120);
  $: lootItems = Array.isArray(items) ? items : [];
  $: hasLootItems = lootItems.length > 0;
  $: dataReducedMotion = reducedMotion ? 'true' : 'false';
  $: dataSfxVolume = String(normalizedSfxVolume);

  function titleForItem(item) {
    if (!item) return '';
    const uiMeta = item.ui && typeof item.ui === 'object' ? item.ui : null;
    if (uiMeta) {
      const label = uiMeta.label || uiMeta.title;
      if (label) return label;
    }
    if (item.name) return item.name;
    const id = String(item.id || '').toLowerCase();
    const cap = id.charAt(0).toUpperCase() + id.slice(1);
    const stars = Number.isFinite(item.stars) ? String(item.stars) : '';
    return stars ? `${cap} Upgrade (${stars})` : `${cap} Upgrade`;
  }

  let cardsDone = false;
  let showNextButton = false;
  $: showCards = cards.length > 0 && !cardsDone;
  $: showRelics = relics.length > 0 && (cards.length === 0 || cardsDone);
  $: remaining = (showCards ? cards.length : 0) + (showRelics ? relics.length : 0);

  function handleSelect(e) {
    const detail = e.detail || {};
    if (detail.type === 'card') {
      cardsDone = true;
    }
    dispatch('select', detail);
  }

  // Auto-advance when there are no selectable rewards and no visible loot/gold.
  // This avoids showing an empty rewards popup in loot-consumed cases.
  let autoTimer;
  $: {
    clearTimeout(autoTimer);
    const noChoices = remaining === 0;
    const noLoot = (!gold || gold <= 0) && !hasLootItems;
    if (noChoices && noLoot) {
      autoTimer = setTimeout(() => dispatch('next'), 5000);
    }
  }
  // Cleanup timer on unmount
  onDestroy(() => clearTimeout(autoTimer));

  // Show Next Room button when there's loot but no choices
  $: {
    const noChoices = remaining === 0;
    const hasLoot = (gold > 0) || hasLootItems;
    showNextButton = noChoices && hasLoot;
  }

  function handleNextRoom() {
    dispatch('lootAcknowledge');
  }
</script>

<style>
  .layout {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .section-title {
    margin: 0.25rem 0 0.5rem;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
  }

  .choices {
    display: grid;
    grid-template-columns: repeat(3, minmax(200px, 1fr));
    gap: 0.75rem;
    align-items: stretch;
    justify-items: center;
    width: 100%;
    max-width: 960px;
  }

  .status {
    margin-top: 0.25rem;
    text-align: center;
    color: #ddd;
  }
  .status ul {
    display: inline-block;
    margin: 0.25rem 0;
    padding-left: 1rem;
    text-align: left;
  }
  /* CSS-based reveal: slide the whole card, twinkles appear first, then card fades in */
  @keyframes overlay-slide {
    0%   { transform: translateY(-40px); }
    100% { transform: translateY(0); }
  }
  /* Twinkles fade in early to "form" the card */
  @keyframes overlay-twinkle-fade {
    0%   { opacity: 0; }
    20%  { opacity: 0.6; }
    40%  { opacity: 1; }
    100% { opacity: 1; }
  }
  /* Card content fades in later than twinkles */
  @keyframes overlay-card-fade {
    0%   { opacity: 0; }
    30%  { opacity: 0; }
    100% { opacity: 1; }
  }
  .reveal {
    animation: overlay-slide 360ms cubic-bezier(0.22, 1, 0.36, 1) both;
    animation-delay: var(--delay, 0ms);
  }
  /* Target the CardArt twinkles layer only */
  .reveal :global(.twinkles) {
    opacity: 0;
    animation: overlay-twinkle-fade 520ms cubic-bezier(0.22, 1, 0.36, 1) both;
    animation-delay: var(--delay, 0ms);
  }
  /* Fade in the card content (including photo/box) slightly after twinkles */
  .reveal :global(.card-art) {
    opacity: 0;
    animation: overlay-card-fade 520ms cubic-bezier(0.22, 1, 0.36, 1) both;
    animation-delay: var(--delay, 0ms);
  }

  .next-button {
    margin-top: 1rem;
    padding: 0.75rem 2rem;
    background: linear-gradient(145deg, #4a90e2, #357abd);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    transition: all 0.2s ease;
  }

  .next-button:hover {
    background: linear-gradient(145deg, #5ba0f2, #4a90e2);
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.3);
  }

  .next-button:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }

  .next-room-overlay {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1500;
    animation: slideUp 0.3s ease-out;
  }

  .next-button.overlay {
    margin: 0;
    padding: 1rem 2.5rem;
    font-size: 1.1rem;
    font-weight: 700;
    border-radius: 2rem;
    background: linear-gradient(145deg, #4CAF50, #45a049);
    box-shadow: 0 6px 20px rgba(0,0,0,0.3), 0 2px 6px rgba(76, 175, 80, 0.4);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(255, 255, 255, 0.2);
  }

  .next-button.overlay:hover {
    background: linear-gradient(145deg, #5CBF60, #4CAF50);
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.4), 0 4px 10px rgba(76, 175, 80, 0.5);
  }

  .next-button.overlay:active {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.3), 0 2px 6px rgba(76, 175, 80, 0.4);
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }

  @media (max-width: 768px) {
    .next-room-overlay {
      bottom: 1rem;
      left: 1rem;
      right: 1rem;
      transform: none;
      text-align: center;
    }

    .next-button.overlay {
      width: 100%;
      padding: 1rem;
    }
  }
  
</style>

<div class="layout" data-reduced-motion={dataReducedMotion} data-sfx-volume={dataSfxVolume}>
  {#if showCards}
  <h3 class="section-title">Choose a Card</h3>
  <div class="choices">
        {#each cards.slice(0,3) as card, i (card.id)}
          <div class:reveal={!reducedMotion} style={`--delay: ${revealDelay(i)}ms`}>
            <RewardCard entry={card} type="card" quiet={iconQuiet} on:select={handleSelect} />
          </div>
        {/each}
    </div>
  {/if}
  {#if showRelics}
  <h3 class="section-title">Choose a Relic</h3>
  <div class="choices">
        {#each relics.slice(0,3) as relic, i (relic.id)}
          <div class:reveal={!reducedMotion} style={`--delay: ${revealDelay(i)}ms`}>
            <CurioChoice entry={relic} quiet={iconQuiet} on:select={handleSelect} />
          </div>
        {/each}
    </div>
  {/if}
  
  {#if hasLootItems}
    <h3 class="section-title">Drops</h3>
    <div class="status">
      <ul>
        {#each lootItems as item}
          <li>{titleForItem(item)}</li>
        {/each}
      </ul>
    </div>
  {/if}
  {#if gold}
    <div class="status">Gold +{gold}</div>
  {/if}
  
  {#if showNextButton}
    <div class="next-room-overlay">
      <button class="next-button overlay" on:click={handleNextRoom}>Next Room</button>
    </div>
  {/if}
  <!-- Auto-advance remains when no choices/loot -->
</div>
