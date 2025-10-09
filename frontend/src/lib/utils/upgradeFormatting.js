export const ITEM_UNIT_SCALE = Object.freeze({
  1: 1,
  2: 125,
  3: 125 ** 2,
  4: 125 ** 3
});

function parseMaterialTier(materialId) {
  if (!materialId) return null;
  const parts = String(materialId).trim().toLowerCase().split('_');
  const last = parts[parts.length - 1];
  const tier = Number.parseInt(last, 10);
  return Number.isFinite(tier) ? tier : null;
}

function normalizeMaterialId(value) {
  if (!value) return '';
  return String(value).trim().toLowerCase();
}

function titleCase(text) {
  if (!text) return '';
  return text.replace(/\b([a-z])/g, (m) => m.toUpperCase());
}

export function formatMaterialName(materialId) {
  const normalized = normalizeMaterialId(materialId);
  if (!normalized) return 'Unknown material';
  const [elementRaw, starRaw] = normalized.split('_');
  const element = titleCase(elementRaw || '');
  if (!starRaw) return element || 'Unknown material';
  const starValue = starRaw.replace(/[^0-9]/g, '');
  const starLabel = starValue ? `${Number(starValue)}★` : `${starRaw}★`;
  return `${element} ${starLabel}`.trim();
}

export function formatMaterialQuantity(count, materialId) {
  const num = Number(count);
  if (!Number.isFinite(num)) return '—';
  const prettyCount = Math.max(0, Math.round(num)).toLocaleString();
  const label = materialId ? formatMaterialName(materialId) : 'materials';
  return `${prettyCount}× ${label}`;
}

function normalizeBreakdown(breakdown) {
  if (!breakdown || typeof breakdown !== 'object') return {};
  const result = {};
  for (const [key, value] of Object.entries(breakdown)) {
    const qty = Number(value);
    if (!Number.isFinite(qty) || qty <= 0) continue;
    result[String(key)] = qty;
  }
  return result;
}

export function computeUnitsFromBreakdown(breakdown) {
  const normalized = normalizeBreakdown(breakdown);
  let total = 0;
  for (const [key, qty] of Object.entries(normalized)) {
    const tier = parseMaterialTier(key);
    if (!Number.isFinite(tier)) continue;
    const scale = ITEM_UNIT_SCALE[tier];
    if (!scale) continue;
    total += qty * scale;
  }
  return total;
}

export function prepareMaterialRequest(cost) {
  if (!cost || typeof cost !== 'object') return null;
  const breakdown = normalizeBreakdown(
    cost.breakdown || cost.per_tier || cost.materials || {}
  );
  let units = cost.units ?? cost.count ?? null;
  if (units != null) {
    const numeric = Number(units);
    if (Number.isFinite(numeric)) {
      units = numeric;
    } else {
      units = null;
    }
  }
  if (units == null && Object.keys(breakdown).length > 0) {
    units = computeUnitsFromBreakdown(breakdown);
  }
  if (units == null) return null;
  if (units < 0) return null;
  const payload = { units };
  if (Object.keys(breakdown).length > 0) {
    payload.breakdown = breakdown;
  }
  return payload;
}

export function extractElementBreakdown(items, elementKey) {
  if (!items) return {};
  const normalizedKey = String(elementKey || 'generic').toLowerCase();
  const prefix = `${normalizedKey}_`;
  const breakdown = {};
  for (const [id, count] of Object.entries(items)) {
    if (!id || !id.toLowerCase().startsWith(prefix)) continue;
    const qty = Number(count);
    if (!Number.isFinite(qty) || qty <= 0) continue;
    breakdown[id] = qty;
  }
  return breakdown;
}

export function formatCost(cost) {
  if (cost == null) return '—';
  if (typeof cost === 'number') {
    return formatMaterialQuantity(cost, null);
  }
  if (typeof cost === 'object') {
    const breakdown = normalizeBreakdown(cost.breakdown || cost.per_tier);
    if (Object.keys(breakdown).length > 0) {
      const entries = Object.entries(breakdown).sort((a, b) => {
        const tierA = parseMaterialTier(a[0]) ?? 0;
        const tierB = parseMaterialTier(b[0]) ?? 0;
        return tierB - tierA;
      });
      return entries
        .map(([materialId, qty]) => formatMaterialQuantity(qty, materialId))
        .join(' + ');
    }
    const { units, count, item, material, id } = cost;
    const materialId = item ?? material ?? id ?? null;
    const quantity = units ?? count;
    if (quantity != null) {
      return formatMaterialQuantity(quantity, materialId);
    }
  }
  return String(cost);
}

export function formatPercent(value) {
  if (value == null) return '0%';
  const num = Number(value) * 100;
  if (!Number.isFinite(num)) return '0%';
  let digits = 2;
  const abs = Math.abs(num);
  if (abs >= 100) digits = 0;
  else if (abs >= 10) digits = 1;
  let formatted = num.toFixed(digits);
  formatted = formatted.replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
  const sign = num >= 0 ? '+' : '';
  return `${sign}${formatted}%`;
}
