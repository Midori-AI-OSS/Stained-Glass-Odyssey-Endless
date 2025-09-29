function readFiniteNumber(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}

export function extractShopPricing(entry) {
  if (!entry || typeof entry !== 'object') {
    return { base: null, taxed: null, tax: null };
  }
  const base = (() => {
    const candidates = [
      entry.base_cost,
      entry.base_price,
      entry.pricing?.base,
      entry.price,
      entry.cost
    ];
    for (const candidate of candidates) {
      const resolved = readFiniteNumber(candidate);
      if (resolved !== null) return resolved;
    }
    return null;
  })();
  const taxed = (() => {
    const candidates = [
      entry.taxed_cost,
      entry.pricing?.taxed,
      entry.price,
      entry.cost,
      base
    ];
    for (const candidate of candidates) {
      const resolved = readFiniteNumber(candidate);
      if (resolved !== null) return resolved;
    }
    return base;
  })();
  const tax = (() => {
    const candidates = [
      entry.tax,
      entry.pricing?.tax,
      (taxed !== null && base !== null) ? taxed - base : null
    ];
    for (const candidate of candidates) {
      const resolved = readFiniteNumber(candidate);
      if (resolved !== null) return resolved < 0 ? 0 : resolved;
    }
    if (taxed !== null && base !== null) {
      const diff = taxed - base;
      return Number.isFinite(diff) && diff > 0 ? diff : 0;
    }
    return null;
  })();
  return { base, taxed, tax };
}

export function normalizeShopPurchase(entry) {
  if (!entry || typeof entry !== 'object') {
    return null;
  }
  const id = entry.id ?? entry.item ?? null;
  if (!id) {
    return null;
  }
  const { base, taxed, tax } = extractShopPricing(entry);
  const normalized = { id };
  if (base !== null) {
    normalized.base_cost = base;
    normalized.base_price = base;
  }
  if (taxed !== null) {
    normalized.cost = taxed;
    normalized.price = taxed;
    normalized.taxed_cost = taxed;
  }
  if (tax !== null) {
    normalized.tax = tax;
  }
  return normalized;
}

const COST_KEYS = ['base_cost', 'base_price', 'cost', 'price', 'taxed_cost', 'tax'];

export function refreshPurchasePricing(entry, roomData) {
  if (!entry || typeof entry !== 'object') {
    return entry;
  }
  if (!roomData || typeof roomData !== 'object') {
    return entry;
  }
  const stockList = Array.isArray(roomData.stock) ? roomData.stock : [];
  const match = stockList.find((stock) => {
    if (!stock || typeof stock !== 'object') return false;
    const stockId = stock.id ?? stock.item ?? null;
    return stockId === entry.id;
  });
  if (!match) {
    return entry;
  }
  const pricing = normalizeShopPurchase(match);
  if (!pricing) {
    return entry;
  }
  const updated = { ...entry };
  for (const key of COST_KEYS) {
    if (Object.prototype.hasOwnProperty.call(pricing, key)) {
      updated[key] = pricing[key];
    }
  }
  return updated;
}

export function buildShopPurchasePayload(entry) {
  if (!entry || typeof entry !== 'object') {
    return null;
  }
  return { ...entry, items: { ...entry } };
}

const noopWait = async () => {};

export async function processSequentialPurchases(
  purchases,
  {
    submit,
    initialRoomData = null,
    waitBetween = noopWait,
    reprice = refreshPurchasePricing,
    buildPayload = buildShopPurchasePayload
  } = {}
) {
  if (typeof submit !== 'function') {
    throw new TypeError('submit must be a function');
  }
  if (!Array.isArray(purchases) || purchases.length === 0) {
    return initialRoomData ?? null;
  }
  const queue = purchases.map((entry) => ({ ...entry }));
  let roomData = initialRoomData ?? null;
  for (let index = 0; index < queue.length; index += 1) {
    const total = queue.length;
    const current = roomData ? reprice(queue[index], roomData) : queue[index];
    queue[index] = current;
    const payload = buildPayload(current);
    if (!payload) {
      continue;
    }
    const result = await submit(payload, index, total);
    if (result !== undefined) {
      roomData = result;
    }
    if (index < total - 1) {
      await waitBetween(index, total);
    }
  }
  return roomData;
}
