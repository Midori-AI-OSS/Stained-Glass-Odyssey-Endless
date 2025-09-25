// UI-centric API for communicating with backend
// Replaces the run-specific API with a simpler state-based approach

import { openOverlay } from './OverlayController.js';
import { httpGet, httpPost } from './httpClient.js';

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
export async function sendAction(action, params = {}) {
  try {
    return await httpPost('/ui/action', { action, params });
  } catch (e) {
    // Add context for action errors
    if (!e.overlayShown) {
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
export async function startRun(party, damageType = '', pressure = 0) {
  return await sendAction('start_run', { 
    party: party || ['player'], 
    damage_type: damageType, 
    pressure 
  });
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
  const base = runId ? `/runs/${encodeURIComponent(runId)}` : '';
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
  const base = runId ? `/runs/${encodeURIComponent(runId)}` : '';
  const path = `${base}/battles/${Math.floor(index)}/events`;
  return httpGet(path, { cache: 'no-store' });
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
