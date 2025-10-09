import { describe, it, expect } from 'vitest';
import { render, cleanup } from '@testing-library/svelte';
import BattleTargetingOverlay from '../src/lib/components/BattleTargetingOverlay.svelte';
import { getDamageTypeColor } from '../src/lib/systems/assetLoader.js';

describe('BattleTargetingOverlay', () => {
  afterEach(() => {
    cleanup();
  });

  it('renders an arrow when attacker and target anchors are available', () => {
    const anchors = {
      attacker: { x: 0.1, y: 0.2 },
      target: { x: 0.8, y: 0.6 },
    };
    const events = [
      {
        type: 'damage_taken',
        source_id: 'attacker',
        target_id: 'target',
        damageTypeId: 'fire',
        metadata: { damage_type_id: 'fire' },
      },
    ];

    const { container } = render(BattleTargetingOverlay, {
      activeId: 'attacker',
      activeTargetId: 'target',
      anchors,
      combatants: [],
      events,
      reducedMotion: false,
      turnPhase: { state: 'start' },
    });

    const line = container.querySelector('line.arrow-line');
    expect(line).not.toBeNull();
    expect(line?.getAttribute('marker-end')).toMatch(/url\(#target-arrow-[^)]+\)/);

    const overlay = container.querySelector('.targeting-overlay');
    expect(overlay?.getAttribute('style')).toContain(`--arrow-color:${getDamageTypeColor('fire')}`);
  });

  it('renders an aftertaste marker when only the target anchor is visible', () => {
    const anchors = {
      target: { x: 0.75, y: 0.4 },
    };
    const events = [
      {
        type: 'relic_effect',
        target_id: 'target',
        effectLabel: 'Aftertaste',
        metadata: {
          effect_label: 'Aftertaste',
          random_damage_type: 'ice',
          damage_type_id: 'ice',
        },
      },
    ];

    const { container } = render(BattleTargetingOverlay, {
      activeId: null,
      activeTargetId: 'target',
      anchors,
      combatants: [],
      events,
      reducedMotion: false,
      turnPhase: { state: 'start' },
    });

    const line = container.querySelector('line.arrow-line');
    expect(line).toBeNull();

    const outer = container.querySelector('circle.node.target.outer');
    const inner = container.querySelector('circle.node.target.inner');
    expect(outer).not.toBeNull();
    expect(inner).not.toBeNull();

    expect(outer?.getAttribute('cx')).toBe('750');
    expect(outer?.getAttribute('cy')).toBe('400');

    const overlay = container.querySelector('.targeting-overlay');
    const expectedColor = getDamageTypeColor('ice');
    expect(overlay?.getAttribute('style')).toContain(`--arrow-color:${expectedColor}`);
  });

  it('indexes combatants by instance_id for fallback lookups', () => {
    const anchors = {
      'summon#1': { x: 0.4, y: 0.6 },
    };

    const { container } = render(BattleTargetingOverlay, {
      activeId: 'summon#1',
      activeTargetId: 'summon#1',
      anchors,
      combatants: [
        {
          id: 'lightstreamswords',
          instance_id: 'summon#1',
          element: 'light',
        },
      ],
      events: [],
      reducedMotion: false,
      turnPhase: { state: 'start' },
    });

    const line = container.querySelector('line.arrow-line');
    expect(line).not.toBeNull();
    expect(line?.getAttribute('x1')).toBe('400');
    expect(line?.getAttribute('y1')).toBe('600');
  });
});
