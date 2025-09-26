import {
  getMusicPlaylist as registryGetMusicPlaylist,
  getMusicFallbackPlaylist as registryGetMusicFallbackPlaylist,
  getAllMusicTracks as registryGetAllMusicTracks,
  getRandomMusicTrack as registryGetRandomMusicTrack
} from './assetRegistry.js';

export function shuffle(array) {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

const coerceOptions = options => (options && typeof options === 'object' ? options : undefined);

export function getMusicTracks(options) {
  return registryGetAllMusicTracks(coerceOptions(options));
}

export function getCharacterPlaylist(charName, category = 'normal', options) {
  return registryGetMusicPlaylist(String(charName || ''), category, coerceOptions(options));
}

export function getRandomMusicTrack(charName, category = 'normal', options) {
  return registryGetRandomMusicTrack(String(charName || ''), category, coerceOptions(options));
}

export function getFallbackPlaylist(category = 'normal', options) {
  return registryGetMusicFallbackPlaylist(category, coerceOptions(options));
}
