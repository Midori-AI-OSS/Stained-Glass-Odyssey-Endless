import { describe, expect, test, beforeEach } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Settings functionality fixes', () => {
  const battleEventFloatersFile = join(import.meta.dir, '../src/lib/components/BattleEventFloaters.svelte');
  const overlayHostFile = join(import.meta.dir, '../src/lib/components/OverlayHost.svelte');
  const uiSettingsFile = join(import.meta.dir, '../src/lib/components/UISettings.svelte');
  const settingsMenuDocFile = join(import.meta.dir, '../.codex/implementation/settings-menu.md');

  test('BattleEventFloaters prevents rendering when disabled', () => {
    const content = readFileSync(battleEventFloatersFile, 'utf8');
    expect(content).toContain('&& !isFloatingDamageDisabled');
    expect(content).toContain('if (events && events.length && !isFloatingDamageDisabled)');
  });

  test('OverlayHost uses simplifiedTransitions for components', () => {
    const content = readFileSync(overlayHostFile, 'utf8');
    expect(content).toContain('simplifiedTransitions ? true : effectiveReducedMotion');
    expect(content).toContain('$: simplifiedTransitions = motionSettings.simplifyOverlayTransitions');
  });

  test('UISettings uses existing background assets', () => {
    const content = readFileSync(uiSettingsFile, 'utf8');
    expect(content).toContain('Cityscape 1');
    expect(content).toContain('Cityscape 2');
    expect(content).toContain('1bd68c8e-5053-48f8-8464-0873942ef5dc.png');
    expect(content).not.toContain('bg_desert.webp');
    expect(content).not.toContain('bg_forest.webp');
  });

  test('Documentation reflects implemented custom background upload', () => {
    const content = readFileSync(settingsMenuDocFile, 'utf8');
    expect(content).toContain('Allows custom background upload via file picker');
    expect(content).toContain('Custom Background**: File picker for uploading');
    expect(content).not.toContain('future feature');
  });
});
