<script>
  import { createEventDispatcher, onDestroy, setContext } from 'svelte';
  import { get } from 'svelte/store';
  import {
    BATTLE_REVIEW_CONTEXT_KEY,
    createBattleReviewState
  } from '../systems/battleReview/state.js';
  import { buildBattleReviewLink } from '../systems/battleReview/urlState.js';
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
  export let initialState = null;

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
    shareableState,
    applyViewState,
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

  let lastInitialSignature = '';
  $: initialSignature = initialState ? JSON.stringify(initialState) : '';
  $: if (initialSignature && initialSignature !== lastInitialSignature) {
    applyViewState(initialState);
    lastInitialSignature = initialSignature;
  }

  let copyState = 'idle';
  let copyTimer = null;
  let shareSnapshot = null;

  $: shareSnapshot = $shareableState;
  $: if (shareSnapshot) {
    dispatch('statechange', shareSnapshot);
  }

  onDestroy(() => {
    state.destroy();
    if (copyTimer) clearTimeout(copyTimer);
  });

  function fmt(n) {
    try {
      return Number(n).toLocaleString();
    } catch (err) {
      return String(n ?? '—');
    }
  }

  function scheduleCopyReset() {
    if (copyTimer) clearTimeout(copyTimer);
    copyTimer = setTimeout(() => {
      copyState = 'idle';
    }, 2200);
  }

  function fallbackCopy(text) {
    try {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'absolute';
      textarea.style.left = '-9999px';
      document.body.appendChild(textarea);
      textarea.select();
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);
      return success;
    } catch {
      return false;
    }
  }

  async function copyLogsLink() {
    if (typeof window === 'undefined') return;
    const shareState = get(shareableState);
    const origin = window.location.origin;
    const link = buildBattleReviewLink(shareState.runId || runId, shareState, { origin });

    const writeClipboard = async () => {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(link);
        return true;
      }
      return fallbackCopy(link);
    };

    try {
      const success = await writeClipboard();
      copyState = success ? 'copied' : 'error';
      if (!success) {
        console.error('copyLogsLink: navigator.clipboard unavailable');
      }
    } catch (error) {
      const success = fallbackCopy(link);
      copyState = success ? 'copied' : 'error';
      if (!success) {
        console.error('Failed to copy logs link:', error);
      }
    }

    scheduleCopyReset();
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
    <button
      class="copy-link"
      type="button"
      on:click={copyLogsLink}
      aria-live="polite"
    >
      {#if copyState === 'copied'}
        Link copied!
      {:else if copyState === 'error'}
        Copy failed
      {:else}
        Copy Logs Link
      {/if}
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

  .copy-link {
    appearance: none;
    border: 1px solid rgba(148, 163, 184, 0.6);
    background: rgba(30, 41, 59, 0.95);
    color: #bae6fd;
    font-size: 0.78rem;
    padding: 0.35rem 0.85rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease;
  }

  .copy-link:hover {
    background: rgba(56, 189, 248, 0.2);
    color: #f0f9ff;
  }

  .copy-link:focus-visible {
    outline: 2px solid rgba(125, 211, 252, 0.9);
    outline-offset: 2px;
  }
</style>
