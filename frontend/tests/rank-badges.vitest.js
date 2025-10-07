import { render, cleanup, screen } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import BattleFighterCard from '../src/lib/battle/BattleFighterCard.svelte';
import RankBadge from '../src/lib/battle/RankBadge.svelte';

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

describe('BattleFighterCard rank outlines', () => {
  it('applies the prime outline for prime foes without rendering a badge', () => {
    const { container } = renderFoe('prime');
    const portrait = container.querySelector('.fighter-portrait');
    expect(portrait?.classList.contains('rank-prime')).toBe(true);
    expect(screen.queryByRole('img', { name: /prime/i })).toBeNull();
  });

  it('keeps the prime outline for glitched prime foes without badges', () => {
    const { container } = renderFoe('glitched prime');
    const portrait = container.querySelector('.fighter-portrait');
    expect(portrait?.classList.contains('rank-prime')).toBe(true);
    expect(screen.queryByRole('img', { name: /glitched prime/i })).toBeNull();
  });

  it('applies the boss outline to boss variants while omitting badges', () => {
    const { container } = renderFoe('glitched boss');
    const portrait = container.querySelector('.fighter-portrait');
    expect(portrait?.classList.contains('rank-boss')).toBe(true);
    expect(screen.queryByRole('img', { name: /boss/i })).toBeNull();
  });
});

describe('RankBadge component', () => {
  function renderBadge(rank) {
    return render(RankBadge, {
      props: {
        rank,
        size: '2rem'
      }
    });
  }

  it('renders a Prime badge with the silver theme', () => {
    renderBadge('prime');
    const badge = screen.getByRole('img', { name: /prime/i });
    expect(badge.getAttribute('data-rank')).toBe('prime');
    expect(badge.getAttribute('data-rank-tier')).toBe('silver');
  });

  it('renders a Glitched Prime badge with the glitch animation', () => {
    renderBadge('glitched prime');
    const badge = screen.getByRole('img', { name: /glitched prime/i });
    expect(badge.getAttribute('data-rank')).toBe('glitched-prime');
    expect(badge.classList.contains('is-glitched')).toBe(true);
  });

  it('renders a Boss badge with the platinum styling', () => {
    renderBadge('boss');
    const badge = screen.getByRole('img', { name: /boss/i });
    expect(badge.getAttribute('data-rank')).toBe('boss');
    expect(badge.getAttribute('data-rank-tier')).toBe('platinum');
  });
});
