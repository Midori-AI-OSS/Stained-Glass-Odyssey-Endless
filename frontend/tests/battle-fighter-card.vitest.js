import { render, cleanup } from '@testing-library/svelte';
import { afterEach, describe, expect, it } from 'vitest';
import BattleFighterCard from '../src/lib/battle/BattleFighterCard.svelte';

afterEach(() => {
  cleanup();
});

describe('BattleFighterCard tick indicators', () => {
  it('renders tick indicator arrows with damage-type palette', () => {
    const tickIndicators = [
      { id: 'dot-1', type: 'dot_tick', amount: 12, damageTypeId: 'poison', timestamp: Date.now() },
      { id: 'hot-1', type: 'hot_tick', amount: 8, damageTypeId: 'light', timestamp: Date.now() + 1 },
    ];

    const { container } = render(BattleFighterCard, {
      props: {
        fighter: { id: 'hero', name: 'Hero', element: 'fire' },
        position: 'bottom',
        tickIndicators,
      },
    });

    const layer = container.querySelector('.tick-indicator-layer');
    expect(layer).not.toBeNull();
    const arrows = Array.from(layer.querySelectorAll('.tick-arrow'));
    expect(arrows).toHaveLength(2);
    expect(arrows[0].classList.contains('dot')).toBe(true);
    expect(arrows[1].classList.contains('hot')).toBe(true);
    expect(arrows[0].getAttribute('style')).toContain('--arrow-color');
    expect(arrows[1].getAttribute('style')).toContain('--arrow-color');
  });

  it('disables tick indicator animations when reduced motion is active', () => {
    const { container } = render(BattleFighterCard, {
      props: {
        fighter: { id: 'hero', name: 'Hero', element: 'water' },
        position: 'top',
        reducedMotion: true,
        tickIndicators: [
          { id: 'dot-1', type: 'dot_tick', amount: 4, damageTypeId: 'ice', timestamp: Date.now() },
        ],
      },
    });

    const layer = container.querySelector('.tick-indicator-layer');
    expect(layer).not.toBeNull();
    expect(layer.classList.contains('reduced')).toBe(true);
  });
});
