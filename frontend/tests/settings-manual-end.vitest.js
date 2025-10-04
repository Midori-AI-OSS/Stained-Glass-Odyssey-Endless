import { beforeEach, describe, expect, test, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/svelte';
import SettingsMenu from '../src/lib/components/SettingsMenu.svelte';

vi.mock('../src/lib/systems/api.js', () => ({
  endRun: vi.fn(() => Promise.resolve()),
  endAllRuns: vi.fn(() => Promise.resolve()),
  wipeData: vi.fn(() => Promise.resolve()),
  exportSave: vi.fn(() => Promise.resolve()),
  importSave: vi.fn(() => Promise.resolve()),
  getLrmConfig: vi.fn(() => Promise.resolve({ available_models: [], current_model: '' })),
  setLrmModel: vi.fn(() => Promise.resolve()),
  testLrmModel: vi.fn(() => Promise.resolve({ response: '' })),
  getBackendHealth: vi.fn(() => Promise.resolve({ status: 'ok', ping_ms: 42 })),
  getTurnPacing: vi.fn(() => Promise.resolve({ default: 0.5, turn_pacing: 0.5 })),
  setTurnPacing: vi.fn(() => Promise.resolve({ default: 0.5, turn_pacing: 0.5 }))
}));

vi.mock('../src/lib/systems/settingsStorage.js', () => ({
  saveSettings: vi.fn(),
  clearSettings: vi.fn(),
  clearAllClientData: vi.fn(),
  motionStore: { subscribe: (run) => { run({ globalReducedMotion: false, simplifyOverlayTransitions: false }); return () => {}; } }
}));

vi.mock('../src/lib/systems/overlayState.js', () => ({
  setManualSyncHalt: vi.fn()
}));

describe('SettingsMenu manual run ending', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('dispatches a forced endRun event with reason detail', async () => {
    const { component } = render(SettingsMenu, {
      props: {
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
        lrmModel: '',
        runId: 'run-123',
        backendFlavor: 'default'
      }
    });

    const handler = vi.fn();
    component.$on('endRun', handler);

    const endButton = await screen.findByRole('button', { name: 'End' });
    await fireEvent.click(endButton);

    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler.mock.calls[0][0]?.detail).toStrictEqual({ reason: 'forced' });
  });
});
