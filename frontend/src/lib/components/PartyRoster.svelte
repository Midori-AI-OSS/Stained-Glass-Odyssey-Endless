<script>
  import { getElementIcon, getElementColor } from '../systems/assetLoader.js';
  import { createEventDispatcher } from 'svelte';
  import { fly } from 'svelte/transition';
  import { flip } from 'svelte/animate';

  /**
   * Displays the available roster and handles character selection.
   *
   * Props:
   * - roster: array of character objects
   * - selected: array of selected character IDs
   * - previewId: ID of the character currently previewed (two-way bound)
   * - compact: render compact icon list when true
   */
  export let roster = [];
  export let selected = [];
  export let previewId;
  export let compact = false;
  export let reducedMotion = false;
  const dispatch = createEventDispatcher();

  let sortKey = 'name';
  let sortDir = 'asc';
  $: sortedRoster = (() => {
    const compare = (a, b) => {
      let res = 0;
      if (sortKey === 'element') {
        res = a.element.localeCompare(b.element);
      } else if (sortKey === 'id') {
        res = String(a.id).localeCompare(String(b.id));
      } else {
        res = a.name.localeCompare(b.name);
      }
      return sortDir === 'asc' ? res : -res;
    };
    const selectedChars = roster
      .filter((c) => selected.includes(c.id))
      .sort(compare);
    const unselectedChars = roster
      .filter((c) => !selected.includes(c.id))
      .sort(compare);
    return [...selectedChars, ...unselectedChars];
  })();

  function select(id, e) {
    // Suppress the single-click select if a long-press just toggled
    if (suppressClick) {
      suppressClick = false;
      e && e.stopPropagation();
      e && e.preventDefault();
      return;
    }
    previewId = id;
  }

  function toggle(id) {
    dispatch('toggle', id);
  }

  // Long-press detection
  let longTimer = null;
  let longTriggered = false;
  let suppressClick = false;
  function onPointerDown(id, e) {
    longTriggered = false;
    clearTimeout(longTimer);
    longTimer = setTimeout(() => {
      longTriggered = true;
      suppressClick = true;
      toggle(id);
    }, 500);
  }
  function onPointerUp() {
    clearTimeout(longTimer);
  }

  // Deterministic pseudo-random from an id string
  function hashId(id) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < String(id).length; i++) {
      h ^= String(id).charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return (h >>> 0) / 0xffffffff;
  }

  function sweepDelay(id) {
    const r = hashId(id);
    // Delay between -2s and 0s for staggered start
    return -(r * 2).toFixed(2);
  }

  function sweepDuration(id) {
    const r = hashId(id * 7 + 'af');
    // Slow sweep: between 10s and 16s
    return (10 + r * 6).toFixed(2);
  }

  function onIntroStart(id, e) {
    if (!reducedMotion && selected.includes(id)) {
      e.target.classList.add('sparkle');
    }
  }

  function onIntroEnd(e) {
    e.target.classList.remove('sparkle');
  }

  // Count of currently selected characters (for divider placement)
  $: selectedCount = roster.filter((c) => selected.includes(c.id)).length;
</script>

{#if compact}
<div class="roster list compact" data-testid="roster">
  {#each roster.filter(c => selected.includes(c.id)) as char}
    <button
      data-testid={`choice-${char.id}`}
      class="char-btn"
      on:click={(e) => select(char.id, e)}
      on:dblclick={() => toggle(char.id)}
      on:pointerdown={(e) => onPointerDown(char.id, e)}
      on:pointerup={onPointerUp}
      on:pointerleave={onPointerUp}>
      <img src={char.img} alt={char.name} class="compact-img" />
    </button>
  {/each}
</div>
{:else}
<div class="roster-container">
  <div class="roster-header">
    <span>{selected.length} / 5 party members</span>
    <div class="sort-controls">
      <label>
        Sort:
        <select bind:value={sortKey}>
          <option value="name">Name</option>
          <option value="element">Element</option>
          <option value="id">ID</option>
        </select>
      </label>
      <button
        type="button"
        class="sort-dir"
        on:click={() => (sortDir = sortDir === 'asc' ? 'desc' : 'asc')}
        aria-label="Toggle sort direction">
        {sortDir === 'asc' ? '↑' : '↓'}
      </button>
    </div>
  </div>
  <div class="inline-divider" aria-hidden="true"></div>
  <div class="roster-list">
  {#if selectedCount > 0}
    <div class="section-label">Party</div>
    {#each roster.filter(c => selected.includes(c.id)).sort((a,b)=>{
      const aKey = sortKey === 'element' ? a.element : (sortKey === 'id' ? String(a.id) : a.name);
      const bKey = sortKey === 'element' ? b.element : (sortKey === 'id' ? String(b.id) : b.name);
      return (sortDir === 'asc' ? 1 : -1) * (aKey > bKey ? 1 : (aKey < bKey ? -1 : 0));
    }) as char (`party-${char.id}`)}
      <button
        type="button"
        data-testid={`choice-${char.id}`}
        class="char-row"
        class:selected={selected.includes(char.id)}
        class:reduced={reducedMotion}
        animate:flip={{ duration: reducedMotion ? 0 : 300 }}
        on:click={(e) => select(char.id, e)}
        on:dblclick={() => !char.is_player && toggle(char.id)}
        on:pointerdown={(e) => !char.is_player && onPointerDown(char.id, e)}
        on:pointerup={onPointerUp}
        on:pointerleave={onPointerUp}
        on:introstart={(e) => onIntroStart(char.id, e)}
        on:introend={onIntroEnd}
        in:fly={{ x: -100, duration: reducedMotion ? 0 : 300 }}
        out:fly={{ x: 100, duration: reducedMotion ? 0 : 300 }}
        style={`border-color: ${getElementColor(char.element)}; --el-color: ${getElementColor(char.element)}; --sweep-delay: ${sweepDelay(char.id)}s; --sweep-duration: ${sweepDuration(char.id)}s;`}>
        <img src={char.img} alt={char.name} class="row-img" />
        <span class="row-name">{char.name}</span>
        <svelte:component
          this={getElementIcon(char.element)}
          class="row-type"
          style={`color: ${getElementColor(char.element)}`}
          aria-hidden="true" />
      </button>
    {/each}
    <div class="inline-divider" aria-hidden="true"></div>
  {/if}
  <div class="section-label">Roster</div>
  {#each roster.filter(c => !selected.includes(c.id)).sort((a,b)=>{
    const aKey = sortKey === 'element' ? a.element : (sortKey === 'id' ? String(a.id) : a.name);
    const bKey = sortKey === 'element' ? b.element : (sortKey === 'id' ? String(b.id) : b.name);
    return (sortDir === 'asc' ? 1 : -1) * (aKey > bKey ? 1 : (aKey < bKey ? -1 : 0));
  }) as char (`roster-${char.id}`)}
    <button
      type="button"
      data-testid={`choice-${char.id}`}
      class="char-row"
      class:selected={selected.includes(char.id)}
      class:reduced={reducedMotion}
      animate:flip={{ duration: reducedMotion ? 0 : 300 }}
      on:click={(e) => select(char.id, e)}
      on:dblclick={() => !char.is_player && toggle(char.id)}
      on:pointerdown={(e) => !char.is_player && onPointerDown(char.id, e)}
      on:pointerup={onPointerUp}
      on:pointerleave={onPointerUp}
      on:introstart={(e) => onIntroStart(char.id, e)}
      on:introend={onIntroEnd}
      in:fly={{ x: -100, duration: reducedMotion ? 0 : 300 }}
      out:fly={{ x: 100, duration: reducedMotion ? 0 : 300 }}
      style={`border-color: ${getElementColor(char.element)}; --el-color: ${getElementColor(char.element)}; --sweep-delay: ${sweepDelay(char.id)}s; --sweep-duration: ${sweepDuration(char.id)}s;`}>
      <img src={char.img} alt={char.name} class="row-img" />
      <span class="row-name">{char.name}</span>
      <svelte:component
        this={getElementIcon(char.element)}
        class="row-type"
        style={`color: ${getElementColor(char.element)}`}
        aria-hidden="true" />
    </button>
  {/each}
  </div>
</div>
{/if}

<style>
.roster-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.roster-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0.4rem;
  color: #fff;
  font-size: 0.9rem;
}

.sort-controls {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

/* No explicit "Required" chip; the remove button conveys it. */

.sort-dir {
  background: transparent;
  border: 1px solid #555;
  color: #fff;
  border-radius: 4px;
  padding: 0 0.25rem;
  cursor: pointer;
}

/* Theme the sort dropdown similar to element picker */
.sort-controls label { color: #ddd; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem; }
.sort-controls select { background:#111; border:1px solid #555; color:#fff; padding:0.25rem 0.4rem; font-size:0.8rem; border-radius: 0; }
.sort-controls select:focus { outline: none; border-color: rgba(120,180,255,0.6); box-shadow: 0 0 0 2px rgba(120,180,255,0.2); }
.sort-dir { background:#111; border:1px solid #555; color:#fff; border-radius: 0; padding: 0.25rem 0.5rem; }
.sort-dir:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.5); }

.roster-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.4rem;
  height: 100%;
  overflow-y: auto;
  min-width: 0;
}

/* Inline divider for section separation */
.inline-divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent); margin: 0.3rem 0; }

.section-label {
  color: #ddd;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  opacity: 0.85;
  padding: 0.1rem 0.35rem;
}

.char-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.4rem;
  background: rgba(0,0,0,0.6);
  border: 2px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
  position: relative;
  overflow: hidden;
  z-index: 0; /* establish stacking context */
  /* Derived element colors for the sweep effect */
  --el-dark: color-mix(in srgb, var(--el-color) 20%, black 80%);
  --el-5darker: color-mix(in srgb, var(--el-color) 95%, black 5%);
  --el-5lighter: color-mix(in srgb, var(--el-color) 95%, white 5%);
}
.char-row:hover { background: rgba(20,20,20,0.8); }
.char-row.selected {
  border-color: #ffd700;
  box-shadow: 0 0 8px rgba(255,215,0,0.5);
}
/* Animated element-color sweep base (paused by default) */
.char-row::before {
  content: '';
  position: absolute;
  inset: 0;
  /* Dark edges use a darkened version of the element color.
     At 5% and 95%, slightly shift (±5%) to smooth the transition. */
  background: linear-gradient(
    90deg,
    var(--el-dark) 0%,
    var(--el-5darker) 25%,
    var(--el-color) 50%,
    var(--el-5lighter) 75%,
    var(--el-dark) 100%
  );
  background-size: 200% 100%;
  background-position: -100% 0;
  opacity: 0; /* hidden by default */
  filter: brightness(1.0); /* base tone under soft-light */
  mix-blend-mode: soft-light; /* subtle color without crushing contrast */
  animation: af-elm-sweep var(--sweep-duration, 12s) linear infinite;
  animation-play-state: paused; /* pause until selected */
  pointer-events: none;
  z-index: 0; /* sit beneath content */
  transition: opacity 280ms ease; /* fade-in when selected */
}

.char-row.selected::before {
  opacity: 0.82; /* brighter to make selection obvious */
  animation-play-state: running; /* start from beginning smoothly */
}

.char-row.selected.reduced::before {
  animation: none;
  opacity: 0.45; /* keep visible but calmer with reduced motion */
}

/* Sparkle trail when moving into party */
.char-row.sparkle::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 50%, var(--el-color) 40%, transparent 60%),
    radial-gradient(circle at 60% 30%, var(--el-color) 40%, transparent 60%),
    radial-gradient(circle at 80% 70%, var(--el-color) 40%, transparent 60%);
  opacity: 0.8;
  animation: sparkleTrail 400ms ease-out forwards;
  pointer-events: none;
}

@keyframes sparkleTrail {
  from { transform: translateX(-20px); opacity: 0.8; }
  to { transform: translateX(0); opacity: 0; }
}

@keyframes af-elm-sweep {
  0% { background-position: -100% 0; }
  100% { background-position: 100% 0; }
}

/* Ensure content renders above the animated sweep */
.row-img, .row-name, .row-type {
  position: relative;
  z-index: 1;
}
.row-img {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #222;
  flex-shrink: 0;
}
.row-name {
  flex: 1;
  text-align: left;
  color: #fff;
  font-size: 0.9rem;
}
.row-type { width: 20px; height: 20px; flex-shrink: 0; }

/* compact mode */
.roster.list.compact {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem;
  background: transparent;
  border: none;
  min-height: 32px;
  height: auto;
}
.roster.list.compact .char-btn {
  border: none;
  background: transparent;
  padding: 0;
  flex-shrink: 0;
}
.roster.list.compact .char-btn img {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  object-fit: cover;
  border: 1px solid #fff;
}
</style>
