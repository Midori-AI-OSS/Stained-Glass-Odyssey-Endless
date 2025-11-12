<script>
  import CardArt from '../CardArt.svelte';

  export let cards = [];
  export let select = () => {};
  export let selectedId = null;
  export let useConciseDescriptions = false;

  function resolveDescription(entry) {
    if (!entry || typeof entry !== 'object') return '';
    const full = typeof entry.full_about === 'string' ? entry.full_about : '';
    const concise = typeof entry.summarized_about === 'string' ? entry.summarized_about : '';
    return useConciseDescriptions ? (concise || full) : (full || concise);
  }
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
      <CardArt
        {entry}
        type="card"
        description={resolveDescription(entry)}
        fullDescription={entry.full_about}
        conciseDescription={entry.summarized_about}
      />
    </button>
  {/each}
</div>

<style>
  .cards-grid {
    display: grid;
    /* Pack tracks to the card width so there is no extra horizontal padding inside cells */
    grid-template-columns: repeat(auto-fill, 280px);
    column-gap: 4px;   /* slightly wider left-right gap */
    row-gap: 6px;      /* extra space below each card */
    align-items: start;
    justify-content: center; /* center whole grid within container */
    justify-items: start;     /* align items to left edge of their track */
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
