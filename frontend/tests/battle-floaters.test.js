import { describe, test, expect } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Battle event floaters', () => {
  const viewSource = readFileSync(
    join(import.meta.dir, '../src/lib/components/BattleView.svelte'),
    'utf8'
  );
  const floaterSource = readFileSync(
    join(import.meta.dir, '../src/lib/components/BattleEventFloaters.svelte'),
    'utf8'
  );

  test('records critical hit metadata on recent events', () => {
    expect(viewSource).toContain('metadata?.is_critical');
    expect(viewSource).toContain('evt.isCritical');
    expect(viewSource).toContain("metadata.is_critical ? 'crit' : ''");
  });

  test('renders an exclamation mark for critical damage floaters', () => {
    expect(floaterSource).toContain("entry.critical && entry.variant === 'damage'");
    expect(floaterSource).toContain('critical = Boolean');
  });
});
