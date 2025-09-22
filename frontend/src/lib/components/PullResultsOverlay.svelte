<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { crossfade } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { createDealSfx } from '../systems/sfx.js';
  import CurioChoice from './CurioChoice.svelte';
  import { getRewardArt } from '../systems/rewardLoader.js';
  import { getCharacterImage } from '../systems/assetLoader.js';
  import { formatName } from '../systems/craftingUtils.js';

  export let results = [];
  export let sfxVolume = 5;
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();
  let stack = [];
  let visible = [];
  let isBatch = false;
  let dealSfx;

  const [send, receive] = crossfade({
    duration: () => (reducedMotion ? 0 : 400),
    easing: cubicOut
  });

  // Create a stable render object with fixed key and initial stack index
  function toRenderable(r, index) {
    if (!r || typeof r !== 'object') return r;
    if (r.type === 'character') {
      const id = String(r.id || '');
      const stars = Number(r.rarity || 5) || 5;
      const stacks = Number(r.stacks || 0) || 0;
      const about = stacks > 1 ? `Duplicate +${stacks - 1}` : 'New character';
      return {
        id,
        name: id,
        stars,
        about,
        artUrl: getCharacterImage(id),
        _key: `${id}:${index}`,
        _stackIndex: index
      };
    }
    if (r.type === 'item') {
      const key = String(r.id || '');
      const stars = Number(r.rarity || 1) || 1;
      const normalized = key.replace('_', '');
      const artUrl = getRewardArt('item', normalized);
      return {
        id: key,
        name: formatName(key),
        stars,
        about: 'Upgrade material',
        artUrl,
        _key: `${key}:${index}`,
        _stackIndex: index
      };
    }
    return r;
  }

  onMount(() => {
    const mapped = Array.isArray(results) ? results.map((r, i) => toRenderable(r, i)) : [];
    isBatch = mapped.length === 5 || mapped.length === 10;
    if (isBatch) {
      stack = mapped;
      if (!reducedMotion) {
        dealSfx = createDealSfx(sfxVolume);
      }
      dealNext();
    } else {
      visible = mapped;
    }
  });

  function playDeal() {
    if (reducedMotion || !dealSfx) return;
    try {
      const node = dealSfx.paused ? dealSfx : dealSfx.cloneNode(true);
      if (node === dealSfx) {
        dealSfx.currentTime = 0;
      } else {
        node.volume = dealSfx.volume;
      }
      node
        .play()
        .catch((error) => {
          if (error?.name === 'AbortError') {
            console.debug('PullResultsOverlay: playback aborted');
          } else {
            console.debug('PullResultsOverlay: playback failed', error);
          }
        });
    } catch {}
  }

  function dealNext() {
    if (stack.length === 0) return;
    // Move the next card from the stack to the visible grid
    visible = [...visible, stack[0]];
    stack = stack.slice(1);
    playDeal();
    if (stack.length > 0) {
      setTimeout(dealNext, reducedMotion ? 0 : 400);
    }
  }

  function close() {
    dispatch('close');
  }
</script>

<div class="layout">
  {#if isBatch}
    <div class="stack" aria-hidden={stack.length === 0}>
      {#each stack as r (r._key)}
        <div class="card" style={`--pos: ${r._stackIndex}`} out:send={{ key: r._key }}>
          <CurioChoice entry={r} disabled={true} />
        </div>
      {/each}
    </div>
  {/if}
  <div class="choices">
    {#each visible as r (r._key)}
      <div class="card" in:receive={{ key: r._key }}>
        <CurioChoice entry={r} disabled={true} />
      </div>
    {/each}
  </div>
  {#if stack.length === 0 && visible.length}
    <button class="done" on:click={close}>Done</button>
  {/if}
</div>

<style>
  .layout {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }
  .choices {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    justify-content: center;
    position: relative;
    z-index: 2;
  }
  .stack {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    z-index: 1;
  }
  .stack .card {
    position: absolute;
    transform: translate(calc(var(--pos) * 4px), calc(var(--pos) * 4px));
    pointer-events: none; /* avoid covering buttons during animation */
  }
  .done {
    padding: 0.5rem 1rem;
    background: #0a0a0a;
    color: #fff;
    border: 2px solid #fff;
    cursor: pointer;
    position: relative;
    z-index: 10; /* ensure visible over any lingering animations */
  }
</style>
