const registry = new Map();

const normalizeId = (value) => {
  if (value == null) return '';
  return String(value).trim();
};

const cloneMetadata = (metadata) => {
  if (!metadata || typeof metadata !== 'object') return {};
  if (typeof structuredClone === 'function') {
    return structuredClone(metadata);
  }
  try {
    return JSON.parse(JSON.stringify(metadata));
  } catch {
    return { ...metadata };
  }
};

export const clearCharacterMetadata = () => {
  registry.clear();
};

export const registerCharacterMetadata = (entries) => {
  if (!Array.isArray(entries)) return;
  for (const entry of entries) {
    if (!entry || typeof entry !== 'object') continue;
    const id = normalizeId(entry.id || entry.character_id || entry.name);
    if (!id) continue;
    const metadata = entry.ui && typeof entry.ui === 'object' ? entry.ui : null;
    if (!metadata) continue;
    registry.set(id, cloneMetadata(metadata));
  }
};

export const replaceCharacterMetadata = (entries) => {
  clearCharacterMetadata();
  registerCharacterMetadata(entries);
};

export const mergeCharacterMetadata = (id, metadata) => {
  const key = normalizeId(id);
  if (!key || !metadata || typeof metadata !== 'object') return;
  const existing = registry.get(key) || {};
  registry.set(key, { ...existing, ...metadata });
};

export const getCharacterMetadata = (id) => {
  const key = normalizeId(id);
  if (!key) return null;
  return registry.get(key) || null;
};
