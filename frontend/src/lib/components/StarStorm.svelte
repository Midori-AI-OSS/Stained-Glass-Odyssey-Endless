<script>
  import { onDestroy } from 'svelte';
  import { getElementColor } from '../systems/assetLoader.js';

  export let color = '';
  export let reducedMotion = false;

  function rand(min, max) { return Math.random() * (max - min) + min; }
  const starElements = ['fire','ice','lightning','light','dark','wind'];
  function randomElementColor() {
    const el = starElements[Math.floor(Math.random() * starElements.length)];
    try { return getElementColor(el); } catch { return '#88a'; }
  }
  function spawnStar(c = color || randomElementColor()) {
    return {
      left: Math.random() * 100,
      size: rand(3, 6),
      duration: rand(18, 28),
      delay: rand(0, 12),
      drift: rand(-20, 20),
      color: c
    };
  }
  function makeStars(count) {
    return Array.from({ length: count }, () => spawnStar());
  }
  $: density = reducedMotion ? 60 : 240;
  let stars = [];
  $: if (stars.length === 0) {
    stars = makeStars(density);
    fadePulse(260);
  }
  $: if (stars.length && stars.length !== density) {
    if (density > stars.length) {
      stars = stars.concat(makeStars(density - stars.length));
    } else if (density < stars.length) {
      stars = stars.slice(0, density);
    }
  }

  let fading = false;
  function fadePulse(dur = 260, low = 0.25) {
    fading = true;
    clearTimeout(fadeTimer);
    fadeTimer = setTimeout(() => { fading = false; }, dur);
  }
  let fadeTimer;

  let lastColor = '';
  let replaceTimer = null;
  let forceTimer = null;
  function startColorTransition() {
    if (!color) return;
    if (replaceTimer) clearInterval(replaceTimer);
    if (forceTimer) clearTimeout(forceTimer);
    fadePulse(260);
    let pool = stars.map((s, i) => ({ s, i }))
      .filter(({ s }) => s.color !== color)
      .map(({ i }) => i);
    if (pool.length === 0) return;
    const intervalMs = 120;
    const targetMs = 1800;
    const ticks = Math.max(1, Math.round(targetMs / intervalMs));
    const batch = Math.max(1, Math.ceil(pool.length / ticks));
    replaceTimer = setInterval(() => {
      const n = Math.min(batch, pool.length);
      for (let k = 0; k < n; k++) {
        const idx = pool.pop();
        if (idx == null) break;
        stars[idx] = spawnStar(color);
      }
      stars = stars.slice();
      if (pool.length === 0) {
        clearInterval(replaceTimer);
        replaceTimer = null;
      }
    }, intervalMs);
    forceTimer = setTimeout(() => {
      if (pool.length > 0) {
        stars = stars.map(s => (s.color === color ? s : spawnStar(color)));
      }
      if (replaceTimer) { clearInterval(replaceTimer); replaceTimer = null; }
    }, targetMs + 400);
  }
  $: if (color && lastColor && color !== lastColor) {
    startColorTransition();
  }
  $: lastColor = color;

  onDestroy(() => {
    if (replaceTimer) clearInterval(replaceTimer);
    if (fadeTimer) clearTimeout(fadeTimer);
    if (forceTimer) clearTimeout(forceTimer);
  });
</script>

<div class="stars" aria-hidden="true" style={`opacity:${fading ? 0.25 : 0.55}`}>
  <div class="storm-blur">
    {#each stars as s}
      <span class="star" style={`--x:${s.left}%; --s:${s.size}px; --d:${s.duration}s; --delay:${s.delay}s; --dx:${s.drift}px; --c:${s.color};`}></span>
    {/each}
  </div>
  {#each stars as s}
    <span class="star" style={`--x:${s.left}%; --s:${s.size}px; --d:${s.duration}s; --delay:${s.delay}s; --dx:${s.drift}px; --c:${s.color};`}>
      <span class="core"></span>
    </span>
  {/each}
</div>

<style>
  .stars { position:absolute; inset:0; overflow:hidden; pointer-events:none; z-index:-1; opacity:0.55; transition: opacity 220ms ease; }
  .star {
    position: absolute;
    top: -10%;
    left: var(--x);
    width: 0;
    height: 0;
    animation-name: af-fallTop;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    animation-duration: var(--d);
    animation-delay: var(--delay);
  }
  .star .core {
    position: absolute;
    top: 0;
    left: 0;
    width: var(--s);
    height: var(--s);
    background: radial-gradient(circle, var(--c) 0%, transparent 70%);
    border-radius: 50%;
    filter: drop-shadow(0 0 8px color-mix(in srgb, var(--c) 70%, transparent));
    animation-name: af-drift;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    animation-duration: var(--d);
    animation-delay: var(--delay);
    z-index: 0;
  }
.star .core::after {
    content: '';
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: calc(var(--s) * -8);
    width: calc(max(2px, var(--s) * 0.4));
    height: calc(var(--s) * 10);
    background: linear-gradient(180deg, color-mix(in srgb, var(--c) 75%, transparent) 0%, transparent 70%);
    filter: blur(1px);
  }
  .storm-blur { position:absolute; inset:0; pointer-events:none; z-index:-1; filter: blur(20px); opacity:0.5; }
  .storm-blur .star::before {
    content: '';
    position: absolute;
    top: calc(var(--s) * -1);
    left: calc(var(--s) * -1);
    width: calc(var(--s) * 3);
    height: calc(var(--s) * 3);
    background: radial-gradient(circle, var(--c) 0%, transparent 70%);
    border-radius: 50%;
    animation-name: af-drift;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    animation-duration: var(--d);
    animation-delay: var(--delay);
  }
  @keyframes af-fallTop {
    0% { top: -10%; opacity:0.0; }
    10% { opacity:1.0; }
    90% { opacity:1.0; }
    100% { top:110%; opacity:0.0; }
  }
  @keyframes af-drift {
    0% { transform: translateX(0); }
    100% { transform: translateX(var(--dx)); }
  }
  :global(html.reduced-motion) .stars .star,
  :global(body.reduced-motion) .stars .star { animation: none; opacity:0.35; top:15%; }
  :global(html.reduced-motion) .stars .star .core,
  :global(body.reduced-motion) .stars .star .core { animation: none; }
</style>
