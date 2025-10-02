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
    expect(floaterSource).toContain(
      "entry.critical && (entry.variant === 'damage' || entry.variant === 'drain')"
    );
    expect(floaterSource).toContain('critical = Boolean');
  });

  test('includes effect_label fallback so aftertaste labels render in floaters', () => {
    const labelBlockStart = floaterSource.indexOf('const LABEL_FALLBACK_KEYS');
    expect(labelBlockStart).toBeGreaterThan(-1);
    const labelBlockEnd = floaterSource.indexOf('];', labelBlockStart);
    expect(labelBlockEnd).toBeGreaterThan(labelBlockStart);
    const labelBlock = floaterSource.slice(labelBlockStart, labelBlockEnd);
    expect(labelBlock).toContain("'effect_label'");
  });

  test('staggered floater scheduling uses index-based offsets', () => {
    const anchor = 'list.forEach((raw, i) => {';
    const start = floaterSource.indexOf(anchor);
    expect(start).toBeGreaterThan(-1);
    const endMarker = 'addTimers.add(handle);';
    const end = floaterSource.indexOf(endMarker, start);
    expect(end).toBeGreaterThan(start);
    const snippet = floaterSource
      .slice(start, end + endMarker.length)
      .replace(/\s+$/g, '');
    expect(snippet).toMatchSnapshot('floater-stagger-block');
  });
});
