import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('DotSelector component', () => {
  test('includes a mute button for 0% volume', () => {
    const content = readFileSync(
      join(import.meta.dir, '../src/lib/components/DotSelector.svelte'),
      'utf8'
    );
    expect(content).toMatch(/aria-label="Mute"/);
    expect(content).toMatch(/select\(0\)/);
  });
});
