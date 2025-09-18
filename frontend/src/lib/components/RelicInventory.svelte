<script>
  import MenuPanel from './MenuPanel.svelte';
  import Tooltip from './Tooltip.svelte';
  export let relics = [];
</script>

<MenuPanel>
  <h3>Relic Inventory</h3>
  {#if relics.length === 0}
    <p>No relics collected yet.</p>
  {:else}
    <ul class="relics">
      {#each relics as relic}
        <li class="relic">
          <Tooltip text={relic.about || ''}>
            <span>{relic.name} x{relic.stacks}</span>
          </Tooltip>
        </li>
      {/each}
    </ul>
  {/if}
</MenuPanel>

<style>
  .relics {
    list-style: none;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .relic {
    border: 2px solid #fff;
    padding: 0.5rem;
    background: #111;
    color: #fff;
  }
</style>
