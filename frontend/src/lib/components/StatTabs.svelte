<script>
  import { createEventDispatcher } from 'svelte';
  import { fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { getElementIcon, getElementColor } from '../systems/assetLoader.js';
  import { formatPercent, formatMaterialQuantity, formatCost } from '../utils/upgradeFormatting.js';

  export let roster = [];
  export let previewId;
  export let selected = [];
  export let userBuffPercent = 0;
  export let upgradeMode = false;
  export let upgradeData = null;
  export let upgradeLoading = false;
  export let upgradeError = null;
  export let upgradeContext = null;
  export let selectedStat = null;
  export let reducedMotion = false;

  const statTabs = ['Core', 'Offense', 'Defense'];
  const dispatch = createEventDispatcher();
  const UPGRADE_STATS = [
    { key: 'max_hp', label: 'HP', hint: 'Bolster survivability.' },
    { key: 'atk', label: 'ATK', hint: 'Improve offensive power.' },
    { key: 'defense', label: 'DEF', hint: 'Stiffen defenses.' },
    { key: 'crit_rate', label: 'Crit Rate', hint: 'Raise critical odds.' },
    { key: 'crit_damage', label: 'Crit DMG', hint: 'Amplify crit damage.' },
    { key: 'vitality', label: 'Vitality', hint: 'Extend buff durations & recovery.' },
    { key: 'mitigation', label: 'Mitigation', hint: 'Soften incoming damage.' }
  ];

  let activeTab = 'Core';
  let previewChar;
  $: previewChar = roster.find((r) => r.id === previewId);
  $: isPlayer = !!previewChar?.is_player;
  $: viewStats = previewChar?.stats || {};

  $: upgradeTotals = upgradeData?.stat_totals || {};
  $: upgradeCounts = upgradeData?.stat_counts || {};
  $: nextCosts = upgradeData?.next_costs || {};
  $: upgradeItems = upgradeData?.items || {};
  $: resolvedElement = upgradeData?.element || previewChar?.element || 'generic';
  $: upgradeMaterialKey = `${String(resolvedElement || 'generic').toLowerCase()}_1`;
  $: availableMaterials = Number(upgradeItems?.[upgradeMaterialKey] ?? 0);
  $: resolvedSelectedStat = (() => {
    if (selectedStat) return selectedStat;
    if (upgradeContext?.pendingStat) return upgradeContext.pendingStat;
    if (upgradeContext?.stat) return upgradeContext.stat;
    if (upgradeContext?.lastRequestedStat) return upgradeContext.lastRequestedStat;
    return UPGRADE_STATS[0]?.key || null;
  })();
  $: activeStatInfo = UPGRADE_STATS.find((entry) => entry.key === resolvedSelectedStat) || UPGRADE_STATS[0];
  $: activeStatLabel = activeStatInfo?.label || '';
  $: activeStatHint = activeStatInfo?.hint || '';
  $: activeStatLevel = Number(upgradeCounts?.[resolvedSelectedStat] ?? 0);
  $: activeNextCost = nextCosts?.[resolvedSelectedStat] ?? null;
  $: activeImpactNow = formatPercent(Number(upgradeTotals?.[resolvedSelectedStat] ?? 0));
  $: impactAfterValue = (() => {
    const current = Number(upgradeTotals?.[resolvedSelectedStat] ?? 0);
    const increment = Number(activeNextCost?.count ?? 0) * 0.001;
    return current + (Number.isFinite(increment) ? increment : 0);
  })();
  $: activeImpactAfter = formatPercent(impactAfterValue);
  $: formattedCost = formatCost(activeNextCost);
  $: upgradeStatusMessage = (() => {
    if (upgradeContext?.pendingStat) {
      return `Upgrading ${activeStatLabel || 'stat'}…`;
    }
    if (upgradeContext?.error) return upgradeContext.error;
    if (upgradeContext?.message) return upgradeContext.message;
    if (upgradeLoading) return 'Loading upgrade data…';
    if (upgradeError) return upgradeError.message || String(upgradeError);
    return '';
  })();

  function toggleMember() {
    if (!previewId) return;
    dispatch('toggle', { id: previewId });
  }

  function openUpgrade() {
    if (!previewId) return;
    dispatch('open-upgrade', { id: previewId, stat: resolvedSelectedStat });
  }

  function closeUpgrade() {
    if (!previewId) return;
    dispatch('close-upgrade', { id: previewId });
  }

  function handleUpgradeDismiss(reason = 'close') {
    if (!upgradeMode) return;
    dispatch('close-upgrade', { id: previewId ?? null, reason });
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

  function requestUpgrade() {
    if (!previewId || !resolvedSelectedStat) return;
    const nextCostCount = activeNextCost?.count ?? null;
    dispatch('request-upgrade', {
      id: previewId,
      stat: resolvedSelectedStat,
      expectedMaterials: nextCostCount,
      availableMaterials
    });
  }

</script>

<div class="stats-panel" data-testid="stats-panel" class:upgrade-active={upgradeMode}>
  <div class="stats-tabs">
    {#each statTabs as tab}
      <button class="tab-btn" class:active={activeTab === tab} on:click={() => activeTab = tab}>
        {tab}
      </button>
    {/each}
  </div>
  {#if previewChar}
    <div class="stats-header">
      <span class="char-name">{previewChar.name}</span>
      <span class="char-level">Lv {previewChar.stats.level ?? previewChar.stats.lv ?? 1}</span>
      <svelte:component
        this={getElementIcon(previewChar.element || 'Generic')}
        class="type-icon"
        style={`color: ${getElementColor(previewChar.element || 'Generic')}`}
        aria-hidden="true" />
    </div>
    {#if previewChar.about}
      <div class="char-about">{previewChar.about}</div>
      <div class="inline-divider" aria-hidden="true"></div>
    {/if}
    <div class="stats-body">
      {#if upgradeMode}
        <div class="upgrade-layer" on:click={() => handleUpgradeDismiss('overlay')}>
          <div
            class="upgrade-panel"
            role="dialog"
            aria-label="Stat upgrade preview"
            on:click|stopPropagation
            in:fly={{ x: reducedMotion ? 0 : 28, duration: reducedMotion ? 0 : 200, easing: quintOut }}
            out:fly={{ x: reducedMotion ? 0 : 20, duration: reducedMotion ? 0 : 160, easing: quintOut }}
          >
            <header>
              <h3>{activeStatLabel} Upgrade</h3>
              {#if activeStatHint}
                <p class="hint">{activeStatHint}</p>
              {/if}
            </header>
            <div class="upgrade-summary">
              <div>
                <span class="label">Impact now</span>
                <span class="value">{activeImpactNow}</span>
              </div>
              <div>
                <span class="label">After upgrade</span>
                <span class="value">{activeImpactAfter}</span>
              </div>
              <div>
                <span class="label">Current level</span>
                <span class="value">Lv {activeStatLevel}</span>
              </div>
              <div>
                <span class="label">Materials</span>
                <span class="value">{formatMaterialQuantity(availableMaterials, upgradeMaterialKey)}</span>
              </div>
            </div>
            <div class="upgrade-costs">
              <div>
                <span class="label">Cost</span>
                <span class="value">{formattedCost}</span>
              </div>
              <div>
                <span class="label">Status</span>
                <span class="value status">{upgradeStatusMessage || 'Ready'}</span>
              </div>
            </div>
            <div class="upgrade-actions">
              <button type="button" class="secondary" on:click={() => handleUpgradeDismiss('cancel')}>
                Cancel
              </button>
              <button
                type="button"
                class="confirm"
                on:click={requestUpgrade}
                disabled={!resolvedSelectedStat || upgradeContext?.pendingStat}
              >
                Upgrade
              </button>
            </div>
          </div>
        </div>
      {:else}
        <div
          class="stats-list"
          in:fly={{ x: reducedMotion ? 0 : -24, duration: reducedMotion ? 0 : 200, easing: quintOut }}
          out:fly={{ x: reducedMotion ? 0 : -18, duration: reducedMotion ? 0 : 150, easing: quintOut }}
        >
          {#if activeTab === 'Core'}
            <div>
              <span>HP</span>
              <span>
                {#if viewStats.max_hp != null}
                  {(viewStats.hp ?? 0) + '/' + formatStat(viewStats.max_hp, getBaseStat(previewChar, 'max_hp'))}
                {:else}
                  {viewStats.hp ?? '-'}
                {/if}
              </span>
            </div>
            <div><span>EXP</span><span>{previewChar.stats.exp ?? previewChar.stats.xp ?? '-'}</span></div>
            <div><span>Vitality</span><span>{formatMult(previewChar.stats.vitality ?? previewChar.stats.vita, getBaseStat(previewChar, 'vitality'))}</span></div>
            <div><span>Regain</span><span>{formatStat(previewChar.stats.regain ?? previewChar.stats.regain_rate, getBaseStat(previewChar, 'regain'))}</span></div>
            <div class="buff-note">Global Buff: +{userBuffPercent}%</div>
          {:else if activeTab === 'Offense'}
            <div><span>ATK</span><span>{formatStat(viewStats.atk, getBaseStat(previewChar, 'atk'))}</span></div>
            <div><span>CRIT Rate</span><span>{formatStat(viewStats.crit_rate, getBaseStat(previewChar, 'crit_rate'), '%')}</span></div>
            <div><span>CRIT DMG</span><span>{formatStat(viewStats.crit_damage, getBaseStat(previewChar, 'crit_damage'), '%')}</span></div>
            <div><span>Effect Hit Rate</span><span>{formatStat(viewStats.effect_hit_rate, getBaseStat(previewChar, 'effect_hit_rate'), '%')}</span></div>
          {:else if activeTab === 'Defense'}
            <div><span>DEF</span><span>{formatStat(viewStats.defense, getBaseStat(previewChar, 'defense'))}</span></div>
            <div><span>Mitigation</span><span>{formatMult(viewStats.mitigation, getBaseStat(previewChar, 'mitigation'))}</span></div>
            <div><span>Dodge Odds</span><span>{formatStat(viewStats.dodge_odds, getBaseStat(previewChar, 'dodge_odds'), '%')}</span></div>
            <div><span>Effect Resist</span><span>{formatStat(viewStats.effect_resistance, getBaseStat(previewChar, 'effect_resistance'), '%')}</span></div>
          {/if}
        </div>
      {/if}
    </div>
  {:else}
    <div class="stats-placeholder">Select a character to view stats</div>
  {/if}
  {#if previewId}
    <div class="stats-confirm">
      {#if upgradeMode}
        <button class="secondary" on:click={() => handleUpgradeDismiss('footer')} title="Close upgrade stats">Cancel upgrade</button>
      {:else}
        <button class="secondary" on:click={openUpgrade} title="Upgrade stats for this character">Upgrade stats</button>
      {/if}
      {#if selected.includes(previewId) && isPlayer}
        <button class="confirm" disabled title="The player must stay in the party">Player is required</button>
      {:else}
        <button class="confirm" on:click={toggleMember}>
          {selected.includes(previewId) ? 'Remove from party' : 'Add to party'}
        </button>
      {/if}
    </div>
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
  .stats-panel.upgrade-active { overflow: hidden; }
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
  .stats-body { position: relative; flex: 1; min-height: 0; }
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
    gap: 0.5rem;
  }
  button.secondary,
  button.confirm {
    background: linear-gradient(0deg, rgba(255,255,255,0.04), rgba(255,255,255,0.04)), rgba(6, 12, 24, 0.55);
    color: #fff;
    border: var(--glass-border);
    padding: 0.45rem 0.8rem;
    min-height: 28px;
    border-radius: 6px;
    transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
    cursor: pointer;
    opacity: 0.9;
    box-shadow: var(--glass-shadow);
    backdrop-filter: var(--glass-filter);
  }
  button.secondary { font-size: 0.9rem; opacity: 0.85; }
  button.confirm { font-size: 0.95rem; }
  button.secondary:hover,
  button.confirm:hover {
    background: linear-gradient(0deg, rgba(255,255,255,0.08), rgba(255,255,255,0.08)), rgba(10, 18, 34, 0.6);
    border-color: rgba(255,255,255,0.55);
  }
  button.confirm:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
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
  .upgrade-layer {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: stretch;
    justify-content: flex-end;
    padding: 0;
    background: none;
  }
  .upgrade-panel {
    flex: 1 1 auto;
    width: 100%;
    height: 100%;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    box-sizing: border-box;
    background: none;
    box-shadow: none;
    border: none;
    backdrop-filter: none;
  }
  .upgrade-panel header h3 {
    margin: 0;
    color: #fff;
    font-size: 1.1rem;
  }
  .upgrade-panel header .hint {
    margin: 0.25rem 0 0;
    color: rgba(255,255,255,0.7);
    font-size: 0.85rem;
  }
  .upgrade-summary, .upgrade-costs {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.5rem;
    color: #ddd;
  }
  .upgrade-summary .value, .upgrade-costs .value { font-weight: 600; color: #fff; }
  .upgrade-summary .label, .upgrade-costs .label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.65;
  }
  .upgrade-costs .status { color: #ffdca8; font-weight: 500; }
  .upgrade-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
  }
  .upgrade-actions .confirm { font-weight: 600; }
</style>
