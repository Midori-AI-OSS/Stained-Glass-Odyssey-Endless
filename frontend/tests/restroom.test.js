import { readFileSync } from 'fs';
import { join } from 'path';
import { describe, test, expect } from 'bun:test';

describe('rest room menu', () => {
  test('shows currency and actions', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/RestRoom.svelte'), 'utf8');
    expect(content).toContain('Rest Room');
    expect(content).toContain('<Coins');
    expect(content).toContain('Pull Character');
    expect(content).toContain('Switch Party');
    expect(content).toContain('Leave');
  });
});
