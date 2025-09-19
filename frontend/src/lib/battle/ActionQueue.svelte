<script>
  import { getCharacterImage, getElementColor } from '../systems/assetLoader.js';
  import { createEventDispatcher } from 'svelte';
  import { flip } from 'svelte/animate';

  export let queue = [];
  export let combatants = [];
  export let reducedMotion = false;
  export let showActionValues = false;
  // Current actor id (normal or bonus); used to pin actor at top
  export let activeId = null;

    const dispatch = createEventDispatcher();

    function findCombatant(id) {
      return combatants.find((c) => c.id === id) || null;
    }

    // Filter queue to alive/visible entries
    $: displayQueue = queue.filter((e) => {
      const fighter = findCombatant(e.id);
      // Only include entries for combatants that still exist and are alive
      if (!fighter) return false; // removed/despawned
      return Number(fighter.hp ?? 0) >= 1;
    });
    // Count bonus entries by actor id
    $: bonusCounts = (() => {
      const map = new Map();
      for (const e of displayQueue) {
        if (e?.bonus) map.set(e.id, (map.get(e.id) || 0) + 1);
      }
      return map;
    })();

    // Base list excludes bonus entries; we render one tile per actor
    $: baseQueue = displayQueue.filter((e) => !e.bonus);

    // Determine current active actor id (prefer provided activeId; otherwise first visible in queue)
    $: currentActiveId = (() => {
      const id = activeId ?? (displayQueue[0] && displayQueue[0].id);
      return id;
    })();

    // Build display items with active actor pinned to top
    $: displayItems = (() => {
      const firstIdx = baseQueue.findIndex((e) => e.id === currentActiveId);
      const ordered = firstIdx > 0
        ? [baseQueue[firstIdx], ...baseQueue.slice(0, firstIdx), ...baseQueue.slice(firstIdx + 1)]
        : baseQueue.slice();
      const counts = new Map();
      return ordered.map((e) => {
        const n = (counts.get(e.id) || 0) + 1;
        counts.set(e.id, n);
        return { entry: e, key: `${e.id}#${n}` };
      });
    })();

    $: activeIndex = 0; // top item is active
    $: needsFade = (displayItems?.length || 0) > 8;

  </script>

<div class="action-queue" data-testid="action-queue">
  <div class="viewport" class:masked={needsFade}>
    <div class="list">
      {#each displayItems as item, i (item.key)}
        {@const entry = item.entry}
        {@const fighter = findCombatant(entry.id)}
        {@const elColor = getElementColor(fighter?.element || entry?.element || 'generic')}
        <div
          class="entry"
          class:active={i === activeIndex}
          style="--element-color: {elColor}"
          animate:flip={{ duration: reducedMotion ? 0 : 220 }}
          on:mouseenter={() => dispatch('hover', { id: fighter?.id ?? null })}
          on:mouseleave={() => dispatch('hover', { id: null })}
        >
          <div class="inner">
            {#if (bonusCounts.get(entry.id) || 0) > 0}
              <div class="bonus-badge">x{bonusCounts.get(entry.id)}</div>
            {/if}
            <img 
              src={getCharacterImage((fighter?.summon_type === 'phantom' && fighter?.summoner_id) ? fighter.summoner_id : (fighter?.summon_type || fighter?.id || entry?.id))} 
              alt="" 
              class="portrait {fighter?.summon_type === 'phantom' ? 'phantom' : ''}" 
              title={(fighter?.name || fighter?.id || entry?.id || '').toString().replace(/[_-]+/g, ' ')}
            />
            {#if showActionValues}
              <div class="av">{Math.round(entry.action_value)}</div>
            {/if}
            <!-- Hover-only name chip -->
            <div class="name-chip">{(fighter?.name || fighter?.id || entry?.id || '').toString().replace(/[_-]+/g, ' ')}</div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  .action-queue {
    position: absolute;
    left: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    --entry-w: 192px;
    --entry-h: 108px; /* 16:9 */
    --gap: 0.25rem; /* baseline spacing */
    --gap-s: 0.125rem; /* compact spacing for non-active */
    --gap-l: 0.375rem; /* extra spacing after active */
    display: block;
    z-index: 2;
  }
  .viewport {
    position: relative;
    max-height: min(calc((var(--entry-h) + var(--gap)) * 8 - var(--gap)), calc(100vh - 2rem));
    overflow: hidden;
  }
  .viewport.masked::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    height: 18px;
    pointer-events: none;
    z-index: 1;
  }
  .viewport.masked::after {
    bottom: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.6), rgba(0,0,0,0));
  }
  .list {
    display: flex;
    flex-direction: column;
    gap: 0; /* manage spacing per-entry to compress non-active */
    align-items: flex-start; /* left-align entries */
    justify-content: center;
  }
  .entry {
    position: relative;
    width: var(--entry-w);
    height: var(--entry-h); /* 16:9 */
    will-change: transform;
    margin-bottom: var(--gap-s);
  }
  .entry.active { margin-bottom: var(--gap-l); }
  .entry:last-child { margin-bottom: 0; }
  .inner {
    position: absolute;
    inset: 0;
    border: 2px solid var(--element-color);
    border-radius: 8px;
    overflow: hidden;
    transform-origin: left center; /* keep scaled items hugged to the left */
    transform: scale(0.75); /* about 25% smaller for non-active */
    transition: transform 160ms ease, box-shadow 160ms ease, border-width 160ms ease;
  }
  .entry.active .inner {
    transform: scale(1);
    border-width: 4px;
    box-shadow: 0 0 8px 2px color-mix(in oklab, var(--element-color) 80%, white);
  }
  .entry:hover .inner {
    box-shadow: 0 0 10px 3px color-mix(in oklab, var(--element-color) 70%, white);
  }
  .entry.active .inner::before {
    content: '';
    position: absolute;
    left: -0.75rem;
    top: 50%;
    transform: translateY(-50%);
    border: 8px solid transparent;
    border-right-color: var(--element-color);
  }
  /* Bonus count badge shown on the actor's tile */
  .bonus-badge {
    position: absolute;
    top: 6px;
    right: 6px;
    font-weight: 800;
    font-size: 0.8rem;
    color: #fff;
    background: rgba(0,0,0,0.55);
    border: 1px solid color-mix(in oklab, var(--element-color) 70%, #fff);
    border-radius: 10px;
    padding: 0 6px;
    line-height: 1.2;
    text-shadow: 0 1px 2px rgba(0,0,0,0.8);
    pointer-events: none;
  }
  .portrait {
    width: 100%;
    height: 100%;
    display: block;
    object-fit: cover;
  }
  .portrait.phantom { filter: grayscale(60%) brightness(0.92); }
  .av {
    position: absolute;
    bottom: 4px;
    right: 4px;
    font-size: 0.75rem;
    background: rgba(0,0,0,0.35);
    box-shadow: inset 0 0 0 2px color-mix(in oklab, var(--element-color) 60%, black);
    border-radius: 6px;
    padding: 0 6px;
    color: var(--element-color);
  }

  /* Hover-only name chip, similar to BattleFighterCard */
  .name-chip {
    position: absolute;
    left: 6px;
    bottom: 6px;
    color: #fff;
    font-weight: 800;
    font-size: 0.78rem;
    line-height: 1.05;
    padding: 2px 8px;
    border-radius: 6px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.9);
    pointer-events: none;
    opacity: 0;
    transform: translateY(2px);
    transition: opacity 120ms ease, transform 120ms ease;
    z-index: 2;
  }
  .entry:hover .name-chip { opacity: 1; transform: translateY(0); }
  /* Soft faded-edge backdrop behind the name chip (mirrors BattleFighterCard) */
  .name-chip::before {
    content: '';
    position: absolute;
    inset: -10px;
    border-radius: 12px;
    background: radial-gradient(
      ellipse at center,
      rgba(0, 0, 0, 0.55) 0%,
      rgba(0, 0, 0, 0.50) 40%,
      rgba(0, 0, 0, 0.30) 70%,
      rgba(0, 0, 0, 0.00) 100%
    );
    filter: blur(4px);
    box-shadow: 0 0 16px rgba(0,0,0,0.3);
    z-index: -1;
    pointer-events: none;
  }
</style>
