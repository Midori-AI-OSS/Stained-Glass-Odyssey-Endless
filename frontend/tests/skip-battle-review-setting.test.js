import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Skip Battle Review setting', () => {
  test('settings storage handles skipBattleReview boolean', () => {
    const settingsFile = join(import.meta.dir, '../src/lib/systems/settingsStorage.js');
    const content = readFileSync(settingsFile, 'utf8');

    // Check load logic
    expect(content).toContain('if (data.skipBattleReview !== undefined) data.skipBattleReview = Boolean(data.skipBattleReview);');

    // Check save logic
    expect(content).toContain('if (merged.skipBattleReview !== undefined) merged.skipBattleReview = Boolean(merged.skipBattleReview);');
  });

  test('settings storage handles display toggles', () => {
    const settingsFile = join(import.meta.dir, '../src/lib/systems/settingsStorage.js');
    const content = readFileSync(settingsFile, 'utf8');

    expect(content).toContain('showTurnCounter: true');
    expect(content).toContain('flashEnrageCounter: true');
    expect(content).toContain('if (data.showTurnCounter !== undefined) data.showTurnCounter = Boolean(data.showTurnCounter);');
    expect(content).toContain('if (data.flashEnrageCounter !== undefined) data.flashEnrageCounter = Boolean(data.flashEnrageCounter);');
    expect(content).toContain('if (merged.showTurnCounter !== undefined) merged.showTurnCounter = Boolean(merged.showTurnCounter);');
    expect(content).toContain('if (merged.flashEnrageCounter !== undefined) merged.flashEnrageCounter = Boolean(merged.flashEnrageCounter);');
  });

  test('viewport state includes skipBattleReview in initialization', () => {
    const viewportFile = join(import.meta.dir, '../src/lib/systems/viewportState.js');
    const content = readFileSync(viewportFile, 'utf8');

    expect(content).toContain('skipBattleReview: saved.skipBattleReview ?? false');
    expect(content).toContain('showTurnCounter: saved.showTurnCounter ?? true');
    expect(content).toContain('flashEnrageCounter: saved.flashEnrageCounter ?? true');
  });

  test('GameplaySettings has skipBattleReview control', () => {
    const gameplayFile = join(import.meta.dir, '../src/lib/components/GameplaySettings.svelte');
    const content = readFileSync(gameplayFile, 'utf8');

    // Check for export
    expect(content).toContain('export let skipBattleReview = false;');
    expect(content).toContain('export let showTurnCounter = true;');
    expect(content).toContain('export let flashEnrageCounter = true;');

    // Check for UI control
    expect(content).toContain('Skip Battle Review');
    expect(content).toContain('bind:checked={skipBattleReview}');
    expect(content).toContain('SkipForward');
    expect(content).toContain('Show Turn Counter');
    expect(content).toContain('Flash Enrage Counter');
  });

  test('OverlayHost respects skipBattleReview flag', () => {
    const overlayFile = join(import.meta.dir, '../src/lib/components/OverlayHost.svelte');
    const content = readFileSync(overlayFile, 'utf8');

    // Check for export
    expect(content).toContain('export let skipBattleReview = false;');
    expect(content).toContain('export let showTurnCounter = true;');
    expect(content).toContain('export let flashEnrageCounter = true;');

    // Check for modified display condition
    expect(content).toContain('reviewOpen && !rewardOpen && reviewReady && !skipBattleReview');

    // Check for auto-skip logic
    expect(content).toContain('reviewOpen && !rewardOpen && reviewReady && skipBattleReview');
    expect(content).toContain("dispatch('nextRoom')");

    // Check that it passes the prop to SettingsMenu
    expect(content).toContain('{skipBattleReview}');
    expect(content).toContain('{showTurnCounter}');
    expect(content).toContain('{flashEnrageCounter}');

    // Check that BattleView receives the toggles
    expect(content).toContain('showTurnCounter={showTurnCounter}');
    expect(content).toContain('flashEnrageCounter={flashEnrageCounter}');
  });

  test('SettingsMenu includes skipBattleReview in save payload', () => {
    const settingsFile = join(import.meta.dir, '../src/lib/components/SettingsMenu.svelte');
    const content = readFileSync(settingsFile, 'utf8');

    // Check for export
    expect(content).toContain('export let skipBattleReview = false;');
    expect(content).toContain('export let showTurnCounter = true;');
    expect(content).toContain('export let flashEnrageCounter = true;');

    // Check for save payload
    expect(content).toContain('skipBattleReview,');
    expect(content).toContain('showTurnCounter,');
    expect(content).toContain('flashEnrageCounter,');

    // Check for GameplaySettings prop
    expect(content).toContain('bind:skipBattleReview');
    expect(content).toContain('bind:showTurnCounter');
    expect(content).toContain('bind:flashEnrageCounter');
  });

  test('GameViewport updates skipBattleReview when saveSettings is dispatched', () => {
    const gameviewportFile = join(import.meta.dir, '../src/lib/components/GameViewport.svelte');
    const content = readFileSync(gameviewportFile, 'utf8');

    // Check that skipBattleReview is included in the saveSettings handler destructuring
    expect(content).toContain('on:saveSettings={(e) => ({ sfxVolume, musicVolume, voiceVolume, framerate, reducedMotion, showActionValues, showTurnCounter, flashEnrageCounter, fullIdleMode, skipBattleReview, animationSpeed } = e.detail)}');

    // Check that skipBattleReview is declared as a local variable
    expect(content).toContain('let skipBattleReview = false;');
    expect(content).toContain('let showTurnCounter = true;');
    expect(content).toContain('let flashEnrageCounter = true;');

    // Check that skipBattleReview is passed to OverlayHost
    expect(content).toContain('{skipBattleReview}');
    expect(content).toContain('{showTurnCounter}');
    expect(content).toContain('{flashEnrageCounter}');
  });
});