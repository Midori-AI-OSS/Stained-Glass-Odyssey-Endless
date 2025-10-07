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
  'kenney_audio/impactGeneric_light_001'
];

const coerceOptions = options => (options && typeof options === 'object' ? { ...options } : {});

export function createDealSfx(volumeSteps = 5, options = {}) {
  if (typeof Audio === 'undefined') return null;
  const opts = coerceOptions(options);
  if (opts.fallback === undefined) {
    opts.fallback = true;
  }
  const clip = getSfxClip(DEAL_SFX_KEYS, opts);
  if (!clip) return null;
  try {
    const audio = new Audio(clip);
    const numericVolume = Number(volumeSteps);
    const clamped = Number.isFinite(numericVolume)
      ? Math.max(0, Math.min(10, numericVolume))
      : 0;
    audio.volume = clamped / 10;
    return audio;
  } catch {
    return null;
  }
}

export function createRewardDropSfx(volumeSteps = 5, options = {}) {
  if (typeof Audio === 'undefined') return null;
  const opts = coerceOptions(options);
  if (opts.fallback === undefined) {
    opts.fallback = true;
  }
  const clip = getSfxClip(REWARD_DROP_SFX_KEYS, opts);
  if (!clip) return null;
  try {
    const audio = new Audio(clip);
    const numericVolume = Number(volumeSteps);
    const clamped = Number.isFinite(numericVolume)
      ? Math.max(0, Math.min(10, numericVolume))
      : 0;
    audio.volume = clamped / 10;
    return audio;
  } catch {
    return null;
  }
}
