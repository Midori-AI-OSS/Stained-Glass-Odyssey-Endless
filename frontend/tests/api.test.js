import { describe, expect, test, mock } from 'bun:test';
import {
  getPlayers,
  getPlayerConfig,
  savePlayerConfig,
  getGacha,
  pullGacha,
  getUpgrade,
  upgradeCharacter,
  upgradeStat,
  wipeData,
  getLrmConfig,
  setLrmModel,
  testLrmModel
} from '../src/lib/systems/api.js';
import {
  startRun,
  updateParty,
  roomAction,
  chooseCard,
  chooseRelic
} from '../src/lib/uiApi.js';

process.env.VITE_API_BASE = 'http://backend.test';

// Helper to mock fetch
function createFetch(response, ok = true, status = 200) {
  return mock(async () => ({ ok, status, json: async () => response }));
}

describe('api calls', () => {
  test('startRun returns run data', async () => {
    global.fetch = createFetch({ run_id: '123', map: [] });
    const result = await startRun(['player']);
    expect(result).toEqual({ run_id: '123', map: [] });
  });

  test('updateParty sends party', async () => {
    global.fetch = createFetch({ status: 'ok' });
    const result = await updateParty(['sample_player']);
    expect(result).toEqual({ status: 'ok' });
  });

  test('getPlayers retrieves roster', async () => {
    global.fetch = createFetch({ players: [{ id: 'sample_player', owned: true }] });
    const result = await getPlayers();
    expect(result).toEqual({ players: [{ id: 'sample_player', owned: true }] });
  });

  test('roomAction posts action', async () => {
    global.fetch = createFetch({ result: 'battle', party: [], foes: [] });
    const result = await roomAction('0', 'attack');
    expect(result).toEqual({ result: 'battle', party: [], foes: [] });
  });

  test('roomAction buy reduces gold and removes item', async () => {
    const fetchMock = mock(async (url, options) => {
      const body = JSON.parse(options.body);
      expect(body).toEqual({
        action: 'room_action',
        params: { room_id: '0', id: 'r1', cost: 10 }
      });
      return { ok: true, status: 200, json: async () => ({ result: 'shop', gold: 90, stock: [] }) };
    });
    global.fetch = fetchMock;
    const result = await roomAction('0', { id: 'r1', cost: 10 });
    expect(result).toEqual({ result: 'shop', gold: 90, stock: [] });
  });

  test('roomAction throws on HTTP error', async () => {
    global.fetch = createFetch({}, false, 500);
    await expect(roomAction('0', 'attack')).rejects.toThrow('HTTP error 500');
  });

  test('getPlayerConfig fetches editor data', async () => {
    const payload = { pronouns: 'they', damage_type: 'Fire', hp: 0, attack: 0, defense: 0 };
    global.fetch = createFetch(payload);
    const result = await getPlayerConfig();
    expect(result).toEqual(payload);
  });

  test('savePlayerConfig posts editor data', async () => {
    global.fetch = createFetch({ status: 'ok' });
    const result = await savePlayerConfig({ pronouns: 'they', damage_type: 'Fire', hp: 1, attack: 2, defense: 3 });
    expect(result).toEqual({ status: 'ok' });
  });

  test('getGacha retrieves state', async () => {
    global.fetch = createFetch({ pity: 0, items: {}, players: [] });
    const result = await getGacha();
    expect(result).toEqual({ pity: 0, items: {}, players: [] });
  });

  test('pullGacha posts count', async () => {
    const fetchMock = mock(async (url, options) => {
      const body = JSON.parse(options.body);
      expect(body).toEqual({ count: 5, banner_id: "standard" });
      return { ok: true, status: 200, json: async () => ({ results: [], pity: 0 }) };
    });
    global.fetch = fetchMock;
    const result = await pullGacha(5);
    expect(result).toEqual({ results: [], pity: 0 });
  });

  test('chooseCard posts card selection', async () => {
    const payload = { card: { id: 'c1', name: 'Card', stars: 1 }, cards: ['c1'] };
    global.fetch = createFetch(payload);
    const result = await chooseCard('c1');
    expect(result).toEqual(payload);
  });

  test('chooseRelic posts relic selection', async () => {
    const payload = { relic: { id: 'r1', name: 'Relic', stars: 1 }, relics: ['r1'] };
    global.fetch = createFetch(payload);
    const result = await chooseRelic('r1');
    expect(result).toEqual(payload);
  });

  test('wipeData posts wipe and returns status', async () => {
    global.fetch = createFetch({ status: 'wiped' });
    const result = await wipeData();
    expect(result).toEqual({ status: 'wiped' });
  });

  test('wipeData throws on HTTP error', async () => {
    global.fetch = createFetch({}, false, 500);
    await expect(wipeData()).rejects.toThrow('HTTP error 500');
  });

  test('getLrmConfig fetches config', async () => {
    const payload = { current_model: 'deepseek', available_models: [] };
    global.fetch = createFetch(payload);
    const result = await getLrmConfig();
    expect(result).toEqual(payload);
  });

  test('setLrmModel posts selection', async () => {
    global.fetch = createFetch({ current_model: 'gemma' });
    const result = await setLrmModel('gemma');
    expect(result).toEqual({ current_model: 'gemma' });
  });

  test('testLrmModel posts prompt', async () => {
    global.fetch = createFetch({ response: 'ok' });
    const result = await testLrmModel('hi');
    expect(result).toEqual({ response: 'ok' });
  });

  test('getUpgrade retrieves data', async () => {
    global.fetch = createFetch({ level: 2, items: { fire_1: 3 } });
    const result = await getUpgrade('player');
    expect(result).toEqual({ level: 2, items: { fire_1: 3 } });
  });

  test('upgradeCharacter posts upgrade', async () => {
    global.fetch = createFetch({ level: 1, items: {} });
    const result = await upgradeCharacter('player');
    expect(result).toEqual({ level: 1, items: {} });
  });

  test('upgradeStat spends points', async () => {
    const fetchMock = mock(async (url, options) => {
      expect(url).toBe('http://backend.test/players/player/upgrade-stat');
      expect(JSON.parse(options.body)).toEqual({ stat_name: 'atk' });
      return {
        ok: true,
        status: 200,
        json: async () => ({ stat_upgraded: 'atk', points_spent: 1 })
      };
    });
    global.fetch = fetchMock;
    const result = await upgradeStat('player', 'atk');
    expect(result).toEqual({ stat_upgraded: 'atk', points_spent: 1 });
  });
});
