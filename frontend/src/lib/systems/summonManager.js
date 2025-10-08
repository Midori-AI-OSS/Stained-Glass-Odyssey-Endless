const DEFAULT_CONFIG = {
  combatantKey: () => '',
  resolveEntityElement: () => 'generic',
  applyLunaSwordVisuals: (entry) => entry,
  normalizeOwnerId: (value) => {
    if (value === undefined || value === null) return '';
    try {
      return String(value);
    } catch {
      return '';
    }
  }
};

export function isSummon(entry) {
  if (!entry || typeof entry !== 'object') return false;
  if (entry.summon_type) return true;
  if (entry.type === 'summon') return true;
  if (entry.is_summon === true) return true;
  return false;
}

export function filterPartyEntities(list) {
  if (!Array.isArray(list)) return [];
  return list.filter((entry) => !isSummon(entry));
}

export function getSummonIdentifier(summon) {
  if (!summon || typeof summon !== 'object') return '';
  const value = summon?.instance_id ?? summon?.id;
  if (value === undefined || value === null) return '';
  try {
    return String(value);
  } catch {
    return '';
  }
}

function normalizeSummonPayload(payload) {
  if (!payload) {
    return [];
  }
  if (Array.isArray(payload)) {
    return payload.filter(Boolean);
  }
  if (payload && typeof payload === 'object') {
    return Object.entries(payload).flatMap(([owner, list]) => {
      const source = Array.isArray(list) ? list : [list];
      return source.filter(Boolean).map((entry) => ({ owner_id: owner, ...entry }));
    });
  }
  return [];
}

function assignAliasValues(renderKey, baseId, summon) {
  const aliasSet = new Set();
  const addAlias = (value) => {
    if (value === undefined || value === null) return;
    try {
      const str = String(value);
      if (str && str !== renderKey) {
        aliasSet.add(str);
      }
    } catch {}
  };
  addAlias(summon?.instance_id);
  addAlias(summon?.id);
  addAlias(baseId);
  return Array.from(aliasSet);
}

export function createSummonManager(config = {}) {
  const settings = { ...DEFAULT_CONFIG, ...config };
  let knownSummons = new Set();
  const renderState = new Map();

  function reset() {
    knownSummons = new Set();
    renderState.clear();
  }

  function prepareSummon(summon, ownerId, side, helpers) {
    if (!summon) return null;

    const { trackHp, summonCounters, seenSummonSlots } = helpers;

    let baseId = getSummonIdentifier(summon);
    if (!baseId) {
      const typeLabel = summon?.summon_type || summon?.type || 'summon';
      const ownerLabel = summon?.summoner_id || ownerId || 'owner';
      const counterKey = `${side}:${ownerLabel}:${typeLabel}`;
      const count = summonCounters.get(counterKey) || 0;
      summonCounters.set(counterKey, count + 1);
      baseId = `${typeLabel}_${ownerLabel}_${count}`;
    }

    const hpKey = settings.combatantKey(`${side}-summon`, baseId, ownerId);
    if (hpKey) {
      trackHp?.(hpKey, summon.hp, summon.max_hp);
    }

    const ownerKey = settings.normalizeOwnerId(ownerId) || 'owner';
    const signatureSource = baseId || summon?.summon_type || summon?.type || 'summon';
    const signature = `${side}:${ownerKey}:${signatureSource}`;
    const slotIndex = seenSummonSlots.get(signature) || 0;
    seenSummonSlots.set(signature, slotIndex + 1);

    let stored = renderState.get(signature);
    if (!stored) {
      stored = [];
      renderState.set(signature, stored);
    }

    let renderKey = '';
    const instanceKey = summon?.instance_id;
    if (instanceKey !== undefined && instanceKey !== null && instanceKey !== '') {
      try {
        renderKey = String(instanceKey);
      } catch {
        renderKey = '';
      }
    }

    if (!renderKey && summon?.renderKey) {
      try {
        renderKey = String(summon.renderKey);
      } catch {
        renderKey = '';
      }
    }

    if (!renderKey && stored[slotIndex]) {
      renderKey = stored[slotIndex];
    }

    if (!renderKey) {
      const baseKey = hpKey || signature;
      renderKey = `${String(baseKey)}#${slotIndex}`;
    }

    if (!renderKey) {
      renderKey = `${signature}#${slotIndex}`;
    }

    if (stored[slotIndex] !== renderKey) {
      stored[slotIndex] = renderKey;
    }

    const anchorIds = assignAliasValues(renderKey, baseId, summon);
    const baseElement = settings.resolveEntityElement?.(summon) ?? 'generic';

    let result = { ...summon, hpKey, renderKey, anchorIds };
    if (baseElement && baseElement !== 'generic') {
      result = { ...result, element: baseElement };
    }

    if (typeof settings.applyLunaSwordVisuals === 'function') {
      const visualized = settings.applyLunaSwordVisuals(result, ownerId, baseElement);
      if (visualized) {
        result = visualized;
      }
    }

    return result;
  }

  function collectSummons(payload, side, helpers) {
    const normalized = normalizeSummonPayload(payload);
    const byOwner = new Map();
    for (const entry of normalized) {
      const owner = entry?.owner_id;
      if (!owner) continue;
      const prepared = prepareSummon(entry, owner, side, helpers);
      if (!prepared) continue;
      if (!byOwner.has(owner)) {
        byOwner.set(owner, []);
      }
      byOwner.get(owner).push(prepared);
    }
    return byOwner;
  }

  function pruneRenderState(seenSummonSlots) {
    for (const [signature, count] of seenSummonSlots) {
      const pool = renderState.get(signature);
      if (pool && pool.length > count) {
        pool.length = count;
      }
    }
    for (const signature of Array.from(renderState.keys())) {
      if (!seenSummonSlots.has(signature)) {
        renderState.delete(signature);
      }
    }
  }

  function detectNewSummons(collections, onNewSummon) {
    const observed = new Set(knownSummons);
    for (const { side, map } of collections) {
      for (const [owner, summons] of map) {
        for (const summon of summons) {
          const ident = getSummonIdentifier(summon);
          if (ident && !observed.has(ident)) {
            if (typeof onNewSummon === 'function') {
              onNewSummon({ side, ownerId: owner, summon });
            }
            observed.add(ident);
            break;
          }
        }
      }
    }
    knownSummons = observed;
  }

  function collectSummonIds(collection, { includeAnchors = false } = {}) {
    const set = new Set();
    for (const summons of collection.values()) {
      for (const summon of summons) {
        const ident = getSummonIdentifier(summon);
        if (ident) {
          set.add(ident);
        }
        if (includeAnchors && Array.isArray(summon?.anchorIds)) {
          for (const alias of summon.anchorIds) {
            if (alias === undefined || alias === null) continue;
            try {
              const str = String(alias);
              if (str) {
                set.add(str);
              }
            } catch {}
          }
        }
      }
    }
    return set;
  }

  function processSnapshot(snapshot, context = {}) {
    const summonCounters = new Map();
    const seenSummonSlots = new Map();
    const helpers = {
      trackHp: context.trackHp,
      summonCounters,
      seenSummonSlots
    };

    const partySummons = collectSummons(snapshot?.party_summons, 'party', helpers);
    const foeSummons = collectSummons(snapshot?.foe_summons, 'foe', helpers);

    detectNewSummons(
      [
        { side: 'party', map: partySummons },
        { side: 'foe', map: foeSummons }
      ],
      context.onNewSummon
    );

    pruneRenderState(seenSummonSlots);

    return {
      partySummons,
      foeSummons,
      partySummonIds: collectSummonIds(partySummons),
      foeSummonIds: collectSummonIds(foeSummons, { includeAnchors: true })
    };
  }

  return {
    processSnapshot,
    reset,
    get knownSummons() {
      return new Set(knownSummons);
    }
  };
}
