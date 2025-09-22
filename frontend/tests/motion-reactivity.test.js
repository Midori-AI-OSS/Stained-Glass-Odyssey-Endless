import { describe, expect, test, beforeEach } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Motion settings reactivity fixes', () => {
  const starStormFile = join(import.meta.dir, '../src/lib/components/StarStorm.svelte');
  const battleFloatersFile = join(import.meta.dir, '../src/lib/components/BattleEventFloaters.svelte');
  const uiSettingsFile = join(import.meta.dir, '../src/lib/components/UISettings.svelte');
  const settingsStorageFile = join(import.meta.dir, '../src/lib/systems/settingsStorage.js');

  test('StarStorm uses motionStore for reactivity', () => {
    const content = readFileSync(starStormFile, 'utf8');
    expect(content).toContain('import { motionStore }');
    expect(content).toContain('$: motionSettings = $motionStore');
  });

  test('BattleEventFloaters uses motionStore for reactivity', () => {
    const content = readFileSync(battleFloatersFile, 'utf8');
    expect(content).toContain('import { motionStore }');
    expect(content).toContain('$: motionSettings = $motionStore');
  });

  test('UISettings updates reducedMotion variable', () => {
    const content = readFileSync(uiSettingsFile, 'utf8');
    expect(content).toContain('reducedMotion = ');
    expect(content).toContain('motionStore');
  });

  test('Settings storage exports reactive stores', () => {
    const content = readFileSync(settingsStorageFile, 'utf8');
    expect(content).toContain('export const motionStore');
    expect(content).toContain('export const themeStore');
    expect(content).toContain('motionStore.set');
    expect(content).toContain('themeStore.set');
  });

  test('updateMotionSettings updates legacy reducedMotion', () => {
    const content = readFileSync(settingsStorageFile, 'utf8');
    expect(content).toContain('reducedMotion: updatedMotion.globalReducedMotion');
  });
});
