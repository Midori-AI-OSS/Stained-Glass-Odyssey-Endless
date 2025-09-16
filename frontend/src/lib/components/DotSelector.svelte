<script>
  import { createEventDispatcher, onMount } from 'svelte';
  export let value = 50;
  export let includeZero = true;
  export let zeroAriaLabel = 'Mute';
  export let zeroContent = '✕';
  const defaultStepAriaLabel = (index) => `${(index + 1) * 10}%`;
  export let formatStepAriaLabel = defaultStepAriaLabel;
  const dispatch = createEventDispatcher();

  let wrapEl;
  let arrowX = 0; // center position in px relative to wrapper

  const select = (v) => {
    const numeric = Number(v);
    const clamped = Number.isFinite(numeric) ? Math.min(100, Math.max(0, Math.round(numeric))) : 0;
    value = clamped;
    dispatch('change', clamped);
  };

  function updateArrow() {
    if (!wrapEl) return;
    const buttons = wrapEl.querySelectorAll('.dot-selector button[data-dot]');
    if (!buttons || !buttons.length) return;
    const numericValue = Number.isFinite(Number(value)) ? Number(value) : 0;
    let target = null;
    let smallestDiff = Infinity;
    for (const button of buttons) {
      const dotValue = Number(button.dataset.dot || '0');
      const diff = Math.abs(dotValue - numericValue);
      if (!target || diff < smallestDiff || (diff === smallestDiff && dotValue > Number(target.dataset.dot || '0'))) {
        target = button;
        smallestDiff = diff;
      }
    }
    if (!target) return;
    const wrapRect = wrapEl.getBoundingClientRect();
    const rect = target.getBoundingClientRect();
    arrowX = rect.left - wrapRect.left + rect.width / 2;
  }

  onMount(() => {
    updateArrow();
    const ro = new ResizeObserver(() => updateArrow());
    try { ro.observe(wrapEl); } catch {}
    const onResize = () => updateArrow();
    window.addEventListener('resize', onResize);
    return () => {
      try { ro.disconnect(); } catch {}
      window.removeEventListener('resize', onResize);
    };
  });

  $: value, updateArrow();
</script>

<div class="dot-selector-wrap" bind:this={wrapEl}>
  <div class="dot-arrow" style={`transform: translateX(${arrowX}px) translateX(-50%)`}/>
  <div class="dot-selector">
    {#if includeZero}
      <button
        type="button"
        class="mute"
        class:selected={Number(value) <= 0}
        aria-label={zeroAriaLabel}
        data-dot="0"
        on:click={() => select(0)}
      >
        {zeroContent}
      </button>
    {/if}
    <div class="dot-steps">
      {#each Array(10) as _, i}
        <button
          type="button"
          class:selected={Number(value) >= (i + 0.5) * 10}
          aria-label={formatStepAriaLabel ? formatStepAriaLabel(i) : defaultStepAriaLabel(i)}
          data-dot={(i + 1) * 10}
          on:click={() => select((i + 1) * 10)}
        />
      {/each}
    </div>
  </div>

</div>

<style>
  .dot-selector-wrap {
    position: relative;
    display: block;
    width: 100%;
  }
  .dot-arrow {
    position: absolute;
    top: calc(100% + 0.2rem); /* arrow sits under dots */
    width: 0;
    height: 0;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-bottom: 8px solid rgba(255, 255, 255, 0.9); /* pointing up */
    transition: transform 200ms ease;
    pointer-events: none;
  }
  .dot-selector {
    display: flex;
    width: 100%;
    gap: 0.5rem; /* small gap between mute and steps */
    align-items: center;
    min-width: 0;
  }
  .dot-steps {
    display: flex;
    align-items: center;
    justify-content: space-between; /* spread dots to fill available space */
    flex: 1 1 auto;
    min-width: 0;
  }
  .dot-selector button {
    -webkit-appearance: none;
    appearance: none;
    box-sizing: border-box;
    padding: 0 !important; /* override shared settings button padding */
    line-height: 0;
    font-size: 0;
    flex: 0 0 auto;
    width: 0.6rem;
    height: 0.6rem; /* explicit height to ensure perfect circle */
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.55);
    background: rgba(255, 255, 255, 0.18);
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
    display: inline-block;
    vertical-align: middle;
    color: rgba(255, 255, 255, 0.9);
  }
  .dot-selector button.mute {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.55rem; /* show the X */
    line-height: 0;
    width: 0.6rem;
    height: 0.6rem;
    border-radius: 50%;
    padding: 0 !important;
    border-width: 1px;
  }
  .dot-selector button.selected {
    background: #fff;
    color: #000;
    border-color: #fff;
  }
</style>
