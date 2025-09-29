import { describe, expect, test } from 'bun:test';
import {
  normalizeShopPurchase,
  processSequentialPurchases
} from '../src/lib/systems/shopPurchases.js';

function taxedCost(basePrice, pressure, itemsBought) {
  if (itemsBought <= 0) {
    return basePrice;
  }
  const rate = 0.01 * (pressure + 1) * itemsBought;
  const tax = Math.ceil(basePrice * rate);
  return basePrice + tax;
}

describe('sequential shop purchases', () => {
  test('reprices remaining selections so multi-buy succeeds on the first attempt', async () => {
    const pressure = 3;
    const stockEntries = [
      { id: 'alpha', base_price: 100 },
      { id: 'beta', base_price: 200 }
    ];

    const initialStock = stockEntries.map((entry) => {
      const taxed = taxedCost(entry.base_price, pressure, 0);
      return {
        id: entry.id,
        base_price: entry.base_price,
        price: taxed,
        cost: taxed,
        tax: taxed - entry.base_price
      };
    });

    const purchases = initialStock
      .map((entry) => normalizeShopPurchase(entry))
      .filter((entry) => entry !== null);

    let itemsBought = 0;
    let remainingStock = [...initialStock];
    let submitCalls = 0;

    const submit = async (payload) => {
      submitCalls += 1;
      const original = stockEntries.find((entry) => entry.id === payload.id);
      expect(original, 'purchase should reference a known stock entry').toBeTruthy();
      const expectedCost = taxedCost(original.base_price, pressure, itemsBought);
      expect(payload.cost).toBe(expectedCost);
      expect(payload.taxed_cost).toBe(expectedCost);
      expect(payload.items).toBeTruthy();
      expect(payload.items.id).toBe(payload.id);

      itemsBought += 1;
      remainingStock = remainingStock
        .filter((entry) => entry.id !== payload.id)
        .map((entry) => {
          const taxed = taxedCost(entry.base_price, pressure, itemsBought);
          return {
            ...entry,
            price: taxed,
            cost: taxed,
            tax: taxed - entry.base_price
          };
        });

      return {
        items_bought: itemsBought,
        stock: remainingStock
      };
    };

    const finalState = await processSequentialPurchases(purchases, {
      initialRoomData: { stock: initialStock, items_bought: 0 },
      submit,
      waitBetween: async () => {}
    });

    expect(submitCalls).toBe(2);
    expect(itemsBought).toBe(2);
    expect(finalState?.items_bought ?? 0).toBe(2);
  });
});
