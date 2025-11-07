import { render, waitFor } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import StubElementIcon from './__fixtures__/StubElementIcon.svelte';
import StubPlayerPreview from './__fixtures__/StubPlayerPreview.svelte';
import StubStarStorm from './__fixtures__/StubStarStorm.svelte';
import StubStatTabs from './__fixtures__/StubStatTabs.svelte';

const hoisted = vi.hoisted(() => ({
  rosterEntries: Array.from({ length: 14 }, (_, index) => ({
    id: index + 1,
    name: `Hero ${index + 1}`,
    full_about: 'Test hero full description',
    summarized_about: 'Test hero',
    owned: true,
    is_player: index === 0,
    element: 'Aurora',
    stats: { hp: 100, atk: 20, defense: 10, level: 1 },
    ui: {}
  }))
}));

const { rosterEntries } = hoisted;

vi.mock('$lib/components/PlayerPreview.svelte', () => ({
  default: StubPlayerPreview
}));

vi.mock('$lib/components/StatTabs.svelte', () => ({
  default: StubStatTabs
}));

vi.mock('$lib/components/StarStorm.svelte', () => ({
  default: StubStarStorm
}));

vi.mock('$lib/systems/api.js', () => ({
  getPlayers: vi.fn().mockResolvedValue({ players: hoisted.rosterEntries, user: { level: 5 } }),
  getUpgrade: vi.fn().mockResolvedValue({}),
  upgradeStat: vi.fn().mockResolvedValue({})
}));

vi.mock('$lib/systems/assetLoader.js', () => ({
  getCharacterImage: vi.fn().mockReturnValue('image.png'),
  getRandomFallback: vi.fn().mockReturnValue('fallback.png'),
  getElementColor: vi.fn().mockReturnValue('rgb(120, 180, 255)'),
  getElementIcon: vi.fn().mockReturnValue(StubElementIcon)
}));

vi.mock('$lib/systems/characterMetadata.js', () => ({
  replaceCharacterMetadata: vi.fn()
}));

import PartyPicker from '$lib/components/PartyPicker.svelte';

function defineMeasurement(el, { clientHeight, scrollHeight }) {
  Object.defineProperty(el, 'clientHeight', {
    configurable: true,
    value: clientHeight
  });
  Object.defineProperty(el, 'scrollHeight', {
    configurable: true,
    value: scrollHeight
  });
}

describe('PartyPicker roster scroll management', () => {
  it('locks the panel and toggles roster fades when overflowing', async () => {
    const { container, getByTestId } = render(PartyPicker, {
      selected: rosterEntries.slice(0, 5).map((entry) => entry.id),
      reducedMotion: true
    });

    await waitFor(() => {
      const renderedChoices = container.querySelectorAll('[data-testid^="choice-"]');
      expect(renderedChoices.length).toBeGreaterThan(12);
    });

    const panel = getByTestId('party-picker').closest('.panel');
    expect(panel).not.toBeNull();
    expect(panel?.classList.contains('locked')).toBe(true);

    const rosterScroll = getByTestId('party-roster-scroll');
    const rosterStyles = getComputedStyle(rosterScroll);
    expect(rosterStyles.overflowY).toBe('auto');

    defineMeasurement(rosterScroll, { clientHeight: 420, scrollHeight: 2000 });

    rosterScroll.scrollTop = 0;
    rosterScroll.dispatchEvent(new Event('scroll'));
    await waitFor(() => {
      expect(getByTestId('roster-fade-bottom').classList.contains('visible')).toBe(true);
    });
    expect(getByTestId('roster-fade-top').classList.contains('visible')).toBe(false);

    rosterScroll.scrollTop = 240;
    rosterScroll.dispatchEvent(new Event('scroll'));
    await waitFor(() => {
      expect(getByTestId('roster-fade-top').classList.contains('visible')).toBe(true);
      expect(getByTestId('roster-fade-bottom').classList.contains('visible')).toBe(true);
    });

    rosterScroll.scrollTop = 1600;
    rosterScroll.dispatchEvent(new Event('scroll'));
    await waitFor(() => {
      expect(getByTestId('roster-fade-bottom').classList.contains('visible')).toBe(false);
    });

    expect(rosterScroll.clientHeight).toBeLessThanOrEqual(window.innerHeight || 768);
  });
});
