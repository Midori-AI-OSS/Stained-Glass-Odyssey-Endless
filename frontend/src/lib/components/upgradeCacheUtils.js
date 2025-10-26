import { ITEM_UNIT_SCALE } from '../utils/upgradeFormatting.js';

function normalizeElementKey(elementKey) {
  return String(elementKey || 'generic').toLowerCase();
}

function buildTierMap(elementKey) {
  const normalized = normalizeElementKey(elementKey);
  return Object.entries(ITEM_UNIT_SCALE)
    .map(([tier, scale]) => ({
      tier: Number(tier),
      scale: Number(scale),
      key: `${normalized}_${tier}`
    }))
    .sort((a, b) => b.tier - a.tier);
}

function cloneElementInventory(items = {}, elementKey = '') {
  const normalizedKey = normalizeElementKey(elementKey);
  const prefix = `${normalizedKey}_`;
  const inventory = {};

  for (const [key, value] of Object.entries(items || {})) {
    if (!key || typeof key !== 'string') continue;
    if (!key.toLowerCase().startsWith(prefix)) continue;
    const normalizedItemKey = key.toLowerCase();
    const numeric = Number(value);
    inventory[normalizedItemKey] = Number.isFinite(numeric) && numeric > 0 ? Math.floor(numeric) : 0;
  }

  const baseKey = `${normalizedKey}_1`;
  if (!Object.prototype.hasOwnProperty.call(inventory, baseKey)) {
    inventory[baseKey] = 0;
  }

  return inventory;
}

export function simulateMaterialConsumption(items = {}, elementKey = '', units = 0) {
  const normalizedKey = normalizeElementKey(elementKey);
  const tiers = buildTierMap(normalizedKey);
  const baseKey = `${normalizedKey}_1`;
  const inventory = cloneElementInventory(items, normalizedKey);
  const remaining = { ...inventory };
  const consumed = {};

  const targetUnits = Math.max(0, Math.floor(Number(units) || 0));
  if (targetUnits <= 0 || tiers.length === 0) {
    return {
      consumed,
      remaining,
      fulfilled: targetUnits === 0,
      spentUnits: 0
    };
  }

  let remainingUnits = targetUnits;

  outer: while (remainingUnits > 0) {
    for (const { tier, scale, key } of tiers) {
      const available = remaining[key] ?? 0;
      if (available <= 0) continue;
      if (tier === 1 || scale <= remainingUnits) {
        remaining[key] = available - 1;
        consumed[key] = (consumed[key] || 0) + 1;
        remainingUnits = Math.max(0, remainingUnits - (tier === 1 ? 1 : scale));
        continue outer;
      }
    }

    let convertCandidate = null;
    for (const { tier, key, scale } of tiers) {
      if (tier === 1) continue;
      const available = remaining[key] ?? 0;
      if (available > 0) {
        convertCandidate = { tier, key, scale };
        break;
      }
    }

    if (!convertCandidate) {
      break;
    }

    remaining[convertCandidate.key] = (remaining[convertCandidate.key] ?? 0) - 1;
    consumed[convertCandidate.key] = (consumed[convertCandidate.key] || 0) + 1;
    remaining[baseKey] = (remaining[baseKey] ?? 0) + convertCandidate.scale;
  }

  const fulfilled = remainingUnits <= 0;
  const spentUnits = Math.max(0, targetUnits - Math.max(0, remainingUnits));
  const normalizedRemaining = {};
  for (const [key, value] of Object.entries(remaining)) {
    normalizedRemaining[key] = value > 0 ? value : 0;
  }

  return {
    consumed,
    remaining: normalizedRemaining,
    fulfilled,
    spentUnits
  };
}

export function mergeUpgradePayload(previousData, result) {
  const base = { ...(previousData || {}) };
  if (result && typeof result === 'object') {
    Object.assign(base, result);
  }

  if (result && Object.prototype.hasOwnProperty.call(result, 'items')) {
    base.items = result.items || {};
  } else if (previousData && Object.prototype.hasOwnProperty.call(previousData, 'items')) {
    base.items = previousData.items;
  } else if (!base.items) {
    base.items = {};
  }

  const payloadMaps = [
    ['stat_totals', {}],
    ['stat_counts', {}],
    ['next_costs', {}],
    ['stat_upgrades', []],
  ];

  for (const [key, fallback] of payloadMaps) {
    if (result && Object.prototype.hasOwnProperty.call(result, key)) {
      base[key] = result[key] ?? fallback;
    } else if (previousData && Object.prototype.hasOwnProperty.call(previousData, key)) {
      base[key] = previousData[key];
    } else if (!Object.prototype.hasOwnProperty.call(base, key)) {
      base[key] = Array.isArray(fallback) ? [] : { ...fallback };
    }
  }

  if (result && Object.prototype.hasOwnProperty.call(result, 'element')) {
    base.element = result.element;
  } else if (previousData && Object.prototype.hasOwnProperty.call(previousData, 'element')) {
    base.element = previousData.element;
  }

  if (result && Object.prototype.hasOwnProperty.call(result, 'materials_remaining')) {
    const hasItems = Object.prototype.hasOwnProperty.call(result, 'items');
    const elementKey = normalizeElementKey(result?.element || base.element);

    if (elementKey && !hasItems) {
      const materialKey = `${elementKey}_1`;
      const tierPrefix = `${elementKey}_`;
      const previousItems = previousData?.items || base.items || {};
      let nextItems = { ...(base.items || {}) };

      if (previousItems && Object.keys(previousItems).length > 0 && Object.prototype.hasOwnProperty.call(result, 'materials_spent')) {
        const simulation = simulateMaterialConsumption(previousItems, elementKey, result.materials_spent);
        const remainingInventory = simulation.remaining;
        nextItems = { ...nextItems };

        for (const key of Object.keys(nextItems)) {
          if (key.toLowerCase().startsWith(tierPrefix) && !Object.prototype.hasOwnProperty.call(remainingInventory, key.toLowerCase())) {
            delete nextItems[key];
          }
        }

        for (const [key, value] of Object.entries(remainingInventory)) {
          nextItems[key] = value;
        }
      }

      nextItems[materialKey] = result.materials_remaining;
      base.items = nextItems;
    }

    base.materials_remaining = result.materials_remaining;
  }

  if (result && Object.prototype.hasOwnProperty.call(result, 'materials_remaining_units')) {
    base.materials_remaining_units = result.materials_remaining_units;
  }

  return base;
}

export function shouldRefreshRoster(result) {
  return !(result && Object.prototype.hasOwnProperty.call(result, 'items'));
}
