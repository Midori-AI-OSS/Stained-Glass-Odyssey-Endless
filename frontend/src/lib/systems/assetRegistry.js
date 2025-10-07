// Centralized asset registry for portraits, summons, backgrounds, and fallbacks.
// This module normalizes asset URLs, manages caches, and exposes hooks so
// metadata payloads can override on-disk resources without touching callers.

import { getCharacterMetadata } from './characterMetadata.js';

const TELEMETRY_EVENT_NAME = 'autofighter:asset-registry';
let telemetryListener = null;
const telemetryCache = new Set();

export const setAssetRegistryTelemetry = handler => {
  telemetryListener = typeof handler === 'function' ? handler : null;
};

export const resetAssetRegistryTelemetry = () => {
  telemetryCache.clear();
};

const emitTelemetry = (kind, detail = {}, options = {}) => {
  const payload = {
    kind,
    detail: { ...detail },
    timestamp: Date.now()
  };
  const defaultKeyParts = [kind, detail?.id ?? detail?.key ?? detail?.type ?? '', detail?.reason ?? ''];
  const onceKey = options.onceKey === false ? null : options.onceKey || defaultKeyParts.join(':');
  if (onceKey) {
    if (telemetryCache.has(onceKey)) {
      return;
    }
    telemetryCache.add(onceKey);
  }
  if (telemetryListener) {
    try {
      telemetryListener(payload);
    } catch (error) {
      try {
        console.error('[assetRegistry] telemetry handler failed', error);
      } catch {}
    }
  }
  try {
    if (
      typeof window !== 'undefined' &&
      typeof window.dispatchEvent === 'function' &&
      typeof window.CustomEvent === 'function'
    ) {
      window.dispatchEvent(new window.CustomEvent(TELEMETRY_EVENT_NAME, { detail: payload }));
    }
  } catch {}
  try {
    console.warn(`[assetRegistry] ${kind}`, payload);
  } catch {}
};

const normalizeAssetUrl = src => {
  if (!src) return '';
  if (
    typeof src === 'string' &&
    (src.startsWith('http') ||
      src.startsWith('blob:') ||
      src.startsWith('data:') ||
      src.startsWith('/'))
  ) {
    return src;
  }
  return new URL(src, import.meta.url).href;
};

const globOrEmpty = (factory, fallbackFactory) => {
  if (typeof factory === 'function') {
    try {
      return factory();
    } catch {}
  }
  if (typeof globalThis.__assetRegistryGlob === 'function' && typeof fallbackFactory === 'function') {
    try {
      return fallbackFactory(globalThis.__assetRegistryGlob) || {};
    } catch {}
  }
  return {};
};

const createModuleMap = modules =>
  Object.fromEntries(
    Object.entries(modules).map(([path, value]) => [path, normalizeAssetUrl(value)])
  );

const characterModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/characters/**/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/characters/**/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const fallbackModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/characters/fallbacks/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/characters/fallbacks/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const backgroundModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/backgrounds/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/backgrounds/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const summonModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/summons/**/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/summons/**/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const cardArtModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/cards/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/cards/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const relicArtModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/relics/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/relics/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const materialIconModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/items/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/items/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const dotModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/dots/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/dots/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const effectModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/effects/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/effects/*/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const cardGlyphModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/cards/Art/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/cards/Art/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const relicGlyphModules = createModuleMap(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/relics/Art/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      }),
    glob =>
      glob('../assets/relics/Art/*.png', {
        eager: true,
        import: 'default',
        query: '?url'
      })
  )
);

const musicModules = Object.entries(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/music/**/*.{mp3,ogg,wav}', {
        eager: true,
        as: 'url'
      }),
    glob =>
      glob('../assets/music/**/*.{mp3,ogg,wav}', {
        eager: true,
        as: 'url'
      })
  )
).reduce((acc, [path, url]) => {
  acc[path] = normalizeAssetUrl(url);
  return acc;
}, {});

const sfxModules = Object.entries(
  globOrEmpty(
    () =>
      import.meta.glob('../assets/sfx/**/*.{mp3,ogg,wav}', {
        eager: true,
        as: 'url'
      }),
    glob =>
      glob('../assets/sfx/**/*.{mp3,ogg,wav}', {
        eager: true,
        as: 'url'
      })
  )
).reduce((acc, [path, url]) => {
  acc[path] = normalizeAssetUrl(url);
  return acc;
}, {});

const STATIC_FALLBACK = normalizeAssetUrl('../assets/midoriai-logo.png');
const DEFAULT_CARD_FALLBACK = normalizeAssetUrl('../assets/cards/gray/bg_attack_default_gray2.png');
const DEFAULT_RELIC_FALLBACK = normalizeAssetUrl('../assets/relics/fallback/placeholder.png');
const DEFAULT_ITEM_FALLBACK = normalizeAssetUrl('../assets/items/generic/generic1.png');
const DEFAULT_DOT_FALLBACK = normalizeAssetUrl('../assets/dots/generic/generic1.png');
const DEFAULT_EFFECT_BUFF_FALLBACK = normalizeAssetUrl('../assets/effects/buffs/generic_buff.png');
const DEFAULT_EFFECT_DEBUFF_FALLBACK = normalizeAssetUrl('../assets/effects/debuffs/generic_debuff.png');

const portraitGalleries = new Map(); // normalized id -> string[] urls
const portraitCanonicals = new Map(); // normalized id -> canonical id

const addPortraitEntry = (canonicalId, url) => {
  const normalized = canonicalId.toLowerCase();
  if (!portraitGalleries.has(normalized)) {
    portraitGalleries.set(normalized, []);
  }
  portraitGalleries.get(normalized).push(url);
  if (!portraitCanonicals.has(normalized)) {
    portraitCanonicals.set(normalized, canonicalId);
  }
};

Object.entries(characterModules).forEach(([path, url]) => {
  const match = path.replace(/..\/assets\/characters\//, '');
  const segments = match.split('/');
  if (!segments.length) return;
  if (segments[0] === 'fallbacks') return;
  if (segments.length === 1) {
    const stem = segments[0].replace(/\.png$/i, '');
    addPortraitEntry(stem, url);
    return;
  }
  const folder = segments[0];
  addPortraitEntry(folder, url);
});

const fallbackPool = Object.values(fallbackModules);
const backgroundPool = Object.values(backgroundModules);

const summonGalleries = new Map(); // normalized id -> [{ url, path, origin, metadata }]
const summonCanonicals = new Map();

const addSummonEntry = (key, entry) => {
  const normalized = key.toLowerCase();
  if (!summonGalleries.has(normalized)) {
    summonGalleries.set(normalized, []);
  }
  summonGalleries.get(normalized).push(entry);
  if (!summonCanonicals.has(normalized)) {
    summonCanonicals.set(normalized, key);
  }
};

Object.entries(summonModules).forEach(([path, url]) => {
  const match = path.match(/assets\/summons\/([^/]+)/i);
  if (!match) return;
  const key = match[1];
  addSummonEntry(key, {
    key,
    url,
    path,
    origin: 'disk',
    metadata: {}
  });
});

const normalizeKey = value => {
  if (value == null) return '';
  const key = String(value).trim().toLowerCase();
  return key;
};

const normalizeDotElement = value => normalizeKey(value) || 'generic';

const dotIndex = (() => {
  const elements = new Map();
  let fallback = DEFAULT_DOT_FALLBACK || STATIC_FALLBACK;
  Object.entries(dotModules).forEach(([path, url]) => {
    if (!url) return;
    const match = path.match(/assets\/dots\/([^/]+)/i);
    const element = normalizeDotElement(match?.[1]);
    if (!elements.has(element)) {
      elements.set(element, []);
    }
    elements.get(element).push(url);
    if (element === 'generic' && (!fallback || fallback === STATIC_FALLBACK)) {
      fallback = url;
    }
  });
  if (!fallback) {
    fallback = STATIC_FALLBACK;
  }
  return { elements, fallback };
})();

export const getDotVariantPool = element => {
  const key = normalizeDotElement(element);
  const pool = dotIndex.elements.get(key) ?? [];
  return [...pool];
};

export const getDotFallback = () => dotIndex.fallback || STATIC_FALLBACK;

const normalizeEffectType = value => {
  const key = normalizeKey(value);
  if (!key) return 'buffs';
  if (key === 'debuff' || key === 'debuffs' || key === 'negative') return 'debuffs';
  return 'buffs';
};

const effectIndex = (() => {
  const types = new Map();
  const fallback = {
    buffs: DEFAULT_EFFECT_BUFF_FALLBACK || STATIC_FALLBACK,
    debuffs: DEFAULT_EFFECT_DEBUFF_FALLBACK || DEFAULT_EFFECT_BUFF_FALLBACK || STATIC_FALLBACK
  };
  Object.entries(effectModules).forEach(([path, url]) => {
    if (!url) return;
    const match = path.match(/assets\/effects\/([^/]+)\/([^/]+)\.png$/i);
    if (!match) return;
    const [, rawType, rawName] = match;
    const type = normalizeEffectType(rawType);
    const name = normalizeKey(rawName);
    if (!types.has(type)) {
      types.set(type, new Map());
    }
    types.get(type).set(name, url);
    if (type === 'buffs' && name === 'generic_buff') {
      fallback.buffs = url;
    }
    if (type === 'debuffs' && name === 'generic_debuff') {
      fallback.debuffs = url;
    }
  });
  if (!fallback.buffs) {
    fallback.buffs = DEFAULT_EFFECT_BUFF_FALLBACK || STATIC_FALLBACK;
  }
  if (!fallback.debuffs) {
    fallback.debuffs = DEFAULT_EFFECT_DEBUFF_FALLBACK || fallback.buffs;
  }
  return { types, fallback };
})();

export const getEffectIconUrl = (type, name) => {
  const normalizedType = normalizeEffectType(type);
  const normalizedName = normalizeKey(name);
  if (!normalizedName) return null;
  const bucket = effectIndex.types.get(normalizedType);
  if (!bucket) return null;
  return bucket.get(normalizedName) ?? null;
};

export const getEffectFallback = type => {
  const normalizedType = normalizeEffectType(type);
  return effectIndex.fallback[normalizedType] ?? effectIndex.fallback.buffs;
};

const normalizeMusicCategory = (category, fallback = 'other') => {
  const normalized = normalizeKey(category);
  if (!normalized) return fallback;
  switch (normalized) {
    case 'fallback':
      return fallback;
    case 'default':
      return 'normal';
    default:
      return normalized;
  }
};

const ensureMusicLibrary = (library, key) => {
  if (!library.has(key)) {
    library.set(key, {
      categories: new Map(),
      defaultCategory: 'normal'
    });
  }
  return library.get(key);
};

const musicLibrary = new Map();
const fallbackMusicLibrary = new Map();
const fallbackMusicPool = [];
const musicTrackMetadataDisk = new Map();
const musicTrackMetadataOverrides = new Map();

const recordDiskMusicMetadata = (url, metadata = {}) => {
  if (!url) return;
  const key = String(url);
  if (!key) return;
  const existing = musicTrackMetadataDisk.get(key) || {};
  musicTrackMetadataDisk.set(key, { ...existing, ...metadata, origin: 'disk' });
};

const recordOverrideMusicMetadata = (url, metadata = {}) => {
  if (!url) return;
  const key = String(url);
  if (!key) return;
  const existing = musicTrackMetadataOverrides.get(key) || {};
  musicTrackMetadataOverrides.set(key, { ...existing, ...metadata, origin: 'metadata' });
};

const clearOverrideMusicMetadata = () => {
  musicTrackMetadataOverrides.clear();
};

Object.entries(musicModules).forEach(([path, url]) => {
  const segments = path.replace(/..\/assets\/music\//, '').split('/');
  if (segments.length === 0) return;
  const character = normalizeKey(segments[0]);
  if (!character) return;
  const fileCategory = segments.length > 2 ? segments[1] : null;
  if (character === 'fallback') {
    const category = normalizeMusicCategory(fileCategory, 'normal');
    if (!fallbackMusicLibrary.has(category)) {
      fallbackMusicLibrary.set(category, []);
    }
    fallbackMusicLibrary.get(category).push(url);
    fallbackMusicPool.push(url);
    recordDiskMusicMetadata(url, {
      category,
      scope: 'fallback',
      path
    });
    return;
  }
  const category = normalizeMusicCategory(fileCategory, 'other');
  const entry = ensureMusicLibrary(musicLibrary, character);
  if (!entry.categories.has(category)) {
    entry.categories.set(category, []);
  }
  entry.categories.get(category).push(url);
  if (category !== 'other') {
    entry.defaultCategory = category;
  }
  recordDiskMusicMetadata(url, {
    character,
    category,
    path
  });
});

const sfxClips = new Map();
const sfxAliases = new Map();
let defaultSfxClip = '';

const registerSfxClip = (key, url) => {
  const normalized = normalizeKey(key);
  if (!normalized || sfxClips.has(normalized)) return;
  sfxClips.set(normalized, url);
  if (!defaultSfxClip) {
    defaultSfxClip = url;
  }
};

const registerSfxAlias = (alias, targets) => {
  const normalized = normalizeKey(alias);
  if (!normalized) return;
  const entries = Array.isArray(targets) ? targets : [targets];
  const resolved = entries
    .map(target => normalizeKey(target))
    .filter(Boolean);
  if (!resolved.length) return;
  sfxAliases.set(normalized, resolved);
};

Object.entries(sfxModules).forEach(([path, url]) => {
  const relative = path.replace(/..\/assets\/sfx\//, '');
  const parts = relative.split('/');
  if (!parts.length) return;
  const filename = parts.pop();
  if (!filename) return;
  const stem = filename.replace(/\.[^.]+$/, '');
  const folder = parts.join('/');
  if (folder) {
    registerSfxClip(`${folder}/${stem}`, url);
  }
  registerSfxClip(stem, url);
});

registerSfxAlias('ui/pull/deal', [
  'kenney_audio/bookflip1',
  'kenney_audio/bookflip2',
  'kenney_audio/bookflip3',
  'kenney_audio/switch22'
]);

registerSfxAlias('ui/reward/drop', [
  'kenney_audio/handleCoins',
  'kenney_audio/handleCoins2',
  'kenney_audio/dropLeather',
  'kenney_audio/impactGeneric_light_001'
]);

registerSfxAlias('ui/default', [
  'kenney_audio/click1',
  'kenney_audio/click2',
  'kenney_audio/click3'
]);

const metadataOverrides = {
  portraitAliases: new Map(),
  portraitGalleries: new Map(),
  portraitCanonicals: new Map(),
  fallbackUrls: [],
  backgroundUrls: [],
  summonAliases: new Map(),
  summonGalleries: new Map(),
  summonCanonicals: new Map(),
  rarityFolders: new Map(),
  rewardArt: new Map(),
  rewardMetadata: new Map(),
  musicTracks: new Map(),
  musicFallbacks: new Map()
};

const manifestState = {
  digest: '',
  portraitAliases: new Map(),
  portraitCanonicals: new Set(),
  portraitMirrorRules: new Map(),
  summonAliases: new Map(),
  summonCanonicals: new Set(),
  summonPortraitKeys: new Set()
};

const defaultSummonPortraitKeys = new Set(['jellyfish']);

const portraitCache = new Map();
let registryVersion = 0;

const markRegistryUpdated = () => {
  registryVersion += 1;
};

export const getAssetRegistryVersion = () => registryVersion;

export const stringHashIndex = (value, modulo) => {
  let hash = 0;
  const str = String(value ?? '');
  for (let i = 0; i < str.length; i += 1) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  const safeModulo = Math.max(modulo, 1);
  return Math.abs(hash) % safeModulo;
};

const normalizeAliasTarget = value => {
  const key = normalizeKey(value);
  return key || '';
};

const normalizeInjectedUrl = value => {
  if (!value) return null;
  const str = String(value).trim();
  if (!str) return null;
  if (str.startsWith('http') || str.startsWith('data:') || str.startsWith('blob:') || str.startsWith('/')) {
    return str;
  }
  return normalizeAssetUrl(str);
};

const cloneEntry = entry => ({
  key: entry.key,
  url: entry.url,
  path: entry.path ?? null,
  origin: entry.origin ?? 'disk',
  metadata: entry.metadata ? { ...entry.metadata } : {}
});

const coerceAudioOptions = options => (options && typeof options === 'object' ? options : {});

const shouldMuteAudio = options => {
  const opts = coerceAudioOptions(options);
  if (opts.disabled === true || opts.disable === true) return true;
  if (opts.allowAudio === false) return true;
  if (opts.muted === true) return true;
  if (opts.sound === false) return true;
  if (opts.volume != null && Number(opts.volume) <= 0) return true;
  if (opts.respectReducedMotion !== false && opts.reducedMotion === true) return true;
  return false;
};

const getMusicEntry = characterId => {
  const key = normalizeKey(characterId);
  if (!key) return null;
  const base = musicLibrary.get(key) || null;
  const override = metadataOverrides.musicTracks.get(key) || null;
  if (!base && !override) return null;
  const categories = new Map();
  if (base) {
    base.categories.forEach((tracks, category) => {
      categories.set(category, [...tracks]);
    });
  }
  if (override) {
    override.categories.forEach((tracks, category) => {
      const existing = categories.get(category) ?? [];
      categories.set(category, [...existing, ...tracks]);
    });
  }
  const defaultCategory = override?.defaultCategory || base?.defaultCategory || 'normal';
  return { categories, defaultCategory };
};

const pickMusicPlaylist = (entry, category) => {
  if (!entry) return [];
  const normalized = normalizeMusicCategory(category, 'normal');
  const candidates = [normalized];
  if (entry.defaultCategory && !candidates.includes(entry.defaultCategory)) {
    candidates.push(entry.defaultCategory);
  }
  if (!candidates.includes('normal')) {
    candidates.push('normal');
  }
  if (!candidates.includes('other')) {
    candidates.push('other');
  }
  for (const cat of candidates) {
    const bucket = entry.categories.get(cat);
    if (Array.isArray(bucket) && bucket.length) {
      return [...bucket];
    }
  }
  return [];
};

export const getMusicPlaylist = (characterId, category = 'normal', options = {}) => {
  if (shouldMuteAudio(options)) return [];
  const entry = getMusicEntry(characterId);
  if (!entry) return [];
  return pickMusicPlaylist(entry, category);
};

export const getMusicFallbackPlaylist = (category = 'normal', options = {}) => {
  if (shouldMuteAudio(options)) return [];
  const normalized = normalizeMusicCategory(category, 'normal');
  const overrideTracks = metadataOverrides.musicFallbacks.get(normalized) ?? [];
  const tracks = fallbackMusicLibrary.get(normalized) ?? [];
  return [...overrideTracks, ...tracks];
};

export const getAllMusicTracks = (options = {}) => {
  if (shouldMuteAudio(options)) return [];
  const overrides = [];
  metadataOverrides.musicFallbacks.forEach(urls => {
    overrides.push(...urls);
  });
  return [...overrides, ...fallbackMusicPool];
};

export const getRandomMusicTrack = (characterId, category = 'normal', options = {}) => {
  if (shouldMuteAudio(options)) return '';
  const id = normalizeKey(characterId);
  const playlist = id
    ? getMusicPlaylist(id, category, options)
    : getAllMusicTracks(options);
  if (!Array.isArray(playlist) || playlist.length === 0) {
    emitTelemetry('music-fallback', {
      id,
      category: normalizeMusicCategory(category, 'normal'),
      reason: id ? 'empty-playlist' : 'no-tracks'
    });
    return '';
  }
  const index = Math.floor(Math.random() * playlist.length);
  return playlist[index] ?? '';
};

export const getMusicTrackMetadata = url => {
  if (!url) return null;
  const key = String(url);
  if (!key) return null;
  const base = musicTrackMetadataDisk.get(key) || null;
  const override = musicTrackMetadataOverrides.get(key) || null;
  if (!base && !override) return null;
  return { ...(base || {}), ...(override || {}) };
};

const expandSfxCandidates = input => {
  const values = Array.isArray(input) ? input : [input];
  const candidates = [];
  values.forEach(value => {
    if (typeof value !== 'string') return;
    const normalized = normalizeKey(value);
    if (!normalized) return;
    if (sfxAliases.has(normalized)) {
      candidates.push(...sfxAliases.get(normalized));
    }
    candidates.push(normalized);
  });
  return candidates;
};

export const getSfxClip = (input, options = {}) => {
  if (shouldMuteAudio(options)) return '';
  const candidates = expandSfxCandidates(input);
  for (const key of candidates) {
    if (sfxClips.has(key)) {
      return sfxClips.get(key) ?? '';
    }
  }
  const opts = coerceAudioOptions(options);
  if (typeof opts.fallback === 'string') {
    return getSfxClip(opts.fallback, { ...opts, fallback: false });
  }
  if (opts.fallback === true && defaultSfxClip) {
    emitTelemetry('sfx-fallback', {
      key: candidates[0] ?? '',
      reason: 'default',
      fallback: defaultSfxClip
    });
    return defaultSfxClip;
  }
  emitTelemetry('sfx-fallback', {
    key: candidates[0] ?? '',
    reason: 'missing'
  });
  return '';
};

export const getDefaultSfxClip = () => defaultSfxClip;

export const getAvailableSfxKeys = () => {
  const keys = new Set();
  sfxClips.forEach((_value, key) => keys.add(key));
  sfxAliases.forEach((_value, key) => keys.add(key));
  return Array.from(keys);
};

const isSummonPortraitKey = key => {
  const normalized = normalizeKey(key);
  if (!normalized) return false;
  if (manifestState.summonPortraitKeys.has(normalized)) return true;
  if (defaultSummonPortraitKeys.has(normalized)) return true;
  return false;
};

const resolvePortraitKey = id => {
  const normalized = normalizeKey(id);
  if (!normalized) return '';
  if (metadataOverrides.portraitAliases.has(normalized)) {
    return metadataOverrides.portraitAliases.get(normalized);
  }
  if (manifestState.portraitAliases.has(normalized)) {
    return manifestState.portraitAliases.get(normalized);
  }
  if (metadataOverrides.summonAliases.has(normalized)) {
    const target = metadataOverrides.summonAliases.get(normalized);
    if (isSummonPortraitKey(target)) {
      return target;
    }
  }
  if (manifestState.summonAliases.has(normalized)) {
    const target = manifestState.summonAliases.get(normalized);
    if (isSummonPortraitKey(target)) {
      return target;
    }
  }
  return normalized;
};

const resolveSummonKey = id => {
  const normalized = normalizeKey(id);
  if (!normalized) return '';
  if (metadataOverrides.summonAliases.has(normalized)) {
    return metadataOverrides.summonAliases.get(normalized);
  }
  if (manifestState.summonAliases.has(normalized)) {
    return manifestState.summonAliases.get(normalized);
  }
  return normalized;
};

const getPortraitGalleryByKey = key => {
  const normalized = normalizeKey(key);
  if (!normalized) return [];
  if (metadataOverrides.portraitGalleries.has(normalized)) {
    return [...metadataOverrides.portraitGalleries.get(normalized)];
  }
  if (portraitGalleries.has(normalized)) {
    return [...portraitGalleries.get(normalized)];
  }
  if (metadataOverrides.summonGalleries.has(normalized)) {
    return metadataOverrides.summonGalleries.get(normalized).map(entry => entry.url);
  }
  if (summonGalleries.has(normalized)) {
    return summonGalleries.get(normalized).map(entry => entry.url);
  }
  return [];
};

const getFallbackPool = () => {
  if (metadataOverrides.fallbackUrls.length) {
    return [...metadataOverrides.fallbackUrls, ...fallbackPool];
  }
  return [...fallbackPool];
};

export const getDefaultFallback = () => STATIC_FALLBACK;

export const clearCharacterImageCache = () => {
  portraitCache.clear();
};

const getCachedPortrait = id => portraitCache.get(id);

const setCachedPortrait = (id, url) => {
  portraitCache.set(id, url);
};

const chooseRandom = list => {
  if (!Array.isArray(list) || list.length === 0) return undefined;
  const idx = Math.floor(Math.random() * list.length);
  return list[idx];
};

const getDeterministicFallback = id => {
  const pool = getFallbackPool();
  if (!pool.length) return STATIC_FALLBACK;
  const index = stringHashIndex(id, pool.length);
  return pool[index] || pool[0];
};

const resolveMirroredPortrait = (mirrorId, metadata) => {
  const rule = manifestState.portraitMirrorRules.get(normalizeKey(mirrorId)) || null;
  const targetId = (metadata && normalizeKey(metadata.portrait_base)) || rule?.target || 'player';
  const cacheKey = targetId || 'player';
  const cached = getCachedPortrait(cacheKey);
  if (cached) return cached;
  const mirrorGallery = getPortraitGalleryByKey(cacheKey);
  if (mirrorGallery.length) {
    const chosen = chooseRandom(mirrorGallery) ?? mirrorGallery[0];
    setCachedPortrait(cacheKey, chosen);
    return chosen;
  }
  const pool = getFallbackPool();
  if (pool.length) {
    const chosen = chooseRandom(pool) ?? pool[0];
    setCachedPortrait(cacheKey, chosen);
    emitTelemetry('portrait-fallback', {
      id: mirrorId,
      key: cacheKey,
      reason: 'mirror-pool',
      portraitPool: 'player_mirror'
    });
    return chosen;
  }
  setCachedPortrait(cacheKey, STATIC_FALLBACK);
  emitTelemetry('portrait-fallback', {
    id: mirrorId,
    key: cacheKey,
    reason: 'mirror-static',
    portraitPool: 'player_mirror'
  });
  return STATIC_FALLBACK;
};

export const getCharacterImage = (characterId, options = {}) => {
  if (!characterId) return STATIC_FALLBACK;
  const id = String(characterId);
  if (!id.trim()) return STATIC_FALLBACK;

  const cached = getCachedPortrait(id);
  if (cached) return cached;

  const key = resolvePortraitKey(id);
  const gallery = getPortraitGalleryByKey(key);
  const pool = getFallbackPool();

  const persist = url => {
    setCachedPortrait(id, url);
    return url;
  };

  const optionsObj = options && typeof options === 'object' ? options : null;
  let metadata = null;
  if (optionsObj && optionsObj.metadata && typeof optionsObj.metadata === 'object') {
    metadata = optionsObj.metadata;
  }
  if (!metadata) {
    metadata = getCharacterMetadata(id);
  }

  const portraitPoolRaw = metadata && (metadata.portrait_pool ?? metadata.portraitPool);
  const portraitPool = portraitPoolRaw ? String(portraitPoolRaw).toLowerCase() : null;

  if (portraitPool === 'player_mirror') {
    return resolveMirroredPortrait(id, metadata || {});
  }

  const metadataFlags = Array.isArray(metadata?.flags) ? metadata.flags : [];
  const isPlayer = options === true || (optionsObj && optionsObj.isPlayer === true);
  const treatAsPlayer =
    isPlayer ||
    portraitPool === 'player_gallery' ||
    portraitPool === 'player' ||
    metadata?.treat_as_player === true ||
    metadataFlags.includes('player_gallery');

  const logPortraitFallback = reason => {
    emitTelemetry('portrait-fallback', {
      id,
      key,
      reason,
      portraitPool,
      treatAsPlayer,
      metadataFlags
    });
  };

  if (treatAsPlayer) {
    if (gallery.length) {
      const chosen = chooseRandom(gallery) ?? gallery[0];
      return persist(chosen);
    }
    if (pool.length) {
      const chosen = chooseRandom(pool) ?? pool[0];
      logPortraitFallback('player-pool');
      return persist(chosen);
    }
    logPortraitFallback('player-static');
    return persist(STATIC_FALLBACK);
  }

  if (gallery.length) {
    if (gallery.length === 1) {
      return persist(gallery[0]);
    }
    const chosen = chooseRandom(gallery) ?? gallery[0];
    return persist(chosen);
  }

  if (pool.length) {
    const fallback = getDeterministicFallback(id);
    logPortraitFallback('pool-fallback');
    return persist(fallback);
  }

  logPortraitFallback('static-fallback');
  return persist(STATIC_FALLBACK);
};

export const getAvailableCharacterIds = () => {
  const ids = new Set();
  portraitCanonicals.forEach(value => ids.add(value));
  metadataOverrides.portraitCanonicals.forEach(value => ids.add(value));
  manifestState.portraitCanonicals.forEach(value => ids.add(value));
  const applySummonKey = key => {
    if (!key) return;
    if (summonCanonicals.has(key)) {
      ids.add(summonCanonicals.get(key));
      return;
    }
    if (manifestState.summonCanonicals.has(key)) {
      ids.add(key);
    }
  };
  defaultSummonPortraitKeys.forEach(applySummonKey);
  manifestState.summonPortraitKeys.forEach(applySummonKey);
  return Array.from(ids);
};

export const getRandomFallback = () => {
  const pool = getFallbackPool();
  if (!pool.length) return STATIC_FALLBACK;
  return chooseRandom(pool) ?? pool[0];
};

export const getHourlyBackground = () => {
  const pool = metadataOverrides.backgroundUrls.length
    ? [...metadataOverrides.backgroundUrls, ...backgroundPool]
    : [...backgroundPool];
  if (!pool.length) return STATIC_FALLBACK;
  const now = new Date();
  const seed =
    now.getFullYear() * 1000000 +
    now.getMonth() * 10000 +
    now.getDate() * 100 +
    now.getHours();
  const idx = stringHashIndex(seed, pool.length);
  return pool[idx] || pool[0];
};

export const getRandomBackground = () => {
  const pool = metadataOverrides.backgroundUrls.length
    ? [...metadataOverrides.backgroundUrls, ...backgroundPool]
    : [...backgroundPool];
  if (!pool.length) return STATIC_FALLBACK;
  return chooseRandom(pool) ?? pool[0];
};

export const hasCharacterGallery = characterId => {
  const key = resolvePortraitKey(characterId);
  const gallery = getPortraitGalleryByKey(key);
  return Array.isArray(gallery) && gallery.length > 1;
};

export const advanceCharacterImage = characterId => {
  if (!characterId) return STATIC_FALLBACK;
  const id = String(characterId);
  if (!id.trim()) return STATIC_FALLBACK;
  const key = resolvePortraitKey(id);
  const gallery = getPortraitGalleryByKey(key);
  if (!Array.isArray(gallery) || gallery.length === 0) {
    return getCachedPortrait(id) ?? getCharacterImage(id);
  }
  const current = getCachedPortrait(id) ?? getCharacterImage(id);
  const index = gallery.indexOf(current);
  const nextIndex = (index >= 0 ? index + 1 : 1) % gallery.length;
  const next = gallery[nextIndex];
  setCachedPortrait(id, next);
  return next;
};

export const getSummonGallery = summonId => {
  const key = resolveSummonKey(summonId);
  if (!key) return [];
  const entries = [];
  if (metadataOverrides.summonGalleries.has(key)) {
    metadataOverrides.summonGalleries.get(key).forEach(entry => entries.push(cloneEntry(entry)));
  }
  if (summonGalleries.has(key)) {
    summonGalleries.get(key).forEach(entry => entries.push(cloneEntry(entry)));
  }
  return entries;
};

export const getSummonArt = (summonId, options = {}) => {
  const entries = getSummonGallery(summonId);
  const key = normalizeKey(summonId);
  if (!entries.length) {
    emitTelemetry('summon-fallback', {
      id: key,
      reason: 'empty-gallery'
    });
    return STATIC_FALLBACK;
  }
  let pool = entries;
  if (typeof options.filter === 'function') {
    const filtered = entries.filter(entry => options.filter(entry));
    if (filtered.length) {
      pool = filtered;
    }
  }
  if (!pool.length) {
    emitTelemetry('summon-fallback', {
      id: key,
      reason: 'filtered-empty'
    });
    return STATIC_FALLBACK;
  }
  if (options.seed != null) {
    const index = stringHashIndex(`${summonId}:${options.seed}`, pool.length);
    return pool[index]?.url ?? pool[0].url;
  }
  const chosen = chooseRandom(pool);
  return chosen?.url ?? pool[0].url;
};

export const getPortraitRarityFolders = characterId => {
  const key = resolvePortraitKey(characterId);
  if (!key) return [];
  if (metadataOverrides.rarityFolders.has(key)) {
    return [...metadataOverrides.rarityFolders.get(key)];
  }
  return [];
};

export const getAvailableSummonIds = () => {
  const ids = new Set();
  summonCanonicals.forEach(value => ids.add(value));
  metadataOverrides.summonCanonicals.forEach(value => ids.add(value));
  manifestState.summonCanonicals.forEach(value => ids.add(value));
  return Array.from(ids);
};

const stripNonAlphanumeric = value => String(value ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');

const createRewardCollection = (modules, options = {}) => {
  const map = new Map();
  const urls = [];
  Object.entries(modules).forEach(([path, url]) => {
    if (!url) return;
    const segments = path.split('/');
    const file = segments.pop()?.replace(/\.png$/i, '');
    const folder = segments.pop();
    if (!file) return;
    const baseKey = options.useFolderKey && folder ? `${folder}/${file}` : file;
    const normalizedBase = normalizeKey(baseKey);
    if (normalizedBase) {
      map.set(normalizedBase, url);
    }
    if (!options.useFolderKey || !folder) {
      const normalizedFile = normalizeKey(file);
      if (normalizedFile) {
        map.set(normalizedFile, url);
      }
    }
    const compact = stripNonAlphanumeric(baseKey);
    if (compact) {
      map.set(compact, url);
    }
    urls.push(url);
  });
  const fallback = options.fallback || urls[0] || '';
  return { map, fallback, all: urls };
};

const rewardCollections = {
  card: createRewardCollection(cardArtModules, {
    fallback: DEFAULT_CARD_FALLBACK,
    useFolderKey: true
  }),
  relic: createRewardCollection(relicArtModules, {
    fallback: DEFAULT_RELIC_FALLBACK,
    useFolderKey: true
  }),
  item: createRewardCollection(materialIconModules, {
    fallback: DEFAULT_ITEM_FALLBACK,
    useFolderKey: false
  })
};

const rewardCache = new Map();

const normalizeRewardType = type => {
  const key = normalizeKey(type);
  if (key === 'cards') return 'card';
  if (key === 'relics') return 'relic';
  if (key === 'items') return 'item';
  if (key === 'material' || key === 'materials') return 'item';
  if (key === 'relic') return 'relic';
  if (key === 'card') return 'card';
  if (key === 'item') return 'item';
  if (!key) return 'item';
  return 'item';
};

const normalizeRewardId = (type, id) => {
  const key = normalizeKey(id);
  if (!key) return '';
  if (type === 'item') {
    return stripNonAlphanumeric(key);
  }
  return key;
};

const rewardCacheKey = (type, id) => `${type}:${id}`;

export const getRewardArt = (type, id) => {
  const normalizedType = normalizeRewardType(type);
  const collection = normalizedType ? rewardCollections[normalizedType] : undefined;
  if (!collection) {
    return DEFAULT_ITEM_FALLBACK;
  }
  const normalizedId = normalizeRewardId(normalizedType, id);
  const cacheKey = rewardCacheKey(normalizedType, normalizedId);
  if (rewardCache.has(cacheKey)) {
    return rewardCache.get(cacheKey);
  }
  if (metadataOverrides.rewardArt.has(cacheKey)) {
    const overrideUrl = metadataOverrides.rewardArt.get(cacheKey);
    if (overrideUrl) {
      rewardCache.set(cacheKey, overrideUrl);
      return overrideUrl;
    }
  }
  let url = normalizedId ? collection.map.get(normalizedId) : null;
  if (!url && normalizedId) {
    const compact = stripNonAlphanumeric(normalizedId);
    if (compact) {
      url = collection.map.get(compact) ?? null;
    }
  }
  if (!url) {
    emitTelemetry('reward-fallback', {
      type: normalizedType,
      id: normalizedId,
      reason: metadataOverrides.rewardArt.has(cacheKey) ? 'override-missing' : 'missing-art'
    });
    url = collection.fallback;
  }
  rewardCache.set(cacheKey, url);
  return url;
};

export const getRewardMetadata = (type, id) => {
  const normalizedType = normalizeRewardType(type);
  const normalizedId = normalizeRewardId(normalizedType, id);
  const key = rewardCacheKey(normalizedType, normalizedId);
  if (!metadataOverrides.rewardMetadata.has(key)) {
    return null;
  }
  return { ...metadataOverrides.rewardMetadata.get(key) };
};

const createGlyphMap = modules => {
  const map = new Map();
  Object.entries(modules).forEach(([path, url]) => {
    if (!url) return;
    const file = path.split('/').pop()?.replace(/\.png$/i, '');
    if (!file) return;
    const compact = stripNonAlphanumeric(file);
    if (compact) {
      map.set(compact, url);
    }
  });
  return map;
};

const glyphCollections = {
  card: createGlyphMap(cardGlyphModules),
  relic: createGlyphMap(relicGlyphModules)
};

const getGlyphCandidateKeys = entry => {
  const candidates = [];
  const id = stripNonAlphanumeric(entry?.id);
  const name = stripNonAlphanumeric(entry?.name);
  if (id) candidates.push(id);
  if (name) candidates.push(name);
  return candidates;
};

export const getGlyphArt = (type, entry) => {
  const normalizedType = normalizeRewardType(type);
  if (normalizedType !== 'card' && normalizedType !== 'relic') {
    return '';
  }
  const map = normalizedType === 'relic' ? glyphCollections.relic : glyphCollections.card;
  if (!entry || typeof entry !== 'object') return '';
  const keys = getGlyphCandidateKeys(entry);
  for (const key of keys) {
    if (map.has(key)) {
      return map.get(key);
    }
  }
  try {
    if (import.meta?.env?.DEV && typeof window !== 'undefined' && keys.length) {
      console.debug('[glyphArt] no match', { type, id: entry?.id, name: entry?.name, keys });
    }
  } catch {}
  return '';
};

const ensureMaterialElement = (store, element) => {
  if (!store.has(element)) {
    store.set(element, {
      first: null,
      byRank: new Map(),
      genericByRank: new Map()
    });
  }
  return store.get(element);
};

const materialIconIndex = (() => {
  const elements = new Map();
  const genericByRank = new Map();
  let genericFirst = materialIconModules['../assets/items/generic/generic1.png'] ?? null;

  Object.entries(materialIconModules).forEach(([path, url]) => {
    if (!url) return;
    const segments = path.split('/');
    const file = segments.pop()?.replace(/\.png$/i, '');
    const folder = segments.pop();
    const element = normalizeKey(folder);
    if (!file || !element) return;
    const entry = ensureMaterialElement(elements, element);
    if (!entry.first) {
      entry.first = url;
    }
    if (file.startsWith(element)) {
      const rank = stripNonAlphanumeric(file.slice(element.length)) || '1';
      entry.byRank.set(rank, url);
    } else if (file.startsWith('generic')) {
      const rank = stripNonAlphanumeric(file.slice('generic'.length)) || '1';
      entry.genericByRank.set(rank, url);
      if (element === 'generic') {
        genericByRank.set(rank, url);
        if (!genericFirst && file === 'generic1') {
          genericFirst = url;
        }
      }
    }
  });

  if (!genericFirst) {
    genericFirst = DEFAULT_ITEM_FALLBACK;
  }

  return {
    fallback: DEFAULT_ITEM_FALLBACK,
    elements,
    genericByRank,
    genericFirst
  };
})();

const materialIconCache = new Map();

const parseMaterialKey = key => {
  const [rawElement, rawRank] = String(key ?? '').split('_');
  const element = normalizeKey(rawElement);
  const rankDigits = stripNonAlphanumeric(rawRank || '');
  const rank = rankDigits || '1';
  return { element, rank };
};

export const getMaterialIcon = key => {
  const { element, rank } = parseMaterialKey(key);
  const cacheKey = rewardCacheKey(element || 'generic', rank);
  if (materialIconCache.has(cacheKey)) {
    return materialIconCache.get(cacheKey);
  }
  let url = null;
  if (element) {
    const entry = materialIconIndex.elements.get(element);
    if (entry) {
      if (entry.byRank.has(rank)) {
        url = entry.byRank.get(rank);
      } else if (entry.genericByRank.has(rank)) {
        url = entry.genericByRank.get(rank);
      } else if (entry.first) {
        url = entry.first;
      }
    }
  }
  if (!url) {
    if (materialIconIndex.genericByRank.has(rank)) {
      url = materialIconIndex.genericByRank.get(rank);
    } else {
      url = materialIconIndex.genericFirst || materialIconIndex.fallback;
    }
  }
  if (!url) {
    url = materialIconIndex.fallback;
    emitTelemetry('material-fallback', {
      id: String(key ?? ''),
      element: element || 'generic',
      rank,
      reason: 'missing-icon'
    });
  }
  materialIconCache.set(cacheKey, url);
  return url;
};

export const getMaterialFallbackIcon = () => materialIconIndex.fallback;

export const onMaterialIconError = event => {
  if (!event || !event.target) return;
  event.target.src = materialIconIndex.fallback;
};

const asArray = value => {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  return [value];
};

const cloneMetadata = value => {
  if (!value || typeof value !== 'object') {
    return {};
  }
  return { ...value };
};

const sanitizeRewardOverrideEntry = entry => {
  if (!entry) {
    return { url: null, metadata: null };
  }
  if (typeof entry === 'string') {
    return { url: normalizeInjectedUrl(entry), metadata: null };
  }
  if (typeof entry === 'object') {
    const url = normalizeInjectedUrl(entry.url || entry.href || entry.src || '');
    const metadata = entry.metadata && typeof entry.metadata === 'object' ? cloneMetadata(entry.metadata) : null;
    return { url, metadata };
  }
  return { url: null, metadata: null };
};

const pickRewardOverride = value => {
  const candidates = asArray(value);
  for (const candidate of candidates) {
    const sanitized = sanitizeRewardOverrideEntry(candidate);
    if (sanitized.url) {
      return sanitized;
    }
  }
  return { url: null, metadata: null };
};

const parseMusicTrackItems = (input, context) => {
  const urls = [];
  asArray(input).forEach(item => {
    if (!item) return;
    if (typeof item === 'string') {
      const url = normalizeInjectedUrl(item);
      if (!url) return;
      recordOverrideMusicMetadata(url, { ...context });
      urls.push(url);
      return;
    }
    if (typeof item === 'object') {
      const url = normalizeInjectedUrl(item.url || item.href || item.src || '');
      if (!url) return;
      const metadata = item.metadata && typeof item.metadata === 'object' ? cloneMetadata(item.metadata) : {};
      recordOverrideMusicMetadata(url, { ...context, ...metadata });
      urls.push(url);
    }
  });
  return urls;
};

const normalizeManifestKey = value => normalizeKey(value);

const sanitizeAliasList = aliases => {
  if (!Array.isArray(aliases)) return [];
  const normalized = aliases
    .map(alias => normalizeManifestKey(alias))
    .filter(Boolean);
  return Array.from(new Set(normalized)).sort();
};

const sanitizePortraitEntry = entry => {
  if (!entry || typeof entry !== 'object') return null;
  const id = normalizeManifestKey(entry.id || entry.canonical || entry.name);
  if (!id) return null;
  const aliases = sanitizeAliasList(entry.aliases);
  const folder = typeof entry.folder === 'string' ? entry.folder : null;
  let mimic = null;
  if (entry.mimic && typeof entry.mimic === 'object') {
    const target = normalizeManifestKey(entry.mimic.target || entry.mimic.base || entry.mimic.mirror);
    const mode = entry.mimic.mode ? String(entry.mimic.mode).trim() : '';
    if (target || mode) {
      mimic = {
        mode,
        target
      };
    }
  }
  return { id, aliases, folder, mimic };
};

const sanitizeSummonEntry = entry => {
  if (!entry || typeof entry !== 'object') return null;
  const id = normalizeManifestKey(entry.id || entry.name);
  if (!id) return null;
  const aliases = sanitizeAliasList(entry.aliases);
  const folder = typeof entry.folder === 'string' ? entry.folder : null;
  const portrait = entry.portrait === true;
  return { id, aliases, folder, portrait };
};

const normalizeManifest = manifest => {
  if (!manifest || typeof manifest !== 'object') {
    return { portraits: [], summons: [] };
  }
  const portraits = Array.isArray(manifest.portraits)
    ? manifest.portraits
        .map(sanitizePortraitEntry)
        .filter(Boolean)
        .sort((a, b) => a.id.localeCompare(b.id))
    : [];
  const summons = Array.isArray(manifest.summons)
    ? manifest.summons
        .map(sanitizeSummonEntry)
        .filter(Boolean)
        .sort((a, b) => a.id.localeCompare(b.id))
    : [];
  return { portraits, summons };
};

export const registerAssetManifest = manifest => {
  const normalized = normalizeManifest(manifest);
  const digest = JSON.stringify(normalized);
  if (digest === manifestState.digest) {
    return;
  }

  manifestState.digest = digest;
  manifestState.portraitAliases.clear();
  manifestState.portraitCanonicals.clear();
  manifestState.portraitMirrorRules.clear();
  manifestState.summonAliases.clear();
  manifestState.summonCanonicals.clear();
  manifestState.summonPortraitKeys.clear();

  normalized.portraits.forEach(entry => {
    manifestState.portraitCanonicals.add(entry.id);
    entry.aliases.forEach(alias => manifestState.portraitAliases.set(alias, entry.id));
    if (entry.mimic) {
      manifestState.portraitMirrorRules.set(entry.id, {
        mode: entry.mimic.mode || '',
        target: entry.mimic.target || ''
      });
    }
  });

  normalized.summons.forEach(entry => {
    manifestState.summonCanonicals.add(entry.id);
    entry.aliases.forEach(alias => manifestState.summonAliases.set(alias, entry.id));
    if (entry.portrait) {
      manifestState.summonPortraitKeys.add(entry.id);
      manifestState.portraitCanonicals.add(entry.id);
      entry.aliases.forEach(alias => {
        if (!manifestState.portraitAliases.has(alias)) {
          manifestState.portraitAliases.set(alias, entry.id);
        }
      });
    }
  });

  clearCharacterImageCache();
  markRegistryUpdated();
};

const toSummonEntries = (key, payload) =>
  asArray(payload)
    .map(item => {
      if (!item) return null;
      if (typeof item === 'string') {
        const url = normalizeInjectedUrl(item);
        if (!url) return null;
        return {
          key,
          url,
          path: null,
          origin: 'metadata',
          metadata: {}
        };
      }
      if (typeof item === 'object' && item.url) {
        const url = normalizeInjectedUrl(item.url);
        if (!url) return null;
        const metadata = { ...item.metadata };
        if (item.element) metadata.element = item.element;
        return {
          key,
          url,
          path: item.path ?? null,
          origin: 'metadata',
          metadata
        };
      }
      return null;
    })
    .filter(Boolean);

export const registerAssetMetadata = metadata => {
  if (!metadata || typeof metadata !== 'object') return;
  let touched = false;

  if (metadata.portraitAliases) {
    for (const [alias, target] of Object.entries(metadata.portraitAliases)) {
      const aliasKey = normalizeKey(alias);
      const targetKey = normalizeAliasTarget(target);
      if (!aliasKey || !targetKey) continue;
      metadataOverrides.portraitAliases.set(aliasKey, targetKey);
      touched = true;
    }
  }

  if (metadata.portraitOverrides) {
    for (const [id, urls] of Object.entries(metadata.portraitOverrides)) {
      const key = normalizeKey(id);
      if (!key) continue;
      const list = asArray(urls)
        .map(normalizeInjectedUrl)
        .filter(Boolean);
      metadataOverrides.portraitGalleries.set(key, list);
      metadataOverrides.portraitCanonicals.set(key, id);
      touched = true;
    }
  }

  if (Array.isArray(metadata.fallbackOverrides)) {
    metadataOverrides.fallbackUrls = metadata.fallbackOverrides
      .map(normalizeInjectedUrl)
      .filter(Boolean);
    touched = true;
  }

  if (Array.isArray(metadata.backgroundOverrides)) {
    metadataOverrides.backgroundUrls = metadata.backgroundOverrides
      .map(normalizeInjectedUrl)
      .filter(Boolean);
    touched = true;
  }

  if (metadata.summonAliases) {
    for (const [alias, target] of Object.entries(metadata.summonAliases)) {
      const aliasKey = normalizeKey(alias);
      const targetKey = normalizeAliasTarget(target);
      if (!aliasKey || !targetKey) continue;
      metadataOverrides.summonAliases.set(aliasKey, targetKey);
      touched = true;
    }
  }

  if (metadata.summonOverrides) {
    for (const [id, entries] of Object.entries(metadata.summonOverrides)) {
      const key = normalizeKey(id);
      if (!key) continue;
      const list = toSummonEntries(key, entries);
      metadataOverrides.summonGalleries.set(key, list);
      metadataOverrides.summonCanonicals.set(key, id);
      touched = true;
    }
  }

  if (metadata.rewardOverrides && typeof metadata.rewardOverrides === 'object') {
    metadataOverrides.rewardArt.clear();
    metadataOverrides.rewardMetadata.clear();
    for (const [type, entries] of Object.entries(metadata.rewardOverrides)) {
      const normalizedType = normalizeRewardType(type);
      if (!entries || typeof entries !== 'object') continue;
      for (const [id, value] of Object.entries(entries)) {
        const normalizedId = normalizeRewardId(normalizedType, id);
        if (!normalizedId) continue;
        const { url, metadata: rewardMeta } = pickRewardOverride(value);
        if (!url) continue;
        const key = rewardCacheKey(normalizedType, normalizedId);
        metadataOverrides.rewardArt.set(key, url);
        if (rewardMeta) {
          metadataOverrides.rewardMetadata.set(key, rewardMeta);
        } else {
          metadataOverrides.rewardMetadata.delete(key);
        }
        touched = true;
      }
    }
    rewardCache.clear();
  }

  let musicTouched = false;
  let musicCleared = false;
  const resetMusicOverrides = () => {
    if (!musicCleared) {
      metadataOverrides.musicTracks.clear();
      metadataOverrides.musicFallbacks.clear();
      clearOverrideMusicMetadata();
      musicCleared = true;
    }
  };

  if (metadata.musicOverrides && typeof metadata.musicOverrides === 'object') {
    resetMusicOverrides();
    for (const [id, config] of Object.entries(metadata.musicOverrides)) {
      const key = normalizeKey(id);
      if (!key) continue;
      const source = config && typeof config === 'object' ? config : {};
      const container =
        (source.tracks && typeof source.tracks === 'object' ? source.tracks : null) ||
        (source.categories && typeof source.categories === 'object' ? source.categories : null) ||
        source;
      if (!container || typeof container !== 'object') continue;
      const categories = new Map();
      Object.entries(container).forEach(([categoryName, entries]) => {
        if (categoryName === 'default' || categoryName === 'defaultCategory' || categoryName === 'tracks' || categoryName === 'categories') {
          return;
        }
        const category = normalizeMusicCategory(categoryName, 'normal');
        const urls = parseMusicTrackItems(entries, {
          character: key,
          category,
          scope: 'character'
        });
        if (urls.length) {
          categories.set(category, urls);
        }
      });
      if (!categories.size) continue;
      const defaultCategoryRaw = source.defaultCategory ?? source.default ?? null;
      const defaultCategory = defaultCategoryRaw
        ? normalizeMusicCategory(defaultCategoryRaw, 'normal')
        : null;
      metadataOverrides.musicTracks.set(key, {
        categories,
        defaultCategory
      });
      musicTouched = true;
    }
  }

  if (metadata.musicFallbacks && typeof metadata.musicFallbacks === 'object') {
    resetMusicOverrides();
    for (const [categoryName, entries] of Object.entries(metadata.musicFallbacks)) {
      const category = normalizeMusicCategory(categoryName, 'normal');
      const urls = parseMusicTrackItems(entries, {
        category,
        scope: 'fallback'
      });
      if (!urls.length) continue;
      metadataOverrides.musicFallbacks.set(category, urls);
      musicTouched = true;
    }
  }

  if (metadata.musicAnnotations && typeof metadata.musicAnnotations === 'object') {
    for (const [rawUrl, meta] of Object.entries(metadata.musicAnnotations)) {
      const url = normalizeInjectedUrl(rawUrl);
      if (!url) continue;
      const annotations = cloneMetadata(meta);
      recordOverrideMusicMetadata(url, { ...annotations, scope: 'annotation' });
      musicTouched = true;
    }
  }

  if (metadata.rarityFolders) {
    for (const [id, folders] of Object.entries(metadata.rarityFolders)) {
      const key = normalizeKey(id);
      if (!key) continue;
      const list = asArray(folders).map(folder => String(folder));
      metadataOverrides.rarityFolders.set(key, Array.from(new Set(list)));
      metadataOverrides.portraitCanonicals.set(key, id);
      touched = true;
    }
  }

  if (musicTouched) {
    touched = true;
  }

  if (touched) {
    clearCharacterImageCache();
    markRegistryUpdated();
  }
};

export const resetAssetRegistryOverrides = () => {
  metadataOverrides.portraitAliases.clear();
  metadataOverrides.portraitGalleries.clear();
  metadataOverrides.portraitCanonicals.clear();
  metadataOverrides.fallbackUrls = [];
  metadataOverrides.backgroundUrls = [];
  metadataOverrides.summonAliases.clear();
  metadataOverrides.summonGalleries.clear();
  metadataOverrides.summonCanonicals.clear();
  metadataOverrides.rarityFolders.clear();
  metadataOverrides.rewardArt.clear();
  metadataOverrides.rewardMetadata.clear();
  metadataOverrides.musicTracks.clear();
  metadataOverrides.musicFallbacks.clear();
  clearOverrideMusicMetadata();
  resetAssetRegistryTelemetry();
  rewardCache.clear();
  materialIconCache.clear();
  clearCharacterImageCache();
  markRegistryUpdated();
};

export { normalizeAssetUrl };
