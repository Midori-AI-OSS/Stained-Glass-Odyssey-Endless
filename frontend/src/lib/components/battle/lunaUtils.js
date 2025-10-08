export function isCandidateLuna(value) {
  if (value === undefined || value === null) return false;
  let text;
  try {
    text = String(value).trim();
  } catch {
    return false;
  }
  if (!text) return false;
  const normalized = text.toLowerCase();
  if (normalized === 'luna') return true;
  const compact = normalized.replace(/[^a-z]/g, '');
  if (compact === 'luna') return true;
  const underscored = normalized.replace(/[^a-z0-9]+/g, '_');
  if (underscored === 'luna') return true;
  if (underscored.startsWith('luna_')) return true;
  return underscored.includes('luna_sword');
}
