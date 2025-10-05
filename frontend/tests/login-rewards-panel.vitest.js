import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/svelte';
import LoginRewardsPanel from '../src/lib/components/LoginRewardsPanel.svelte';

const mockGetLoginRewardStatus = vi.fn();

vi.mock('../src/lib/systems/uiApi.js', () => ({
  getLoginRewardStatus: mockGetLoginRewardStatus
}));

describe('LoginRewardsPanel reward grouping', () => {
  beforeEach(() => {
    mockGetLoginRewardStatus.mockResolvedValue({
      seconds_until_reset: 3600,
      reset_at: new Date().toISOString(),
      rooms_completed: 1,
      rooms_required: 3,
      daily_rdr_bonus: 0.05,
      claimed_today: false,
      streak: 4,
      reward_items: [
        {
          item_id: 'ITEM-001',
          name: 'Photon Blade',
          stars: 3,
          damage_type: 'fire'
        },
        {
          item_id: 'ITEM-001',
          name: 'Photon Blade',
          stars: 3,
          damage_type: 'fire'
        },
        {
          item_id: 'ITEM-002',
          name: 'Aqua Core',
          stars: 2,
          damage_type: 'water'
        }
      ]
    });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  test('renders duplicate rewards as a single entry with quantity suffix', async () => {
    const { container } = render(LoginRewardsPanel);

    const groupedReward = await screen.findByText('Photon Blade (2x)');
    expect(groupedReward).toBeInTheDocument();

    const chips = container.querySelectorAll('.reward-chip');
    expect(chips).toHaveLength(2);

    const soloReward = await screen.findByText('Aqua Core');
    expect(soloReward.textContent?.trim()).toBe('Aqua Core');

    expect(mockGetLoginRewardStatus).toHaveBeenCalledTimes(1);
  });
});
