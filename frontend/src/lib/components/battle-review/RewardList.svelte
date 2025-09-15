<script>
  import RewardCard from '../RewardCard.svelte';
  import CurioChoice from '../CurioChoice.svelte';
  export let cards = [];
  export let relics = [];
</script>

<div class="reward-list">
  {#if cards.length}
    <div class="cards">
      {#each cards as card}
        <RewardCard {card} />
      {/each}
    </div>
  {/if}
  {#if relics.length}
    <div class="relics">
      {#each relics as relic}
        <CurioChoice {relic} />
      {/each}
    </div>
  {/if}
</div>
