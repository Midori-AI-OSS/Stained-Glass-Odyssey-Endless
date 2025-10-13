import { describe, expect, test, beforeEach, afterEach, mock } from 'bun:test';

import {
  registerAssetMetadata,
  resetAssetRegistryOverrides
} from '../src/lib/systems/assetRegistry.js';

const currentPlayers = { players: [], user: { level: 1, exp: 0, next_level_exp: 100 } };
const TRACKS = {
  lunaNormal: 'https://example.com/luna-track.mp3',
  emberNormal: 'https://example.com/ember-track.mp3',
  fallbackNormal: 'https://example.com/fallback-normal.mp3',
  fallbackWeak: 'https://example.com/fallback-weak.mp3',
  fallbackBoss: 'https://example.com/fallback-boss.mp3',
  ixiaBoss: 'https://example.com/ixia-boss.mp3'
};

const BASE_FALLBACKS = {
  normal: [TRACKS.fallbackNormal],
  weak: [TRACKS.fallbackWeak],
  boss: [TRACKS.fallbackBoss]
};

mock.module('../src/lib/systems/settingsStorage.js', () => ({
  loadSettings: () => ({})
}));

mock.module('../src/lib/systems/api.js', () => ({
  getPlayers: async () => currentPlayers
}));

const originalMathRandom = Math.random;

const configureMusic = overrides => {
  const metadata = { musicFallbacks: BASE_FALLBACKS };
  if (overrides && Object.keys(overrides).length > 0) {
    metadata.musicOverrides = overrides;
  }
  registerAssetMetadata(metadata);
};

describe('selectBattleMusic weighting', () => {
  beforeEach(() => {
    currentPlayers.players = [];
    currentPlayers.user = { level: 1, exp: 0, next_level_exp: 100 };
    resetAssetRegistryOverrides();
    Math.random = originalMathRandom;
  });

  afterEach(() => {
    resetAssetRegistryOverrides();
    Math.random = originalMathRandom;
  });

  test('defaults to equal weighting when metadata is absent', async () => {
    currentPlayers.players = [
      { id: 'luna', element: 'Moon' },
      { id: 'ember', element: 'Fire' },
    ];
    configureMusic({
      luna: { normal: [TRACKS.lunaNormal] },
      ember: { normal: [TRACKS.emberNormal] }
    });

    const { loadInitialState, selectBattleMusic } = await import('../src/lib/systems/viewportState.js');
    await loadInitialState();

    Math.random = () => 0;
    const playlist = selectBattleMusic({
      roomType: 'battle-normal',
      party: [{ id: 'luna' }],
      foes: [{ id: 'ember' }],
    });

    expect(playlist).toEqual([TRACKS.lunaNormal]);
  });

  test('applies metadata weighting overrides when provided', async () => {
    currentPlayers.players = [
      { id: 'luna', element: 'Moon', music: { weights: { default: 3 } } },
      { id: 'ember', element: 'Fire' },
    ];
    configureMusic({
      luna: { normal: [TRACKS.lunaNormal] },
      ember: { normal: [TRACKS.emberNormal] }
    });

    const { loadInitialState, selectBattleMusic } = await import('../src/lib/systems/viewportState.js');
    await loadInitialState();

    Math.random = () => 0.74;
    const playlist = selectBattleMusic({
      roomType: 'battle-normal',
      party: [{ id: 'luna' }],
      foes: [{ id: 'ember' }],
    });

    expect(playlist).toEqual([TRACKS.lunaNormal]);
  });

  test('falls back to the reduced-motion safe playlist when no combatants are ready', async () => {
    currentPlayers.players = [
      { id: 'luna', element: 'Moon' },
    ];

    configureMusic({});

    const { loadInitialState, selectBattleMusic } = await import('../src/lib/systems/viewportState.js');
    await loadInitialState();

    Math.random = () => 0.5;
    const playlist = selectBattleMusic({
      roomType: 'battle-normal',
      party: [],
      foes: [],
    });

    expect(playlist).toEqual([TRACKS.fallbackNormal]);
  });

  test('uses normal fallback when combatant only has boss tracks', async () => {
    currentPlayers.players = [
      { id: 'ixia', element: 'Shadow' }
    ];

    configureMusic({
      ixia: {
        defaultCategory: 'boss',
        boss: [TRACKS.ixiaBoss]
      }
    });

    const { loadInitialState, selectBattleMusic } = await import('../src/lib/systems/viewportState.js');
    await loadInitialState();

    Math.random = () => 0.2;
    const playlist = selectBattleMusic({
      roomType: 'battle-normal',
      party: [{ id: 'ixia' }],
      foes: [{ id: 'slime' }]
    });

    expect(playlist).toEqual([TRACKS.fallbackNormal]);
  });
});
