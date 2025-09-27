import { afterAll, beforeAll, describe, expect, test } from 'bun:test';

let registry;

beforeAll(async () => {
  const musicUrl = '/__fixtures__/music/luna/normal/theme.mp3';
  const sfxUrl = '/__fixtures__/sfx/ui/deal.ogg';
  globalThis.__assetRegistryGlob = (pattern) => {
    if (pattern.includes('/music/')) {
      return {
        '../assets/music/luna/normal/theme.mp3': musicUrl
      };
    }
    if (pattern.includes('/sfx/')) {
      return {
        '../assets/sfx/kenney_audio/bookFlip1.ogg': sfxUrl
      };
    }
    return {};
  };
  registry = await import('../src/lib/systems/assetRegistry.js');
});

afterAll(() => {
  delete globalThis.__assetRegistryGlob;
});

describe('asset registry audio helpers', () => {
  test('resolves character playlists from disk', () => {
    const playlist = registry.getMusicPlaylist('luna', 'normal');
    expect(Array.isArray(playlist)).toBe(true);
    expect(playlist.length).toBeGreaterThan(0);
  });

  test('music helpers respect reduced-motion preferences', () => {
    const playlist = registry.getMusicPlaylist('luna', 'normal', { reducedMotion: true });
    expect(playlist).toEqual([]);
    const fallback = registry.getMusicFallbackPlaylist('normal', { reducedMotion: true });
    expect(fallback).toEqual([]);
    const any = registry.getAllMusicTracks({ reducedMotion: true });
    expect(any).toEqual([]);
    const random = registry.getRandomMusicTrack('luna', 'normal', { reducedMotion: true });
    expect(random).toBe('');
  });

  test('sfx helpers provide resolved clips and handle fallbacks', () => {
    const clip = registry.getSfxClip('ui/pull/deal');
    expect(typeof clip).toBe('string');
    expect(clip.length).toBeGreaterThan(0);

    const fallback = registry.getSfxClip('missing-sfx', { fallback: true });
    expect(typeof fallback).toBe('string');
    expect(fallback.length).toBeGreaterThan(0);

    const muted = registry.getSfxClip('ui/pull/deal', { reducedMotion: true });
    expect(muted).toBe('');
  });

  test('available sfx keys include alias entries', () => {
    const keys = registry.getAvailableSfxKeys();
    expect(Array.isArray(keys)).toBe(true);
    expect(keys).toContain('ui/pull/deal');
  });
});
