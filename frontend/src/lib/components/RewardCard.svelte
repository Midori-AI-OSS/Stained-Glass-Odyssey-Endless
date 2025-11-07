<script>
  import CardArt from './CardArt.svelte';
  import Tooltip from './Tooltip.svelte';
  import { createEventDispatcher } from 'svelte';
  import { selectionAnimationCssVariables } from '../constants/rewardAnimationTokens.js';
  export let entry = {};
  export let type = 'card';
  export let size = 'normal';
  export let quiet = false;
  export let fluid = false;
  export let selectionKey = '';
  export let selected = false;
  export let reducedMotion = false;
  export let fullDescription = '';
  export let conciseDescription = '';
  export let description = '';
  export let tooltip = '';
  export let useConciseDescriptions = false;
  export let descriptionModeLabel = '';
  const dispatch = createEventDispatcher();
  // enable usage as a normal button too
  export let disabled = false;
  export let ariaLabel = '';
  $: label = ariaLabel || `Select ${type} ${entry?.name || entry?.id || ''}`;
  $: btnType = 'button';
  $: tabIndex = disabled ? -1 : 0;
  $: role = 'button';
  $: ariaDisabled = disabled ? 'true' : 'false';
  $: descriptionMode = descriptionModeLabel || (useConciseDescriptions ? 'Concise descriptions' : 'Full descriptions');
  $: resolvedDescription = (() => {
    if (description && String(description).trim()) {
      return String(description).trim();
    }
    if (useConciseDescriptions) {
      return (conciseDescription && String(conciseDescription).trim()) || (fullDescription && String(fullDescription).trim()) || '';
    }
    return (fullDescription && String(fullDescription).trim()) || (conciseDescription && String(conciseDescription).trim()) || '';
  })();
  $: tooltipText = (() => {
    const explicit = tooltip || entry?.tooltip;
    if (explicit) {
      return explicit;
    }
    if (!resolvedDescription) {
      return '';
    }
    return descriptionMode ? `${resolvedDescription} — ${descriptionMode}` : resolvedDescription;
  })();
  $: descriptionModeToken = useConciseDescriptions ? 'concise' : 'full';
  const selectionAnimationVars = selectionAnimationCssVariables();
  const selectionAnimationStyle = Object.entries(selectionAnimationVars)
    .map(([key, value]) => `${key}: ${value}`)
    .join('; ');

  function dispatchSelect() {
    dispatch('select', { type, id: entry?.id, entry, key: selectionKey });
  }

  function handleClick() {
    if (disabled) return;
    dispatchSelect();
  }

  $: onKey = (e) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      dispatchSelect();
    }
  };
  $: noop = null;
  // end

</script>

{#if tooltipText}
  <Tooltip text={tooltipText}>
    <div
      class="card-shell"
      class:selected={selected}
      data-reduced-motion={reducedMotion ? 'true' : 'false'}
      data-description-mode={descriptionModeToken}
      style={selectionAnimationStyle}
    >
      <button
        class="card"
        type={btnType}
        aria-label={label}
        aria-disabled={ariaDisabled}
        aria-pressed={selected ? 'true' : 'false'}
        {tabIndex}
        role={role}
        on:click={handleClick}
        on:keydown={onKey}
      >
        <CardArt
          {entry}
          {type}
          {size}
          hideFallback={true}
          {quiet}
          {fluid}
          description={resolvedDescription}
          fullDescription={fullDescription}
          conciseDescription={conciseDescription}
        />
      </button>
    </div>
  </Tooltip>
{:else}
  <div
    class="card-shell"
    class:selected={selected}
    data-reduced-motion={reducedMotion ? 'true' : 'false'}
    data-description-mode={descriptionModeToken}
    style={selectionAnimationStyle}
  >
    <button
      class="card"
      type={btnType}
      aria-label={label}
      aria-disabled={ariaDisabled}
      aria-pressed={selected ? 'true' : 'false'}
      {tabIndex}
      role={role}
      on:click={handleClick}
      on:keydown={onKey}
    >
      <CardArt
        {entry}
        {type}
        {size}
        hideFallback={true}
        {quiet}
        {fluid}
        description={resolvedDescription}
        fullDescription={fullDescription}
        conciseDescription={conciseDescription}
      />
    </button>
  </div>
{/if}

<style>
  .card-shell {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.65rem;
    padding-bottom: 0.35rem;
    transition: transform 120ms ease, filter 120ms ease;
  }

  .card-shell[data-reduced-motion='true'] {
    transition: none;
  }

  .card {
    position: relative;
    padding: 0;
    border: none;
    background: none;
    cursor: pointer;
    filter: drop-shadow(0 2px 6px rgba(0,0,0,0.35));
    transition: transform 120ms ease, filter 120ms ease;
  }
  .card:hover,
  .card:focus-visible {
    transform: translateY(-2px);
    filter: drop-shadow(0 6px 14px rgba(0,0,0,0.45));
    outline: none;
  }
  .card-shell.selected .card {
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

  .card-shell.selected[data-reduced-motion='false'] :global(.card-art) {
    transform-origin: center;
    animation: reward-selection-wiggle var(--reward-selection-wiggle-duration)
      ease-in-out infinite;
  }

  .card-shell[data-reduced-motion='true'] :global(.card-art) {
    animation: none;
  }

  /* Tooltip visuals are provided by Tooltip.svelte + settings-shared.css */
</style>
