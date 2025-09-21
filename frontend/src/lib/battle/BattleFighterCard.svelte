<script>
  import { Circle as PipCircle } from 'lucide-svelte';
  import TripleRingSpinner from '../components/TripleRingSpinner.svelte';
  import {
    getCharacterImage,
    getElementColor,
    getElementIcon,
    getDamageTypePalette,
    hasCharacterGallery,
    advanceCharacterImage
  } from '../systems/assetLoader.js';
  import { motionStore } from '../systems/settingsStorage.js';

  export let fighter = {};
  export let position = 'bottom'; // 'top' for foes, 'bottom' for party
  export let reducedMotion = false; // Legacy prop for backward compatibility
  export let size = 'normal'; // 'normal' or 'small'
  export let sizePx = 0; // optional explicit pixel size override
  export let highlight = false; // glow when referenced (e.g., hovered in action queue)

  // Use granular motion settings for portrait glows
  $: motionSettings = $motionStore || { 
    globalReducedMotion: false, 
    disablePortraitGlows: false 
  };
  $: effectiveReducedMotion = reducedMotion || motionSettings.globalReducedMotion;
  $: disablePortraitGlows = motionSettings.disablePortraitGlows;

  let prevElement = fighter.element;
  let elementChanged = false;

  // Image prioritization: for phantom summons, use the original summoner's id
  // so their portrait is shown. Otherwise use summon_type (e.g., jellyfish_*),
  // falling back to the entity id.
  $: imageId = (fighter?.summon_type === 'phantom' && fighter?.summoner_id)
      ? fighter.summoner_id
      : (fighter?.summon_type || fighter?.id || '');
  $: elColor = getElementColor(fighter.element);
  $: elIcon = getElementIcon(fighter.element);
  // Make party (bottom) portraits larger for readability
  $: portraitSize = sizePx ? `${sizePx}px` : (size === 'small' ? '48px' : (size === 'medium' ? '96px' : (position === 'bottom' ? '256px' : '96px')));

  // Element-specific glow effects for different damage types
  $: elementGlow = getElementGlow(fighter.element);

  $: isLunaSwordSummon = Boolean(fighter?.lunaSword || fighter?.luna_sword);
  $: lunaSwordElement = isLunaSwordSummon ? (fighter?.lunaSwordType || fighter?.element || fighter?.damage_type) : '';
  $: lunaSwordArtUrl = isLunaSwordSummon ? (fighter?.lunaSwordArt || fighter?.luna_sword_art || '') : '';
  $: lunaSwordPalette = isLunaSwordSummon
    ? fighter?.lunaSwordPalette || getDamageTypePalette(lunaSwordElement || fighter?.element || fighter?.damage_type)
    : null;
  $: lunaSwordOverlayStyle = isLunaSwordSummon && lunaSwordPalette
    ? `--luna-sword-base:${lunaSwordPalette.base}; --luna-sword-highlight:${lunaSwordPalette.highlight}; --luna-sword-shadow:${lunaSwordPalette.shadow};`
    : '';
  $: showLunaSwordArt = Boolean(isLunaSwordSummon && lunaSwordArtUrl);

  // Rank-based outline animation (slow, subtle)
  $: rankKey = String(fighter?.rank || '').toLowerCase().trim();
  $: isPrimeRank = rankKey.includes('prime');
  $: isBossRank = rankKey.includes('boss');
  // Very slow base duration (~150s) with slight per-instance variation and offset
  const BASE_OUTLINE_SEC = 150;
  let outlineAnimDur = `${(BASE_OUTLINE_SEC * (0.88 + Math.random() * 0.24)).toFixed(2)}s`;
  let outlineAnimDelay = `${(Math.random() * BASE_OUTLINE_SEC).toFixed(2)}s`;

  $: if (fighter.element !== prevElement) {
    if (!reducedMotion) {
      elementChanged = true;
    }
    prevElement = fighter.element;
  }

  $: ultRatio = Math.max(0, Math.min(1, Number(fighter?.ultimate_charge || 0) / 15));
  $: tiltAngle = Math.min(ultRatio, 0.98) / 0.98;

  // Randomized, slow pulse timing for the ult icon
  let ultIconPulseDelay = (Math.random() * 4 + 2).toFixed(2); // 2–6s
  let ultIconPulseDur = (Math.random() * 6 + 6).toFixed(2);   // 6–12s

  function getStackCount(p) {
    const stacks = p?.stacks;
    if (typeof stacks === 'object') {
      if ('count' in stacks) return stacks.count;
      return stacks.mitigation ?? 0;
    }
    return stacks ?? 0;
  }

  // (removed ring planet layout)
  
  function getElementGlow(element) {
    switch(element?.toLowerCase()) {
      case 'fire':
        return {
          color: '#ff4444',
          effect: 'fire-glow',
          animation: 'fire-flicker'
        };
      case 'water':
      case 'ice':
        return {
          color: '#4444ff',
          effect: 'water-glow',
          animation: 'water-ripple'
        };
      case 'earth':
      case 'ground':
        return {
          color: '#8b4513',
          effect: 'earth-glow',
          animation: 'earth-pulse'
        };
      case 'air':
      case 'wind':
      case 'lightning':
        return {
          color: '#ffff44',
          effect: 'air-glow',
          animation: 'air-spark'
        };
      case 'light':
      case 'holy':
        return {
          color: '#ffffaa',
          effect: 'light-glow',
          animation: 'light-shine'
        };
      case 'dark':
      case 'shadow':
        return {
          color: '#6644aa',
          effect: 'dark-glow',
          animation: 'dark-pulse'
        };
      default:
        return {
          color: '#888888',
          effect: 'generic-glow',
          animation: 'generic-pulse'
        };
    }
  }

  $: isDead = (fighter?.hp || 0) <= 0;
  $: isPhantom = fighter?.summon_type === 'phantom';
  $: canCycle = hasCharacterGallery(imageId);
  
  // Display name for hover label
  $: displayName = (() => {
    const raw = String(fighter?.name || fighter?.id || '').trim();
    return raw.replace(/[_-]+/g, ' ');
  })();

  function resetElementChange() {
    elementChanged = false;
  }

  // Local image state to enable cross-fade when cycling gallery images
  let imageVersion = 0;
  $: basePortraitUrl = (imageVersion, getCharacterImage(imageId));
  $: portraitImageUrl = showLunaSwordArt ? lunaSwordArtUrl : basePortraitUrl;
  let fading = false;

  function cyclePortraitIfAvailable() {
    try {
      const id = imageId;
      if (!id) return;
      if (!hasCharacterGallery(id)) return;
      // Begin fade-out
      fading = true;
      const dur = 160;
      setTimeout(() => {
        // Advance to next image and re-compute
        advanceCharacterImage(id);
        imageVersion++;
        // Allow the DOM to apply the new background, then fade-in
        requestAnimationFrame(() => {
          setTimeout(() => { fading = false; }, 10);
        });
      }, dur);
    } catch {}
  }
</script>

  <div
    class="modern-fighter-card {position} {size}"
    class:dead={isDead}
    class:highlight={highlight && !isDead && !disablePortraitGlows}
    style="--portrait-size: {portraitSize}; --element-color: {elColor}; --element-glow-color: {elementGlow.color}"
  >
  <div
    class="element-wrapper"
    class:element-change={elementChanged}
    class:reduced={reducedMotion}
    on:animationend={resetElementChange}
  >
    <div
      class="fighter-portrait"
      class:can-cycle={canCycle}
      class:rank-prime={isPrimeRank}
      class:rank-boss={isBossRank}
      class:reduced={reducedMotion}
      on:click={cyclePortraitIfAvailable}
      style={`--outline-anim-dur: ${outlineAnimDur}; --outline-anim-delay: ${outlineAnimDelay};`}
    >
      <div
        class="portrait-image"
        class:element-glow={!isDead && Boolean(fighter?.ultimate_ready) && !disablePortraitGlows}
        class:reduced={effectiveReducedMotion}
        class:phantom={isPhantom && !isDead}
        class:fading={fading}
        class:luna-sword={showLunaSwordArt}
        style={`background-image: url("${portraitImageUrl}")`}
      >
      {#if showLunaSwordArt}
        <div class="luna-sword-overlay" style={lunaSwordOverlayStyle} aria-hidden="true"></div>
      {/if}
      {#if !reducedMotion && !isDead && fighter?.ultimate_ready}
        <div class="element-effect {elementGlow.effect}"></div>
      {/if}
    </div>
      <!-- Rank badge removed per design: outline subtly animates instead. -->
    <!-- Overlay UI: pips (left), passives (middle), ult gauge (right) -->
    <div class="overlay-ui">
      <!-- Old "action pips" removed to avoid confusion with passive pips. -->
      {#if (fighter.passives || []).length}
        <div class="passive-indicators" class:reduced={reducedMotion}>
          {#each fighter.passives as p (p.id)}
            {@const count = getStackCount(p)}
            <div class="passive" class:pips-mode={(p.display === 'pips' && count <= 5)} class:spinner-mode={(p.display === 'spinner')} class:number-mode={(p.display !== 'spinner' && !(p.display === 'pips' && count <= 5))}>
              {#if p.display === 'spinner'}
                <TripleRingSpinner color={elColor} duration="1.5s" {reducedMotion} />
              {:else if p.display === 'pips'}
                {#if count <= 5}
                  <div class="pips">
                    {#each Array(count) as _, i (i)}
                      <PipCircle
                        class="pip-icon filled"
                        stroke="none"
                        fill="currentColor"
                        aria-hidden="true"
                      />
                    {/each}
                  </div>
                {:else}
                  <span class="count">{count}</span>
                {/if}
              {:else}
                <span class="count">{p.max_stacks ? `${count}/${p.max_stacks}` : count}</span>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
      <div
        class="ult-gauge"
        class:ult-ready={Boolean(fighter?.ultimate_ready)}
        class:reduced={reducedMotion}
        style="--element-color: {elColor}; --p: {ultRatio}; --tilt: {tiltAngle}deg"
      aria-label="Ultimate Gauge"
      >
        <div class="ult-fill"></div>
        <svelte:component
          this={elIcon}
          class="ult-icon"
          style={`--ult-icon-pulse-delay: ${ultIconPulseDelay}s; --ult-icon-pulse-dur: ${ultIconPulseDur}s;`}
          aria-hidden="true"
        />
        {#if !fighter?.ultimate_ready}
          <div class="ult-pulse" style={`animation-duration: ${Math.max(0.4, 1.6 - 1.2 * ultRatio)}s`}></div>
        {/if}
        {#if fighter?.ultimate_ready && !disablePortraitGlows}
          <div class="ult-glow"></div>
        {/if}
      </div>
    </div>
    <!-- Hover-only name chip (bottom-left) -->
    {#if displayName}
      <div class="name-chip" aria-hidden="true">{displayName}</div>
    {/if}
    </div>
  </div>
</div>

<style>
  .modern-fighter-card {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .element-wrapper {
    display: contents;
  }

  .element-change .fighter-portrait,
  .element-change :global(.ult-icon) {
    animation: element-change 0.4s ease;
  }

  .element-wrapper.reduced .fighter-portrait,
  .element-wrapper.reduced :global(.ult-icon) {
    animation: none;
    transition: none;
  }

  @keyframes element-change {
    0% { filter: brightness(1); transform: scale(1); }
    50% { filter: brightness(1.4); transform: scale(1.05); }
    100% { filter: brightness(1); transform: scale(1); }
  }

  .fighter-portrait {
    position: relative;
    width: var(--portrait-size);
    height: var(--portrait-size);
    border-radius: 8px;
    overflow: hidden;
    background: var(--glass-bg);
    border: 2px solid var(--element-color, rgba(255, 255, 255, 0.3));
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    transition: border-color 0.3s ease;
  }
  /* Rank-based outline animations (very slow, subtle) */
  .fighter-portrait.rank-prime:not(.reduced) {
    animation: prime-outline-pulse var(--outline-anim-dur, 150s) linear infinite;
    animation-delay: var(--outline-anim-delay, 0s);
  }
  .fighter-portrait.rank-boss:not(.reduced) {
    animation: boss-outline-shift var(--outline-anim-dur, 150s) linear infinite;
    animation-delay: var(--outline-anim-delay, 0s);
  }
  @keyframes prime-outline-pulse {
    0% {
      border-color: color-mix(in oklab, var(--element-color) 85%, white 15%);
    }
    50% {
      border-color: color-mix(in oklab, var(--element-color) 100%, black 0%);
    }
    100% {
      border-color: color-mix(in oklab, var(--element-color) 85%, black 15%);
    }
  }
  @keyframes boss-outline-shift {
    0% {
      border-color: var(--element-color);
    }
    50% {
      border-color: color-mix(in oklab, var(--element-color) 10%, white 90%);
    }
    100% {
      border-color: var(--element-color);
    }
  }
  .fighter-portrait.can-cycle { cursor: pointer; }
  .fighter-portrait :global(.card-rank-badge) {
    position: absolute;
    top: clamp(0.35rem, calc(var(--portrait-size) * 0.08), 0.75rem);
    left: clamp(0.35rem, calc(var(--portrait-size) * 0.08), 0.75rem);
    pointer-events: none;
    z-index: 4;
  }

  /* External highlight (e.g., hovering the action queue) */
  .modern-fighter-card.highlight .fighter-portrait {
    border-color: color-mix(in oklab, var(--element-color) 75%, white);
    box-shadow: 0 0 12px 4px color-mix(in oklab, var(--element-color) 65%, black);
  }

  .portrait-image {
    width: 100%;
    height: 100%;
    background-size: cover;
    background-position: center;
    position: relative;
    transition: opacity 180ms ease, filter 0.3s ease;
    opacity: 1;
  }
  .portrait-image.luna-sword {
    background-repeat: no-repeat;
    filter: saturate(1.08);
  }
  .portrait-image.fading { opacity: 0; }

  .luna-sword-overlay {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-color: color-mix(in oklab, var(--luna-sword-base, rgba(255, 255, 255, 0.35)) 45%, transparent);
    background-image:
      radial-gradient(circle at 25% 20%, color-mix(in oklab, var(--luna-sword-highlight, rgba(255, 255, 255, 0.4)) 80%, transparent) 0%, transparent 55%),
      radial-gradient(circle at 78% 72%, color-mix(in oklab, var(--luna-sword-base, rgba(255, 255, 255, 0.3)) 70%, transparent) 0%, transparent 70%),
      linear-gradient(150deg, color-mix(in oklab, var(--luna-sword-base, rgba(255, 255, 255, 0.25)) 60%, transparent) 0%, color-mix(in oklab, var(--luna-sword-shadow, rgba(0, 0, 0, 0.5)) 75%, transparent) 100%);
    mix-blend-mode: screen;
    opacity: 0.78;
    transition: opacity 220ms ease;
  }

  .portrait-image.fading .luna-sword-overlay {
    opacity: 0;
  }

  .reduced .luna-sword-overlay {
    mix-blend-mode: normal;
    opacity: 0.55;
  }

  .portrait-image.element-glow {
    filter: drop-shadow(0 0 6px var(--element-glow-color));
  }

  .portrait-image.element-glow:not(.reduced) {
    transition: filter 0.2s ease-in-out;
  }

  .element-effect {
    position: absolute;
    inset: 0;
    pointer-events: none;
    opacity: 0.6;
  }

  /* Element-specific visual effects */
  .fire-glow {
    background: radial-gradient(
      circle at 50% 80%,
      rgba(255, 59, 48, 0.35) 0%,      /* iOS red */
      rgba(255, 59, 48, 0.18) 40%,
      transparent 70%
    );
    animation: fire-flicker 2s ease-in-out infinite alternate;
  }

  .water-glow {
    background: radial-gradient(circle at 50% 50%, 
      rgba(68, 68, 255, 0.3) 0%,
      rgba(100, 200, 255, 0.2) 40%,
      transparent 70%);
    animation: water-ripple 3s ease-in-out infinite;
  }

  .earth-glow {
    background: radial-gradient(circle at 50% 100%, 
      rgba(139, 69, 19, 0.3) 0%,
      rgba(160, 82, 45, 0.2) 40%,
      transparent 70%);
    animation: earth-pulse 4s ease-in-out infinite;
  }

  .air-glow {
    background: radial-gradient(circle at 50% 20%, 
      rgba(255, 255, 68, 0.3) 0%,
      rgba(255, 255, 200, 0.2) 40%,
      transparent 70%);
    animation: air-spark 1.5s ease-in-out infinite;
  }

  .light-glow {
    background: radial-gradient(circle at 50% 50%, 
      rgba(255, 255, 170, 0.4) 0%,
      rgba(255, 255, 255, 0.2) 40%,
      transparent 70%);
    animation: light-shine 3s ease-in-out infinite;
  }

  .dark-glow {
    background: radial-gradient(circle at 50% 50%, 
      rgba(102, 68, 170, 0.4) 0%,
      rgba(75, 0, 130, 0.3) 40%,
      transparent 70%);
    animation: dark-pulse 2.5s ease-in-out infinite;
  }

  .generic-glow {
    background: radial-gradient(circle at 50% 50%, 
      rgba(136, 136, 136, 0.2) 0%,
      transparent 60%);
    animation: generic-pulse 3s ease-in-out infinite;
  }

  /* Element animations */
  @keyframes fire-flicker {
    0%, 100% { 
      opacity: 0.4;
      transform: scale(1);
    }
    50% { 
      opacity: 0.7;
      transform: scale(1.05);
    }
  }

  @keyframes water-ripple {
    0%, 100% { 
      opacity: 0.3;
      transform: scale(1) rotate(0deg);
    }
    33% { 
      opacity: 0.5;
      transform: scale(1.02) rotate(1deg);
    }
    66% { 
      opacity: 0.4;
      transform: scale(0.98) rotate(-1deg);
    }
  }

  @keyframes earth-pulse {
    0%, 100% { 
      opacity: 0.2;
      transform: scale(1);
    }
    50% { 
      opacity: 0.4;
      transform: scale(1.03);
    }
  }

  @keyframes air-spark {
    0%, 100% { 
      opacity: 0.3;
      filter: brightness(1);
    }
    25% { 
      opacity: 0.6;
      filter: brightness(1.2);
    }
    75% { 
      opacity: 0.4;
      filter: brightness(1.1);
    }
  }

  @keyframes light-shine {
    0%, 100% { 
      opacity: 0.3;
      filter: brightness(1) blur(0px);
    }
    50% { 
      opacity: 0.6;
      filter: brightness(1.3) blur(1px);
    }
  }

  @keyframes dark-pulse {
    0%, 100% { 
      opacity: 0.3;
      box-shadow: inset 0 0 10px rgba(102, 68, 170, 0.3);
    }
    50% { 
      opacity: 0.5;
      box-shadow: inset 0 0 15px rgba(75, 0, 130, 0.5);
    }
  }

  @keyframes generic-pulse {
    0%, 100% { 
      opacity: 0.2;
    }
    50% { 
      opacity: 0.3;
    }
  }

  /* Overlay UI inside portrait */
  .overlay-ui {
    position: absolute;
    bottom: 4px;
    right: 4px;
    display: flex;
    align-items: flex-end;
    gap: 6px;
    pointer-events: none;
  }

  .passive-indicators {
    --pip-size: clamp(4px, calc(var(--portrait-size) * 0.09), 12px);
    --pip-gap: clamp(2px, calc(var(--portrait-size) * 0.03), 4px);
    display: flex;
    gap: 2px;
    pointer-events: none;
  }
  .passive {
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
    padding: 0 4px;
    min-width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    line-height: 1;
  }
  .passive.pips-mode {
    background: transparent;
    box-shadow: none;
    border: none;
    padding: 0;
    min-width: 0;
    height: auto;
  }
  .passive.spinner-mode {
    background: transparent;
    box-shadow: none;
    border: none;
    padding: 0;
    min-width: 0;
    height: auto;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
  }
  .passive.number-mode {
    background: rgba(0,0,0,0.35);
    box-shadow: inset 0 0 0 2px color-mix(in oklab, var(--element-color, #6cf) 60%, black);
    border: none;
    backdrop-filter: none;
    border-radius: 6px;
    padding: 0 6px;
    min-width: unset;
    height: unset;
  }
  .pips { display: flex; gap: var(--pip-gap); line-height: 0; }
  /* (removed planet-mode styles) */
  :global(.pip-icon) {
    width: var(--pip-size);
    height: var(--pip-size);
    display: block;
    color: rgba(0, 0, 0, 0.55);
    stroke: none;
    fill: currentColor;
    transition: color 0.2s;
  }
  :global(.pip-icon.filled) { color: var(--element-color); }
  .passive-indicators.reduced :global(.pip-icon) { transition: none; }
  .passive-indicators.reduced :global(.pip-icon.filled) { transform: none; }
  .count {
    font-size: clamp(0.9rem, calc(var(--portrait-size) * 0.11), 1.2rem);
    line-height: 1;
    font-weight: 900;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.9);
  }

  .pip-row {
    display: flex;
    gap: 4px;
    align-items: center;
    margin-right: 2px;
  }
  .pip {
    width: calc(var(--portrait-size) * 0.05);
    height: calc(var(--portrait-size) * 0.05);
    border-radius: 2px;
    background: rgba(255,255,255,0.25);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.2);
  }
  .pip.filled { background: color-mix(in oklab, var(--element-color, #6cf) 50%, black); }

  /* Numeric actions indicator (used by Luna, Carly, etc.) */
  .pip-number {
    position: relative;
    min-width: calc(var(--portrait-size) * 0.18);
    height: calc(var(--portrait-size) * 0.18);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: calc(var(--portrait-size) * 0.10);
    color: #fff;
    background: rgba(0,0,0,0.35);
    box-shadow: inset 0 0 0 2px color-mix(in oklab, var(--element-color, #6cf) 60%, black);
    text-shadow: 0 1px 2px rgba(0,0,0,0.9);
    pointer-events: none;
  }

  /* Ult gauge: bottom-up fill with subtle wave */
  .ult-gauge {
    position: relative;
    width: calc(var(--portrait-size) * 0.32);
    height: calc(var(--portrait-size) * 0.32);
    border-radius: 50%;
    background: rgba(0,0,0,0.35);
    overflow: hidden;
    border: 2px solid color-mix(in oklab, var(--element-color, #6cf) 60%, black);
    /* Ensure children (icon) are perfectly centered regardless of SVG internals */
    display: grid;
    place-items: center;
  }
  /* Keep gauge size consistent; only shrink the icon for summons */
  /* Soft faded-edge backdrop around the ult gauge */
  .ult-gauge::before {
    content: '';
    position: absolute;
    inset: -10px;
    border-radius: 50%;
    background: radial-gradient(
      circle at center,
      rgba(0, 0, 0, 0.55) 0%,
      rgba(0, 0, 0, 0.45) 40%,
      rgba(0, 0, 0, 0.25) 70%,
      rgba(0, 0, 0, 0.00) 100%
    );
    filter: blur(4px);
    pointer-events: none;
    z-index: -1;
  }
  .ult-fill {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: calc(var(--p, 0) * 100%);
    /* Solid single-color fill based on the element color */
    background: color-mix(in oklab, var(--element-color, #6cf) 68%, black);
    /* Make the rising fill see-through so the portrait/icon shows */
    opacity: 0.55;
    z-index: 0;
    transform-origin: bottom center;
    animation: ult-tilt 10s ease-in-out infinite;
    transition: height 0.3s ease-out;
  }
  @keyframes ult-tilt {
    0%, 100% { transform: rotate(calc(var(--tilt, 0deg) * -1)); }
    50% { transform: rotate(var(--tilt, 0deg)); }
  }
  /* Style the icon rendered by the child SVG component */
  .ult-gauge :global(.ult-icon) {
    /* Centered by the parent grid; keep relative for stacking */
    position: relative;
    width: 80%;
    height: 80%;
    color: rgba(190, 190, 190, 0.95); /* more gray */
    filter: grayscale(100%);
    opacity: 0.5; /* more transparent */
    z-index: 1;
    pointer-events: none;
    /* Prevent the SVG from shrinking oddly */
    display: block;
    transition: opacity 0.3s ease;
    transform-origin: center;
    will-change: transform, opacity;
    animation: ult-icon-pulse var(--ult-icon-pulse-dur, 9s) ease-in-out var(--ult-icon-pulse-delay, 0s) infinite alternate;
  }
  /* Normal player portraits (bottom): slightly smaller icon for balance */
  .modern-fighter-card.bottom .ult-gauge :global(.ult-icon) {
    width: 60%;
    height: 60%;
  }
  /* Summons render at medium size; shrink ult icon to 25% inside gauge */
  .modern-fighter-card.medium .ult-gauge :global(.ult-icon) {
    width: 25%;
    height: 25%;
  }
  .ult-gauge.ult-ready :global(.ult-icon) { opacity: 0.8; }
  .ult-gauge.reduced :global(.ult-icon) {
    animation: none !important;
  }
  @keyframes ult-icon-pulse {
    0% { transform: scale(1); opacity: 0.4; }
    50% { transform: scale(1.12); opacity: 0.6; }
    100% { transform: scale(1); opacity: 0.4; }
  }
  /* Breathing pulse while charging; speeds up as --p increases */
  .ult-pulse {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    pointer-events: none;
    z-index: 2;
    background: radial-gradient(circle,
      color-mix(in oklab, var(--element-color, #6cf) 30%, white) 0%,
      transparent 70%);
    opacity: 0.15;
    mix-blend-mode: screen;
    animation-name: ult-breathe;
    animation-timing-function: ease-in-out;
    animation-iteration-count: infinite;
  }
  @keyframes ult-breathe {
    0%, 100% { transform: scale(0.95); opacity: 0.12; }
    50% { transform: scale(1.05); opacity: 0.25; }
  }
  /* Soft feather at the fill boundary when not full */
  .ult-gauge:not(.ult-ready)::after {
    content: '';
    position: absolute;
    left: 0; right: 0;
    height: 14px;
    bottom: calc((var(--p, 0) * 100%) - 7px);
    background: linear-gradient(
      to top,
      color-mix(in oklab, var(--element-color, #6cf) 70%, black) 0%,
      color-mix(in oklab, var(--element-color, #6cf) 35%, black) 70%,
      rgba(0,0,0,0) 100%
    );
    filter: blur(3px);
    opacity: 0.45;
    pointer-events: none;
    transition: bottom 0.3s ease-out;
  }
  .ult-gauge.reduced .ult-fill,
  .ult-gauge.reduced:not(.ult-ready)::after {
    transition: none;
    animation: none;
  }
  .ult-ready .ult-fill { filter: drop-shadow(0 0 8px var(--element-color)); }
  .ult-glow {
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    background: radial-gradient(circle, color-mix(in oklab, var(--element-color, #6cf) 50%, white) 0%, transparent 70%);
    opacity: 0.22;
    animation: ult-pulse 1.4s ease-in-out infinite;
    z-index: 3;
  }
  @keyframes ult-pulse {
    0%, 100% { transform: scale(1); opacity: 0.25; }
    50% { transform: scale(1.08); opacity: 0.45; }
  }

  /* Dead state */
  .dead .fighter-portrait {
    opacity: 0.4;
    filter: grayscale(100%);
    /* Keep outline element-colored even when dead for consistency */
    border-color: var(--element-color, rgba(255, 255, 255, 0.3));
  }

  /* Phantom ally: subtly tinted to indicate it's a clone */
  .portrait-image.phantom {
    filter: grayscale(60%) brightness(0.92);
  }

  .dead .element-effect {
    display: none;
  }

  /* Size variants */
  .small .element-indicator {
    width: 12px;
    height: 12px;
    font-size: 6px;
  }

  /* Hover effects */
  .fighter-portrait:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  }

  .dead .fighter-portrait:hover {
    transform: none;
  }

  /* Position-specific styling removed to keep outlines element-colored */

  /* Responsive adjustments */
  @media (max-width: 600px) {
    /* No element indicator; overlay UI scales naturally */
  }

  /* Name chip styling — mirrors HP number backdrop aesthetics */
  .name-chip {
    position: absolute;
    left: 6px;
    bottom: 6px;
    color: #fff;
    font-weight: 800;
    font-size: clamp(0.7rem, calc(var(--portrait-size) * 0.10), 1rem);
    line-height: 1.05;
    padding: 2px 8px;
    border-radius: 6px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.9);
    pointer-events: none;
    opacity: 0;
    transform: translateY(2px);
    transition: opacity 120ms ease, transform 120ms ease;
    z-index: 3;
  }
  .fighter-portrait:hover .name-chip { opacity: 1; transform: translateY(0); }
  .dead .fighter-portrait:hover .name-chip { opacity: 0; }
  /* Soft faded-edge backdrop behind the name chip (same as HP number style) */
  .name-chip::before {
    content: '';
    position: absolute;
    inset: -10px;
    border-radius: 12px;
    background: radial-gradient(
      ellipse at center,
      rgba(0, 0, 0, 0.55) 0%,
      rgba(0, 0, 0, 0.50) 40%,
      rgba(0, 0, 0, 0.30) 70%,
      rgba(0, 0, 0, 0.00) 100%
    );
    filter: blur(4px);
    box-shadow: 0 0 16px rgba(0,0,0,0.3);
    z-index: -1;
    pointer-events: none;
  }
</style>
 
