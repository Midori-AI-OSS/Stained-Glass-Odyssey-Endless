import { getSfxClip } from './assetRegistry.js';

const DEAL_SFX_KEYS = [
  'ui/pull/deal',
  'kenney_audio/bookflip1',
  'kenney_audio/bookflip2',
  'kenney_audio/switch22'
];

const REWARD_DROP_SFX_KEYS = [
  'ui/reward/drop',
  'kenney_audio/handleCoins',
  'kenney_audio/handleCoins2',
  'kenney_audio/dropLeather',
  'kenney_audio/impactGeneric_light_001'
];

const coerceOptions = options => (options && typeof options === 'object' ? { ...options } : {});

const clampVolumeSteps = value => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  if (numeric <= 0) return 0;
  if (numeric >= 10) return 10;
  return numeric;
};

const createNoopPlayer = volume => ({
  play: () => Promise.resolve(false),
  stop: () => {},
  setVolume: () => {},
  getVolume: () => clampVolumeSteps(volume),
  get element() {
    return null;
  }
});

export function createSequentialSfxPlayer({ keys = [], volume = 5, reducedMotion = false, options = {} } = {}) {
  if (typeof Audio === 'undefined') return null;
  const normalizedKeys = Array.isArray(keys) ? keys : [keys];
  const filteredKeys = normalizedKeys.filter(key => typeof key === 'string' && key.length > 0);
  if (filteredKeys.length === 0) return null;

  if (reducedMotion) {
    return createNoopPlayer(volume);
  }

  const opts = coerceOptions(options);
  if (opts.fallback === undefined) {
    opts.fallback = true;
  }

  const clip = getSfxClip(filteredKeys, opts);
  if (!clip) return null;

  let steps = clampVolumeSteps(volume);
  let baseElement = null;

  const ensureBaseElement = () => {
    if (baseElement) return baseElement;
    try {
      baseElement = new Audio(clip);
      baseElement.volume = steps / 10;
      return baseElement;
    } catch {
      baseElement = null;
      return null;
    }
  };

  const stop = () => {
    if (!baseElement) return;
    try {
      baseElement.pause();
      baseElement.currentTime = 0;
    } catch {
      // ignore failures when resetting audio nodes
    }
  };

  const play = () => {
    const base = ensureBaseElement();
    if (!base) return Promise.resolve(false);
    let node = base;
    if (!base.paused) {
      try {
        node = base.cloneNode(true);
      } catch {
        node = base;
      }
    }

    try {
      node.volume = steps / 10;
    } catch {
      // ignore volume assignment failures on cloned nodes
    }

    if (node === base) {
      try {
        node.currentTime = 0;
      } catch {
        // ignore failures while rewinding audio
      }
    }

    try {
      const result = node.play();
      if (result && typeof result.catch === 'function') {
        return result.catch(error => {
          if (error?.name !== 'AbortError') {
            try {
              console.debug('[sfx] playback failed', error);
            } catch {}
          }
          return false;
        });
      }
      return Promise.resolve(true);
    } catch (error) {
      if (error?.name !== 'AbortError') {
        try {
          console.debug('[sfx] playback failed', error);
        } catch {}
      }
      return Promise.resolve(false);
    }
  };

  const setVolume = nextSteps => {
    steps = clampVolumeSteps(nextSteps);
    if (!baseElement) return;
    try {
      baseElement.volume = steps / 10;
    } catch {
      // ignore volume assignment failures
    }
  };

  return {
    play,
    stop,
    setVolume,
    getVolume: () => steps,
    get element() {
      return ensureBaseElement();
    }
  };
}

export function createDealSfx(volumeSteps = 5, options = {}) {
  const opts = coerceOptions(options);
  const { reducedMotion = false, ...rest } = opts;
  return createSequentialSfxPlayer({
    keys: DEAL_SFX_KEYS,
    volume: volumeSteps,
    reducedMotion,
    options: rest
  });
}

export function createRewardDropSfx(volumeSteps = 5, options = {}) {
  const opts = coerceOptions(options);
  const { reducedMotion = false, ...rest } = opts;
  return createSequentialSfxPlayer({
    keys: REWARD_DROP_SFX_KEYS,
    volume: volumeSteps,
    reducedMotion,
    options: rest
  });
}
