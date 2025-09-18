<script>
  import { onMount } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  import { writable } from 'svelte/store';
  import { getPlayers, getUpgrade, upgradeCharacter, upgradeStat } from '../systems/api.js';
  import { getCharacterImage, getRandomFallback, getElementColor } from '../systems/assetLoader.js';
  import MenuPanel from './MenuPanel.svelte';
  import PartyRoster from './PartyRoster.svelte';
  import PlayerPreview from './PlayerPreview.svelte';
  import StatTabs from './StatTabs.svelte';
  import { browser, dev } from '$app/environment';

  let roster = [];
  let userBuffPercent = 0;

  export let selected = [];
  export let compact = false;
  let previewId;
  export let reducedMotion = false;
  // Label for the primary action; overlays set this to "Save Party" or "Start Run"
  export let actionLabel = 'Save Party';
  // Pressure level for run difficulty
  let pressure = 0;
  const dispatch = createEventDispatcher();
  let previewElementOverride = '';
  const previewMode = writable('portrait');
  let upgradeContext = null;
  let lastPreviewedId = null;
  let upgradeCache = {};
  let upgradeTokens = {};
  const EMPTY_UPGRADE_STATE = { data: null, loading: false, error: null };
  let previewUpgradeState = EMPTY_UPGRADE_STATE;
  const STAT_LABELS = {
    max_hp: 'HP',
    atk: 'ATK',
    defense: 'DEF',
    crit_rate: 'Crit Rate',
    crit_damage: 'Crit DMG'
  };
  // Clear override when preview is not the player
  $: {
    const cur = roster.find(r => r.id === previewId);
    if (!cur?.is_player) previewElementOverride = '';
  }

  $: currentElementName = (() => {
    const cur = roster.find(r => r.id === previewId);
    const el = previewElementOverride || (cur && cur.element) || '';
    return el ? String(el) : '';
  })();
  $: starColor = currentElementName ? (() => { try { return getElementColor(currentElementName); } catch { return ''; } })() : '';
  $: if ((previewId ?? null) !== lastPreviewedId) {
    lastPreviewedId = previewId ?? null;
    upgradeContext = null;
    previewMode.set('portrait');
    if (previewId) refreshUpgradeData(previewId, { force: true });
    try { dispatch('previewMode', { mode: 'portrait', id: previewId ?? null }); } catch {}
  }
  $: previewUpgradeState = readUpgradeState(previewId, upgradeCache);

  function readUpgradeState(id, cache = upgradeCache) {
    const key = id == null ? null : String(id);
    return key && cache[key] ? cache[key] : EMPTY_UPGRADE_STATE;
  }

  async function refreshUpgradeData(id, { force = false } = {}) {
    if (!id) return null;
    const key = String(id);
    const existing = upgradeCache[key];
    if (!force && existing) {
      if (existing.loading) return existing.data ?? null;
      if (existing.data && !existing.error) return existing.data;
    }

    const token = (upgradeTokens[key] || 0) + 1;
    upgradeTokens = { ...upgradeTokens, [key]: token };
    upgradeCache = { ...upgradeCache, [key]: { ...(existing || {}), loading: true } };

    try {
      const data = await getUpgrade(id);
      if (upgradeTokens[key] !== token) return data;
      upgradeCache = { ...upgradeCache, [key]: { data, loading: false, error: null } };
      return data;
    } catch (err) {
      if (upgradeTokens[key] !== token) return null;
      upgradeCache = {
        ...upgradeCache,
        [key]: { data: existing?.data ?? null, loading: false, error: err }
      };
      return null;
    }
  }

  onMount(async () => {
    await refreshRoster();
  });

  async function refreshRoster() {
    try {
      const data = await getPlayers();
      userBuffPercent = data.user?.level ?? 0;
      function resolveElement(p) {
        let e = p?.element;
        if (e && typeof e !== 'string') e = e.id || e.name;
        return e && !/generic/i.test(String(e)) ? e : 'Generic';
      }
      const oldPreview = previewId;
      const oldSelected = [...selected];
      function isNonPlayable(entry) {
        const gr = Number(entry?.stats?.gacha_rarity);
        if (!Number.isNaN(gr)) {
          return gr === 0;
        }
        // Fallback: explicitly hide known non-playables if rarity not provided
        return entry.id === 'mimic';
      }

      roster = data.players
        .map((p) => ({
          id: p.id,
          name: p.name,
          about: p.about,
          img: getCharacterImage(p.id, p.is_player) || getRandomFallback(),
          owned: p.owned,
          is_player: p.is_player,
          element: resolveElement(p),
          stats: p.stats ?? { hp: 0, atk: 0, defense: 0, level: 1 }
        }))
        // Only show characters the user can actually use
        .filter((p) => (p.owned || p.is_player) && !isNonPlayable(p))
        .sort((a, b) => (a.is_player ? -1 : b.is_player ? 1 : 0));
      // Restore selection and preview where possible
      selected = oldSelected.filter((id) => roster.some((c) => c.id === id));
      const player = roster.find((p) => p.is_player);
      // Ensure the player is always in party; if party is full, replace the last non-player
      if (player && !selected.includes(player.id)) {
        if (selected.length >= 5) {
          // Remove the last non-player entry to make room
          const withoutPlayer = selected.filter((id) => id !== player.id);
          withoutPlayer.pop();
          selected = [...withoutPlayer, player.id];
        } else {
          selected = [...selected, player.id];
        }
      }
      const defaultPreview = player ? player.id : (roster[0]?.id || null);
      previewId = oldPreview ?? selected[0] ?? defaultPreview;
    } catch (e) {
      if (dev || !browser) {
        const { error } = await import('$lib/systems/logger.js');
        error('Unable to load roster. Is the backend running on 59002?');
      }
    }
  }

  function statLabel(statKey) {
    if (!statKey) return 'Stat';
    if (STAT_LABELS[statKey]) return STAT_LABELS[statKey];
    const pretty = String(statKey).replace(/_/g, ' ').trim();
    return pretty ? pretty.replace(/\b\w/g, (c) => c.toUpperCase()) : statKey;
  }

  function formatPercent(value) {
    if (value == null) return '+0%';
    const num = Number(value) * 100;
    if (!Number.isFinite(num)) return '+0%';
    let digits = 2;
    const abs = Math.abs(num);
    if (abs >= 100) digits = 0;
    else if (abs >= 10) digits = 1;
    let formatted = num.toFixed(digits);
    formatted = formatted.replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
    const sign = num >= 0 ? '+' : '';
    return `${sign}${formatted}%`;
  }

  function toggleMember(id) {
    if (!id) return;
    // The player cannot be removed from the party
    const player = roster.find((p) => p.is_player);
    if (player && id === player.id) return;
    if (selected.includes(id)) {
      selected = selected.filter((c) => c !== id);
    } else if (selected.length < 5) {
      selected = [...selected, id];
    }
  }

  function handlePreviewMode(detail, mode) {
    const char = detail?.id ? roster.find((p) => p.id === detail.id) : roster.find((p) => p.id === previewId);
    const nextDetail = {
      ...(detail || {}),
      id: char?.id ?? previewId ?? null,
      character: char || null
    };
    upgradeContext = mode === 'upgrade' ? nextDetail : null;
    previewMode.set(mode);
    try { dispatch('previewMode', { mode, ...nextDetail }); } catch {}
  }

  async function forwardUpgradeRequest(detail) {
    if (upgradeContext?.pendingStat || upgradeContext?.pendingConversion) return;

    const char = detail?.id ? roster.find((p) => p.id === detail.id) : roster.find((p) => p.id === previewId);
    const payload = {
      ...(detail || {}),
      id: char?.id ?? previewId ?? null,
      character: char || null
    };
    const { id, stat } = payload;
    const isUpgradeMode = modeIsUpgrade();

    if (isUpgradeMode) {
      upgradeContext = {
        id,
        character: payload.character,
        stat: stat || null,
        lastRequestedStat: stat || null,
        pendingStat: stat || null,
        pendingConversion: false,
        message: '',
        error: ''
      };
    }

    try { dispatch('requestUpgrade', payload); } catch {}

    if (!id || !stat) return;

    try {
      const result = await upgradeStat(id, stat);
      await refreshUpgradeData(id, { force: true });
      await refreshRoster();
      const updatedChar = roster.find((p) => p.id === id) || payload.character || null;
      const statKey = result?.stat_upgraded || stat;
      const percent = result?.upgrade_percent;
      const bonusText = percent != null ? formatPercent(percent) : '';
      const label = statLabel(statKey);
      const message = bonusText ? `Upgraded ${label} by ${bonusText}.` : `Upgraded ${label}.`;
      if (isUpgradeMode) {
        upgradeContext = {
          id,
          character: updatedChar,
          stat: statKey,
          lastRequestedStat: stat || null,
          pendingStat: null,
          pendingConversion: false,
          message,
          error: ''
        };
      }
    } catch (err) {
      if (isUpgradeMode) {
        const label = statLabel(stat || '');
        upgradeContext = {
          id,
          character: payload.character,
          stat: stat || null,
          lastRequestedStat: stat || null,
          pendingStat: null,
          pendingConversion: false,
          message: '',
          error: err?.message || `Unable to upgrade ${label}.`
        };
      }
    }
  }

  async function forwardConversionRequest(detail) {
    if (upgradeContext?.pendingStat || upgradeContext?.pendingConversion) return;

    const char = detail?.id ? roster.find((p) => p.id === detail.id) : roster.find((p) => p.id === previewId);
    const payload = {
      ...(detail || {}),
      id: char?.id ?? previewId ?? null,
      character: char || null
    };

    const { id } = payload;
    const rawStar = Number(detail?.starLevel ?? detail?.star_level ?? detail?.star ?? detail?.starlevel);
    const rawCount = Number(detail?.itemCount ?? detail?.item_count ?? detail?.count);
    if (!id || !Number.isFinite(rawStar) || !Number.isFinite(rawCount)) return;
    const starLevel = Math.min(4, Math.max(1, Math.floor(rawStar)));
    const itemCount = Math.max(1, Math.floor(rawCount));

    const isUpgradeMode = modeIsUpgrade();
    const existing = upgradeContext && upgradeContext.id === id ? upgradeContext : null;

    if (isUpgradeMode) {
      upgradeContext = {
        id,
        character: payload.character,
        stat: existing?.stat ?? null,
        lastRequestedStat: existing?.lastRequestedStat ?? null,
        pendingStat: null,
        pendingConversion: true,
        message: '',
        error: ''
      };
    }

    try {
      await upgradeCharacter(id, starLevel, itemCount);
      await refreshUpgradeData(id, { force: true });
      await refreshRoster();
      if (isUpgradeMode) {
        const updatedChar = roster.find((p) => p.id === id) || payload.character || null;
        upgradeContext = {
          id,
          character: updatedChar,
          stat: existing?.stat ?? null,
          lastRequestedStat: existing?.lastRequestedStat ?? null,
          pendingStat: null,
          pendingConversion: false,
          message: `Converted ${itemCount}× ${starLevel}★ items to upgrade points.`,
          error: ''
        };
      }
    } catch (err) {
      if (isUpgradeMode) {
        upgradeContext = {
          id,
          character: payload.character,
          stat: existing?.stat ?? null,
          lastRequestedStat: existing?.lastRequestedStat ?? null,
          pendingStat: null,
          pendingConversion: false,
          message: '',
          error: err?.message || 'Unable to convert items.'
        };
      }
    }
  }

  function modeIsUpgrade() {
    let val = 'portrait';
    const unsubscribe = previewMode.subscribe((v) => { val = v; });
    unsubscribe?.();
    return val === 'upgrade';
  }
</script>

{#if compact}
  <PartyRoster {roster} {selected} bind:previewId {compact} {reducedMotion} on:toggle={(e) => toggleMember(e.detail)} />
{:else}
  <MenuPanel {starColor} {reducedMotion}>
    <div class="full" data-testid="party-picker">
      <PartyRoster {roster} {selected} bind:previewId {reducedMotion} on:toggle={(e) => toggleMember(e.detail)} />
      <PlayerPreview
        {roster}
        {previewId}
        overrideElement={previewElementOverride}
        mode={$previewMode}
        upgradeContext={upgradeContext}
        upgradeData={previewUpgradeState.data}
        upgradeLoading={previewUpgradeState.loading}
        upgradeError={previewUpgradeState.error}
        {reducedMotion}
        on:open-upgrade={(e) => handlePreviewMode(e.detail, 'upgrade')}
        on:close-upgrade={(e) => handlePreviewMode(e.detail, 'portrait')}
        on:request-upgrade={(e) => forwardUpgradeRequest(e.detail)}
        on:request-convert={(e) => forwardConversionRequest(e.detail)}
        on:element-change={(e) => { previewElementOverride = e.detail?.element || previewElementOverride; refreshRoster(); }}
      />
      <div class="right-col">
        <StatTabs {roster} {previewId} {selected} {userBuffPercent}
          upgradeMode={$previewMode === 'upgrade'}
          on:toggle={(e) => toggleMember(e.detail)}
          on:open-upgrade={(e) => handlePreviewMode(e.detail, 'upgrade')}
          on:close-upgrade={(e) => handlePreviewMode(e.detail, 'portrait')}
        />
        <div class="party-actions-inline">
          {#if actionLabel === 'Start Run'}
            <div class="pressure-inline" aria-label="Pressure Level Controls">
              <span class="pressure-inline-label">Pressure</span>
              <button class="pressure-btn" on:click={() => pressure = Math.max(0, pressure - 1)} disabled={pressure <= 0}>
                ◀
              </button>
              <span class="pressure-value" data-testid="pressure-value">{pressure}</span>
              <button class="pressure-btn" on:click={() => pressure = pressure + 1}>
                ▶
              </button>
            </div>
          {/if}
          <button class="wide" on:click={() => dispatch('save', { pressure })}>{actionLabel}</button>
          <button class="wide" on:click={() => dispatch('cancel')}>Cancel</button>
        </div>
      </div>
    </div>
  </MenuPanel>
{/if}

<style>
  .full {
    display: grid;
    grid-template-columns: minmax(8rem, 22%) 1fr minmax(12rem, 26%);
    width: 100%;
    height: 96%;
    max-width: 100%;
    max-height: 98%;
    /* allow internal scrolling instead of clipping when content grows */
    position: relative;
    z-index: 0; /* establish stacking context so stars can sit behind */
  }
  .right-col { display: flex; flex-direction: column; min-height: 0; }
  
  .pressure-controls { margin-top: 0.5rem; }
  .pressure-label { display: block; color: #fff; font-size: 0.9rem; margin-bottom: 0.3rem; text-align: center; }
  .pressure-input { display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
  .pressure-btn { 
    background: rgba(0,0,0,0.5); 
    border: 1px solid rgba(255,255,255,0.35); 
    color: #fff; 
    padding: 0.3rem 0.5rem; 
    cursor: pointer;
    border-radius: 3px;
  }
  .pressure-btn:hover:not(:disabled) { 
    background: rgba(255,255,255,0.1); 
  }
  .pressure-btn:disabled { 
    opacity: 0.5; 
    cursor: not-allowed; 
  }
  .pressure-value { 
    color: #fff; 
    font-weight: bold; 
    min-width: 2rem; 
    text-align: center; 
  }
  /* Inline row containing pressure + primary actions */
  .party-actions-inline { display:flex; align-items:center; gap:0.5rem; margin-top: 0.5rem; }
  .pressure-inline { display:flex; align-items:center; gap:0.4rem; padding: 0.2rem 0.4rem; }
  .pressure-inline-label { color:#fff; opacity:0.85; font-size: 0.9rem; margin-right: 0.1rem; }
  .party-actions-inline .wide { flex: 1; border: 1px solid rgba(255,255,255,0.35); background: rgba(0,0,0,0.5); color:#fff; padding: 0.45rem 0.8rem; }
  /* Match Add/Remove party hover style for Start/Save/Cancel */
  .party-actions-inline .wide:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.5); }

  /* Falling starfield */
  </style>
