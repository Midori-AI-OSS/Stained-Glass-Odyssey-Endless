import { describe, expect, test, beforeEach, afterEach } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Granular motion integration fixes', () => {
  const gameViewportFile = join(import.meta.dir, '../src/lib/components/GameViewport.svelte');
  const uiSettingsFile = join(import.meta.dir, '../src/lib/components/UISettings.svelte');
  const battleViewFile = join(import.meta.dir, '../src/lib/components/BattleView.svelte');
  const battleEffectsFile = join(import.meta.dir, '../src/lib/effects/BattleEffects.svelte');
  const battleFighterCardFile = join(import.meta.dir, '../src/lib/battle/BattleFighterCard.svelte');
  const overlayHostFile = join(import.meta.dir, '../src/lib/components/OverlayHost.svelte');
  const settingsStorageModuleUrl = new URL('../src/lib/systems/settingsStorage.js', import.meta.url).href;

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

  test('UISettings exposes battle FX toggle', () => {
    const content = readFileSync(uiSettingsFile, 'utf8');
    expect(content).toContain('Enable RPG Maker FX');
    expect(content).toContain('motionSettings.enableBattleFx');
    expect(content).toContain('updateMotion({ enableBattleFx: e.target.checked })');
  });

  test('BattleView uses granular motion settings', () => {
    const content = readFileSync(battleViewFile, 'utf8');
    expect(content).toContain('import { motionStore }');
    expect(content).toContain('effectiveReducedMotion');
    expect(content).toContain('motionSettings = $motionStore');
    expect(content).toContain('battleFxEnabled');
    expect(content).toContain('battleFxActive = battleFxEnabled && !effectiveReducedMotion');
    expect(content).toContain('!battleFxEnabled');
    expect(content).toContain('<BattleEffects cue={effectCue} enabled={battleFxActive} />');
  });

  test('BattleEffects component respects enabled flag', () => {
    const content = readFileSync(battleEffectsFile, 'utf8');
    expect(content).toContain('export let enabled = false');
    expect(content).toContain('if (!enabled || !name) return');
    expect(content).toContain('if (!mounted || !enabled || !canvas) return null');
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

  describe('Battle FX preference persistence', () => {
    const SETTINGS_KEY = 'autofighter_settings';
    let settingsModule;
    let storageBacking;

    beforeEach(async () => {
      storageBacking = new Map();
      globalThis.window = {
        matchMedia: () => ({
          matches: false,
          addEventListener: () => {},
          removeEventListener: () => {}
        })
      };
      globalThis.localStorage = {
        getItem: (key) => (storageBacking.has(key) ? storageBacking.get(key) : null),
        setItem: (key, value) => storageBacking.set(key, String(value)),
        removeItem: (key) => storageBacking.delete(key),
        clear: () => storageBacking.clear()
      };

      settingsModule = await import(`${settingsStorageModuleUrl}?t=${Date.now()}`);
      settingsModule.clearSettings();
      settingsModule.motionStore.set(null);
      settingsModule.themeStore.set(null);
    });

    afterEach(() => {
      delete globalThis.localStorage;
      delete globalThis.window;
    });

    test('enableBattleFx defaults off and persists when toggled', () => {
      const initial = settingsModule.loadSettings();
      expect(initial.motion.enableBattleFx).toBe(false);

      settingsModule.updateMotionSettings({ enableBattleFx: true });
      const stored = JSON.parse(globalThis.localStorage.getItem(SETTINGS_KEY));
      expect(stored.motion.enableBattleFx).toBe(true);

      const reloaded = settingsModule.loadSettings();
      expect(reloaded.motion.enableBattleFx).toBe(true);
    });
  });
});
