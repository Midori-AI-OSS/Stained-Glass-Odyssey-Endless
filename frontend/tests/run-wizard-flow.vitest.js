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
      description: 'Base challenge level',
      stacking: { minimum: 0, maximum: 20, step: 1, default: 5 },
      grants_reward_bonus: true
    },
    {
      id: 'enemy_buff',
      label: 'Enemy Buff',
      description: 'Improve foe stats',
      stacking: { minimum: 0, maximum: 10, step: 1, default: 0 },
      grants_reward_bonus: true
    },
    {
      id: 'character_stat_down',
      label: 'Stat Down',
      description: 'Reduce party stats for extra rewards',
      stacking: { minimum: 0, maximum: 5, step: 1, default: 0 },
      grants_reward_bonus: false
    }
  ],
  pressure: { tooltip: 'Pressure influences encounter difficulty.' }
};

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

    await fireEvent.change(pressureInput, { target: { value: '7' } });
    await fireEvent.change(enemyInput, { target: { value: '3' } });

    const modifiersNext = screen.getByRole('button', { name: 'Next' });
    await fireEvent.click(modifiersNext);
    await tick();

    expect(screen.getByRole('heading', { name: 'Review & Start' })).toBeTruthy();

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
      modifiers: expect.objectContaining({ pressure: 7, enemy_buff: 3 })
    });

    const events = logMenuAction.mock.calls.map(([, eventName]) => eventName);
    expect(events).toContain('metadata_loaded');
    expect(events).toContain('run_type_selected');
    expect(events).toContain('modifiers_confirmed');
    expect(events).toContain('start_submitted');
  });

  test('surfaces metadata errors and logs telemetry', async () => {
    getRunConfigurationMetadata.mockRejectedValueOnce(new Error('metadata offline'));

    render(RunChooser, { props: { runs: [] } });
    await waitFor(() => expect(getRunConfigurationMetadata).toHaveBeenCalled());

    expect(await screen.findByText('metadata offline')).toBeTruthy();
    expect(logMenuAction.mock.calls.map(([, eventName]) => eventName)).toContain('metadata_error');
  });
});
