import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';

import EffectsChargeContainer from '../src/lib/components/battle/EffectsChargeContainer.svelte';

describe('EffectsChargeContainer', () => {
  it('renders progress bars with estimated damage text', () => {
    const charges = [
      { id: 'burn', name: 'Burn Burst', progress: 0.5, estimated_damage: 240 },
      { id: 'storm', name: 'Storm Lash', progress: 0.9, estimated_damage: 810 },
    ];

    render(EffectsChargeContainer, { props: { charges } });

    const entries = screen.getAllByTestId('effect-charge-entry');
    expect(entries.length).toBe(2);

    const bars = screen.getAllByRole('progressbar');
    expect(bars.length).toBe(2);

    const burnProgress = screen.getByRole('progressbar', {
      name: /Burn Burst 50% charged, approximately 240 damage/i,
    });
    expect(burnProgress).toBeTruthy();

    const damageGuess = screen.getByText(/≈ 810/);
    expect(damageGuess).toBeTruthy();
  });
});
