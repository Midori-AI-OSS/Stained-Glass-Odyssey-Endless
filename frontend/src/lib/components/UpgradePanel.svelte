<script>
  import { onMount } from 'svelte';
  import { getUpgrade, upgradeStat } from '../systems/api.js';
  import { createEventDispatcher } from 'svelte';
  import { getElementColor } from '../systems/assetLoader.js';
  import {
    formatCost,
    formatPercent,
    formatMaterialQuantity,
    formatMaterialName,
    extractElementBreakdown,
    computeUnitsFromBreakdown,
    prepareMaterialRequest
  } from '../utils/upgradeFormatting.js';

  export let id;
  export let element; // e.g. 'Light', 'Fire'

  const UPGRADEABLE_STATS = ['max_hp', 'atk', 'defense', 'crit_rate', 'crit_damage', 'vitality', 'mitigation'];
  const STAT_LABELS = {
    max_hp: 'HP',
    atk: 'ATK',
    defense: 'DEF',
    crit_rate: 'Crit Rate',
    crit_damage: 'Crit DMG',
    vitality: 'Vitality',
    mitigation: 'Mitigation'
  };

  function formatLabel(stat) {
    return STAT_LABELS[stat] || String(stat).replace(/_/g, ' ');
  }

  let items = {};
  let statTotals = {};
  let statCounts = {};
  let nextCosts = {};
  let backendElement = '';
  let loading = true;
  let upgradeRepeats = 1;
  let spendStat = 'atk';
  let message = '';
  let error = '';
  let submitting = false;
  const dispatch = createEventDispatcher();

  $: resolvedElement = backendElement || element || 'Generic';
  $: elementKey = String(resolvedElement || 'Generic').toLowerCase();
  $: materialKey = `${elementKey}_1`;
  $: accent = getElementColor(resolvedElement || 'Generic');
  $: elementInventory = extractElementBreakdown(items, elementKey);
  $: availableMaterials = computeUnitsFromBreakdown(elementInventory);
  $: availableSummary = (() => {
    const summary = formatCost({ item: materialKey, units: availableMaterials, breakdown: elementInventory });
    if (summary === '—') {
      return formatMaterialQuantity(availableMaterials, materialKey);
    }
    return summary;
  })();
  $: nextCostForStat = nextCosts?.[spendStat] || null;
  $: levelForStat = Number(statCounts?.[spendStat] ?? 0);
  $: totalPercentForStat = statTotals?.[spendStat] ?? 0;
  $: levelsSummary = UPGRADEABLE_STATS.map((key) => {
    const level = Number(statCounts?.[key] ?? 0);
    const percent = statTotals?.[key] ?? 0;
    return `${formatLabel(key)} L${level} (${formatPercent(percent)})`;
  }).join(', ');

  async function load({ resetStatus = false } = {}) {
    loading = true;
    if (resetStatus) {
      message = '';
      error = '';
    }
    try {
      const data = await getUpgrade(id);
      items = data.items || {};
      statTotals = data.stat_totals || {};
      statCounts = data.stat_counts || {};
      nextCosts = data.next_costs || {};
      backendElement = data.element || backendElement;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    load({ resetStatus: true });
  });

  async function spendMaterials() {
    message = '';
    error = '';
    const repeats = Math.max(1, Number(upgradeRepeats) || 1);
    submitting = true;
    try {
      const options = { repeat: repeats };
      const materialRequest = prepareMaterialRequest(nextCostForStat);
      if (materialRequest) {
        options.materials = materialRequest;
      }
      const result = await upgradeStat(id, String(spendStat), options);
      await load({ resetStatus: false });
      if (result) {
        const label = formatLabel(result.stat_upgraded || spendStat);
        const completed = Number(result.completed_upgrades) || 0;
        const percent = result.upgrade_percent;
        if (completed > 0) {
          const percentText = percent ? formatPercent(percent) : '';
          if (completed === 1) {
            message = percentText ? `Upgraded ${label} by ${percentText}.` : `Upgraded ${label}.`;
          } else {
            message = percentText
              ? `Upgraded ${label} ${completed}× for ${percentText} total.`
              : `Upgraded ${label} ${completed}×.`;
          }
        } else {
          message = `No upgrades applied to ${label}.`;
        }
        if (result.error) {
          error = result.error;
        }
        if (result.materials_remaining != null) {
          items = { ...items, [materialKey]: result.materials_remaining };
        }
        dispatch('upgraded', { id, stat: String(spendStat), repeats, result });
      }
    } catch (err) {
      error = err?.message || 'Upgrade failed';
    } finally {
      submitting = false;
    }
  }
</script>

<div class="upgrade-panel" data-testid="upgrade-panel" style={`--accent: ${accent}`}
>
  {#if loading}
    <div>Loading upgrades...</div>
  {:else}
    <div class="row">
      <div class="label">Material</div>
      <div class="value">{formatMaterialName(materialKey)}</div>
    </div>
    <div class="row">
      <div class="label">Available</div>
      <div class="value">{availableSummary}</div>
    </div>

    <div class="section">
      <div class="label">Spend materials</div>
      <div class="controls">
        <label>Stat
          <select bind:value={spendStat} class="themed">
            {#each UPGRADEABLE_STATS as s}
              <option value={s}>{formatLabel(s)}</option>
            {/each}
          </select>
        </label>
        <label>Times
          <input type="number" min="1" bind:value={upgradeRepeats} class="themed" />
        </label>
        <button
          class="themed"
          on:click={spendMaterials}
          disabled={submitting || upgradeRepeats < 1 || availableMaterials <= 0}
        >
          {submitting ? 'Spending…' : 'Spend materials'}
        </button>
      </div>
      <div class="hint">Level {levelForStat} • Bonus {formatPercent(totalPercentForStat)}</div>
      <div class="hint">Next {formatLabel(spendStat)} cost: {formatCost(nextCostForStat)}</div>
      {#if levelsSummary}
        <div class="hint">Levels: {levelsSummary}</div>
      {/if}
    </div>

    {#if message}
      <div class="msg">{message}</div>
    {/if}
    {#if error}
      <div class="msg error">{error}</div>
    {/if}
  {/if}
</div>

<style>
.upgrade-panel { margin-top: 0.5rem; font-size: 0.9rem; color: #ddd; display: flex; flex-direction: column; gap: 0.4rem; }
.row { display: flex; justify-content: space-between; gap: 0.5rem; }
.label { color: #bbb; }
.value { color: #eee; }
.section { margin-top: 0.35rem; padding-top: 0.35rem; border-top: 1px solid rgba(255,255,255,0.15); }
.controls { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem; flex-wrap: wrap; }

/* Themed form controls and buttons */
.themed { background: #111; color: #fff; border: 1px solid rgba(255,255,255,0.28); border-radius: 6px; padding: 0.28rem 0.5rem; font-size: 0.85rem; }
.themed:focus, .themed:focus-visible { outline: none; border-color: var(--accent, #8ac); box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent, #8ac) 25%, transparent); }
button.themed { cursor: pointer; background: color-mix(in srgb, var(--accent, #8ac) 18%, #0a0a0a); border-color: var(--accent, #8ac); }
button.themed:hover { background: color-mix(in srgb, var(--accent, #8ac) 30%, #0a0a0a); }
button.themed:disabled { opacity: 0.55; cursor: not-allowed; filter: grayscale(0.2); }

.hint { font-size: 0.8rem; color: #aaa; margin-top: 0.2rem; }
.msg { margin-top: 0.3rem; color: #9fd6ff; font-size: 0.85rem; }
.msg.error { color: #ff9f9f; }
</style>
