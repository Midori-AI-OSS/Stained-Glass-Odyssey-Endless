import { derived, get, writable } from 'svelte/store';
import { runStateStore } from './runState.js';

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
}

export function setBattleActive(active) {
  runStateStore.setBattleActive(active);
}
