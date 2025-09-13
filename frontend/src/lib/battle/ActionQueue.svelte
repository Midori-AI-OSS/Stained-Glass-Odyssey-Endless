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

    $: displayQueue = queue.filter((e) => {
      const fighter = findCombatant(e.id);
      return fighter.hp >= 1;
    });
    $: activeIndex = displayQueue.findIndex((e) => !e.bonus);
    $: needsFade = (displayQueue?.length || 0) > 8;
  </script>

<div class="action-queue" data-testid="action-queue">
  <div class="viewport" class:masked={needsFade}>
    <div class="list">
      {#each displayQueue as entry, i (entry.bonus ? `b-${entry.id}-${i}` : entry.id)}
        {@const fighter = findCombatant(entry.id)}
        {@const elColor = getElementColor(fighter.element)}
        <div
          class="entry"
          class:active={i === activeIndex}
          class:bonus={entry.bonus}
          style="--element-color: {elColor}"
          animate:flip={{ duration: reducedMotion ? 0 : 220 }}
        >
          <img src={getCharacterImage(fighter.summon_type || fighter.id)} alt="" class="portrait" />
          {#if showActionValues}
            <div class="av">{Math.round(entry.action_value)}</div>
          {/if}
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
    --gap: 0.5rem;
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
    gap: var(--gap);
    align-items: center;
    justify-content: center;
  }
  .entry {
    position: relative;
    width: var(--entry-w);
    height: var(--entry-h); /* 16:9 */
    will-change: transform;
    border: 2px solid var(--element-color);
    border-radius: 8px;
    overflow: hidden;
  }
  .entry.active {
    border-width: 4px;
    box-shadow: 0 0 8px 2px color-mix(in oklab, var(--element-color) 80%, white);
  }
  .entry.active::before {
    content: '';
    position: absolute;
    left: -0.75rem;
    top: 50%;
    transform: translateY(-50%);
    border: 8px solid transparent;
    border-right-color: var(--element-color);
  }
  .entry.bonus {
    opacity: 0.6;
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
