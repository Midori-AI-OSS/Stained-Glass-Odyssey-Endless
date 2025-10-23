import { derived, get, writable } from 'svelte/store';
import { runStateStore } from './runState.js';
import { createRewardPhaseController } from './rewardProgression.js';

const defaultState = Object.freeze({
  rewardOpen: false,
  reviewOpen: false,
  reviewReady: false,
  manualHalt: false
});

function normalizeBoolean(value) {
  return value === true || value === 'true' || value === 1 || value === '1';
}

export function createOverlayStateStore() {
  const { subscribe, set, update } = writable({ ...defaultState });

  function setState(partial) {
    update((state) => ({ ...state, ...(partial || {}) }));
  }

  return {
    subscribe,
    getSnapshot() {
      return get({ subscribe });
    },
    setRewardOpen(open) {
      setState({ rewardOpen: Boolean(open) });
    },
    setReviewOpen(open) {
      setState({ reviewOpen: Boolean(open) });
    },
    setReviewReady(ready) {
      setState({ reviewReady: Boolean(ready) });
    },
    setManualHalt(halt) {
      setState({ manualHalt: Boolean(halt) });
    },
    reset() {
      set({ ...defaultState });
    }
  };
}

export const overlayStateStore = createOverlayStateStore();
export const overlayState = overlayStateStore;

const rewardPhaseMachine = createRewardPhaseController();
export const rewardPhaseController = rewardPhaseMachine;
export const rewardPhaseState = rewardPhaseMachine;

export const overlayBlocking = derived(overlayStateStore, ($state) => {
  return Boolean($state.rewardOpen || ($state.reviewOpen && $state.reviewReady));
});

export const haltSync = derived(
  [overlayStateStore, overlayBlocking],
  ([$state, blocking]) => Boolean($state.manualHalt || blocking)
);

export const battleActive = derived(runStateStore, ($state) => Boolean($state.battleActive));

export function setRewardOverlayOpen(open) {
  overlayStateStore.setRewardOpen(open);
}

export function setReviewOverlayState({ open, ready }) {
  if (open !== undefined) {
    overlayStateStore.setReviewOpen(normalizeBoolean(open));
  }
  if (ready !== undefined) {
    overlayStateStore.setReviewReady(normalizeBoolean(ready));
  }
}

export function setManualSyncHalt(halt) {
  overlayStateStore.setManualHalt(halt);
}

export function resetOverlayState() {
  overlayStateStore.reset();
  rewardPhaseMachine.reset();
}

export function setBattleActive(active) {
  runStateStore.setBattleActive(active);
}

export function updateRewardProgression(payload, options = {}) {
  return rewardPhaseMachine.ingest(payload, options);
}

export function advanceRewardPhase() {
  return rewardPhaseMachine.advance();
}

export function skipToRewardPhase(phase) {
  return rewardPhaseMachine.skipTo(phase);
}

export function resetRewardProgression() {
  return rewardPhaseMachine.reset();
}
