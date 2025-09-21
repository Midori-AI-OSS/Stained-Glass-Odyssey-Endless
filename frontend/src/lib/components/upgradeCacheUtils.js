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
    const elementKey = String(result.element || base.element || '').toLowerCase();
    if (elementKey) {
      const materialKey = `${elementKey}_1`;
      base.items = { ...(base.items || {}) };
      base.items[materialKey] = result.materials_remaining;
    }
    base.materials_remaining = result.materials_remaining;
  }

  return base;
}

export function shouldRefreshRoster(result) {
  return !(result && Object.prototype.hasOwnProperty.call(result, 'items'));
}
