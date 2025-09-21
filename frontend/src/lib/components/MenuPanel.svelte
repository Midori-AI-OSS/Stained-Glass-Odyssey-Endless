<script>
  import ElementOrbs from './ElementOrbs.svelte';
  export let padding = '0.5rem';
  export let reducedMotion = false;
  export let starColor = '';
  export let style = '';
  export let animationSpeed = 1; // Animation speed from settings
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
>
  <ElementOrbs color={starColor} {reducedMotion} {animationSpeed} />
  <slot />
</div>
