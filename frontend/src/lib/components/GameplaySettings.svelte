<script>
  import { Power, Timer } from 'lucide-svelte';
  import Tooltip from './Tooltip.svelte';

  const MIN_ANIMATION_SPEED = 0.1;
  const MAX_ANIMATION_SPEED = 2;

  export let showActionValues = false;
  export let fullIdleMode = false;
  export let animationSpeed = 1;
  export let scheduleSave;
  export let handleEndRun;
  export let endingRun = false;
  export let endRunStatus = '';

  $: displaySpeed = (() => {
    const numeric = Number(animationSpeed);
    if (!Number.isFinite(numeric) || numeric <= 0) return '1.0';
    return numeric.toFixed(1);
  })();

  function handleSpeedInput(event) {
    const value = Number(event?.currentTarget?.value ?? animationSpeed);
    if (!Number.isFinite(value)) return;
    const clamped = Math.min(MAX_ANIMATION_SPEED, Math.max(MIN_ANIMATION_SPEED, value));
    animationSpeed = Math.round(clamped * 10) / 10;
    scheduleSave();
  }
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
      <Tooltip text="Scale battle animation pacing. Higher is faster.">
        <span class="label"><Timer /> Animation Speed</span>
      </Tooltip>
    </div>
    <div class="control-right">
      <input
        type="range"
        min={MIN_ANIMATION_SPEED}
        max={MAX_ANIMATION_SPEED}
        step="0.1"
        value={animationSpeed}
        on:input={handleSpeedInput}
      />
      <span class="value" aria-live="polite">{displaySpeed}×</span>
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
