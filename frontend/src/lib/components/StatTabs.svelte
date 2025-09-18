<script>
  import { createEventDispatcher } from 'svelte';
  import { HeartPulse, Swords, Shield, Crosshair, Sparkles } from 'lucide-svelte';
  import { getElementIcon, getElementColor } from '../systems/assetLoader.js';
  import { getUpgrade, upgradeStat } from '../systems/api.js';

  export let roster = [];
  export let previewId;
  export let selected = [];
  export let userBuffPercent = 0;
  export let previewMode = 'portrait';

  const statTabs = ['Core', 'Offense', 'Defense'];
  let activeTab = 'Core';
  const dispatch = createEventDispatcher();

  const UPGRADE_STATS = [
    { key: 'max_hp', label: 'HP', icon: HeartPulse, summary: 'Increase max health.' },
    { key: 'atk', label: 'ATK', icon: Swords, summary: 'Boost offensive power.' },
    { key: 'defense', label: 'DEF', icon: Shield, summary: 'Reduce incoming damage.' },
    { key: 'crit_rate', label: 'CRIT Rate', icon: Crosshair, summary: 'Raise critical odds.' },
    { key: 'crit_damage', label: 'CRIT DMG', icon: Sparkles, summary: 'Amplify critical hits.' }
  ];

  let previewChar;
  $: previewChar = roster.find((r) => r.id === previewId);
  $: isPlayer = !!previewChar?.is_player;
  $: viewStats = previewChar?.stats || {};

  let upgradeData = null;
  let upgradeError = '';
  let upgradeMessage = '';
  let upgradeMessageType = 'info';
  let loadingUpgrade = false;
  let loadingForId = null;
  let pendingStats = new Set();
  let lastLoadedId = null;

  $: statTotals = upgradeData?.stat_totals || {};
  $: nextCosts = upgradeData?.next_costs || {};
  $: availablePoints = Number(upgradeData?.upgrade_points ?? upgradeData?.remaining_points ?? 0);

  async function loadUpgradeDataFor(id) {
    if (!id) return;
    loadingForId = id;
    loadingUpgrade = true;
    upgradeError = '';
    try {
      const data = await getUpgrade(id);
      if (previewChar?.id === id) {
        upgradeData = data || {};
      }
    } catch (err) {
      if (previewChar?.id === id) {
        upgradeData = null;
        upgradeError = err?.message || 'Failed to load upgrade data';
      }
    } finally {
      if (loadingForId === id) {
        loadingUpgrade = false;
        loadingForId = null;
      }
    }
  }

  async function refreshUpgradeData() {
    if (!previewChar?.id) return;
    await loadUpgradeDataFor(previewChar.id);
  }

  $: if (previewChar?.id && previewChar.id !== lastLoadedId) {
    lastLoadedId = previewChar.id;
    upgradeData = null;
    upgradeError = '';
    upgradeMessage = '';
    pendingStats = new Set();
    loadUpgradeDataFor(previewChar.id);
  }

  $: if (!previewChar?.id) {
    upgradeData = null;
    upgradeError = '';
    upgradeMessage = '';
    lastLoadedId = null;
    pendingStats = new Set();
  }

  function toggleMember() {
    if (!previewId) return;
    dispatch('toggle', previewId);
  }

  function formatStat(runtimeValue, baseValue, suffix = '') {
    const isPercent = suffix === '%';
    const rv = runtimeValue == null ? null : (isPercent ? runtimeValue * 100 : runtimeValue);
    const bv = baseValue == null ? null : (isPercent ? baseValue * 100 : baseValue);

    if (bv !== null && rv !== null && rv !== bv) {
      const modifier = rv - bv;
      const sign = modifier >= 0 ? '+' : '';
      const show = (v) => (Number.isInteger(v) ? v : v.toFixed(1));
      return `${show(rv)}${suffix} (${show(bv)}${sign}${show(modifier)})`;
    }
    if (rv === null) return '-';
    return `${Number.isInteger(rv) ? rv : rv.toFixed(1)}${suffix}`;
  }

  function formatMult(runtimeValue, baseValue) {
    const rv = runtimeValue == null ? null : Number(runtimeValue);
    const bv = baseValue == null ? null : Number(baseValue);
    const show = (v) => {
      if (v == null || !isFinite(v)) return '-';
      const rounded = Math.round(v);
      return Math.abs(v - rounded) < 1e-6 ? String(rounded) : v.toFixed(2);
    };
    if (rv === null) return '-';
    if (bv !== null && rv !== bv) {
      const modifier = rv - bv;
      const sign = modifier >= 0 ? '+' : '';
      return `${show(rv)}x (${show(bv)}${sign}${show(modifier)})`;
    }
    return `${show(rv)}x`;
  }

  function getBaseStat(character, statName) {
    return character.stats?.base_stats?.[statName];
  }

  function statLabel(key) {
    return UPGRADE_STATS.find((s) => s.key === key)?.label || key;
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

  function formatPoints(value, placeholder = '0') {
    const num = Number(value);
    if (!Number.isFinite(num)) return placeholder;
    return Math.max(0, Math.round(num)).toLocaleString();
  }

  function costFor(statKey) {
    const raw = nextCosts?.[statKey];
    if (raw == null) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function formatCost(statKey) {
    const cost = costFor(statKey);
    if (cost == null) return '—';
    return `${formatPoints(cost, '—')} pts`;
  }

  function canUpgradeStat(statKey) {
    if (!previewChar?.id) return false;
    if (loadingUpgrade) return false;
    if (pendingStats.has(statKey)) return false;
    if (availablePoints <= 0) return false;
    const cost = costFor(statKey);
    if (cost == null) return true;
    return availablePoints >= cost;
  }

  async function handleStatUpgrade(statKey) {
    if (!previewChar?.id) return;
    if (!canUpgradeStat(statKey)) return;

    upgradeMessage = '';
    upgradeMessageType = 'info';
    const next = new Set(pendingStats);
    next.add(statKey);
    pendingStats = next;

    const id = previewChar.id;
    try {
      const result = await upgradeStat(id, statKey);
      const percent = result?.upgrade_percent;
      const bonusText = percent != null ? formatPercent(percent) : '';
      upgradeMessage = bonusText ? `Upgraded ${statLabel(statKey)} by ${bonusText}.` : `Upgraded ${statLabel(statKey)}.`;
      upgradeMessageType = 'success';
      await loadUpgradeDataFor(id);
      dispatch('refresh-roster');
    } catch (err) {
      upgradeMessage = err?.message || 'Upgrade failed';
      upgradeMessageType = 'error';
    } finally {
      const copy = new Set(pendingStats);
      copy.delete(statKey);
      pendingStats = copy;
    }
  }

  function openUpgradeMode() {
    if (!previewChar?.id) return;
    dispatch('open-upgrade-mode', { id: previewChar.id });
  }

  function closeUpgradeMode() {
    dispatch('close-upgrade-mode', { id: previewChar?.id ?? null });
  }
</script>

<div class="stats-panel" data-testid="stats-panel">
  <div class="stats-tabs">
    {#each statTabs as tab}
      <button class="tab-btn" class:active={activeTab === tab} on:click={() => activeTab = tab}>
        {tab}
      </button>
    {/each}
  </div>
  {#if previewId}
    {#each roster.filter((r) => r.id === previewId) as sel}
      <div class="stats-header">
        <span class="char-name">{sel.name}</span>
        <span class="char-level">Lv {sel.stats.level ?? sel.stats.lv ?? 1}</span>
        <svelte:component
          this={getElementIcon(sel.element || 'Generic')}
          class="type-icon"
          style={`color: ${getElementColor(sel.element || 'Generic')}`}
          aria-hidden="true" />
      </div>
      {#if sel.about}
        <div class="char-about">{sel.about}</div>
        <div class="inline-divider" aria-hidden="true"></div>
      {/if}
      <div class="stats-list">
        {#if activeTab === 'Core'}
          <div>
            <span>HP</span>
            <span>
              {#if viewStats.max_hp != null}
                {(viewStats.hp ?? 0) + '/' + formatStat(viewStats.max_hp, getBaseStat(sel, 'max_hp'))}
              {:else}
                {viewStats.hp ?? '-'}
              {/if}
            </span>
          </div>
          <div><span>EXP</span><span>{sel.stats.exp ?? sel.stats.xp ?? '-'}</span></div>
          <div><span>Vitality</span><span>{formatMult(sel.stats.vitality ?? sel.stats.vita, getBaseStat(sel, 'vitality'))}</span></div>
          <div><span>Regain</span><span>{formatStat(sel.stats.regain ?? sel.stats.regain_rate, getBaseStat(sel, 'regain'))}</span></div>
          <div class="buff-note">Global Buff: +{userBuffPercent}%</div>
        {:else if activeTab === 'Offense'}
          <div><span>ATK</span><span>{formatStat(viewStats.atk, getBaseStat(sel, 'atk'))}</span></div>
          <div><span>CRIT Rate</span><span>{formatStat(viewStats.crit_rate, getBaseStat(sel, 'crit_rate'), '%')}</span></div>
          <div><span>CRIT DMG</span><span>{formatStat(viewStats.crit_damage, getBaseStat(sel, 'crit_damage'), '%')}</span></div>
          <div><span>Effect Hit Rate</span><span>{formatStat(viewStats.effect_hit_rate, getBaseStat(sel, 'effect_hit_rate'), '%')}</span></div>
        {:else if activeTab === 'Defense'}
          <div><span>DEF</span><span>{formatStat(viewStats.defense, getBaseStat(sel, 'defense'))}</span></div>
          <div><span>Mitigation</span><span>{formatMult(viewStats.mitigation, getBaseStat(sel, 'mitigation'))}</span></div>
          <div><span>Dodge Odds</span><span>{formatStat(viewStats.dodge_odds, getBaseStat(sel, 'dodge_odds'), '%')}</span></div>
          <div><span>Effect Resist</span><span>{formatStat(viewStats.effect_resistance, getBaseStat(sel, 'effect_resistance'), '%')}</span></div>
        {/if}
      </div>
    {/each}
  {:else}
    <div class="stats-placeholder">Select a character to view stats</div>
  {/if}
  {#if previewId}
    <div class="stats-confirm">
      {#if selected.includes(previewId) && isPlayer}
        <button class="confirm" disabled title="The player must stay in the party">Player is required</button>
      {:else}
        <button class="confirm" on:click={toggleMember}>
          {selected.includes(previewId) ? 'Remove from party' : 'Add to party'}
        </button>
      {/if}
    </div>
  {/if}
  {#if previewId}
    {#each roster.filter((r) => r.id === previewId) as sel}
      <div class="inline-divider" aria-hidden="true"></div>
      <section class="upgrade-block">
        <header class="upgrade-header">
          <div class="upgrade-title">
            <h3>Stat Upgrades</h3>
            <span>Permanent bonuses earned from upgrade items.</span>
          </div>
          <div class="upgrade-actions">
            <button class="refresh-btn" on:click={refreshUpgradeData} disabled={loadingUpgrade}>
              Refresh
            </button>
            {#if previewMode === 'upgrade'}
              <button class="mode-toggle" on:click={closeUpgradeMode}>
                Done
              </button>
            {:else}
              <button class="mode-toggle" on:click={openUpgradeMode} disabled={!previewChar}>
                Upgrade view
              </button>
            {/if}
          </div>
        </header>
        <div class="points-summary">
          <span class="label">Available points</span>
          <span class="value">{formatPoints(availablePoints, '0')}</span>
        </div>
        {#if upgradeError}
          <div class="upgrade-message error">{upgradeError}</div>
        {/if}
        {#if loadingUpgrade && !upgradeData}
          <div class="upgrade-loading">Loading upgrade info…</div>
        {:else if upgradeData}
          <div class="upgrade-list">
            {#each UPGRADE_STATS as stat}
              <div class="upgrade-row">
                <div class="stat-label">
                  <svelte:component this={stat.icon} class="stat-icon" aria-hidden="true" />
                  <div class="stat-text">
                    <span>{stat.label}</span>
                    <small>{stat.summary}</small>
                  </div>
                </div>
                <div class="stat-metrics">
                  <span class="metric bonus">Bonus: {formatPercent(statTotals[stat.key])}</span>
                  <span class="metric available">Available: {formatPoints(availablePoints, '0')}</span>
                  <span class="metric cost">Next cost: {formatCost(stat.key)}</span>
                </div>
                <button
                  class="stat-upgrade-btn"
                  on:click={() => handleStatUpgrade(stat.key)}
                  disabled={!canUpgradeStat(stat.key)}
                >
                  {pendingStats.has(stat.key) ? 'Applying…' : 'Upgrade'}
                </button>
              </div>
            {/each}
          </div>
        {:else}
          <div class="upgrade-loading">Upgrade data unavailable.</div>
        {/if}
        {#if upgradeMessage}
          <div class="upgrade-message" class:success={upgradeMessageType === 'success'} class:error={upgradeMessageType === 'error'}>
            {upgradeMessage}
          </div>
        {/if}
      </section>
    {/each}
  {/if}
</div>

<style>
  .stats-panel {
    flex: 1;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.25);
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    box-sizing: border-box;
    border-radius: 8px;
    position: relative;
  }
  .stats-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    padding-bottom: 0.5rem;
  }
  .char-name { font-size: 1.2rem; color: #fff; flex: 1; }
  .char-level { font-size: 1rem; color: #ccc; }
  .type-icon { width: 24px; height: 24px; }
  .buff-note { font-size: 0.85rem; color: #ccc; margin-bottom: 0.3rem; }
  .char-about { margin: 0.25rem 0; font-style: italic; }
  .stats-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .stats-list div { display: flex; justify-content: space-between; color: #ddd; }
  .stats-placeholder {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #888;
    font-style: italic;
  }
  .stats-confirm {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    min-height: 32px;
    padding: 0.15rem 0;
    margin-top: 0.25rem;
  }
  button.confirm {
    background: rgba(0,0,0,0.5);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.35);
    padding: 0.45rem 0.8rem;
    align-self: flex-end;
    font-size: 0.95rem;
    min-height: 28px;
    border-radius: 0;
    transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
  }
  button.confirm:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.5); }
  .stats-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  .tab-btn {
    background: rgba(255,255,255,0.1);
    color: #ddd;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s;
  }
  .tab-btn.active { background: rgba(255,255,255,0.3); color: #fff; }
  .inline-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent);
    margin: 0 0 0.35rem 0;
  }

  .upgrade-block {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    background: rgba(0,0,0,0.22);
    padding: 0.75rem;
    border-radius: 6px;
  }
  .upgrade-header {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 0.5rem;
    align-items: flex-start;
  }
  .upgrade-title h3 {
    margin: 0;
    font-size: 1rem;
    color: #fff;
  }
  .upgrade-title span {
    display: block;
    margin-top: 0.2rem;
    font-size: 0.75rem;
    color: #ccc;
  }
  .upgrade-actions {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  .mode-toggle,
  .refresh-btn {
    background: rgba(0,0,0,0.55);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.35);
    padding: 0.35rem 0.7rem;
    border-radius: 4px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .mode-toggle:hover:not(:disabled),
  .refresh-btn:hover:not(:disabled) {
    background: rgba(255,255,255,0.12);
    border-color: rgba(255,255,255,0.5);
  }
  .mode-toggle:disabled,
  .refresh-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .points-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255,255,255,0.05);
    padding: 0.45rem 0.6rem;
    border-radius: 4px;
    color: #ddd;
    font-size: 0.9rem;
  }
  .points-summary .label { font-weight: 600; }
  .points-summary .value { font-family: 'IBM Plex Mono', monospace; }
  .upgrade-list {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }
  .upgrade-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr) auto;
    gap: 0.75rem;
    align-items: center;
    background: rgba(0,0,0,0.2);
    padding: 0.55rem 0.6rem;
    border-radius: 6px;
  }
  .stat-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #fff;
  }
  .stat-icon {
    width: 22px;
    height: 22px;
  }
  .stat-text span { font-weight: 600; }
  .stat-text small {
    display: block;
    font-size: 0.7rem;
    color: #aaa;
    margin-top: 0.1rem;
  }
  .stat-metrics {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    color: #ccc;
    font-size: 0.75rem;
  }
  .stat-metrics .metric { display: flex; gap: 0.25rem; }
  .stat-upgrade-btn {
    background: rgba(0,0,0,0.5);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.35);
    padding: 0.4rem 0.7rem;
    border-radius: 4px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .stat-upgrade-btn:hover:not(:disabled) {
    background: rgba(255,255,255,0.12);
    border-color: rgba(255,255,255,0.5);
  }
  .stat-upgrade-btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
  .upgrade-loading {
    font-size: 0.85rem;
    color: #bbb;
  }
  .upgrade-message {
    font-size: 0.8rem;
    padding: 0.45rem 0.6rem;
    border-radius: 4px;
    border: 1px solid rgba(255,255,255,0.25);
    background: rgba(255,255,255,0.06);
    color: #eee;
  }
  .upgrade-message.success {
    border-color: rgba(0, 255, 160, 0.35);
    background: rgba(0, 255, 160, 0.12);
    color: #c7ffe5;
  }
  .upgrade-message.error {
    border-color: rgba(255, 64, 64, 0.35);
    background: rgba(255, 64, 64, 0.12);
    color: #ffbcbc;
  }
</style>
