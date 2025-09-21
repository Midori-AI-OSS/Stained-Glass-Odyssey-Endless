<script>
  import { getElementColor } from '../systems/assetLoader.js';
  import { motionStore } from '../systems/settingsStorage.js';
  import { createOrbTokens, deterministicVariation } from '../systems/animationTokens.js';

  export let color = '';
  export let reducedMotion = false; // Legacy prop for backward compatibility
  export let animationSpeed = 1; // Animation speed from GameplaySettings

  // Check both legacy prop and new granular settings using reactive store
  $: motionSettings = $motionStore || { globalReducedMotion: false, disableStarStorm: false };
  $: isElementOrbsDisabled = reducedMotion || motionSettings.globalReducedMotion || motionSettings.disableStarStorm;

  const fallbackTint = '#88a';
  const fallbackPalette = ['#7eb8ff', '#ff9f9f', '#b58dff', '#7fe8c9', '#ffe694', '#94a7ff', '#ffb7df', '#8fe3ff'];

  function resolveColorToken(token, fallback) {
    if (!token) return fallback;
    if (typeof token === 'string' && (token.startsWith('#') || token.startsWith('rgb'))) {
      return token;
    }
    try {
      return getElementColor(token);
    } catch {
      return fallback;
    }
  }

  // Base orb descriptors with deterministic positioning and properties
  const orbDescriptors = [
    { id: 'zenith', x: 18, y: 24, radiusBase: 450, base: 'light' },
    { id: 'aurora', x: 68, y: 18, radiusBase: 425, base: 'wind' },
    { id: 'ember', x: 32, y: 64, radiusBase: 496, base: 'fire' },
    { id: 'tide', x: 80, y: 68, radiusBase: 415, base: 'ice' },
    { id: 'umbra', x: 12, y: 76, radiusBase: 430, base: 'dark' },
    { id: 'volt', x: 48, y: 40, radiusBase: 455, base: 'lightning' },
    { id: 'bloom', x: 56, y: 82, radiusBase: 461, base: '#ff9fcc' }
  ];

  // Create orbs with deterministic animation properties using tokens
  $: orbs = orbDescriptors.map((descriptor, index) => {
    const animTokens = createOrbTokens(descriptor.id, { animationSpeed, motionSettings });
    const radiusVariation = deterministicVariation(descriptor.id + '-radius', 0.9, 1.1);
    
    return {
      ...descriptor,
      radius: Math.round(descriptor.radiusBase * radiusVariation),
      baseColor: resolveColorToken(descriptor.base, fallbackPalette[index % fallbackPalette.length]),
      driftDuration: animTokens.driftDuration,
      delay: animTokens.delay,
      delayS: animTokens.delayS,
      isStatic: animTokens.isStatic,
    };
  });

  $: tintColor = resolveColorToken(color, fallbackTint);
</script>

<div
  class="element-orbs"
  class:element-orbs--reduced={isElementOrbsDisabled}
  aria-hidden="true"
  style={`--orb-tint:${tintColor};`}
>
  {#if isElementOrbsDisabled}
    <div class="element-orbs__veil"></div>
  {:else}
    {#each orbs as orb (orb.id)}
      <div
        class="orb-shell"
        class:orb-shell--static={orb.isStatic}
        style={`--orb-x:${orb.x}%; --orb-y:${orb.y}%; --orb-radius:${orb.radius}px; --orb-drift:${(orb.driftDuration / 1000).toFixed(2)}s; --orb-delay:${orb.delayS}; --orb-base-color:${orb.baseColor};`}
      >
        <span class="orb"></span>
      </div>
    {/each}
  {/if}
}</div>

<style>
  .element-orbs {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
    z-index: -1;
    opacity: 0.6;
    transition: opacity 420ms ease;
    --orb-tint: #88a;
  }

  .element-orbs:not(.element-orbs--reduced) {
    display: block;
  }

  .orb-shell {
    position: absolute;
    left: var(--orb-x);
    top: var(--orb-y);
    width: calc(var(--orb-radius) * 2);
    height: calc(var(--orb-radius) * 2);
    margin-left: calc(var(--orb-radius) * -1);
    margin-top: calc(var(--orb-radius) * -1);
    will-change: transform, opacity;
  }

  .orb-shell:not(.orb-shell--static) {
    animation: orbFloat var(--orb-drift) ease-in-out infinite;
    animation-delay: calc(-1 * var(--orb-delay));
  }

  .orb-shell:nth-of-type(2n):not(.orb-shell--static) {
    animation-direction: alternate;
  }

  .orb {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    opacity: 0.85;
    mix-blend-mode: screen;
    --orb-tint: color-mix(in srgb, var(--orb-base-color) 48%, var(--orb-tint) 52%);
    background:
      radial-gradient(circle at 28% 26%, color-mix(in srgb, var(--orb-tint) 70%, white 30%) 0%, transparent 60%),
      radial-gradient(circle at 72% 70%, color-mix(in srgb, var(--orb-tint) 80%, transparent) 0%, transparent 80%),
      radial-gradient(circle, color-mix(in srgb, var(--orb-tint) 55%, transparent) 0%, transparent 92%);
    transition: background 1500ms ease, opacity 1200ms ease;
  }

  .orb-shell:nth-of-type(3n) .orb {
    opacity: 0.9;
  }

  .orb-shell:nth-of-type(4n) .orb {
    opacity: 0.7;
  }

  @keyframes orbFloat {
    0% {
      transform: translate3d(0, 0, 0) scale(0.94);
      opacity: 0.75;
    }
    35% {
      transform: translate3d(calc(var(--orb-radius) * 0.08), calc(var(--orb-radius) * -0.05), 0) scale(1.02);
      opacity: 0.92;
    }
    70% {
      transform: translate3d(calc(var(--orb-radius) * -0.07), calc(var(--orb-radius) * 0.06), 0) scale(1.05);
      opacity: 1;
    }
    100% {
      transform: translate3d(calc(var(--orb-radius) * 0.05), calc(var(--orb-radius) * -0.04), 0) scale(0.97);
      opacity: 0.78;
    }
  }

  .element-orbs--reduced {
    opacity: 0.5;
  }

  .element-orbs__veil {
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 24% 24%, color-mix(in srgb, var(--orb-tint) 60%, white 40%) 0%, transparent 58%),
      radial-gradient(circle at 78% 28%, color-mix(in srgb, var(--orb-tint) 55%, #85a9ff 45%) 0%, transparent 68%),
      radial-gradient(circle at 46% 78%, color-mix(in srgb, var(--orb-tint) 50%, #ffb6ef 50%) 0%, transparent 72%),
      linear-gradient(180deg, color-mix(in srgb, var(--orb-tint) 35%, #0d1220 65%) 0%, transparent 100%);
    mix-blend-mode: screen;
    opacity: 0.75;
  }

  /* Static state for reduced motion */
  .orb-shell--static {
    opacity: 0.85;
    transform: translate3d(0, 0, 0) scale(1);
  }

  /* Global reduced motion override */
  :global(html.reduced-motion) .element-orbs:not(.element-orbs--reduced) .orb-shell,
  :global(body.reduced-motion) .element-orbs:not(.element-orbs--reduced) .orb-shell {
    animation: none;
    opacity: 0.85;
  }
</style>
