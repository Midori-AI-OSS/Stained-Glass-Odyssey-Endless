import { render, screen, cleanup } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { tick } from 'svelte';

import OverlayStub from './__fixtures__/BattleTargetingOverlay.stub.svelte';
import QueueStub from './__fixtures__/ActionQueue.stub.svelte';
import FloatersStub from './__fixtures__/BattleEventFloaters.stub.svelte';
import ProjectileStub from './__fixtures__/BattleProjectileLayer.stub.svelte';
import EffectsStub from './__fixtures__/BattleEffects.stub.svelte';
import FighterCardStub from './__fixtures__/BattleFighterCard.stub.svelte';
import EnrageIndicatorStub from './__fixtures__/EnrageIndicator.stub.svelte';
import BattleLogStub from './__fixtures__/BattleLog.stub.svelte';
import StatusIconsStub from './__fixtures__/StatusIcons.stub.svelte';

vi.mock('$lib', () => ({
  roomAction: vi.fn(),
}));

vi.mock('../src/lib/components/BattleTargetingOverlay.svelte', () => ({
  default: OverlayStub,
}));
vi.mock('../src/lib/battle/ActionQueue.svelte', () => ({
  default: QueueStub,
}));
vi.mock('../src/lib/components/BattleEventFloaters.svelte', () => ({
  default: FloatersStub,
}));
vi.mock('../src/lib/components/BattleProjectileLayer.svelte', () => ({
  default: ProjectileStub,
}));
vi.mock('../src/lib/effects/BattleEffects.svelte', () => ({
  default: EffectsStub,
}));
vi.mock('../src/lib/battle/BattleFighterCard.svelte', () => ({
  default: FighterCardStub,
}));
vi.mock('../src/lib/battle/BattleLog.svelte', () => ({
  default: BattleLogStub,
}));
vi.mock('../src/lib/battle/StatusIcons.svelte', () => ({
  default: StatusIconsStub,
}));
vi.mock('../src/lib/battle/EnrageIndicator.svelte', () => ({
  default: EnrageIndicatorStub,
}));

import BattleView from '../src/lib/components/BattleView.svelte';
import { roomAction } from '$lib';
import { motionStore } from '../src/lib/systems/settingsStorage.js';

async function settle() {
  await Promise.resolve();
  await tick();
  await Promise.resolve();
}

describe('BattleView effect queue guard', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    motionStore.set({
      globalReducedMotion: false,
      disablePortraitGlows: false,
      simplifyOverlayTransitions: false,
      enableBattleFx: true,
    });
    roomAction.mockReset();
  });

  afterEach(() => {
    cleanup();
    vi.clearAllTimers();
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('suppresses duplicate SummonEffect enqueues without silencing playback', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { component } = render(BattleView, {
      props: {
        runId: '',
        active: false,
        framerate: 60,
        showHud: false,
        showFoes: false,
      },
    });

    const state = component.$capture_state?.();
    expect(state?.queueEffect).toBeTypeOf('function');

    const queueEffect = state.queueEffect;
    const effectsProbe = screen.getByTestId('effects-probe');

    queueEffect('SummonEffect');
    queueEffect('SummonEffect');
    queueEffect('SummonEffect');

    expect(effectsProbe.dataset.cue).toBe('SummonEffect');

    await settle();

    expect(effectsProbe.dataset.cue).toBe('');
    expect(effectsProbe.dataset.lastCue).toBe('SummonEffect');

    queueEffect('SummonEffect');
    expect(effectsProbe.dataset.cue).toBe('SummonEffect');

    await settle();

    expect(
      warnSpy.mock.calls.some(([message]) =>
        typeof message === 'string' && message.includes('effect_update_depth_exceeded'),
      ),
    ).toBe(false);

    warnSpy.mockRestore();
  });

  it('prevents recursive polling when summons queue effects', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const deferred = (() => {
      let resolve;
      const promise = new Promise((res) => {
        resolve = res;
      });
      return { promise, resolve };
    })();

    roomAction.mockResolvedValue({
      party: [],
      foes: [],
      recent_events: [],
      effects_charge: [],
    });
    roomAction.mockReturnValueOnce(deferred.promise);

    render(BattleView, {
      props: {
        runId: 'RUN-123',
        active: true,
        framerate: 60,
        showHud: false,
        showFoes: false,
      },
    });

    expect(roomAction).toHaveBeenCalledTimes(1);

    deferred.resolve({
      party: [{ id: 'hero', hp: 10, max_hp: 10 }],
      foes: [],
      party_summons: [
        {
          owner_id: 'hero',
          id: 'sprite-001',
          hp: 5,
          max_hp: 5,
        },
      ],
      recent_events: [],
      effects_charge: [],
    });

    await settle();

    expect(roomAction).toHaveBeenCalledTimes(1);
    expect(
      warnSpy.mock.calls.some(([message]) =>
        typeof message === 'string' && message.includes('effect_update_depth_exceeded'),
      ),
    ).toBe(false);

    vi.advanceTimersByTime(1000);
    await settle();

    expect(roomAction).toHaveBeenCalledTimes(2);

    warnSpy.mockRestore();
  });
});
