<script>
  import RewardCard from '../RewardCard.svelte';
  import CurioChoice from '../CurioChoice.svelte';
  import { createEventDispatcher, getContext } from 'svelte';
  import { uiStore } from '../../systems/settingsStorage.js';
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

  $: conciseDescriptionsEnabled = Boolean($uiStore?.conciseDescriptions);
  $: descriptionModeLabel = conciseDescriptionsEnabled ? 'Concise descriptions' : 'Full descriptions';

  function resolveDescription(entry) {
    if (!entry || typeof entry !== 'object') return '';
    const full = typeof entry.full_about === 'string' ? entry.full_about : '';
    const concise = typeof entry.summarized_about === 'string' ? entry.summarized_about : '';
    return conciseDescriptionsEnabled ? (concise || full) : (full || concise);
  }
</script>

<div class="reward-list">
  {#if cards.length}
    <div class="cards">
      {#each cards as card}
        <RewardCard
          entry={card}
          on:select={forward}
          fullDescription={card.full_about}
          conciseDescription={card.summarized_about}
          description={resolveDescription(card)}
          useConciseDescriptions={conciseDescriptionsEnabled}
          descriptionModeLabel={descriptionModeLabel}
        />
      {/each}
    </div>
  {/if}
  {#if relics.length}
    <div class="relics">
      {#each relics as relic}
        <CurioChoice
          entry={relic}
          on:select={forward}
          fullDescription={relic.full_about}
          conciseDescription={relic.summarized_about}
          description={resolveDescription(relic)}
          useConciseDescriptions={conciseDescriptionsEnabled}
          descriptionModeLabel={descriptionModeLabel}
        />
      {/each}
    </div>
  {/if}
</div>
