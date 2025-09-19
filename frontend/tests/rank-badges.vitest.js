import { render, cleanup, screen } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import BattleFighterCard from '../src/lib/battle/BattleFighterCard.svelte';

vi.mock('../src/lib/systems/assetLoader.js', () => ({
  getCharacterImage: () => 'placeholder.png',
  getElementColor: () => '#888888',
  getElementIcon: () => null,
  hasCharacterGallery: () => false,
  advanceCharacterImage: () => {}
}));

afterEach(() => {
  cleanup();
});

function renderFoe(rank) {
  const fighter = {
    id: `foe-${rank}`,
    name: `Dummy ${rank}`,
    rank,
    element: 'fire',
    hp: 120,
    max_hp: 120,
    ultimate_charge: 0,
    passives: []
  };

  return render(BattleFighterCard, {
    props: {
      fighter,
      position: 'top',
      reducedMotion: true,
      size: 'small'
    }
  });
}

describe('BattleFighterCard rank badges', () => {
  it('renders a Prime badge with the silver theme', () => {
    renderFoe('prime');
    const badge = screen.getByRole('img', { name: /prime/i });
    expect(badge.getAttribute('data-rank')).toBe('prime');
    expect(badge.getAttribute('data-rank-tier')).toBe('silver');
  });

  it('renders a Glitched Prime badge with the glitch animation', () => {
    renderFoe('glitched prime');
    const badge = screen.getByRole('img', { name: /glitched prime/i });
    expect(badge.getAttribute('data-rank')).toBe('glitched-prime');
    expect(badge.classList.contains('is-glitched')).toBe(true);
  });

  it('renders a Boss badge with the platinum styling', () => {
    renderFoe('boss');
    const badge = screen.getByRole('img', { name: /boss/i });
    expect(badge.getAttribute('data-rank')).toBe('boss');
    expect(badge.getAttribute('data-rank-tier')).toBe('platinum');
  });
});
