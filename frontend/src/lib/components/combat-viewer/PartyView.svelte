<script>
  export let party = [];
</script>

<div class="party-view">
  {#each party as member}
    <div class="party-member">{member.name}</div>
  {/each}
</div>
