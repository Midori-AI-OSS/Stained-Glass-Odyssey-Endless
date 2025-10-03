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

  test('DETAIL_LABEL_KEYS include nested effect_label variants for aftertaste metadata', () => {
    const detailBlockStart = floaterSource.indexOf('const DETAIL_LABEL_KEYS');
    expect(detailBlockStart).toBeGreaterThan(-1);
    const detailBlockEnd = floaterSource.indexOf('];', detailBlockStart);
    expect(detailBlockEnd).toBeGreaterThan(detailBlockStart);
    const detailBlock = floaterSource.slice(detailBlockStart, detailBlockEnd);
    expect(detailBlock).toContain("'effect_label'");
    expect(detailBlock).toContain("'effectLabel'");
  });

  test('card and relic floater fallback inspects metadata.details effect_label', () => {
    const detailsBlockStart = floaterSource.indexOf('const details = meta.details;');
    expect(detailsBlockStart).toBeGreaterThan(-1);
    const fallbackPushStart = floaterSource.indexOf('fallbackValues.push(', detailsBlockStart);
    expect(fallbackPushStart).toBeGreaterThan(detailsBlockStart);
    const fallbackPushEnd = floaterSource.indexOf(');', fallbackPushStart);
    expect(fallbackPushEnd).toBeGreaterThan(fallbackPushStart);
    const fallbackBlock = floaterSource.slice(fallbackPushStart, fallbackPushEnd);
    expect(fallbackBlock).toContain('details.effect_label');
    expect(fallbackBlock).toContain('details.effectLabel');
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
