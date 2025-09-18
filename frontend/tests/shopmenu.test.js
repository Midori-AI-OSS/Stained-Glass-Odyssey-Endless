import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

const shopMenuPath = join(import.meta.dir, '../src/lib/components/ShopMenu.svelte');
const overlayHostPath = join(import.meta.dir, '../src/lib/components/OverlayHost.svelte');
const pagePath = join(import.meta.dir, '../src/routes/+page.svelte');

describe('Shop menu tax metadata', () => {
  test('exposes surcharge props and UI affordances', () => {
    const content = readFileSync(shopMenuPath, 'utf8');
    expect(content).toContain('export let taxSummary');
    expect(content).toContain('export let itemsBought');
    expect(content).toContain('data-testid="shop-tax-note"');
    expect(content).toContain('class="price-breakdown"');
  });

  test('forwards tax summary via overlay host', () => {
    const content = readFileSync(overlayHostPath, 'utf8');
    expect(content).toContain('taxSummary={roomData.tax_summary || roomData.taxSummary || null}');
    expect(content).toContain('itemsBought={roomData.items_bought}');
  });

  test('shop buy payload includes base and taxed costs', () => {
    const content = readFileSync(pagePath, 'utf8');
    expect(content).toContain('payload.base_cost');
    expect(content).toContain('payload.taxed_cost');
    expect(content).toContain('payload.tax');
  });
});
