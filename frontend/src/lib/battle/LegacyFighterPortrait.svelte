<script>
  // Renders a fighter portrait with HP bar, element chip, and status icons.
  import { getCharacterImage, getElementColor, getElementIcon } from '../systems/assetLoader.js';
  import StatusIcons from './StatusIcons.svelte';

  export let fighter = {};
  export let reducedMotion = false;
  // Optional rank identifier retained for analytics / data attributes
  export let rankTag = null;
  function getStackCount(p) {
    const stacks = p?.stacks;
    if (typeof stacks === 'object') {
      if ('count' in stacks) return stacks.count;
      return stacks.mitigation ?? 0;
    }
    return stacks ?? 0;
  }

  function isOvercharged(stacks) {
    return typeof stacks === 'object' && stacks.overcharged;
  }

  $: passiveTip = (fighter.passives || [])
    .map((p) => {
      const count = getStackCount(p);
      const oc = isOvercharged(p.stacks);
      return `${p.id}${count > 1 ? ` x${count}` : ''}${oc ? ' (overcharged)' : ''}`;
    })
    .join(', ');

  // Percent helpers for HP and overheal (shields)
  $: _maxHP = Number(fighter?.max_hp || 0);
  $: _hp = Number(fighter?.hp || 0);
  $: _shields = Number(fighter?.shields || 0);
  $: hpPct = _maxHP > 0 ? Math.min(100, (100 * _hp) / _maxHP) : 0;
  $: ohPct = _maxHP > 0 ? Math.max(0, Math.min(100, (100 * _shields) / _maxHP)) : 0;
  // TODO: Make this dynamic per-character (max overheal percent).
  // For now, allow up to +100% overheal to display visually.
  const OH_CAP_UI = 100;
  $: ohDispPct = Math.min(ohPct, OH_CAP_UI);
  $: hpHue = (hpPct / 100) * 120;
  $: hpColor = `hsl(${hpHue}, 100%, 45%)`;

  $: elColor = getElementColor(fighter.element);
  $: ultProgress = Math.max(0, Math.min(1, Number(fighter?.ultimate_charge || 0) / 15));
  let lowContrast = false;
  let prevUltReady = false;
  let showUltPulse = false;

  $: if (fighter.ultimate_ready && !prevUltReady && !reducedMotion) {
    showUltPulse = true;
    setTimeout(() => {
      showUltPulse = false;
    }, 600);
  }
  $: prevUltReady = fighter.ultimate_ready;

  // Improve ring readability for dark-type or low-brightness colors
  function parseHex(hex) {
    if (typeof hex !== 'string') return null;
    const h = hex.trim();
    const m3 = /^#([\da-fA-F])([\da-fA-F])([\da-fA-F])$/;
    const m6 = /^#([\da-fA-F]{2})([\da-fA-F]{2})([\da-fA-F]{2})$/;
    let r, g, b;
    if (m6.test(h)) {
      const m = h.match(m6);
      r = parseInt(m[1], 16); g = parseInt(m[2], 16); b = parseInt(m[3], 16);
    } else if (m3.test(h)) {
      const m = h.match(m3);
      r = parseInt(m[1] + m[1], 16); g = parseInt(m[2] + m[2], 16); b = parseInt(m[3] + m[3], 16);
    } else {
      return null;
    }
    return { r, g, b };
  }
  function isLowBrightness(color) {
    const rgb = parseHex(color);
    if (!rgb) return false;
    const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000; // 0-255
    return brightness < 145; // threshold tuned for dark background
  }
  $: lowContrast = (() => {
    const name = String(fighter?.element || '').toLowerCase();
    if (name === 'dark') return true;
    return isLowBrightness(elColor);
  })();

  // NOTE: Do not add ult icon pulse/size logic here.
  // The Fighter UI overlays and ult gauge behavior live in BattleFighterCard.svelte.
  // This portrait component is used in multiple contexts; keep it minimal.
</script>

<div class="portrait-wrap">
  <div
    class="portrait-frame"
    class:ultimate-ready={fighter.ultimate_ready}
    title={passiveTip}
    style={`--el-color: ${elColor}`}
    data-rank-tag={rankTag != null ? rankTag : fighter?.rank}
  >
    <img
      src={getCharacterImage((fighter?.summon_type === 'phantom' && fighter?.summoner_id) ? fighter.summoner_id : (fighter?.summon_type || fighter?.id))}
      alt=""
      class="portrait {fighter?.summon_type === 'phantom' ? 'phantom' : ''}"
      style={`border-color: ${elColor}`}
    />
    <div class="element-chip" class:low-contrast={lowContrast}>
      {#if showUltPulse}
        <div class="ult-ready-pulse"></div>
      {/if}
      <svg class="ultimate-ring" viewBox="0 0 20 20">
        <circle class="track" cx="10" cy="10" r="9" />
        <circle
          class="contrast"
          pathLength="100"
          cx="10"
          cy="10"
          r="9"
          style={`stroke-dasharray: ${ultProgress * 100} 100`}
        />
        <circle
          class="fill"
          pathLength="100"
          cx="10"
          cy="10"
          r="9"
          style={`stroke-dasharray: ${ultProgress * 100} 100`}
        />
      </svg>
      <svelte:component
        this={getElementIcon(fighter.element)}
        class="element-icon"
        style={`color: ${elColor}`}
        aria-hidden="true"
      />
    </div>
  </div>
  <div class="hp-bar" class:reduced={reducedMotion}>
    {#if ohDispPct > 0}
      <div
        class="overheal-fill"
        style={`width: calc(${ohDispPct}% + 5px); left: -5px;`}
      ></div>
    {/if}
    <div class="hp-fill" style={`width: ${hpPct}%; background-color: ${hpColor};`}></div>
  </div>
  {#if ((Array.isArray(fighter.hots) ? fighter.hots.length : 0) + (Array.isArray(fighter.dots) ? fighter.dots.length : 0) + (Array.isArray(fighter.active_effects) ? fighter.active_effects.length : 0)) > 0}
    <!-- Buff Bar: shows current HoT/DoT effects under the portrait. -->
    <!-- This bar is intentionally styled with a stained-glass look, matching
         the stats panels and top bars. Keep this comment to clarify purpose. -->
    <div class="buff-bar">
      <StatusIcons hots={fighter.hots} dots={fighter.dots} active_effects={fighter.active_effects} layout="bar" />
    </div>
  {/if}
</div>

<style>
  .portrait-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .hp-bar {
    /* Slightly narrower than portrait for breathing room, centered by parent */
    width: calc(var(--portrait-size) - 0.75rem);
    height: 0.4rem; /* a bit smaller */
    border: 1px solid #000;
    background: #333;
    margin-top: 0.35rem; /* add space below the portrait */
    position: relative;
    overflow: visible; /* allow underlay to extend slightly to the left */
    border-radius: 3px;
  }
  .hp-fill {
    height: 100%;
    background: #0f0;
    position: absolute;
    left: 0;
    top: 0;
    transition: width 0.3s linear, background-color 0.3s linear;
  }
  .overheal-fill {
    height: calc(100% + 2px);
    background: rgba(255, 255, 255, 0.92);
    position: absolute;
    left: 0;
    top: -1px; /* slight upward offset */
    transition: width 0.3s linear;
  }
  .hp-bar.reduced .hp-fill,
  .hp-bar.reduced .overheal-fill {
    transition: none;
  }
  .portrait-frame { position: relative; width: var(--portrait-size); height: var(--portrait-size); }
  /* Scale chip and pips relative to the portrait so Battle Review auto-resizes */
  .portrait-frame {
    --chip-size: calc(var(--portrait-size) * 0.34);
    /* Allow pips to scale across views while staying small */
    --pip-size: clamp(4px, calc(var(--portrait-size) * 0.11), 10px);
    --pip-gap: clamp(1px, calc(var(--portrait-size) * 0.02), 3px);
  }
  .portrait {
    width: 100%;
    height: 100%;
    border: 2px solid #555;
    border-radius: 4px;
    display: block;
  }
  .portrait.phantom { filter: grayscale(60%) brightness(0.92); }
  .portrait-frame.ultimate-ready { box-shadow: 0 0 8px var(--el-color); }
  .element-chip {
    position: absolute;
    bottom: 2px;
    right: 2px;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    width: var(--chip-size);
    height: var(--chip-size);
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 50%;
    isolation: isolate; /* ensure pseudo-element stays within stacking context */
    /* Strong background blur to improve ring/icon readability on all elements */
    backdrop-filter: blur(12px) saturate(110%);
    -webkit-backdrop-filter: blur(12px) saturate(110%);
  }
  /* Remove outer fade/glow around the element chip per feedback */
  .element-chip::before { content: none; }
  .ultimate-ring { position: absolute; inset: 0; transform: rotate(-90deg); }
  .ult-ready-pulse {
    position: absolute;
    inset: -2px;
    border-radius: 50%;
    border: 2px solid var(--el-color);
    box-shadow: 0 0 6px var(--el-color);
    opacity: 0.8;
    animation: ult-pulse 0.6s ease-out;
    pointer-events: none;
    z-index: -1;
  }
  @keyframes ult-pulse {
    from { transform: scale(1); opacity: 0.8; }
    to { transform: scale(1.6); opacity: 0; }
  }
  .track {
    fill: none;
    stroke: rgba(0, 0, 0, 0.4);
    stroke-width: 2;
  }
  /* Contrast stroke sits behind the colored fill; only visible on low-contrast */
  .contrast {
    fill: none;
    stroke: #fff;
    stroke-opacity: 0.55;
    stroke-width: 3;
    opacity: 0;
    transition: opacity 0.15s linear;
  }
  .fill {
    fill: none;
    stroke: var(--el-color);
    stroke-width: 2;
    transition: stroke-dasharray 0.2s linear;
  }
  .element-chip.low-contrast .contrast { opacity: 1; }
  .element-chip.low-contrast .track { stroke: rgba(255, 255, 255, 0.25); }
  :global(.element-icon) { width: calc(var(--chip-size) * 0.5); height: calc(var(--chip-size) * 0.5); display: block; }


  /* Buff Bar (stained-glass style) */
  .buff-bar {
    width: calc(var(--portrait-size) - 0.75rem); /* slightly narrower than portrait (left/right smaller) */
    margin: 0.5rem auto 0; /* add a bit more space from portrait and center it */
    padding: 0.25rem;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
  }
</style>
