<script>
  import { createSpinnerTokens } from '../systems/animationTokens.js';

  export let color = 'var(--element-color, currentColor)';
  export let duration = null; // Will use tokens if null
  export let reducedMotion = false;
  export let animationSpeed = 1; // Animation speed from settings

  // Create animation tokens for consistent timing
  $: spinnerTokens = createSpinnerTokens({ animationSpeed, motionSettings: { globalReducedMotion: reducedMotion } });
  $: effectiveDuration = duration ?? `${(spinnerTokens.duration / 1000).toFixed(2)}s`;
</script>

<div
  class="triple-ring-spinner"
  style={`--spinner-color: ${color}; --duration: ${effectiveDuration};`}
  class:reduced={reducedMotion || spinnerTokens.isReduced}
  aria-hidden="true"
>
  <div class="ring r1"></div>
  <div class="ring r2"></div>
  <div class="ring r3"></div>
</div>

<style>
  .triple-ring-spinner {
    position: relative;
    /* Resolve to pixels to ensure correct orbital radii */
    /* Slightly smaller default size and a gentle upward nudge */
    --size: var(--spinner-size, clamp(14px, calc(var(--portrait-size, 96px) * 0.16), 30px));
    width: var(--size);
    height: var(--size);
    transform: translateY(-6px);
  }
  .ring {
    position: absolute;
    top: 50%;
    left: 50%;
    border: 2px solid var(--spinner-color, currentColor);
    border-radius: 50%;
    opacity: 0.6;
    animation: pulse calc(var(--duration) * 2) ease-in-out infinite;
  }
  /* Define absolute ring sizes and their orbit radii in px */
  .r1 { --ring-size-px: var(--size); --orbit: calc(var(--size) / 2); animation-delay: 0s; }
  .r2 { --ring-size-px: calc(var(--size) * 0.66); --orbit: calc(var(--size) * 0.66 / 2); animation-delay: calc(var(--duration) / 3); }
  .r3 { --ring-size-px: calc(var(--size) * 0.33); --orbit: calc(var(--size) * 0.33 / 2); animation-delay: calc(var(--duration) * 2 / 3); }
  .ring {
    width: var(--ring-size-px);
    height: var(--ring-size-px);
    margin: calc(var(--ring-size-px) / -2);
  }
  /* Remove orbiting dots/orbs */
  .ring::before { content: none; display: none; }
  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.6; }
    50% { transform: scale(1.2); opacity: 1; }
  }
  .reduced .ring,
  .reduced .ring::before {
    animation: none;
  }
</style>
