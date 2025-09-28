<!--
  OverlayHost.svelte
  Renders all modal overlays based on the overlayView store
  and forwards user actions to the parent GameViewport.
-->
<script>
  import { overlayView, overlayData } from '../systems/OverlayController.js';
  import { createEventDispatcher } from 'svelte';
  import OverlaySurface from './OverlaySurface.svelte';
  import PopupWindow from './PopupWindow.svelte';
  import PartyPicker from './PartyPicker.svelte';
  import PullsMenu from './PullsMenu.svelte';
  import BattleReview from './BattleReview.svelte';
  import RewardOverlay from './RewardOverlay.svelte';
  import PullResultsOverlay from './PullResultsOverlay.svelte';
  import CharacterEditor from './CharacterEditor.svelte';
  import Inventory from './Inventory.svelte';
  import SettingsMenu from './SettingsMenu.svelte';
  import Guidebook from './Guidebook.svelte';
  import RunChooser from './RunChooser.svelte';
  import ShopMenu from './ShopMenu.svelte';
  import BattleView from './BattleView.svelte';
  import ErrorOverlay from './ErrorOverlay.svelte';
  import BackendNotReady from './BackendNotReady.svelte';
  import BackendShutdownOverlay from './BackendShutdownOverlay.svelte';
  import FloatingLoot from './FloatingLoot.svelte';
  import CombatViewer from './CombatViewer.svelte';
  import { rewardOpen as computeRewardOpen } from '../systems/viewportState.js';
  import { getBattleSummary } from '../systems/uiApi.js';
  import { motionStore } from '../systems/settingsStorage.js';
  import { setRewardOverlayOpen, setReviewOverlayState } from '../systems/overlayState.js';

  export let selected = [];
  export let runId = '';
  export let roomData = null;
  export let shopProcessing = false;
  export let battleSnapshot = null;
  export let editorState = {};
  export let sfxVolume = 5;
  export let musicVolume = 5;
  export let voiceVolume = 5;
  export let framerate = 60;
  export let reducedMotion = false; // Legacy prop for backward compatibility
  export let showActionValues = false;
  export let showTurnCounter = true;
  export let flashEnrageCounter = true;
  export let fullIdleMode = false;
  export let skipBattleReview = false;
  export let animationSpeed = 1;
  export let selectedParty = [];
  export let battleActive = false;
  export let backendFlavor = '';

  // Use granular motion settings with fallback to legacy prop
  $: motionSettings = $motionStore || { 
    globalReducedMotion: false, 
    simplifyOverlayTransitions: false 
  };
  $: effectiveReducedMotion = reducedMotion || motionSettings.globalReducedMotion;
  $: simplifiedTransitions = motionSettings.simplifyOverlayTransitions;
  $: overlayReducedMotion = simplifiedTransitions ? true : effectiveReducedMotion;

  const dispatch = createEventDispatcher();
  const now = () => new Date().toISOString();
  function logOverlay(msg, extra = {}) {
    try {
      console.log(`[OverlayHost] ${now()} ${msg}`, { runId, result: roomData?.result, battle_index: roomData?.battle_index, ...extra });
    } catch (e) {}
  }
  // Determine whether to show rewards overlay based on raw room data.
  // Floating loot messages are suppressed after first display via `lootConsumed`,
  // but the overlay should remain visible until the player advances.
  $: rewardOpen = computeRewardOpen(roomData, battleActive);
  // Review should display after a battle finishes, once reward choices (if any) are done.
  // Only show review when we have a valid battle_index to load summaries
  $: reviewOpen = Boolean(
    roomData && (roomData.result === 'battle' || roomData.result === 'boss') && !battleActive &&
    typeof roomData.battle_index === 'number' && roomData.battle_index > 0
  );
  // Force BattleReview to fully unmount/remount per battle to GC internal state
  $: reviewKey = `${runId}|${roomData?.battle_index || 0}`;

  // Gate showing the review until the battle summary is ready
  let reviewReady = false;
  let reviewSummary = null;
  let reviewLoadingToken = 0;
  async function waitForReview(battleIndex, tokenRef) {
    // Retry a few times while backend finalizes logs
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    for (let attempt = 0; attempt < 10; attempt++) {
      // If another request superseded this one, stop
      if (tokenRef.value !== reviewLoadingToken) return;
      try {
        const res = await getBattleSummary(battleIndex, runId);
        if (tokenRef.value !== reviewLoadingToken) return;
        reviewSummary = res || { damage_by_type: {} };
        reviewReady = true;
        return;
      } catch (err) {
        // 404 expected briefly; keep retrying
        if (err?.status !== 404) {
          // For non-404 errors, stop waiting and let UI fall back later
          reviewSummary = null;
          reviewReady = true; // allow overlay to open rather than hang
          return;
        }
      }
      await sleep(attempt < 5 ? 350 : 700);
    }
    // After max retries, allow overlay to open even if empty
    reviewSummary = null;
    reviewReady = true;
  }

  $: if (reviewOpen) {
    // Start loading for this battle
    reviewReady = false;
    reviewSummary = null;
    const tokenRef = { value: ++reviewLoadingToken };
    logOverlay('reviewOpen true - starting waitForReview', { token: tokenRef.value });
    if (roomData?.battle_index > 0) {
      waitForReview(roomData.battle_index, tokenRef);
    }
  } else {
    // Reset gate when review is not open
    reviewReady = false;
    reviewSummary = null;
  }

  // Auto-skip Battle Review when skipBattleReview is enabled
  $: if (reviewOpen && !rewardOpen && reviewReady && skipBattleReview) {
    // Battle is complete and ready for review, but user wants to skip - advance immediately
    logOverlay('auto-skip review -> dispatch nextRoom');
    dispatch('nextRoom');
  }

  // Ensure Battle Review receives only true party members (exclude summons)
  function filterPartyEntities(list) {
    if (!Array.isArray(list)) return [];
    return list.filter((e) => {
      const obj = (e && typeof e === 'object') ? e : null;
      return !(obj && (obj.summon_type || obj.type === 'summon' || obj.is_summon));
    });
  }
  $: reviewPartyData = (() => {
    let src = [];
    if (battleSnapshot?.party && battleSnapshot.party.length) {
      src = battleSnapshot.party;
    } else if (roomData?.party && roomData.party.length) {
      src = roomData.party;
    } else if (Array.isArray(selectedParty) && selectedParty.length) {
      // Fall back to the current selectedParty (ids only) to avoid pulling in
      // backend summaries that might include summons.
      src = selectedParty;
    }
    return filterPartyEntities(src);
  })();

  // Surface overlay gating through shared overlay state helpers
  $: setRewardOverlayOpen(rewardOpen);
  $: setReviewOverlayState({ open: reviewOpen, ready: reviewReady });

  function titleForItem(item) {
    if (!item) return '';
    const uiMeta = item.ui && typeof item.ui === 'object' ? item.ui : null;
    if (uiMeta) {
      const label = uiMeta.label || uiMeta.title;
      if (label) return label;
    }
    if (item.name) return item.name;
    const id = String(item.id || '').toLowerCase();
    const cap = id.charAt(0).toUpperCase() + id.slice(1);
    const stars = Number.isFinite(item.stars) ? String(item.stars) : '';
    return stars ? `${cap} Upgrade (${stars})` : `${cap} Upgrade`;
  }

  let lootMessages = [];
  let lootConsumed = false;
  let lastRoom = null;
  let msgId = 0;
  function pushLoot(text) {
    lootMessages = [...lootMessages, { id: msgId++, text }];
  }
  function removeLoot(id) {
    lootMessages = lootMessages.filter((m) => m.id !== id);
  }
  $: if (roomData !== lastRoom) {
    lootConsumed = false;
    lastRoom = roomData;
    // Log room changes for debug tracing
    try { console.log(`[OverlayHost] ${now()} roomData changed`, { runId, result: roomData?.result, battle_index: roomData?.battle_index, roomId: roomData?.id || roomData?.room_id || null }); } catch(e) {}
  }
  $: if (!lootConsumed && roomData?.loot) {
    if (roomData.loot.gold) pushLoot(`Gold +${roomData.loot.gold}`);
    if (roomData.loot.items) {
      for (const item of roomData.loot.items) {
        pushLoot(titleForItem(item));
      }
    }
    lootConsumed = true;
  }
</script>

{#if $overlayView === 'party'}
  <OverlaySurface zIndex={1300}>
    <PartyPicker bind:selected reducedMotion={simplifiedTransitions ? true : effectiveReducedMotion}
      allowElementChange={false}
      on:save={() => dispatch('saveParty')}
      on:editorChange={(e) => dispatch('editorChange', e.detail)}
      on:cancel={() => dispatch('back')}
    />
  </OverlaySurface>
{/if}

{#if $overlayView === 'defeat'}
  <PopupWindow title="Defeat" on:close={() => dispatch('back')}>
    <div style="padding: 0.5rem 0.25rem; line-height: 1.4;">
      <p>Your party was defeated.</p>
      <p>You have been returned to the main menu.</p>
      <div class="stained-glass-row" style="justify-content: flex-end; margin-top: 0.75rem;">
        <button class="icon-btn" on:click={() => dispatch('back')}>OK</button>
      </div>
    </div>
  </PopupWindow>
{/if}

{#if $overlayView === 'error'}
  <ErrorOverlay
    message={$overlayData.message || 'An unexpected error occurred.'}
    traceback={$overlayData.traceback || ''}
    on:close={() => dispatch('back')}
  />
{/if}

{#if $overlayView === 'backend-shutdown'}
  <BackendShutdownOverlay
    message={$overlayData.message || 'A critical backend error occurred.'}
    traceback={$overlayData.traceback || ''}
    status={$overlayData.status || 500}
    on:close={() => dispatch('back')}
  />
{/if}

{#if $overlayView === 'run-choose'}
  <PopupWindow title="Resume or Start Run" maxWidth="720px" zIndex={1300} on:close={() => dispatch('back')}>
    <RunChooser runs={$overlayData.runs || []}
      on:choose={(e) => dispatch('loadRun', e.detail.run)}
      on:load={(e) => dispatch('loadRun', e.detail.run)}
      on:startNew={() => dispatch('startNewRun')}
    />
  </PopupWindow>
{/if}

{#if $overlayView === 'backend-not-ready'}
  <BackendNotReady
    apiBase={$overlayData.apiBase || ''}
    message={$overlayData.message || 'Backend is not ready yet.'}
    on:close={() => dispatch('back')}
  />
{/if}

{#if $overlayView === 'party-start'}
  <OverlaySurface>
    <PartyPicker bind:selected reducedMotion={simplifiedTransitions ? true : effectiveReducedMotion}
      allowElementChange={true}
      actionLabel="Start Run"
      on:save={(e) => dispatch('startRun', e.detail)}
      on:editorChange={(e) => dispatch('editorChange', e.detail)}
      on:cancel={() => dispatch('back')}
    />
  </OverlaySurface>
{/if}

{#if $overlayView === 'pulls'}
  <OverlaySurface zIndex={1300}>
    <PullsMenu on:close={() => dispatch('back')} />
  </OverlaySurface>
{/if}

{#if $overlayView === 'warp-info'}
  <PopupWindow
    title="Warp Mechanics"
    maxWidth="640px"
    zIndex={1350}
    on:close={() => dispatch('back')}
  >
    <div class="warp-info-body">
      <p>
        Warps spend gacha tickets to roll from the current banner. Each pull advances pity,
        steadily improving the odds of 5★ and 6★ rewards until a top rarity is found.
      </p>
      <ul class="warp-info-list">
        <li>Single pulls cost 1 ticket, while ×5 and ×10 options spend 5 or 10 at once.</li>
        <li>
          Pity carries across all banners and resets after any 5★ or 6★ reward, whichever comes
          first.
        </li>
        <li>Duplicate characters grant upgrade materials instead of extra copies.</li>
      </ul>
      <p class="warp-info-note">
        Tip: Saving up for larger batches guarantees the animation plays once per session while still
        honoring your current pity level.
      </p>
      <div class="stained-glass-row" style="justify-content: flex-end; margin-top: 0.75rem;">
        <button class="icon-btn" on:click={() => dispatch('back')}>Back to pulls</button>
      </div>
    </div>
  </PopupWindow>
{/if}

  {#if $overlayView === 'pull-results'}
  <OverlaySurface zIndex={1400}>
    <PullResultsOverlay {sfxVolume} results={$overlayData.results || []} on:close={() => dispatch('back')} />
  </OverlaySurface>
{/if}

{#if $overlayView === 'editor'}
  <OverlaySurface zIndex={1300}>
    <CharacterEditor
      {...editorState}
      on:close={() => dispatch('back')}
      on:save={(e) => { dispatch('editorSave', e.detail); dispatch('back'); }}
    />
  </OverlaySurface>
{/if}

{#if $overlayView === 'inventory'}
  <PopupWindow title="Inventory" padding="0" maxWidth="1200px" zIndex={1300} on:close={() => dispatch('back')}>
    <Inventory cards={roomData?.cards ?? []} relics={roomData?.relics ?? []} />
  </PopupWindow>
{/if}

{#if $overlayView === 'combat-viewer'}
  <OverlaySurface zIndex={1300}>
    <CombatViewer 
      party={battleSnapshot?.party ?? []}
      foes={battleSnapshot?.foes ?? []}
      {runId}
      {battleSnapshot}
      on:close={() => dispatch('back')}
      on:pauseCombat={() => dispatch('pauseCombat')}
      on:resumeCombat={() => dispatch('resumeCombat')}
    />
  </OverlaySurface>
{/if}

{#if $overlayView === 'settings'}
  <PopupWindow title="Settings" maxWidth="960px" maxHeight="90vh" zIndex={1300} on:close={() => dispatch('back')}>
    <SettingsMenu
      {sfxVolume}
      {musicVolume}
      {voiceVolume}
      {framerate}
      {reducedMotion}
      {showActionValues}
      {showTurnCounter}
      {flashEnrageCounter}
      {fullIdleMode}
      {skipBattleReview}
      bind:animationSpeed
      {runId}
      {backendFlavor}
      on:save={(e) => dispatch('saveSettings', e.detail)}
      on:endRun={() => dispatch('endRun')}
    />
  </PopupWindow>
{/if}

{#if $overlayView === 'guidebook'}
  <PopupWindow title="Guidebook" maxWidth="1200px" maxHeight="90vh" zIndex={1300} on:close={() => dispatch('back')}>
    <Guidebook />
  </PopupWindow>
{/if}

{#if rewardOpen}
  <PopupWindow
    title={(roomData?.card_choices?.length || 0) > 0 ? 'Choose a Card' : 'Choose a Relic'}
    maxWidth="880px"
    maxHeight="100%"
    zIndex={1100}
    surfaceNoScroll={true}
    on:close={() => { /* block closing while choices remain */ }}
  >
    <RewardOverlay
      cards={roomData.card_choices || []}
      relics={roomData.relic_choices || []}
      items={roomData.loot?.items || []}
      gold={roomData.loot?.gold || 0}
      {fullIdleMode}
      on:select={(e) => dispatch('rewardSelect', e.detail)}
      on:next={() => dispatch('nextRoom')}
      on:lootAcknowledge={() => dispatch('lootAcknowledge')}
    />
  </PopupWindow>
{/if}

{#if reviewOpen && !rewardOpen && reviewReady && !skipBattleReview}
  <PopupWindow
    title="Battle Review"
    maxWidth="1200px"
    maxHeight="100%"
    zIndex={1100}
    padding="1.25rem"
    reducedMotion={overlayReducedMotion}
    surfaceNoScroll={true}
    on:close={() => dispatch('nextRoom')}
  >
    {#key reviewKey}
      <BattleReview
        runId={runId}
        battleIndex={roomData?.battle_index || 0}
        prefetchedSummary={reviewSummary}
        partyData={reviewPartyData}
        foeData={(battleSnapshot?.foes && battleSnapshot?.foes.length) ? battleSnapshot.foes : (roomData?.foes || [])}
        cards={[]}
        relics={[]}
        reducedMotion={overlayReducedMotion}
      />
    {/key}
    <div slot="footer" class="stained-glass-row" style="justify-content: flex-end; margin-top: 0.75rem;">
      <button class="icon-btn" on:click={() => dispatch('nextRoom')}>Next Room</button>
    </div>
  </PopupWindow>
{/if}

{#if roomData && roomData.result === 'shop'}
  <OverlaySurface zIndex={1100}>
    <ShopMenu
      items={roomData.stock || roomData.items || []}
      gold={roomData.gold}
      itemsBought={roomData.items_bought}
      taxSummary={roomData.tax_summary || roomData.taxSummary || null}
      reducedMotion={simplifiedTransitions ? true : effectiveReducedMotion}
      processing={shopProcessing}
      on:buy={(e) => dispatch('shopBuy', e.detail)}
      on:reroll={() => dispatch('shopReroll')}
      on:close={() => dispatch('shopLeave')}
    />
  </OverlaySurface>
{/if}


{#if roomData && (roomData.result === 'battle' || roomData.result === 'boss') && (battleActive || rewardOpen || reviewOpen)}
  <div class="overlay-inset">
    <BattleView
      {runId}
      {framerate}
      {selectedParty}
      enrage={roomData?.enrage}
      reducedMotion={simplifiedTransitions ? true : effectiveReducedMotion}
      showActionValues={showActionValues}
      showTurnCounter={showTurnCounter}
      flashEnrageCounter={flashEnrageCounter}
      active={battleActive}
      showHud={true}
      showFoes={true}
      on:snapshot-start={() => dispatch('snapshot-start')}
      on:snapshot-end={() => dispatch('snapshot-end')}
    />
  </div>
{/if}

{#each lootMessages as m, i (m.id)}
  <FloatingLoot message={m.text} offset={i * 20} on:done={() => removeLoot(m.id)} />
{/each}

<style>
  .warp-info-body {
    padding: 0.5rem 0.25rem;
    line-height: 1.5;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .warp-info-list {
    margin: 0;
    padding-left: 1.2rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .warp-info-note {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.75);
  }

  .overlay-inset {
    position: absolute;
    inset: 0;
    z-index: 1; /* always sit below popup overlays */
    background: rgba(0,0,0,0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  .stained-glass-row {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 0.5rem;
    padding: 0.5rem 0.7rem;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
  }

  /* Keep action bar pinned to the bottom inside scrollable MenuPanel */
  .sticky-bottom {
    position: sticky;
    bottom: 0;
    z-index: 5;
    /* Subtle gradient to separate from content when overlapping */
    background:
      linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.12) 35%, rgba(0,0,0,0.18) 100%),
      var(--glass-bg);
  }

  /* Party actions: stack full-width buttons vertically */
  .party-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .party-actions .icon-btn {
    width: 100%;
    height: auto;
    padding: 0.6rem 0.75rem;
    font-size: 1rem;
    justify-content: center;
  }

  .icon-btn {
    background: rgba(255,255,255,0.10);
    border: none;
    border-radius: 0;
    width: 2.9rem;
    height: 2.9rem;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    border: 1px solid rgba(255,255,255,0.35);
    cursor: pointer;
    transition: background 0.18s, box-shadow 0.18s;
    box-shadow: 0 1px 4px 0 rgba(0,40,120,0.10);
  }
  .icon-btn:hover {
    background: rgba(120,180,255,0.22);
    box-shadow: 0 2px 8px 0 rgba(0,40,120,0.18);
  }
</style>
