import { render, cleanup } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { tick } from 'svelte';

import BasicStub from './__fixtures__/BasicComponent.stub.svelte';

const loadInitialState = vi.fn(async () => ({
  settings: {
    sfxVolume: 5,
    musicVolume: 5,
    voiceVolume: 5,
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
const startGameMusic = vi.fn();
const selectBattleMusic = vi.fn(() => []);
const applyMusicVolume = vi.fn();
const playVoice = vi.fn();
const applyVoiceVolume = vi.fn();
const stopGameMusic = vi.fn();

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

vi.mock('../src/lib/systems/viewportState.js', async () => {
  const actual = await vi.importActual('../src/lib/systems/viewportState.js');
  return {
    ...actual,
    loadInitialState,
    mapSelectedParty,
    startGameMusic,
    selectBattleMusic,
    applyMusicVolume,
    playVoice,
    applyVoiceVolume,
    stopGameMusic,
  };
});

import GameViewport from '../src/lib/components/GameViewport.svelte';

async function flush() {
  await Promise.resolve();
  await tick();
  await Promise.resolve();
}

describe('GameViewport map rendering with extended floors', () => {
  afterEach(() => {
    cleanup();
  });

  it('surfaces the correct room number for a 100-room floor', async () => {
    const rooms = Array.from({ length: 100 }, (_, index) => ({
      index,
      room_type: index === 0 ? 'start' : index === 99 ? 'battle-boss-floor' : 'battle-normal',
      floor: 1,
      pressure: 0,
    }));

    const { getByText, container, component } = render(GameViewport, {
      props: {
        runId: 'run-100',
        mapRooms: rooms,
        currentIndex: 99,
        currentRoomType: 'battle-boss-floor',
        battleActive: true,
        roomData: { result: 'battle', battle_index: 1, party: [], foes: [] },
        roomTags: [],
        items: [],
      },
    });

    await flush();

    expect(getByText(/Room 100/)).toBeTruthy();
    const viewportWrap = container.querySelector('.viewport-wrap');
    expect(viewportWrap).not.toBeNull();

    component.$set({ currentIndex: 49 });
    await flush();
    expect(getByText(/Room 50/)).toBeTruthy();
  });
});
