<script>
  export let damage = {};
</script>

<div class="damage-graphs">
  {#each Object.entries(damage) as [type, value]}
    <div class="damage-row">{type}: {value}</div>
  {/each}
</div>
