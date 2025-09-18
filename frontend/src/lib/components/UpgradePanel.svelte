<script>
  import { onMount } from 'svelte';
  import { getUpgrade, upgradeCharacter, upgradeStat } from '../systems/api.js';
  import { createEventDispatcher } from 'svelte';
  import { getElementColor } from '../systems/assetLoader.js';

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
  let statUpgrades = [];
  let statTotals = {};
  let nextCosts = {};
  let upgradePoints = 0;
  let loading = true;
  let starLevel = 4;
  let itemCount = 1;
  let upgradeRepeats = 1;
  let spendStat = 'atk';
  let message = '';
  const dispatch = createEventDispatcher();

  const isPlayer = () => String(id) === 'player';
  const elem = () => String(element || '').toLowerCase();

  async function load() {
    loading = true;
    message = '';
    try {
      const data = await getUpgrade(id);
      items = data.items || {};
      statUpgrades = data.stat_upgrades || [];
      statTotals = data.stat_totals || {};
      nextCosts = data.next_costs || {};
      upgradePoints = Number(data.upgrade_points) || 0;
    } finally {
      loading = false;
    }
  }

  onMount(load);

  $: have1 = items[`${elem()}_1`] || 0;
  $: have2 = items[`${elem()}_2`] || 0;
  $: have3 = items[`${elem()}_3`] || 0;
  $: have4 = items[`${elem()}_4`] || 0;
  $: accent = getElementColor(element || 'Generic');

  // For the player, total available items at the selected star across all elements
  $: totalAtStar = Object.entries(items)
    .filter(([k]) => k.endsWith(`_${starLevel}`))
    .reduce((acc, [, v]) => acc + (v || 0), 0);

  $: canUse = isPlayer()
    ? (totalAtStar >= itemCount && itemCount > 0)
    : ((items[`${elem()}_${starLevel}`] || 0) >= itemCount && itemCount > 0);

  async function useItems() {
    message = '';
    try {
      await upgradeCharacter(id, Number(starLevel), Number(itemCount));
      await load();
      message = 'Converted to upgrade points.';
      dispatch('upgraded', { id, starLevel: Number(starLevel), itemCount: Number(itemCount) });
    } catch (e) {
      message = e?.message || 'Upgrade failed';
    }
  }

  function formatPoints(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return '—';
    return Math.max(0, Math.round(num)).toLocaleString();
  }

  function formatCost(value) {
    const points = formatPoints(value);
    return points === '—' ? '—' : `${points} pts`;
  }

  function formatPercent(value) {
    if (value == null) return '0%';
    const num = Number(value) * 100;
    if (!Number.isFinite(num)) return '0%';
    let digits = 2;
    const abs = Math.abs(num);
    if (abs >= 100) digits = 0;
    else if (abs >= 10) digits = 1;
    let formatted = num.toFixed(digits);
    formatted = formatted.replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
    const sign = num >= 0 ? '+' : '';
    return `${sign}${formatted}%`;
  }

  async function spendPointsFn() {
    message = '';
    const repeats = Math.max(1, Number(upgradeRepeats) || 1);
    try {
      let result = null;
      for (let i = 0; i < repeats; i += 1) {
        result = await upgradeStat(id, String(spendStat));
      }
      await load();
      if (result) {
        const label = result.stat_upgraded || spendStat;
        const bonus = formatPercent(result.upgrade_percent);
        message = `Upgraded ${label} by ${bonus}.`;
      } else {
        message = `Upgraded ${spendStat}.`;
      }
      dispatch('upgraded', { id, stat: String(spendStat), repeats });
    } catch (e) {
      message = e?.message || 'Spend failed';
    }
  }
</script>

<div class="upgrade-panel" data-testid="upgrade-panel" style={`--accent: ${accent}`}
>
  {#if loading}
    <div>Loading upgrades...</div>
  {:else}
    <div class="row">
      <div class="label">Element items</div>
      <div class="value">{element}: 1★ {have1}, 2★ {have2}, 3★ {have3}, 4★ {have4}</div>
    </div>
    <div class="row"><div class="label">Upgrade points</div><div class="value">{upgradePoints}</div></div>

    <div class="section">
      <div class="label">Convert items</div>
      <div class="controls">
        <label>Star
          <select bind:value={starLevel} class="themed">
            <option value={1}>1★</option>
            <option value={2}>2★</option>
            <option value={3}>3★</option>
            <option value={4}>4★</option>
          </select>
        </label>
        <label>Count
          <input type="number" min="1" bind:value={itemCount} class="themed" />
        </label>
        <button class="themed" on:click={useItems} disabled={!canUse}>Convert to Points</button>
      </div>
      <div class="hint">Player can convert any element items; others must match {element}.</div>
    </div>

    <div class="section">
      <div class="label">Spend points</div>
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
        <button class="themed" on:click={spendPointsFn} disabled={!upgradePoints || upgradeRepeats < 1}>Spend</button>
      </div>
      <div class="hint">Next cost for {spendStat}: {formatCost(nextCosts[spendStat])}</div>
      {#if Object.keys(statTotals).length}
        <div class="hint">
          Totals:
          {UPGRADEABLE_STATS.map((k) => {
            const val = Number(statTotals?.[k] ?? 0);
            return `${formatLabel(k)}: ${(val * 100).toFixed(2)}%`;
          }).join(', ')}
        </div>
      {/if}
    </div>

    {#if message}
      <div class="msg">{message}</div>
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
</style>
