import { afterEach, beforeEach, describe, expect, test } from 'bun:test';
import { writable } from 'svelte/store';
import {
  createPollingController,
  createBattlePollingController,
  createMapPollingController,
  rootPollingController
} from '../src/lib/systems/pollingOrchestrator.js';
import { createRunStateStore, runStateStore } from '../src/lib/systems/runState.js';

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

describe('polling orchestrator', () => {
  beforeEach(() => {
    runStateStore.reset();
  });

  afterEach(() => {
    rootPollingController.stop();
  });

  test('polls UI state when not halted and not blocked', async () => {
    const halt = writable(false);
    const overlay = writable(false);
    const payloads = [];

    const controller = createPollingController({
      getUIStateFn: async () => ({ mode: 'menu' }),
      haltStore: { subscribe: halt.subscribe },
      overlayStore: { subscribe: overlay.subscribe },
      getOverlayView: () => 'main',
      successDelayMs: 5,
      retryBaseDelayMs: 5,
      maxRetryDelayMs: 20
    });

    const unsubscribe = controller.onUIState((payload) => {
      payloads.push(payload);
    });

    controller.start();
    await delay(25);
    controller.stop();

    expect(payloads.length).toBeGreaterThanOrEqual(1);
    expect(payloads[0]).toEqual({ mode: 'menu' });

    unsubscribe();
  });

  test('stopping controller prevents rescheduling after in-flight request', async () => {
    const halt = writable(false);
    const overlay = writable(false);
    let resolveRequest;
    let calls = 0;

    const controller = createPollingController({
      getUIStateFn: () => {
        calls += 1;
        return new Promise((resolve) => {
          resolveRequest = () => resolve({ mode: 'menu' });
        });
      },
      haltStore: { subscribe: halt.subscribe },
      overlayStore: { subscribe: overlay.subscribe },
      getOverlayView: () => 'main',
      successDelayMs: 5,
      retryBaseDelayMs: 5,
      maxRetryDelayMs: 20
    });

    controller.start();
    await delay(5);
    controller.stop();

    expect(typeof resolveRequest).toBe('function');
    resolveRequest();
    await delay(20);

    expect(calls).toBe(1);
  });

  test('pauses polling while halt or overlay blocking is active', async () => {
    const halt = writable(true);
    const overlay = writable(false);
    let calls = 0;

    const controller = createPollingController({
      getUIStateFn: async () => {
        calls += 1;
        return { mode: 'menu' };
      },
      haltStore: { subscribe: halt.subscribe },
      overlayStore: { subscribe: overlay.subscribe },
      getOverlayView: () => 'main',
      successDelayMs: 5,
      retryBaseDelayMs: 5,
      maxRetryDelayMs: 20
    });

    controller.start();
    await delay(20);
    expect(calls).toBe(0);

    halt.set(false);
    await delay(20);
    expect(calls).toBeGreaterThanOrEqual(1);

    overlay.set(true);
    const previousCalls = calls;
    await delay(20);
    expect(calls).toBe(previousCalls);

    controller.stop();
  });

  test('tracks consecutive failures with exponential backoff', async () => {
    const halt = writable(false);
    const overlay = writable(false);
    let attempt = 0;
    const statusUpdates = [];

    const controller = createPollingController({
      getUIStateFn: async () => {
        attempt += 1;
        if (attempt < 3) {
          throw new Error('network');
        }
        return { mode: 'menu' };
      },
      haltStore: { subscribe: halt.subscribe },
      overlayStore: { subscribe: overlay.subscribe },
      getOverlayView: () => 'main',
      successDelayMs: 5,
      retryBaseDelayMs: 5,
      maxRetryDelayMs: 40
    });

    const unsubscribe = controller.status.subscribe((value) => {
      statusUpdates.push(value);
    });

    controller.start();
    await delay(80);
    controller.stop();

    const finalStatus = statusUpdates.at(-1);
    expect(attempt).toBeGreaterThanOrEqual(3);
    expect(finalStatus?.consecutiveFailures).toBe(0);
    expect(finalStatus?.lastError).toBeNull();

    unsubscribe();
  });

  test('battle polling controller reacts to store state', async () => {
    const halt = writable(false);
    const overlay = writable(false);
    const store = createRunStateStore();
    const snapshots = [];

    const controller = createBattlePollingController({
      runStore: store,
      haltStore: { subscribe: halt.subscribe },
      overlayStore: { subscribe: overlay.subscribe },
      getOverlayView: () => 'main',
      fetchSnapshot: async () => ({ next_room: 'event', awaiting_next: true }),
      getDelayMs: () => 0,
      handlers: {
        onBattleComplete: ({ snapshot }) => snapshots.push(snapshot),
        onBattleSettled: () => {}
      }
    });

    store.setRunId('battle-001');
    store.setBattleActive(true);
    await delay(20);

    expect(snapshots).toHaveLength(1);
    expect(store.getSnapshot().battleActive).toBe(false);

    controller.destroy();
  });

  test('map polling controller hydrates map metadata', async () => {
    const halt = writable(false);
    const overlay = writable(false);
    const store = createRunStateStore();
    const maps = [];

    const controller = createMapPollingController({
      runStore: store,
      haltStore: { subscribe: halt.subscribe },
      overlayStore: { subscribe: overlay.subscribe },
      getOverlayView: () => 'main',
      intervalMs: 0,
      getMapFn: async () => ({
        party: ['alpha'],
        map: { rooms: [{ room_type: 'start' }] },
        current_state: { current_index: 0, current_room_type: 'start' }
      }),
      handlers: {
        onUpdate: ({ data }) => maps.push(data)
      }
    });

    store.setRunId('map-001');
    store.setBattleActive(false);
    await delay(20);

    expect(maps.length).toBeGreaterThanOrEqual(1);
    expect(store.getSnapshot().mapRooms).toEqual([{ room_type: 'start' }]);
    expect(store.getSnapshot().currentIndex).toBe(0);

    controller.destroy();
  });
});
