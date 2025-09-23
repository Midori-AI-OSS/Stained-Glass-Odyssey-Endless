import { describe, test, expect } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

  describe('ActionQueue component', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/battle/ActionQueue.svelte'), 'utf8');
    test('renders portraits and optional action values', () => {
      expect(content).toContain('getCharacterImage');
      expect(content).toContain('showActionValues');
      expect(content).toContain('flashEnrageCounter');
      expect(content).toContain('showTurnCounter');
      expect(content).toContain('animate:flip');
      expect(content).toContain('bonus-badge');
      expect(content).toContain('queue-header');
      expect(content).toContain('enrage-chip');
    });
  });

describe('Settings menu toggle', () => {
  const content = readFileSync(join(import.meta.dir, '../src/lib/components/GameplaySettings.svelte'), 'utf8');
  test('includes Show Action Values control', () => {
    expect(content).toContain('Show Action Values');
    expect(content).toContain('bind:checked={showActionValues}');
  });
  test('includes Show Turn Counter control', () => {
    expect(content).toContain('Show Turn Counter');
    expect(content).toContain('bind:checked={showTurnCounter}');
  });
  test('includes Flash Enrage Counter control', () => {
    expect(content).toContain('Flash Enrage Counter');
    expect(content).toContain('bind:checked={flashEnrageCounter}');
  });
  test('includes Full Idle Mode control', () => {
    expect(content).toContain('Full Idle Mode');
    expect(content).toContain('bind:checked={fullIdleMode}');
  });
  test('includes Animation Speed slider', () => {
    expect(content).toContain('Animation Speed');
    expect(content).toContain('DotSelector');
    expect(content).toContain('bind:value={dotSpeed}');
  });
});
