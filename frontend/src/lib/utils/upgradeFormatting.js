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

export function formatCost(cost) {
  if (cost == null) return '—';
  if (typeof cost === 'number') {
    return formatMaterialQuantity(cost, null);
  }
  if (typeof cost === 'object') {
    const { count, item, material, id } = cost;
    const materialId = item ?? material ?? id ?? null;
    return formatMaterialQuantity(count, materialId);
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
