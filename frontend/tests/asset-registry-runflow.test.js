import { afterEach, beforeEach, describe, expect, test } from 'bun:test';

if (typeof import.meta.glob !== 'function') {
  test('asset registry run flow unsupported', () => {});
} else {
  const {
    getCharacterImage,
    getSummonArt,
    getRewardArt,
    getRewardMetadata,
    getMusicPlaylist,
    getMusicFallbackPlaylist,
    getRandomMusicTrack,
    getMusicTrackMetadata,
    registerAssetMetadata,
    resetAssetRegistryOverrides,
    setAssetRegistryTelemetry,
    resetAssetRegistryTelemetry
  } = await import('../src/lib/systems/assetRegistry.js');
  const { getDotImage, getEffectImage } = await import('../src/lib/systems/assetLoader.js');

  describe('asset registry run flow', () => {
    let telemetryEvents = [];

    beforeEach(() => {
      telemetryEvents = [];
      resetAssetRegistryTelemetry();
      setAssetRegistryTelemetry(event => {
        telemetryEvents.push(event);
      });
    });

    afterEach(() => {
      setAssetRegistryTelemetry(null);
      resetAssetRegistryOverrides();
    });

    test('resolves core assets and records fallback telemetry', () => {
      const portrait = getCharacterImage('becca');
      expect(typeof portrait).toBe('string');
      expect(portrait.length).toBeGreaterThan(0);

      telemetryEvents.length = 0;
      const missingPortrait = getCharacterImage('missing_test_id');
      expect(typeof missingPortrait).toBe('string');
      expect(telemetryEvents.some(event => event.kind === 'portrait-fallback')).toBe(true);

      const summonUrl = getSummonArt('jellyfish');
      expect(typeof summonUrl).toBe('string');

      telemetryEvents.length = 0;
      const missingSummon = getSummonArt('missing_summon_id');
      expect(typeof missingSummon).toBe('string');
      expect(telemetryEvents.some(event => event.kind === 'summon-fallback')).toBe(true);

      const dot = getDotImage('fire_dot');
      expect(typeof dot).toBe('string');

      const effect = getEffectImage({ name: 'attack_up', modifiers: { attack: 5 } });
      expect(typeof effect).toBe('string');

      telemetryEvents.length = 0;
      const reward = getRewardArt('item', 'unknown_reward');
      expect(typeof reward).toBe('string');
      expect(telemetryEvents.some(event => event.kind === 'reward-fallback')).toBe(true);
    });

    test('applies metadata overrides for rewards and audio', () => {
      registerAssetMetadata({
        rewardOverrides: {
          item: {
            ember_1: { url: 'https://example.com/ember.png', metadata: { source: 'test-suite' } }
          }
        },
        musicOverrides: {
          becca: {
            defaultCategory: 'boss',
            tracks: {
              boss: [
                {
                  url: 'https://example.com/audio/boss-theme.mp3',
                  metadata: { composer: 'QA', bpm: 120 }
                }
              ]
            }
          }
        },
        musicFallbacks: {
          normal: [
            {
              url: 'https://example.com/audio/fallback-theme.mp3',
              metadata: { composer: 'Fallback Team' }
            }
          ]
        },
        musicAnnotations: {
          'https://example.com/audio/boss-theme.mp3': { mood: 'intense' }
        }
      });

      const rewardUrl = getRewardArt('item', 'ember_1');
      expect(rewardUrl).toBe('https://example.com/ember.png');
      expect(getRewardMetadata('item', 'ember_1')).toMatchObject({ source: 'test-suite' });

      const bossPlaylist = getMusicPlaylist('becca', 'boss', {});
      expect(bossPlaylist).toContain('https://example.com/audio/boss-theme.mp3');

      const bossMetadata = getMusicTrackMetadata('https://example.com/audio/boss-theme.mp3');
      expect(bossMetadata).toMatchObject({
        character: 'becca',
        category: 'boss',
        composer: 'QA',
        bpm: 120,
        mood: 'intense',
        scope: 'character'
      });

      const fallbackPlaylist = getMusicFallbackPlaylist('normal', {});
      expect(fallbackPlaylist).toContain('https://example.com/audio/fallback-theme.mp3');

      const fallbackMetadata = getMusicTrackMetadata('https://example.com/audio/fallback-theme.mp3');
      expect(fallbackMetadata).toMatchObject({
        category: 'normal',
        composer: 'Fallback Team',
        scope: 'fallback'
      });
    });

    test('music fallback telemetry fires when playlists are empty', () => {
      telemetryEvents.length = 0;
      const track = getRandomMusicTrack('missing_character', 'normal', {});
      expect(track).toBe('');
      expect(telemetryEvents.some(event => event.kind === 'music-fallback')).toBe(true);
    });
  });
}
