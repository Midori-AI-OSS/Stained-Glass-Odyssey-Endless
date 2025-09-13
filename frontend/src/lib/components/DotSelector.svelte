<script>
  import { createEventDispatcher } from 'svelte';
  export let value = 50;
  const dispatch = createEventDispatcher();

  const select = (v) => {
    value = v;
    dispatch('change', v);
  };
</script>

<div class="dot-selector">
  <button
    type="button"
    class="mute"
    class:selected={value === 0}
    aria-label="Mute"
    on:click={() => select(0)}
  >
    ✕
  </button>
  {#each Array(10) as _, i}
    <button
      type="button"
      class:selected={value >= (i + 1) * 10}
      aria-label={(i + 1) * 10 + '%'}
      on:click={() => select((i + 1) * 10)}
    />
  {/each}
</div>

<style>
  .dot-selector {
    display: flex;
    gap: 0.3rem;
  }
  .dot-selector button {
    width: 0.6rem;
    height: 0.6rem;
    border-radius: 50%;
    border: none;
    background: rgba(255, 255, 255, 0.3);
    cursor: pointer;
    transition: background 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .dot-selector button.mute {
    font-size: 0.5rem;
    color: rgba(255, 255, 255, 0.9);
  }
  .dot-selector button.selected {
    background: #fff;
    color: #000;
  }
</style>
