<script>
  import CardArt from './CardArt.svelte';
  import Tooltip from './Tooltip.svelte';
  import { createEventDispatcher } from 'svelte';
  import { selectionAnimationCssVariables } from '../constants/rewardAnimationTokens.js';
  import { rewardConfirmCssVariables } from '../constants/rewardConfirmTokens.js';
  export let entry = {};
  export let type = 'card';
  export let size = 'normal';
  export let quiet = false;
  export let fluid = false;
  export let selectionKey = '';
  export let selected = false;
  export let confirmable = false;
  export let confirmDisabled = false;
  export let confirmLabel = 'Confirm';
  export let reducedMotion = false;
  const dispatch = createEventDispatcher();
  // enable usage as a normal button too
  export let disabled = false;
  export let ariaLabel = '';
  $: label = ariaLabel || `Select ${type} ${entry?.name || entry?.id || ''}`;
  $: btnType = 'button';
  $: tabIndex = disabled ? -1 : 0;
  $: role = 'button';
  $: ariaDisabled = disabled ? 'true' : 'false';
  const selectionAnimationVars = selectionAnimationCssVariables();
  const selectionAnimationStyle = Object.entries(selectionAnimationVars)
    .map(([key, value]) => `${key}: ${value}`)
    .join('; ');
  const confirmButtonVars = rewardConfirmCssVariables();
  const confirmButtonStyle = Object.entries(confirmButtonVars)
    .map(([key, value]) => `${key}: ${value}`)
    .join('; ');

  function dispatchSelect() {
    dispatch('select', { type, id: entry?.id, entry, key: selectionKey });
  }

  function dispatchConfirm() {
    dispatch('confirm', { type, id: entry?.id, entry, key: selectionKey });
  }

  function handleClick() {
    if (disabled) return;
    if (confirmable && selected && !confirmDisabled) {
      dispatchConfirm();
      return;
    }
    dispatchSelect();
  }

  $: onKey = (e) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (confirmable && selected && !confirmDisabled) {
        dispatchConfirm();
        return;
      }
      dispatchSelect();
    }
  };
  $: noop = null;
  // end

</script>

{#if entry.tooltip || entry.about}
  <Tooltip text={entry.tooltip || entry.about}>
    <div
      class="card-shell"
      class:selected={selected}
      class:confirmable={confirmable}
      data-reduced-motion={reducedMotion ? 'true' : 'false'}
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
        <CardArt {entry} {type} {size} hideFallback={true} {quiet} {fluid} />
      </button>
      {#if confirmable}
        <button
          class="card-confirm reward-confirm-button"
          type="button"
          aria-label={`Confirm card ${entry?.name || entry?.id || 'selection'}`}
          data-reward-confirm="card"
          disabled={confirmDisabled}
          style={confirmButtonStyle}
          on:click={() => {
            if (!confirmDisabled) dispatchConfirm();
          }}
        >
          {confirmLabel}
        </button>
      {/if}
    </div>
  </Tooltip>
{:else}
  <div
    class="card-shell"
    class:selected={selected}
    class:confirmable={confirmable}
    data-reduced-motion={reducedMotion ? 'true' : 'false'}
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
      <CardArt {entry} {type} {size} hideFallback={true} {quiet} {fluid} />
    </button>
    {#if confirmable}
      <button
        class="card-confirm reward-confirm-button"
        type="button"
        aria-label={`Confirm card ${entry?.name || entry?.id || 'selection'}`}
        data-reward-confirm="card"
        disabled={confirmDisabled}
        style={confirmButtonStyle}
        on:click={() => {
          if (!confirmDisabled) dispatchConfirm();
        }}
      >
        {confirmLabel}
      </button>
    {/if}
  </div>
{/if}

<style>
  @import '../styles/reward-confirm.css';

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

  .card-shell.confirmable .card-confirm {
    display: inline-flex;
  }

  @keyframes reward-selection-wiggle {
    0% {
      transform: scale(1) rotate(0deg);
    }
    16% {
      transform: scale(var(--reward-selection-wiggle-scale-max))
        rotate(var(--reward-selection-wiggle-rotation));
    }
    34% {
      transform: scale(var(--reward-selection-wiggle-scale-min))
        rotate(calc(var(--reward-selection-wiggle-rotation) * -1));
    }
    52% {
      transform: scale(var(--reward-selection-wiggle-scale-max))
        rotate(var(--reward-selection-wiggle-rotation));
    }
    70% {
      transform: scale(1) rotate(0deg);
    }
    100% {
      transform: scale(1) rotate(0deg);
    }
  }

  .card-shell.confirmable.selected[data-reduced-motion='false'] :global(.card-art) {
    animation: reward-selection-wiggle var(--reward-selection-wiggle-duration)
      ease-in-out infinite;
  }

  .card-shell[data-reduced-motion='true'] :global(.card-art) {
    animation: none;
  }

  .card-confirm {
    display: none;
  }
  /* Tooltip visuals are provided by Tooltip.svelte + settings-shared.css */
</style>
