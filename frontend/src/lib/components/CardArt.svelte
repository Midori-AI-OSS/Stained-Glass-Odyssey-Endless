<script>
  export let entry = {};
  export let type = 'card';
  export let roundIcon = false;
  export let size = 'normal';
  export let hideFallback = false;
  export let compact = false;
  // When true, suppress ambient marks and border twinkles for cleaner embedding (e.g., shop)
  export let quiet = false;
  // When false, suppress the title in the card header (viewer usage)
  export let showTitle = true;
  // When true, fill parent container instead of fixed pixel size
  export let fluid = false;
  // When false, suppress the about panel under the glyph
  export let showAbout = true;
  // When true, render only the artwork area filling the container (no title/about)
  export let imageOnly = false;
  import { getHourlyBackground, getGlyphArt } from '../systems/assetLoader.js';
  const starColors = {
    1: '#808080',  // gray
    2: '#1E90FF',  // blue
    3: '#228B22',  // green
    4: '#800080',  // purple
    5: '#FF3B30',  // red
    6: '#FFD700',  // gold
    fallback: '#708090'
  };
  $: width = compact ? 60 : (size === 'small' ? 140 : 280);
  // Fixed card height so top box can be exactly 50%
  $: cardHeight = compact ? 60 : (size === 'small' ? 320 : 440);
  // Styles used for outer wrapper; if fluid, stretch to parent
  $: widthStyle = fluid ? '100%' : `${width}px`;
  // Preserve aspect ratio when fluid to avoid distortion
  $: heightStyle = fluid ? 'auto' : `${cardHeight}px`;
  $: ratioStyle = fluid ? 'aspect-ratio: 7 / 11;' : '';
  $: color = starColors[entry.stars] || starColors.fallback;
  // Helper function to convert hex color to rgba with opacity
  function hexToRgba(hex, alpha) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return `rgba(128, 128, 128, ${alpha})`;
    return `rgba(${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}, ${alpha})`;
  }
  // Compute rgba values for different alpha levels based on accent color
  $: accentAlpha03 = hexToRgba(color, 0.03);
  $: accentAlpha28 = hexToRgba(color, 0.28);
  $: accentAlpha45 = hexToRgba(color, 0.45);
  $: accentAlpha55 = hexToRgba(color, 0.55);
  $: accentAlpha60 = hexToRgba(color, 0.60);
  $: accentAlpha65 = hexToRgba(color, 0.65);
  $: accentAlpha68 = hexToRgba(color, 0.68);
  $: accentAlpha92 = hexToRgba(color, 0.92);
  // Background image for the interbox (top section)
  // Use special art for specific relics when available.
  let bg = getHourlyBackground();
  // Allow explicit image override for the glyph background when provided
  $: {
    const explicit = entry?.artUrl || entry?.imageUrl || entry?.img;
    const custom = explicit || getGlyphArt(type, entry);
    bg = custom || getHourlyBackground();
  }
  // Ambient floating gray marks under the glyph box
  function rand(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
  function makeMarks(count) {
    return Array.from({ length: count }, () => ({
      left: Math.random() * 90 + 5, // percent
      top: Math.random() * 70 + 10, // percent
      size: rand(6, 16),            // px
      duration: rand(30, 60),       // seconds
      delay: rand(0, 20),           // seconds
      dx: rand(-24, 24),            // px
      dy: rand(-12, 12),            // px
    }));
  }
  let marks = [];
  $: marks = quiet ? [] : makeMarks(size === 'small' ? 14 : 24);
  // Border twinkles configuration
  function makeTwinkles(count) {
    const sides = ['top','right','bottom','left'];
    const shapes = ['dot','cross','diamond','dot']; // bias towards dots
    return Array.from({ length: count }, () => ({
      side: sides[Math.floor(Math.random() * sides.length)],
      pos: Math.random() * 100,       // 0-100%
      size: rand(4, 9),               // px
      duration: rand(4, 9),           // seconds
      delay: rand(0, 8),              // seconds
      shape: shapes[Math.floor(Math.random() * shapes.length)]
    }));
  }
  let twinkles = [];
  $: starRank = Math.max(1, Math.min(Number(entry?.stars || 1), 5));
  $: baseTwinkles = size === 'small' ? 16 : 28;
  // Slightly increase baseline twinkle intensity for 1-star
  $: twinkleFactor = 1.2 + (starRank - 1) * 0.6;
  $: twinkleCount = Math.round(baseTwinkles * twinkleFactor);
  // Nudge baseline alpha so 1-star is a bit more visible
  $: twinkleAlpha = Math.min(0.85, 0.60 + (starRank - 1) * 0.08);
  $: twinkles = quiet ? [] : makeTwinkles(twinkleCount);
</script>

<div class="card-art" class:fluid={fluid} style={`width:${widthStyle}; height:${heightStyle}; ${ratioStyle} --accent:${color}; --twA:${twinkleAlpha}; --accent-03:${accentAlpha03}; --accent-28:${accentAlpha28}; --accent-45:${accentAlpha45}; --accent-55:${accentAlpha55}; --accent-60:${accentAlpha60}; --accent-65:${accentAlpha65}; --accent-68:${accentAlpha68}; --accent-92:${accentAlpha92};` }>
  {#if imageOnly}
    <div class="glyph full">
      <div class="glyph-bg" style={`background-image:url(${bg})`}></div>
      {#if entry.stars}
        <div class="stars-overlay">{'★'.repeat(entry.stars || 0)}</div>
      {/if}
    </div>
  {:else}
    <div class="topbox" style={`--accent:${color}`}>
      {#if showTitle}
        <div class="title">{entry.name}</div>
      {/if}
      <div class={`glyph${roundIcon ? ' round' : ''}`}>
        <div class="glyph-bg" style={`background-image:url(${bg})`}></div>
        <div class="glyph-ambient">
          {#each marks as m}
            <span
              class="mark"
              style={`left:${m.left}%; top:${m.top}%; width:${m.size}px; height:${m.size}px; animation-duration:${m.duration}s; animation-delay:${m.delay}s; --dx:${m.dx}px; --dy:${m.dy}px;`}
            />
          {/each}
        </div>
        <div class="stars-overlay">{'★'.repeat(entry.stars || 0)}</div>
      </div>
    </div>
    {#if showAbout && entry.about}
      <div class="about-box">{entry.about}</div>
    {/if}
    <div class="twinkles" aria-hidden="true">
      {#each twinkles as t}
        <span
          class={`twinkle s-${t.side} shape-${t.shape}`}
          style={`--p:${t.pos}%; --s:${t.size}px; animation-duration:${t.duration}s; animation-delay:${t.delay}s;`}
        />
      {/each}
    </div>
  {/if}
</div>

<style>
  .card-art {
    background: linear-gradient(180deg, rgba(0,0,0,0.65), rgba(0,0,0,0.45));
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    color: #fff;
    box-shadow: 0 2px 10px rgba(0,0,0,0.35);
    backdrop-filter: blur(6px);
    position: relative;
    box-sizing: border-box;
  }
  /* Star-rank tint spanning the full card, so both top and bottom areas pick up the accent.
     Keep it subtle so the bottom stays dark but colored. */
  .card-art::before {
    content: '';
    position: absolute;
    inset: 0;
    background: var(--accent-03);
    pointer-events: none;
    /* No z-index needed; pseudo-element paints behind normal content by default */
  }
  .topbox {
    position: relative;
    height: 50%;
    width: 100%;
    /* Make the star-rank accent area slightly see-through */
    background: transparent;
    display: grid;
    grid-template-rows: auto 1fr;
    align-items: stretch;
    justify-items: stretch;
    padding: 6px 8px;
    box-sizing: border-box;
  }
  /* Semi-transparent animated accent overlay so content remains crisp */
  .topbox::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 0;
    background-image:
      /* subtle top-to-bottom shade */
      linear-gradient(180deg, rgba(0,0,0,0.06), rgba(0,0,0,0.16)),
      /* animated accent gradient - mixing accent with white/black for gradient stops */
      linear-gradient(
        135deg,
        rgba(255,255,255,0.85) 0%,
        var(--accent-92) 50%,
        rgba(255,255,255,0.85) 100%
      );
    background-color: var(--accent-68);
    background-size: auto, 220% 220%;
    background-position: center, 0% 50%;
    animation: accent-pan 14s ease-in-out infinite;
    opacity: 0.60; /* reduced tint */
    pointer-events: none;
    z-index: 0;
  }
  @keyframes accent-pan {
    0% { background-position: center, 0% 50%; }
    50% { background-position: center, 100% 50%; }
    100% { background-position: center, 0% 50%; }
  }
  @media (prefers-reduced-motion: reduce) {
    .topbox::before { animation: none; background-position: center, 50% 50%; }
  }
  .glyph-bg {
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    /* Let the artwork show with full color and brightness */
    filter: saturate(1.05) contrast(1.06);
    opacity: 1;
    z-index: 0; /* bottom-most inside glyph */
    border-radius: inherit;
  }
  .glyph-ambient {
    position: absolute;
    inset: 0;
    overflow: hidden;
    z-index: 2; /* above image, below stars */
    border-radius: inherit;
  }
  .mark {
    position: absolute;
    background: rgba(200,200,200,0.16);
    border-radius: 50%;
    filter: blur(0.6px);
    animation-name: drift;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    animation-direction: alternate;
  }
  @keyframes drift {
    from { transform: translate(0, 0); }
    to { transform: translate(var(--dx), var(--dy)); }
  }
  .title {
    justify-self: start;
    align-self: start;
    font-weight: 700;
    font-size: 0.95rem;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.45);
    z-index: 1;
  }
  .glyph {
    display: flex;
    align-items: center;
    justify-content: center;
    justify-self: stretch;
    align-self: stretch;
    width: 100%;
    max-width: none;
    color: #fff;
    font-weight: 800;
    font-size: 2rem;
    letter-spacing: 1px;
    /* Keep a subtle highlight, but remove heavy darkening so art isn't gray */
    background: radial-gradient(ellipse at 50% 40%, rgba(255,255,255,0.08), rgba(0,0,0,0.0) 60%);
    border: 2px solid rgba(255,255,255,0.18);
    box-shadow: 0 2px 10px rgba(0,0,0,0.35);
    border-radius: 10px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.4);
    position: relative;
    margin-top: 6px;
    z-index: 1; /* glyph content base; specific layers override */
  }
  .glyph.full {
    position: absolute;
    inset: 0;
    margin: 0;
    border-radius: inherit;
    border: none;
    background: none;
  }
  /* Accent outline overlay above glyph image */
  .glyph::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    box-shadow: inset 0 0 0 2px var(--accent);
    z-index: 4; /* ensure outline is above photo and ambient */
    pointer-events: none;
  }

  /* Border twinkles around the card outline */
  .twinkles {
    position: absolute;
    inset: 0;
    z-index: 2; /* above base; glyph has its own higher overlays */
    pointer-events: none;
    border-radius: inherit;
  }
  .twinkle {
    position: absolute;
    width: var(--s);
    height: var(--s);
    opacity: 0;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255, var(--twA)) 0%, var(--accent-60) 55%, transparent 70%);
    box-shadow:
      0 0 4px var(--accent-65),
      0 0 10px var(--accent-45);
    animation-name: twinkle-pop;
    animation-timing-function: ease-in-out;
    animation-iteration-count: infinite;
  }
  /* Shape variants */
  .twinkle.shape-dot { border-radius: 50%; }
  .twinkle.shape-cross { border-radius: 0; background: none; }
  .twinkle.shape-diamond { border-radius: 2px; transform: rotate(45deg); }

  .twinkle.shape-diamond {
    background:
      radial-gradient(circle at 50% 50%, rgba(255,255,255,var(--twA)) 0%, transparent 70%);
    box-shadow:
      0 0 4px var(--accent-65),
      0 0 10px var(--accent-45);
  }
  .twinkle.shape-cross::before,
  .twinkle.shape-cross::after {
    content: '';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    background: linear-gradient(
      to right,
      transparent,
      var(--accent-55),
      transparent
    );
    filter: drop-shadow(0 0 6px var(--accent-55));
    border-radius: 2px;
  }
  .twinkle.shape-cross::before { width: calc(var(--s) * 1.6); height: calc(var(--s) * 0.18); }
  .twinkle.shape-cross::after  { width: calc(var(--s) * 0.18); height: calc(var(--s) * 1.6); }
  /* Side placement helpers */
  .twinkle.s-top { top: 2px; left: var(--p); }
  .twinkle.s-bottom { bottom: 2px; left: var(--p); }
  .twinkle.s-left { left: 2px; top: var(--p); }
  .twinkle.s-right { right: 2px; top: var(--p); }

  @keyframes twinkle-pop {
    0%, 75%, 100% { opacity: 0; transform: scale(0.3); }
    12% { opacity: 0.6; transform: scale(1); }
    20% { opacity: 0.9; }
    35% { opacity: 0.25; transform: scale(0.8); }
    50% { opacity: 0.0; transform: scale(0.4); }
  }
  .glyph.round {
    justify-self: center;
    align-self: center;
    width: 70%;
    max-width: 180px;
    aspect-ratio: 1 / 1;
    border-radius: 50%;
  }
  /* When fluid, allow the relic round glyph to scale with the card width */
  .card-art.fluid .glyph.round {
    max-width: none;
    width: 78%;
  }
  .stars-overlay {
    position: absolute;
    bottom: 6px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.95rem;
    text-shadow: 0 1px 2px rgba(0,0,0,0.35);
    pointer-events: none;
    z-index: 5; /* above glyph image, outline, and orbs */
  }
  .about-box {
    flex: 1;
    margin: 0;
    /* Darken slightly more to reduce color bleed from full-card tint */
    background: rgba(0,0,0,0.58);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 0;
    padding: 10px 12px;
    font-size: 0.9rem;
    line-height: 1.25;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.25);
    box-sizing: border-box;
  }
</style>
