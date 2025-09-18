<script>
  /**
   * Shows a portrait preview or inline upgrade mode for the selected character.
   */
  import { createEventDispatcher } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { getElementIcon, getElementColor } from '../systems/assetLoader.js';
  import { Heart, Sword, Shield, Crosshair, Zap, HeartPulse, ShieldPlus } from 'lucide-svelte';

  export let roster = [];
  export let previewId;
  export let overrideElement = '';
  export let mode = 'portrait';
  export let upgradeContext = null;
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  const UPGRADE_STATS = [
    { key: 'max_hp', label: 'HP', hint: 'Bolster survivability.' },
    { key: 'atk', label: 'ATK', hint: 'Improve offensive power.' },
    { key: 'defense', label: 'DEF', hint: 'Stiffen defenses.' },
    { key: 'crit_rate', label: 'Crit Rate', hint: 'Raise critical odds.' },
    { key: 'crit_damage', label: 'Crit DMG', hint: 'Amplify crit damage.' }
  ];
  const STAT_ICONS = {
    max_hp: Heart,
    atk: Sword,
    defense: Shield,
    crit_rate: Crosshair,
    crit_damage: Zap
  };

  $: selected = roster.find((r) => r.id === previewId);
  $: elementName = overrideElement || selected?.element || '';
  $: accent = getElementColor(elementName || 'Generic');
  $: ElementIcon = getElementIcon(elementName || 'Generic');
  $: highlightedStat = upgradeContext?.stat || upgradeContext?.lastRequestedStat || null;
  $: isLight = String(elementName || '').toLowerCase() === 'light';
  // Light "sun" layout: percentage anchors (x,y) in [0..100]
  const lightLayout = {
    hp:         { x: 50, y: 52 },
    atk:        { x: 37, y: 36 },
    def:        { x: 63, y: 36 },
    crit_rate:  { x: 26, y: 24 },
    crit_damage:{ x: 28, y: 50 },
    vit:        { x: 20, y: 42 },
    mit:        { x: 80, y: 44 },
  };

  function enterUpgrade() {
    if (!selected) return;
    dispatch('open-upgrade', { id: selected.id });
  }

  function closeUpgrade(reason = 'close') {
    if (!selected) {
      dispatch('close-upgrade', { id: null, reason });
      return;
    }
    dispatch('close-upgrade', { id: selected.id, reason });
  }

  function requestUpgrade(stat) {
    if (!selected || !stat) return;
    dispatch('request-upgrade', { id: selected.id, stat });
  }

  function handleBackgroundClick(event) {
    if (event.target !== event.currentTarget) return;
    closeUpgrade('background');
  }
</script>

<div class="preview" data-mode={mode} class:upgrade-mode={mode === 'upgrade'}>
  {#if previewId}
    {#if selected}
      {#if mode === 'portrait'}
        <div class="portrait" in:fade={{ duration: reducedMotion ? 0 : 120 }} out:fade={{ duration: reducedMotion ? 0 : 120 }}>
          <img
            src={selected.img}
            alt={selected.name}
            style={`--outline: ${getElementColor(overrideElement || selected.element)};`}
          />
          <!-- Hidden: legacy portrait-mode upgrade button -->
          <!--
          <button
            type="button"
            class="upgrade-toggle"
            on:click={enterUpgrade}
            disabled={!selected}
          >
            Upgrade stats
          </button>
          -->
        </div>
      {:else if mode === 'upgrade'}
        <div
          class="upgrade-wrapper"
          in:fade={{ duration: reducedMotion ? 0 : 120 }}
          out:fade={{ duration: reducedMotion ? 0 : 120 }}
        >
          <!-- Dimmed & blurred portrait backdrop -->
          {#if selected?.img}
            <div class="upgrade-bg" aria-hidden="true">
              <img src={selected.img} alt="" />
              <!-- Fill the photo area with a large damage-type icon -->
              <div class="element-bg" style={`color: ${accent};`}>
                <svelte:component this={ElementIcon} aria-hidden="true" />
              </div>
              <div class="vignette" />
            </div>
          {/if}
          {#if isLight}
            <!-- Light damage type layout: sun diagram with connectors -->
            <div
              class="stat-slots light"
              aria-label="Stat upgrade options (Light)"
              on:click|stopPropagation
              style={`--accent:${accent}; color:${accent}`}
            >
              <svg class="stat-links" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true" style={`color:${accent}`}>
                <!-- HP center to ATK/DEF -->
                <line x1={`${lightLayout.hp.x}`} y1={`${lightLayout.hp.y}`} x2={`${lightLayout.atk.x}`} y2={`${lightLayout.atk.y}`} stroke="currentColor" />
                <line x1={`${lightLayout.hp.x}`} y1={`${lightLayout.hp.y}`} x2={`${lightLayout.def.x}`} y2={`${lightLayout.def.y}`} stroke="currentColor" />
                <!-- ATK to children: crit rate, crit dmg, vit -->
                <line x1={`${lightLayout.atk.x}`} y1={`${lightLayout.atk.y}`} x2={`${lightLayout.crit_rate.x}`} y2={`${lightLayout.crit_rate.y}`} stroke="currentColor" />
                <line x1={`${lightLayout.atk.x}`} y1={`${lightLayout.atk.y}`} x2={`${lightLayout.crit_damage.x}`} y2={`${lightLayout.crit_damage.y}`} stroke="currentColor" />
                <line x1={`${lightLayout.atk.x}`} y1={`${lightLayout.atk.y}`} x2={`${lightLayout.vit.x}`} y2={`${lightLayout.vit.y}`} stroke="currentColor" />
                <!-- DEF to MIT -->
                <line x1={`${lightLayout.def.x}`} y1={`${lightLayout.def.y}`} x2={`${lightLayout.mit.x}`} y2={`${lightLayout.mit.y}`} stroke="currentColor" />
              </svg>

              <!-- Buttons; icons inherit accent via color -->
              <button type="button" class="stat-icon-btn" style={`left:${lightLayout.hp.x}%; top:${lightLayout.hp.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='max_hp'} on:click={() => requestUpgrade('max_hp')} aria-label="HP" title="HP — Bolster survivability.">
                <Heart aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${lightLayout.atk.x}%; top:${lightLayout.atk.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='atk'} on:click={() => requestUpgrade('atk')} aria-label="Attack" title="ATK — Improve offensive power.">
                <Sword aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${lightLayout.def.x}%; top:${lightLayout.def.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='defense'} on:click={() => requestUpgrade('defense')} aria-label="Defense" title="DEF — Stiffen defenses.">
                <Shield aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${lightLayout.crit_rate.x}%; top:${lightLayout.crit_rate.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='crit_rate'} on:click={() => requestUpgrade('crit_rate')} aria-label="Crit Rate" title="Crit Rate — Raise critical odds.">
                <Crosshair aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${lightLayout.crit_damage.x}%; top:${lightLayout.crit_damage.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='crit_damage'} on:click={() => requestUpgrade('crit_damage')} aria-label="Crit Damage" title="Crit DMG — Amplify crit damage.">
                <Zap aria-hidden="true" />
              </button>
              <!-- VIT (new) -->
              <!-- TODO: Backend: add 'vit' stat to upgrade API and totals -->
              <button type="button" class="stat-icon-btn" style={`left:${lightLayout.vit.x}%; top:${lightLayout.vit.y}%; transform:translate(-50%,-50%); color:${accent}`}
                disabled aria-disabled="true" aria-label="Vitality (coming soon)" title="Vit — backend integration pending">
                <HeartPulse aria-hidden="true" />
              </button>
              <!-- MIT (new) -->
              <!-- TODO: Backend: add 'mit' stat to upgrade API and totals -->
              <button type="button" class="stat-icon-btn" style={`left:${lightLayout.mit.x}%; top:${lightLayout.mit.y}%; transform:translate(-50%,-50%); color:${accent}`}
                disabled aria-disabled="true" aria-label="Mitigation (coming soon)" title="Mit — backend integration pending">
                <ShieldPlus aria-hidden="true" />
              </button>
            </div>
          {:else}
            <!-- Default layout: top toolbar row -->
            <div class="stat-toolbar" aria-label="Stat upgrade options" on:click|stopPropagation>
              {#each UPGRADE_STATS as stat}
                {#if STAT_ICONS[stat.key]}
                  <button
                    type="button"
                    class="stat-icon-btn"
                    class:active={highlightedStat === stat.key}
                    on:click={() => requestUpgrade(stat.key)}
                    aria-label={stat.label}
                    title={`${stat.label} — ${stat.hint}`}
                  >
                    <svelte:component this={STAT_ICONS[stat.key]} aria-hidden="true" />
                  </button>
                {/if}
              {/each}
              <!-- Extra stats available for all damage types; disabled until backend adds support -->
              <!-- TODO: Backend: add 'vit' and 'mit' to upgrade API and player stat totals -->
              <button type="button" class="stat-icon-btn" disabled aria-disabled="true" aria-label="Vitality (coming soon)" title="Vit — backend integration pending">
                <HeartPulse aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" disabled aria-disabled="true" aria-label="Mitigation (coming soon)" title="Mit — backend integration pending">
                <ShieldPlus aria-hidden="true" />
              </button>
            </div>
          {/if}
          <div
            class="upgrade-card"
            style={`--accent: ${accent};`}
            in:scale={{ duration: reducedMotion ? 0 : 160, easing: quintOut }}
            out:scale={{ duration: reducedMotion ? 0 : 120, easing: quintOut }}
          >
            <!--
              TEMPORARILY DISABLED UPGRADE MENU
              The element chip and stat buttons are commented out per request.
              We will re-enable these later.
            <div class="icon-row">
              <div class="element-chip" aria-label={`${elementName || 'Generic'} damage type`}>
                <svelte:component this={ElementIcon} aria-hidden="true" />
                <span>{elementName || 'Generic'}</span>
              </div>
            </div>
            <div class="stat-grid">
              {#each UPGRADE_STATS as stat}
                <button
                  type="button"
                  class="stat-button"
                  class:active={highlightedStat === stat.key}
                  on:click={() => requestUpgrade(stat.key)}
                >
                  <span class="label">{stat.label}</span>
                  <span class="hint">{stat.hint}</span>
                </button>
              {/each}
            </div>
            -->
          </div>
        </div>
      {/if}
    {/if}
  {:else}
    <div class="placeholder">Select up to 4 allies</div>
  {/if}
</div>

<style>
  .preview {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    min-width: 0;
    min-height: 0;
    position: relative;
  }
  .portrait {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .portrait img {
    width: auto;
    height: auto;
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border: 3px solid var(--outline, #555);
    background: #222;
    border-radius: 12px;
    box-shadow:
      0 8px 24px rgba(0,0,0,0.5),
      0 0 18px color-mix(in srgb, var(--outline, #888) 65%, transparent),
      0 0 36px color-mix(in srgb, var(--outline, #888) 35%, transparent);
    display: block;
    margin: 0 auto;
  }
  .upgrade-toggle {
    position: absolute;
    bottom: 0.75rem;
    right: 0.75rem;
    background: rgba(0,0,0,0.65);
    border: 1px solid rgba(255,255,255,0.35);
    color: #fff;
    padding: 0.35rem 0.65rem;
    border-radius: 0.5rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: transform 140ms ease, background 140ms ease;
  }
  .upgrade-toggle:hover {
    background: rgba(255,255,255,0.12);
    transform: translateY(-1px);
  }
  .upgrade-toggle:disabled {
    opacity: 0.55;
    cursor: not-allowed;
    transform: none;
  }
  .upgrade-mode .upgrade-toggle {
    display: none;
  }
  .upgrade-wrapper {
    position: relative;
    z-index: 10;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(6, 8, 12, 0.5);
    border-radius: 14px;
    overflow: hidden;
  }
  /* Backdrop with dimmed & blurred portrait */
  .upgrade-bg { position: absolute; inset: 0; z-index: 0; pointer-events: none; }
  .upgrade-bg img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: blur(10px) saturate(0.9) brightness(0.6);
    transform: scale(1.08);
  }
  .upgrade-bg .element-bg {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    /* Place above the blurred photo but below vignette */
    z-index: 1;
  }
  .upgrade-bg .element-bg :global(svg) {
    width: min(70vmin, 86%);
    height: auto;
    opacity: 0.22;
    /* Lucide icons use stroke; color controls stroke via currentColor */
    filter: blur(2px) drop-shadow(0 6px 22px rgba(0,0,0,0.45));
  }
  .upgrade-bg .vignette {
    position: absolute; inset: 0;
    background:
      radial-gradient(ellipse at 50% 35%, rgba(0,0,0,0.0), rgba(0,0,0,0.35) 60%, rgba(0,0,0,0.65) 100%),
      linear-gradient(180deg, rgba(0,0,0,0.55), rgba(0,0,0,0.55));
    pointer-events: none;
  }
  .upgrade-card {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 100%;
    max-height: 100%;
    /* Temporarily remove panel visuals to reveal background icon */
    background: transparent;
    border: none;
    border-radius: 14px;
    padding: 0;
    box-shadow: none;
    display: flex;
    flex-direction: column;
    gap: 0;
    /* Let background clicks pass through; re-enable on specific children */
    pointer-events: none;
  }
  /* Positioned stat slots for Light element */
  .stat-slots { position: absolute; inset: 0; z-index: 3; pointer-events: none; }
  .stat-slots .stat-icon-btn { position: absolute; pointer-events: auto; z-index: 1; }
  .stat-links { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; color: var(--accent, #6ab); z-index: 0; }
  .stat-links line {
    /* Much thinner and significantly darker mix of the element color */
    stroke: color-mix(in srgb, currentColor 30%, #000000);
    stroke-width: 0.45;
    stroke-linecap: round;
    opacity: 0.85;
    filter: none;
  }
  .stat-icon-btn:disabled { opacity: 0.55; cursor: not-allowed; }
  .close {
    position: absolute;
    top: 0.5rem;
    right: 0.6rem;
    width: 1.6rem;
    height: 1.6rem;
    border-radius: 50%;
    border: 1px solid rgba(255,255,255,0.35);
    background: rgba(0,0,0,0.4);
    color: #fff;
    font-size: 1.1rem;
    line-height: 1;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    /* Re-enable pointer events for the close button */
    pointer-events: auto;
  }
  .close:hover {
    background: rgba(255,255,255,0.15);
  }
  .icon-row {
    display: flex;
    justify-content: center;
    margin-top: 0.25rem;
  }
  .element-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.4rem 0.8rem;
    border-radius: 999px;
    background: color-mix(in srgb, var(--accent, #6ab) 25%, rgba(0,0,0,0.65));
    color: color-mix(in srgb, var(--accent, #6ab) 90%, #fff);
    border: 1px solid color-mix(in srgb, var(--accent, #6ab) 40%, rgba(255,255,255,0.35));
    font-size: 0.9rem;
  }
  .element-chip svg {
    width: 1.4rem;
    height: 1.4rem;
  }
  .stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(7.5rem, 1fr));
    gap: 0.6rem;
  }
  .stat-button {
    background: rgba(0,0,0,0.55);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 0.65rem;
    padding: 0.75rem 0.65rem;
    color: #e6ecff;
    text-align: left;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    transition: transform 140ms ease, border-color 140ms ease, background 140ms ease;
  }
  .stat-button:hover {
    transform: translateY(-1px);
    border-color: color-mix(in srgb, var(--accent, #6ab) 55%, rgba(255,255,255,0.35));
    background: color-mix(in srgb, var(--accent, #6ab) 25%, rgba(0,0,0,0.55));
  }
  .stat-button.active {
    border-color: color-mix(in srgb, var(--accent, #6ab) 65%, rgba(255,255,255,0.5));
    background: color-mix(in srgb, var(--accent, #6ab) 30%, rgba(0,0,0,0.65));
  }
  .stat-button .label {
    font-weight: 600;
    letter-spacing: 0.04em;
  }
  .stat-button .hint {
    font-size: 0.75rem;
    color: rgba(220,228,255,0.75);
  }
  .placeholder {
    color: #888;
    font-style: italic;
  }
  /* Top stat toolbar */
  .stat-toolbar {
    position: absolute;
    top: 0.75rem;
    left: 50%;
    transform: translateX(-50%);
    display: inline-flex;
    gap: 0.5rem;
    padding: 0;            /* remove grouped background padding */
    border-radius: 999px;  /* harmless with transparent background */
    background: transparent; /* remove grouped background */
    border: none;            /* remove grouped border */
    box-shadow: none;        /* remove grouped shadow */
    pointer-events: auto;
    z-index: 2;
  }
  .stat-icon-btn {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(0,0,0,0.55);
    color: color-mix(in srgb, var(--accent, #6ab) 90%, #ffffff);
    border: 1px solid color-mix(in srgb, var(--accent, #6ab) 40%, rgba(255,255,255,0.35));
    transition: transform 140ms ease, background 140ms ease, border-color 140ms ease;
    cursor: pointer;
    pointer-events: auto;
  }
  .stat-icon-btn:hover,
  .stat-icon-btn:focus-visible {
    transform: translateY(-1px);
    background: color-mix(in srgb, var(--accent, #6ab) 25%, rgba(0,0,0,0.55));
    border-color: color-mix(in srgb, var(--accent, #6ab) 55%, rgba(255,255,255,0.35));
    outline: none;
  }
  .stat-icon-btn.active {
    background: color-mix(in srgb, var(--accent, #6ab) 30%, rgba(0,0,0,0.65));
    border-color: color-mix(in srgb, var(--accent, #6ab) 65%, rgba(255,255,255,0.5));
  }
  .stat-icon-btn :global(svg) {
    width: 22px;
    height: 22px;
    filter: drop-shadow(0 1px 2px rgba(0,0,0,0.4));
  }
  @media (prefers-reduced-motion: reduce) {
    .upgrade-toggle,
    .stat-button {
      transition: none;
    }
  }
</style>
