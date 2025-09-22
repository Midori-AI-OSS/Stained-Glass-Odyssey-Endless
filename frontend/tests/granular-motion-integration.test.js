import { describe, expect, test, beforeEach } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Granular motion integration fixes', () => {
  const gameViewportFile = join(import.meta.dir, '../src/lib/components/GameViewport.svelte');
  const uiSettingsFile = join(import.meta.dir, '../src/lib/components/UISettings.svelte');
  const battleViewFile = join(import.meta.dir, '../src/lib/components/BattleView.svelte');
  const battleFighterCardFile = join(import.meta.dir, '../src/lib/battle/BattleFighterCard.svelte');
  const overlayHostFile = join(import.meta.dir, '../src/lib/components/OverlayHost.svelte');

  test('GameViewport uses themeStore for reactive theme changes', () => {
    const content = readFileSync(gameViewportFile, 'utf8');
    expect(content).toContain('import { themeStore, motionStore, THEMES }');
    expect(content).toContain('$: themeSettings = $themeStore');
    expect(content).toContain('backgroundFromTheme');
  });

  test('UISettings includes background picker for static mode', () => {
    const content = readFileSync(uiSettingsFile, 'utf8');
    expect(content).toContain('Static Background');
    expect(content).toContain('Custom Background');
    expect(content).toContain('themeSettings.backgroundBehavior === \'static\'');
    expect(content).toContain('themeSettings.backgroundBehavior === \'custom\'');
  });

  test('BattleView uses granular motion settings', () => {
    const content = readFileSync(battleViewFile, 'utf8');
    expect(content).toContain('import { motionStore }');
    expect(content).toContain('effectiveReducedMotion');
    expect(content).toContain('motionSettings = $motionStore');
  });

  test('BattleFighterCard respects portrait glow settings', () => {
    const content = readFileSync(battleFighterCardFile, 'utf8');
    expect(content).toContain('disablePortraitGlows');
    expect(content).toContain('&& !disablePortraitGlows');
    expect(content).toContain('motionStore');
  });

  test('OverlayHost uses motion settings for transitions', () => {
    const content = readFileSync(overlayHostFile, 'utf8');
    expect(content).toContain('simplifiedTransitions');
    expect(content).toContain('effectiveReducedMotion');
    expect(content).toContain('motionStore');
  });
});
