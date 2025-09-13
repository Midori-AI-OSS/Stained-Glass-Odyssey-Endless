<script>
  import { getCharacterImage, getElementColor } from '../systems/assetLoader.js';
  import { flip } from 'svelte/animate';

  export let queue = [];
  export let combatants = [];
  export let reducedMotion = false;
  export let showActionValues = false;

    function findCombatant(id) {
      return combatants.find((c) => c.id === id) || { id };
    }

    // Track visual fade state when the active actor cycles to bottom
    let prevKeys = [];
    let prevActiveKey = null;
    let exiting = {}; // key -> true while fading out
    let entering = {}; // key -> true while fading in at bottom

    function markExiting(key) {
      exiting = { ...exiting, [key]: true };
    }
    function clearExiting(key) {
      const { [key]: _, ...rest } = exiting; exiting = rest;
    }
    function markEntering(key) {
      entering = { ...entering, [key]: true };
    }
    function clearEntering(key) {
      const { [key]: _, ...rest } = entering; entering = rest;
    }

    $: displayQueue = queue.filter((e) => {
      const fighter = findCombatant(e.id);
      // Include if unknown (so summons still render) or alive
      return fighter?.hp == null ? true : Number(fighter.hp) >= 1;
    });
    // Stable keys: one normal (N) per id, optional bonus (B) per id
    $: displayItems = displayQueue.map((e) => ({ entry: e, key: `${e.id}|${e.bonus ? 'B' : 'N'}` }));
    $: activeIndex = displayQueue.findIndex((e) => !e.bonus);
    $: needsFade = (displayQueue?.length || 0) > 8;

    // Detect when the previously active item moves down the list and apply fade-out->in
    $: {
      const keys = displayItems.map((i) => i.key);
      const activeKey = displayItems[activeIndex]?.key;
      if (prevActiveKey && prevActiveKey !== activeKey) {
        const newIndex = keys.indexOf(prevActiveKey);
        // If the previous active still exists and moved below the active index, treat as completed
        if (newIndex !== -1 && newIndex > activeIndex) {
          const outMs = reducedMotion ? 0 : 180;
          const moveMs = reducedMotion ? 0 : 220; // matches flip duration
          const inMs = reducedMotion ? 0 : 240;
          markExiting(prevActiveKey);
          // Keep hidden until movement completes, then fade-in
          setTimeout(() => {
            clearExiting(prevActiveKey);
            markEntering(prevActiveKey);
            setTimeout(() => { clearEntering(prevActiveKey); }, inMs);
          }, outMs + moveMs);
        }
      }
      prevKeys = keys;
      prevActiveKey = activeKey || prevActiveKey;
    }
  </script>

<div class="action-queue" data-testid="action-queue">
  <div class="viewport" class:masked={needsFade}>
    <div class="list">
      {#each displayItems as item, i (item.key)}
        {@const entry = item.entry}
        {@const fighter = findCombatant(entry.id)}
        {@const elColor = getElementColor(fighter.element)}
        <div
          class="entry"
          class:active={i === activeIndex}
          class:bonus={entry.bonus}
          class:exiting={Boolean(exiting[item.key])}
          class:entering={Boolean(entering[item.key])}
          style="--element-color: {elColor}"
          animate:flip={{ duration: reducedMotion ? 0 : 220 }}
        >
          <div class="inner">
            <img src={getCharacterImage(fighter.summon_type || fighter.id)} alt="" class="portrait" />
            {#if showActionValues}
              <div class="av">{Math.round(entry.action_value)}</div>
            {/if}
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
    transition: transform 160ms ease, box-shadow 160ms ease, border-width 160ms ease, opacity 160ms ease;
    opacity: 1;
  }
  .entry.active .inner {
    transform: scale(1);
    border-width: 4px;
    box-shadow: 0 0 8px 2px color-mix(in oklab, var(--element-color) 80%, white);
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
  .entry.bonus {
    /* Slightly de-emphasize bonus entries */
  }
  .entry.bonus .inner {
    opacity: 0.6;
  }
  /* Fade behavior for completed actors cycling to bottom */
  .entry.exiting .inner {
    opacity: 0; /* fade out as it moves down */
  }
  .entry.entering .inner {
    animation: aq-fade-in 240ms ease both;
  }
  @keyframes aq-fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  .portrait {
    width: 100%;
    height: 100%;
    display: block;
    object-fit: cover;
  }
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
</style>
