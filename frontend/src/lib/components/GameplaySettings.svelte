<script>
  import { Power, Timer, Bot, ListOrdered } from 'lucide-svelte';
  import DotSelector from './DotSelector.svelte';
  import Tooltip from './Tooltip.svelte';

  const MIN_ANIMATION_SPEED = 0.1;
  const MAX_ANIMATION_SPEED = 2;
  const DEFAULT_ANIMATION_SPEED = 1;
  const DOT_SCALE = 100;

  export let showActionValues = false;
  export let fullIdleMode = false;
  export let animationSpeed = DEFAULT_ANIMATION_SPEED;
  export let baseTurnPacing = 0.5;
  export let scheduleSave;
  export let handleEndRun;
  export let endingRun = false;
  export let endRunStatus = '';

  const zeroSpeedLabel = `${MIN_ANIMATION_SPEED.toFixed(1)}× speed`;
  const ZERO_DOT_CONTENT = ' ';

  function clampValue(value, min, max) {
    if (!Number.isFinite(value)) return min;
    if (value < min) return min;
    if (value > max) return max;
    return value;
  }

  function normalizedSpeed(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return DEFAULT_ANIMATION_SPEED;
    return clampValue(numeric, MIN_ANIMATION_SPEED, MAX_ANIMATION_SPEED);
  }

  function speedToDots(speed) {
    const clamped = normalizedSpeed(speed);
    const ratio = (clamped - MIN_ANIMATION_SPEED) / (MAX_ANIMATION_SPEED - MIN_ANIMATION_SPEED);
    return Math.round(ratio * DOT_SCALE);
  }

  function dotsToSpeed(dots) {
    const numeric = Number(dots);
    if (!Number.isFinite(numeric)) return normalizedSpeed(animationSpeed);
    const clampedDots = clampValue(numeric, 0, DOT_SCALE);
    const ratio = clampedDots / DOT_SCALE;
    const raw = MIN_ANIMATION_SPEED + ratio * (MAX_ANIMATION_SPEED - MIN_ANIMATION_SPEED);
    const rounded = Math.round(raw * 10) / 10;
    return clampValue(rounded, MIN_ANIMATION_SPEED, MAX_ANIMATION_SPEED);
  }

  function formatSpeedStepLabel(index) {
    const derived = dotsToSpeed((index + 1) * 10);
    return `${derived.toFixed(1)}× speed`;
  }

  let dotSpeed = speedToDots(animationSpeed);

  $: {
    const mapped = speedToDots(animationSpeed);
    if (mapped !== dotSpeed) {
      dotSpeed = mapped;
    }
  }

  $: displaySpeed = (() => {
    const numeric = Number(animationSpeed);
    if (!Number.isFinite(numeric) || numeric <= 0) return '1.0';
    return numeric.toFixed(1);
  })();

  // Show the effective pacing as seconds in the label: (Xs)
  $: turnSeconds = (() => {
    const base = Number(baseTurnPacing);
    const norm = normalizedSpeed(animationSpeed);
    const b = Number.isFinite(base) && base > 0 ? base : 0.5;
    const s = b / (norm || 1);
    return (Math.max(0.01, s)).toFixed(2);
  })();

  function handleSpeedChange() {
    const nextSpeed = dotsToSpeed(dotSpeed);
    if (!Number.isFinite(nextSpeed)) return;
    const previous = Number(animationSpeed);
    animationSpeed = nextSpeed;
    if (!Number.isFinite(previous) || Math.abs(nextSpeed - previous) > 0.001) {
      scheduleSave();
    }
  }
</script>

<div class="settings-panel">
  <div class="control">
    <div class="control-left">
      <Tooltip text="Display numeric action values in the turn order.">
        <span class="label"><ListOrdered /> Show Action Values</span>
      </Tooltip>
    </div>
    <div class="control-right">
      <input type="checkbox" bind:checked={showActionValues} on:change={scheduleSave} />
    </div>
  </div>
  <div class="control">
    <div class="control-left">
      <Tooltip text="Automate rewards and room progression.">
        <span class="label"><Bot /> Full Idle Mode</span>
      </Tooltip>
    </div>
    <div class="control-right">
      <input type="checkbox" bind:checked={fullIdleMode} on:change={scheduleSave} />
    </div>
  </div>
  <div class="control">
    <div class="control-left">
      <Tooltip text="Scale battle animation pacing. Higher is faster.">
        <span class="label"><Timer /> Animation Speed ({turnSeconds}s)</span>
      </Tooltip>
    </div>
    <div class="control-right">
      <DotSelector
        bind:value={dotSpeed}
        on:change={handleSpeedChange}
        zeroAriaLabel={zeroSpeedLabel}
        zeroContent={ZERO_DOT_CONTENT}
        muteAsIcon={false}
        formatStepAriaLabel={formatSpeedStepLabel}
      />
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
