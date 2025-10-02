<script>
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { onDestroy } from 'svelte';
  import { browser } from '$app/environment';

  import StarStorm from './StarStorm.svelte';
  export let padding = '0.5rem';
  export let reducedMotion;
  export let starColor = '';
  export let style = '';

  const TRANSITION_DURATION = 220;

  let prefersReducedMotion = false;

  if (browser) {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const updatePreference = (event) => {
      prefersReducedMotion = event.matches;
    };

    updatePreference(mediaQuery);

    mediaQuery.addEventListener?.('change', updatePreference);
    mediaQuery.addListener?.(updatePreference);

    onDestroy(() => {
      mediaQuery.removeEventListener?.('change', updatePreference);
      mediaQuery.removeListener?.(updatePreference);
    });
  }

  $: shouldReduceMotion = reducedMotion ?? prefersReducedMotion;

  $: flyInOptions = shouldReduceMotion
    ? { duration: 0 }
    : { y: -12, duration: TRANSITION_DURATION, easing: cubicOut };

  $: flyOutOptions = shouldReduceMotion
    ? { duration: 0 }
    : { y: 12, duration: TRANSITION_DURATION, easing: cubicOut };

  $: fadeOptions = shouldReduceMotion
    ? { duration: 0 }
    : { duration: TRANSITION_DURATION, easing: cubicOut };
</script>

<style>
  .panel {
    position: relative;
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: 100%;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    padding: var(--padding);
    overflow-y: auto;
    overflow-x: hidden;
    /* Slightly lighten the stained-glass background for better readability */
    background: linear-gradient(0deg, rgba(255,255,255,0.06), rgba(255,255,255,0.06)), var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
  }

  /* Themed scrollbars for dark UI */
  .panel {
    scrollbar-width: thin;
    scrollbar-color: rgba(190, 190, 200, 0.6) rgba(50, 50, 60, 0.35);
  }
  .panel::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }
  .panel::-webkit-scrollbar-track {
    background: rgba(50, 50, 60, 0.35);
    border-radius: 8px;
  }
  .panel::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, rgba(200, 200, 210, 0.55), rgba(160, 160, 175, 0.55));
    border-radius: 8px;
    border: 2px solid rgba(0, 0, 0, 0.2);
  }
  .panel::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, rgba(215, 215, 225, 0.7), rgba(175, 175, 190, 0.7));
  }
</style>

<div
  {...$$restProps}
  class={`panel ${$$props.class || ''}`}
  style={`--padding: ${padding}; ${style}`}
  in:fly={flyInOptions}
  in:fade={fadeOptions}
  out:fly={flyOutOptions}
  out:fade={fadeOptions}
>
  <StarStorm color={starColor} reducedMotion={shouldReduceMotion} />
  <slot />
</div>
