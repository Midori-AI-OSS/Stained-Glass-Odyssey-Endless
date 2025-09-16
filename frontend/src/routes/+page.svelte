<script>
  import GameViewport from '$lib/components/GameViewport.svelte';
  import { onMount } from 'svelte';
  import { 
    getPlayerConfig, 
    savePlayerConfig, 
    getBackendFlavor, 
    endAllRuns,
    startRun,
    roomAction,
    chooseCard,
    chooseRelic,
    advanceRoom,
    getMap,
    getActiveRuns,
    getUIState,
    sendAction,
    loadRunState,
    saveRunState,
    clearRunState,
    FEEDBACK_URL,
    openOverlay,
    backOverlay,
    homeOverlay
  } from '$lib';
  import { updateParty, acknowledgeLoot } from '$lib/systems/uiApi.js';
  import { buildRunMenu } from '$lib/components/RunButtons.svelte';
  import { browser, dev } from '$app/environment';

  let runId = '';
  let backendFlavor = '';
  let selectedParty = ['sample_player'];
  let roomData = null;
  // Track map state to render room/floor context in battle header
  let mapRooms = [];
  let currentIndex = 0;
  let currentRoomType = '';
  let viewportBg = '';
  let nextRoom = '';

  let editorConfigs = {};
  let editorState = { pronouns: '', damageType: 'Light', hp: 0, attack: 0, defense: 0 };
  let battleActive = false;
  // When true, suppress backend syncing/polling (e.g., during defeat popup)
  let haltSync = false;
  let fullIdleMode = false;
  let animationSpeed = 1;
  // Preserve the last live battle snapshot (with statuses) for review UI
  let lastBattleSnapshot = null;
  // Prevent overlapping room fetches
  let enterRoomPending = false;

  // Convert backend-provided party lists into a flat array of player IDs.
  // Filters out summons and de-duplicates entries.
  function normalizePartyIds(list) {
    if (!Array.isArray(list)) return null;
    const ids = [];
    for (const item of list) {
      const isSummon = typeof item === 'object' && (item?.summon_type || item?.type === 'summon' || item?.is_summon);
      if (isSummon) continue;
      const id = typeof item === 'string' ? item : (item?.id || item?.name || '');
      if (id) ids.push(String(id));
    }
    return Array.from(new Set(ids));
  }

  // Normalize status fields so downstream components can rely on
  // `passives`, `dots`, and `hots` arrays of objects on each fighter.
  function mapStatuses(snapshot) {
    if (!snapshot) return snapshot;
    function map(list = []) {
      return list.map((f) => {
        const status = f.status || {};
        return {
          ...f,
          passives: status.passives || f.passives || [],
          dots: status.dots || f.dots || [],
          hots: status.hots || f.hots || []
        };
      });
    }
    // Normalize party/foes shapes: arrays are preferred; accept object maps or alternate keys
    if (snapshot && !Array.isArray(snapshot.party) && snapshot.party && typeof snapshot.party === 'object') {
      snapshot.party = Object.values(snapshot.party);
    }
    if (snapshot && !Array.isArray(snapshot.foes)) {
      if (snapshot.foes && typeof snapshot.foes === 'object') {
        snapshot.foes = Object.values(snapshot.foes);
      } else if (Array.isArray(snapshot.enemies)) {
        snapshot.foes = snapshot.enemies;
      } else if (snapshot.enemies && typeof snapshot.enemies === 'object') {
        snapshot.foes = Object.values(snapshot.enemies);
      }
    }
    if (Array.isArray(snapshot.party)) snapshot.party = map(snapshot.party);
    if (Array.isArray(snapshot.foes)) snapshot.foes = map(snapshot.foes);
    return snapshot;
  }

  onMount(async () => {
    // Always ensure sync is not halted on load
    if (typeof window !== 'undefined') {
      window.afHaltSync = false;
      window.afBattleActive = false; // Initialize battle state for ping indicator
    }

    // Always attempt to restore run state from localStorage, regardless of backend status
    const saved = loadRunState();
    
    async function syncWithBackend() {
      if (!saved?.runId) return;
      
      try {
        const data = await getMap(saved.runId);
        if (!data) {
          clearRunState();
          return;
        }
        
        // Use backend as source of truth for all state
        runId = saved.runId;
        selectedParty = normalizePartyIds(data.party) || selectedParty;
        mapRooms = data.map.rooms || [];
        
        // Use the enhanced current_state data from backend
        if (data.current_state) {
          currentIndex = data.current_state.current_index || 0;
          currentRoomType = data.current_state.current_room_type || '';
          nextRoom = data.current_state.next_room_type || '';
          
          // Set room data directly from backend if available
          if (data.current_state.room_data) {
            roomData = data.current_state.room_data;
            
            // If it's a battle and has snapshot data, start battle state
            if (data.current_state.room_data.result === 'battle' && !data.current_state.awaiting_next) {
              battleActive = true;
              stopStatePoll(); // Stop state polling when battle starts
              startBattlePoll();
            }
          }
        } else {
          // Fallback to map-based state for backward compatibility
          currentIndex = data.map.current || 0;
          currentRoomType = mapRooms[currentIndex]?.room_type || '';
          nextRoom = mapRooms[currentIndex + 1]?.room_type || '';
          await enterRoom();
        }
        
        saveRunState(runId);
        
        // Start state polling after successful sync (if not in battle)
        if (!battleActive) {
          startStatePoll();
        }
      } catch (e) {
        // If run restoration fails due to backend unavailability, keep the runId for later retry
        if (saved?.runId) {
          runId = saved.runId;
        }
      }
    }
    
    // Try to get backend flavor and sync with backend
    try {
      backendFlavor = await getBackendFlavor();
      window.backendFlavor = backendFlavor;
      
      // Backend is ready, try new UI state approach first
      try {
        await pollUIState();
        startUIStatePoll();
      } catch (e) {
        // Fall back to existing sync approach
        console.warn('UI state polling failed, falling back to existing sync:', e);
        await syncWithBackend();
      }
    } catch (e) {
      // Backend not ready, but still attempt to restore run state for later
      if (saved?.runId) {
        runId = saved.runId;
      }
      // Dedicated overlay opened in getBackendFlavor; user can retry when backend is ready
    }
  });

  async function openRun() {
    // First, check backend for any active runs and let user choose
    try {
      const data = await getActiveRuns();
      const activeRuns = data?.runs || [];
      if (activeRuns.length > 0) {
        openOverlay('run-choose', { runs: activeRuns });
        return;
      }
    } catch {}

    if (runId) {
      // If we have a runId, sync with backend to get current state
      try {
        const data = await getMap(runId);
        if (data) {
          selectedParty = normalizePartyIds(data.party) || selectedParty;
          mapRooms = data.map.rooms || [];
          
          // Use backend's current_state as source of truth
          if (data.current_state) {
            currentIndex = data.current_state.current_index || 0;
            currentRoomType = data.current_state.current_room_type || '';
            nextRoom = data.current_state.next_room_type || '';
            
            // Use room data from backend if available
            if (data.current_state.room_data) {
              roomData = data.current_state.room_data;
              
              // If it's a battle and not awaiting next, start battle state
              if (data.current_state.room_data.result === 'battle' && !data.current_state.awaiting_next) {
                battleActive = true;
                stopStatePoll(); // Stop state polling when battle starts
                startBattlePoll();
              }
            }
          } else {
            // Fallback for backward compatibility
            currentIndex = data.map.current || 0;
            currentRoomType = mapRooms[currentIndex]?.room_type || '';
            nextRoom = mapRooms[currentIndex + 1]?.room_type || '';
          }
        } else {
          // Run not found on backend, clear local state
          console.warn('Run not found on backend, clearing local state');
          clearRunState();
          runId = '';
        }
      } catch (e) {
        // If we can't get run data, show error but don't clear runId
        console.warn('Failed to restore run data:', e.message);
      }
      
      homeOverlay();
      if (!battleActive && !roomData) {
        enterRoom();
      }
      
      // Force backend state sync and start state polling when clicking run button
      if (runId && !battleActive) {
        startStatePoll();
      }
    } else {
      openOverlay('party-start');
    }
  }

  async function handleRunEnd() {
    // Halt any in-flight battle snapshot polling ASAP
    haltSync = true;
    if (typeof window !== 'undefined') {
      window.afHaltSync = true;
      window.afBattleActive = false; // Update battle state for ping indicator
    }
    // Proactively ask backend to end any active runs to avoid lingering state
    try { await endAllRuns(); } catch {}
    runId = '';
    roomData = null;
    // Drop any retained snapshot to free memory and avoid stale data
    lastBattleSnapshot = null;
    nextRoom = '';
    battleActive = false;
    stopBattlePoll();
    stopStatePoll();
    stopUIStatePoll();
    homeOverlay();
    clearRunState();
  }

  function handleDefeat() {
    // Clear run state, go to main menu, and show a defeat popup
    haltSync = true;
    if (typeof window !== 'undefined') {
      window.afHaltSync = true;
      window.afBattleActive = false; // Update battle state for ping indicator
    }
    handleRunEnd();
    // Open a lightweight popup informing the player
    openOverlay('defeat');
  }

  async function handleStart(event) {
    const pressure = event?.detail?.pressure || 0;
    haltSync = false;
    if (typeof window !== 'undefined') {
      window.afHaltSync = false;
      window.afBattleActive = false; // Initialize battle state
    }
    
    // Stop any existing polling when starting a new run
    stopStatePoll();
    stopBattlePoll();

    // Check for active/live runs first
    try {
      const activeRunsData = await getActiveRuns();
      const activeRuns = activeRunsData.runs || [];
      
      if (activeRuns.length > 0) {
        // If the user set a specific pressure and it differs from the existing run,
        // end all runs to honor the new selection.
        const existing = activeRuns[0];
        const existingPressure = existing?.map?.rooms?.[0]?.pressure ?? 0;
        if (Number(existingPressure) !== Number(pressure)) {
          try { await endAllRuns(); } catch {}
        } else {
          // Resume the first active run found
          const activeRun = existing;
          runId = activeRun.run_id;
          mapRooms = activeRun.map.rooms || [];
          currentIndex = activeRun.map.current || 0;
          currentRoomType = mapRooms[currentIndex]?.room_type || '';
          nextRoom = mapRooms[currentIndex + 1]?.room_type || '';
          saveRunState(runId);
          homeOverlay();
          await enterRoom();
          
          // Start state polling after resuming existing run (if not in battle)
          if (!battleActive) {
            startStatePoll();
          }
          return;
        }
      }
    } catch (error) {
      // If checking for active runs fails, fall back to starting a new run
      console.warn('Failed to check for active runs, starting new run:', error);
    }

    // No active runs found, start a new run
    const dmgType = editorConfigs.player?.damageType || editorState.damageType;
    const data = await startRun(selectedParty, dmgType, pressure);
    runId = data.run_id;
    mapRooms = data.map.rooms || [];
    currentIndex = data.map.current || 0;
    currentRoomType = mapRooms[currentIndex]?.room_type || '';
    nextRoom = mapRooms[currentIndex + 1]?.room_type || '';
    saveRunState(runId);
    homeOverlay();
    await enterRoom();
    
    // Start state polling after successfully starting new run (if not in battle)
    if (!battleActive) {
      startStatePoll();
    }
  }

  async function handleLoadExistingRun(e) {
    try {
      const chosen = e?.detail || e; // Overlay dispatches the run object directly
      const rid = chosen?.run_id;
      if (!rid) { backOverlay(); return; }
      const data = await getMap(rid);
      if (!data) { backOverlay(); return; }
      runId = rid;
      selectedParty = normalizePartyIds(data.party) || selectedParty;
      mapRooms = data.map.rooms || [];
      currentIndex = data.map.current || 0;
      currentRoomType = mapRooms[currentIndex]?.room_type || '';
      nextRoom = mapRooms[currentIndex + 1]?.room_type || '';
      saveRunState(runId);
      backOverlay();
      homeOverlay();
      await enterRoom();
      
      // Start state polling after loading existing run (if not in battle)
      if (!battleActive) {
        startStatePoll();
      }
    } catch (e) {
      backOverlay();
    }
  }

  async function handleStartNewRun() {
    // Ensure we truly start fresh: end any active runs first
    try { await endAllRuns(); } catch {}
    openOverlay('party-start');
  }

  async function handleParty() {
    if (battleActive) return;
    openOverlay('party');
  }

  async function handlePartySave() {
    if (runId) {
      await updateParty(selectedParty);
    }
    backOverlay();
  }

  async function openEditor() {
    if (battleActive) return;
    const data = await getPlayerConfig();
    editorState = {
      pronouns: data.pronouns,
      damageType: data.damage_type,
      hp: data.hp,
      attack: data.attack,
      defense: data.defense,
    };
    editorConfigs.player = { ...editorState };
    openOverlay('editor');
  }

  async function handleEditorSave(e) {
    editorState = {
      ...e.detail,
      hp: +e.detail.hp,
      attack: +e.detail.attack,
      defense: +e.detail.defense,
    };
    editorConfigs.player = { ...editorState };
    await savePlayerConfig({
      pronouns: editorState.pronouns,
      damage_type: editorState.damageType,
      hp: editorState.hp,
      attack: editorState.attack,
      defense: editorState.defense,
    });
  }

  function handleEditorChange(e) {
    const detail = e.detail || {};
    if (detail.id) {
      editorConfigs[detail.id] = { ...(editorConfigs[detail.id] || {}), ...detail.config };
      if (detail.id === 'player') {
        editorState = { ...editorState, ...detail.config };
      }
    } else {
      editorState = { ...editorState, ...detail };
      editorConfigs.player = { ...(editorConfigs.player || {}), ...detail };
    }
  }

  async function openPulls() {
    if (battleActive) return;
    openOverlay('pulls');
  }


  function openFeedback() {
    window.open(FEEDBACK_URL, '_blank', 'noopener');
  }

  async function openInventory() {
    openOverlay('inventory');
  }

  function openCombatViewer() {
    if (!battleActive) return;
    openOverlay('combat-viewer');
  }

  // Combat pause/resume functions using roomAction
  async function handlePauseCombat() {
    if (!runId) return;
    try {
      await roomAction('0', 'pause');
      console.log('Combat paused');
    } catch (error) {
      console.error('Failed to pause combat:', error);
    }
  }

  async function handleResumeCombat() {
    if (!runId) return;
    try {
      await roomAction('0', 'resume');
      console.log('Combat resumed');
    } catch (error) {
      console.error('Failed to resume combat:', error);
    }
  }

  let battleTimer;
  let stateTimer;
  // Determine framerate-derived polling. We read from localStorage to avoid
  // pulling in settings modules here and to honor the user's FPS setting.
  function getFramerateSetting() {
    try {
      const raw = localStorage.getItem('autofighter_settings');
      if (!raw) return 60;
      const data = JSON.parse(raw);
      const fps = Number(data?.framerate ?? 60);
      return Number.isFinite(fps) && fps > 0 ? fps : 60;
    } catch {
      return 60;
    }
  }
  function getBattlePollDelayMs() {
    const fps = getFramerateSetting();
    // Polls/sec = fps/10, so delay = 1000 / (fps/10) = 10000 / fps
    return 10000 / Math.max(1, fps);
  }
  function getStallTicks() {
    // Keep stall window ~3 seconds regardless of polling rate
    // pollsPerSecond = fps / 10
    const fps = getFramerateSetting();
    const pollsPerSecond = Math.max(0.1, fps / 10);
    return Math.max(1, Math.round(pollsPerSecond * 3));
  }
  let stalledTicks = 0;
  let missingSnapTicks = 0;

  function hasRewards(snap) {
    if (!snap) return false;
    const cards = (snap?.card_choices?.length || 0) > 0;
    const relics = (snap?.relic_choices?.length || 0) > 0;
    const lootItems = (snap?.loot?.items?.length || 0) > 0;
    const lootGold = (snap?.loot?.gold || 0) > 0;
    return cards || relics || lootItems || lootGold;
  }

  function stopBattlePoll() {
    if (battleTimer) {
      clearTimeout(battleTimer);
      battleTimer = null;
    }
  }

  function startBattlePoll() {
    stopBattlePoll(); // Clear any existing timer
    missingSnapTicks = 0;
    try {
      if (typeof window !== 'undefined' && (window.afRewardOpen === true || window.afReviewOpen === true)) return;
    } catch {}
    if (battleActive && !haltSync && runId) {
      pollBattle();
    }
  }

  async function pollBattle() {
    if (!battleActive || haltSync || !runId) return;
    try {
      if (typeof window !== 'undefined' && (window.afRewardOpen === true || window.afReviewOpen === true)) {
        stopBattlePoll();
        return;
      }
    } catch {}
    try {
      const snap = mapStatuses(await roomAction("0", {"action": "snapshot"}));
      if (snap?.snapshot_missing) {
        missingSnapTicks += 1;
        if (missingSnapTicks > getStallTicks()) {
          battleActive = false;
          stopBattlePoll();
          // Surface reconnect prompt when snapshot cannot be recovered
          try { openOverlay('error', { message: 'Battle state unavailable. Please reconnect.', traceback: '' }); } catch {}
          startStatePoll();
          return;
        }
      } else {
        missingSnapTicks = 0;
        lastBattleSnapshot = snap || lastBattleSnapshot;
      }
      if (snap?.error) {
        roomData = snap;
        lastBattleSnapshot = snap || lastBattleSnapshot;
        battleActive = false;
        stopBattlePoll();
        stalledTicks = 0;
        // Start state polling when battle ends with error
        startStatePoll();
        // Surface backend-declared errors via popup
        try { openOverlay('error', { message: snap.error, traceback: '' }); } catch {}
        return;
      }
      const snapHasRewards = hasRewards(snap);
      const snapCompleted = Boolean(snap?.awaiting_next) || Boolean(snap?.next_room) || snap?.result === 'defeat';
      const partyDead = Array.isArray(snap?.party) && snap.party.length > 0 && snap.party.every(m => (m?.hp ?? 1) <= 0);
      const foesDead = Array.isArray(snap?.foes) && snap.foes.length > 0 && snap.foes.every(f => (f?.hp ?? 1) <= 0);
      const combatOver = partyDead || foesDead;
      if (snapHasRewards || snapCompleted) {
        // Stop only when rewards or completion flags arrive
        roomData = snap;
        lastBattleSnapshot = snap || lastBattleSnapshot;
        const rewardsReady = hasRewards(roomData);
        if (rewardsReady || snapCompleted) {
          battleActive = false;
          stopBattlePoll();
          nextRoom = snap.next_room || nextRoom;
          if (typeof snap.current_index === 'number') currentIndex = snap.current_index;
          if (snap.current_room) currentRoomType = snap.current_room;
          stalledTicks = 0;
          
          // Start state polling when battle ends (unless defeated)
          if (snap?.result !== 'defeat') {
            startStatePoll();
          }

          // If run ended in defeat, immediately return home and show defeat popup
          if (snap?.result === 'defeat') {
            handleDefeat();
          }
          // Auto-advance if awaiting_next without any reward choices or loot present
          try {
            if (!rewardsReady && snap?.awaiting_next && !snap?.awaiting_loot && runId) {
              await handleNextRoom();
            }
          } catch {}
          // Do not auto-advance; show Battle Review popup after rewards.
          return;
        }
      }
      if (combatOver) {
        // Update snapshot but keep polling until rewards are available
        roomData = snap;
        stalledTicks += 1;
        if (stalledTicks > getStallTicks()) {
          battleActive = false;
          stopBattlePoll();
          roomData = { ...snap, error: 'Battle results could not be fetched.' };
          // Start state polling when battle stalls
          startStatePoll();
          if (dev || !browser) {
            const { warn } = await import('$lib/systems/logger.js');
            warn('Battle results could not be fetched.');
          }
          return;
        }
      } else {
        stalledTicks = 0;
      }
    } catch (err) {
      // Treat snapshot errors as transient unless run is confirmed ended.
      if (err?.status === 404 || String(err?.message || '').toLowerCase().includes('run ended')) {
        handleRunEnd();
        return;
      }
      console.warn('Battle polling failed:', err?.message || err);
    }
    try {
      if (typeof window !== 'undefined' && (window.afRewardOpen === true || window.afReviewOpen === true)) {
        stopBattlePoll();
        return;
      }
    } catch {}
    if (battleActive && !haltSync && runId) {
      battleTimer = setTimeout(pollBattle, getBattlePollDelayMs());
    }
  }

  function stopStatePoll() {
    if (stateTimer) {
      clearTimeout(stateTimer);
      stateTimer = null;
    }
  }

  async function pollState() {
    // Don't poll if we're in battle, halted, in menu, or no runId
    if (battleActive || haltSync || !runId) return;
    // Pause polling while Reward or Battle Review overlays are open
    try {
      if (typeof window !== 'undefined' && (window.afRewardOpen === true || window.afReviewOpen === true)) {
        stopStatePoll();
        return;
      }
    } catch {}

    // Don't poll if we're in a menu/overlay (not 'main')
    try {
      const { get } = await import('svelte/store');
      const { overlayView } = await import('$lib/systems/OverlayController.js');
      const currentView = get(overlayView);
      if (currentView !== 'main') return;
    } catch {
      // If we can't check overlay state, continue
    }

    try {
      const data = await getMap(runId);
      if (!data) {
        // Run no longer exists, clear local state
        handleRunEnd();
        return;
      }

      // Update state from backend (backend is source of truth)
      selectedParty = normalizePartyIds(data.party) || selectedParty;
      mapRooms = data.map.rooms || [];
      
      // Use backend's current_state as source of truth
      if (data.current_state) {
        currentIndex = data.current_state.current_index || 0;
        currentRoomType = data.current_state.current_room_type || '';
        nextRoom = data.current_state.next_room_type || '';
        
        // Update room data if available
        if (data.current_state.room_data) {
          roomData = data.current_state.room_data;
          
          // If backend indicates we should be in battle but we're not, start battle
          if (data.current_state.room_data.result === 'battle' && !data.current_state.awaiting_next && !battleActive) {
            battleActive = true;
            pollBattle(); // Start battle polling
            return; // Exit state polling when battle starts
          }
        }
      }
      
      saveRunState(runId);
    } catch (e) {
      // Don't show overlays for polling errors to avoid spam
      console.warn('State polling failed:', e?.message || e);
      if (String(e?.message || '').toLowerCase().includes('run ended') || e?.status === 404) {
        handleRunEnd();
        return;
      }
    }

    // Schedule next state poll if conditions are still met
    try {
      if (typeof window !== 'undefined' && (window.afRewardOpen === true || window.afReviewOpen === true)) {
        stopStatePoll();
        return;
      }
    } catch {}
    if (!battleActive && !haltSync && runId) {
      stateTimer = setTimeout(pollState, 5000); // Poll every 5 seconds
    }
  }

  function startStatePoll() {
    stopStatePoll(); // Clear any existing timer
    // Do not schedule polling while Reward or Battle Review overlays are open
    try {
      if (typeof window !== 'undefined' && (window.afReviewOpen === true || window.afRewardOpen === true)) return;
    } catch {}
    if (!battleActive && !haltSync && runId) {
      stateTimer = setTimeout(pollState, 5000);
    }
  }

  async function enterRoom() {
    if (enterRoomPending) return;
    if (haltSync) return;
    if (!runId) return;
    enterRoomPending = true;
    stopBattlePoll();
    // Ensure header reflects the room we are entering now
    currentRoomType = mapRooms?.[currentIndex]?.room_type || currentRoomType || nextRoom;
    if (!currentRoomType) {
      enterRoomPending = false;
      return;
    }
    let endpoint = currentRoomType;
    if (endpoint.includes('battle')) {
      endpoint = currentRoomType.includes('boss') ? 'boss' : 'battle';
    }
    try {
      // Fetch first, then decide whether to show rewards or start battle polling.
      const data = mapStatuses(await roomAction("0", ""));
      roomData = data;
      if (data?.error) {
        // Show error popup for successful-but-error payloads
        try { openOverlay('error', { message: data.error, traceback: '' }); } catch {}
        return;
      }
      // If this response indicates a defeated run, stop syncing and show popup.
      if (data?.result === 'defeat') {
        handleDefeat();
        return;
      }
      if (data.party) {
        selectedParty = normalizePartyIds(data.party) || selectedParty;
      }
      // Keep map-derived indices and current room type in sync when available
      if (typeof data.current_index === 'number') currentIndex = data.current_index;
      if (data.current_room) currentRoomType = data.current_room;
      nextRoom = data.next_room || (mapRooms?.[currentIndex + 1]?.room_type || nextRoom || '');
      saveRunState(runId);
      if (endpoint === 'battle' || endpoint === 'boss') {
        const gotRewards = hasRewards(data);
        if (gotRewards) {
          battleActive = false;
          stopBattlePoll();
          return;
        }
        // If backend reports awaiting_next without choices or loot, force-advance
        try {
          const noChoices = ((data?.card_choices?.length || 0) === 0) && ((data?.relic_choices?.length || 0) === 0);
          if (data?.awaiting_next && noChoices && !data?.awaiting_loot && runId) {
            await handleNextRoom();
            return;
          }
        } catch {}
        // Do not auto-advance; allow Battle Review popup to appear.
        const noFoes = !Array.isArray(data?.foes) || data.foes.length === 0;
        if (noFoes) {
          // Try to fetch the saved battle snapshot (e.g., after refresh while awaiting rewards).
          try {
            if (haltSync || !runId) return;
            const snap = mapStatuses(await roomAction("0", {"action": "snapshot"}));
            const snapHasRewards = hasRewards(snap);
            if (snapHasRewards) {
              roomData = snap;
              lastBattleSnapshot = snap || lastBattleSnapshot;
              battleActive = false;
              stopBattlePoll();
              nextRoom = snap.next_room || nextRoom;
              if (typeof snap.current_index === 'number') currentIndex = snap.current_index;
              if (snap.current_room) currentRoomType = snap.current_room;
              return;
            }
          } catch {}
        }
        // If the snapshot didn't include current room type yet, fall back to pre-room value
        // Actively set a sensible type for header during combat
        if (!currentRoomType) currentRoomType = mapRooms?.[currentIndex]?.room_type || (endpoint.includes('boss') ? 'battle-boss-floor' : 'battle-normal');
        battleActive = true;
        if (typeof window !== 'undefined') window.afBattleActive = true; // Update global state for ping indicator
        startBattlePoll();
      } else {
        battleActive = false;
        if (typeof window !== 'undefined') window.afBattleActive = false; // Update global state for ping indicator
        stopBattlePoll();
        // Start state polling for non-battle rooms
        startStatePoll();
        // Non-battle rooms that are immediately ready to advance (no choices, no loot)
        // should auto-advance to avoid getting stuck.
        try {
          const noChoices = ((data?.card_choices?.length || 0) === 0) && ((data?.relic_choices?.length || 0) === 0);
          if (data?.awaiting_next && noChoices && !data?.awaiting_loot && runId) {
            await handleNextRoom();
            return;
          }
        } catch {}
      }
    } catch (e) {
      try {
        if (haltSync || !runId) return;
        const snap = mapStatuses(await roomAction("0", {"action": "snapshot"}));
        roomData = snap;
        battleActive = false;
        stopBattlePoll();
        nextRoom = snap.next_room || nextRoom;
        if (typeof snap.current_index === 'number') currentIndex = snap.current_index;
        if (snap.current_room) currentRoomType = snap.current_room;
        saveRunState(runId);
        // Avoid noisy overlays on transient 400s.
        const simpleRecoverable = (e?.status === 400 || e?.status === 404) || /not ready|awaiting next|invalid room|out of range/i.test(String(e?.message || ''));
        if (!simpleRecoverable) {
          openOverlay('error', {
            message: 'Failed to enter room. Restored latest battle state.',
            traceback: (e && e.stack) || ''
          });
        }
      } catch {
        // Surface error via overlay for consistency
        openOverlay('error', { message: 'Failed to enter room.', traceback: '' });
        if (dev || !browser) {
          const { error } = await import('$lib/systems/logger.js');
          error('Failed to enter room.', e);
        }
      }
    } finally {
      enterRoomPending = false;
    }
  }

  async function handleRewardSelect(detail) {
    let res;
    if (detail.type === 'card') {
      // chooseCard now routes via /ui/action and does not take runId
      res = await chooseCard(detail.id);
      // Trigger Svelte reactivity by reassigning the object reference
      if (roomData) {
        roomData = { ...roomData, card_choices: [] };
      }
    } else if (detail.type === 'relic') {
      // chooseRelic now routes via /ui/action and does not take runId
      res = await chooseRelic(detail.id);
      // Trigger Svelte reactivity by reassigning the object reference
      if (roomData) {
        roomData = { ...roomData, relic_choices: [] };
      }
    }
    if (res && res.next_room) {
      nextRoom = res.next_room;
    }
    // Do not auto-advance; show Battle Review popup next.
  }

  let autoHandling = false;
  async function maybeAutoHandle() {
    if (!fullIdleMode || autoHandling || !runId || !roomData) return;
    autoHandling = true;
    try {
      if (roomData.card_choices?.length > 0) {
        const choice = roomData.card_choices[0];
        const res = await chooseCard(choice.id);
        roomData = { ...roomData, card_choices: [] };
        if (res && res.next_room) { nextRoom = res.next_room; }
        return;
      }
      if (roomData.relic_choices?.length > 0) {
        const choice = roomData.relic_choices[0];
        const res = await chooseRelic(choice.id);
        roomData = { ...roomData, relic_choices: [] };
        if (res && res.next_room) { nextRoom = res.next_room; }
        return;
      }
      const hasLoot = (roomData.loot?.gold || 0) > 0 || (roomData.loot?.items || []).length > 0;
      if (roomData.awaiting_loot || hasLoot) {
        await handleLootAcknowledge();
        return;
      }
      if (roomData.result === 'shop') {
        await handleNextRoom();
        return;
      }
      if (roomData.awaiting_next) {
        await handleNextRoom();
      }
    } finally {
      autoHandling = false;
    }
  }

  $: fullIdleMode && roomData && maybeAutoHandle();
  async function handleShopBuy(item) {
    if (!runId) return;
    roomData = await roomAction('0', { id: item.id, cost: item.cost });
  }
  async function handleShopReroll() {
    if (!runId) return;
    roomData = await roomAction('0', { action: 'reroll' });
  }
  async function handleShopLeave() {
    if (!runId) return;
    roomData = await roomAction('0', { action: 'leave' });
    if (roomData?.awaiting_card || roomData?.awaiting_relic || roomData?.awaiting_loot) {
      return;
    }
    const res = await advanceRoom();
    if (res && typeof res.current_index === 'number') {
      currentIndex = res.current_index;
      // Refresh map data when advancing floors
      if (res.next_room) {
        currentRoomType = res.next_room;
      }
      const mapData = await getMap(runId);
      if (mapData?.map?.rooms) {
        mapRooms = mapData.map.rooms;
        currentRoomType = mapRooms?.[currentIndex]?.room_type || currentRoomType;
      }
    }
    if (res && res.next_room) {
      nextRoom = res.next_room;
    }
    await enterRoom();
  }

  async function handleNextRoom() {
    if (!runId) return;
    // Ensure syncing is enabled when advancing to the next room
    haltSync = false;
    if (typeof window !== 'undefined') window.afHaltSync = false;
    
    // Check if we're currently in battle review mode by checking if review is open
    const inBattleReview = Boolean(
      roomData && (roomData.result === 'battle' || roomData.result === 'boss') && !battleActive &&
      typeof roomData.battle_index === 'number' && roomData.battle_index > 0
    );
    
    // If not in battle review, check for outstanding card/relic choices
    if (!inBattleReview) {
      const awaitingCardOrRelic =
        (roomData?.card_choices?.length || 0) > 0 ||
        (roomData?.relic_choices?.length || 0) > 0 ||
        roomData?.awaiting_card ||
        roomData?.awaiting_relic;
      if (awaitingCardOrRelic) return;
    }
    
    // If only loot remains, acknowledge it before advancing so the backend clears the gate.
    try {
      const hasLoot = Boolean((roomData?.loot?.gold || 0) > 0 || (roomData?.loot?.items || []).length > 0);
      if (roomData?.awaiting_loot || hasLoot) {
        stopBattlePoll();
        try { await acknowledgeLoot(runId); } catch { /* ignore if already acknowledged */ }
      }
    } catch { /* no-op */ }
    // If the run has ended due to defeat, clear state and show defeat popup immediately
    if (roomData?.ended && roomData?.result === "defeat") {
      handleDefeat();
      return;
    }
    // Close reward overlay and unmount previous BattleView immediately
    roomData = null;
    // GC last battle snapshot so review/combat viewer state doesn't linger
    lastBattleSnapshot = null;
    battleActive = false;
    stopBattlePoll();
    // Do not start state polling here; we'll advance and enter the next room
    // directly to avoid timing races that can require extra clicks.
    try {
      // Advance progression until the backend actually advances the room.
      // This collapses any remaining progression steps (e.g., loot → review)
      // so a single click proceeds.
      let res = await advanceRoom();
      let guard = 0;
      while (res && res.progression_advanced && guard++ < 5) {
        // Small delay to allow state write
        await new Promise((r) => setTimeout(r, 50));
        res = await advanceRoom();
      }
      if (res && typeof res.current_index === 'number') {
        currentIndex = res.current_index;
        // When advancing floors, the mapRooms data becomes stale
        // Use the next_room from the response instead of looking up in old mapRooms
        if (res.next_room) {
          currentRoomType = res.next_room;
        }
        // Refresh map data to get the updated floor information
        const mapData = await getMap(runId);
        if (mapData?.map?.rooms) {
          mapRooms = mapData.map.rooms;
          // Now we can safely use the updated mapRooms
          currentRoomType = mapRooms?.[currentIndex]?.room_type || currentRoomType;
        }
      }
      if (res && res.next_room) {
        nextRoom = res.next_room;
      }
      // Try entering the next room with a few short retries to avoid timing issues
      for (let i = 0; i < 5; i++) {
        await new Promise((r) => setTimeout(r, 150 + i * 150));
        await enterRoom();
        const isBattleSnapshot = roomData && (roomData.result === 'battle' || roomData.result === 'boss');
        const progressed = (roomData && (!isBattleSnapshot || battleActive));
        if (progressed) break;
      }
      // If we still haven't progressed, resume polling to recover gracefully
      if (!roomData) {
        startStatePoll();
      }
    } catch (e) {
      // If not ready (e.g., server 400), refresh snapshot so rewards remain visible.
      try {
        if (haltSync || !runId) return;
        const snap = mapStatuses(await roomAction("0", {"action": "snapshot"}));
        roomData = snap;
        // If the backend still indicates we're awaiting the next room and
        // there are no choices to make, attempt the advance again.
        const noChoices = ((snap?.card_choices?.length || 0) === 0) && ((snap?.relic_choices?.length || 0) === 0);
        if (snap?.awaiting_next && noChoices) {
          try {
            const res2 = await advanceRoom();
            if (res2 && typeof res2.current_index === 'number') {
              currentIndex = res2.current_index;
              // Refresh map data for retry attempts too
              if (res2.next_room) {
                currentRoomType = res2.next_room;
              }
              const mapData = await getMap(runId);
              if (mapData?.map?.rooms) {
                mapRooms = mapData.map.rooms;
                currentRoomType = mapRooms?.[currentIndex]?.room_type || currentRoomType;
              }
            }
            if (res2 && res2.next_room) {
              nextRoom = res2.next_room;
            }
            for (let i = 0; i < 5; i++) {
              await new Promise((r) => setTimeout(r, 150 + i * 150));
              await enterRoom();
              const isBattleSnapshot = roomData && (roomData.result === 'battle' || roomData.result === 'boss');
              const progressed = (roomData && (!isBattleSnapshot || battleActive));
              if (progressed) break;
            }
            if (!roomData) {
              startStatePoll();
            }
            return;
          } catch {}
        }
      } catch {
        /* no-op */
      }
    }
  }

  async function handleLootAcknowledge() {
    if (!runId) return;
    stopBattlePoll();
    try {
      await acknowledgeLoot(runId);
    } catch (e) {
      console.warn('Loot acknowledgement failed:', e?.message || e);
      startStatePoll();
      return;
    }
    await handleNextRoom();
  }

  async function handleForceNextRoom() {
    if (!runId) return;
    // Force-advance regardless of current overlay/state; safety for stuck awaiting_next
    haltSync = false;
    if (typeof window !== 'undefined') window.afHaltSync = false;
    // Clear current snapshot to avoid stale gating
    roomData = null;
    // Also clear any retained battle snapshot to free memory
    lastBattleSnapshot = null;
    battleActive = false;
    stopBattlePoll();
    // Start state polling when force advancing room
    startStatePoll();
    try {
      const res = await advanceRoom();
      if (res && typeof res.current_index === 'number') {
        currentIndex = res.current_index;
        if (res.next_room) currentRoomType = res.next_room;
        const mapData = await getMap(runId);
        if (mapData?.map?.rooms) {
          mapRooms = mapData.map.rooms;
          currentRoomType = mapRooms?.[currentIndex]?.room_type || currentRoomType;
        }
      }
      if (res && res.next_room) nextRoom = res.next_room;
      await enterRoom();
    } catch (e) {
      // Surface via overlay for visibility
      openOverlay('error', { message: 'Failed to force-advance room.', traceback: (e && e.stack) || '' });
    }
  }
  let items = [];
  $: items = buildRunMenu(
    {
      openRun,
      handleParty,
      openPulls,
      openFeedback,
      openInventory,
      openSettings: () => openOverlay('settings'),
      openGuidebook: () => openOverlay('guidebook')
    },
    battleActive
  );

  // NEW UI API APPROACH: Simplified state management
  let uiState = null;
  let uiStateTimer = null;
  
  function stopUIStatePoll() {
    if (uiStateTimer) {
      clearTimeout(uiStateTimer);
      uiStateTimer = null;
    }
  }

  function startUIStatePoll() {
    stopUIStatePoll();
    try {
      if (typeof window !== 'undefined' && (window.afRewardOpen === true || window.afReviewOpen === true)) return;
    } catch {}
    if (!haltSync) {
      pollUIState();
    }
  }

  async function pollUIState() {
    if (haltSync) return;
    try {
      if (typeof window !== 'undefined' && (window.afRewardOpen === true || window.afReviewOpen === true)) {
        stopUIStatePoll();
        return;
      }
    } catch {}

    // Don't poll if we're in a menu/overlay (not 'main') - same protection as old pollState
    try {
      const { get } = await import('svelte/store');
      const { overlayView } = await import('$lib/systems/OverlayController.js');
      const currentView = get(overlayView);
      if (currentView !== 'main') return;
    } catch {
      // If we can't check overlay state, continue
    }
    
    try {
      const newUIState = await getUIState();
      uiState = newUIState;
      
      // Update local state based on UI state  
      if (uiState.mode === 'menu') {
        // No active run, clear local state
        runId = '';
        roomData = null;
        battleActive = false;
        clearRunState();
      } else if (uiState.mode === 'playing') {
        // Active run, update state from backend
        runId = uiState.active_run || '';
        if (uiState.game_state) {
          const gameState = uiState.game_state;
          selectedParty = normalizePartyIds(gameState.party) || selectedParty;
          mapRooms = gameState.map?.rooms || [];
          
          if (gameState.current_state) {
            currentIndex = gameState.current_state.current_index || 0;
            currentRoomType = gameState.current_state.current_room_type || '';
            nextRoom = gameState.current_state.next_room_type || '';
            roomData = gameState.current_state.room_data || null;
          }
          
          saveRunState(runId);
        }
      } else if (uiState.mode === 'battle') {
        // Battle mode - backend reports an active combat
        runId = uiState.active_run || runId || '';
        const roomState = uiState.game_state?.current_state?.room_data;
        if (roomState && !roomState.snapshot_missing) {
          roomData = roomState;
          lastBattleSnapshot = roomState;
        } else {
          roomData = null;
        }
        battleActive = true;
        if (typeof window !== 'undefined') window.afBattleActive = true;
        startBattlePoll();
      } else {
        // Other modes like card_selection, relic_selection, etc.
        runId = uiState.active_run || runId || '';
        battleActive = false;
        if (typeof window !== 'undefined') window.afBattleActive = false;
        if (uiState.game_state?.current_state?.room_data) {
          roomData = uiState.game_state.current_state.room_data;
        }
      }
      
      // Continue polling (simplified - no complex battle state management)
      if (!haltSync && uiState.mode !== 'menu') {
        try {
          if (typeof window !== 'undefined' && (window.afRewardOpen === true || window.afReviewOpen === true)) return;
        } catch {}
        uiStateTimer = setTimeout(pollUIState, 1000); // Poll every second
      }
      
    } catch (e) {
      console.warn('UI state polling failed:', e);
      // Retry after delay
      if (!haltSync) {
        try {
          if (typeof window !== 'undefined' && (window.afRewardOpen === true || window.afReviewOpen === true)) return;
        } catch {}
        uiStateTimer = setTimeout(pollUIState, 2000);
      }
    }
  }

  // Simple UI action helper
  async function performUIAction(action, params = {}) {
    try {
      await sendAction(action, params);
      // Immediately poll for updated state
      await pollUIState();
    } catch (e) {
      console.error('UI action failed:', action, e);
      throw e;
    }
  }

</script>

<style>
  :global(:root) {
    --glass-bg: linear-gradient(135deg, rgba(10,10,10,0.96) 0%, rgba(30,30,30,0.92) 100%),
      repeating-linear-gradient(120deg, rgba(255,255,255,0.04) 0 2px, transparent 2px 8px),
      linear-gradient(60deg, rgba(255,255,255,0.06) 10%, rgba(0,0,0,0.38) 80%);
    --glass-border: 1.5px solid rgba(40,40,40,0.44);
    --glass-shadow: 0 2px 18px 0 rgba(0,0,0,0.32), 0 1.5px 0 0 rgba(255,255,255,0.04) inset;
    --glass-filter: blur(3.5px) saturate(1.05);
  }
  :global(html, body) {
    margin: 0;
    padding: 0;
    height: 100vh;
    /* allow scrolling when content is larger than the viewport
       (prevent content from being clipped at the right/bottom) */
    overflow: auto;
    background: #000;
    color: #fff;
    box-sizing: border-box;
  }

  /* Make the viewport container responsive and avoid forcing a second
     full-height which can overflow when inner elements have borders/padding. */
  .viewport-wrap {
    width: 100%;
    max-width: 98vw;
    max-height: 98vh;
    height: 100%;
    margin: 0 auto;
    box-sizing: border-box;
    /* avoid horizontal scrollbar; allow vertical scrolling */
    overflow-x: hidden;
    overflow-y: auto;
    padding: 0 0.5rem; /* small horizontal padding so elements don't touch the edge */
  }
</style>

<div class="viewport-wrap">
  <GameViewport
    runId={runId}
    roomData={roomData}
    battleSnapshot={lastBattleSnapshot}
    background={viewportBg}
    mapRooms={mapRooms}
    currentIndex={currentIndex}
    currentRoomType={currentRoomType}
    bind:selected={selectedParty}
    items={items}
    editorState={editorState}
    battleActive={battleActive}
    backendFlavor={backendFlavor}
    bind:animationSpeed
    bind:fullIdleMode
    on:startRun={handleStart}
    on:editorSave={(e) => handleEditorSave(e)}
    on:editorChange={(e) => handleEditorChange(e)}
    on:openInventory={openInventory}
    on:openParty={handleParty}
    on:openCombatViewer={openCombatViewer}
    on:pauseCombat={handlePauseCombat}
    on:resumeCombat={handleResumeCombat}
    on:back={backOverlay}
    on:home={homeOverlay}
    on:settings={() => openOverlay('settings')}
    on:rewardSelect={(e) => handleRewardSelect(e.detail)}
    on:loadRun={(e) => handleLoadExistingRun(e.detail)}
    on:startNewRun={handleStartNewRun}
    on:shopBuy={(e) => handleShopBuy(e.detail)}
    on:shopReroll={handleShopReroll}
    on:shopLeave={handleShopLeave}
    on:nextRoom={handleNextRoom}
    on:lootAcknowledge={handleLootAcknowledge}
    on:endRun={handleRunEnd}
    on:forceNextRoom={handleForceNextRoom}
    on:saveParty={handlePartySave}
    on:error={(e) => openOverlay('error', e.detail)}
  />
</div>
