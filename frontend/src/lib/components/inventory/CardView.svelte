<script>
  import CardArt from '../CardArt.svelte';
  export let cards = [];
  export let select = () => {};
</script>

<div class="card-view">
  {#each cards as [id, qty]}
    <div class="card-item" on:click={() => select(id, 'card', qty)}>
      <CardArt id={id} stars={1} />
      <span class="qty">{qty}</span>
    </div>
  {/each}
</div>
