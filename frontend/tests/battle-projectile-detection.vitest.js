import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/svelte';

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
import { motionStore } from '../src/lib/systems/settingsStorage.js';
import { roomAction } from '$lib';

function renderBattleView() {
  return render(BattleView, {
    props: {
      runId: '',
      active: false,
      framerate: 60,
      showHud: false,
      showFoes: false,
    },
  });
}

describe('BattleView projectile detection', () => {
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

  it('recognizes direct attack events from any source', () => {
    const { component } = renderBattleView();
    const state = component.$capture_state?.();
    expect(state?.isProjectileAttackEvent).toBeTypeOf('function');
    expect(state?.buildProjectilePayload).toBeTypeOf('function');

    const event = {
      type: 'damage_taken',
      amount: 32,
      source_id: 'hero-alpha',
      target_id: 'foe-omega',
      metadata: {
        attack_sequence: 42,
        attack_index: 1,
        attack_total: 3,
        damage_type_id: 'fire',
      },
    };

    expect(state.isProjectileAttackEvent(event)).toBe(true);
    const payload = state.buildProjectilePayload(event);
    expect(payload).toEqual(
      expect.objectContaining({
        sourceId: 'hero-alpha',
        targetId: 'foe-omega',
        variant: 'photonBlade',
      }),
    );
    expect(payload.sequenceKey).toContain('seq:42');
    expect(state.isProjectileAttackEvent({ type: 'heal_received' })).toBe(false);
  });

  it('queues photon blade projectiles for qualifying events', () => {
    const { component } = renderBattleView();
    const state = component.$capture_state?.();
    expect(state?.registerProjectileEvents).toBeTypeOf('function');

    const probe = screen.getByTestId('projectiles-probe');
    expect(probe.dataset.count).toBe('0');

    const projectileEvent = {
      type: 'damage_taken',
      amount: 12,
      source_id: 'scout-1',
      target_id: 'beast-7',
      metadata: {
        attack_sequence: 'combo-7',
        attack_index: 2,
        attack_total: 2,
        damage_type_id: 'wind',
      },
    };

    state.registerProjectileEvents([projectileEvent]);
    expect(probe.dataset.count).toBe('1');
    expect(probe.dataset.starts).toBe('scout-1');
    expect(probe.dataset.targets).toBe('beast-7');
    expect(probe.dataset.sequences).toContain('combo-7');

    state.registerProjectileEvents([
      { type: 'dot_tick', target_id: 'beast-7', source_id: 'scout-1' },
    ]);
    expect(probe.dataset.count).toBe('1');
  });
});
