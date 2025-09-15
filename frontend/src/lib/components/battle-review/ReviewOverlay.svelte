<script>
  import DamageGraphs from './DamageGraphs.svelte';
  import RewardList from './RewardList.svelte';
  export let summary = {};
  export let cards = [];
  export let relics = [];
</script>

<div class="review-overlay">
  <DamageGraphs damage={summary?.damage_by_type || {}} />
  <RewardList {cards} {relics} />
</div>
