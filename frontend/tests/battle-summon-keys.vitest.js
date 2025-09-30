import { render, cleanup } from '@testing-library/svelte';
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

async function settle() {
  await Promise.resolve();
  await tick();
  await Promise.resolve();
}

describe('BattleView summon render keys', () => {
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

  it('renders multiple summons sharing an id without duplicate key warnings', async () => {
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
      foes: [],
      queue: [
        { id: 'hero' },
      ],
      recent_events: [],
      turn: 1,
      party_summons: {
        hero: [
          { id: 'shadow_clone', name: 'Clone A', hp: 12, max_hp: 12 },
          { id: 'shadow_clone', name: 'Clone B', hp: 10, max_hp: 12 },
        ],
      },
    };

    roomAction.mockImplementation(() => Promise.resolve(clone(snapshot)));

    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(BattleView, {
        props: {
          runId: 'summon-key-test',
          active: true,
          framerate: 10000,
          showHud: false,
          showFoes: false,
        },
      });
    }).not.toThrow();

    await settle();

    expect(roomAction).toHaveBeenCalled();

    const duplicateWarning = [...warnSpy.mock.calls, ...errorSpy.mock.calls].some(([message]) =>
      typeof message === 'string' && message.toLowerCase().includes('each block key'),
    );
    expect(duplicateWarning).toBe(false);

    warnSpy.mockRestore();
    errorSpy.mockRestore();
  });
});
