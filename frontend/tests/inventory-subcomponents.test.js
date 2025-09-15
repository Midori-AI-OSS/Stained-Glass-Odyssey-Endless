import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

const cardView = readFileSync(join(import.meta.dir, '../src/lib/components/inventory/CardView.svelte'), 'utf8');
const relicView = readFileSync(join(import.meta.dir, '../src/lib/components/inventory/RelicView.svelte'), 'utf8');
const materialsPanel = readFileSync(join(import.meta.dir, '../src/lib/components/inventory/MaterialsPanel.svelte'), 'utf8');

describe('inventory subcomponents', () => {
  test('CardView lists cards', () => {
    expect(cardView).toContain('cards-grid');
  });
  test('RelicView lists relics', () => {
    expect(relicView).toContain('relics-grid');
  });
  test('MaterialsPanel shows materials grid', () => {
    expect(materialsPanel).toContain('materials-grid');
  });
});
