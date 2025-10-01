<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import TripleRingSpinner from '../TripleRingSpinner.svelte';
  import BattleReview from '../BattleReview.svelte';
  import MenuPanel from '../MenuPanel.svelte';
  import { listTrackedRuns, getTrackedRun } from '../../systems/uiApi.js';

  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  let runs = [];
  let runsStatus = 'idle';
  let runsError = '';
  let selectedRunId = '';

  let runDetails = null;
  let runStatus = 'idle';
  let runError = '';

  let selectedFightKey = '';
  let selectedBattleIndex = null;
  let fights = [];

  let runsController = null;
  let detailsController = null;
  let loadToken = 0;

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

  function deriveBattleIndex(entry, fallback) {
    const candidates = [
      entry?.battle_index,
      entry?.battleIndex,
      entry?.index,
      entry?.battle?.index,
      entry?.id
    ];
    for (const candidate of candidates) {
      const n = Number(candidate);
      if (Number.isFinite(n) && n > 0) {
        return Math.floor(n);
      }
    }
    return fallback ?? null;
  }

  function deriveFightLabel(entry, fallbackIndex) {
    const candidates = [
      entry?.battle_name,
      entry?.battleName,
      entry?.room_name,
      entry?.roomName,
      entry?.room_type,
      entry?.roomType
    ];
    for (const candidate of candidates) {
      if (candidate) {
        return String(candidate);
      }
    }
    return `Fight ${fallbackIndex}`;
  }

  $: fights = (() => {
    const summaries =
      runDetails?.battle_summaries || runDetails?.battleSummaries || [];
    if (!Array.isArray(summaries) || summaries.length === 0) {
      return [];
    }
    return summaries.map((summary, idx) => {
      const fallback = idx + 1;
      const battleIndex = deriveBattleIndex(summary, fallback);
      return {
        battleIndex,
        label: deriveFightLabel(summary, battleIndex || fallback),
        summary
      };
    });
  })();

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

  function handleRunChange(event) {
    selectedRunId = event?.target?.value || '';
  }

  function handleFightChange(event) {
    selectedFightKey = event?.target?.value || '';
  }

  function closeMenu() {
    dispatch('close');
  }
</script>

<MenuPanel
  class="battle-review-menu"
  data-testid="battle-review-menu"
  padding="1rem"
  {reducedMotion}
>
  <header class="menu-header">
    <h2>Battle Review Archive</h2>
    <button type="button" class="close-btn" on:click={closeMenu}>Close</button>
  </header>

  <section class="selectors">
    <label>
      <span class="label-text">Run</span>
      {#if runsStatus === 'loading'}
        <div class="loading-line">
          <TripleRingSpinner {reducedMotion} />
          <span>Loading runs…</span>
        </div>
      {:else if runsStatus === 'error'}
        <div class="status-text error">{runsError}</div>
      {:else if runs.length === 0}
        <div class="status-text empty">No tracked runs found.</div>
      {:else}
        <select on:change={handleRunChange} bind:value={selectedRunId}>
          {#each runs as run, index (runValue(run))}
            <option value={runValue(run)}>{runLabel(run, index)}</option>
          {/each}
        </select>
      {/if}
    </label>

    <label>
      <span class="label-text">Fight</span>
      {#if runStatus === 'loading' && runsStatus !== 'error'}
        <div class="loading-line">
          <TripleRingSpinner {reducedMotion} />
          <span>Loading battles…</span>
        </div>
      {:else if runStatus === 'error'}
        <div class="status-text error">{runError}</div>
      {:else if fights.length === 0}
        <div class="status-text empty">
          {selectedRunId ? 'No fights recorded for this run.' : 'Select a run to view fights.'}
        </div>
      {:else}
        <select on:change={handleFightChange} bind:value={selectedFightKey}>
          {#each fights as fight (String(fight.battleIndex))}
            <option value={String(fight.battleIndex)}>{fight.label}</option>
          {/each}
        </select>
      {/if}
    </label>
  </section>

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
    color: #fff;
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
    background: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: inherit;
    padding: 0.35rem 0.8rem;
    cursor: pointer;
    border-radius: 4px;
    font-size: 0.95rem;
    transition: background 0.2s ease, box-shadow 0.2s ease;
  }

  .close-btn:hover {
    background: rgba(120, 180, 255, 0.25);
    box-shadow: 0 2px 8px rgba(0, 40, 120, 0.18);
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
    gap: 0.35rem;
    font-size: 0.95rem;
  }

  .label-text {
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  select {
    background: rgba(20, 30, 55, 0.9);
    border: 1px solid rgba(130, 160, 220, 0.4);
    color: inherit;
    border-radius: 6px;
    padding: 0.5rem 0.6rem;
    font-size: 0.95rem;
    appearance: none;
  }

  .loading-line {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-height: 2.2rem;
  }

  .status-text {
    font-size: 0.9rem;
    opacity: 0.85;
    min-height: 2.2rem;
    display: flex;
    align-items: center;
  }

  .status-text.error {
    color: #f8a0a0;
  }

  .status-text.empty {
    color: rgba(255, 255, 255, 0.7);
  }

  .review-host {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-height: 0;
  }

  .review-host :global(.battle-review-panel) {
    background: rgba(15, 20, 35, 0.78);
    border: 1px solid rgba(110, 140, 200, 0.35);
    box-shadow: 0 18px 42px rgba(5, 10, 25, 0.6);
  }
</style>
