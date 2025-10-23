import { normalizeRewardPreview } from './rewardPreviewFormatter.js';

function cloneStagingBucketEntries(values) {
  if (!Array.isArray(values)) {
    return [];
  }
  return values.map((entry) => {
    if (!entry || typeof entry !== 'object') {
      return entry;
    }
    const clone = { ...entry };
    if (clone.preview) {
      clone.preview = normalizeRewardPreview(clone.preview);
    }
    return clone;
  });
}

function resolveEffectiveSource(source, fallback) {
  if (source && typeof source === 'object') {
    return source;
  }
  if (fallback && typeof fallback === 'object') {
    return fallback;
  }
  return {};
}

export function normalizeRewardStagingPayload(source, fallback) {
  const effective = resolveEffectiveSource(source, fallback);
  return {
    cards: cloneStagingBucketEntries(effective.cards),
    relics: cloneStagingBucketEntries(effective.relics),
    items: cloneStagingBucketEntries(effective.items)
  };
}

export function resolveRewardStagingPayload({ current, next, type, intent } = {}) {
  const normalizedType = type === 'card' || type === 'relic' ? type : null;
  const normalizedIntent = typeof intent === 'string' ? intent : null;
  const normalized = normalizeRewardStagingPayload(next, current);

  if (normalizedIntent === 'confirm' && normalizedType) {
    const bucketKey = normalizedType === 'card' ? 'cards' : 'relics';
    const responseIncludesBucket =
      next &&
      typeof next === 'object' &&
      Object.prototype.hasOwnProperty.call(next, bucketKey);

    if (!responseIncludesBucket) {
      return { ...normalized, [bucketKey]: [] };
    }
  }

  return normalized;
}
