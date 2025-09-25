<script>
  import { onDestroy, onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import BattleReview from '$lib/components/BattleReview.svelte';
  import {
    parseBattleReviewSearchParams,
    buildBattleReviewLink
  } from '$lib/systems/battleReview/urlState.js';
  import { loadSettings, motionStore } from '$lib/systems/settingsStorage.js';

  let reducedMotion = false;
  let motionUnsub = null;

  onMount(() => {
    loadSettings();
    motionUnsub = motionStore.subscribe((value) => {
      reducedMotion = Boolean(value?.globalReducedMotion);
    });
  });

  onDestroy(() => {
    motionUnsub?.();
  });

  $: currentPage = $page;
  $: runId = currentPage.params.run_id;
  $: initialState = parseBattleReviewSearchParams(currentPage.url.searchParams);
  $: battleIndex = initialState.battleIndex;

  function handleStateChange(event) {
    const detail = event.detail || {};
    if (detail.runId && detail.runId !== runId) {
      return;
    }
    const nextLink = buildBattleReviewLink(runId, detail, { origin: '' });
    const currentPath = `${currentPage.url.pathname}${currentPage.url.search}`;
    if (nextLink !== currentPath) {
      goto(nextLink, { replaceState: true, noScroll: true, keepfocus: true });
    }
  }
</script>

<svelte:head>
  <title>Battle Logs — {runId}</title>
</svelte:head>

<main class="logs-page" aria-labelledby="logs-heading">
  <h1 id="logs-heading" class="sr-only">Battle logs for run {runId}</h1>
  <div class="logs-shell">
    <BattleReview
      {runId}
      {battleIndex}
      reducedMotion={reducedMotion}
      initialState={initialState}
      cards={[]}
      relics={[]}
      party={[]}
      foes={[]}
      on:statechange={handleStateChange}
    />
  </div>
</main>

<style>
  .logs-page {
    display: flex;
    justify-content: center;
    padding: 2rem 1rem 4rem;
    background: radial-gradient(circle at top, rgba(15, 23, 42, 0.85), rgba(2, 6, 23, 0.95));
    min-height: 100vh;
    color: #e2e8f0;
  }

  .logs-shell {
    width: min(1100px, 100%);
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }
</style>
