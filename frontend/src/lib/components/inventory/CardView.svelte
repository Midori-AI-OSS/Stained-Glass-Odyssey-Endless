<script>
  import CardArt from '../CardArt.svelte';

  export let cards = [];
  export let select = () => {};
  export let selectedId = null;
</script>

<div class="cards-grid">
  {#each cards as [entry, qty]}
    <button
      type="button"
      class="card-cell"
      class:selected={selectedId === entry.id}
      on:click={() => select(entry.id, 'card', 1)}
      aria-label={entry.name}
    >
      <CardArt {entry} type="card" />
    </button>
  {/each}
</div>

<style>
  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.25rem;
    align-items: start;
    justify-items: center;
  }

  .card-cell {
    position: relative;
    padding: 0;
    border: none;
    background: none;
    cursor: pointer;
  }

  .card-cell.selected {
    outline: 2px solid rgba(120, 180, 255, 0.6);
    outline-offset: 2px;
  }

  /* Cards never stack; no qty badge here. */
</style>
