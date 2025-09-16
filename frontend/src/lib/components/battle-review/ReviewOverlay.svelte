<script>
  import DamageGraphs from './DamageGraphs.svelte';
  import RewardList from './RewardList.svelte';
  export let summary = {};
  export let cards = [];
  export let relics = [];
  // Optional: allow parent views that already render element damage
  // summaries to hide the duplicate graph here.
  export let showDamageGraphs = true;

  // Aggregate damage totals across all entities so graphs display per-element numbers
  function aggregateDamageByElement(byType = {}) {
    const totals = {};
    for (const types of Object.values(byType)) {
      for (const [elem, amount] of Object.entries(types || {})) {
        totals[elem] = (totals[elem] || 0) + (amount || 0);
      }
    }
    return totals;
  }

  $: damageTotals = aggregateDamageByElement(summary?.damage_by_type || {});
</script>

<div class="review-overlay">
  {#if showDamageGraphs}
    <DamageGraphs damage={damageTotals} />
  {/if}
  <RewardList {cards} {relics} />
  
</div>
