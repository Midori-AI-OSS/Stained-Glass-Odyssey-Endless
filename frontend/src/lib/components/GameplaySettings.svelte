<script>
  import { Power } from 'lucide-svelte';
  import Tooltip from './Tooltip.svelte';
  export let showActionValues = false;
  export let scheduleSave;
  export let handleEndRun;
  export let endingRun = false;
  export let endRunStatus = '';
</script>

<div class="settings-panel">
  <div class="control">
    <Tooltip text="Display numeric action values in the turn order.">
      <span class="label">Show Action Values</span>
    </Tooltip>
    <input type="checkbox" bind:checked={showActionValues} on:change={scheduleSave} />
  </div>
  <div class="control">
    <Tooltip text="End the current run.">
      <span class="label"><Power /> End Run</span>
    </Tooltip>
    <button on:click={handleEndRun} disabled={endingRun}>{endingRun ? 'Ending…' : 'End'}</button>
    {#if endRunStatus}
      <span class="status" data-testid="endrun-status">{endRunStatus}</span>
    {/if}
  </div>
</div>

<style src="./settings-shared.css"></style>
