import { describe, test, expect } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

  describe('ActionQueue component', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/battle/ActionQueue.svelte'), 'utf8');
    test('renders portraits and optional action values', () => {
      expect(content).toContain('getCharacterImage');
      expect(content).toContain('showActionValues');
      expect(content).toContain('animate:flip');
      expect(content).toContain('class:bonus');
      expect(content).toContain('.entry.active');
    });
  });

describe('Settings menu toggle', () => {
  const content = readFileSync(join(import.meta.dir, '../src/lib/components/GameplaySettings.svelte'), 'utf8');
  test('includes Show Action Values control', () => {
    expect(content).toContain('Show Action Values');
    expect(content).toContain('bind:checked={showActionValues}');
  });
  test('includes Full Idle Mode control', () => {
    expect(content).toContain('Full Idle Mode');
    expect(content).toContain('bind:checked={fullIdleMode}');
  });
});
