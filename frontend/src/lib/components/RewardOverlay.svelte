<script>
  import { createEventDispatcher, onDestroy } from 'svelte';
  import { cubicOut } from 'svelte/easing';
  import { scale } from 'svelte/transition';
  import RewardCard from './RewardCard.svelte';
  import CurioChoice from './CurioChoice.svelte';
  import { getMaterialIcon, onMaterialIconError } from '../systems/assetLoader.js';
  import { createRewardDropSfx } from '../systems/sfx.js';

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

  const starColors = {
    1: '#808080',
    2: '#1E90FF',
    3: '#228B22',
    4: '#800080',
    5: '#FF3B30',
    6: '#FFD700',
    fallback: '#708090'
  };

  function sanitizeStars(value) {
    const num = Number(value);
    if (!Number.isFinite(num) || num <= 0) return 1;
    return Math.min(Math.round(num), 6);
  }

  function accentForItem(item) {
    if (String(item?.id || '') === 'ticket') {
      return starColors.fallback;
    }
    const stars = sanitizeStars(item?.stars);
    return starColors[stars] || starColors.fallback;
  }

  function materialKeyForItem(item) {
    const id = String(item?.id || '').trim();
    if (!id) return '';
    if (id === 'ticket') return 'ticket';
    const rawStars = Number(item?.stars);
    if (!Number.isFinite(rawStars) || rawStars <= 0) {
      return id;
    }
    const stars = sanitizeStars(rawStars);
    return `${id}_${stars}`;
  }

  function stackFromItem(item) {
    if (!item || typeof item !== 'object') return 1;
    const candidates = ['count', 'quantity', 'qty', 'amount'];
    for (const key of candidates) {
      if (key in item) {
        const value = Number(item[key]);
        if (Number.isFinite(value) && value > 0) {
          return Math.max(1, Math.floor(value));
        }
      }
    }
    if (typeof item.stacks === 'number' && Number.isFinite(item.stacks)) {
      const stacks = Number(item.stacks);
      if (stacks > 0) return Math.floor(stacks);
    }
    return 1;
  }

  $: dropEntries = (() => {
    if (!hasLootItems) return [];
    const grouped = [];
    const seen = new Map();
    let fallbackIndex = 0;
    for (const item of lootItems) {
      if (!item || typeof item !== 'object') continue;
      const baseKey = materialKeyForItem(item);
      const groupKey = baseKey || `fallback-${fallbackIndex++}`;
      const iconKey = baseKey || String(item.id || '');
      const count = stackFromItem(item);
      const label = titleForItem(item);
      const accent = accentForItem(item);
      const existing = seen.get(groupKey);
      if (existing) {
        existing.count += count;
        if (label) existing.label = label;
        continue;
      }
      const safeLabel = label || (iconKey ? iconKey.replace(/_/g, ' ') : 'Loot item');
      const entry = {
        key: `drop-${groupKey}`,
        icon: getMaterialIcon(iconKey),
        label: safeLabel,
        count,
        accent
      };
      seen.set(groupKey, entry);
      grouped.push(entry);
    }
    return grouped;
  })();

  const DROP_REVEAL_INTERVAL_MS = 220;
  let visibleDrops = [];
  let dropRevealTimers = [];
  let dropRevealGeneration = 0;
  let dropSfxPlayer = null;
  let dropPopTransition = null;

  $: dropPopTransition = reducedMotion
    ? null
    : { duration: 180, easing: cubicOut, start: 0.75 };

  function clearDropRevealTimers() {
    if (dropRevealTimers.length === 0) return;
    for (const timer of dropRevealTimers) {
      clearTimeout(timer);
    }
    dropRevealTimers = [];
  }

  function stopDropAudio(release = false) {
    if (!dropSfxPlayer) return;
    try {
      dropSfxPlayer.stop?.();
    } catch {
      // ignore playback reset failures
    }
    if (release) {
      dropSfxPlayer = null;
    }
  }

  function playRewardDropAudio() {
    if (reducedMotion) return;
    if (normalizedSfxVolume <= 0) {
      stopDropAudio(true);
      return;
    }
    if (!dropSfxPlayer) {
      dropSfxPlayer = createRewardDropSfx(normalizedSfxVolume, { reducedMotion });
    }
    if (!dropSfxPlayer || typeof dropSfxPlayer.play !== 'function') return;
    if (typeof dropSfxPlayer.setVolume === 'function') {
      dropSfxPlayer.setVolume(normalizedSfxVolume);
    }
    const playPromise = dropSfxPlayer.play();
    if (playPromise && typeof playPromise.catch === 'function') {
      playPromise.catch(() => {});
    }
  }

  function updateDropSequence(entries, motionReduced) {
    dropRevealGeneration += 1;
    const generation = dropRevealGeneration;
    clearDropRevealTimers();
    if (!Array.isArray(entries) || entries.length === 0) {
      visibleDrops = [];
      stopDropAudio(true);
      return;
    }
    if (motionReduced) {
      stopDropAudio(true);
      visibleDrops = entries;
      return;
    }
    stopDropAudio();
    visibleDrops = [];
    entries.forEach((_, index) => {
      const timer = setTimeout(() => {
        if (generation !== dropRevealGeneration) return;
        visibleDrops = entries.slice(0, index + 1);
        playRewardDropAudio();
      }, index * DROP_REVEAL_INTERVAL_MS);
      dropRevealTimers.push(timer);
    });
  }

  $: updateDropSequence(dropEntries, reducedMotion);

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
  onDestroy(() => {
    clearTimeout(autoTimer);
    clearDropRevealTimers();
    stopDropAudio(true);
  });

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

  .drops-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: flex-start;
    gap: 0.75rem;
    width: 100%;
    max-width: 640px;
    padding: 0.35rem 0;
  }

  .drop-tile {
    position: relative;
    width: 64px;
    height: 64px;
    border-radius: 12px;
    background: color-mix(in oklab, var(--accent, rgba(255,255,255,0.12)) 28%, rgba(10, 12, 20, 0.92));
    border: 1px solid color-mix(in oklab, var(--accent, rgba(255,255,255,0.2)) 38%, rgba(255,255,255,0.08));
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px;
    overflow: hidden;
    transition: transform 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
    will-change: transform, opacity;
  }

  .drop-tile:hover {
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 14px 26px rgba(0, 0, 0, 0.45);
  }

  .drop-icon {
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.4));
  }

  .drop-count {
    position: absolute;
    bottom: 6px;
    right: 8px;
    background: rgba(0, 0, 0, 0.78);
    color: #fff;
    border-radius: 6px;
    padding: 0 0.4rem;
    font-size: 0.75rem;
    font-weight: 700;
    line-height: 1.1rem;
    min-width: 1.5rem;
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
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
    <div class="drops-row" role="list">
      {#each visibleDrops as entry (entry.key)}
        <div
          class="drop-tile"
          role="listitem"
          style={`--accent: ${entry.accent}`}
          aria-label={`${entry.label}${entry.count > 1 ? ` x${entry.count}` : ''}`}
          in:scale={dropPopTransition}
        >
          <img
            class="drop-icon"
            src={entry.icon}
            alt=""
            aria-hidden="true"
            on:error={onMaterialIconError}
          />
          {#if entry.count > 1}
            <span class="drop-count">x{entry.count}</span>
          {/if}
          <span class="sr-only">{entry.label}{entry.count > 1 ? ` x${entry.count}` : ''}</span>
        </div>
      {/each}
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
