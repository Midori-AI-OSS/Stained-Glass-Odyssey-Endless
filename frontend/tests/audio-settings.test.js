import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('AudioSettings component', () => {
  test('replaces sliders with DotSelector', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/AudioSettings.svelte'), 'utf8');
    expect((content.match(/DotSelector/g) || []).length).toBeGreaterThanOrEqual(3);
  });
});
