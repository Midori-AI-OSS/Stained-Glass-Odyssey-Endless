<script>
  export let foes = [];
</script>

<div class="foe-view">
  {#each foes as foe}
    <div class="foe-member">{foe.name}</div>
  {/each}
</div>
