import { describe, expect, test } from 'bun:test';
import { createRunStateStore } from '../src/lib/systems/runState.js';

function createMemoryStorage(initial = {}) {
  let store = { ...initial };
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(store, key) ? store[key] : null;
    },
    setItem(key, value) {
      store[key] = String(value);
    },
    removeItem(key) {
      delete store[key];
    },
    snapshot() {
      return { ...store };
    }
  };
}

describe('run state store', () => {
  test('persists and restores run identifiers', () => {
    const storage = createMemoryStorage();
    const store = createRunStateStore(storage);

    store.setRunId('run-001');
    expect(store.getSnapshot().runId).toBe('run-001');
    expect(storage.snapshot().runState).toBe('{"runId":"run-001"}');

    const fresh = createRunStateStore(storage);
    const restored = fresh.restoreFromStorage();
    expect(restored).toEqual({ runId: 'run-001' });
    expect(fresh.getSnapshot().runId).toBe('run-001');
  });

  test('normalizes party identifiers and map metadata', () => {
    const store = createRunStateStore(createMemoryStorage());
    store.setParty([{ id: 'alpha' }, { name: 'beta' }, 'alpha']);
    expect(store.getSnapshot().selectedParty).toEqual(['alpha', 'beta']);

    store.setMapRooms([{ room_type: 'event' }]);
    expect(store.getSnapshot().mapRooms).toEqual([{ room_type: 'event' }]);

    store.setCurrentRoom({ index: 2, currentRoomType: 'battle', nextRoomType: 'boss' });
    const snapshot = store.getSnapshot();
    expect(snapshot.currentIndex).toBe(2);
    expect(snapshot.currentRoomType).toBe('battle');
    expect(snapshot.nextRoom).toBe('boss');
  });

  test('tracks room data, battle flags, and snapshots', () => {
    const store = createRunStateStore(createMemoryStorage());
    store.setRoomData({ result: 'battle' });
    store.setBattleActive(true);
    store.setLastBattleSnapshot({ foes: [] });

    const snapshot = store.getSnapshot();
    expect(snapshot.roomData).toEqual({ result: 'battle' });
    expect(snapshot.battleActive).toBe(true);
    expect(snapshot.lastBattleSnapshot).toEqual({ foes: [] });

    store.setBattleActive(false);
    expect(store.getSnapshot().battleActive).toBe(false);
  });

  test('clear removes persisted state without mutating in-memory snapshot', () => {
    const storage = createMemoryStorage({ runState: '{"runId":"run-002"}' });
    const store = createRunStateStore(storage);
    store.restoreFromStorage();

    store.setMapRooms([{ room_type: 'shop' }]);
    store.clear();
    expect(storage.snapshot()).toEqual({});
    expect(store.getSnapshot().mapRooms).toEqual([{ room_type: 'shop' }]);
  });

  test('applyUIState resets state when menu mode is reported', () => {
    const storage = createMemoryStorage({ runState: '{"runId":"run-003"}' });
    const store = createRunStateStore(storage);
    store.setRunId('run-003');
    store.setBattleActive(true);
    store.setRoomData({ foo: 'bar' });

    const result = store.applyUIState({ mode: 'menu' });
    expect(result).toEqual({ mode: 'menu', runId: '', battleActive: false });
    expect(store.getSnapshot()).toMatchObject({
      runId: '',
      roomData: null,
      battleActive: false,
      mapRooms: []
    });
    expect(storage.snapshot()).toEqual({});
  });

  test('applyUIState hydrates run metadata from backend payloads', () => {
    const storage = createMemoryStorage();
    const store = createRunStateStore(storage);
    const payload = {
      mode: 'battle',
      active_run: 'run-007',
      game_state: {
        party: [{ id: 'alpha' }, { name: 'beta' }, { id: 'alpha' }],
        map: { rooms: [{ room_type: 'battle' }, { room_type: 'event' }] },
        current_state: {
          current_index: 1,
          current_room_type: 'battle',
          next_room_type: 'event',
          room_data: { foes: [], snapshot_missing: false }
        }
      }
    };

    const result = store.applyUIState(payload);
    expect(result).toEqual({ mode: 'battle', runId: 'run-007', battleActive: true });

    expect(store.getSnapshot()).toMatchObject({
      runId: 'run-007',
      selectedParty: ['alpha', 'beta'],
      mapRooms: [{ room_type: 'battle' }, { room_type: 'event' }],
      currentIndex: 1,
      currentRoomType: 'battle',
      nextRoom: 'event',
      battleActive: true,
      roomData: { foes: [], snapshot_missing: false },
      lastBattleSnapshot: { foes: [], snapshot_missing: false }
    });
    expect(storage.snapshot()).toEqual({ runState: '{"runId":"run-007"}' });
  });
});
