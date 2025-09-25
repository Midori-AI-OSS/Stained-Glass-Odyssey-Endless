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
import MenuPanel from './MenuPanel.svelte';

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

<MenuPanel class="battle-review-panel" padding="1.25rem" {reducedMotion}>
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
</MenuPanel>

<style>
  .battle-review-layout {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
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
    padding: 0.75rem 0.9rem;
    background: linear-gradient(0deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05)), var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
    border-radius: 0;
  }

  .header-metric {
    padding: 0.3rem 0.65rem;
    background: color-mix(in oklab, rgba(148, 163, 184, 0.4) 32%, transparent 68%);
    border: 1px solid rgba(148, 163, 184, 0.45);
    border-radius: 0;
    box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.45);
  }

  .spacer {
    flex: 1;
  }

  .events-toggle,
  .copy-link {
    appearance: none;
    border: 1px solid rgba(148, 163, 184, 0.55);
    background: color-mix(in oklab, var(--glass-bg) 80%, rgba(148, 163, 184, 0.35) 20%);
    color: #e2e8f0;
    font-size: 0.78rem;
    padding: 0.4rem 0.85rem;
    border-radius: 0;
    cursor: pointer;
    transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
  }

  .events-toggle:hover,
  .copy-link:hover {
    background: color-mix(in oklab, rgba(56, 189, 248, 0.22) 45%, var(--glass-bg) 55%);
    border-color: rgba(125, 211, 252, 0.65);
    color: #f0f9ff;
  }

  .events-toggle.busy {
    opacity: 0.7;
    cursor: progress;
  }

  .copy-link {
    color: #bae6fd;
  }

  .copy-link:focus-visible,
  .events-toggle:focus-visible {
    outline: 2px solid rgba(125, 211, 252, 0.9);
    outline-offset: 2px;
  }
</style>
