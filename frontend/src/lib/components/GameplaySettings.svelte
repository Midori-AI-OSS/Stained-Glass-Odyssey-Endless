<script>
  import { Power } from 'lucide-svelte';
  import Tooltip from './Tooltip.svelte';
  export let showActionValues = false;
  export let fullIdleMode = false;
  export let scheduleSave;
  export let handleEndRun;
  export let endingRun = false;
  export let endRunStatus = '';
</script>

<div class="settings-panel">
  <div class="control">
    <div class="control-left">
      <Tooltip text="Display numeric action values in the turn order.">
        <span class="label">Show Action Values</span>
      </Tooltip>
    </div>
    <div class="control-right">
      <input type="checkbox" bind:checked={showActionValues} on:change={scheduleSave} />
    </div>
  </div>
  <div class="control">
    <div class="control-left">
      <Tooltip text="Automate rewards and room progression.">
        <span class="label">Full Idle Mode</span>
      </Tooltip>
    </div>
    <div class="control-right">
      <input type="checkbox" bind:checked={fullIdleMode} on:change={scheduleSave} />
    </div>
  </div>
  <div class="control">
    <div class="control-left">
      <Tooltip text="End the current run.">
        <span class="label"><Power /> End Run</span>
      </Tooltip>
    </div>
    <div class="control-right">
      <button on:click={handleEndRun} disabled={endingRun}>{endingRun ? 'Ending…' : 'End'}</button>
    </div>
  </div>
  {#if endRunStatus}
    <p class="status" data-testid="endrun-status">{endRunStatus}</p>
  {/if}
</div>

<style>
  @import './settings-shared.css';
</style>
