<script>
  import { createEventDispatcher } from 'svelte';
  import OverlaySurface from './OverlaySurface.svelte';
  import MenuPanel from './MenuPanel.svelte';

  const dispatch = createEventDispatcher();

  export let title = '';
  export let padding = '0.5rem';
  // Constrain popup size (useful for reward overlay)
  export let maxWidth = '820px';
  export let maxHeight = '85vh';
  export let zIndex = 1000;
  export let bareSurface = false;
  export let surfaceNoScroll = false;
  export let reducedMotion = false;

  function close() {
    dispatch('close');
  }

  function popupBounceOut(node, options = {}) {
    const { reducedMotion: motionDisabled = false } = options;

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (motionDisabled || prefersReducedMotion) {
      return {
        duration: 0
      };
    }

    const duration = 210;
    const overshoot = 0.02;
    const liftPhase = 0.65;

    return {
      duration,
      css: (_t, u) => {
        const progress = Math.min(1, Math.max(0, u));
        let scale = 1;

        if (progress < liftPhase) {
          const liftProgress = liftPhase === 0 ? 1 : progress / liftPhase;
          scale = 1 + overshoot * liftProgress;
        } else {
          const settleRange = Math.max(0.0001, 1 - liftPhase);
          const settleProgress = (progress - liftPhase) / settleRange;
          scale = 1 + overshoot * (1 - settleProgress);
        }

        const opacity = 1 - progress;
        return `transform: scale(${scale}); opacity: ${opacity};`;
      }
    };
  }
</script>

{#if bareSurface}
  <div
    class="box"
    class:motion-enabled={!reducedMotion}
    out:popupBounceOut={{ reducedMotion }}
    style={`--max-w: ${maxWidth}; --max-h: ${maxHeight}` }
  >
    <div class="inner">
      <div class="content-wrap">
        <MenuPanel class="panel-body" {padding} {reducedMotion}>
          {#if title}
            <header class="head">
              <h3>{title}</h3>
              <button class="mini" title="Close" on:click={close}>✕</button>
            </header>
          {/if}
          <slot />
        </MenuPanel>
        <div class="panel-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </div>
{:else}
  <OverlaySurface {zIndex} noScroll={surfaceNoScroll}>
    <div
      class="box"
      class:motion-enabled={!reducedMotion}
      out:popupBounceOut={{ reducedMotion }}
      style={`--max-w: ${maxWidth}; --max-h: ${maxHeight}` }
    >
      <div class="inner">
        <div class="content-wrap">
          <MenuPanel class="panel-body" {padding} {reducedMotion}>
            {#if title}
              <header class="head">
                <h3>{title}</h3>
                <button class="mini" title="Close" on:click={close}>✕</button>
              </header>
            {/if}
            <slot />
          </MenuPanel>
          <div class="panel-footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </div>
  </OverlaySurface>
{/if}

<style>
  .head {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .head h3 {
    margin: 0;
    font-size: 1rem;
  }

  .head .mini {
    margin-left: auto;
  }

  .mini {
    border: 1px solid #fff;
    background: #111;
    color: #fff;
    font-size: 0.7rem;
    padding: 0.25rem 0.45rem;
    cursor: pointer;
  }

  .box {
    /* center within overlay */
    margin: auto;
    width: min(var(--max-w), 90%);
    /* Let height shrink to fit content, but cap it */
    max-height: var(--max-h);
    /* Contain layout; inner body scrolls */
    overflow: hidden;
    display: flex;
    flex-direction: column;
    /* allow children to shrink and scroll within */
    min-height: 0;
    transform-origin: center;
  }

  .box.motion-enabled {
    animation: popup-bounce-in 210ms ease-out both;
  }

  @media (prefers-reduced-motion: reduce) {
    .box.motion-enabled {
      animation: none;
    }
  }

  @keyframes popup-bounce-in {
    0% {
      transform: scale(0.92);
      opacity: 0;
    }
    65% {
      transform: scale(1.02);
      opacity: 1;
    }
    100% {
      transform: scale(1);
      opacity: 1;
    }
  }

  .inner { display: flex; flex-direction: column; min-height: 0; }

  .content-wrap { display: flex; flex-direction: column; min-height: 0; }

  /* Scroll the body, keep footer visible */
  .panel-body { flex: 1 1 auto; min-height: 0; overflow: auto; }
  .panel-footer { flex: 0 0 auto; }
</style>
