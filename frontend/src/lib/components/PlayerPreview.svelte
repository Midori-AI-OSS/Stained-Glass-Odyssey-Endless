<script>
  /**
   * Shows a portrait preview or inline upgrade mode for the selected character.
   */
  import { createEventDispatcher } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { getElementIcon, getElementColor } from '../systems/assetLoader.js';

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

  $: selected = roster.find((r) => r.id === previewId);
  $: elementName = overrideElement || selected?.element || '';
  $: accent = getElementColor(elementName || 'Generic');
  $: ElementIcon = getElementIcon(elementName || 'Generic');
  $: highlightedStat = upgradeContext?.stat || upgradeContext?.lastRequestedStat || null;

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
          <button
            type="button"
            class="upgrade-toggle"
            on:click={enterUpgrade}
            disabled={!selected}
          >
            Upgrade stats
          </button>
        </div>
      {:else if mode === 'upgrade'}
        <div
          class="upgrade-wrapper"
          on:click={handleBackgroundClick}
          in:fade={{ duration: reducedMotion ? 0 : 120 }}
          out:fade={{ duration: reducedMotion ? 0 : 120 }}
        >
          <div
            class="upgrade-card"
            style={`--accent: ${accent};`}
            in:scale={{ duration: reducedMotion ? 0 : 160, easing: quintOut }}
            out:scale={{ duration: reducedMotion ? 0 : 120, easing: quintOut }}
          >
            <button class="close" type="button" aria-label="Return to portrait" on:click={() => closeUpgrade('button')}>
              ×
            </button>
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
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(6, 8, 12, 0.72);
    border-radius: 14px;
  }
  .upgrade-card {
    position: relative;
    width: 100%;
    max-width: 100%;
    max-height: 100%;
    background: rgba(12,14,20,0.92);
    border: 2px solid color-mix(in srgb, var(--accent, #6ab) 30%, rgba(255,255,255,0.35));
    border-radius: 14px;
    padding: 1rem;
    box-shadow:
      0 12px 30px rgba(0,0,0,0.55),
      0 0 24px color-mix(in srgb, var(--accent, #6ab) 40%, transparent);
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }
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
  @media (prefers-reduced-motion: reduce) {
    .upgrade-toggle,
    .stat-button {
      transition: none;
    }
  }
</style>
