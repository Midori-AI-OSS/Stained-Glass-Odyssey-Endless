<script>
  import CurioChoice from '../CurioChoice.svelte';
  export let relics = [];
  export let select = () => {};
</script>

<div class="relic-view">
  {#each relics as [entry, qty]}
    <div class="relic-item" on:click={() => select(entry.id, 'relic', qty)}>
      <CurioChoice entry={entry} />
      <span class="qty">{qty}</span>
    </div>
  {/each}
</div>
