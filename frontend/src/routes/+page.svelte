<script>
  import GameViewport from '$lib/components/GameViewport.svelte';
  import { get, onMount, onDestroy } from 'svelte';
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
    DISCORD_URL,
    WEBSITE_URL,
    openOverlay,
    backOverlay,
    homeOverlay,
    overlayBlocking,
    setManualSyncHalt,
    setBattleActive,
    runStateStore,
    startUIPolling,
    stopUIPolling,
    syncUIPolling,
    rootPollingController,
    configureBattlePollingHandlers,
    configureMapPollingHandlers,
    battlePollingController,
    mapPollingController,
    syncBattlePolling,
    syncMapPolling
  } from '$lib';
  import { updateParty, acknowledgeLoot } from '$lib/systems/uiApi.js';
  import { buildRunMenu } from '$lib/components/RunButtons.svelte';
  import { browser, dev } from '$app/environment';

  const runState = runStateStore;

  function getRunSnapshot() {
    return runState.getSnapshot();
  }

  function getRunId() {
    return runId;
  }

  function inBattle() {
    return Boolean(battleActive);
  }


  let runSnapshot = runState.getSnapshot();
  let selectedParty = [...runSnapshot.selectedParty];
  let runId = runSnapshot.runId;
  let mapRooms = runSnapshot.mapRooms;
  let currentIndex = runSnapshot.currentIndex;
  let currentRoomType = runSnapshot.currentRoomType;
  let nextRoom = runSnapshot.nextRoom;
  let roomData = runSnapshot.roomData;
  let battleActive = runSnapshot.battleActive;
  let lastBattleSnapshot = runSnapshot.lastBattleSnapshot;

  $: runSnapshot = $runState;
  $: ({ runId, mapRooms, currentIndex, currentRoomType, nextRoom, roomData, battleActive, lastBattleSnapshot } = runSnapshot);

  function partiesEqual(a, b) {
    if (a === b) return true;
    if (!Array.isArray(a) || !Array.isArray(b)) return false;
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i += 1) {
      if (a[i] !== b[i]) return false;
    }
    return true;
  }

  $: if (!partiesEqual(selectedParty, runSnapshot.selectedParty)) {
    selectedParty = [...runSnapshot.selectedParty];
  }

  $: if (!partiesEqual(runSnapshot.selectedParty, selectedParty)) {
    runState.setParty(selectedParty);
  }

  let backendFlavor = '';
  let viewportBg = '';

  let editorConfigs = {};
  let editorState = { pronouns: '', damageType: 'Light', hp: 0, attack: 0, defense: 0 };
  let playerConfigLoaded = false;
  let playerConfigPromise = null;
  // When true, suppress backend syncing/polling (e.g., during defeat popup)
  let haltSync = false;
  let fullIdleMode = false;
  let animationSpeed = 1;
  // Preserve the last live battle snapshot (with statuses) for review UI
  // Prevent overlapping room fetches
  let enterRoomPending = false;
  // Ensure shop purchases are processed sequentially
  let shopBuyQueue = Promise.resolve();
  // Track active shop processing to halt polling and show indicator
  let shopProcessing = false;
  let shopProcessingCount = 0;
  let detachUIPoll = null;

  function overlayIsBlocking() {
    try {
      return get(overlayBlocking);
    } catch {
      return false;
    }
  }

  $: setBattleActive($runState.battleActive);
  $: setManualSyncHalt(haltSync);

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

  function applyPlayerConfig(data = {}) {
    const toNumber = (value, fallback = 0) => {
      const num = Number(value);
      return Number.isFinite(num) ? num : fallback;
    };

    const normalized = {
      pronouns: data?.pronouns ?? '',
      damageType: data?.damage_type ?? data?.damageType ?? editorState.damageType ?? 'Light',
      hp: toNumber(data?.hp, editorState.hp ?? 0),
      attack: toNumber(data?.attack, editorState.attack ?? 0),
      defense: toNumber(data?.defense, editorState.defense ?? 0)
    };

    editorState = normalized;
    editorConfigs = { ...editorConfigs, player: { ...normalized } };
    playerConfigLoaded = true;
    return normalized;
  }

  async function syncPlayerConfig({ force = false } = {}) {
    if (!force) {
      if (playerConfigLoaded && editorConfigs?.player) {
        return { ...editorConfigs.player };
      }
      if (playerConfigPromise) {
        return playerConfigPromise;
      }
    }

    const loader = (async () => {
      try {
        const data = await getPlayerConfig();
        if (!data) {
          playerConfigLoaded = false;
          return null;
        }
        return applyPlayerConfig(data);
      } catch (error) {
        playerConfigLoaded = false;
        throw error;
      }
    })();

    playerConfigPromise = loader;

    try {
      const result = await loader;
      return result;
    } catch (error) {
      if (dev) {
        console.warn('Failed to load player config:', error);
      }
      return null;
    } finally {
      playerConfigPromise = null;
    }
  }

  onMount(async () => {
    detachUIPoll = rootPollingController.onUIState(applyUIStatePayload);
    // Always ensure sync is not halted on load
    // Always attempt to restore run state from localStorage, regardless of backend status
    const saved = loadRunState();

    await syncPlayerConfig().catch(() => {});
    
    async function syncWithBackend() {
      if (!saved?.runId) return;

      try {
        const data = await getMap(saved.runId);
        if (!data) {
          clearRunState();
          runState.reset();
          return;
        }

        runState.setRunId(saved.runId);
        runState.setParty(normalizePartyIds(data.party));
        runState.setMapRooms(data.map?.rooms || []);

        const currentState = data.current_state;
        if (currentState) {
          runState.setCurrentRoom({
            index: currentState.current_index ?? 0,
            currentRoomType: currentState.current_room_type || '',
            nextRoomType: currentState.next_room_type || ''
          });

          if (currentState.room_data) {
            runState.setRoomData(currentState.room_data);

            if (currentState.room_data.result === 'battle' && !currentState.awaiting_next) {
              runState.setBattleActive(true);
              stopMapPolling();
              triggerBattlePoll();
            }
          } else {
            runState.setRoomData(null);
          }
        } else {
          const rooms = data.map?.rooms || [];
          const index = data.map?.current || 0;
          runState.setCurrentRoom({
            index,
            currentRoomType: rooms[index]?.room_type || '',
            nextRoomType: rooms[index + 1]?.room_type || ''
          });
          await enterRoom();
        }

        saveRunState(saved.runId);

        if (!inBattle()) {
          scheduleMapRefresh();
        }
      } catch (e) {
        if (saved?.runId) {
          runState.setRunId(saved.runId);
        }
      }
    }
    
    // Try to get backend flavor and sync with backend
    try {
      backendFlavor = await getBackendFlavor();
      window.backendFlavor = backendFlavor;
      
      // Backend is ready, try new UI state approach first
      startUIPolling();
      try {
        const bootstrapState = await getUIState();
        applyUIStatePayload(bootstrapState);
        syncUIPolling();
      } catch (e) {
        // Fall back to existing sync approach
        console.warn('UI state polling failed, falling back to existing sync:', e);
        stopUIPolling();
        await syncWithBackend();
      }
    } catch (e) {
      // Backend not ready, but still attempt to restore run state for later
      if (saved?.runId) {
        runState.setRunId(saved.runId);
      }
      // Dedicated overlay opened in getBackendFlavor; user can retry when backend is ready
    }
  });

  onDestroy(() => {
    if (typeof detachUIPoll === 'function') {
      try { detachUIPoll(); } catch {}
    }
    stopUIPolling();
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

    const currentRunId = getRunId();
    if (currentRunId) {
      // If we have a runId, sync with backend to get current state
      try {
        const data = await getMap(currentRunId);
        if (data) {
          runState.setParty(normalizePartyIds(data.party));
          runState.setMapRooms(data.map?.rooms || []);

          // Use backend's current_state as source of truth
          if (data.current_state) {
            runState.setCurrentRoom({
              index: data.current_state.current_index || 0,
              currentRoomType: data.current_state.current_room_type || '',
              nextRoomType: data.current_state.next_room_type || ''
            });

            // Use room data from backend if available
            if (data.current_state.room_data) {
              runState.setRoomData(data.current_state.room_data);

              // If it's a battle and not awaiting next, start battle state
              if (data.current_state.room_data.result === 'battle' && !data.current_state.awaiting_next) {
                runState.setBattleActive(true);
                stopMapPolling(); // Stop map polling when battle starts
                triggerBattlePoll();
              }
            }
          } else {
            // Fallback for backward compatibility
            const rooms = data.map?.rooms || [];
            const index = data.map?.current || 0;
            runState.setCurrentRoom({
              index,
              currentRoomType: rooms[index]?.room_type || '',
              nextRoomType: rooms[index + 1]?.room_type || ''
            });
          }
        } else {
          // Run not found on backend, clear local state
          console.warn('Run not found on backend, clearing local state');
          clearRunState();
          runState.reset();
        }
      } catch (e) {
        // If we can't get run data, show error but don't clear runId
        console.warn('Failed to restore run data:', e.message);
      }

      homeOverlay();
      if (!inBattle() && !roomData) {
        enterRoom();
      }

      // Force backend state sync and start state polling when clicking run button
      if (getRunId() && !inBattle()) {
        scheduleMapRefresh();
      }
    } else {
      openOverlay('party-start');
    }
  }

  async function handleRunEnd() {
    // Halt any in-flight battle snapshot polling ASAP
    haltSync = true;
    // Proactively ask backend to end any active runs to avoid lingering state
    try { await endAllRuns(); } catch {}
    runState.reset();
    runState.setLastBattleSnapshot(null);
    runState.setBattleActive(false);
    stopBattlePolling();
    stopMapPolling();
    stopUIPolling();
    homeOverlay();
    clearRunState();
  }

  function handleDefeat() {
    // Clear run state, go to main menu, and show a defeat popup
    haltSync = true;
    handleRunEnd();
    // Open a lightweight popup informing the player
    openOverlay('defeat');
  }

  async function handleStart(event) {
    const pressure = event?.detail?.pressure || 0;
    haltSync = false;

    // Stop any existing polling when starting a new run
    stopMapPolling();
    stopBattlePolling();

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
          runState.setRunId(existing.run_id);
          runState.setMapRooms(existing.map?.rooms || []);
          runState.setCurrentRoom({
            index: existing.map?.current || 0,
            currentRoomType: existing.map?.rooms?.[existing.map?.current || 0]?.room_type || '',
            nextRoomType: existing.map?.rooms?.[(existing.map?.current || 0) + 1]?.room_type || ''
          });
          if (Array.isArray(existing?.party)) {
            runState.setParty(normalizePartyIds(existing.party));
          }
          runState.setBattleActive(false);
          saveRunState(existing.run_id);
          homeOverlay();
          await enterRoom();

          // Start state polling after resuming existing run (if not in battle)
          if (!inBattle()) {
            scheduleMapRefresh();
          }
          return;
        }
      }
    } catch (error) {
      // If checking for active runs fails, fall back to starting a new run
      console.warn('Failed to check for active runs, starting new run:', error);
    }

    // No active runs found, start a new run
    await syncPlayerConfig();

    const dmgType = editorConfigs.player?.damageType || editorState.damageType;
    const data = await startRun(selectedParty, dmgType, pressure);
    runState.setRunId(data.run_id);
    runState.setMapRooms(data.map?.rooms || []);
    runState.setCurrentRoom({
      index: data.map?.current || 0,
      currentRoomType: data.map?.rooms?.[data.map?.current || 0]?.room_type || '',
      nextRoomType: data.map?.rooms?.[(data.map?.current || 0) + 1]?.room_type || ''
    });
    runState.setBattleActive(false);
    saveRunState(data.run_id);
    homeOverlay();
    await enterRoom();

    // Start state polling after successfully starting new run (if not in battle)
    if (!inBattle()) {
      scheduleMapRefresh();
    }
  }

  async function handleLoadExistingRun(e) {
    try {
      const chosen = e?.detail || e; // Overlay dispatches the run object directly
      const rid = chosen?.run_id;
      if (!rid) { backOverlay(); return; }
      const data = await getMap(rid);
      if (!data) { backOverlay(); return; }
      runState.setRunId(rid);
      runState.setParty(normalizePartyIds(data.party));
      runState.setMapRooms(data.map?.rooms || []);
      runState.setCurrentRoom({
        index: data.map?.current || 0,
        currentRoomType: data.map?.rooms?.[data.map?.current || 0]?.room_type || '',
        nextRoomType: data.map?.rooms?.[(data.map?.current || 0) + 1]?.room_type || ''
      });
      runState.setBattleActive(false);
      saveRunState(rid);
      backOverlay();
      homeOverlay();
      await enterRoom();

      // Start state polling after loading existing run (if not in battle)
      if (!inBattle()) {
        scheduleMapRefresh();
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
    if (inBattle()) return;
    openOverlay('party');
  }

  async function handlePartySave() {
    if (getRunId()) {
      await updateParty(selectedParty);
    }
    backOverlay();
  }

  async function openEditor() {
    if (inBattle()) return;
    await syncPlayerConfig({ force: true });
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
    playerConfigLoaded = true;
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
    if (inBattle()) return;
    openOverlay('pulls');
  }


  function openFeedback() {
    window.open(FEEDBACK_URL, '_blank', 'noopener');
  }

  function openDiscord() {
    window.open(DISCORD_URL, '_blank', 'noopener');
  }

  function openWebsite() {
    window.open(WEBSITE_URL, '_blank', 'noopener');
  }

  async function openInventory() {
    openOverlay('inventory');
  }

  function openCombatViewer() {
    if (!inBattle()) return;
    openOverlay('combat-viewer');
  }

  // Combat pause/resume functions using roomAction
  async function handlePauseCombat() {
    const runId = getRunId();
    if (!runId) return;
    try {
      await roomAction('0', 'pause');
      console.log('Combat paused');
    } catch (error) {
      console.error('Failed to pause combat:', error);
    }
  }

  async function handleResumeCombat() {
    const runId = getRunId();
    if (!runId) return;
    try {
      await roomAction('0', 'resume');
      console.log('Combat resumed');
    } catch (error) {
      console.error('Failed to resume combat:', error);
    }
  }

  function hasRewards(snap) {
    if (!snap) return false;
    const cards = (snap?.card_choices?.length || 0) > 0;
    const relics = (snap?.relic_choices?.length || 0) > 0;
    const lootItems = (snap?.loot?.items?.length || 0) > 0;
    const lootGold = (snap?.loot?.gold || 0) > 0;
    return cards || relics || lootItems || lootGold;
  }

  function scheduleMapRefresh() {
    mapPollingController.syncNow();
  }

  function stopMapPolling() {
    try { mapPollingController.stop(); } catch {}
  }

  function triggerBattlePoll() {
    battlePollingController.syncNow();
  }

  function stopBattlePolling() {
    try { battlePollingController.stop(); } catch {}
  }

  configureBattlePollingHandlers({
    onMissingSnapshotTimeout: () => {
      try {
        openOverlay('error', { message: 'Battle state unavailable. Please reconnect.', traceback: '' });
      } catch {}
      scheduleMapRefresh();
    },
    onBattleError: ({ error }) => {
      if (error) {
        try {
          openOverlay('error', { message: error, traceback: '' });
        } catch {}
      }
      scheduleMapRefresh();
    },
    onBattleComplete: ({ snapshot }) => {
      if (snapshot?.result !== 'defeat') {
        scheduleMapRefresh();
      }
    },
    onAutoAdvance: async () => {
      try {
        await handleNextRoom();
      } catch {}
    },
    onDefeat: () => {
      handleDefeat();
    },
    onBattleSettled: () => {
      scheduleMapRefresh();
    },
    onRunEnd: () => {
      handleRunEnd();
    }
  });

  configureMapPollingHandlers({
    onRunEnd: () => {
      handleRunEnd();
    },
    onError: (error) => {
      console.warn('State polling failed:', error?.message || error);
    },
    onBattleDetected: () => {
      battlePollingController.syncNow();
    }
  });

  async function enterRoom() {
    if (enterRoomPending) return;
    if (haltSync) return;
    const snapshot = getRunSnapshot();
    const runId = snapshot.runId;
    if (!runId) return;
    const mapRooms = snapshot.mapRooms;
    const currentIndex = snapshot.currentIndex;
    const currentRoomType = snapshot.currentRoomType;
    const nextRoom = snapshot.nextRoom;
    const lastBattleSnapshot = snapshot.lastBattleSnapshot;
    enterRoomPending = true;
    stopBattlePolling();
    // Ensure header reflects the room we are entering now
    const fallbackRoomType = mapRooms?.[currentIndex]?.room_type || currentRoomType || nextRoom;
    if (!fallbackRoomType) {
      enterRoomPending = false;
      return;
    }
    runState.setCurrentRoom({ currentRoomType: fallbackRoomType });
    let endpoint = fallbackRoomType;
    if (endpoint.includes('battle')) {
      endpoint = fallbackRoomType.includes('boss') ? 'boss' : 'battle';
    }
    try {
      // Fetch first, then decide whether to show rewards or start battle polling.
      const data = mapStatuses(await roomAction("0", ""));
      runState.setRoomData(data);
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
        runState.setParty(normalizePartyIds(data.party));
      }
      // Keep map-derived indices and current room type in sync when available
      if (typeof data.current_index === 'number') {
        runState.setCurrentRoom({ index: data.current_index });
      }
      if (data.current_room) {
        runState.setCurrentRoom({ currentRoomType: data.current_room });
      }
      const derivedNextRoom = data.next_room || (mapRooms?.[currentIndex + 1]?.room_type || nextRoom || '');
      runState.setCurrentRoom({ nextRoomType: derivedNextRoom });
      saveRunState(runId);
      if (endpoint === 'battle' || endpoint === 'boss') {
        const gotRewards = hasRewards(data);
        if (gotRewards) {
          runState.setBattleActive(false);
          stopBattlePolling();
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
              runState.setRoomData(snap);
              runState.setLastBattleSnapshot(snap || lastBattleSnapshot);
              runState.setBattleActive(false);
              stopBattlePolling();
              runState.setCurrentRoom({
                nextRoomType: snap.next_room || nextRoom,
                index: typeof snap.current_index === 'number' ? snap.current_index : undefined,
                currentRoomType: snap.current_room || undefined
              });
              return;
            }
          } catch {}
        }
        // If the snapshot didn't include current room type yet, fall back to pre-room value
        // Actively set a sensible type for header during combat
        if (!currentRoomType) {
          const fallback = mapRooms?.[currentIndex]?.room_type || (endpoint.includes('boss') ? 'battle-boss-floor' : 'battle-normal');
          runState.setCurrentRoom({ currentRoomType: fallback });
        }
        runState.setBattleActive(true);
        triggerBattlePoll();
      } else {
        runState.setBattleActive(false);
        stopBattlePolling();
        // Start state polling for non-battle rooms
        scheduleMapRefresh();
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
        runState.setRoomData(snap);
        runState.setBattleActive(false);
        stopBattlePolling();
        runState.setCurrentRoom({
          nextRoomType: snap.next_room || nextRoom,
          index: typeof snap.current_index === 'number' ? snap.current_index : undefined,
          currentRoomType: snap.current_room || undefined
        });
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
      if (roomData) {
        runState.setRoomData({ ...roomData, card_choices: [] });
      }
    } else if (detail.type === 'relic') {
      // chooseRelic now routes via /ui/action and does not take runId
      res = await chooseRelic(detail.id);
      if (roomData) {
        runState.setRoomData({ ...roomData, relic_choices: [] });
      }
    }
    if (res && res.next_room) {
      runState.setCurrentRoom({ nextRoomType: res.next_room });
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
        runState.setRoomData({ ...roomData, card_choices: [] });
        if (res && res.next_room) { runState.setCurrentRoom({ nextRoomType: res.next_room }); }
        return;
      }
      if (roomData.relic_choices?.length > 0) {
        const choice = roomData.relic_choices[0];
        const res = await chooseRelic(choice.id);
        runState.setRoomData({ ...roomData, relic_choices: [] });
        if (res && res.next_room) { runState.setCurrentRoom({ nextRoomType: res.next_room }); }
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
  function readFiniteNumber(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
  }

  function extractShopPricing(entry) {
    if (!entry || typeof entry !== 'object') {
      return { base: null, taxed: null, tax: null };
    }
    const base = (() => {
      const candidates = [
        entry.base_cost,
        entry.base_price,
        entry.pricing?.base,
        entry.price,
        entry.cost
      ];
      for (const candidate of candidates) {
        const resolved = readFiniteNumber(candidate);
        if (resolved !== null) return resolved;
      }
      return null;
    })();
    const taxed = (() => {
      const candidates = [
        entry.taxed_cost,
        entry.pricing?.taxed,
        entry.price,
        entry.cost,
        base
      ];
      for (const candidate of candidates) {
        const resolved = readFiniteNumber(candidate);
        if (resolved !== null) return resolved;
      }
      return base;
    })();
    const tax = (() => {
      const candidates = [
        entry.tax,
        entry.pricing?.tax,
        (taxed !== null && base !== null) ? taxed - base : null
      ];
      for (const candidate of candidates) {
        const resolved = readFiniteNumber(candidate);
        if (resolved !== null) return resolved < 0 ? 0 : resolved;
      }
      if (taxed !== null && base !== null) {
        const diff = taxed - base;
        return Number.isFinite(diff) && diff > 0 ? diff : 0;
      }
      return null;
    })();
    return { base, taxed, tax };
  }

  function normalizeShopPurchase(entry) {
    if (!entry || typeof entry !== 'object') {
      return null;
    }
    const id = entry.id ?? entry.item ?? null;
    if (!id) {
      return null;
    }
    const { base, taxed, tax } = extractShopPricing(entry);
    const normalized = { id };
    if (base !== null) {
      normalized.base_cost = base;
      normalized.base_price = base;
    }
    if (taxed !== null) {
      normalized.cost = taxed;
      normalized.price = taxed;
      normalized.taxed_cost = taxed;
    }
    if (tax !== null) {
      normalized.tax = tax;
    }
    return normalized;
  }

  async function handleShopBuy(item) {
    if (!runId) return;
    const rawEntries = (() => {
      if (Array.isArray(item)) {
        return item;
      }
      if (item && typeof item === 'object') {
        if (Array.isArray(item.items)) {
          return item.items;
        }
        if (item.items && typeof item.items === 'object') {
          return [item.items];
        }
        return [item];
      }
      return [];
    })();

    const purchases = rawEntries
      .map((entry) => normalizeShopPurchase(entry))
      .filter((entry) => entry !== null);

    if (!purchases.length) {
      return;
    }

    const payload = (() => {
      if (purchases.length === 1) {
        const [single] = purchases;
        // Preserve per-item pricing fields so payload.base_cost / payload.taxed_cost / payload.tax
        // remain available for backend analytics and receipts.
        return { ...single, items: { ...single } };
      }
      return { items: purchases.map((entry) => ({ ...entry })) };
    })();

    // Begin processing gate: first active purchase halts UI polling and shows indicator
    shopProcessingCount += 1;
    if (shopProcessingCount === 1) {
      shopProcessing = true;
      haltSync = true;
      // Stop any polling timers immediately
      try { stopBattlePolling(); } catch {}
      try { stopMapPolling(); } catch {}
      try { if (uiStateTimer) { clearTimeout(uiStateTimer); uiStateTimer = null; } } catch {}
    }

    try {
      // Queue shop purchases to ensure backend requests run one at a time
      // and add a brief pacing delay between purchases for clarity.
      shopBuyQueue = shopBuyQueue
        .then(async () => {
          const result = await roomAction('0', payload);
          runState.setRoomData(result);
          // Slow down between sequential purchases
          await new Promise((r) => setTimeout(r, 750));
        })
        .catch((err) => {
          console.error('Shop buy error', err);
        });
      // Await the queued operation so callers don't overlap implicitly
      await shopBuyQueue;
    } finally {
      shopProcessingCount = Math.max(0, shopProcessingCount - 1);
      if (shopProcessingCount === 0) {
        // Resume polling after processing completes
        shopProcessing = false;
        haltSync = false;
        // Optionally kick a state poll to refresh UI
        try { scheduleMapRefresh(); } catch {}
      }
    }
  }
  async function handleShopReroll() {
    if (!runId) return;
    const updated = await roomAction('0', { action: 'reroll' });
    runState.setRoomData(updated);
  }
  async function handleShopLeave() {
    if (!runId) return;
    const leaveState = await roomAction('0', { action: 'leave' });
    runState.setRoomData(leaveState);
    if (leaveState?.awaiting_card || leaveState?.awaiting_relic || leaveState?.awaiting_loot) {
      return;
    }
    const res = await advanceRoom();
    if (res && typeof res.current_index === 'number') {
      runState.setCurrentRoom({ index: res.current_index });
      // Refresh map data when advancing floors
      if (res.next_room) {
        runState.setCurrentRoom({ currentRoomType: res.next_room });
      }
      const mapData = await getMap(runId);
      if (mapData?.map?.rooms) {
        const updatedRooms = mapData.map.rooms;
        runState.setMapRooms(updatedRooms);
        runState.setCurrentRoom({ currentRoomType: updatedRooms?.[res.current_index]?.room_type || currentRoomType });
      }
    }
    if (res && res.next_room) {
      runState.setCurrentRoom({ nextRoomType: res.next_room });
    }
    await enterRoom();
  }

  async function handleNextRoom() {
    if (!runId) return;
    // Ensure syncing is enabled when advancing to the next room
    haltSync = false;
    
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
        stopBattlePolling();
        try { await acknowledgeLoot(runId); } catch { /* ignore if already acknowledged */ }
      }
    } catch { /* no-op */ }
    // If the run has ended due to defeat, clear state and show defeat popup immediately
    if (roomData?.ended && roomData?.result === "defeat") {
      handleDefeat();
      return;
    }
    // Close reward overlay and unmount previous BattleView immediately
    runState.setRoomData(null);
    // GC last battle snapshot so review/combat viewer state doesn't linger
    runState.setLastBattleSnapshot(null);
    runState.setBattleActive(false);
    stopBattlePolling();
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
        runState.setCurrentRoom({ index: res.current_index });
        // When advancing floors, the mapRooms data becomes stale
        // Use the next_room from the response instead of looking up in old mapRooms
        if (res.next_room) {
          runState.setCurrentRoom({ currentRoomType: res.next_room });
        }
        // Refresh map data to get the updated floor information
        const mapData = await getMap(runId);
        if (mapData?.map?.rooms) {
          const updatedRooms = mapData.map.rooms;
          runState.setMapRooms(updatedRooms);
          runState.setCurrentRoom({ currentRoomType: updatedRooms?.[res.current_index]?.room_type || currentRoomType });
        }
      }
      if (res && res.next_room) {
        runState.setCurrentRoom({ nextRoomType: res.next_room });
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
        scheduleMapRefresh();
      }
    } catch (e) {
      // If not ready (e.g., server 400), refresh snapshot so rewards remain visible.
      try {
        if (haltSync || !runId) return;
        const snap = mapStatuses(await roomAction("0", {"action": "snapshot"}));
        runState.setRoomData(snap);
        // If the backend still indicates we're awaiting the next room and
        // there are no choices to make, attempt the advance again.
        const noChoices = ((snap?.card_choices?.length || 0) === 0) && ((snap?.relic_choices?.length || 0) === 0);
        if (snap?.awaiting_next && noChoices) {
          try {
            const res2 = await advanceRoom();
            if (res2 && typeof res2.current_index === 'number') {
              runState.setCurrentRoom({ index: res2.current_index });
              // Refresh map data for retry attempts too
              if (res2.next_room) {
                runState.setCurrentRoom({ currentRoomType: res2.next_room });
              }
              const mapData = await getMap(runId);
              if (mapData?.map?.rooms) {
                const retryRooms = mapData.map.rooms;
                runState.setMapRooms(retryRooms);
                runState.setCurrentRoom({ currentRoomType: retryRooms?.[res2.current_index]?.room_type || currentRoomType });
              }
            }
            if (res2 && res2.next_room) {
              runState.setCurrentRoom({ nextRoomType: res2.next_room });
            }
            for (let i = 0; i < 5; i++) {
              await new Promise((r) => setTimeout(r, 150 + i * 150));
              await enterRoom();
              const isBattleSnapshot = roomData && (roomData.result === 'battle' || roomData.result === 'boss');
              const progressed = (roomData && (!isBattleSnapshot || battleActive));
              if (progressed) break;
            }
            if (!roomData) {
              scheduleMapRefresh();
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
    stopBattlePolling();
    try {
      await acknowledgeLoot(runId);
    } catch (e) {
      console.warn('Loot acknowledgement failed:', e?.message || e);
      scheduleMapRefresh();
      return;
    }
    await handleNextRoom();
  }

  async function handleForceNextRoom() {
    if (!runId) return;
    // Force-advance regardless of current overlay/state; safety for stuck awaiting_next
    haltSync = false;
    // Clear current snapshot to avoid stale gating
    runState.setRoomData(null);
    // Also clear any retained battle snapshot to free memory
    runState.setLastBattleSnapshot(null);
    runState.setBattleActive(false);
    stopBattlePolling();
    // Start state polling when force advancing room
    scheduleMapRefresh();
    try {
      const res = await advanceRoom();
      if (res && typeof res.current_index === 'number') {
        runState.setCurrentRoom({ index: res.current_index });
        if (res.next_room) runState.setCurrentRoom({ currentRoomType: res.next_room });
        const mapData = await getMap(runId);
        if (mapData?.map?.rooms) {
          const refreshedRooms = mapData.map.rooms;
          runState.setMapRooms(refreshedRooms);
          runState.setCurrentRoom({ currentRoomType: refreshedRooms?.[res.current_index]?.room_type || currentRoomType });
        }
      }
      if (res && res.next_room) runState.setCurrentRoom({ nextRoomType: res.next_room });
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
      openDiscord,
      openWebsite,
      openInventory,
      openSettings: () => openOverlay('settings'),
      openGuidebook: () => openOverlay('guidebook')
    },
    battleActive
  );

  let uiState = null;

  function applyUIStatePayload(newUIState) {
    uiState = newUIState;
    let summary;
    try {
      summary = runStateStore.applyUIState(newUIState);
    } catch (error) {
      if (dev) {
        console.warn('Failed to update runStateStore from UI state:', error);
      }
    }

    if (!summary) {
      return;
    }

    const { mode, runId: activeRunId, battleActive: uiBattleActive } = summary;

    if (mode === 'menu') {
      runState.setLastBattleSnapshot(null);
      runState.setBattleActive(false);
      stopBattlePolling();
      stopMapPolling();
      clearRunState();
      return;
    }

    if (activeRunId) {
      saveRunState(activeRunId);
    }

    if (uiBattleActive) {
      triggerBattlePoll();
    } else {
      runState.setBattleActive(false);
      scheduleMapRefresh();
    }
  }

  // Simple UI action helper
  async function performUIAction(action, params = {}) {
    try {
      await sendAction(action, params);
      // Immediately poll for updated state
      syncUIPolling();
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
    {shopProcessing}
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
