// UI-centric API for communicating with backend
// Replaces the run-specific API with a simpler state-based approach

import { openOverlay } from './OverlayController.js';
import { httpGet, httpPost } from './httpClient.js';

const RUN_CONFIG_STORAGE_KEY = 'run_config_metadata_v1';

let cachedRunConfiguration = null;
let cachedRunConfigurationHash = null;
let runConfigurationPromise = null;

/**
 * Get the complete UI state from the backend.
 * Returns the current UI mode, game state, and available actions.
 */
export async function getUIState() {
  try {
    return await httpGet('/ui');
  } catch (e) {
    // Add context for UI state errors
    if (!e.overlayShown) {
      const message = e.message || 'Failed to get UI state';
      openOverlay('error', { message, traceback: e?.stack || '' });
      console.error('getUIState failure:', { message });
    }
    throw e;
  }
}

/**
 * Send an action to the backend.
 * @param {string} action - The action to perform
 * @param {object} params - Action-specific parameters
 */
export async function sendAction(action, params = {}, { suppressOverlay = false } = {}) {
  try {
    return await httpPost('/ui/action', { action, params }, {}, suppressOverlay);
  } catch (e) {
    // Add context for action errors
    if (!suppressOverlay && !e.overlayShown) {
      const message = e.message || `Failed to execute action: ${action}`;
      openOverlay('error', { message, traceback: e?.stack || '' });
      console.error('sendAction failure:', { action, params, message });
    }
    throw e;
  }
}

/**
 * Start a new run with the specified party.
 * @param {Array} party - List of party member IDs
 * @param {string} damageType - Damage type for the player
 * @param {number} pressure - Pressure setting
 */
export async function startRun(options) {
  const payload = normalizeStartRunPayload(options);
  return await sendAction('start_run', payload);
}

function normalizeStartRunPayload(options) {
  if (Array.isArray(options)) {
    return {
      party: options || ['player'],
      damage_type: '',
      pressure: 0,
      metadata_version: null
    };
  }

  if (options && typeof options === 'object') {
    const {
      party,
      damageType = '',
      pressure = 0,
      runType = null,
      modifiers = null,
      metadataVersion = null
    } = options;
    const normalizedParty = Array.isArray(party) && party.length > 0 ? party : ['player'];
    const normalizedModifiers = normalizeModifiers(modifiers);
    const normalizedPressure = Number.isFinite(Number(pressure)) ? Number(pressure) : 0;
    const normalizedMetadataVersion = metadataVersion ?? null;
    return {
      party: normalizedParty,
      damage_type: damageType,
      pressure: normalizedPressure,
      run_type: runType || undefined,
      modifiers: normalizedModifiers,
      metadata_version: normalizedMetadataVersion
    };
  }

  return {
    party: ['player'],
    damage_type: '',
    pressure: 0,
    metadata_version: null
  };
}

function normalizeModifiers(modifiers) {
  if (!modifiers || typeof modifiers !== 'object') {
    return undefined;
  }

  const normalized = {};
  for (const [key, value] of Object.entries(modifiers)) {
    const numeric = Number(value);
    normalized[key] = Number.isFinite(numeric) ? numeric : value;
  }
  return normalized;
}

function getSessionStorage() {
  if (typeof window === 'undefined') {
    return null;
  }
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

function deriveMetadataHash(payload) {
  if (!payload || typeof payload !== 'object') {
    return null;
  }
  if (typeof payload.metadata_hash === 'string' && payload.metadata_hash.trim()) {
    return payload.metadata_hash.trim();
  }
  if (typeof payload.version === 'string' && payload.version.trim()) {
    return payload.version.trim();
  }
  return null;
}

function cloneMetadataPayload(payload) {
  if (!payload || typeof payload !== 'object') {
    return payload ?? null;
  }
  if (typeof structuredClone === 'function') {
    try {
      return structuredClone(payload);
    } catch {}
  }
  try {
    return JSON.parse(JSON.stringify(payload));
  } catch {
    return payload;
  }
}

function loadCachedRunConfiguration() {
  if (cachedRunConfiguration) {
    return;
  }
  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  try {
    const raw = storage.getItem(RUN_CONFIG_STORAGE_KEY);
    if (!raw) {
      return;
    }
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') {
      const payloadSource = parsed.payload && typeof parsed.payload === 'object' ? parsed.payload : parsed;
      const cloned = cloneMetadataPayload(payloadSource);
      cachedRunConfiguration = cloned;
      cachedRunConfigurationHash = parsed.hash || deriveMetadataHash(cloned);
    }
  } catch (err) {
    console.warn('Failed to load cached run configuration metadata', err);
    cachedRunConfiguration = null;
    cachedRunConfigurationHash = null;
  }
}

function persistRunConfigurationCache(payload) {
  const cloned = cloneMetadataPayload(payload);
  cachedRunConfiguration = cloned || null;
  cachedRunConfigurationHash = deriveMetadataHash(cloned);

  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  try {
    const serialized = JSON.stringify({
      hash: cachedRunConfigurationHash,
      payload: cloned,
      savedAt: Date.now()
    });
    storage.setItem(RUN_CONFIG_STORAGE_KEY, serialized);
  } catch (err) {
    console.warn('Failed to persist run configuration metadata cache', err);
  }
}

export function resetRunConfigurationMetadataCache() {
  cachedRunConfiguration = null;
  cachedRunConfigurationHash = null;
  if (runConfigurationPromise) {
    runConfigurationPromise = null;
  }
  const storage = getSessionStorage();
  if (storage) {
    try {
      storage.removeItem(RUN_CONFIG_STORAGE_KEY);
    } catch {}
  }
}

export async function getRunConfigurationMetadata({
  suppressOverlay = false,
  forceRefresh = false,
  metadataHash = null
} = {}) {
  loadCachedRunConfiguration();

  if (
    !forceRefresh &&
    cachedRunConfiguration &&
    (!metadataHash || !cachedRunConfigurationHash || metadataHash === cachedRunConfigurationHash)
  ) {
    return cachedRunConfiguration;
  }

  if (!forceRefresh && runConfigurationPromise) {
    return runConfigurationPromise;
  }

  runConfigurationPromise = httpGet('/run/config', {}, suppressOverlay)
    .then((payload) => {
      persistRunConfigurationCache(payload);
      return cachedRunConfiguration;
    })
    .catch((error) => {
      runConfigurationPromise = null;
      throw error;
    })
    .finally(() => {
      runConfigurationPromise = null;
    });

  return runConfigurationPromise;
}

export async function logMenuAction(menu, event, data = {}) {
  if (!event) return;
  const params = {
    menu: menu || 'Run',
    event,
    details: data
  };
  try {
    await sendAction('log_menu_action', params, { suppressOverlay: true });
  } catch (err) {
    // Logging should never interrupt the user flow; swallow errors silently.
    if (typeof console !== 'undefined') {
      console.warn('logMenuAction failed', err);
    }
  }
}

/**
 * Perform a room action.
 * @param {string} roomId - The room ID (typically "0" for current room)
 * @param {object|string} actionData - Action-specific data
 */
export async function roomAction(roomId = '0', actionData = {}) {
  const params = { room_id: roomId };
  if (actionData && typeof actionData === 'object') {
    Object.assign(params, actionData);
  } else if (actionData) {
    params.action = actionData;
  }
  return await sendAction('room_action', params);
}

/**
 * Advance to the next room.
 */
export async function advanceRoom() {
  const state = await getUIState();
  const gs = state?.game_state || {};
  const cs = gs?.current_state || {};
  if (cs.awaiting_card || cs.awaiting_relic || cs.awaiting_loot) {
    const message = 'Cannot advance room until all rewards are collected.';
    openOverlay('error', { message, traceback: '' });
    const err = new Error(message);
    err.status = 400;
    err.overlayShown = true;
    throw err;
  }
  return await sendAction('advance_room');
}

/**
 * Choose a card reward.
 * @param {string} cardId - The card ID to choose
 */
export async function chooseCard(cardId) {
  return await sendAction('choose_card', { card_id: cardId });
}

/**
 * Choose a relic reward.
 * @param {string} relicId - The relic ID to choose
 */
export async function chooseRelic(relicId) {
  return await sendAction('choose_relic', { relic_id: relicId });
}

/**
 * Acknowledge and collect room loot.
 * @param {string} runId - The current run identifier
 */
export async function acknowledgeLoot(runId) {
  return httpPost(`/rewards/loot/${runId}`);
}

/**
 * Fetch the player's daily login reward status.
 * @param {Object} [options]
 * @param {boolean} [options.suppressOverlay=true] - Skip the global error overlay on failure.
 */
export async function getLoginRewardStatus({ suppressOverlay = true } = {}) {
  return httpGet('/rewards/login', {}, suppressOverlay);
}

/**
 * Claim the available daily login reward bundle.
 * @param {boolean} [suppressOverlay=true] - Skip the global error overlay on failure.
 */
export async function claimLoginReward(suppressOverlay = true) {
  return httpPost('/rewards/login/claim', {}, {}, suppressOverlay);
}

/**
 * Retrieve a battle summary for the current run.
 * @param {number} battleIndex - Index of the battle to fetch
 */
export async function getBattleSummary(battleIndex, runId = '') {
  const index = Number(battleIndex);
  if (!Number.isFinite(index) || index <= 0) {
    throw new Error('Invalid battle index');
  }
  const base = runId ? `/logs/${encodeURIComponent(runId)}` : '';
  const path = `${base}/battles/${Math.floor(index)}/summary`;
  return httpGet(path, { cache: 'no-store' });
}

/**
 * Retrieve detailed battle events for the current run.
 * @param {number} battleIndex - Index of the battle to fetch
 */
export async function getBattleEvents(battleIndex, runId = '') {
  const index = Number(battleIndex);
  if (!Number.isFinite(index) || index <= 0) {
    throw new Error('Invalid battle index');
  }
  const base = runId ? `/logs/${encodeURIComponent(runId)}` : '';
  const path = `${base}/battles/${Math.floor(index)}/events`;
  return httpGet(path, { cache: 'no-store' });
}

/**
 * Fetch the list of tracked runs available for review.
 * @param {AbortSignal} [signal] optional abort controller signal
 */
export async function listTrackedRuns({ signal } = {}) {
  const opts = signal ? { signal } : {};
  const payload = await httpGet('/tracking/runs', opts, true);
  const rawRuns = Array.isArray(payload)
    ? payload
    : Array.isArray(payload?.runs)
      ? payload.runs
      : [];
  const runs = rawRuns.map(normalizeRunSummary);
  return { runs };
}

/**
 * Fetch details for a tracked run including battle summaries.
 * @param {string} runId
 * @param {AbortSignal} [signal]
 */
export async function getTrackedRun(runId, { signal } = {}) {
  if (!runId) {
    throw new Error('Run id is required');
  }
  const opts = signal ? { signal } : {};
  const payload = await httpGet(`/tracking/runs/${encodeURIComponent(runId)}`, opts, true);
  if (!payload || typeof payload !== 'object') {
    return payload;
  }

  const result = { ...payload };
  if (result.run && typeof result.run === 'object') {
    result.run = normalizeRunSummary(result.run);
    if (!result.configuration && result.run?.configuration) {
      result.configuration = result.run.configuration;
    }
  } else if (!result.run) {
    const configuration = normalizeRunConfiguration(result);
    if (configuration) {
      result.configuration = configuration;
    }
  }

  return result;
}

/**
 * Group ordered battle summaries by floor, incrementing the floor when the
 * room index resets.
 *
 * @param {Array<Record<string, any>>} summaries
 * @returns {Array<{ floor: number, label: string, fights: Array<{ battleIndex: number, label: string, summary: Record<string, any> }> }>}
 */
export function groupBattleSummariesByFloor(summaries = []) {
  if (!Array.isArray(summaries) || summaries.length === 0) {
    return [];
  }

  const floors = [];
  let currentFloor = 1;
  let currentGroup = { floor: currentFloor, fights: [] };
  let lastRoomIndex = null;

  const coerceIndex = (value) => {
    if (value === undefined || value === null) return null;
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
  };

  const ensureGroupPushed = () => {
    if (currentGroup.fights.length > 0) {
      floors.push(currentGroup);
    }
  };

  const deriveBattleIndex = (entry, fallback) => {
    const candidates = [
      entry?.battle_index,
      entry?.battleIndex,
      entry?.index,
      entry?.battle?.index,
      entry?.id
    ];
    for (const candidate of candidates) {
      const n = Number(candidate);
      if (Number.isFinite(n) && n > 0) {
        return Math.floor(n);
      }
    }
    return fallback;
  };

  const deriveFightLabel = (entry, fallbackIndex) => {
    const candidates = [
      entry?.battle_name,
      entry?.battleName,
      entry?.room_name,
      entry?.roomName,
      entry?.room_type,
      entry?.roomType
    ];
    for (const candidate of candidates) {
      if (candidate) {
        return String(candidate);
      }
    }
    return `Fight ${fallbackIndex}`;
  };

  summaries.forEach((entry, idx) => {
    const roomIndex = coerceIndex(entry?.room_index ?? entry?.roomIndex);
    const battleIndex = deriveBattleIndex(entry, idx + 1);

    if (
      lastRoomIndex !== null &&
      roomIndex !== null &&
      roomIndex < lastRoomIndex
    ) {
      ensureGroupPushed();
      currentFloor += 1;
      currentGroup = { floor: currentFloor, fights: [] };
    }

    const label = deriveFightLabel(entry, battleIndex || idx + 1);
    currentGroup.fights.push({ battleIndex, label, summary: entry });

    if (roomIndex !== null) {
      lastRoomIndex = roomIndex;
    }
  });

  ensureGroupPushed();

  return floors.map((floorGroup) => ({
    floor: floorGroup.floor,
    label: `Floor ${floorGroup.floor}`,
    fights: floorGroup.fights.map((fight, fightIdx) => ({
      battleIndex: fight.battleIndex || fightIdx + 1,
      label: fight.label || `Fight ${fightIdx + 1}`,
      summary: fight.summary
    }))
  }));
}

function normalizeRunSummary(run) {
  if (!run || typeof run !== 'object') {
    return run ?? {};
  }
  const normalized = { ...run };
  const configuration = normalizeRunConfiguration(run);
  if (configuration) {
    normalized.configuration = configuration;
  } else {
    delete normalized.configuration;
  }
  return normalized;
}

function normalizeRunConfiguration(source) {
  if (!source || typeof source !== 'object') {
    return null;
  }

  const baseConfiguration = isPlainObject(source.configuration) ? source.configuration : {};

  const runType =
    baseConfiguration.run_type ??
    baseConfiguration.runType ??
    source.run_type ??
    source.runType ??
    null;

  const modifiers = coerceConfigurationValue(
    baseConfiguration.modifiers,
    baseConfiguration.modifiers_json,
    baseConfiguration.modifiersJson,
    source.modifiers,
    source.modifiers_json,
    source.modifiersJson
  );

  const rewardBonuses = coerceConfigurationValue(
    baseConfiguration.reward_bonuses,
    baseConfiguration.rewardBonuses,
    baseConfiguration.reward_json,
    baseConfiguration.rewardJson,
    source.reward_bonuses,
    source.rewardBonuses,
    source.reward_json,
    source.rewardJson
  );

  if (runType == null && modifiers == null && rewardBonuses == null) {
    return null;
  }

  return {
    runType: runType ?? null,
    run_type: runType ?? null,
    modifiers: modifiers ?? {},
    rewardBonuses: rewardBonuses ?? {},
    reward_bonuses: rewardBonuses ?? {},
  };
}

function coerceConfigurationValue(...candidates) {
  for (const candidate of candidates) {
    if (candidate === undefined || candidate === null) {
      continue;
    }
    const parsed = parseMaybeJSON(candidate);
    if (parsed === undefined || parsed === null) {
      continue;
    }
    if (isPlainObject(parsed) || Array.isArray(parsed)) {
      return parsed;
    }
    if (typeof parsed === 'string' && parsed.trim() === '') {
      continue;
    }
    return parsed;
  }
  return null;
}

function parseMaybeJSON(value) {
  if (typeof value !== 'string') {
    return value;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return value;
  }
  try {
    return JSON.parse(trimmed);
  } catch {
    return value;
  }
}

function isPlainObject(value) {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

/**
 * Fetch catalog data for relics, cards, DoTs, and HoTs.
 */
export async function getCatalogData() {
  const [relics, cards, dots, hots] = await Promise.all([
    httpGet('/catalog/relics'),
    httpGet('/catalog/cards'),
    httpGet('/catalog/dots'),
    httpGet('/catalog/hots'),
  ]);

  return {
    relics: relics.relics || [],
    cards: cards.cards || [],
    dots: dots.dots || [],
    hots: hots.hots || [],
  };
}

// For backward compatibility with existing code, we can provide fallback functions
// that use the old API format but internally use the new UI API

/**
 * @deprecated Use getUIState() instead
 */
export async function getMap(_runId) {
  const uiState = await getUIState();
  if (uiState.mode === 'menu') {
    return null; // Simulate run not found
  }
  return uiState.game_state;
}

/**
 * @deprecated Use getUIState() instead  
 */
export async function getActiveRuns() {
  const uiState = await getUIState();
  if (uiState.active_run) {
    return {
      runs: [{
        run_id: uiState.active_run,
        party: uiState.game_state?.party || [],
        map: uiState.game_state?.map || {}
      }]
    };
  }
  return { runs: [] };
}

/**
 * Update the current party selection on the backend.
 * @param {Array} party - List of party member IDs
 */
export async function updateParty(party) {
  return await sendAction('update_party', { party });
}
