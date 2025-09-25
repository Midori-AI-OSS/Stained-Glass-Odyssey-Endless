<script>
  import RewardCard from '../RewardCard.svelte';
  import CurioChoice from '../CurioChoice.svelte';
  import { createEventDispatcher, getContext } from 'svelte';
  import { BATTLE_REVIEW_CONTEXT_KEY } from '../../systems/battleReview/state.js';
  export let cards = [];
  export let relics = [];
  const dispatch = createEventDispatcher();
  const reviewContext = getContext(BATTLE_REVIEW_CONTEXT_KEY);
  const dispatchSelect = reviewContext?.dispatchSelect;
  function forward(e) {
    dispatch('select', e.detail);
    if (dispatchSelect) {
      dispatchSelect(e.detail);
    }
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
