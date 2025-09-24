import { describe, expect, test, beforeEach, afterEach, mock } from 'bun:test';

const currentPlayers = { players: [], user: { level: 1, exp: 0, next_level_exp: 100 } };
const playlists = new Map();
const fallbackPlaylists = {
  normal: ['fallback-normal'],
  weak: ['fallback-weak'],
  boss: ['fallback-boss'],
};

mock.module('../src/lib/systems/settingsStorage.js', () => ({
  loadSettings: () => ({})
}));

mock.module('../src/lib/systems/api.js', () => ({
  getPlayers: async () => currentPlayers
}));

mock.module('../src/lib/systems/music.js', () => ({
  getCharacterPlaylist: (id, category) => playlists.get(`${id}:${category}`) ?? [],
  getMusicTracks: () => Object.values(fallbackPlaylists).flat(),
  getFallbackPlaylist: (category) => fallbackPlaylists[category] ?? [],
  shuffle: (list) => list,
}));

const originalMathRandom = Math.random;

describe('selectBattleMusic weighting', () => {
  beforeEach(() => {
    currentPlayers.players = [];
    currentPlayers.user = { level: 1, exp: 0, next_level_exp: 100 };
    playlists.clear();
    fallbackPlaylists.normal = ['fallback-normal'];
    fallbackPlaylists.weak = ['fallback-weak'];
    fallbackPlaylists.boss = ['fallback-boss'];
    Math.random = originalMathRandom;
  });

  afterEach(() => {
    Math.random = originalMathRandom;
  });

  test('defaults to equal weighting when metadata is absent', async () => {
    currentPlayers.players = [
      { id: 'luna', element: 'Moon' },
      { id: 'ember', element: 'Fire' },
    ];
    playlists.set('luna:normal', ['luna-track']);
    playlists.set('ember:normal', ['ember-track']);

    const { loadInitialState, selectBattleMusic } = await import('../src/lib/systems/viewportState.js');
    await loadInitialState();

    Math.random = () => 0;
    const playlist = selectBattleMusic({
      roomType: 'battle-normal',
      party: [{ id: 'luna' }],
      foes: [{ id: 'ember' }],
    });

    expect(playlist).toEqual(['luna-track']);
  });

  test('applies metadata weighting overrides when provided', async () => {
    currentPlayers.players = [
      { id: 'luna', element: 'Moon', music: { weights: { default: 3 } } },
      { id: 'ember', element: 'Fire' },
    ];
    playlists.set('luna:normal', ['luna-track']);
    playlists.set('ember:normal', ['ember-track']);

    const { loadInitialState, selectBattleMusic } = await import('../src/lib/systems/viewportState.js');
    await loadInitialState();

    Math.random = () => 0.74;
    const playlist = selectBattleMusic({
      roomType: 'battle-normal',
      party: [{ id: 'luna' }],
      foes: [{ id: 'ember' }],
    });

    expect(playlist).toEqual(['luna-track']);
  });

  test('falls back to the reduced-motion safe playlist when no combatants are ready', async () => {
    currentPlayers.players = [
      { id: 'luna', element: 'Moon' },
    ];

    const { loadInitialState, selectBattleMusic } = await import('../src/lib/systems/viewportState.js');
    await loadInitialState();

    Math.random = () => 0.5;
    const playlist = selectBattleMusic({
      roomType: 'battle-normal',
      party: [],
      foes: [],
    });

    expect(playlist).toEqual(['fallback-normal']);
  });
});
