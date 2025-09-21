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

  test('viewport state includes skipBattleReview in initialization', () => {
    const viewportFile = join(import.meta.dir, '../src/lib/systems/viewportState.js');
    const content = readFileSync(viewportFile, 'utf8');
    
    expect(content).toContain('skipBattleReview: saved.skipBattleReview ?? false');
  });

  test('GameplaySettings has skipBattleReview control', () => {
    const gameplayFile = join(import.meta.dir, '../src/lib/components/GameplaySettings.svelte');
    const content = readFileSync(gameplayFile, 'utf8');
    
    // Check for export
    expect(content).toContain('export let skipBattleReview = false;');
    
    // Check for UI control
    expect(content).toContain('Skip Battle Review');
    expect(content).toContain('bind:checked={skipBattleReview}');
    expect(content).toContain('SkipForward');
  });

  test('OverlayHost respects skipBattleReview flag', () => {
    const overlayFile = join(import.meta.dir, '../src/lib/components/OverlayHost.svelte');
    const content = readFileSync(overlayFile, 'utf8');
    
    // Check for export
    expect(content).toContain('export let skipBattleReview = false;');
    
    // Check for modified display condition
    expect(content).toContain('reviewOpen && !rewardOpen && reviewReady && !skipBattleReview');
    
    // Check for auto-skip logic
    expect(content).toContain('reviewOpen && !rewardOpen && reviewReady && skipBattleReview');
    expect(content).toContain("dispatch('nextRoom')");
    
    // Check that it passes the prop to SettingsMenu
    expect(content).toContain('{skipBattleReview}');
  });

  test('SettingsMenu includes skipBattleReview in save payload', () => {
    const settingsFile = join(import.meta.dir, '../src/lib/components/SettingsMenu.svelte');
    const content = readFileSync(settingsFile, 'utf8');
    
    // Check for export
    expect(content).toContain('export let skipBattleReview = false;');
    
    // Check for save payload
    expect(content).toContain('skipBattleReview,');
    
    // Check for GameplaySettings prop
    expect(content).toContain('bind:skipBattleReview');
  });
});