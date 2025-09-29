import { render, screen, cleanup, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { tick } from 'svelte';

import OverlayStub from './__fixtures__/BattleTargetingOverlay.stub.svelte';
import QueueStub from './__fixtures__/ActionQueue.stub.svelte';
import FloatersStub from './__fixtures__/BattleEventFloaters.stub.svelte';
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

function clone(value) {
  if (typeof structuredClone === 'function') {
    return structuredClone(value);
  }
  return JSON.parse(JSON.stringify(value));
}

function buildSnapshot({ turnPhase, statusPhase, includeActiveIds = true } = {}) {
  const snapshot = {
    party: [
      {
        id: 'hero',
        name: 'Hero',
        hp: 100,
        max_hp: 100,
        damage_types: ['fire'],
      },
    ],
    foes: [
      {
        id: 'goblin',
        name: 'Goblin',
        hp: 80,
        max_hp: 80,
        damage_types: ['earth'],
      },
    ],
    queue: [
      { id: 'hero' },
      { id: 'goblin' },
    ],
    recent_events: [],
    turn: 1,
  };

  if (includeActiveIds) {
    snapshot.active_id = 'hero';
    snapshot.active_target_id = 'goblin';
  }

  if (turnPhase !== undefined) {
    snapshot.turn_phase = turnPhase;
  }

  if (statusPhase) {
    snapshot.status_phase = statusPhase;
  }

  return snapshot;
}

async function settle() {
  await Promise.resolve();
  await tick();
  await Promise.resolve();
}

describe('BattleView turn phase handling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    roomAction.mockReset();
  });

  afterEach(() => {
    cleanup();
    vi.clearAllTimers();
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('persists attacker targeting through start/resolve and clears on end', async () => {
    const statusPhaseTemplate = {
      phase: 'dot',
      state: 'start',
      target_id: 'goblin',
      effect_ids: ['burn'],
      effect_names: ['Burn'],
      order: 1,
    };

    const modernSnapshots = [
      buildSnapshot({
        turnPhase: { state: 'start', attacker_id: 'hero', target_id: 'goblin' },
        statusPhase: clone(statusPhaseTemplate),
      }),
      buildSnapshot({
        turnPhase: { state: 'resolve' },
        statusPhase: clone({ ...statusPhaseTemplate, state: 'resolve' }),
        includeActiveIds: false,
      }),
      buildSnapshot({
        turnPhase: { state: 'end' },
        statusPhase: clone({ ...statusPhaseTemplate, state: 'end' }),
        includeActiveIds: false,
      }),
    ];
    const fallbackSnapshot = modernSnapshots[modernSnapshots.length - 1];

    roomAction.mockImplementation(() =>
      Promise.resolve(clone(modernSnapshots.length ? modernSnapshots.shift() : fallbackSnapshot))
    );

    const { container, component } = render(BattleView, {
      props: {
        runId: 'modern-turn-phase',
        active: true,
        framerate: 10000,
        showStatusTimeline: true,
        showHud: false,
        showFoes: true,
      },
    });

    await settle();

    await waitFor(() => {
      expect(screen.getByTestId('overlay-probe').dataset.phaseState).toBe('start');
    });
    expect(screen.getByTestId('overlay-probe').dataset.attacker).toBe('hero');
    expect(screen.getByTestId('queue-probe').dataset.activeId).toBe('hero');
    expect(container.querySelector('.status-timeline')).not.toBeNull();

    await vi.advanceTimersByTimeAsync(1);
    await settle();

    await waitFor(() => {
      expect(screen.getByTestId('overlay-probe').dataset.phaseState).toBe('resolve');
    });
    expect(screen.getByTestId('overlay-probe').dataset.attacker).toBe('hero');
    expect(screen.getByTestId('queue-probe').dataset.activeId).toBe('hero');
    expect(container.querySelector('.status-timeline')).not.toBeNull();

    await vi.advanceTimersByTimeAsync(1);
    await settle();

    await waitFor(() => {
      expect(screen.getByTestId('overlay-probe').dataset.phaseState).toBe('end');
    });
    expect(screen.getByTestId('overlay-probe').dataset.attacker).toBe('');
    expect(screen.getByTestId('queue-probe').dataset.activeId).toBe('');
    await waitFor(() => {
      expect(container.querySelector('.status-timeline')).toBeNull();
    });

    component.$set({ active: false });
    await settle();
  });

  it('falls back to legacy active fields when turn_phase is absent', async () => {
    const legacySnapshot = buildSnapshot({
      statusPhase: {
        phase: 'dot',
        state: 'start',
        target_id: 'goblin',
        effect_ids: ['burn'],
        effect_names: ['Burn'],
        order: 1,
      },
    });

    roomAction.mockImplementation(() => Promise.resolve(clone(legacySnapshot)));

    const { container, component } = render(BattleView, {
      props: {
        runId: 'legacy-turn-phase',
        active: true,
        framerate: 10000,
        showStatusTimeline: true,
        showHud: false,
        showFoes: true,
      },
    });

    await settle();

    const overlay = await screen.findByTestId('overlay-probe');
    expect(overlay.dataset.phasePresent).toBe('no');
    expect(overlay.dataset.attacker).toBe('hero');
    expect(screen.getByTestId('queue-probe').dataset.activeId).toBe('hero');
    expect(container.querySelector('.status-timeline')).not.toBeNull();

    component.$set({ active: false });
    await settle();
  });
});
