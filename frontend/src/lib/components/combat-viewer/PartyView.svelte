<script>
  import PartyRoster from '../PartyRoster.svelte';

  export let roster = [];
  export let selectedId = null;
</script>

<div class="roster-section party-view">
  <h4 class="roster-title">Party</h4>
  <PartyRoster
    {roster}
    selected={[selectedId].filter(Boolean)}
    bind:previewId={selectedId}
    reducedMotion={true}
    on:toggle={() => {}}
  />
</div>

