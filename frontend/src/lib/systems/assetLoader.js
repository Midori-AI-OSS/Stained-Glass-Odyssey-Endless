// Enhanced asset loader for characters, backgrounds, and damage types

import { Flame, Snowflake, Zap, Sun, Moon, Wind, Circle } from 'lucide-svelte';

import {
  advanceCharacterImage as registryAdvanceCharacterImage,
  clearCharacterImageCache as registryClearCharacterImageCache,
  getAssetRegistryVersion,
  getAvailableCharacterIds as registryGetAvailableCharacterIds,
  getAvailableSummonIds,
  getCharacterImage as registryGetCharacterImage,
  getDefaultFallback,
  getHourlyBackground as registryGetHourlyBackground,
  getPortraitRarityFolders,
  getRandomBackground as registryGetRandomBackground,
  getRandomFallback as registryGetRandomFallback,
  getRewardArt,
  getSummonArt as registryGetSummonArt,
  getSummonGallery,
  getGlyphArt,
  getMaterialFallbackIcon,
  getMaterialIcon,
  getDotVariantPool,
  getDotFallback,
  getEffectIconUrl,
  getEffectFallback,
  hasCharacterGallery as registryHasCharacterGallery,
  onMaterialIconError,
  registerAssetManifest,
  registerAssetMetadata,
  resetAssetRegistryOverrides,
  stringHashIndex
} from './assetRegistry.js';

export {
  registryAdvanceCharacterImage as advanceCharacterImage,
  registryClearCharacterImageCache as clearCharacterImageCache,
  registryGetAvailableCharacterIds as getAvailableCharacterIds,
  registryGetCharacterImage as getCharacterImage,
  registryGetHourlyBackground as getHourlyBackground,
  registryGetRandomBackground as getRandomBackground,
  registryGetRandomFallback as getRandomFallback,
  getRewardArt,
  getGlyphArt,
  getMaterialIcon,
  getMaterialFallbackIcon,
  onMaterialIconError,
  registryHasCharacterGallery as hasCharacterGallery,
  registryGetSummonArt as getSummonArt,
  getPortraitRarityFolders,
  registerAssetManifest,
  registerAssetMetadata,
  resetAssetRegistryOverrides,
  getDefaultFallback,
  getSummonGallery,
  getAvailableSummonIds,
  stringHashIndex
};

const ELEMENT_ICONS = {
  fire: Flame,
  ice: Snowflake,
  lightning: Zap,
  light: Sun,
  dark: Moon,
  wind: Wind,
  generic: Circle
};

const ELEMENT_COLORS = {
  // Fire closer to a vivid red for better readability
  fire: '#ff3b30',
  ice: '#82caff',
  lightning: '#ffd700',
  light: '#ffff99',
  dark: '#8a2be2',
  wind: '#7fff7f',
  generic: '#cccccc'
};

const DAMAGE_TYPE_ALIASES = {
  none: 'generic',
  neutral: 'generic',
  holy: 'light',
  shadow: 'dark',
  lightning: 'lightning',
  electric: 'lightning',
  thunder: 'lightning',
  frost: 'ice',
  ice: 'ice',
  water: 'ice',
  flame: 'fire',
  fire: 'fire',
  wind: 'wind',
  air: 'wind',
};

const SWORD_KEYWORD_ALIASES = {
  bolt: 'lightning',
  bolts: 'lightning',
  charge: 'lightning',
  crimson: 'fire',
  ember: 'fire',
  embers: 'fire',
  flame: 'fire',
  flames: 'fire',
  flare: 'fire',
  frost: 'ice',
  glaive: 'generic',
  glimmer: 'light',
  glow: 'light',
  green: 'wind',
  ice: 'ice',
  lightning: 'lightning',
  lightstream: 'light',
  luna: 'dark',
  lunar: 'dark',
  moon: 'dark',
  radiant: 'light',
  shadow: 'dark',
  shock: 'lightning',
  spark: 'lightning',
  storm: 'lightning',
  sun: 'light',
  tempest: 'wind',
  verdant: 'wind',
  white: 'light',
  wind: 'wind'
};

const LIGHTSTREAM_SWORD_ELEMENTS = new Set([
  'fire',
  'ice',
  'lightning',
  'light',
  'dark',
  'wind'
]);

export function normalizeDamageTypeId(typeId) {
  if (!typeId) return 'generic';
  const lowered = String(typeId).trim().toLowerCase();
  if (!lowered) return 'generic';
  return DAMAGE_TYPE_ALIASES[lowered] || lowered;
}

function clampByte(value) {
  return Math.min(255, Math.max(0, Math.round(value)));
}

function mixChannel(channel, target, ratio) {
  return clampByte(channel + (target - channel) * ratio);
}

function shiftColor(hex, ratio) {
  if (typeof hex !== 'string') return '#cccccc';
  const normalized = hex.replace('#', '');
  if (!/^[0-9a-fA-F]{6}$/.test(normalized)) {
    return '#cccccc';
  }
  const value = parseInt(normalized, 16);
  let r = (value >> 16) & 0xff;
  let g = (value >> 8) & 0xff;
  let b = value & 0xff;
  if (ratio > 0) {
    r = mixChannel(r, 255, ratio);
    g = mixChannel(g, 255, ratio);
    b = mixChannel(b, 255, ratio);
  } else if (ratio < 0) {
    const amount = Math.abs(ratio);
    r = mixChannel(r, 0, amount);
    g = mixChannel(g, 0, amount);
    b = mixChannel(b, 0, amount);
  }
  const combined = (r << 16) | (g << 8) | b;
  return `#${combined.toString(16).padStart(6, '0')}`;
}

const defaultFallback = getDefaultFallback();
export function getElementIcon(element) {
  return ELEMENT_ICONS[(element || '').toLowerCase()] || Circle;
}

export function getElementColor(element) {
  return ELEMENT_COLORS[(element || '').toLowerCase()] || '#aaa';
}

export function getDamageTypeIcon(typeId) {
  const key = normalizeDamageTypeId(typeId);
  return ELEMENT_ICONS[key] || Circle;
}

export function getDamageTypeColor(typeId, options = {}) {
  const key = normalizeDamageTypeId(typeId);
  const base = ELEMENT_COLORS[key] || '#cccccc';
  const variant = (options.variant || '').toLowerCase();
  if (variant === 'heal' || variant === 'hot' || variant === 'buff') {
    return shiftColor(base, 0.4);
  }
  if (variant === 'dot' || variant === 'drain') {
    return shiftColor(base, -0.25);
  }
  return base;
}

export function getDamageTypeVisual(typeId, options = {}) {
  return {
    icon: getDamageTypeIcon(typeId),
    color: getDamageTypeColor(typeId, options)
  };
}

function tokenizeSwordPath(path) {
  const tokens = [];
  if (!path) return tokens;
  try {
    const parts = path.split('/');
    const idx = parts.findIndex(part => part.toLowerCase().includes('lightstreamswords'));
    if (idx >= 0) {
      if (parts[idx + 1]) {
        tokens.push(...parts[idx + 1].split(/[^a-zA-Z0-9]+/));
      }
      if (parts[idx + 2]) {
        tokens.push(...parts[idx + 2].split(/[^a-zA-Z0-9]+/));
      }
    }
    const file = parts[parts.length - 1] || '';
    const stem = file.replace(/\.png$/i, '');
    tokens.push(...stem.split(/[^a-zA-Z0-9]+/));
  } catch {}
  return tokens
    .map(token => token?.toLowerCase?.() || '')
    .filter(Boolean);
}

function inferSwordElementFromPath(path) {
  const tokens = tokenizeSwordPath(path);
  for (const token of tokens) {
    const alias = SWORD_KEYWORD_ALIASES[token];
    if (alias && LIGHTSTREAM_SWORD_ELEMENTS.has(alias)) {
      return alias;
    }
    const normalized = normalizeDamageTypeId(token);
    if (LIGHTSTREAM_SWORD_ELEMENTS.has(normalized)) {
      return normalized;
    }
  }
  return 'generic';
}

let cachedSwordAssets;
let cachedSwordVersion = -1;

function buildLightstreamSwordAssets() {
  const version = getAssetRegistryVersion();
  if (cachedSwordAssets && cachedSwordVersion === version) {
    return cachedSwordAssets;
  }
  const map = {
    fire: [],
    ice: [],
    lightning: [],
    light: [],
    dark: [],
    wind: [],
    generic: []
  };
  const pooled = new Set();
  for (const url of map.generic) {
    if (typeof url === 'string' && url) {
      pooled.add(url);
    }
  }
  const entries = getSummonGallery('lightstreamswords');
  for (const entry of entries) {
    const url = entry?.url;
    if (!url) continue;
    let element = entry?.metadata?.element
      ? normalizeDamageTypeId(entry.metadata.element)
      : inferSwordElementFromPath(entry.path || entry.url);
    if (!LIGHTSTREAM_SWORD_ELEMENTS.has(element)) {
      element = 'generic';
    }
    if (!map[element]) map[element] = [];
    if (!map[element].includes(url)) {
      map[element].push(url);
    }
    pooled.add(url);
    const fallbackElements = Array.isArray(entry?.metadata?.fallbackElements)
      ? entry.metadata.fallbackElements
      : [];
    for (const extra of fallbackElements) {
      const normalized = normalizeDamageTypeId(extra);
      if (!normalized || !map[normalized]) continue;
      if (!map[normalized].includes(url)) {
        map[normalized].push(url);
      }
    }
  }
  map.generic = Array.from(pooled);
  cachedSwordAssets = map;
  cachedSwordVersion = version;
  return map;
}

function ensureSwordList(element) {
  const map = buildLightstreamSwordAssets();
  const key = normalizeDamageTypeId(element);
  const list = map[key];
  if (Array.isArray(list) && list.length) return list;
  const generic = map.generic || [];
  return generic.length ? generic : [];
}

export function getLightstreamSwordArt(typeId, options = {}) {
  const key = normalizeDamageTypeId(typeId);
  const list = ensureSwordList(key);
  if (!list.length) {
    return '';
  }
  const seed = String(options.seed || '') || key;
  const idx = stringHashIndex(`${key}:${seed}`, list.length);
  const art = list[idx] || list[0] || '';
  if (!art || art === defaultFallback) {
    return '';
  }
  return art;
}

export function getDamageTypePalette(typeId) {
  const key = normalizeDamageTypeId(typeId);
  const base = getDamageTypeColor(key);
  return {
    base,
    highlight: shiftColor(base, 0.35),
    shadow: shiftColor(base, -0.35)
  };
}

export function getLightstreamSwordVisual(typeId, options = {}) {
  const element = normalizeDamageTypeId(typeId);
  const art = getLightstreamSwordArt(element, options);
  const palette = getDamageTypePalette(element);
  return {
    art,
    element,
    color: palette.base,
    palette
  };
}

// Internal helper to infer an element from a DoT id/name
function inferElementFromKey(key) {
  const k = String(key || '').toLowerCase();
  if (k.includes('lightning')) return 'lightning';
  if (k.includes('fire')) return 'fire';
  if (k.includes('ice')) return 'ice';
  if (k.includes('light')) return 'light';
  if (k.includes('dark')) return 'dark';
  if (k.includes('wind')) return 'wind';
  return 'generic';
}

// Public: return inferred element for a DoT effect object or id
export function getDotElement(effect) {
  try {
    if (effect && typeof effect === 'object') {
      const candidate = effect.element || effect.damage_type || effect.type;
      if (candidate) return String(candidate).toLowerCase();
    }
  } catch {}
  const key = typeof effect === 'object' ? effect?.id : effect;
  return inferElementFromKey(key);
}

// Choose a DoT icon based on an effect object or id
// Falls back to generic if no themed match is found.
export function getDotImage(effect) {
  const key = String((typeof effect === 'object' ? effect?.id : effect) || '').toLowerCase();
  let element = '';
  try {
    if (effect && typeof effect === 'object') {
      element = String(effect.element || effect.damage_type || effect.type || '').toLowerCase();
    }
  } catch {}
  if (!element) element = inferElementFromKey(key);
  const list = getDotVariantPool(element);
  const fallback = getDotFallback() || defaultFallback;
  if (list.length === 0) return fallback;
  const idx = stringHashIndex(key || element, list.length);
  return list[idx] || fallback;
}

// Internal helper to infer effect type (buff vs debuff) from modifiers
function inferEffectType(effect) {
  if (!effect || typeof effect !== 'object') return 'buffs';
  
  const modifiers = effect.modifiers || effect.stat_modifiers || {};
  
  // Check if any modifier is negative (debuff) or positive (buff)
  for (const [, value] of Object.entries(modifiers)) {
    if (typeof value === 'number') {
      if (value < 0) return 'debuffs';
      if (value > 0) return 'buffs';
    }
  }
  
  // Default to buffs if we can't determine
  return 'buffs';
}

// Internal helper to get effect name for icon mapping
function getEffectIconName(effect) {
  if (!effect || typeof effect !== 'object') return 'generic_buff';
  
  const name = String(effect.name || effect.id || '').toLowerCase();
  
  // Map specific effect names to icon names
  const nameMap = {
    'aftertaste': 'aftertaste',
    'critical_boost': 'critical_boost',
    'attack_up': 'attack_up',
    'defense_up': 'defense_up',
    'defense_down': 'defense_down',
    'vitality_up': 'vitality_up',
    'mitigation_up': 'mitigation_up'
  };
  
  // Check for exact matches first
  if (nameMap[name]) return nameMap[name];
  
  // Check for partial matches
  for (const [key, icon] of Object.entries(nameMap)) {
    if (name.includes(key.replace('_', ''))) return icon;
  }
  
  // Check modifiers to guess icon type
  const modifiers = effect.modifiers || effect.stat_modifiers || {};
  for (const [stat, value] of Object.entries(modifiers)) {
    if (stat === 'atk' || stat === 'attack') return value > 0 ? 'attack_up' : 'attack_down';
    if (stat === 'defense' || stat === 'def') return value > 0 ? 'defense_up' : 'defense_down';
    if (stat === 'vitality') return 'vitality_up';
    if (stat === 'mitigation') return 'mitigation_up';
  }
  
  // Fall back to generic based on effect type
  const effectType = inferEffectType(effect);
  return effectType === 'debuffs' ? 'generic_debuff' : 'generic_buff';
}

// Choose an effect icon based on an effect object
// Falls back to generic buff/debuff if no specific icon is found.
export function getEffectImage(effect) {
  if (!effect || typeof effect !== 'object') {
    return getEffectFallback('buffs') || defaultFallback;
  }

  const effectType = inferEffectType(effect);
  const iconName = getEffectIconName(effect);

  // Try to find the specific icon
  const iconUrl = getEffectIconUrl(effectType, iconName);
  if (iconUrl) return iconUrl;

  // Fall back to generic for this effect type
  const genericIcon = effectType === 'debuffs' ? 'generic_debuff' : 'generic_buff';
  const genericUrl = getEffectIconUrl(effectType, genericIcon);
  if (genericUrl) return genericUrl;

  // Final fallback
  const fallback = getEffectFallback(effectType) || getEffectFallback('buffs');
  return fallback || defaultFallback;
}
