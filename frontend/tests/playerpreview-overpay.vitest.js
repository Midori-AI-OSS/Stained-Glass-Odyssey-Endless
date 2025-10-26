import { afterEach, beforeAll, describe, expect, test } from 'vitest';

process.env.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = 'true';
globalThis.SVELTE_ALLOW_RUNES_OUTSIDE_SVELTE = true;
globalThis.DEV = false;

let renderComponent;
let fireEvent;
let cleanup;
let PlayerPreview;

beforeAll(async () => {
  ({ render: renderComponent, fireEvent, cleanup } = await import('@testing-library/svelte'));
  PlayerPreview = (await import('../src/lib/components/PlayerPreview.svelte?test')).default;
});

afterEach(() => {
  cleanup?.();
});

describe('PlayerPreview overpay flow', () => {
  test('shows overpay prompt and dispatches allowOverpay payload', async () => {
    const roster = [
      {
        id: 'player-1',
        name: 'Aurora',
        img: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x8BAgMCAOlf7QAAAABJRU5ErkJggg==',
        is_player: true,
        element: 'Water',
        stats: { level: 1 }
      }
    ];

    const upgradeData = {
      element: 'water',
      items: {
        water_1: 0,
        water_2: 1
      },
      stat_totals: {},
      stat_counts: { atk: 0 },
      next_costs: {
        atk: {
          item: 'water_1',
          units: 125,
          breakdown: {
            water_2: 1
          }
        }
      }
    };

    const events = [];

    const { component, getByText } = renderComponent(PlayerPreview, {
      props: {
        roster,
        previewId: 'player-1',
        mode: 'upgrade',
        allowElementChange: false,
        upgradeContext: { stat: 'atk', pendingStat: null },
        upgradeData,
        upgradeLoading: false,
        upgradeError: null,
        selectedStat: 'atk',
        reducedMotion: true
      }
    });

    component.$on('request-upgrade', (event) => events.push(event.detail));

    expect(getByText('Missing 125× Water 1★. Convert higher-tier shards to continue:')).toBeTruthy();

    const button = getByText('Overpay with higher-tier shards');
    await fireEvent.click(button);

    expect(events.length).toBe(1);
    const detail = events[0];
    expect(detail.allowOverpay).toBe(true);
    expect(detail.expectedMaterials).toEqual({ units: 125 });
    expect(detail.totalMaterials).toBe(125);
    expect(detail.total_materials).toBe(125);
  });
});
