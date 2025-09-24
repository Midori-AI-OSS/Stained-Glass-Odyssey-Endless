<script>
  import { onMount } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  import { writable } from 'svelte/store';
  import { getPlayers, getUpgrade, upgradeStat } from '../systems/api.js';
  import { getCharacterImage, getRandomFallback, getElementColor } from '../systems/assetLoader.js';
  import { replaceCharacterMetadata } from '../systems/characterMetadata.js';
  import MenuPanel from './MenuPanel.svelte';
  import PartyRoster from './PartyRoster.svelte';
  import PlayerPreview from './PlayerPreview.svelte';
  import StatTabs from './StatTabs.svelte';
  import { browser, dev } from '$app/environment';
  import { mergeUpgradePayload, shouldRefreshRoster } from './upgradeCacheUtils.js';
  import { formatMaterialQuantity } from '../utils/upgradeFormatting.js';

  let roster = [];
  let userBuffPercent = 0;

  export let selected = [];
  export let compact = false;
  let previewId;
  export let reducedMotion = false;
  // Label for the primary action; overlays set this to "Save Party" or "Start Run"
  export let actionLabel = 'Save Party';
  // Pressure level for run difficulty
  export let allowElementChange = false;
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
    // Ensure upgrade data (incl. inventory counts) is fresh when opening this menu
    if (previewId) {
      await refreshUpgradeData(previewId, { force: true });
    }
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
        const meta = entry?.ui && typeof entry.ui === 'object' ? entry.ui : {};
        if (meta.non_selectable === true) {
          return true;
        }
        const gr = Number(entry?.stats?.gacha_rarity);
        if (!Number.isNaN(gr)) {
          return gr === 0 && meta.allow_select !== true;
        }
        return false;
      }

      replaceCharacterMetadata(data.players || []);
      roster = data.players
        .map((p) => ({
          id: p.id,
          name: p.name,
          about: p.about,
          img: getCharacterImage(p.id, p.is_player) || getRandomFallback(),
          owned: p.owned,
          is_player: p.is_player,
          element: resolveElement(p),
          stats: p.stats ?? { hp: 0, atk: 0, defense: 0, level: 1 },
          ui: p.ui || {}
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

      if (player) {
        const savedElement = player.element || '';
        try { dispatch('editorChange', { damageType: savedElement }); } catch {}
      }
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
    // When entering upgrade mode, force-refresh upgrade data so convert availability is accurate
    if (mode === 'upgrade' && nextDetail.id) {
      try { refreshUpgradeData(nextDetail.id, { force: true }); } catch {}
    }
    try { dispatch('previewMode', { mode, ...nextDetail }); } catch {}
  }

  async function forwardUpgradeRequest(detail) {
    if (upgradeContext?.pendingStat) return;

    const char = detail?.id ? roster.find((p) => p.id === detail.id) : roster.find((p) => p.id === previewId);
    const payload = {
      ...(detail || {}),
      id: char?.id ?? previewId ?? null,
      character: char || null
    };
    const { id, stat } = payload;
    const rawRepeats = detail?.repeats ?? detail?.repeat ?? 1;
    let repeats = Number(rawRepeats);
    if (!Number.isFinite(repeats) || repeats < 1) {
      repeats = 1;
    }
    repeats = Math.max(1, Math.min(Math.floor(repeats), 50));
    const isUpgradeMode = modeIsUpgrade();

    if (isUpgradeMode) {
      upgradeContext = {
        id,
        character: payload.character,
        stat: stat || null,
        lastRequestedStat: stat || null,
        pendingStat: stat || null,
        message: '',
        error: ''
      };
    }

    try { dispatch('requestUpgrade', payload); } catch {}

    if (!id || !stat) return;

    const options = { repeat: repeats };
    const expectedMaterials = detail?.expectedMaterials ?? detail?.materials ?? null;
    if (expectedMaterials != null) {
      options.materials = expectedMaterials;
    }
    const budget = detail?.totalMaterials ?? detail?.total_materials ?? detail?.totalPoints ?? detail?.total_points ?? detail?.availableMaterials ?? null;
    if (budget != null) {
      options.total_materials = budget;
    }

    try {
      const result = await upgradeStat(id, stat, options);
      const key = String(id);
      const previous = upgradeCache[key];
      const previousData = previous?.data || null;
      let mergedData = mergeUpgradePayload(previousData, result);

      const elementKey = String(result?.element || mergedData?.element || payload.character?.element || 'generic').toLowerCase();
      if (!mergedData.items) {
        mergedData.items = {};
      }
      if (result.materials_remaining != null) {
        mergedData.items = {
          ...mergedData.items,
          [`${elementKey}_1`]: result.materials_remaining
        };
      }

      upgradeCache = {
        ...upgradeCache,
        [key]: {
          data: mergedData,
          loading: false,
          error: null
        }
      };

      const updatedChar = roster.find((p) => p.id === id) || payload.character || null;
      const statKey = result?.stat_upgraded || stat;
      const totalPercent = Number(result?.upgrade_percent) || 0;
      const completed = Number(result?.completed_upgrades) || 0;
      const materialsSpent = Number(result?.materials_spent) || 0;
      const label = statLabel(statKey || stat || '');
      const percentText = totalPercent ? formatPercent(totalPercent) : '';
      const materialLabel = materialsSpent > 0
        ? ` (${formatMaterialQuantity(materialsSpent, `${elementKey}_1`)})`
        : '';

      let message = '';
      if (completed > 0) {
        if (completed === 1) {
          message = percentText
            ? `Upgraded ${label} by ${percentText}${materialLabel}.`
            : `Upgraded ${label}${materialLabel}.`;
        } else {
          message = percentText
            ? `Upgraded ${label} ${completed}× for ${percentText} total${materialLabel}.`
            : `Upgraded ${label} ${completed}×${materialLabel}.`;
        }
      } else {
        message = `No upgrades applied to ${label}.`;
      }

      let errorText = '';
      if (completed < repeats) {
        const desired = Math.max(1, repeats);
        errorText = `Stopped after ${completed}/${desired} upgrades for ${label}.`;
      }

      const needsRosterRefresh = shouldRefreshRoster(result);
      if (needsRosterRefresh) {
        await refreshRoster();
      }

      if (isUpgradeMode) {
        const refreshedChar = roster.find((p) => p.id === id) || updatedChar;
        upgradeContext = {
          id,
          character: refreshedChar,
          stat: statKey || null,
          lastRequestedStat: stat || null,
          pendingStat: null,
          message,
          error: errorText
        };
      }
    } catch (err) {
      if (isUpgradeMode) {
        upgradeContext = {
          id,
          character: payload.character,
          stat: stat || null,
          lastRequestedStat: stat || null,
          pendingStat: null,
          message: '',
          error: err?.message || `Unable to upgrade ${statLabel(stat || '')}.`
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
        {allowElementChange}
        mode={$previewMode}
        upgradeContext={upgradeContext}
        upgradeData={previewUpgradeState.data}
        upgradeLoading={previewUpgradeState.loading}
        upgradeError={previewUpgradeState.error}
        {reducedMotion}
        on:open-upgrade={(e) => handlePreviewMode(e.detail, 'upgrade')}
        on:close-upgrade={(e) => handlePreviewMode(e.detail, 'portrait')}
        on:request-upgrade={(e) => forwardUpgradeRequest(e.detail)}
        on:element-change={(e) => {
          const el = e.detail?.element || '';
          previewElementOverride = el || previewElementOverride;
          // Propagate player element change to editor state so start_run gets damage_type
          try { dispatch('editorChange', { damageType: el }); } catch {}
          refreshRoster();
          if (previewId) {
            refreshUpgradeData(previewId, { force: true });
          }
        }}
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
