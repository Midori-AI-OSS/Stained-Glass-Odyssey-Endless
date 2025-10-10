import { render, cleanup } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { tick } from 'svelte';

import BasicStub from './__fixtures__/BasicComponent.stub.svelte';

const startGameMusic = vi.fn();
const selectBattleMusic = vi.fn(({ foes = [] } = {}) => {
  const hasLuna = foes.some((foe) => foe && (foe.id === 'luna' || foe.name === 'Luna'));
  return hasLuna ? ['luna-track'] : ['battle-track'];
});
const loadInitialState = vi.fn(async () => ({
  settings: {
    sfxVolume: 5,
    musicVolume: 12,
    voiceVolume: 7,
    framerate: 60,
    reducedMotion: false,
    showActionValues: false,
    showTurnCounter: true,
    flashEnrageCounter: true,
    fullIdleMode: false,
    skipBattleReview: false,
    animationSpeed: 1,
  },
  roster: [],
  user: { level: 1, exp: 0, next_level_exp: 100 },
}));
const mapSelectedParty = vi.fn(() => []);
const roomLabel = vi.fn(() => '');
const roomInfo = vi.fn(() => ({}));
const applyMusicVolume = vi.fn();
const playVoice = vi.fn();
const applyVoiceVolume = vi.fn();
const stopGameMusic = vi.fn();
const rewardOpen = vi.fn(() => false);
const resumeGameMusic = vi.fn();

vi.mock('../src/lib/components/RoomView.svelte', () => ({
  default: BasicStub,
}));

vi.mock('../src/lib/components/NavBar.svelte', () => ({
  default: BasicStub,
}));

vi.mock('../src/lib/components/OverlayHost.svelte', () => ({
  default: BasicStub,
}));

vi.mock('../src/lib/components/MainMenu.svelte', () => ({
  default: BasicStub,
}));

vi.mock('../src/lib/components/LoginRewardsPanel.svelte', () => ({
  default: BasicStub,
}));

vi.mock('../src/lib/components/AboutGamePanel.svelte', () => ({
  default: BasicStub,
}));

vi.mock('../src/lib/components/RewardsSidePanel.svelte', () => ({
  default: BasicStub,
}));

vi.mock('../src/lib/systems/assetLoader.js', () => ({
  getHourlyBackground: () => 'stub/background.png',
}));

vi.mock('../src/lib/systems/viewportState.js', () => ({
  loadInitialState,
  mapSelectedParty,
  roomLabel,
  roomInfo,
  startGameMusic,
  selectBattleMusic,
  applyMusicVolume,
  playVoice,
  applyVoiceVolume,
  stopGameMusic,
  rewardOpen,
  resumeGameMusic,
}));

vi.mock('../src/lib/systems/settingsStorage.js', async () => {
  const { writable } = await import('svelte/store');
  return {
    themeStore: writable({
      selected: 'default',
      customAccent: '#8ac',
      backgroundBehavior: 'rotating',
      customBackground: null,
    }),
    motionStore: writable({}),
    THEMES: {
      default: { accent: 'level-based' },
      custom: { accent: '#8ac' },
    },
  };
});

import GameViewport from '../src/lib/components/GameViewport.svelte';

async function flush() {
  await Promise.resolve();
  await tick();
  await Promise.resolve();
}

describe('GameViewport battle music reactivity', () => {
  beforeEach(() => {
    startGameMusic.mockClear();
    selectBattleMusic.mockClear();
    loadInitialState.mockClear();
    mapSelectedParty.mockClear();
    roomLabel.mockClear();
    roomInfo.mockClear();
    applyMusicVolume.mockClear();
    playVoice.mockClear();
    applyVoiceVolume.mockClear();
    stopGameMusic.mockClear();
    rewardOpen.mockClear();
    resumeGameMusic.mockClear();
  });

  afterEach(() => {
    cleanup();
  });

  it('does not restart music when foes update mid-battle', async () => {
    const initialRoom = {
      current_room: 'battle-normal',
      battle_index: 3,
      party: [
        { id: 'hero', name: 'Hero' },
      ],
      foes: [
        { id: 'slime', name: 'Slime' },
        { id: 'bat', name: 'Bat' },
      ],
    };

    const { component } = render(GameViewport, {
      props: {
        roomData: initialRoom,
        currentRoomType: 'battle-normal',
        battleActive: false,
      },
    });

    await flush();

    expect(startGameMusic).toHaveBeenCalledTimes(1);
    expect(selectBattleMusic).toHaveBeenCalledTimes(1);

    component.$set({ battleActive: true });
    await flush();

    expect(startGameMusic).toHaveBeenCalledTimes(1);

    const foeRemoved = {
      ...initialRoom,
      foes: [initialRoom.foes[0]],
    };

    component.$set({ roomData: foeRemoved });
    await flush();

    expect(startGameMusic).toHaveBeenCalledTimes(1);
    expect(selectBattleMusic).toHaveBeenCalledTimes(2);
  });

  it('switches to Luna playlist when she arrives mid-battle', async () => {
    const baseRoom = {
      current_room: 'battle-normal',
      battle_index: 9,
      party: [
        { id: 'hero', name: 'Hero' },
      ],
      foes: [],
    };

    const { component } = render(GameViewport, {
      props: {
        roomData: baseRoom,
        currentRoomType: 'battle-normal',
        battleActive: true,
      },
    });

    await flush();

    expect(startGameMusic).toHaveBeenCalledTimes(1);
    expect(startGameMusic.mock.calls[0][1]).toEqual(['battle-track']);

    const lunaSnapshot = {
      ...baseRoom,
      foes: [
        { id: 'luna', name: 'Luna' },
      ],
    };

    component.$set({ roomData: lunaSnapshot });
    await flush();

    expect(selectBattleMusic).toHaveBeenCalledTimes(2);
    expect(startGameMusic).toHaveBeenCalledTimes(2);
    expect(startGameMusic.mock.calls[1][1]).toEqual(['luna-track']);
  });
});
