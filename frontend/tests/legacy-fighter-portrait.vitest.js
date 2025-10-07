import { render, cleanup } from '@testing-library/svelte';
import { afterEach, describe, expect, it } from 'vitest';

import LegacyFighterPortrait from '../src/lib/battle/LegacyFighterPortrait.svelte';

afterEach(() => {
  cleanup();
});

describe('LegacyFighterPortrait ultimate ring', () => {
  it('scales ring progress with the supplied ultimate maximum', () => {
    const { container } = render(LegacyFighterPortrait, {
      props: {
        fighter: {
          id: 'luna',
          element: 'light',
          ultimate_charge: 7500,
          ultimate_max: 15000
        }
      }
    });

    const fill = container.querySelector('.ultimate-ring .fill');
    expect(fill).not.toBeNull();
    expect(fill.getAttribute('style')).toContain('stroke-dasharray: 50');
  });

  it('uses the legacy fallback when no ultimate maximum is provided', () => {
    const { container } = render(LegacyFighterPortrait, {
      props: {
        fighter: {
          id: 'rookie',
          element: 'wind',
          ultimate_charge: 6
        }
      }
    });

    const fill = container.querySelector('.ultimate-ring .fill');
    expect(fill).not.toBeNull();
    expect(fill.getAttribute('style')).toContain('stroke-dasharray: 40');
  });
});
