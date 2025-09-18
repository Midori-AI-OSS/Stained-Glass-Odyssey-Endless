<script>
  /**
   * Shows a portrait preview or inline upgrade mode for the selected character.
   */
  import { createEventDispatcher } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { getElementIcon, getElementColor } from '../systems/assetLoader.js';
  import { savePlayerConfig } from '../systems/api.js';
  import { Heart, Sword, Shield, Crosshair, Zap, HeartPulse, ShieldPlus } from 'lucide-svelte';
  import { formatPoints, formatCost, formatPercent } from '../utils/upgradeFormatting.js';

  export let roster = [];
  export let previewId;
  export let overrideElement = '';
  export let mode = 'portrait';
  export let upgradeContext = null;
  export let upgradeData = null;
  export let upgradeLoading = false;
  export let upgradeError = null;
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();
  const ELEMENTS = ['Light','Fire','Ice','Lightning','Wind','Dark'];
  async function chooseElement(name) {
    const s = String(name || '');
    const pretty = s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : '';
    try {
      if (pretty) await savePlayerConfig({ damage_type: pretty });
      try { dispatch('element-change', { element: pretty }); } catch {}
    } catch (e) {
      // overlay shown by http layer
    }
  }

  const UPGRADE_STATS = [
    { key: 'max_hp', label: 'HP', hint: 'Bolster survivability.' },
    { key: 'atk', label: 'ATK', hint: 'Improve offensive power.' },
    { key: 'defense', label: 'DEF', hint: 'Stiffen defenses.' },
    { key: 'crit_rate', label: 'Crit Rate', hint: 'Raise critical odds.' },
    { key: 'crit_damage', label: 'Crit DMG', hint: 'Amplify crit damage.' },
    { key: 'vitality', label: 'Vitality', hint: 'Extend buff durations & recovery.' },
    { key: 'mitigation', label: 'Mitigation', hint: 'Soften incoming damage.' }
  ];
  const STAT_ICONS = {
    max_hp: Heart,
    atk: Sword,
    defense: Shield,
    crit_rate: Crosshair,
    crit_damage: Zap,
    vitality: HeartPulse,
    mitigation: ShieldPlus
  };
  let convertStar = 1;
  let convertCount = 1;

  $: selected = roster.find((r) => r.id === previewId);
  $: elementName = overrideElement || selected?.element || '';
  $: accent = getElementColor(elementName || 'Generic');
  $: ElementIcon = getElementIcon(elementName || 'Generic');
  $: pendingStat = upgradeContext?.pendingStat || null;
  $: highlightedStat =
    pendingStat || upgradeContext?.stat || upgradeContext?.lastRequestedStat || null;
  $: upgradeItems = upgradeData?.items || {};
  $: upgradePointsValue = upgradeData?.upgrade_points;
  $: upgradeTotals = upgradeData?.stat_totals || {};
  $: upgradeCosts = upgradeData?.next_costs || {};
  $: upgradeErrorMessage = upgradeError ? (upgradeError.message || String(upgradeError)) : '';
  $: convertStarNum = Math.min(4, Math.max(1, Number(convertStar) || 1));
  $: convertCountNum = Math.max(1, Number(convertCount) || 1);
  $: availableAtStar = computeAvailable(convertStarNum);
  $: pendingConversion = Boolean(upgradeContext?.pendingConversion);
  $: pendingAction = Boolean(upgradeContext?.pendingStat || upgradeContext?.pendingConversion);
  $: canConvert = Boolean(upgradeData && !upgradeLoading && !pendingAction && availableAtStar >= convertCountNum && convertCountNum > 0);
  function statLabel(stat) {
    if (!stat) return '';
    const match = UPGRADE_STATS.find((s) => s.key === stat);
    if (match) return match.label;
    const pretty = String(stat).replace(/_/g, ' ').trim();
    return pretty ? pretty.replace(/\b\w/g, (c) => c.toUpperCase()) : stat;
  }

  function computeAvailable(starLevel) {
    if (!selected) return 0;
    const star = Math.max(1, Math.min(4, Number(starLevel) || 0));
    if (!star) return 0;
    if (selected.is_player) {
      return Object.entries(upgradeItems)
        .filter(([key]) => key.endsWith(`_${star}`))
        .reduce((acc, [, value]) => acc + (Number(value) || 0), 0);
    }
    const key = `${String(elementName || 'generic').toLowerCase()}_${star}`;
    return Number(upgradeItems[key]) || 0;
  }

  function formatStatTotal(value) {
    if (value == null) return '—';
    return formatPercent(value);
  }
  // Sun layout: baseline positions (percentages) we will copy to each element
  const sunLayout = {
    hp:         { x: 50, y: 52 },
    atk:        { x: 37, y: 36 },
    def:        { x: 63, y: 36 },
    crit_rate:  { x: 26, y: 24 },
    crit_damage:{ x: 28, y: 50 },
    vitality:   { x: 20, y: 42 },
    mitigation: { x: 80, y: 44 },
  };
  // Per-damage-type layout map — start with copies of sunLayout for each
  function clone(o){ return JSON.parse(JSON.stringify(o)); }
  const baseLayouts = {
    light: clone(sunLayout),
    fire: clone(sunLayout),
    ice: clone(sunLayout),
    lightning: clone(sunLayout),
    dark: clone(sunLayout),
    wind: clone(sunLayout),
    generic: clone(sunLayout)
  };
  $: elementKey = String(elementName || 'generic').toLowerCase();
  function deg2rad(d){ return (Math.PI/180) * d; }
  function makeOrbLayout(base, radius = 18, order = ['atk','def','crit_rate','crit_damage','vitality','mitigation'], startDeg = -90) {
    const layout = clone(base);
    const cx = base.hp.x;
    const cy = base.hp.y;
    for (let i = 0; i < order.length; i++) {
      const ang = deg2rad(startDeg + i * (360 / order.length));
      layout[order[i]] = {
        x: cx + radius * Math.cos(ang),
        y: cy + radius * Math.sin(ang)
      };
    }
    return layout;
  }
  function makeLightningLayout(base) {
    const layout = clone(base);
    // Top-down zig-zag bolt path
    layout.hp           = { x: 50, y: 12 };
    layout.atk          = { x: 34, y: 26 };
    layout.def          = { x: 64, y: 38 };
    layout.crit_rate    = { x: 30, y: 52 };
    layout.crit_damage  = { x: 60, y: 64 };
    layout.vitality     = { x: 28, y: 78 };
    layout.mitigation   = { x: 58, y: 88 };
    return layout;
  }
  function makeFireLayout(base) {
    const layout = clone(base);
    // Teardrop flame silhouette: HP near base, tip at top
    layout.hp           = { x: 50, y: 78 };
    layout.atk          = { x: 42, y: 66 };
    layout.crit_rate    = { x: 36, y: 52 };
    layout.crit_damage  = { x: 42, y: 38 };
    layout.mitigation   = { x: 50, y: 24 }; // flame tip
    layout.def          = { x: 58, y: 40 };
    layout.vitality     = { x: 64, y: 56 };
    return layout;
  }
  function makeDarkLayout(base) {
    const layout = clone(base);
    // Crescent moon: points along a left-side arc, gap on the upper-right
    const cx = 48, cy = 52, r = 22;
    // Rotate anticlockwise by ~20 degrees (screen coordinates: decrease deg)
    const rot = -20;
    const pos = (deg) => ({ x: cx + r * Math.cos(deg2rad(deg + rot)), y: cy + r * Math.sin(deg2rad(deg + rot)) });
    layout.hp          = { x: 44, y: 52 };         // slightly left of center
    layout.def         = pos(110);  // upper-left
    layout.vitality    = pos(145);
    layout.crit_damage = pos(180);
    layout.mitigation  = pos(215);
    layout.crit_rate   = pos(240);
    layout.atk         = pos(265);  // lower-left
    return layout;
  }
  function makeIceLayout(base) {
    const layout = clone(base);
    // Six-armed snowflake around HP center
    const cx = 50, cy = 52, r = 22;
    const order = ['atk','crit_rate','def','mitigation','crit_damage','vitality'];
    for (let i = 0; i < order.length; i++) {
      const ang = deg2rad(-90 + i * 60); // start at top, go clockwise
      layout[order[i]] = { x: cx + r * Math.cos(ang), y: cy + r * Math.sin(ang) };
    }
    layout.hp = { x: cx, y: cy };
    return layout;
  }
  const ICE_KEYS = ['atk','crit_rate','def','mitigation','crit_damage','vitality'];
  function computeIceSpikes(layout) {
    const spikes = {};
    const cx = layout.hp.x, cy = layout.hp.y;
    for (let i = 0; i < ICE_KEYS.length; i++) {
      const k = ICE_KEYS[i];
      const n = layout[k];
      if (!n) continue;
      // Place short spikes in a small ring around the icon, not just outward
      const count = 4 + ((i * 2) % 5); // 4..8
      const length = 6; // shorter, closer to the icon
      const offset = deg2rad((i * 37) % 360); // deterministic rotation per node
      const arr = [];
      for (let j = 0; j < count; j++) {
        const ang = offset + (j * (2 * Math.PI / count)); // full circle around the node
        arr.push({ x: n.x + length * Math.cos(ang), y: n.y + length * Math.sin(ang) });
      }
      spikes[k] = arr;
    }
    return spikes;
  }
  $: currentLayout =
    elementKey === 'light'
      ? makeOrbLayout(baseLayouts.light)
      : elementKey === 'lightning'
        ? makeLightningLayout(baseLayouts.lightning)
        : elementKey === 'fire'
          ? makeFireLayout(baseLayouts.fire)
          : elementKey === 'dark'
            ? makeDarkLayout(baseLayouts.dark)
            : elementKey === 'ice'
              ? makeIceLayout(baseLayouts.ice)
            : (baseLayouts[elementKey] || baseLayouts.generic);
  $: iceSpikes = elementKey === 'ice' ? computeIceSpikes(currentLayout) : null;
  const PERIPH_KEYS = ['atk','def','crit_rate','crit_damage','vitality','mitigation'];
  function computeRingEdges(layout, keys) {
    const cx = layout.hp.x, cy = layout.hp.y;
    const pts = keys
      .filter((k) => layout[k])
      .map((k) => ({ k, a: Math.atan2(layout[k].y - cy, layout[k].x - cx) }));
    pts.sort((p, q) => p.a - q.a);
    const edges = [];
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i].k;
      const b = pts[(i + 1) % pts.length].k; // close the ring
      edges.push([a, b]);
    }
    return edges;
  }
  $: ringEdges = elementKey === 'light' ? computeRingEdges(currentLayout, PERIPH_KEYS) : [];

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
    if (!selected || !stat || pendingAction) return;
    dispatch('request-upgrade', { id: selected.id, stat });
  }

  function convertItems() {
    if (!selected || !canConvert) return;
    dispatch('request-convert', { id: selected.id, starLevel: convertStarNum, itemCount: convertCountNum });
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
          <!-- Upgrade button moved next to Add/Remove in StatTabs -->
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
          <!-- Element selector toolbar -->
          <div class="element-toolbar" on:click|stopPropagation>
            {#each ELEMENTS as el}
              {#key el}
                <button type="button" class="element-btn" class:active={String(elementName).toLowerCase() === el.toLowerCase()}
                  aria-label={`Set element ${el}`}
                  style={`--el:${getElementColor(el)}; color:${getElementColor(el)}`}
                  on:click={() => chooseElement(el)}
                >
                  <svelte:component this={getElementIcon(el)} aria-hidden="true" />
                </button>
              {/key}
            {/each}
          </div>
          <!-- Sun layout: used for all damage types for now -->
          <div
            class="stat-slots"
            aria-label="Stat upgrade options"
            aria-busy={pendingStat ? 'true' : undefined}
            on:click|stopPropagation
            style={`--accent:${accent}; color:${accent}`}
          >
               <svg class="stat-links" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true" style={`color:${accent}`}>
                {#if elementKey === 'light'}
                  <!-- Hub links: connect HP to every stat -->
                  {#each PERIPH_KEYS as k}
                    <line x1={`${currentLayout.hp.x}`} y1={`${currentLayout.hp.y}`} x2={`${currentLayout[k].x}`} y2={`${currentLayout[k].y}`} stroke="currentColor" />
                  {/each}
                  <!-- Ring links: connect stats around in a circle -->
                  {#each ringEdges as e}
                    <line x1={`${currentLayout[e[0]].x}`} y1={`${currentLayout[e[0]].y}`} x2={`${currentLayout[e[1]].x}`} y2={`${currentLayout[e[1]].y}`} stroke="currentColor" />
                  {/each}
                {:else if elementKey === 'lightning'}
                  <!-- Lightning: sequential zig-zag from HP through all stats -->
                  {#each ['hp','atk','def','crit_rate','crit_damage','vitality','mitigation'] as key, i}
                    {#if i < 6}
                      <line x1={`${currentLayout[key].x}`} y1={`${currentLayout[key].y}`} x2={`${currentLayout[['atk','def','crit_rate','crit_damage','vitality','mitigation'][i]].x}`} y2={`${currentLayout[['atk','def','crit_rate','crit_damage','vitality','mitigation'][i]].y}`} stroke="currentColor" />
                    {/if}
                  {/each}
                {:else if elementKey === 'ice'}
                  <!-- Ice: spokes from HP; each outer node emits multiple short spikes -->
                  {#each ICE_KEYS as k}
                    <line x1={`${currentLayout.hp.x}`} y1={`${currentLayout.hp.y}`} x2={`${currentLayout[k].x}`} y2={`${currentLayout[k].y}`} stroke="currentColor" />
                    {#each iceSpikes?.[k] || [] as p}
                      <line x1={`${currentLayout[k].x}`} y1={`${currentLayout[k].y}`} x2={`${p.x}`} y2={`${p.y}`} stroke="currentColor" />
                    {/each}
                  {/each}
                {:else if elementKey === 'fire'}
                  <!-- Fire: flame outline from base (HP) up to tip and back around -->
                  {#each ['hp','atk','crit_rate','crit_damage','mitigation','def','vitality','hp'] as key, i}
                    {#if i < 7}
                      <line x1={`${currentLayout[key].x}`} y1={`${currentLayout[key].y}`} x2={`${currentLayout[['atk','crit_rate','crit_damage','mitigation','def','vitality','hp'][i]].x}`} y2={`${currentLayout[['atk','crit_rate','crit_damage','mitigation','def','vitality','hp'][i]].y}`} stroke="currentColor" />
                    {/if}
                  {/each}
                {:else if elementKey === 'dark'}
                  <!-- Dark: crescent moon. Hub links from HP to ATK and DEF; arc around left side -->
                  <line x1={`${currentLayout.hp.x}`} y1={`${currentLayout.hp.y}`} x2={`${currentLayout.atk.x}`} y2={`${currentLayout.atk.y}`} stroke="currentColor" />
                  <line x1={`${currentLayout.hp.x}`} y1={`${currentLayout.hp.y}`} x2={`${currentLayout.def.x}`} y2={`${currentLayout.def.y}`} stroke="currentColor" />
                  {#each ['def','vitality','crit_damage','mitigation','crit_rate','atk'] as a, i}
                    {#if i < 5}
                      <line x1={`${currentLayout[a].x}`} y1={`${currentLayout[a].y}`} x2={`${currentLayout[['vitality','crit_damage','mitigation','crit_rate','atk','def'][i]].x}`} y2={`${currentLayout[['vitality','crit_damage','mitigation','crit_rate','atk','def'][i]].y}`} stroke="currentColor" />
                    {/if}
                  {/each}
                {:else}
                  <!-- Default hub/branch pattern (previous behavior) -->
                  <line x1={`${currentLayout.hp.x}`} y1={`${currentLayout.hp.y}`} x2={`${currentLayout.atk.x}`} y2={`${currentLayout.atk.y}`} stroke="currentColor" />
                  <line x1={`${currentLayout.hp.x}`} y1={`${currentLayout.hp.y}`} x2={`${currentLayout.def.x}`} y2={`${currentLayout.def.y}`} stroke="currentColor" />
                  <line x1={`${currentLayout.atk.x}`} y1={`${currentLayout.atk.y}`} x2={`${currentLayout.crit_rate.x}`} y2={`${currentLayout.crit_rate.y}`} stroke="currentColor" />
                  <line x1={`${currentLayout.atk.x}`} y1={`${currentLayout.atk.y}`} x2={`${currentLayout.crit_damage.x}`} y2={`${currentLayout.crit_damage.y}`} stroke="currentColor" />
                  <line x1={`${currentLayout.atk.x}`} y1={`${currentLayout.atk.y}`} x2={`${currentLayout.vitality.x}`} y2={`${currentLayout.vitality.y}`} stroke="currentColor" />
                  <line x1={`${currentLayout.def.x}`} y1={`${currentLayout.def.y}`} x2={`${currentLayout.mitigation.x}`} y2={`${currentLayout.mitigation.y}`} stroke="currentColor" />
                {/if}
               </svg>

              <!-- Buttons; icons inherit accent via color -->
              <button type="button" class="stat-icon-btn" style={`left:${currentLayout.hp.x}%; top:${currentLayout.hp.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='max_hp'} disabled={pendingAction} on:click={() => requestUpgrade('max_hp')} aria-label="HP" title="HP — Bolster survivability.">
                <Heart aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${currentLayout.atk.x}%; top:${currentLayout.atk.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='atk'} disabled={pendingAction} on:click={() => requestUpgrade('atk')} aria-label="Attack" title="ATK — Improve offensive power.">
                <Sword aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${currentLayout.def.x}%; top:${currentLayout.def.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='defense'} disabled={pendingAction} on:click={() => requestUpgrade('defense')} aria-label="Defense" title="DEF — Stiffen defenses.">
                <Shield aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${currentLayout.crit_rate.x}%; top:${currentLayout.crit_rate.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='crit_rate'} disabled={pendingAction} on:click={() => requestUpgrade('crit_rate')} aria-label="Crit Rate" title="Crit Rate — Raise critical odds.">
                <Crosshair aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${currentLayout.crit_damage.x}%; top:${currentLayout.crit_damage.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='crit_damage'} disabled={pendingAction} on:click={() => requestUpgrade('crit_damage')} aria-label="Crit Damage" title="Crit DMG — Amplify crit damage.">
                <Zap aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${currentLayout.vitality.x}%; top:${currentLayout.vitality.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='vitality'} disabled={!!pendingStat} on:click={() => requestUpgrade('vitality')} aria-label="Vitality" title="Vitality — Extend buff durations & recovery.">
                <HeartPulse aria-hidden="true" />
              </button>
              <button type="button" class="stat-icon-btn" style={`left:${currentLayout.mitigation.x}%; top:${currentLayout.mitigation.y}%; transform:translate(-50%,-50%); color:${accent}`}
                class:active={highlightedStat==='mitigation'} disabled={!!pendingStat} on:click={() => requestUpgrade('mitigation')} aria-label="Mitigation" title="Mitigation — Soften incoming damage.">
                <ShieldPlus aria-hidden="true" />
              </button>
          </div>
          <div
            class="upgrade-card"
            style={`--accent: ${accent};`}
            in:scale={{ duration: reducedMotion ? 0 : 160, easing: quintOut }}
            out:scale={{ duration: reducedMotion ? 0 : 120, easing: quintOut }}
          >
            <div class="upgrade-feedback" role="status" aria-live="polite">
              {#if pendingStat}
                <p class="upgrade-status pending">Upgrading {statLabel(pendingStat)}…</p>
              {:else if pendingConversion}
                <p class="upgrade-status pending">Converting items…</p>
              {:else if upgradeContext?.error}
                <p class="upgrade-status error">{upgradeContext.error}</p>
              {:else if upgradeContext?.message}
                <p class="upgrade-status success">{upgradeContext.message}</p>
              {/if}
            </div>
            <div class="upgrade-summary" aria-live="polite">
              {#if upgradeLoading}
                <p class="upgrade-note">Loading upgrade data…</p>
              {:else if upgradeData}
                {#if upgradeErrorMessage}
                  <p class="upgrade-status error">{upgradeErrorMessage}</p>
                {/if}
                <div class="points-row">
                  <span class="points-label">Upgrade points</span>
                  <span class="points-value">{formatPoints(upgradePointsValue)}</span>
                </div>
                <div class="stat-upgrade-grid">
                  {#each UPGRADE_STATS as stat}
                    <div class="stat-upgrade-row">
                      <span class="stat-upgrade-label">{stat.label}</span>
                      <span class="stat-upgrade-total" data-label="Total">{formatStatTotal(upgradeTotals[stat.key])}</span>
                      <span class="stat-upgrade-cost" data-label="Next">{formatCost(upgradeCosts[stat.key])}</span>
                    </div>
                  {/each}
                </div>
                <div class="conversion-section">
                  <div class="conversion-header">Convert items to points</div>
                  <div class="conversion-form">
                    <label class="conversion-field">
                      <span>Star</span>
                      <select bind:value={convertStar} disabled={pendingAction || upgradeLoading}>
                        <option value={1}>1★</option>
                        <option value={2}>2★</option>
                        <option value={3}>3★</option>
                        <option value={4}>4★</option>
                      </select>
                    </label>
                    <label class="conversion-field">
                      <span>Count</span>
                      <input type="number" min="1" step="1" bind:value={convertCount} disabled={pendingAction || upgradeLoading} />
                    </label>
                    <button type="button" class="convert-btn" on:click={convertItems} disabled={!canConvert}>
                      Convert
                    </button>
                  </div>
                  <div class="conversion-note">
                    <span>Available {convertStarNum}★: {availableAtStar}</span>
                    {#if availableAtStar < convertCountNum}
                      <span class="conversion-warning">Need {convertCountNum}</span>
                    {/if}
                  </div>
                  <div class="conversion-note">
                    {selected?.is_player
                      ? 'Player can convert any element items.'
                      : `Requires ${elementName || 'Generic'} items.`}
                  </div>
                </div>
              {:else if upgradeErrorMessage}
                <p class="upgrade-status error">{upgradeErrorMessage}</p>
              {:else}
                <p class="upgrade-note">Upgrade data unavailable.</p>
              {/if}
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
  .upgrade-feedback {
    pointer-events: none;
    display: flex;
    justify-content: center;
    padding: 0.75rem 0 0.5rem;
    min-height: 2.2rem;
  }
  .upgrade-status {
    margin: 0;
    font-size: 0.95rem;
    text-align: center;
    color: rgba(255,255,255,0.88);
    text-shadow: 0 2px 6px rgba(0,0,0,0.5);
  }
  .upgrade-status.success { color: #d7f3ff; }
  .upgrade-status.error { color: #ffc4c4; }
  .upgrade-status.pending { color: #ffecb5; }
  .upgrade-status.hint { color: rgba(255,255,255,0.65); }
  .upgrade-summary {
    pointer-events: auto;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0 0.85rem 0.85rem;
  }
  .upgrade-note {
    margin: 0;
    font-size: 0.85rem;
    color: rgba(230,236,255,0.8);
    text-align: center;
  }
  .points-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    background: rgba(0,0,0,0.45);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 0.65rem;
    padding: 0.55rem 0.75rem;
  }
  .points-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(240,246,255,0.65);
  }
  .points-value {
    font-size: 1.05rem;
    font-weight: 600;
    color: #f1f5ff;
  }
  .stat-upgrade-grid {
    display: grid;
    gap: 0.45rem;
  }
  .stat-upgrade-row {
    display: grid;
    grid-template-columns: 1fr auto auto;
    align-items: center;
    gap: 0.45rem;
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 0.55rem;
    padding: 0.45rem 0.6rem;
  }
  .stat-upgrade-label {
    font-weight: 600;
    color: #f0f6ff;
    letter-spacing: 0.04em;
  }
  .stat-upgrade-total,
  .stat-upgrade-cost {
    font-size: 0.85rem;
    color: rgba(220,228,255,0.85);
    text-align: right;
  }
  .stat-upgrade-total::before,
  .stat-upgrade-cost::before {
    content: attr(data-label);
    display: block;
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(220,228,255,0.55);
  }
  .conversion-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding-top: 0.65rem;
    border-top: 1px solid rgba(255,255,255,0.12);
  }
  .conversion-header {
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(236,242,255,0.8);
  }
  .conversion-form {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: flex-end;
  }
  .conversion-field {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-size: 0.78rem;
    color: rgba(228,234,255,0.75);
  }
  .conversion-field select,
  .conversion-field input {
    background: rgba(0,0,0,0.55);
    color: #f5f9ff;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 0.5rem;
    padding: 0.35rem 0.55rem;
    min-width: 4.5rem;
  }
  .conversion-field select:focus,
  .conversion-field select:focus-visible,
  .conversion-field input:focus,
  .conversion-field input:focus-visible {
    outline: none;
    border-color: color-mix(in srgb, var(--accent, #6ab) 45%, rgba(255,255,255,0.35));
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent, #6ab) 25%, transparent);
  }
  .conversion-field select:disabled,
  .conversion-field input:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
  .convert-btn {
    background: color-mix(in srgb, var(--accent, #6ab) 25%, rgba(0,0,0,0.6));
    border: 1px solid color-mix(in srgb, var(--accent, #6ab) 55%, rgba(255,255,255,0.35));
    color: #f5f9ff;
    border-radius: 0.55rem;
    padding: 0.45rem 0.85rem;
    cursor: pointer;
    transition: transform 140ms ease, background 140ms ease, border-color 140ms ease;
    pointer-events: auto;
  }
  .convert-btn:hover:enabled {
    transform: translateY(-1px);
    background: color-mix(in srgb, var(--accent, #6ab) 40%, rgba(0,0,0,0.55));
  }
  .convert-btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
    transform: none;
  }
  .conversion-note {
    font-size: 0.75rem;
    color: rgba(220,228,255,0.75);
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
  }
  .conversion-warning {
    color: #ffc4c4;
  }
  /* Element select toolbar */
  .element-toolbar {
    position: absolute;
    top: 0.5rem;
    left: 50%;
    transform: translateX(-50%);
    display: inline-flex;
    gap: 0.35rem;
    z-index: 3;
    pointer-events: auto;
  }
  .element-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(0,0,0,0.55);
    border: 1px solid color-mix(in srgb, var(--el) 55%, rgba(255,255,255,0.35));
    box-shadow: 0 2px 8px rgba(0,0,0,0.35);
    cursor: pointer;
  }
  .element-btn.active { box-shadow: inset 0 0 0 2px var(--el); }
  .element-btn :global(svg) { width: 18px; height: 18px; }
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
 
