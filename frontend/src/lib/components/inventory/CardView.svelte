<script>
  import CardArt from '../CardArt.svelte';
  export let cards = [];
  export let select = () => {};
</script>

<div class="card-view">
  {#each cards as [entry, qty]}
    <div class="card-item" on:click={() => select(entry.id, 'card', qty)}>
      <CardArt {entry} type="card" />
      <span class="qty">{qty}</span>
    </div>
  {/each}
</div>
