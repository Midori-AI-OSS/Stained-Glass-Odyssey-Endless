import { afterEach, beforeAll, describe, expect, test } from 'bun:test';

if (typeof import.meta.glob !== 'function') {
  test('asset registry unsupported', () => {});
} else {
  const {
    getCharacterImage,
    getDefaultFallback,
    getRandomFallback,
    getSummonArt,
    getSummonGallery,
    getPortraitRarityFolders,
    getRewardArt,
    getGlyphArt,
    getMaterialIcon,
    getMaterialFallbackIcon,
    onMaterialIconError,
    registerAssetManifest,
    registerAssetMetadata,
    resetAssetRegistryOverrides
  } = await import('../src/lib/systems/assetRegistry.js');

  describe('asset registry', () => {
    beforeAll(() => {
      registerAssetManifest({
        portraits: [
          {
            id: 'echo',
            folder: 'characters/echo',
            aliases: ['lady_echo']
          },
          {
            id: 'mimic',
            folder: null,
            aliases: [],
            mimic: { mode: 'player_mirror', target: 'player' }
          }
        ],
        summons: [
          {
            id: 'jellyfish',
            folder: 'summons/jellyfish',
            aliases: ['jellyfish_healing', 'jellyfish_electric', 'jellyfish_poison', 'jellyfish_shielding'],
            portrait: true
          },
          {
            id: 'lightstreamswords',
            folder: 'summons/lightstreamswords',
            aliases: ['lightstreamsword']
          }
        ]
      });
    });

    afterEach(() => {
      resetAssetRegistryOverrides();
    });

    test('resolves built-in portrait assets', () => {
      const url = getCharacterImage('becca');
      expect(typeof url).toBe('string');
      expect(url.includes('becca')).toBe(true);
    });

    test('resolves summon alias portraits from canonical gallery', () => {
      const aliasUrl = getCharacterImage('jellyfish_electric');
      expect(typeof aliasUrl).toBe('string');
      expect(aliasUrl).not.toBe(getDefaultFallback());

      const galleryUrls = getSummonGallery('jellyfish').map(entry => entry.url);
      expect(Array.isArray(galleryUrls)).toBe(true);
      expect(galleryUrls.length).toBeGreaterThan(0);
      expect(galleryUrls).toContain(aliasUrl);
    });

    test('derives mimic portraits using manifest mirror rule', () => {
      const url = getCharacterImage('mimic', { metadata: { portrait_pool: 'player_mirror' } });
      expect(typeof url).toBe('string');
    });

    test('provides fallback assets for unknown ids', () => {
      const portrait = getCharacterImage('unknown_entity');
      expect(typeof portrait).toBe('string');
      const fallback = getRandomFallback();
      expect(typeof fallback).toBe('string');
    });

    test('resolves summon art galleries', () => {
      const art = getSummonArt('lightstreamswords');
      expect(typeof art).toBe('string');
      expect(art.length).toBeGreaterThan(0);
      const gallery = getSummonGallery('lightstreamswords');
      expect(Array.isArray(gallery)).toBe(true);
      expect(gallery.length).toBeGreaterThan(0);
    });

    test('accepts metadata overrides for portraits and summons', () => {
      registerAssetMetadata({
        portraitAliases: { hero_prime: 'becca' },
        portraitOverrides: { mystic: 'https://example.com/mystic.png' },
        fallbackOverrides: ['https://example.com/fallback.png'],
        backgroundOverrides: ['https://example.com/background.png'],
        summonOverrides: {
          phoenix: { url: 'https://example.com/phoenix.png', element: 'fire' }
        },
        rarityFolders: { mystic: ['5star', '6star'] }
      });

      const aliasUrl = getCharacterImage('hero_prime');
      expect(typeof aliasUrl).toBe('string');
      expect(aliasUrl.includes('becca') || aliasUrl.includes('midoriai-logo')).toBe(true);

      const overrideUrl = getCharacterImage('mystic');
      expect(overrideUrl).toBe('https://example.com/mystic.png');

      const rarity = getPortraitRarityFolders('mystic');
      expect(rarity).toContain('5star');
      expect(rarity).toContain('6star');

      const phoenixArt = getSummonArt('phoenix');
      expect(phoenixArt).toBe('https://example.com/phoenix.png');

      const phoenixGallery = getSummonGallery('phoenix');
      expect(phoenixGallery[0]?.metadata?.element).toBe('fire');
    });

    test('caches reward art and falls back to generic icons', () => {
      const first = getRewardArt('item', 'fire1');
      const second = getRewardArt('item', 'fire1');
      expect(typeof first).toBe('string');
      expect(first.length).toBeGreaterThan(0);
      expect(second).toBe(first);

      const fallback = getRewardArt('item', 'missing_item');
      expect(fallback).toBe(getMaterialFallbackIcon());

      const unknownType = getRewardArt('glyph', 'anything');
      expect(unknownType).toBe(getMaterialFallbackIcon());
    });

    test('pairs glyph art using id or name compaction', () => {
      const glyph = getGlyphArt('card', { id: 'adamantine_band', name: 'Adamantine Band' });
      expect(typeof glyph).toBe('string');
      expect(glyph.length).toBeGreaterThan(0);

      const missing = getGlyphArt('relic', { id: 'does_not_exist', name: 'Unknown' });
      expect(missing).toBe('');

      const unsupported = getGlyphArt('item', { id: 'adamantine_band', name: 'Adamantine Band' });
      expect(unsupported).toBe('');
    });

    test('loads material icons with cache support and fallback handler', () => {
      const icon = getMaterialIcon('fire_1');
      const cached = getMaterialIcon('fire_1');
      expect(typeof icon).toBe('string');
      expect(icon.length).toBeGreaterThan(0);
      expect(cached).toBe(icon);

      const generic = getMaterialIcon('void_99');
      expect(typeof generic).toBe('string');
      expect(generic.length).toBeGreaterThan(0);

      const event = { target: { src: '' } };
      onMaterialIconError(event);
      expect(event.target.src).toBe(getMaterialFallbackIcon());
    });
  });
}
