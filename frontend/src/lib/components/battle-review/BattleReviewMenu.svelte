<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import TripleRingSpinner from '../TripleRingSpinner.svelte';
  import BattleReview from '../BattleReview.svelte';
  import MenuPanel from '../MenuPanel.svelte';
  import { listTrackedRuns, getTrackedRun } from '../../systems/uiApi.js';
  import { deriveFightsFromRunDetails } from './battleReviewMenuHelpers.js';

  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  let runs = [];
  let runsStatus = 'idle';
  let runsError = '';
  let selectedRunId = '';
  let selectedRunSummary = null;

  let runDetails = null;
  let runStatus = 'idle';
  let runError = '';

  let selectedFightKey = '';
  let selectedBattleIndex = null;
  let fights = [];
  let runConfiguration = null;
  let modifierEntries = [];
  let rewardEntries = [];

  let runsController = null;
  let detailsController = null;
  let loadToken = 0;

  const menuPanelBackground = [
    'radial-gradient(140% 95% at 82% -10%, rgba(59, 130, 246, 0.28), transparent 65%)',
    'radial-gradient(120% 90% at 18% -18%, rgba(236, 72, 153, 0.22), transparent 60%)',
    'radial-gradient(160% 110% at 50% 120%, rgba(14, 116, 144, 0.32), transparent 70%)',
    'linear-gradient(180deg, rgba(15, 23, 42, 0.96) 0%, rgba(10, 12, 24, 0.94) 52%, rgba(15, 23, 42, 0.98) 100%)'
  ].join(', ');

  const menuPanelStyle = [
    `background: ${menuPanelBackground}`,
    '--glass-bg: linear-gradient(140deg, rgba(12, 19, 35, 0.94) 0%, rgba(8, 12, 26, 0.9) 100%)',
    '--glass-border: 1px solid rgba(148, 163, 184, 0.26)',
    '--glass-shadow: 0 28px 48px rgba(2, 6, 23, 0.58), 0 1px 0 rgba(148, 163, 184, 0.12) inset'
  ].join('; ');
  const selectOptionStyle = 'background-color: rgba(15, 23, 42, 0.94); color: #e2e8f0;';

  onMount(() => {
    loadRuns();
    return () => {
      try {
        runsController?.abort();
      } catch {}
      try {
        detailsController?.abort();
      } catch {}
    };
  });

  function runValue(run) {
    const value = run?.run_id ?? run?.id ?? '';
    return value != null ? String(value) : '';
  }

  function runLabel(run, index) {
    const label = run?.label ?? run?.name ?? '';
    const id = run?.run_id ?? run?.id ?? '';
    if (label && id) {
      return `${label} — ${id}`;
    }
    if (label) {
      return String(label);
    }
    if (id) {
      return String(id);
    }
    return `Run ${index + 1}`;
  }

  async function loadRuns() {
    runsController?.abort();
    runsController = new AbortController();
    runsStatus = 'loading';
    runsError = '';

    try {
      const { runs: list } = await listTrackedRuns({ signal: runsController.signal });
      runs = Array.isArray(list) ? list : [];
      runsStatus = 'ready';
      if (runs.length === 0) {
        selectedRunId = '';
      } else if (!runs.some((run) => runValue(run) === selectedRunId)) {
        selectedRunId = runValue(runs[0]);
      }
    } catch (error) {
      if (error?.name === 'AbortError') {
        return;
      }
      runs = [];
      runsStatus = 'error';
      runsError = error?.message || 'Failed to load runs.';
      selectedRunId = '';
    }
  }

  async function loadRunDetails(id) {
    const token = ++loadToken;
    detailsController?.abort();
    detailsController = new AbortController();
    runStatus = 'loading';
    runError = '';
    runDetails = null;

    try {
      const data = await getTrackedRun(id, { signal: detailsController.signal });
      if (token !== loadToken) {
        return;
      }
      runDetails = data || {};
      runStatus = 'ready';
    } catch (error) {
      if (error?.name === 'AbortError') {
        return;
      }
      if (token !== loadToken) {
        return;
      }
      runDetails = null;
      runStatus = 'error';
      runError = error?.message || 'Failed to load run details.';
    }
  }

  $: if (selectedRunId) {
    loadRunDetails(selectedRunId);
  }

  $: if (!selectedRunId) {
    runDetails = null;
    if (runsStatus === 'ready') {
      runStatus = 'idle';
    }
  }

  $: fights = deriveFightsFromRunDetails(runDetails);

  $: {
    if (!fights.length) {
      selectedFightKey = '';
    } else if (!fights.some((fight) => String(fight.battleIndex) === selectedFightKey)) {
      selectedFightKey = String(fights[0].battleIndex);
    }
  }

  $: {
    const match = fights.find((fight) => String(fight.battleIndex) === selectedFightKey) || null;
    selectedBattleIndex = match?.battleIndex ?? null;
  }

  $: selectedRunSummary = runs.find((run) => runValue(run) === selectedRunId) || null;
  $: runConfiguration =
    runDetails?.run?.configuration ||
    runDetails?.configuration ||
    selectedRunSummary?.configuration ||
    null;
  $: modifierEntries = configurationEntries(runConfiguration?.modifiers);
  $: rewardEntries = configurationEntries(
    runConfiguration?.rewardBonuses ?? runConfiguration?.reward_bonuses
  );

  function handleRunChange(event) {
    selectedRunId = event?.target?.value || '';
  }

  function handleFightChange(event) {
    selectedFightKey = event?.target?.value || '';
  }

  function closeMenu() {
    dispatch('close');
  }

  function configurationEntries(source) {
    if (!source) {
      return [];
    }
    if (Array.isArray(source)) {
      return source.map((entry, index) => {
        if (isPlainObject(entry)) {
          const label = entry.label ?? entry.name ?? entry.id ?? `Entry ${index + 1}`;
          const value =
            entry.value ?? entry.amount ?? entry.bonus ?? entry.modifier ?? entry.score ?? entry;
          return [label, value];
        }
        return [`Entry ${index + 1}`, entry];
      });
    }
    if (isPlainObject(source)) {
      return Object.entries(source);
    }
    return [['value', source]];
  }

  function formatConfigValue(value) {
    if (value === null || value === undefined) {
      return '—';
    }
    if (typeof value === 'number') {
      return Number.isInteger(value) ? value : value.toFixed(2);
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    if (Array.isArray(value)) {
      return value.map((item) => formatConfigValue(item)).join(', ');
    }
    if (isPlainObject(value)) {
      try {
        return JSON.stringify(value);
      } catch (error) {
        return String(value);
      }
    }
    return String(value);
  }

  function formatRunTypeLabel(value) {
    if (!value) {
      return 'Unknown';
    }
    const str = String(value).replace(/[_-]+/g, ' ');
    return str
      .split(' ')
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  function isPlainObject(value) {
    return !!value && typeof value === 'object' && !Array.isArray(value);
  }
</script>

<MenuPanel
  class="battle-review-menu"
  data-testid="battle-review-menu"
  padding="1rem"
  {reducedMotion}
  style={menuPanelStyle}
>
  <header class="menu-header">
    <h2>Battle Review Archive</h2>
    <button type="button" class="close-btn" on:click={closeMenu}>Close</button>
  </header>

  <section class="selectors">
    <label class="selector-card">
      <span class="label-text">Run</span>
      {#if runsStatus === 'loading'}
        <div class="loading-line" role="status" aria-live="polite">
          <TripleRingSpinner {reducedMotion} />
          <span>Loading runs…</span>
        </div>
      {:else if runsStatus === 'error'}
        <div class="status-text error" role="alert">{runsError}</div>
      {:else if runs.length === 0}
        <div class="status-text empty">No tracked runs found.</div>
      {:else}
        <select on:change={handleRunChange} bind:value={selectedRunId}>
          {#each runs as run, index (runValue(run))}
            <option value={runValue(run)} style={selectOptionStyle}>{runLabel(run, index)}</option>
          {/each}
        </select>
      {/if}
    </label>

    <label class="selector-card">
      <span class="label-text">Fight</span>
      {#if runStatus === 'loading' && runsStatus !== 'error'}
        <div class="loading-line" role="status" aria-live="polite">
          <TripleRingSpinner {reducedMotion} />
          <span>Loading battles…</span>
        </div>
      {:else if runStatus === 'error'}
        <div class="status-text error" role="alert">{runError}</div>
      {:else if fights.length === 0}
        <div class="status-text empty">
          {selectedRunId ? 'No fights recorded for this run.' : 'Select a run to view fights.'}
        </div>
      {:else}
        <select on:change={handleFightChange} bind:value={selectedFightKey}>
          {#each fights as fight (String(fight.battleIndex))}
            <option value={String(fight.battleIndex)} style={selectOptionStyle}>{fight.label}</option>
          {/each}
        </select>
      {/if}
    </label>
  </section>

  {#if runConfiguration}
    <section class="run-configuration">
      <h3>Run Configuration</h3>
      <div class="config-row">
        <span class="config-label">Run Type</span>
        <span class="config-value">{formatRunTypeLabel(runConfiguration.runType ?? runConfiguration.run_type)}</span>
      </div>
      {#if modifierEntries.length}
        <div class="config-subheading">Modifiers</div>
        <ul class="config-list">
          {#each modifierEntries as [label, value], index (`modifier-${index}`)}
            <li>
              <span class="config-label">{label}</span>
              <span class="config-value">{formatConfigValue(value)}</span>
            </li>
          {/each}
        </ul>
      {/if}
      {#if rewardEntries.length}
        <div class="config-subheading">Reward Bonuses</div>
        <ul class="config-list">
          {#each rewardEntries as [label, value], index (`reward-${index}`)}
            <li>
              <span class="config-label">{label}</span>
              <span class="config-value">{formatConfigValue(value)}</span>
            </li>
          {/each}
        </ul>
      {/if}
    </section>
  {/if}

  {#if selectedBattleIndex}
    <section class="review-host">
      <BattleReview
        runId={selectedRunId}
        battleIndex={selectedBattleIndex}
        {reducedMotion}
      />
    </section>
  {/if}
</MenuPanel>

<style>
  :global(.battle-review-menu) {
    gap: 1rem;
    color: #e2e8f0;
    color-scheme: dark;
  }

  .menu-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.25rem 0;
  }

  .menu-header h2 {
    margin: 0;
    font-size: 1.4rem;
    letter-spacing: 0.02em;
  }

  .close-btn {
    appearance: none;
    border: 1px solid rgba(148, 163, 184, 0.55);
    background: color-mix(in oklab, var(--glass-bg) 78%, rgba(148, 163, 184, 0.32) 22%);
    color: #f0f9ff;
    padding: 0.38rem 0.9rem;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
  }

  .close-btn:hover {
    background: color-mix(in oklab, rgba(56, 189, 248, 0.28) 45%, var(--glass-bg) 55%);
    border-color: rgba(125, 211, 252, 0.65);
    color: #f8fafc;
  }

  .close-btn:focus-visible {
    outline: 2px solid rgba(125, 211, 252, 0.9);
    outline-offset: 2px;
  }

  .selectors {
    display: grid;
    gap: 0.75rem;
  }

  @media (min-width: 780px) {
    .selectors {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      align-items: end;
    }
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.95rem;
  }

  .selector-card {
    padding: 0.85rem;
    background: linear-gradient(0deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.03)), var(--glass-bg);
    border: var(--glass-border);
    box-shadow: var(--glass-shadow);
    backdrop-filter: var(--glass-filter);
    width: 100%;
    box-sizing: border-box;
  }

  .label-text {
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  :global(.battle-review-menu select) {
    appearance: none;
    background-color: rgba(15, 23, 42, 0.95);
    border: 1px solid rgba(148, 163, 184, 0.45);
    box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.3);
    color: #f8fafc;
    color-scheme: dark;
    padding: 0.5rem 0.65rem;
    font-size: 0.95rem;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, color 0.18s ease;
    width: 100%;
  }

  :global(.battle-review-menu select:hover) {
    border-color: rgba(125, 211, 252, 0.65);
    box-shadow: inset 0 0 0 1px rgba(56, 189, 248, 0.22);
  }

  :global(.battle-review-menu select:focus-visible) {
    outline: 2px solid rgba(125, 211, 252, 0.9);
    outline-offset: 2px;
  }

  :global(.battle-review-menu select option),
  :global(.battle-review-menu select optgroup) {
    background-color: rgba(15, 23, 42, 0.94);
    color: #e2e8f0;
    font: inherit;
  }

  :global(.battle-review-menu select option:hover),
  :global(.battle-review-menu select option:checked),
  :global(.battle-review-menu select option:focus) {
    background-color: rgba(56, 189, 248, 0.28);
    color: #f8fafc;
  }

  :global(.battle-review-menu select option:disabled) {
    color: rgba(148, 163, 184, 0.65);
  }

  .loading-line {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-height: 2.2rem;
    padding: 0.45rem 0.5rem;
    background: color-mix(in oklab, rgba(148, 163, 184, 0.35) 25%, transparent 75%);
    border: 1px solid rgba(148, 163, 184, 0.35);
  }

  .status-text {
    font-size: 0.9rem;
    opacity: 0.85;
    min-height: 2.2rem;
    display: flex;
    align-items: center;
    padding: 0.45rem 0.5rem;
    background: color-mix(in oklab, rgba(148, 163, 184, 0.22) 20%, transparent 80%);
    border: 1px solid rgba(148, 163, 184, 0.35);
  }

  .status-text.error {
    color: #fecaca;
    border-color: rgba(239, 68, 68, 0.45);
    background: linear-gradient(0deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.04)), var(--glass-bg);
  }

  .status-text.empty {
    color: rgba(226, 232, 240, 0.8);
  }

  .run-configuration {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.9rem 1rem;
    background: linear-gradient(0deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.03)), var(--glass-bg);
    border: var(--glass-border);
    box-shadow: var(--glass-shadow);
    backdrop-filter: var(--glass-filter);
  }

  .run-configuration h3 {
    margin: 0;
    font-size: 1.1rem;
    letter-spacing: 0.02em;
  }

  .config-row {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
    font-size: 0.95rem;
  }

  .config-subheading {
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    opacity: 0.75;
  }

  .config-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .config-list li {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    font-size: 0.9rem;
  }

  .config-label {
    font-weight: 600;
  }

  .config-value {
    font-variant-numeric: tabular-nums;
    text-align: right;
  }

  .review-host {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-height: 0;
  }

  .review-host :global(.battle-review-panel) {
    background: linear-gradient(0deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02)), var(--glass-bg);
    border: var(--glass-border);
    box-shadow: var(--glass-shadow);
    backdrop-filter: var(--glass-filter);
  }
</style>
