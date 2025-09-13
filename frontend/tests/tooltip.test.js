import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Tooltip component', () => {
  test('provides accessible markup and events', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/Tooltip.svelte'), 'utf8');
    expect(content).toContain('role="tooltip"');
    expect(content).toContain('on:mouseenter');
    expect(content).toContain('on:focusin');
  });
});
