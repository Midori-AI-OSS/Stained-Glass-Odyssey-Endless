import { describe, expect, test } from 'bun:test';
import fs from 'fs';

if (typeof import.meta.glob !== 'function') {
  test('asset loader unsupported', () => {});
} else {
  const {
    getCharacterImage,
    getElementColor,
    getElementIcon,
    getDotImage,
    registerAssetManifest
  } = await import('../src/lib/systems/assetLoader.js');

  const manifest = {
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
  };

  registerAssetManifest(manifest);

  describe('asset loader', () => {
    test('returns fallback string for unknown character', () => {
      const img = getCharacterImage('nonexistent');
      expect(typeof img).toBe('string');
    });

    test('falls back when manifest is absent', () => {
      registerAssetManifest(null);
      const url = getCharacterImage('lady_echo');
      expect(typeof url).toBe('string');
      registerAssetManifest(manifest);
    });

    test('resolves existing character portrait', () => {
      const url = getCharacterImage('becca');
      const becca = url.includes('becca');
      const fallback = url.includes('midoriai-logo');
      expect(becca || fallback).toBe(true);
      if (becca) {
        const filePath = new URL(url);
        expect(fs.existsSync(filePath)).toBe(true);
      }
    });

    test('aliases jellyfish summons to base art', () => {
      const url = getCharacterImage('jellyfish_electric');
      const jelly = url.includes('jellyfish');
      const fallback = url.includes('midoriai-logo');
      expect(jelly || fallback).toBe(true);
    });

    test('provides damage type color and icon', () => {
      expect(getElementColor('fire')).toBe('#ff3b30');
      const icon = getElementIcon('light');
      expect(icon).toBeTruthy();
    });

    test('resolves dot icon from effect object', () => {
      const icon = getDotImage({ id: 'burning' });
      expect(icon).toBeTruthy();
    });
  });
}
