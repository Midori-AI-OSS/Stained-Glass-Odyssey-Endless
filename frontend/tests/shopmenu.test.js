import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

const shopMenuPath = join(import.meta.dir, '../src/lib/components/ShopMenu.svelte');
const overlayHostPath = join(import.meta.dir, '../src/lib/components/OverlayHost.svelte');
const purchaseUtilsPath = join(import.meta.dir, '../src/lib/systems/shopPurchases.js');

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

  test('shop purchase helpers include base and taxed costs', () => {
    const content = readFileSync(purchaseUtilsPath, 'utf8');
    expect(content).toContain('normalized.base_cost');
    expect(content).toContain('normalized.taxed_cost');
    expect(content).toContain('normalized.tax');
    expect(content).toContain('buildShopPurchasePayload');
  });
});
