<script>
  import RewardCard from '../RewardCard.svelte';
  import CurioChoice from '../CurioChoice.svelte';
  import { createEventDispatcher } from 'svelte';
  export let cards = [];
  export let relics = [];
  const dispatch = createEventDispatcher();
  function forward(e) {
    dispatch('select', e.detail);
  }
</script>

<div class="reward-list">
  {#if cards.length}
    <div class="cards">
      {#each cards as card}
        <RewardCard entry={card} on:select={forward} />
      {/each}
    </div>
  {/if}
  {#if relics.length}
    <div class="relics">
      {#each relics as relic}
        <CurioChoice entry={relic} on:select={forward} />
      {/each}
    </div>
  {/if}
</div>
