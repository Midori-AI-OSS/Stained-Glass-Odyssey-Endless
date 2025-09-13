<script>
  import { Power } from 'lucide-svelte';
  export let showActionValues = false;
  export let scheduleSave;
  export let handleEndRun;
  export let endingRun = false;
  export let endRunStatus = '';
</script>

<div class="settings-panel">
  <div class="control" title="Display numeric action values in the turn order.">
    <label>Show Action Values</label>
    <input type="checkbox" bind:checked={showActionValues} on:change={scheduleSave} />
  </div>
  <div class="control" title="End the current run.">
    <Power />
    <label>End Run</label>
    <button on:click={handleEndRun} disabled={endingRun}>{endingRun ? 'Ending…' : 'End'}</button>
    {#if endRunStatus}
      <span class="status" data-testid="endrun-status">{endRunStatus}</span>
    {/if}
  </div>
</div>

<style src="./settings-shared.css"></style>
