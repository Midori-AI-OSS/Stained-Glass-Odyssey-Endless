// Centralized asset registry for portraits, summons, backgrounds, and fallbacks.
// This module normalizes asset URLs, manages caches, and exposes hooks so
// metadata payloads can override on-disk resources without touching callers.

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

const createModuleMap = modules =>
  Object.fromEntries(
    Object.entries(modules).map(([path, value]) => [path, normalizeAssetUrl(value)])
  );

const characterModules = createModuleMap(
  import.meta.glob('../assets/characters/**/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  })
);

const fallbackModules = createModuleMap(
  import.meta.glob('../assets/characters/fallbacks/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  })
);

const backgroundModules = createModuleMap(
  import.meta.glob('../assets/backgrounds/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  })
);

const summonModules = createModuleMap(
  import.meta.glob('../assets/summons/**/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  })
);

const cardArtModules = createModuleMap(
  import.meta.glob('../assets/cards/*/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  })
);

const relicArtModules = createModuleMap(
  import.meta.glob('../assets/relics/*/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  })
);

const materialIconModules = createModuleMap(
  import.meta.glob('../assets/items/*/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  })
);

const cardGlyphModules = createModuleMap(
  import.meta.glob('../assets/cards/Art/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  })
);

const relicGlyphModules = createModuleMap(
  import.meta.glob('../assets/relics/Art/*.png', {
    eager: true,
    import: 'default',
    query: '?url'
  })
);

const STATIC_FALLBACK = normalizeAssetUrl('../assets/midoriai-logo.png');
const DEFAULT_CARD_FALLBACK = normalizeAssetUrl('../assets/cards/gray/bg_attack_default_gray2.png');
const DEFAULT_RELIC_FALLBACK = normalizeAssetUrl('../assets/relics/fallback/placeholder.png');
const DEFAULT_ITEM_FALLBACK = normalizeAssetUrl('../assets/items/generic/generic1.png');

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

const metadataOverrides = {
  portraitAliases: new Map(),
  portraitGalleries: new Map(),
  portraitCanonicals: new Map(),
  fallbackUrls: [],
  backgroundUrls: [],
  summonAliases: new Map(),
  summonGalleries: new Map(),
  summonCanonicals: new Map(),
  rarityFolders: new Map()
};

const defaultPortraitAliases = new Map([
  ['lady_echo', 'echo']
]);

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

const normalizeKey = value => {
  if (value == null) return '';
  const key = String(value).trim().toLowerCase();
  return key;
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

const resolvePortraitKey = id => {
  const normalized = normalizeKey(id);
  if (!normalized) return '';
  if (normalized === 'mimic') return 'mimic';
  if (metadataOverrides.portraitAliases.has(normalized)) {
    return metadataOverrides.portraitAliases.get(normalized);
  }
  if (defaultPortraitAliases.has(normalized)) {
    return defaultPortraitAliases.get(normalized);
  }
  if (normalized.startsWith('jellyfish_')) return 'jellyfish';
  return normalized;
};

const resolveSummonKey = id => {
  const normalized = normalizeKey(id);
  if (!normalized) return '';
  if (metadataOverrides.summonAliases.has(normalized)) {
    return metadataOverrides.summonAliases.get(normalized);
  }
  if (normalized.startsWith('jellyfish_')) return 'jellyfish';
  if (normalized === 'lightstreamsword') return 'lightstreamswords';
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

const summonPortraitKeys = new Set(['jellyfish']);

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

const resolveMimicPortrait = () => {
  const cached = getCachedPortrait('player');
  if (cached) return cached;
  const playerList = getPortraitGalleryByKey('player');
  if (playerList.length) {
    const chosen = chooseRandom(playerList) ?? playerList[0];
    setCachedPortrait('player', chosen);
    return chosen;
  }
  const pool = getFallbackPool();
  if (pool.length) {
    const chosen = chooseRandom(pool) ?? pool[0];
    setCachedPortrait('player', chosen);
    return chosen;
  }
  setCachedPortrait('player', STATIC_FALLBACK);
  return STATIC_FALLBACK;
};

export const getCharacterImage = (characterId, options = {}) => {
  if (!characterId) return STATIC_FALLBACK;
  const id = String(characterId);
  if (!id.trim()) return STATIC_FALLBACK;

  if (id === 'mimic') {
    return resolveMimicPortrait();
  }

  const cached = getCachedPortrait(id);
  if (cached) return cached;

  const key = resolvePortraitKey(id);
  const gallery = getPortraitGalleryByKey(key);
  const pool = getFallbackPool();

  const persist = url => {
    setCachedPortrait(id, url);
    return url;
  };

  const isPlayer = options === true || (options && options.isPlayer === true);

  if (isPlayer || id === 'lady_echo') {
    if (gallery.length) {
      const chosen = chooseRandom(gallery) ?? gallery[0];
      return persist(chosen);
    }
    if (pool.length) {
      const chosen = chooseRandom(pool) ?? pool[0];
      return persist(chosen);
    }
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
    return persist(fallback);
  }

  return persist(STATIC_FALLBACK);
};

export const getAvailableCharacterIds = () => {
  const ids = new Set();
  portraitCanonicals.forEach(value => ids.add(value));
  metadataOverrides.portraitCanonicals.forEach(value => ids.add(value));
  summonPortraitKeys.forEach(key => {
    if (summonCanonicals.has(key)) ids.add(summonCanonicals.get(key));
  });
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
  if (!entries.length) return STATIC_FALLBACK;
  let pool = entries;
  if (typeof options.filter === 'function') {
    const filtered = entries.filter(entry => options.filter(entry));
    if (filtered.length) {
      pool = filtered;
    }
  }
  if (!pool.length) return STATIC_FALLBACK;
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
  let url = normalizedId ? collection.map.get(normalizedId) : null;
  if (!url && normalizedId) {
    const compact = stripNonAlphanumeric(normalizedId);
    if (compact) {
      url = collection.map.get(compact) ?? null;
    }
  }
  if (!url) {
    url = collection.fallback;
  }
  rewardCache.set(cacheKey, url);
  return url;
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
  rewardCache.clear();
  materialIconCache.clear();
  clearCharacterImageCache();
  markRegistryUpdated();
};

export { normalizeAssetUrl };
