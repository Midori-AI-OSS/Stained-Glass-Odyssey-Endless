// viewportState.js
// Helper utilities for GameViewport including settings init,
// room metadata helpers, and background music control.
import { loadSettings } from './settingsStorage.js';
import { getPlayers } from './api.js';
import {
  getCharacterPlaylist,
  getMusicTracks,
  getFallbackPlaylist,
  shuffle,
} from './music.js';

export async function loadInitialState() {
  const saved = loadSettings();
  const settings = {
    sfxVolume: saved.sfxVolume ?? 5,
    musicVolume: saved.musicVolume ?? 5,
    voiceVolume: saved.voiceVolume ?? 5,
    framerate: saved.framerate !== undefined ? Number(saved.framerate) : 60,
    autocraft: true,
    reducedMotion: saved.reducedMotion ?? false,
    showActionValues: saved.showActionValues ?? false,
  };
  let roster = [];
  let user = { level: 1, exp: 0, next_level_exp: 100 };
  try {
    const data = await getPlayers();
    function resolveElement(p) {
      let e = p?.element;
      if (e && typeof e !== 'string') e = e.id || e.name;
      return e && !/generic/i.test(String(e)) ? e : 'Generic';
    }
    roster = data.players.map(p => ({ id: p.id, element: resolveElement(p) }));
    user = data.user || user;
  } catch {
    roster = [];
  }
  return { settings, roster, user };
}

export function mapSelectedParty(roster, selected) {
  return selected.map(id => {
    const info = roster.find(r => r.id === id);
    return { id, element: info?.element || 'Generic' };
  });
}

export function roomLabel(type) {
  switch (String(type || '')) {
    case 'battle-weak':
      return 'Weak Battle';
    case 'battle-normal':
      return 'Normal Battle';
    case 'battle-boss-floor':
      return 'Floor Boss';
    case 'shop':
      return 'Shop';
    case 'start':
      return 'Start';
    default:
      if (!type) return 'Battle';
      return String(type).replace(/\b\w/g, c => c.toUpperCase()).replaceAll('-', ' ');
  }
}

export function roomInfo(mapRooms, currentIndex, currentRoomType, roomData) {
  const cur = mapRooms?.[currentIndex] || null;
  const nxt = mapRooms?.[currentIndex + 1] || null;
  return {
    pressure: cur?.pressure ?? roomData?.pressure ?? 0,
    floorNumber: cur?.floor ?? 1,
    roomNumber: (cur?.index ?? currentIndex ?? 0) + 1,
    currentType: currentRoomType || roomData?.current_room || '',
    nextType: nxt?.room_type || (roomData?.next_room ?? ''),
  };
}

export function rewardOpen(roomData, _battleActive) {
  if (!roomData) return false;
  const hasCards = (roomData?.card_choices?.length || 0) > 0;
  const hasRelics = (roomData?.relic_choices?.length || 0) > 0;
  // Only open the reward overlay for selectable choices (cards/relics).
  // Loot items/gold are displayed via floating messages, not as a blocking popup.
  return Boolean(hasCards || hasRelics);
}

export function selectBattleMusic({ roomType, party = [], foes = [] }) {
  const type = String(roomType || '');
  const category =
    type === 'battle-weak'
      ? 'weak'
      : type === 'battle-boss-floor'
        ? 'boss'
        : 'normal';

  if (type === 'battle-boss-floor') {
    const boss = foes?.[0];
    const name = typeof boss === 'string' ? boss : boss?.id || boss?.name;
    const playlist = getCharacterPlaylist(String(name || '').toLowerCase(), 'boss');
    if (playlist.length) return playlist;
    // Fallback: use fallback library (boss first, then normal)
    const fbBoss = getFallbackPlaylist('boss');
    if (fbBoss.length) return fbBoss;
    return getFallbackPlaylist('normal');
  }

  if (type.startsWith('battle')) {
    const ready = (party?.length || 0) > 0 && (foes?.length || 0) > 0;
    if (!ready) {
      const fb = getFallbackPlaylist(category);
      return fb.length ? fb : [];
    }
  }

  const candidates = [];

  function addCandidate(entity) {
    const name = typeof entity === 'string' ? entity : entity?.id || entity?.name;
    if (!name) return;
    const id = String(name).toLowerCase();
    const list = getCharacterPlaylist(id, category);
    if (!list.length) return;
    const weight = id === 'luna' ? 3 : 1;
    candidates.push({ list, weight });
  }

  party.forEach(addCandidate);
  foes.forEach(addCandidate);

  if (candidates.length === 0) {
    const fb = getFallbackPlaylist(category);
    return fb.length ? fb : [];
  }

  // Weighted random draw
  const total = candidates.reduce((sum, c) => sum + c.weight, 0);
  let roll = Math.random() * total;
  for (const c of candidates) {
    roll -= c.weight;
    if (roll < 0) return c.list;
  }
  return candidates[0].list;
}

// In SSR, global Audio is not defined. Guard all audio operations.
function hasAudio() {
  return typeof Audio !== 'undefined';
}

let gameAudio;
let currentMusicVolume = 5;
let currentPlaylist = [];
// Keep unshuffled source so repeated calls with the same playlist don't restart
let originalPlaylist = [];
let playlistIndex = 0;
let playlistLoop = true;
// No cross-context reuse to avoid mismatched character music between fights

// Session guard to prevent overlapping music instances when playlists change
// or resume events race with new starts. Any stale callbacks from older
// sessions will no-op when they observe a mismatched token.
let playSession = 0;

// Fade control. We apply a multiplicative fade factor to the base volume
// so user volume changes during fades are respected.
let musicFadeFactor = 1; // 0..1
const DEFAULT_FADE_OUT_MS = 400;
const DEFAULT_FADE_IN_MS = 650;
let nextFadeInMs = 0;

let voiceAudio;
let currentVoiceVolume = 5;

function _musicLog(event, payload = {}) {
  try {
    // Keep logs compact and consistent for debugging overlap
    console.info(`[music] ${event}`, payload);
  } catch {}
}

function _applyMusicVolumeNow() {
  if (!gameAudio) return;
  let level = (Number(currentMusicVolume) || 0) / 100;
  level = Math.max(0, Math.min(1, level));
  let fade = Number(musicFadeFactor);
  if (!Number.isFinite(fade)) fade = 1;
  fade = Math.max(0, Math.min(1, fade));
  const vol = Math.max(0, Math.min(1, level * fade));
  try { gameAudio.volume = vol; } catch {}
}

function playNextTrack(session = playSession) {
  if (!hasAudio()) return;
  if (session !== playSession) return; // stale call
  let src = '';
  if (currentPlaylist.length > 0) {
    src = currentPlaylist[playlistIndex];
  } else {
    // Prefer fallback normal category; if empty, any fallback track
    const fb = getFallbackPlaylist('normal');
    if (fb.length) {
      src = fb[Math.floor(Math.random() * fb.length)];
    } else {
      const any = getMusicTracks();
      src = any.length ? any[Math.floor(Math.random() * any.length)] : '';
    }
  }
  if (!src) { _musicLog('start-skip', { session, reason: 'no-src', hadPlaylist: currentPlaylist.length > 0 }); return; }
  gameAudio = new Audio(src);
  // If a fade-in is requested for this start, begin from silence
  if (nextFadeInMs > 0) {
    musicFadeFactor = 0;
  } else {
    musicFadeFactor = 1;
  }
  _applyMusicVolumeNow();
  _musicLog('start', {
    session,
    src,
    index: playlistIndex,
    playlistLength: currentPlaylist.length,
    loop: playlistLoop,
    volume: (Number(currentMusicVolume) || 0) / 100,
    fadeFactor: musicFadeFactor,
    fadeInMs: nextFadeInMs,
  });
  const onEnded = () => {
    if (session !== playSession) return; // ignore if superseded
    _musicLog('ended', { session, src, index: playlistIndex, playlistLength: currentPlaylist.length });
    if (currentPlaylist.length > 0) {
      playlistIndex += 1;
      if (playlistIndex >= currentPlaylist.length) {
        if (playlistLoop) {
          currentPlaylist = shuffle(currentPlaylist);
          playlistIndex = 0;
        } else {
          currentPlaylist = [];
        }
      }
    }
    playNextTrack(session);
  };
  gameAudio.addEventListener('ended', onEnded);
  gameAudio.play().catch(() => {});
  // Kick off fade-in after playback starts
  if (nextFadeInMs > 0) {
    _fadeInCurrent(nextFadeInMs, session);
    nextFadeInMs = 0;
  }
}

export function startGameMusic(volume, playlist = [], loop = true) {
  if (typeof volume === 'number') currentMusicVolume = volume;
  const newSource = Array.isArray(playlist) ? playlist.slice() : [];
  const samePlaylist =
    newSource.length === originalPlaylist.length &&
    newSource.every((src, i) => src === originalPlaylist[i]) &&
    loop === playlistLoop;
  if (samePlaylist && gameAudio) {
    _applyMusicVolumeNow();
    return;
  }
  const oldAudio = gameAudio;
  originalPlaylist = newSource;
  // Advance session so old callbacks no-op
  playSession += 1;
  const sessionForStart = playSession;
  // Prepare new playlist immediately
  if (newSource.length > 0) {
    currentPlaylist = shuffle(newSource);
    playlistIndex = 0;
    playlistLoop = loop;
  } else {
    currentPlaylist = [];
  }
  _musicLog('playlist', { session: sessionForStart, count: currentPlaylist.length });
  if (!hasAudio()) return;
  nextFadeInMs = DEFAULT_FADE_IN_MS;
  playNextTrack(sessionForStart);
  if (oldAudio) {
    _fadeOutAudio(oldAudio, DEFAULT_FADE_OUT_MS).finally(() => {
      try { oldAudio.pause(); } catch {}
    });
  }
}

export function applyMusicVolume(volume) {
  currentMusicVolume = typeof volume === 'number' ? volume : currentMusicVolume;
  _applyMusicVolumeNow();
}

export function playVoice(src, volume) {
  if (!src) return;
  if (!hasAudio()) return;
  if (typeof volume === 'number') currentVoiceVolume = volume;
  stopVoice();
  voiceAudio = new Audio(src);
  voiceAudio.volume = currentVoiceVolume / 100;
  voiceAudio.play().catch(() => {});
}

export function applyVoiceVolume(volume) {
  currentVoiceVolume = typeof volume === 'number' ? volume : currentVoiceVolume;
  if (voiceAudio) {
    voiceAudio.volume = currentVoiceVolume / 100;
  }
}

export function stopVoice() {
  if (voiceAudio) {
    try { voiceAudio.pause(); } catch {}
    voiceAudio = null;
  }
}

export function stopGameMusic() {
  // Also advance session so any pending callbacks become no-ops
  playSession += 1;
  _stopGameAudio(false, DEFAULT_FADE_OUT_MS, playSession);
}

export function resumeGameMusic() {
  if (!hasAudio()) return;
  try {
    if (gameAudio) {
      if (gameAudio.paused) {
        _applyMusicVolumeNow();
        gameAudio.play().catch(() => {});
      }
    } else {
      startGameMusic(currentMusicVolume, currentPlaylist, playlistLoop);
    }
  } catch {}
}

function _stopGameAudio(bumpSession = false, fadeMs = 0, session = playSession) {
  if (bumpSession) playSession += 1;
  const localSession = session;
  if (!gameAudio) return;
  if (!hasAudio()) { gameAudio = null; return; }
  const src = gameAudio?.src || '';
  const t = (() => { try { return gameAudio?.currentTime || 0; } catch { return 0; } })();
  _musicLog('stop-request', { session: localSession, src, fadeMs, at: t });
  if (fadeMs > 0) {
    return _fadeOutCurrent(fadeMs, localSession).finally(() => {
      if (localSession !== playSession) return;
      try { gameAudio?.pause(); } catch {}
      gameAudio = null;
      musicFadeFactor = 1; // reset
      _musicLog('stopped', { session: localSession, src });
    });
  } else {
    try { gameAudio.pause(); } catch {}
    gameAudio = null;
    musicFadeFactor = 1;
    _musicLog('stopped', { session: localSession, src });
    return Promise.resolve();
  }
}

function _fadeOutCurrent(ms, session) {
  if (!gameAudio) return Promise.resolve();
  return new Promise((resolve) => {
    const start = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    const step = (nowTs) => {
      if (session !== playSession) return resolve();
      const now = typeof nowTs === 'number' ? nowTs : ((typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now());
      const t = Math.max(0, Math.min(1, (now - start) / ms));
      musicFadeFactor = Math.max(0, Math.min(1, 1 - t));
      _applyMusicVolumeNow();
      if (t < 1 && gameAudio) {
        if (typeof requestAnimationFrame !== 'undefined') requestAnimationFrame(step);
        else setTimeout(() => step(), 16);
      } else {
        resolve();
      }
    };
    if (typeof requestAnimationFrame !== 'undefined') requestAnimationFrame(step);
    else setTimeout(() => step(), 0);
  });
}

function _fadeInCurrent(ms, session) {
  if (!gameAudio) return;
  const start = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
  const step = (nowTs) => {
    if (session !== playSession) return;
    const now = typeof nowTs === 'number' ? nowTs : ((typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now());
    const t = Math.max(0, Math.min(1, (now - start) / ms));
    musicFadeFactor = Math.max(0, Math.min(1, t));
    _applyMusicVolumeNow();
    if (t < 1 && gameAudio) {
      if (typeof requestAnimationFrame !== 'undefined') requestAnimationFrame(step);
      else setTimeout(() => step(), 16);
    }
  };
  if (typeof requestAnimationFrame !== 'undefined') requestAnimationFrame(step);
  else setTimeout(() => step(), 0);
}

function _fadeOutAudio(audio, ms) {
  if (!audio) return Promise.resolve();
  return new Promise((resolve) => {
    const start = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    const initial = (() => { try { return audio.volume; } catch { return 1; } })();
    const step = (nowTs) => {
      const now = typeof nowTs === 'number' ? nowTs : ((typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now());
      const t = Math.max(0, Math.min(1, (now - start) / ms));
      try { audio.volume = initial * (1 - t); } catch {}
      if (t < 1 && audio) {
        if (typeof requestAnimationFrame !== 'undefined') requestAnimationFrame(step);
        else setTimeout(() => step(), 16);
      } else {
        resolve();
      }
    };
    if (typeof requestAnimationFrame !== 'undefined') requestAnimationFrame(step);
    else setTimeout(() => step(), 0);
  });
}
