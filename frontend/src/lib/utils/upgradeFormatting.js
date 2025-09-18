export function formatPoints(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '—';
  return Math.max(0, Math.round(num)).toLocaleString();
}

export function formatCost(value) {
  const points = formatPoints(value);
  return points === '—' ? '—' : `${points} pts`;
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
