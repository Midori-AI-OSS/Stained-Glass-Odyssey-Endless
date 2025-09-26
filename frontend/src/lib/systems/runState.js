import { get, writable } from 'svelte/store';

const STORAGE_KEY = 'runState';

/**
 * @typedef {object} RunState
 * @property {string} runId
 * @property {string[]} selectedParty
 * @property {Array<Record<string, unknown>>} mapRooms
 * @property {number} currentIndex
 * @property {string} currentRoomType
 * @property {string} nextRoom
 * @property {Record<string, unknown> | null} roomData
 * @property {boolean} battleActive
 * @property {Record<string, unknown> | null} lastBattleSnapshot
 */

const defaultState = Object.freeze({
  runId: '',
  selectedParty: ['sample_player'],
  mapRooms: [],
  currentIndex: 0,
  currentRoomType: '',
  nextRoom: '',
  roomData: null,
  battleActive: false,
  lastBattleSnapshot: null
});

function resolveStorage(candidate) {
  if (!candidate) return null;
  if (typeof candidate.getItem !== 'function') return null;
  if (typeof candidate.setItem !== 'function') return null;
  if (typeof candidate.removeItem !== 'function') return null;
  return candidate;
}

function getBrowserStorage() {
  try {
    if (typeof window !== 'undefined' && window?.localStorage) {
      return resolveStorage(window.localStorage);
    }
  } catch {}
  return null;
}

export function normalizePartyIds(party) {
  if (!Array.isArray(party)) return defaultState.selectedParty;
  const seen = new Set();
  const normalized = [];
  for (const entry of party) {
    const id = typeof entry === 'string' ? entry : entry?.id || entry?.name;
    if (!id) continue;
    const key = String(id);
    if (seen.has(key)) continue;
    seen.add(key);
    normalized.push(key);
  }
  return normalized.length ? normalized : defaultState.selectedParty;
}

function normalizeRooms(rooms) {
  if (!Array.isArray(rooms)) return [];
  return rooms.map((room) => (room && typeof room === 'object' ? { ...room } : room));
}

export function createRunStateStore(storageCandidate) {
  const storage = resolveStorage(storageCandidate) || getBrowserStorage();
  const { subscribe, set, update } = writable({ ...defaultState });

  function coerceRunId(value) {
    return value ? String(value) : '';
  }

  function persist(runId) {
    if (!storage) return;
    const id = coerceRunId(runId);
    if (!id) {
      try {
        storage.removeItem(STORAGE_KEY);
      } catch {}
      return;
    }
    try {
      storage.setItem(STORAGE_KEY, JSON.stringify({ runId: id }));
    } catch {}
  }

  function setState(partial) {
    update((state) => {
      const next = { ...state };
      for (const [key, value] of Object.entries(partial || {})) {
        if (value !== undefined) {
          next[key] = value;
        }
      }
      return next;
    });
  }

  return {
    subscribe,
    /**
     * Read the current run state snapshot synchronously.
     * @returns {RunState}
     */
    getSnapshot() {
      return get({ subscribe });
    },
    /**
     * Apply a UI state payload from the backend to the run store.
     * @param {Record<string, unknown> | null | undefined} payload
     * @returns {{ mode: string; runId: string; battleActive: boolean }}
     */
    applyUIState(payload) {
      const mode = payload?.mode ? String(payload.mode) : 'unknown';
      if (!payload || mode === 'menu') {
        set({ ...defaultState });
        persist('');
        return { mode, runId: '', battleActive: false };
      }

      const updates = {};
      const runId = coerceRunId(payload?.active_run);
      if (runId) {
        updates.runId = runId;
      }

      const gameState = payload?.game_state || {};

      if (gameState?.party) {
        updates.selectedParty = normalizePartyIds(gameState.party);
      }

      if (gameState?.map?.rooms) {
        updates.mapRooms = normalizeRooms(gameState.map.rooms);
      }

      const currentState = gameState?.current_state || {};
      if (Number.isFinite(currentState?.current_index)) {
        updates.currentIndex = Number(currentState.current_index) || 0;
      }
      if (typeof currentState?.current_room_type === 'string') {
        updates.currentRoomType = currentState.current_room_type;
      }
      if (typeof currentState?.next_room_type === 'string') {
        updates.nextRoom = currentState.next_room_type;
      }

      if (currentState?.room_data) {
        updates.roomData = { ...currentState.room_data };
        if (mode === 'battle' && !currentState.room_data?.snapshot_missing) {
          updates.lastBattleSnapshot = { ...currentState.room_data };
        }
      } else {
        updates.roomData = null;
      }

      const inBattle = mode === 'battle';
      updates.battleActive = inBattle;

      setState(updates);
      persist(runId);

      return {
        mode,
        runId,
        battleActive: inBattle
      };
    },
    /**
     * Update the stored run identifier and persist it.
     * @param {string} runId
     */
    setRunId(runId) {
      const id = runId ? String(runId) : '';
      setState({ runId: id });
      persist(id);
    },
    /**
     * Replace the selected party roster.
     * @param {string[] | Array<{ id?: string; name?: string }>} party
     */
    setParty(party) {
      const normalized = normalizePartyIds(party);
      setState({ selectedParty: normalized });
    },
    /**
     * Update map metadata for the current run.
     * @param {Array<Record<string, unknown>>} rooms
     */
    setMapRooms(rooms) {
      setState({ mapRooms: normalizeRooms(rooms) });
    },
    /**
     * Update current/next room indices and labels.
     * @param {{ index?: number; currentRoomType?: string; nextRoomType?: string }} payload
     */
    setCurrentRoom(payload = {}) {
      const { index, currentRoomType, nextRoomType } = payload;
      setState({
        currentIndex: Number.isFinite(index) ? Number(index) : undefined,
        currentRoomType: typeof currentRoomType === 'string' ? currentRoomType : undefined,
        nextRoom: typeof nextRoomType === 'string' ? nextRoomType : undefined
      });
    },
    /**
     * Replace the active room payload.
     * @param {Record<string, unknown> | null} roomData
     */
    setRoomData(roomData) {
      setState({ roomData: roomData ?? null });
    },
    /**
     * Flag the run as currently being in battle.
     * @param {boolean} active
     */
    setBattleActive(active) {
      setState({ battleActive: Boolean(active) });
    },
    /**
     * Cache the latest battle snapshot for review overlays.
     * @param {Record<string, unknown> | null} snapshot
     */
    setLastBattleSnapshot(snapshot) {
      setState({ lastBattleSnapshot: snapshot ?? null });
    },
    /**
     * Reset all run-specific fields to their defaults without touching persistence.
     */
    reset() {
      set({ ...defaultState });
    },
    /**
     * Attempt to restore the persisted run identifier and update the store.
     * @returns {{ runId: string } | null}
     */
    restoreFromStorage() {
      if (!storage) return null;
      try {
        const raw = storage.getItem(STORAGE_KEY);
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        const id = parsed?.runId ? String(parsed.runId) : '';
        if (!id) return null;
        setState({ runId: id });
        return { runId: id };
      } catch {
        return null;
      }
    },
    /**
     * Persist the provided run id without mutating in-memory state.
     * @param {string} runId
     */
    persistRunId(runId) {
      persist(runId);
    },
    /**
     * Remove any stored run identifier and reset in-memory state.
     */
    clear() {
      if (storage) {
        try {
          storage.removeItem(STORAGE_KEY);
        } catch {}
      }
    }
  };
}

export const runStateStore = createRunStateStore();

export const runState = runStateStore;

export function loadRunState() {
  return runStateStore.restoreFromStorage();
}

export function saveRunState(runId) {
  if (runId) {
    runStateStore.persistRunId(runId);
  }
}

export function clearRunState() {
  runStateStore.clear();
}
