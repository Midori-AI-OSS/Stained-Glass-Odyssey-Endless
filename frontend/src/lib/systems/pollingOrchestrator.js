import { get, writable } from 'svelte/store';
import { haltSync, overlayBlocking } from './overlayState.js';
import { normalizePartyIds, runStateStore, saveRunState } from './runState.js';
import { getUIState, getMap, roomAction } from './uiApi.js';
import { shouldHandleRunEndError } from './runErrorGuard.js';

const DEFAULT_SUCCESS_DELAY_MS = 1000;
const DEFAULT_RETRY_BASE_MS = 2000;
const DEFAULT_MAX_RETRY_MS = 10000;
const DEFAULT_STATE_POLL_DELAY_MS = 5000;

function calculateBackoff(base, max, failures) {
  const attempt = Math.max(1, failures);
  const delay = base * Math.pow(2, attempt - 1);
  return Math.min(delay, max);
}

async function loadOverlayView() {
  const [{ get }, overlay] = await Promise.all([
    import('svelte/store'),
    import('./OverlayController.js')
  ]);
  return () => {
    try {
      return get(overlay.overlayView);
    } catch {
      return 'main';
    }
  };
}

function createOverlayResolver(getOverlayView) {
  let overlayAccessorPromise = null;
  return async function resolveOverlayView() {
    if (typeof getOverlayView === 'function') {
      try {
        return await getOverlayView();
      } catch {
        return 'main';
      }
    }

    if (!overlayAccessorPromise) {
      overlayAccessorPromise = loadOverlayView();
    }
    try {
      const accessor = await overlayAccessorPromise;
      return accessor();
    } catch {
      return 'main';
    }
  };
}

function createPollGate({ haltStore, overlayStore, resolveOverlayView }) {
  return async function shouldPoll() {
    if (haltStore && get(haltStore)) return false;
    if (overlayStore && get(overlayStore)) return false;
    try {
      if (typeof resolveOverlayView === 'function') {
        return (await resolveOverlayView()) === 'main';
      }
    } catch {
      return true;
    }
    return true;
  };
}

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

function hasRewards(snap) {
  if (!snap) return false;
  const cards = (snap?.card_choices?.length || 0) > 0;
  const relics = (snap?.relic_choices?.length || 0) > 0;
  const lootItems = (snap?.loot?.items?.length || 0) > 0;
  const lootGold = (snap?.loot?.gold || 0) > 0;
  return cards || relics || lootItems || lootGold;
}

function getFramerateSetting() {
  try {
    const raw = typeof window !== 'undefined' ? window.localStorage?.getItem('autofighter_settings') : null;
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
  return 10000 / Math.max(1, fps);
}

function getBattleStallTicks() {
  const fps = getFramerateSetting();
  const pollsPerSecond = Math.max(0.1, fps / 10);
  return Math.max(1, Math.round(pollsPerSecond * 3));
}

export function createPollingController({
  getUIStateFn = getUIState,
  haltStore = haltSync,
  overlayStore = overlayBlocking,
  getOverlayView = null,
  successDelayMs = DEFAULT_SUCCESS_DELAY_MS,
  retryBaseDelayMs = DEFAULT_RETRY_BASE_MS,
  maxRetryDelayMs = DEFAULT_MAX_RETRY_MS,
  initialSubscribers = [runStateStore.applyUIState]
} = {}) {
  const statusStore = writable({
    active: false,
    paused: false,
    lastTick: null,
    consecutiveFailures: 0,
    lastError: null
  });

  const uiSubscribers = new Set(initialSubscribers.filter((fn) => typeof fn === 'function'));

  const resolveOverlayView = createOverlayResolver(getOverlayView);
  const shouldPoll = createPollGate({ haltStore, overlayStore, resolveOverlayView });

  let timer = null;
  let destroyed = false;
  let stopped = false;

  function notifyUI(payload) {
    for (const handler of Array.from(uiSubscribers)) {
      try {
        handler(payload);
      } catch (error) {
        console.error('UI polling handler failed', error);
      }
    }
  }

  function setStatus(updater) {
    statusStore.update((current) => {
      if (typeof updater === 'function') {
        return { ...current, ...updater(current) };
      }
      return { ...current, ...(updater || {}) };
    });
  }

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function schedule(delay) {
    if (destroyed || stopped) return;
    clearTimer();
    timer = setTimeout(() => {
      timer = null;
      tick();
    }, Math.max(0, delay));
  }

  async function tick() {
    if (destroyed || stopped) return;

    const canPoll = await shouldPoll();
    if (destroyed || stopped) {
      return;
    }

    if (!canPoll) {
      setStatus({ active: false, paused: true });
      if (!destroyed && !stopped) {
        schedule(successDelayMs);
      }
      return;
    }

    setStatus({ active: true, paused: false });

    try {
      const payload = await getUIStateFn();
      if (destroyed || stopped) {
        return;
      }
      notifyUI(payload);
      setStatus({
        active: false,
        paused: false,
        lastTick: Date.now(),
        consecutiveFailures: 0,
        lastError: null
      });
      schedule(successDelayMs);
    } catch (error) {
      setStatus((current) => {
        const failures = current.consecutiveFailures + 1;
        return {
          active: false,
          paused: false,
          lastTick: Date.now(),
          consecutiveFailures: failures,
          lastError: error
        };
      });
      if (!destroyed && !stopped) {
        const delay = calculateBackoff(
          retryBaseDelayMs,
          maxRetryDelayMs,
          get(statusStore).consecutiveFailures
        );
        schedule(delay);
      }
    }
  }

  function start() {
    destroyed = false;
    stopped = false;
    if (!timer) {
      schedule(0);
    }
  }

  function stop() {
    stopped = true;
    clearTimer();
    setStatus({ active: false, paused: false });
  }

  function syncNow() {
    if (destroyed || stopped) return;
    schedule(0);
  }

  function destroy() {
    destroyed = true;
    stopped = true;
    clearTimer();
    uiSubscribers.clear();
  }

  function onUIState(handler) {
    if (typeof handler !== 'function') {
      return () => {};
    }
    uiSubscribers.add(handler);
    return () => {
      uiSubscribers.delete(handler);
    };
  }

  return {
    start,
    stop,
    syncNow,
    destroy,
    onUIState,
    status: { subscribe: statusStore.subscribe }
  };
}

export function createBattlePollingController({
  fetchSnapshot = () => roomAction('0', { action: 'snapshot' }),
  haltStore = haltSync,
  overlayStore = overlayBlocking,
  getOverlayView = null,
  runStore = runStateStore,
  getDelayMs = getBattlePollDelayMs,
  getStallLimit = getBattleStallTicks,
  handlers = {}
} = {}) {
  const statusStore = writable({
    active: false,
    lastTick: null,
    consecutiveFailures: 0,
    lastError: null
  });

  const resolveOverlayView = createOverlayResolver(getOverlayView);
  const shouldPoll = createPollGate({ haltStore, overlayStore, resolveOverlayView });

  const callbacks = {
    onSnapshot: handlers.onSnapshot || (() => {}),
    onBattleComplete: handlers.onBattleComplete || (() => {}),
    onAutoAdvance: handlers.onAutoAdvance || (() => {}),
    onDefeat: handlers.onDefeat || (() => {}),
    onMissingSnapshotTimeout: handlers.onMissingSnapshotTimeout || (() => {}),
    onBattleError: handlers.onBattleError || (() => {}),
    onBattleSettled: handlers.onBattleSettled || (() => {}),
    onRunEnd: handlers.onRunEnd || (() => {})
  };

  function configureHandlers(next = {}) {
    if (next && typeof next === 'object') {
      for (const [key, value] of Object.entries(next)) {
        if (key in callbacks && typeof value === 'function') {
          callbacks[key] = value;
        }
      }
    }
  }

  let timer = null;
  let destroyed = false;
  let missingSnapTicks = 0;
  let stalledTicks = 0;
  let unsubscribeRun = null;
  let previousBattleActive = false;

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function schedule(delay) {
    if (destroyed) return;
    clearTimer();
    timer = setTimeout(() => {
      timer = null;
      tick();
    }, Math.max(0, delay));
  }

  async function tick() {
    if (destroyed) return;
    const snapshot = runStore.getSnapshot();
    if (!snapshot.battleActive || !snapshot.runId) {
      stop();
      return;
    }

    if (!(await shouldPoll())) {
      setStatus({ active: false });
      schedule(getDelayMs());
      return;
    }

    setStatus({ active: true });

    try {
      const raw = await fetchSnapshot(snapshot.runId);
      const snap = mapStatuses(raw);
      const stallLimit = getStallLimit();

      if (snap?.snapshot_missing) {
        missingSnapTicks += 1;
        if (missingSnapTicks > stallLimit) {
          runStore.setBattleActive(false);
          clearTimer();
          callbacks.onMissingSnapshotTimeout({ snapshot: snap, runId: snapshot.runId });
          callbacks.onBattleSettled({ snapshot: snap, runId: snapshot.runId });
          setStatus({ active: false, consecutiveFailures: 0, lastTick: Date.now() });
          return;
        }
      } else {
        missingSnapTicks = 0;
        runStore.setLastBattleSnapshot(snap || snapshot.lastBattleSnapshot);
      }

      callbacks.onSnapshot({ snapshot: snap, runId: snapshot.runId });

      if (snap?.error) {
        runStore.setRoomData(snap);
        runStore.setLastBattleSnapshot(snap || snapshot.lastBattleSnapshot);
        runStore.setBattleActive(false);
        clearTimer();
        callbacks.onBattleError({ snapshot: snap, runId: snapshot.runId, error: snap.error });
        callbacks.onBattleSettled({ snapshot: snap, runId: snapshot.runId });
        setStatus({ active: false, lastTick: Date.now(), consecutiveFailures: 0, lastError: null });
        return;
      }

      const snapHasRewards = hasRewards(snap);
      const snapCompleted = Boolean(snap?.awaiting_next) || Boolean(snap?.next_room) || snap?.result === 'defeat';
      const partyDead = Array.isArray(snap?.party) && snap.party.length > 0 && snap.party.every((m) => (m?.hp ?? 1) <= 0);
      const foesDead = Array.isArray(snap?.foes) && snap.foes.length > 0 && snap.foes.every((f) => (f?.hp ?? 1) <= 0);
      const combatOver = partyDead || foesDead;

      if (snapHasRewards || snapCompleted) {
        runStore.setRoomData(snap);
        runStore.setLastBattleSnapshot(snap || snapshot.lastBattleSnapshot);
        runStore.setBattleActive(false);
        runStore.setCurrentRoom({
          nextRoomType: snap?.next_room || snapshot.nextRoom,
          index: typeof snap?.current_index === 'number' ? snap.current_index : undefined,
          currentRoomType: snap?.current_room || undefined
        });
        clearTimer();
        callbacks.onBattleComplete({ snapshot: snap, runId: snapshot.runId });
        if (snap?.result === 'defeat') {
          callbacks.onDefeat({ snapshot: snap, runId: snapshot.runId });
        } else if (!snapHasRewards && snap?.awaiting_next && !snap?.awaiting_loot) {
          callbacks.onAutoAdvance({ snapshot: snap, runId: snapshot.runId });
        }
        callbacks.onBattleSettled({ snapshot: snap, runId: snapshot.runId });
        setStatus({ active: false, lastTick: Date.now(), consecutiveFailures: 0, lastError: null });
        return;
      }

      if (combatOver) {
        runStore.setRoomData(snap);
        stalledTicks += 1;
        if (stalledTicks > stallLimit) {
          runStore.setBattleActive(false);
          runStore.setRoomData({ ...snap, error: 'Battle results could not be fetched.' });
          clearTimer();
          callbacks.onBattleError({ snapshot: snap, runId: snapshot.runId, error: 'Battle results could not be fetched.' });
          callbacks.onBattleSettled({ snapshot: snap, runId: snapshot.runId });
          setStatus({ active: false, lastTick: Date.now(), consecutiveFailures: 0, lastError: null });
          return;
        }
      } else {
        stalledTicks = 0;
      }

      setStatus({ active: false, lastTick: Date.now(), consecutiveFailures: 0, lastError: null });
      schedule(getDelayMs());
    } catch (error) {
      if (shouldHandleRunEndError(error)) {
        runStore.setBattleActive(false);
        clearTimer();
        callbacks.onRunEnd({ error });
        callbacks.onBattleSettled({ error });
        setStatus({ active: false, lastError: null, consecutiveFailures: 0, lastTick: Date.now() });
        return;
      }

      setStatus((current) => ({
        active: false,
        lastTick: Date.now(),
        lastError: error,
        consecutiveFailures: current.consecutiveFailures + 1
      }));
      schedule(getDelayMs());
    }
  }

  function setStatus(updater) {
    statusStore.update((current) => {
      if (typeof updater === 'function') {
        return { ...current, ...updater(current) };
      }
      return { ...current, ...(updater || {}) };
    });
  }

  function start() {
    destroyed = false;
    missingSnapTicks = 0;
    stalledTicks = 0;
    if (!timer) {
      schedule(0);
    }
  }

  function stop() {
    clearTimer();
    setStatus({ active: false });
  }

  function syncNow() {
    if (destroyed) return;
    schedule(0);
  }

  function destroy() {
    destroyed = true;
    clearTimer();
    if (unsubscribeRun) {
      unsubscribeRun();
      unsubscribeRun = null;
    }
  }

  unsubscribeRun = runStore.subscribe((state) => {
    if (destroyed) return;
    if (state.battleActive && state.runId) {
      if (!previousBattleActive) {
        start();
      }
    } else {
      if (previousBattleActive) {
        stop();
      }
    }
    previousBattleActive = Boolean(state.battleActive && state.runId);
  });

  return {
    start,
    stop,
    syncNow,
    destroy,
    configureHandlers,
    status: { subscribe: statusStore.subscribe }
  };
}

export function createMapPollingController({
  getMapFn = getMap,
  haltStore = haltSync,
  overlayStore = overlayBlocking,
  getOverlayView = null,
  runStore = runStateStore,
  intervalMs = DEFAULT_STATE_POLL_DELAY_MS,
  handlers = {}
} = {}) {
  const resolveOverlayView = createOverlayResolver(getOverlayView);
  const shouldPoll = createPollGate({ haltStore, overlayStore, resolveOverlayView });

  const callbacks = {
    onRunEnd: handlers.onRunEnd || (() => {}),
    onError: handlers.onError || (() => {}),
    onUpdate: handlers.onUpdate || (() => {}),
    onBattleDetected: handlers.onBattleDetected || (() => {})
  };

  function configureHandlers(next = {}) {
    if (next && typeof next === 'object') {
      for (const [key, value] of Object.entries(next)) {
        if (key in callbacks && typeof value === 'function') {
          callbacks[key] = value;
        }
      }
    }
  }

  let timer = null;
  let destroyed = false;
  let unsubscribeRun = null;
  let previousEligible = false;

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function schedule(delay) {
    if (destroyed) return;
    clearTimer();
    timer = setTimeout(() => {
      timer = null;
      tick();
    }, Math.max(0, delay));
  }

  async function tick() {
    if (destroyed) return;
    const snapshot = runStore.getSnapshot();
    if (!snapshot.runId || snapshot.battleActive) {
      stop();
      return;
    }

    if (!(await shouldPoll())) {
      schedule(intervalMs);
      return;
    }

    try {
      const data = await getMapFn(snapshot.runId);
      if (!data) {
        callbacks.onRunEnd();
        return;
      }

      if (data.party) {
        runStore.setParty(normalizePartyIds(data.party));
      }
      if (data.map?.rooms) {
        runStore.setMapRooms(data.map.rooms || []);
      }

      const currentState = data.current_state || {};
      if (typeof currentState.current_index === 'number') {
        runStore.setCurrentRoom({ index: currentState.current_index });
      }
      if (typeof currentState.current_room_type === 'string') {
        runStore.setCurrentRoom({ currentRoomType: currentState.current_room_type });
      }
      if (typeof currentState.next_room_type === 'string') {
        runStore.setCurrentRoom({ nextRoomType: currentState.next_room_type });
      }

      if (currentState.room_data) {
        runStore.setRoomData(currentState.room_data);
        if (currentState.room_data.result === 'battle' && !currentState.awaiting_next) {
          runStore.setBattleActive(true);
          callbacks.onBattleDetected({ data: currentState.room_data, runId: snapshot.runId });
        }
      }

      saveRunState(snapshot.runId);
      callbacks.onUpdate({ data, runId: snapshot.runId });
    } catch (error) {
      callbacks.onError(error);
      if (shouldHandleRunEndError(error) || String(error?.message || '').toLowerCase().includes('run ended')) {
        callbacks.onRunEnd();
        return;
      }
    }

    if (!destroyed) {
      schedule(intervalMs);
    }
  }

  function start() {
    destroyed = false;
    if (!timer) {
      schedule(intervalMs);
    }
  }

  function stop() {
    clearTimer();
  }

  function syncNow() {
    if (destroyed) return;
    schedule(0);
  }

  function destroy() {
    destroyed = true;
    clearTimer();
    if (unsubscribeRun) {
      unsubscribeRun();
      unsubscribeRun = null;
    }
  }

  unsubscribeRun = runStore.subscribe((state) => {
    if (destroyed) return;
    const eligible = Boolean(state.runId && !state.battleActive);
    if (eligible && !previousEligible) {
      start();
    }
    if (!eligible && previousEligible) {
      stop();
    }
    previousEligible = eligible;
  });

  return {
    start,
    stop,
    syncNow,
    destroy,
    configureHandlers
  };
}

export const rootPollingController = createPollingController();
export const uiPollingStatus = rootPollingController.status;

export const battlePollingController = createBattlePollingController();
export const mapPollingController = createMapPollingController();

export function configureBattlePollingHandlers(handlers) {
  battlePollingController.configureHandlers(handlers);
}

export function configureMapPollingHandlers(handlers) {
  mapPollingController.configureHandlers(handlers);
}

export function startUIPolling() {
  rootPollingController.start();
}

export function stopUIPolling() {
  rootPollingController.stop();
}

export function syncUIPolling() {
  rootPollingController.syncNow();
}

export function syncBattlePolling() {
  battlePollingController.syncNow();
}

export function syncMapPolling() {
  mapPollingController.syncNow();
}
