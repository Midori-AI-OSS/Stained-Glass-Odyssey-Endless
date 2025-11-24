const TIER_SUFFIXES = [
  { tier: 'glitched', suffix: '_glitched' },
  { tier: 'prime', suffix: '_prime' },
  { tier: 'boss', suffix: '_boss' }
];

const TIER_PRIORITY = TIER_SUFFIXES.reduce((acc, entry, index) => {
  acc[entry.tier] = index;
  return acc;
}, {});
TIER_PRIORITY.normal = TIER_SUFFIXES.length;

function derivePassiveTier(id) {
  if (!id || typeof id !== 'string') {
    return { baseId: '', tier: 'normal' };
  }
  const normalizedId = id.toLowerCase();
  for (const { tier, suffix } of TIER_SUFFIXES) {
    if (normalizedId.endsWith(suffix)) {
      return {
        baseId: id.slice(0, id.length - suffix.length),
        tier
      };
    }
  }
  return { baseId: id, tier: 'normal' };
}

export function dedupeTieredPassives(passives = []) {
  if (!Array.isArray(passives)) {
    return [];
  }

  const seen = new Map();
  const baseOrder = [];

  for (const entry of passives) {
    if (!entry) {
      continue;
    }
    const id = typeof entry === 'string' ? entry : entry.id;
    if (!id || typeof id !== 'string') {
      continue;
    }
    const { baseId, tier } = derivePassiveTier(id);
    if (!baseId) {
      continue;
    }
    const rank = TIER_PRIORITY[tier];
    if (!seen.has(baseId)) {
      seen.set(baseId, { entry, rank });
      baseOrder.push(baseId);
      continue;
    }
    const current = seen.get(baseId);
    if (rank < current.rank) {
      seen.set(baseId, { entry, rank });
    }
  }

  return baseOrder.map((baseId) => seen.get(baseId).entry);
}
