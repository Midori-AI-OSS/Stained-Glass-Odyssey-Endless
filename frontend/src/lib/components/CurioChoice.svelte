<script>
  import CardArt from './CardArt.svelte';
  import Tooltip from './Tooltip.svelte';
  import { createEventDispatcher } from 'svelte';
  export let entry = {};
  export let size = 'normal';
  export let quiet = false;
  export let compact = false;
  const dispatch = createEventDispatcher();
  function handleClick() {
    dispatch('select', { type: 'relic', id: entry?.id, entry });
  }
  export let disabled = false;
  $: tabIndex = disabled ? -1 : 0;
  $: ariaDisabled = disabled ? 'true' : 'false';
  $: onKey = (e) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };
</script>

{#if !compact && (entry.tooltip || entry.about)}
  <Tooltip text={entry.tooltip || entry.about}>
    <button class="curio" aria-label={`Select relic ${entry.name || entry.id}`} {tabIndex} aria-disabled={ariaDisabled} on:click={handleClick} on:keydown={onKey}>
      <CardArt {entry} type="relic" roundIcon={true} {size} {quiet} {compact} />
    </button>
  </Tooltip>
{:else}
  <button class="curio" aria-label={`Select relic ${entry.name || entry.id}`} {tabIndex} aria-disabled={ariaDisabled} on:click={handleClick} on:keydown={onKey}>
    <CardArt {entry} type="relic" roundIcon={true} {size} {quiet} {compact} />
  </button>
{/if}

<style>
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
  /* Tooltip visuals are provided by Tooltip.svelte + settings-shared.css */
  .select-bar {
    position: absolute;
    left: 0;
    right: 0;
    bottom: -10px;
    margin: 0 auto;
    width: 80%;
    text-align: center;
    color: #fff;
    background: rgba(120,180,255,0.22);
    border: 1px solid rgba(255,255,255,0.18);
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    backdrop-filter: blur(4px);
    pointer-events: none;
  }
</style>
