<script>
  import CardArt from './CardArt.svelte';
  import Tooltip from './Tooltip.svelte';
  import { createEventDispatcher } from 'svelte';
  import { selectionAnimationCssVariables } from '../constants/rewardAnimationTokens.js';

  export let entry = {};
  export let size = 'normal';
  export let quiet = false;
  export let compact = false;
  export let fluid = false;
  export let selectionKey = '';
  export let selected = false;
  export let reducedMotion = false;
  export let disabled = false;

  const dispatch = createEventDispatcher();

  const selectionAnimationVars = selectionAnimationCssVariables();
  const selectionAnimationStyle = Object.entries(selectionAnimationVars)
    .map(([key, value]) => `${key}: ${value}`)
    .join('; ');
  function dispatchSelect() {
    dispatch('select', { type: 'relic', id: entry?.id, entry, key: selectionKey });
  }

  function handleClick() {
    if (disabled) return;
    dispatchSelect();
  }

  $: tabIndex = disabled ? -1 : 0;
  $: ariaDisabled = disabled ? 'true' : 'false';
  $: onKey = (e) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      dispatchSelect();
    }
  };
</script>

{#if !compact && (entry.tooltip || entry.about)}
  <Tooltip text={entry.tooltip || entry.about}>
    <div
      class="curio-shell"
      class:selected={selected}
      data-reduced-motion={reducedMotion ? 'true' : 'false'}
      style={selectionAnimationStyle}
    >
      <button
        class="curio"
        aria-label={`Select relic ${entry.name || entry.id}`}
        {tabIndex}
        aria-disabled={ariaDisabled}
        data-reward-relic="true"
        data-selection-key={selectionKey}
        on:click={handleClick}
        on:keydown={onKey}
      >
        <CardArt
          {entry}
          type="relic"
          roundIcon={true}
          {size}
          {quiet}
          {compact}
          {fluid}
        />
      </button>
    </div>
  </Tooltip>
{:else}
  <div
    class="curio-shell"
    class:selected={selected}
    data-reduced-motion={reducedMotion ? 'true' : 'false'}
    style={selectionAnimationStyle}
  >
    <button
      class="curio"
      aria-label={`Select relic ${entry.name || entry.id}`}
      {tabIndex}
      aria-disabled={ariaDisabled}
      data-reward-relic="true"
      data-selection-key={selectionKey}
      on:click={handleClick}
      on:keydown={onKey}
    >
      <CardArt {entry} type="relic" roundIcon={true} {size} {quiet} {compact} {fluid} />
    </button>
  </div>
{/if}

<style>
  
  .curio-shell {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.55rem;
    padding-bottom: 0.25rem;
    transition: transform 120ms ease, filter 120ms ease;
  }

  .curio-shell[data-reduced-motion='true'] {
    transition: none;
  }

  .curio {
    position: relative;
    padding: 0;
    border: none;
    background: none;
    cursor: pointer;
    filter: drop-shadow(0 2px 6px rgba(0,0,0,0.35));
    transition: transform 120ms ease, filter 120ms ease;
  }

  .curio:hover,
  .curio:focus-visible {
    transform: translateY(-2px) scale(1.02);
    filter: drop-shadow(0 6px 14px rgba(0,0,0,0.45));
    outline: none;
  }

  .curio-shell.selected .curio {
    filter: drop-shadow(0 8px 18px rgba(20, 80, 160, 0.55));
  }

  @keyframes reward-selection-wiggle {
    0%,
    100% {
      transform: translate3d(0, 0, 0) rotate(0deg);
    }
    10%,
    30%,
    50% {
      transform: translate3d(var(--reward-selection-wiggle-translate), 0, 0)
        rotate(var(--reward-selection-wiggle-rotation));
    }
    20%,
    40%,
    60% {
      transform: translate3d(calc(var(--reward-selection-wiggle-translate) * -1), 0, 0)
        rotate(calc(var(--reward-selection-wiggle-rotation) * -1));
    }
    70%,
    80%,
    90% {
      transform: translate3d(0, 0, 0) rotate(0deg);
    }
  }

  .curio-shell.selected[data-reduced-motion='false'] :global(.card-art) {
    transform-origin: center;
    animation: reward-selection-wiggle var(--reward-selection-wiggle-duration) ease-in-out infinite;
  }

  .curio-shell[data-reduced-motion='true'] :global(.card-art) {
    animation: none;
  }

  /* Tooltip visuals are provided by Tooltip.svelte + settings-shared.css */
</style>
