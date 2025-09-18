<script>
  import CardArt from './CardArt.svelte';
  import Tooltip from './Tooltip.svelte';
  import { createEventDispatcher } from 'svelte';
  export let entry = {};
  export let type = 'card';
  export let size = 'normal';
  export let quiet = false;
  const dispatch = createEventDispatcher();
  function handleClick() {
    dispatch('select', { type, id: entry?.id, entry });
  }
  // enable usage as a normal button too
  export let disabled = false;
  export let ariaLabel = '';
  $: label = ariaLabel || `Select ${type} ${entry?.name || entry?.id || ''}`;
  $: btnType = 'button';
  $: tabIndex = disabled ? -1 : 0;
  $: role = 'button';
  $: ariaDisabled = disabled ? 'true' : 'false';
  $: onKey = (e) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };
  $: noop = null;
  // end
  
</script>

{#if entry.tooltip || entry.about}
  <Tooltip text={entry.tooltip || entry.about}>
    <button class="card" type={btnType} aria-label={label} {tabIndex} role={role} aria-disabled={ariaDisabled} on:click={handleClick} on:keydown={onKey}>
      <CardArt {entry} {type} {size} hideFallback={true} {quiet} />
    </button>
  </Tooltip>
{:else}
  <button class="card" type={btnType} aria-label={label} {tabIndex} role={role} aria-disabled={ariaDisabled} on:click={handleClick} on:keydown={onKey}>
    <CardArt {entry} {type} {size} hideFallback={true} {quiet} />
  </button>
{/if}

<style>
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
  /* Tooltip visuals are provided by Tooltip.svelte + settings-shared.css */
</style>
