<!--
  GameViewport.svelte
  Orchestrates high-level state for the game view. Navigation and
  overlays are delegated to NavBar and OverlayHost, while run helpers
  live in viewportState.js.
-->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  import RoomView from './RoomView.svelte';
  import NavBar from './NavBar.svelte';
  import OverlayHost from './OverlayHost.svelte';
  import { getHourlyBackground } from '../systems/assetLoader.js';
  import MainMenu from './MainMenu.svelte';
  import LoginRewardsPanel from './LoginRewardsPanel.svelte';
  import AboutGamePanel from './AboutGamePanel.svelte';
  import {
    loadInitialState,
    mapSelectedParty,
    roomLabel,
    roomInfo,
    startGameMusic,
    selectBattleMusic,
    applyMusicVolume,
    playVoice,
    applyVoiceVolume,
    stopGameMusic,
  } from '../systems/viewportState.js';
  import { rewardOpen as computeRewardOpen } from '../systems/viewportState.js';
  import { overlayView } from '../systems/OverlayController.js';

  export let runId = '';
  export let roomData = null;
  export let battleSnapshot = null;
  export let background = '';
  export let items = [];
  export let mapRooms = [];
  export let currentIndex = 0;
  export let currentRoomType = '';
  export let editorState = {};
  export let battleActive = false;
  export let selected = [];
  export let backendFlavor = '';
  export let fullIdleMode = false;
  export let animationSpeed = 1;

  let randomBg = '';
  let roster = [];
  let userState = { level: 1, exp: 0, next_level_exp: 100 };
  let sfxVolume = 5;
  let musicVolume = 5;
    let voiceVolume = 5;
    let framerate = 60;
    let reducedMotion = false;
    let showActionValues = false;
  let selectedParty = [];
  let snapshotLoading = false;

  const dispatch = createEventDispatcher();

  onMount(async () => {
    if (!background) {
      randomBg = getHourlyBackground();
    }
    const init = await loadInitialState();
      ({ sfxVolume, musicVolume, voiceVolume, framerate, reducedMotion, showActionValues, fullIdleMode, animationSpeed } =
        init.settings);
    roster = init.roster;
    userState = init.user;
    // Ensure music starts after first user gesture if autoplay was blocked
    try {
      const { resumeGameMusic } = await import('../systems/viewportState.js');
      const resumeOnce = () => { resumeGameMusic(); cleanup(); };
      const cleanup = () => {
        try {
          window.removeEventListener('pointerdown', resumeOnce);
          window.removeEventListener('keydown', resumeOnce);
        } catch {}
      };
      window.addEventListener('pointerdown', resumeOnce, { once: true });
      window.addEventListener('keydown', resumeOnce, { once: true });
    } catch {}
  });

  onDestroy(() => {
    stopGameMusic();
  });

  $: selectedParty = mapSelectedParty(roster, selected);
  $: applyMusicVolume(musicVolume);
  $: applyVoiceVolume(voiceVolume);
  $: roomData?.voice && playVoice(roomData.voice, voiceVolume);
  $: info = roomInfo(mapRooms, currentIndex, currentRoomType, roomData);
  $: rewardOpen = computeRewardOpen(roomData, battleActive);
  $: reviewOpen = Boolean(roomData && (roomData.result === 'battle' || roomData.result === 'boss') && !battleActive);

  let lastMusicKey = '';

  // Compute a global accent color from the user's global level and
  // use it as the outline for the full WebUI. This keeps a consistent
  // visual theme tied to progression.
  function levelToAccent(level) {
    try {
      const lv = Math.max(1, Number(level) || 1);
      const hue = (lv * 12) % 360; // cycle hues as level increases
      return `hsl(${hue} 85% 55%)`;
    } catch {
      return '#8ac';
    }
  }
  $: accentColor = levelToAccent(userState?.level || 1);
  $: levelProgress = (() => {
    const exp = Number(userState?.exp || 0);
    const next = Number(userState?.next_level_exp || 0) || 0;
    if (next <= 0) return 0;
    const p = Math.max(0, Math.min(1, exp / next));
    return p;
  })();
  $: viewportStyle = `--bg: url(${background || randomBg}); --accent: ${accentColor}; --level-progress: ${levelProgress}`;
  $: {
    // Change music per room type and battle index (new fights) and
    // rerun when party/foe combatants change to trigger character themes.
    const typeKey = String(currentRoomType || roomData?.current_room || '');
    const battleKey = String(roomData?.battle_index || 0);
    const partyKey = (roomData?.party || [])
      .map((p) => (typeof p === 'string' ? p : p.id || p.name))
      .sort()
      .join(',');
    const foeKey = (roomData?.foes || [])
      .map((f) => (typeof f === 'string' ? f : f.id || f.name))
      .sort()
      .join(',');
    const key = `${typeKey}|${battleKey}|${partyKey}|${foeKey}`;
    if (key !== lastMusicKey) {
      lastMusicKey = key;
      const playlist = selectBattleMusic({
        roomType: typeKey,
        party: roomData?.party || [],
        foes: roomData?.foes || [],
      });
      startGameMusic(musicVolume, playlist);
    }
  }
</script>

<style>
  .viewport-wrap {
    width: 100%;
    height: 100%;
    overflow: hidden;
    box-sizing: border-box;
  }
  .viewport {
    --ui-top-offset: calc(1.2rem + 2.9rem + 1.2rem);
    width: 100%;
    height: 100%;
    border: 2px solid var(--accent, #fff);
    box-shadow:
      0 0 0 1px color-mix(in srgb, var(--accent, #8ac) 30%, transparent),
      0 0 32px 0 color-mix(in srgb, var(--accent, #8ac) 18%, transparent) inset;
    box-sizing: border-box;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    background-image: var(--bg);
    background-size: cover;
    background-position: center;
    overflow: hidden;
    position: relative;
  }
  /* Progress outline driven by global user level EXP */
  .viewport::before {
    content: '';
    position: absolute;
    inset: -2px; /* extend slightly to avoid clipping */
    padding: 2px; /* outline thickness */
    border-radius: 0;
    background:
      conic-gradient(
        var(--accent, #8ac) 0 calc(var(--level-progress, 0) * 1turn),
        rgba(255,255,255,0.12) 0 1turn
      );
    -webkit-mask:
      linear-gradient(#000 0 0) content-box,
      linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude; /* standard property */
    pointer-events: none;
  }
  .placeholder {
    color: #ddd;
    font-size: 0.95rem;
    text-align: center;
    backdrop-filter: blur(2px);
    background: rgba(0,0,0,0.35);
    padding: 0.5rem 0.75rem;
    border-radius: 0;
  }
  .overlay-inset {
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  @media (max-width: 599px) {
    .viewport { aspect-ratio: auto; min-height: 240px; }
  }
  .top-center-header {
    position: absolute;
    top: 1.2rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10;
    display: flex;
    align-items: center;
  }
  .title-chip {
    padding: 0.45rem 0.75rem;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
    border-radius: 0;
    font-size: 0.95rem;
    line-height: 1;
    white-space: nowrap;
  }
  .arrow { margin: 0 0.5rem; opacity: 0.9; }
  .user-level-bar {
    position: fixed; /* stick to the user's screen, not the viewport box */
    bottom: 0;
    left: 0;
    right: 0;
    height: 6px;
    background: #222;
    z-index: 9999; /* above game overlays */
    pointer-events: none; /* do not block clicks */
  }
  .user-level-bar .fill {
    height: 100%;
    background: linear-gradient(red, green);
  }
</style>

<div class="viewport-wrap">
  <div class="viewport" style={viewportStyle}>
    <NavBar
      {battleActive}
      viewMode={$overlayView}
      {snapshotLoading}
      {runId}
      on:home={() => dispatch('home')}
      on:forceNextRoom={() => dispatch('forceNextRoom')}
      on:openInventory={() => dispatch('openInventory')}
      on:openParty={() => dispatch('openParty')}
      on:openCombatViewer={() => dispatch('openCombatViewer')}
      
      on:settings={() => dispatch('settings')}
      on:back={() => dispatch('back')}
    />
    {#if battleActive || rewardOpen || reviewOpen}
      <div class="top-center-header">
        <div class="title-chip">
          Pressure {info.pressure} / Floor {info.floorNumber} / Room {info.roomNumber} / {roomLabel(info.currentType)}
        </div>
        <div class="arrow">→</div>
        <div class="title-chip">
          {roomLabel(info.nextType) || 'Unknown'}
        </div>
      </div>
    {/if}
    {#if $overlayView === 'main' && !battleActive && !rewardOpen && !reviewOpen}
      <LoginRewardsPanel />
      <MainMenu {items} />
      <AboutGamePanel {userState} />
    {/if}
    {#if runId && roomData && !(((roomData.result === 'battle') || (roomData.result === 'boss')) && !battleActive)}
      <RoomView result={roomData.result} foes={roomData.foes} party={roomData.party} activeId={roomData.active_id} />
    {:else if runId}
      <div class="placeholder">Awaiting next room...</div>
    {/if}
      <OverlayHost
        bind:selected
        {runId}
        {roomData}
        {battleSnapshot}
        {editorState}
        {sfxVolume}
        {musicVolume}
        {voiceVolume}
        {framerate}
        {reducedMotion}
        {showActionValues}
        {fullIdleMode}
        bind:animationSpeed
        {selectedParty}
        {battleActive}
        {backendFlavor}
        on:saveParty={() => dispatch('saveParty')}
      on:startRun={(e) => dispatch('startRun', e.detail)}
        on:back={() => dispatch('back')}
      on:pauseCombat={() => dispatch('pauseCombat')}
      on:resumeCombat={() => dispatch('resumeCombat')}
      on:rewardSelect={(e) => dispatch('rewardSelect', e.detail)}
      on:nextRoom={() => dispatch('nextRoom')}
      on:lootAcknowledge={() => dispatch('lootAcknowledge')}
      on:editorSave={(e) => dispatch('editorSave', e.detail)}
      on:editorChange={(e) => dispatch('editorChange', e.detail)}
      on:loadRun={(e) => dispatch('loadRun', e.detail)}
      on:startNewRun={() => dispatch('startNewRun')}
      on:saveSettings={(e) => ({ sfxVolume, musicVolume, voiceVolume, framerate, reducedMotion, showActionValues, fullIdleMode, animationSpeed } = e.detail)}
      on:endRun={() => dispatch('endRun')}
      on:shopBuy={(e) => dispatch('shopBuy', e.detail)}
      on:shopReroll={() => dispatch('shopReroll')}
        on:shopLeave={() => dispatch('shopLeave')}
        on:snapshot-start={() => (snapshotLoading = true)}
        on:snapshot-end={() => (snapshotLoading = false)}
      />
    <div class="user-level-bar">
      <div
        class="fill"
        style={`width: ${Math.min(
          100,
          100 * (userState.exp / userState.next_level_exp)
        )}%`}
      />
    </div>
  </div>
</div>
