import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('PlayerPreview component', () => {
  const file = join(import.meta.dir, '../src/lib/components/PlayerPreview.svelte');

  test('exports mode-aware props', () => {
    const content = readFileSync(file, 'utf8');
    expect(content).toContain("export let mode = 'portrait'");
    expect(content).toContain('export let upgradeContext = null');
    expect(content).toContain('{#if mode === \'portrait\'}');
    expect(content).toContain('{:else if mode === \'upgrade\'}');
  });

  test('dispatches upgrade events', () => {
    const content = readFileSync(file, 'utf8');
    expect(content).toContain("dispatch('open-upgrade'");
    expect(content).toContain("dispatch('close-upgrade'");
    expect(content).toContain("dispatch('request-upgrade'");
    expect(content).toContain('Upgrade stats');
    expect(content).toContain('class="stat-button"');
  });
});
