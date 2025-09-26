import { beforeEach, describe, expect, test } from 'bun:test';
import { get } from 'svelte/store';
import {
  overlayStateStore,
  overlayBlocking,
  haltSync,
  battleActive,
  setRewardOverlayOpen,
  setReviewOverlayState,
  setManualSyncHalt,
  resetOverlayState,
  setBattleActive
} from '../src/lib/systems/overlayState.js';
import { runStateStore } from '../src/lib/systems/runState.js';

describe('overlay state gating helpers', () => {
  beforeEach(() => {
    resetOverlayState();
    runStateStore.reset();
  });

  test('reward overlay toggles blocking state', () => {
    expect(get(overlayBlocking)).toBe(false);
    setRewardOverlayOpen(true);
    expect(get(overlayBlocking)).toBe(true);
    setRewardOverlayOpen(false);
    expect(get(overlayBlocking)).toBe(false);
  });

  test('review overlay blocks when ready', () => {
    setReviewOverlayState({ open: true, ready: false });
    expect(get(overlayBlocking)).toBe(false);
    setReviewOverlayState({ ready: true });
    expect(get(overlayBlocking)).toBe(true);
    setReviewOverlayState({ open: false });
    expect(get(overlayBlocking)).toBe(false);
  });

  test('manual halt participates in haltSync derived value', () => {
    expect(get(haltSync)).toBe(false);
    setManualSyncHalt(true);
    expect(get(haltSync)).toBe(true);
    setManualSyncHalt(false);
    expect(get(haltSync)).toBe(false);
  });

  test('battleActive proxies the run state store', () => {
    expect(get(battleActive)).toBe(false);
    setBattleActive(true);
    expect(runStateStore.getSnapshot().battleActive).toBe(true);
    expect(get(battleActive)).toBe(true);
    setBattleActive(false);
    expect(get(battleActive)).toBe(false);
  });

  test('resetOverlayState clears all overlay flags', () => {
    setRewardOverlayOpen(true);
    setReviewOverlayState({ open: true, ready: true });
    setManualSyncHalt(true);
    resetOverlayState();
    expect(overlayStateStore.getSnapshot()).toEqual({
      rewardOpen: false,
      reviewOpen: false,
      reviewReady: false,
      manualHalt: false
    });
    expect(get(overlayBlocking)).toBe(false);
    expect(get(haltSync)).toBe(false);
  });
});
