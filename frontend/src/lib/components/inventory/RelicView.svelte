<script>
  import CurioChoice from '../CurioChoice.svelte';
  export let relics = [];
  export let select = () => {};
</script>

<div class="relic-view">
  {#each relics as [id, qty]}
    <div class="relic-item" on:click={() => select(id, 'relic', qty)}>
      <CurioChoice id={id} />
      <span class="qty">{qty}</span>
    </div>
  {/each}
</div>
