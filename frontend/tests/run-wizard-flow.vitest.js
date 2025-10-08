import { beforeEach, describe, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { tick } from 'svelte';

vi.mock('$app/environment', () => ({
  browser: true,
  dev: false,
  building: false,
  version: {}
}));

vi.mock('../src/lib/components/PartyPicker.svelte', async () => ({
  default: (await import('./__fixtures__/RunWizardPartyPicker.stub.svelte')).default
}));

vi.mock('../src/lib/systems/uiApi.js', () => ({
  getRunConfigurationMetadata: vi.fn(),
  logMenuAction: vi.fn()
}));

import RunChooser from '../src/lib/components/RunChooser.svelte';
import { getRunConfigurationMetadata, logMenuAction } from '../src/lib/systems/uiApi.js';

const BASE_METADATA = {
  version: '1.0.0',
  run_types: [
    {
      id: 'standard',
      label: 'Standard Run',
      description: 'Default experience',
      default_modifiers: { pressure: 5 }
    },
    {
      id: 'boss',
      label: 'Boss Rush',
      description: 'Challenging multi-boss gauntlet',
      default_modifiers: { pressure: 8, enemy_buff: 2 }
    }
  ],
  modifiers: [
    {
      id: 'pressure',
      label: 'Pressure',
      category: 'economy',
      description: 'Base challenge level',
      stacking: { minimum: 0, step: 1, default: 5 },
      grants_reward_bonus: false,
      reward_bonuses: {},
      effects: {
        encounter_bonus: {
          type: 'step',
          step_size: 5,
          amount_per_step: 1,
          description: 'Adds +1 base foe slot for every five stacks before party-size adjustments.'
        },
        defense_floor: {
          type: 'linear',
          per_stack: 10,
          description: 'Foes roll at least pressure × 10 defense before variance is applied.'
        },
        elite_spawn_bonus_pct: {
          type: 'linear',
          per_stack: 1,
          description: 'Prime and Glitched odds each gain +1 percentage point per stack.'
        },
        shop_multiplier: {
          type: 'exponential',
          base: 1.26,
          description: 'Shop prices multiply by 1.26^pressure (±5% variance before repeat-visit taxes).'
        }
      },
      preview: [
        {
          stacks: 0,
          encounter_bonus: 0,
          defense_floor: 0,
          elite_spawn_bonus_pct: 0,
          shop_multiplier: 1
        },
        {
          stacks: 5,
          encounter_bonus: 1,
          defense_floor: 50,
          elite_spawn_bonus_pct: 5,
          shop_multiplier: 3.2
        }
      ]
    },
    {
      id: 'enemy_buff',
      label: 'Enemy Buff',
      category: 'foe',
      description: 'Improve foe stats',
      stacking: { minimum: 0, maximum: null, step: 1, default: 0 },
      grants_reward_bonus: true,
      reward_bonuses: {
        exp_bonus_per_stack: 0.01,
        rdr_bonus_per_stack: 0.01
      },
      effects: {
        stat: 'atk',
        per_stack: 0.01,
        scaling_type: 'additive'
      },
      preview: [
        { stacks: 0, raw_bonus: 0, effective_bonus: 0 },
        { stacks: 3, raw_bonus: 0.03, effective_bonus: 0.025 }
      ]
    },
    {
      id: 'character_stat_down',
      label: 'Stat Down',
      category: 'player',
      description: 'Reduce party stats for extra rewards',
      stacking: { minimum: 0, maximum: 5, step: 1, default: 0 },
      grants_reward_bonus: false,
      reward_bonuses: {
        exp_bonus_first_stack: 0.001,
        exp_bonus_additional_stack: 0.0012,
        rdr_bonus_first_stack: 0.001,
        rdr_bonus_additional_stack: 0.0012
      },
      effects: {
        primary_penalty_per_stack: 0.001,
        overflow_penalty_per_stack: 0.000001,
        overflow_threshold: 500
      },
      preview: [
        { stacks: 0, effective_multiplier: 1, bonus_rdr: 0, bonus_exp: 0 },
        { stacks: 1, effective_multiplier: 0.999, bonus_rdr: 0.001, bonus_exp: 0.001 }
      ]
    }
  ],
  pressure: { tooltip: 'Pressure influences encounter difficulty.' }
};

function readRewardValue(label) {
  const headings = screen.queryAllByText('Reward Preview');
  for (const heading of headings) {
    const container = heading.closest('section') ?? heading.closest('.reward-preview');
    if (!container) continue;
    const rows = Array.from(container.querySelectorAll('.preview-grid > div'));
    for (const row of rows) {
      const labelNode = row.querySelector('.preview-label');
      if (labelNode?.textContent?.trim() === label) {
        const valueNode = row.querySelector('.preview-value');
        return valueNode?.textContent?.trim() ?? null;
      }
    }
  }
  return null;
}

describe('RunChooser wizard flow', () => {
  beforeEach(() => {
    cleanup();
    localStorage.clear();
    vi.clearAllMocks();
    getRunConfigurationMetadata.mockResolvedValue(JSON.parse(JSON.stringify(BASE_METADATA)));
    logMenuAction.mockResolvedValue();
  });

  test('numbers steps sequentially when resume is skipped', async () => {
    const { container } = render(RunChooser, { props: { runs: [] } });

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalled());
    await tick();

    const indicatorSteps = Array.from(
      container.querySelectorAll('.step-indicator span')
    ).map((node) => node.textContent?.trim());

    expect(indicatorSteps).toEqual(['1', '2', '3', '4']);
    expect(screen.getByRole('heading', { name: 'Build Your Party' })).toBeTruthy();
  });

  test('walks through wizard, persists selections, and submits payload', async () => {
    const { component, container } = render(RunChooser, { props: { runs: [] } });
    const startSpy = vi.fn();
    component.$on('startRun', (event) => startSpy(event.detail));

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalled());
    await tick();

    await fireEvent.click(screen.getByTestId('set-party'));

    const nextFromParty = screen.getByRole('button', { name: 'Next' });
    expect(nextFromParty).not.toBeDisabled();
    await fireEvent.click(nextFromParty);
    await tick();

    expect(screen.getByRole('heading', { name: 'Choose Run Type' })).toBeTruthy();

    await fireEvent.click(screen.getByRole('button', { name: /boss rush/i }));
    await tick();

    const goToModifiers = screen.getByRole('button', { name: 'Next' });
    await fireEvent.click(goToModifiers);
    await tick();

    expect(screen.getByRole('heading', { name: 'Configure Modifiers' })).toBeTruthy();

    const modifierNodes = Array.from(container.querySelectorAll('.modifier'));
    const pressureInput = modifierNodes
      .find((node) => node.querySelector('.modifier-label')?.textContent?.includes('Pressure'))
      ?.querySelector('input');
    const enemyInput = modifierNodes
      .find((node) => node.querySelector('.modifier-label')?.textContent?.includes('Enemy Buff'))
      ?.querySelector('input');

    expect(pressureInput).toBeTruthy();
    expect(enemyInput).toBeTruthy();

    await fireEvent.input(pressureInput, { target: { value: '7' } });
    await fireEvent.input(enemyInput, { target: { value: '3' } });

    const modifiersNext = screen.getByRole('button', { name: 'Next' });
    await fireEvent.click(modifiersNext);
    await tick();

    expect(screen.getByRole('heading', { name: 'Review & Start' })).toBeTruthy();
    expect(screen.getByText('Pressure: 7')).toBeTruthy();
    expect(screen.getByText('Enemy Buff: 3')).toBeTruthy();
    expect(readRewardValue('RDR Bonus')).toBe('+3%');
    expect(readRewardValue('EXP Bonus')).toBe('+3%');

    const startButton = screen.getByRole('button', { name: 'Start Run' });
    await fireEvent.click(startButton);
    await tick();

    expect(startSpy).toHaveBeenCalledTimes(1);
    const payload = startSpy.mock.calls[0][0];

    expect(payload).toMatchObject({
      party: ['unit-1', 'unit-2'],
      damageType: 'fire',
      pressure: 7,
      runType: 'boss',
      modifiers: expect.objectContaining({ pressure: 7, enemy_buff: 3 })
    });
    expect(payload.metadataVersion).toBe(BASE_METADATA.version);

    const persisted = JSON.parse(localStorage.getItem('run_wizard_defaults_v1') || '{}');
    expect(persisted).toMatchObject({
      runTypeId: 'boss',
      damageType: 'fire',
      party: ['unit-1', 'unit-2'],
      modifiers: expect.objectContaining({ pressure: 7, enemy_buff: 3 }),
      metadataVersion: BASE_METADATA.version,
      metadataSignature: BASE_METADATA.version
    });

    const presetStore = JSON.parse(localStorage.getItem('run_wizard_recent_presets_v1') || '{}');
    expect(presetStore?.boss?.[0]?.values).toMatchObject({
      pressure: 7,
      enemy_buff: 3,
      character_stat_down: 0
    });
    expect(presetStore?.boss?.[0]?.metadataVersion).toBe(BASE_METADATA.version);
    expect(presetStore?.boss?.[0]?.metadataSignature).toBe(BASE_METADATA.version);

    const events = logMenuAction.mock.calls.map(([, eventName]) => eventName);
    expect(events).toContain('metadata_loaded');
    expect(events).toContain('run_type_selected');
    expect(events).toContain('modifiers_confirmed');
    expect(events).toContain('start_submitted');
  });

  test('updates reward preview when metadata refresh changes rewards', async () => {
    const initialMetadata = JSON.parse(JSON.stringify(BASE_METADATA));
    initialMetadata.metadata_hash = '1.0.0';
    const refreshedMetadata = JSON.parse(JSON.stringify(BASE_METADATA));
    refreshedMetadata.version = '1.1.0';
    refreshedMetadata.metadata_hash = 'refresh-hash';
    refreshedMetadata.modifiers = refreshedMetadata.modifiers.map((entry) => {
      if (entry.id === 'enemy_buff') {
        return {
          ...entry,
          reward_bonuses: {
            exp_bonus_per_stack: 0.015,
            rdr_bonus_per_stack: 0.015
          }
        };
      }
      return entry;
    });

    getRunConfigurationMetadata.mockImplementation(async ({ metadataHash }) => {
      if (metadataHash === 'refresh-hash') {
        return JSON.parse(JSON.stringify(refreshedMetadata));
      }
      return JSON.parse(JSON.stringify(initialMetadata));
    });

    localStorage.setItem(
      'run_wizard_defaults_v1',
      JSON.stringify({
        runTypeId: 'standard',
        modifiers: { enemy_buff: 2 },
        party: ['unit-1', 'unit-2'],
        damageType: 'fire'
      })
    );

    const { component } = render(RunChooser, { props: { runs: [] } });

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalledTimes(1));
    await tick();

    await fireEvent.click(screen.getByTestId('set-party'));
    const nextFromParty = screen.getByRole('button', { name: 'Next' });
    await fireEvent.click(nextFromParty);
    await tick();

    const goToModifiers = screen.getByRole('button', { name: 'Next' });
    await fireEvent.click(goToModifiers);
    await tick();

    expect(readRewardValue('RDR Bonus')).toBe('+2%');
    expect(readRewardValue('EXP Bonus')).toBe('+2%');

    component.$set({ metadataHash: 'refresh-hash' });

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalledTimes(2));
    await tick();

    await waitFor(() => {
      expect(readRewardValue('RDR Bonus')).toBe('+3%');
      expect(readRewardValue('EXP Bonus')).toBe('+3%');
    });
  });

  test('retains modifier selections on confirm after metadata refresh', async () => {
    const initialMetadata = JSON.parse(JSON.stringify(BASE_METADATA));
    initialMetadata.metadata_hash = 'initial-hash';
    const refreshedMetadata = JSON.parse(JSON.stringify(BASE_METADATA));
    refreshedMetadata.version = '1.0.1';
    refreshedMetadata.metadata_hash = 'refresh-hash';

    getRunConfigurationMetadata.mockImplementation(async ({ metadataHash }) => {
      if (metadataHash === 'refresh-hash') {
        return JSON.parse(JSON.stringify(refreshedMetadata));
      }
      return JSON.parse(JSON.stringify(initialMetadata));
    });

    const { component, container } = render(RunChooser, {
      props: { runs: [], metadataHash: 'initial-hash' }
    });

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalledTimes(1));
    await tick();

    await fireEvent.click(screen.getByTestId('set-party'));
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();

    await fireEvent.click(screen.getByRole('button', { name: /boss rush/i }));
    await tick();

    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();

    const modifierNodes = Array.from(container.querySelectorAll('.modifier'));
    const pressureInput = modifierNodes
      .find((node) => node.querySelector('.modifier-label')?.textContent?.includes('Pressure'))
      ?.querySelector('input');
    const enemyInput = modifierNodes
      .find((node) => node.querySelector('.modifier-label')?.textContent?.includes('Enemy Buff'))
      ?.querySelector('input');

    expect(pressureInput).toBeTruthy();
    expect(enemyInput).toBeTruthy();

    await fireEvent.input(pressureInput, { target: { value: '6' } });
    await fireEvent.input(enemyInput, { target: { value: '2' } });

    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();

    expect(screen.getByRole('heading', { name: 'Review & Start' })).toBeTruthy();
    expect(screen.getByText('Pressure: 6')).toBeTruthy();
    expect(screen.getByText('Enemy Buff: 2')).toBeTruthy();

    await component.$set({ metadataHash: 'refresh-hash' });
    await tick();

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalledTimes(2));
    await tick();

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Review & Start' })).toBeTruthy();
      expect(screen.queryByText('Pressure: 6')).toBeTruthy();
      expect(screen.queryByText('Enemy Buff: 2')).toBeTruthy();
    });
  });

  test('surfaces metadata errors and logs telemetry', async () => {
    getRunConfigurationMetadata.mockRejectedValueOnce(new Error('metadata offline'));

    render(RunChooser, { props: { runs: [] } });
    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalled());

    expect(await screen.findByText('metadata offline')).toBeTruthy();
    expect(logMenuAction.mock.calls.map(([, eventName]) => eventName)).toContain('metadata_error');
  });

  test('renders metadata-driven tooltips and previews', async () => {
    const { container } = render(RunChooser, { props: { runs: [] } });

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalled());
    await tick();

    await fireEvent.click(screen.getByTestId('set-party'));
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await fireEvent.click(screen.getByRole('button', { name: /boss rush/i }));
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();

    const previewChips = Array.from(container.querySelectorAll('.preview-chip'));
    const pressureChip = previewChips.find((chip) => chip.textContent?.includes('Shop ×'));
    expect(pressureChip?.textContent).toContain('Shop ×3.2');

    const pressureTooltip = screen.getByRole('button', { name: /Pressure modifier details/i });
    const pressureTooltipText = pressureTooltip.getAttribute('data-tooltip') || '';
    expect(pressureTooltipText).toContain('Stacks are uncapped');
    expect(pressureTooltipText).toContain('Stacks increase by 1 each time.');
    expect(pressureTooltipText).toContain('Stacks continue scaling beyond this preview because the modifier is uncapped.');
    expect(pressureTooltipText).toContain('Adds +1 base foe slot for every five stacks');

    const foeTooltip = screen.getByRole('button', { name: /Enemy Buff modifier details/i });
    const foeTooltipText = foeTooltip.getAttribute('data-tooltip') || '';
    expect(foeTooltipText).toContain('Each stack modifies attack by +1% Attack');
    expect(foeTooltipText).toContain('+1% EXP');

    const playerTooltip = screen.getByRole('button', { name: /Stat Down modifier details/i });
    const playerTooltipText = playerTooltip.getAttribute('data-tooltip') || '';
    expect(playerTooltipText).toContain('Each stack reduces all player stats by 0.1%');
    expect(playerTooltipText).toContain('Stacks beyond 500 reduce stats by only 0.0001%');
    expect(playerTooltipText).toContain('0.1% RDR');

    expect(container.textContent).toContain('Effects: +1% Attack/stack');
    expect(container.textContent).toContain('Effects: -0.1% stats/stack');
    expect(container.textContent).toContain('RDR +0.1%');
  });

  test('quick start presets surface recent modifier selections', async () => {
    const first = render(RunChooser, { props: { runs: [] } });

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalled());
    await tick();

    await fireEvent.click(screen.getByTestId('set-party'));
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await fireEvent.click(screen.getByRole('button', { name: /boss rush/i }));
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();

    const modifierNodes = Array.from(first.container.querySelectorAll('.modifier'));
    const pressureInput = modifierNodes
      .find((node) => node.querySelector('.modifier-label')?.textContent?.includes('Pressure'))
      ?.querySelector('input');
    const enemyInput = modifierNodes
      .find((node) => node.querySelector('.modifier-label')?.textContent?.includes('Enemy Buff'))
      ?.querySelector('input');

    await fireEvent.input(pressureInput, { target: { value: '9' } });
    await fireEvent.input(enemyInput, { target: { value: '4' } });

    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();
    await fireEvent.click(screen.getByRole('button', { name: 'Start Run' }));
    await tick();

    cleanup();
    getRunConfigurationMetadata.mockClear();
    logMenuAction.mockClear();
    getRunConfigurationMetadata.mockResolvedValue(JSON.parse(JSON.stringify(BASE_METADATA)));

    const second = render(RunChooser, { props: { runs: [] } });

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalled());
    await tick();

    await fireEvent.click(screen.getByTestId('set-party'));
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();

    const quickStartButton = await screen.findByRole('button', { name: /Apply preset 1/i });
    await fireEvent.click(quickStartButton);
    await tick();

    const secondModifiers = Array.from(second.container.querySelectorAll('.modifier'));
    const secondPressure = secondModifiers
      .find((node) => node.querySelector('.modifier-label')?.textContent?.includes('Pressure'))
      ?.querySelector('input');
    const secondEnemy = secondModifiers
      .find((node) => node.querySelector('.modifier-label')?.textContent?.includes('Enemy Buff'))
      ?.querySelector('input');

    expect(secondPressure?.value).toBe('9');
    expect(secondEnemy?.value).toBe('4');

    const events = logMenuAction.mock.calls.map(([, eventName]) => eventName);
    expect(events).toContain('preset_applied');

    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();
    await fireEvent.click(screen.getByRole('button', { name: 'Start Run' }));
    await tick();

    const startPayloads = logMenuAction.mock.calls
      .filter(([, eventName]) => eventName === 'start_submitted')
      .map(([, , payload]) => payload);
    expect(startPayloads[startPayloads.length - 1]).toMatchObject({ quick_start: true });

    const presetStore = JSON.parse(localStorage.getItem('run_wizard_recent_presets_v1') || '{}');
    expect(presetStore?.boss?.[0]?.metadataSignature).toBe(BASE_METADATA.version);
  });

  test('persists metadata hash for cache-aware reloads', async () => {
    cleanup();
    localStorage.clear();
    getRunConfigurationMetadata.mockReset();
    logMenuAction.mockReset();

    const HASHED_METADATA = {
      ...BASE_METADATA,
      metadata_hash: 'hash-001'
    };

    getRunConfigurationMetadata.mockResolvedValueOnce(JSON.parse(JSON.stringify(HASHED_METADATA)));

    const { container } = render(RunChooser, { props: { runs: [] } });

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalled());
    await tick();

    await fireEvent.click(screen.getByTestId('set-party'));
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await fireEvent.click(screen.getByRole('button', { name: /standard run/i }));
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();

    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await tick();
    await fireEvent.click(screen.getByRole('button', { name: 'Start Run' }));
    await tick();

    const persisted = JSON.parse(localStorage.getItem('run_wizard_defaults_v1') || '{}');
    expect(persisted.metadataSignature).toBe('hash-001');
    expect(persisted.metadataVersion).toBe(BASE_METADATA.version);

    const presetStore = JSON.parse(localStorage.getItem('run_wizard_recent_presets_v1') || '{}');
    expect(presetStore?.standard?.[0]?.metadataSignature).toBe('hash-001');
    expect(presetStore?.standard?.[0]?.metadataVersion).toBe(BASE_METADATA.version);

    const metadataBadge = container.querySelector('.preset-metadata');
    expect(metadataBadge?.textContent).toContain('Metadata 1.0.0');
  });

  test('refetches metadata when metadata hash updates', async () => {
    getRunConfigurationMetadata.mockResolvedValueOnce(JSON.parse(JSON.stringify(BASE_METADATA)));

    const { component } = render(RunChooser, {
      props: { runs: [], metadataHash: '1.0.0' }
    });

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalledTimes(1));
    expect(getRunConfigurationMetadata.mock.calls[0][0]).toMatchObject({ metadataHash: '1.0.0' });

    getRunConfigurationMetadata.mockResolvedValueOnce(
      JSON.parse(JSON.stringify({ ...BASE_METADATA, version: '1.0.1' }))
    );

    await component.$set({ metadataHash: '1.0.1' });
    await tick();

    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalledTimes(2));
    expect(getRunConfigurationMetadata.mock.calls[1][0]).toMatchObject({ metadataHash: '1.0.1' });
  });
});
