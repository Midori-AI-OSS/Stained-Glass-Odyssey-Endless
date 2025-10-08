import { beforeEach, describe, expect, test } from 'vitest';
import { JSDOM } from 'jsdom';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = '1';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
process.env.NODE_ENV = process.env.NODE_ENV || 'production';
globalThis.__SVELTE_DEV__ = false;

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://localhost' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.navigator = dom.window.navigator;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.CustomEvent = dom.window.CustomEvent;
globalThis.requestAnimationFrame = dom.window.requestAnimationFrame ?? ((cb) => setTimeout(cb, 0));
globalThis.cancelAnimationFrame = dom.window.cancelAnimationFrame ?? ((id) => clearTimeout(id));

const { cleanup, fireEvent, render, screen } = await import('@testing-library/svelte');
const { default: RewardOverlay } = await import('../src/lib/components/RewardOverlay.svelte');

const baseProps = {
  cards: [
    {
      id: 'radiant-beam',
      name: 'Radiant Beam',
      stars: 4
    }
  ],
  relics: [],
  items: [],
  gold: 0,
  partyStats: [],
  ended: false,
  nextRoom: '',
  fullIdleMode: false,
  sfxVolume: 5,
  reducedMotion: false
};

describe('RewardOverlay selection regression', () => {
  beforeEach(() => {
    cleanup();
  });

  test('keeps cards selectable when parent rejects the choice', async () => {
    const { component } = render(RewardOverlay, { props: baseProps });

    component.$on('select', (event) => {
      setTimeout(() => {
        event.detail?.respond?.({ ok: false });
      }, 0);
    });

    const cardButton = screen.getByRole('button', { name: /select card radiant beam/i });
    await fireEvent.click(cardButton);

    await new Promise((resolve) => setTimeout(resolve, 5));

    expect(screen.getByRole('button', { name: /select card radiant beam/i })).toBeInTheDocument();
  });
});
