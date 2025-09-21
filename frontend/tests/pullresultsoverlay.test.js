import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('PullResultsOverlay component', () => {
  test('stacks results and deals sequentially', () => {
    const content = readFileSync(
      join(import.meta.dir, '../src/lib/components/PullResultsOverlay.svelte'),
      'utf8'
    );
    expect(content).toContain('crossfade');
    expect(content).toContain('stack =');
    expect(content).toContain('dealNext');
    expect(content).toContain('catch((error) => {');
    expect(content).toContain('PullResultsOverlay: playback aborted');
  });
});
