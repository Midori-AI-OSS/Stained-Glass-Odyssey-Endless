// Enhanced asset loader for characters, backgrounds, and damage types

import { Flame, Snowflake, Zap, Sun, Moon, Wind, Circle } from 'lucide-svelte';

// Safely normalize a URL string coming from Vite globs
function normalizeUrl(src) {
  if (!src) return '';
  // If Vite already gave us an absolute or root-relative path, use it as-is.
  if (
    typeof src === 'string' &&
    (src.startsWith('http') || src.startsWith('blob:') || src.startsWith('data:') || src.startsWith('/'))
  ) {
    return src;
  }
  return new URL(src, import.meta.url).href;
}

// Load all character images (including folders and fallbacks)
// Note: do NOT guard import.meta.glob with typeof checks — Vite must
// statically analyze these calls to inline the module map at build time.
const characterModules = Object.fromEntries(
  Object.entries(
    import.meta.glob('../assets/characters/**/*.png', {
      eager: true,
      import: 'default',
      query: '?url'
    })
  ).map(([p, src]) => [p, normalizeUrl(src)])
);

const fallbackModules = Object.fromEntries(
  Object.entries(
    import.meta.glob('../assets/characters/fallbacks/*.png', {
      eager: true,
      import: 'default',
      query: '?url'
    })
  ).map(([p, src]) => [p, normalizeUrl(src)])
);

const backgroundModules = Object.fromEntries(
  Object.entries(
    import.meta.glob('../assets/backgrounds/*.png', {
      eager: true,
      import: 'default',
      query: '?url'
    })
  ).map(([p, src]) => [p, normalizeUrl(src)])
);

const lightstreamSwordModules = Object.fromEntries(
  Object.entries(
    import.meta.glob('../assets/**/lightstreamswords/**/*.png', {
      eager: true,
      import: 'default',
      query: '?url'
    })
  ).map(([p, src]) => [p, normalizeUrl(src)])
);

// Load DoT icons by element folder (e.g., ./assets/dots/fire/*.png)
const dotModules = Object.fromEntries(
  Object.entries(
    import.meta.glob('../assets/dots/*/*.png', {
      eager: true,
      import: 'default',
      query: '?url'
    })
  ).map(([p, src]) => [p, normalizeUrl(src)])
);

// Load effect icons by type folder (e.g., ./assets/effects/buffs/*.png)
const effectModules = Object.fromEntries(
  Object.entries(
    import.meta.glob('../assets/effects/*/*.png', {
      eager: true,
      import: 'default',
      query: '?url'
    })
  ).map(([p, src]) => [p, normalizeUrl(src)])
);

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

// Parse character assets into organized structure
const characterAssets = {};
const fallbackAssets = Object.values(fallbackModules);
const backgroundAssets = Object.values(backgroundModules);
const defaultFallback = normalizeUrl('../assets/midoriai-logo.png');
const DOT_DEFAULT = normalizeUrl('../assets/dots/generic/generic1.png');
const EFFECT_DEFAULT = normalizeUrl('../assets/effects/buffs/generic_buff.png');

// Organize character assets by character ID (folder or single file)
Object.keys(characterModules).forEach(p => {
  const match = p.match(/assets\/characters\/(.+?)\/(.+?)\.png$/) ||
                p.match(/assets\/characters\/(.+?)\.png$/);
  
  if (match) {
    const [, charId, fileName] = match;
    const actualCharId = fileName ? charId : charId.replace('.png', '');
    
    if (!characterAssets[actualCharId]) {
      characterAssets[actualCharId] = [];
    }

    // Skip fallbacks folder
    if (actualCharId !== 'fallbacks') {
      characterAssets[actualCharId].push(characterModules[p]);
    }
  }
});

// Seeded random function for consistent hourly backgrounds
function seededRandom(seed) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

// Get current hour seed (changes every hour)
function getHourSeed() {
  const now = new Date();
  return now.getFullYear() * 1000000 + 
         now.getMonth() * 10000 + 
         now.getDate() * 100 + 
         now.getHours();
}

// Known folder aliases when the on-disk folder name differs from character id
const CHARACTER_ASSET_ALIASES = {
  lady_echo: 'echo'
};

// Helper: resolve asset key for a given character id (handles aliases/patterns)
function resolveCharacterKey(characterId) {
  let key = CHARACTER_ASSET_ALIASES[characterId] || characterId;
  if (typeof key === 'string' && key.startsWith('jellyfish_')) key = 'jellyfish';
  return key;
}

// Get image from character folder or fallback
export function getCharacterImage(characterId, _isPlayer = false) {
  if (!characterId) return defaultFallback;

  // Resolve folder alias when id differs from asset folder
  let key = resolveCharacterKey(characterId);

  // If this is the Mimic, always mirror the Player's chosen image for this session
  if (characterId === 'mimic') {
    // Return cached player image if present
    const cachedPlayer = characterImageCache.get('player');
    if (cachedPlayer) return cachedPlayer;
    // Otherwise, choose and cache the player's image using the same rules
    const playerList = characterAssets['player'];
    if (Array.isArray(playerList) && playerList.length > 0) {
      const rnd = Math.floor(Math.random() * playerList.length);
      const chosen = playerList[rnd];
      characterImageCache.set('player', chosen);
      return chosen;
    }
    if (fallbackAssets.length > 0) {
      const rnd = Math.floor(Math.random() * fallbackAssets.length);
      const chosen = fallbackAssets[rnd];
      characterImageCache.set('player', chosen);
      return chosen;
    }
    characterImageCache.set('player', defaultFallback);
    return defaultFallback;
  }

  // First, return any cached image (prevents reload flicker on re-renders)
  const cached = characterImageCache.get(characterId);
  if (cached) return cached;

  // Player/Lady Echo: random-once-per-page-load (session-cached)
  if (_isPlayer === true || characterId === 'lady_echo') {
    const list = characterAssets[key];
    if (Array.isArray(list) && list.length > 0) {
      const rnd = Math.floor(Math.random() * list.length);
      const chosen = list[rnd];
      characterImageCache.set(characterId, chosen);
      return chosen;
    }
    if (fallbackAssets.length > 0) {
      const rnd = Math.floor(Math.random() * fallbackAssets.length);
      const chosen = fallbackAssets[rnd];
      characterImageCache.set(characterId, chosen);
      return chosen;
    }
    characterImageCache.set(characterId, defaultFallback);
    return defaultFallback;
  }

  // Any character with a folder/gallery: random-once-per-page-load (session-cached)
  if (characterAssets[key] && characterAssets[key].length > 0) {
    const images = characterAssets[key];
    if (images.length > 1) {
      const rnd = Math.floor(Math.random() * images.length);
      const chosen = images[rnd];
      characterImageCache.set(characterId, chosen);
      return chosen;
    }
    // Single image in folder — just use it
    const chosen = images[0];
    characterImageCache.set(characterId, chosen);
    return chosen;
  }

  if (fallbackAssets.length > 0) {
    const idx = stringHashIndex(characterId, fallbackAssets.length);
    const chosen = fallbackAssets[idx];
    characterImageCache.set(characterId, chosen);
    return chosen;
  }

  characterImageCache.set(characterId, defaultFallback);
  return defaultFallback;
}

// Get background with hourly consistency
export function getHourlyBackground() {
  if (backgroundAssets.length === 0) return defaultFallback;
  
  const seed = getHourSeed();
  const randomIndex = Math.floor(seededRandom(seed) * backgroundAssets.length);
  return backgroundAssets[randomIndex];
}

// Get random background (for immediate random needs)
export function getRandomBackground() {
  if (backgroundAssets.length === 0) return defaultFallback;

  const randomIndex = Math.floor(Math.random() * backgroundAssets.length);
  return backgroundAssets[randomIndex];
}

// Get all available character IDs
export function getAvailableCharacterIds() {
  return Object.keys(characterAssets);
}

// Get random fallback image
export function getRandomFallback() {
  if (fallbackAssets.length === 0) return defaultFallback;

  const randomIndex = Math.floor(Math.random() * fallbackAssets.length);
  return fallbackAssets[randomIndex];
}

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

// Build DoT assets map: { fire: [urls...], ice: [...], ... }
const dotAssets = (() => {
  const map = {
    fire: [],
    ice: [],
    lightning: [],
    light: [],
    dark: [],
    wind: [],
    generic: []
  };
  for (const [p, url] of Object.entries(dotModules)) {
    const m = p.match(/assets\/dots\/(\w+)\//);
    const key = (m?.[1] || 'generic').toLowerCase();
    if (!map[key]) map[key] = [];
    map[key].push(url);
  }
  return map;
})();

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
    if (alias) return alias;
    const normalized = normalizeDamageTypeId(token);
    if (normalized && normalized !== 'generic') {
      return normalized;
    }
  }
  return 'generic';
}

const lightstreamSwordAssets = (() => {
  const map = {
    fire: [],
    ice: [],
    lightning: [],
    light: [],
    dark: [],
    wind: [],
    generic: []
  };
  for (const [p, url] of Object.entries(lightstreamSwordModules)) {
    const element = inferSwordElementFromPath(p);
    if (!map[element]) map[element] = [];
    map[element].push(url);
  }
  return map;
})();

function ensureSwordList(element) {
  const key = normalizeDamageTypeId(element);
  const list = lightstreamSwordAssets[key];
  if (Array.isArray(list) && list.length) return list;
  const generic = lightstreamSwordAssets.generic || [];
  return generic.length ? generic : [];
}

export function getLightstreamSwordArt(typeId, options = {}) {
  const key = normalizeDamageTypeId(typeId);
  const list = ensureSwordList(key);
  if (!list.length) {
    return defaultFallback;
  }
  const seed = String(options.seed || '') || key;
  const idx = stringHashIndex(`${key}:${seed}`, list.length);
  return list[idx] || list[0];
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

// Build Effect assets map: { buffs: {name: url, ...}, debuffs: {name: url, ...} }
const effectAssets = (() => {
  const map = {
    buffs: {},
    debuffs: {}
  };
  for (const [p, url] of Object.entries(effectModules)) {
    const m = p.match(/assets\/effects\/(\w+)\/(\w+)\.png$/);
    if (m) {
      const [, type, name] = m;
      const effectType = type.toLowerCase();
      const effectName = name.toLowerCase();
      if (!map[effectType]) map[effectType] = {};
      map[effectType][effectName] = url;
    }
  }
  return map;
})();

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
  const list = dotAssets[element] || dotAssets.generic || [];
  if (list.length === 0) return DOT_DEFAULT || defaultFallback;
  const idx = stringHashIndex(key || element, list.length);
  return list[idx] || DOT_DEFAULT || defaultFallback;
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
    return EFFECT_DEFAULT || defaultFallback;
  }
  
  const effectType = inferEffectType(effect);
  const iconName = getEffectIconName(effect);
  
  // Try to find the specific icon
  const iconUrl = effectAssets[effectType]?.[iconName];
  if (iconUrl) return iconUrl;
  
  // Fall back to generic for this effect type
  const genericIcon = effectType === 'debuffs' ? 'generic_debuff' : 'generic_buff';
  const genericUrl = effectAssets[effectType]?.[genericIcon];
  if (genericUrl) return genericUrl;
  
  // Final fallback
  return EFFECT_DEFAULT || defaultFallback;
}

// Export assets for debugging
export { characterAssets, fallbackAssets, backgroundAssets, effectAssets };

// Internal: cache and helpers for stable image selection
const characterImageCache = new Map();

function stringHashIndex(str, modulo) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (h << 5) - h + str.charCodeAt(i);
    h |= 0;
  }
  const idx = Math.abs(h) % Math.max(modulo, 1);
  return idx;
}

export function clearCharacterImageCache() {
  characterImageCache.clear();
}

// Public: whether a character has a gallery (more than one image) available
export function hasCharacterGallery(characterId) {
  if (!characterId) return false;
  const key = resolveCharacterKey(characterId);
  const list = characterAssets[key];
  return Array.isArray(list) && list.length > 1;
}

// Public: advance cached character image to the next one in its gallery
// Returns the chosen image url (or current one if no change)
export function advanceCharacterImage(characterId) {
  if (!characterId) return defaultFallback;
  const key = resolveCharacterKey(characterId);
  const list = characterAssets[key];
  if (!Array.isArray(list) || list.length === 0) {
    return characterImageCache.get(characterId) || getCharacterImage(characterId);
  }
  // Determine current index by cache or selection rule
  const current = characterImageCache.get(characterId) || getCharacterImage(characterId);
  let idx = list.indexOf(current);
  if (idx < 0) idx = 0;
  const nextIdx = (idx + 1) % list.length;
  const next = list[nextIdx];
  characterImageCache.set(characterId, next);
  return next;
}
