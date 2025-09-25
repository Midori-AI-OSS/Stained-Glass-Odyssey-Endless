<script>
  import { createEventDispatcher, onDestroy, setContext } from 'svelte';
  import {
    BATTLE_REVIEW_CONTEXT_KEY,
    createBattleReviewState
  } from '../systems/battleReview/state.js';
  import TabsShell from './battle-review/TabsShell.svelte';
  import EventsDrawer from './battle-review/EventsDrawer.svelte';

  export let runId = '';
  export let battleIndex = 0;
  export let cards = [];
  export let relics = [];
  export let party = [];
  export let foes = [];
  export let partyData = [];
  export let foeData = [];
  export let reducedMotion = false;
  export let prefetchedSummary = null;

  const dispatch = createEventDispatcher();

  const state = createBattleReviewState({
    runId,
    battleIndex,
    cards,
    relics,
    party,
    foes,
    partyData,
    foeData,
    reducedMotion,
    prefetchedSummary
  });

  const {
    summary,
    resultSummary,
    eventsOpen,
    eventsStatus,
    toggleEvents,
    updateProps
  } = state;

  setContext(BATTLE_REVIEW_CONTEXT_KEY, {
    ...state,
    dispatchSelect: (detail) => dispatch('select', detail)
  });

  $: updateProps({
    runId,
    battleIndex,
    cards,
    relics,
    party,
    foes,
    partyData,
    foeData,
    reducedMotion,
    prefetchedSummary
  });

  onDestroy(() => {
    state.destroy();
  });

  function fmt(n) {
    try {
      return Number(n).toLocaleString();
    } catch (err) {
      return String(n ?? '—');
    }
  }
</script>

<svelte:options accessors={true} />

<div class="battle-review-layout">
  <header class="review-header">
    <div class="header-metric">Result: {$resultSummary.result}</div>
    <div class="header-metric">
      Duration: {$resultSummary.duration != null ? `${$resultSummary.duration}s` : '—'}
    </div>
    <div class="header-metric">Events: {fmt($resultSummary.eventCount)}</div>
    <div class="header-metric">Criticals: {fmt($summary?.critical_hits ? Object.values($summary.critical_hits).reduce((a, b) => a + b, 0) : 0)}</div>
    <span class="spacer"></span>
    <button
      class="events-toggle"
      class:busy={$eventsStatus === 'loading'}
      on:click={toggleEvents}
      type="button"
    >
      {$eventsOpen ? 'Hide' : 'Show'} Event Log
    </button>
  </header>

  <TabsShell />
  <EventsDrawer />
</div>

<style>
  .battle-review-layout {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }

  .review-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    font-size: 0.85rem;
    color: #f1f5f9;
  }

  .header-metric {
    padding: 0.25rem 0.5rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  .spacer {
    flex: 1;
  }

  .events-toggle {
    appearance: none;
    border: 1px solid rgba(148, 163, 184, 0.6);
    background: rgba(15, 23, 42, 0.9);
    color: #e2e8f0;
    font-size: 0.78rem;
    padding: 0.35rem 0.75rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease;
  }

  .events-toggle:hover {
    background: rgba(51, 65, 85, 0.8);
    color: #f8fafc;
  }

  .events-toggle.busy {
    opacity: 0.7;
    cursor: progress;
  }
</style>
