import { afterEach, describe, expect, test } from 'bun:test';

if (typeof import.meta.glob !== 'function') {
  test('asset registry unsupported', () => {});
} else {
  const {
    getCharacterImage,
    getRandomFallback,
    getSummonArt,
    getSummonGallery,
    getPortraitRarityFolders,
    registerAssetMetadata,
    resetAssetRegistryOverrides
  } = await import('../src/lib/systems/assetRegistry.js');

  describe('asset registry', () => {
    afterEach(() => {
      resetAssetRegistryOverrides();
    });

    test('resolves built-in portrait assets', () => {
      const url = getCharacterImage('becca');
      expect(typeof url).toBe('string');
      expect(url.includes('becca')).toBe(true);
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
  });
}
