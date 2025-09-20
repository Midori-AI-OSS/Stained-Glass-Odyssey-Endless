<script>
  import { getElementColor } from '../systems/assetLoader.js';

  export let color = '';
  export let reducedMotion = false;

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

  const orbDescriptors = [
    { id: 'zenith', x: 18, y: 24, radius: 450, drift: 56, delay: 0, base: 'light' },
    { id: 'aurora', x: 68, y: 18, radius: 425, drift: 64, delay: 8, base: 'wind' },
    { id: 'ember', x: 32, y: 64, radius: 496, drift: 52, delay: 14, base: 'fire' },
    { id: 'tide', x: 80, y: 68, radius: 415, drift: 70, delay: 20, base: 'ice' },
    { id: 'umbra', x: 12, y: 76, radius: 430, drift: 60, delay: 11, base: 'dark' },
    { id: 'volt', x: 48, y: 40, radius: 455, drift: 48, delay: 5, base: 'lightning' },
    { id: 'bloom', x: 56, y: 82, radius: 461, drift: 74, delay: 25, base: '#ff9fcc' }
  ];

  const orbs = orbDescriptors.map((descriptor, index) => ({
    ...descriptor,
    baseColor: resolveColorToken(descriptor.base, fallbackPalette[index % fallbackPalette.length])
  }));

  $: tintColor = resolveColorToken(color, fallbackTint);
</script>

<div
  class="storm"
  class:storm--reduced={reducedMotion}
  aria-hidden="true"
  style={`--storm-tint:${tintColor};`}
>
  {#if reducedMotion}
    <div class="storm__veil"></div>
  {:else}
    {#each orbs as orb (orb.id)}
      <div
        class="orb-shell"
        style={`--orb-x:${orb.x}%; --orb-y:${orb.y}%; --orb-radius:${orb.radius}px; --orb-drift:${orb.drift}s; --orb-delay:${orb.delay}s; --orb-base-color:${orb.baseColor};`}
      >
        <span class="orb"></span>
      </div>
    {/each}
  {/if}
</div>

<style>
  .storm {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
    z-index: -1;
    opacity: 0.6;
    transition: opacity 420ms ease;
    --storm-tint: #88a;
  }

  .storm:not(.storm--reduced) {
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
    animation: orbFloat var(--orb-drift) ease-in-out infinite;
    animation-delay: calc(-1 * var(--orb-delay));
    will-change: transform, opacity;
  }

  .orb-shell:nth-of-type(2n) {
    animation-direction: alternate;
  }

  .orb {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    opacity: 0.85;
    mix-blend-mode: screen;
    --orb-tint: color-mix(in srgb, var(--orb-base-color) 48%, var(--storm-tint) 52%);
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

  .storm--reduced {
    opacity: 0.5;
  }

  .storm__veil {
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 24% 24%, color-mix(in srgb, var(--storm-tint) 60%, white 40%) 0%, transparent 58%),
      radial-gradient(circle at 78% 28%, color-mix(in srgb, var(--storm-tint) 55%, #85a9ff 45%) 0%, transparent 68%),
      radial-gradient(circle at 46% 78%, color-mix(in srgb, var(--storm-tint) 50%, #ffb6ef 50%) 0%, transparent 72%),
      linear-gradient(180deg, color-mix(in srgb, var(--storm-tint) 35%, #0d1220 65%) 0%, transparent 100%);
    mix-blend-mode: screen;
    opacity: 0.75;
  }

  :global(html.reduced-motion) .storm:not(.storm--reduced) .orb-shell,
  :global(body.reduced-motion) .storm:not(.storm--reduced) .orb-shell {
    animation: none;
    opacity: 0.85;
  }
</style>
