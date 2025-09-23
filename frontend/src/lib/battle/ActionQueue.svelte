<script>
  import { getCharacterImage, getElementColor } from '../systems/assetLoader.js';
  import { createEventDispatcher } from 'svelte';
  import { flip } from 'svelte/animate';

  export let queue = [];
  export let combatants = [];
  export let reducedMotion = false;
  export let effectiveReducedMotion = false;
  export let showActionValues = false;
  // Current actor id (normal or bonus); used to pin actor at top
  export let activeId = null;
  export let currentTurn = null;
  export let enrage = { active: false, stacks: 0, turns: 0 };
  export let showTurnCounter = true;
  export let flashEnrageCounter = true;

  const dispatch = createEventDispatcher();

  $: motionDisabled = reducedMotion || effectiveReducedMotion;
  $: normalizedTurn = Number.parseInt(currentTurn ?? '', 10);
  $: displayTurn = Number.isFinite(normalizedTurn) && normalizedTurn > 0 ? normalizedTurn : '—';
  $: enrageCount = (() => {
    const primary = enrage?.stacks ?? enrage?.turns ?? 0;
    const parsed = Number(primary);
    if (!Number.isFinite(parsed)) return 0;
    return Math.max(0, Math.trunc(parsed));
  })();
  $: showEnrageChip = Boolean(enrage?.active);
  $: enragePulse = showEnrageChip && !motionDisabled && flashEnrageCounter;

  function findCombatant(id) {
    return combatants.find((c) => c.id === id) || null;
  }

  const TURN_COUNTER_ID = 'turn_counter';

  // Filter queue to alive/visible entries
  $: displayQueue = queue.filter((e) => {
    const id = e?.id;
    if (!id) return false;
    if (id === TURN_COUNTER_ID) return showTurnCounter;
    const fighter = findCombatant(id);
    // Only include entries for combatants that still exist and are alive
    if (!fighter) return false; // removed/despawned
    return Number(fighter.hp ?? 0) >= 1;
  });
  // Count bonus entries by actor id
  $: bonusCounts = (() => {
    const map = new Map();
    for (const e of displayQueue) {
      if (e?.id === TURN_COUNTER_ID) continue;
      if (e?.bonus) map.set(e.id, (map.get(e.id) || 0) + 1);
    }
    return map;
  })();

  // Base list excludes bonus entries; we render one tile per actor
  $: baseQueue = displayQueue.filter((e) => !(e?.bonus && e?.id !== TURN_COUNTER_ID));

  // Determine current active actor id (prefer provided activeId; otherwise first visible in queue)
  $: currentActiveId = (() => {
    if (activeId) return activeId;
    const firstFighter = displayQueue.find((e) => e.id !== TURN_COUNTER_ID);
    return firstFighter?.id ?? null;
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
        {#if entry.id === TURN_COUNTER_ID}
          <div
            class="entry turn-counter"
            class:enraged={showEnrageChip}
            class:motionless={motionDisabled}
            animate:flip={{ duration: motionDisabled ? 0 : 220 }}
          >
            <div class="inner">
              <div class="turn-card">
                <div class="turn-label">
                  <span class="label-text">Turn</span>
                  <span class="turn-value">{displayTurn}</span>
                </div>
                {#if showEnrageChip}
                  <span class="enrage-chip" class:pulse={enragePulse}>Enrage: {enrageCount}</span>
                {/if}
              </div>
            </div>
          </div>
        {:else}
          {@const fighter = findCombatant(entry.id)}
          {@const elColor = getElementColor(fighter?.element || entry?.element || 'generic')}
          <div
            class="entry"
            class:active={i === activeIndex}
            style="--element-color: {elColor}"
            animate:flip={{ duration: motionDisabled ? 0 : 220 }}
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
        {/if}
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
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.4rem;
    z-index: 2;
  }
  .enrage-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    background: color-mix(in oklab, rgba(160, 20, 36, 0.65) 80%, rgba(60, 0, 0, 0.25));
    border: 1px solid rgba(255, 120, 140, 0.75);
    color: #ffe8ed;
    box-shadow: 0 0 6px 0 rgba(255, 90, 110, 0.45);
  }
  .enrage-chip.pulse {
    animation: enragePulse 2.6s ease-in-out infinite;
  }
  .entry.turn-counter {
    --turn-accent: color-mix(in oklab, #4c8cff 75%, white);
    margin-bottom: var(--gap);
  }
  .entry.turn-counter .inner {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.75rem;
    background: linear-gradient(
      135deg,
      color-mix(in oklab, rgba(20, 32, 50, 0.65) 55%, rgba(10, 12, 18, 0.8)),
      color-mix(in oklab, var(--turn-accent) 65%, rgba(10, 12, 18, 0.85))
    );
    border-width: 3px;
    border-style: solid;
    border-color: color-mix(in oklab, var(--turn-accent) 70%, white);
    box-shadow: 0 0 12px 2px color-mix(in oklab, var(--turn-accent) 40%, rgba(0,0,0,0.85));
    transform: scale(0.88);
    transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 220ms ease;
  }
  .entry.turn-counter .inner::before { display: none; }
  .entry.turn-counter.enraged { --turn-accent: color-mix(in oklab, #ff5268 85%, white); }
  .entry.turn-counter .turn-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    height: 100%;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.045em;
    color: color-mix(in oklab, var(--turn-accent) 90%, white);
    text-shadow: 0 2px 6px rgba(0,0,0,0.75);
  }
  .entry.turn-counter .turn-label {
    display: flex;
    align-items: baseline;
    gap: 0.45rem;
  }
  .entry.turn-counter .label-text {
    font-size: 0.85rem;
    font-weight: 700;
    color: color-mix(in oklab, var(--turn-accent) 60%, white);
    letter-spacing: 0.08em;
  }
  .entry.turn-counter .turn-value {
    font-size: 1.6rem;
    font-weight: 900;
    color: #fff;
    line-height: 1;
    filter: drop-shadow(0 0 4px rgba(0,0,0,0.55));
  }
  .entry.turn-counter .enrage-chip {
    align-self: center;
    margin-top: 0.2rem;
    box-shadow: 0 0 10px 2px color-mix(in oklab, var(--turn-accent) 45%, rgba(0,0,0,0.65));
  }
  .entry.turn-counter.motionless .inner {
    transition-duration: 0.01ms !important;
    box-shadow: 0 0 10px 1px color-mix(in oklab, var(--turn-accent) 35%, rgba(0,0,0,0.8));
  }
  .viewport {
    position: relative;
    width: var(--entry-w);
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

  @media (prefers-reduced-motion: reduce) {
    .entry.turn-counter .inner {
      transition-duration: 0.01ms !important;
    }
    .entry.turn-counter .enrage-chip {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
    }
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

  @keyframes enragePulse {
    0%, 100% {
      background: color-mix(in oklab, rgba(160, 20, 36, 0.65) 60%, rgba(30, 0, 0, 0.25));
      box-shadow: 0 0 6px 0 rgba(255, 90, 110, 0.45);
      border-color: rgba(255, 120, 140, 0.75);
    }
    50% {
      background: color-mix(in oklab, rgba(220, 40, 60, 0.8) 85%, rgba(60, 0, 0, 0.25));
      box-shadow: 0 0 18px 4px rgba(255, 110, 130, 0.65);
      border-color: rgba(255, 160, 180, 0.9);
    }
  }
</style>
