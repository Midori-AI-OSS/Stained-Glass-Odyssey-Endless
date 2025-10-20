import { get, writable } from 'svelte/store';
import { warn as defaultLogger } from './logger.js';

const DEFAULT_SEQUENCE = Object.freeze(['drops', 'cards', 'relics', 'battle_review']);

const LEGACY_ALIASES = Object.freeze({
  card: 'cards',
  cards: 'cards',
  relic: 'relics',
  relics: 'relics',
  loot: 'drops',
  drop: 'drops',
  drops: 'drops',
  reward: 'drops',
  review: 'battle_review',
  'battle-review': 'battle_review',
  'battle review': 'battle_review',
  'battle_review': 'battle_review'
});

const VALID_PHASES = new Set(DEFAULT_SEQUENCE);

function normalizePhase(value) {
  if (value == null) return null;
  let candidate = String(value).trim().toLowerCase();
  if (!candidate) return null;
  candidate = candidate.replace(/\s+/g, '_');
  const mapped = LEGACY_ALIASES[candidate] ?? candidate;
  return VALID_PHASES.has(mapped) ? mapped : null;
}

function orderPhases(phases, fallbackSequence = DEFAULT_SEQUENCE) {
  const normalizedOrder = [];
  const seen = new Set();
  for (const entry of phases || []) {
    const normalized = normalizePhase(entry);
    if (!normalized || seen.has(normalized)) continue;
    normalizedOrder.push(normalized);
    seen.add(normalized);
  }

  const result = [];
  const used = new Set();
  for (const step of fallbackSequence) {
    if (seen.has(step) && !used.has(step)) {
      result.push(step);
      used.add(step);
    }
  }

  for (const step of normalizedOrder) {
    if (!used.has(step)) {
      result.push(step);
      used.add(step);
    }
  }

  return result;
}

function createSnapshot({
  sequence,
  completedSet,
  raw,
  diagnostics,
  forceCurrent
}) {
  const sanitizedSequence = [];
  const orderSeen = new Set();
  for (const entry of sequence || []) {
    const normalized = normalizePhase(entry);
    if (!normalized || orderSeen.has(normalized)) continue;
    sanitizedSequence.push(normalized);
    orderSeen.add(normalized);
  }

  const normalizedCompleted = new Set();
  for (const value of completedSet || []) {
    const normalized = normalizePhase(value);
    if (normalized && orderSeen.has(normalized)) {
      normalizedCompleted.add(normalized);
    }
  }

  let enforcedCurrent = null;
  if (forceCurrent) {
    const normalized = normalizePhase(forceCurrent);
    if (normalized && orderSeen.has(normalized)) {
      enforcedCurrent = normalized;
      normalizedCompleted.delete(normalized);
      for (const phase of sanitizedSequence) {
        if (phase === normalized) break;
        normalizedCompleted.add(phase);
      }
    }
  }

  const completed = sanitizedSequence.filter((phase) => normalizedCompleted.has(phase));

  let current = null;
  for (const phase of sanitizedSequence) {
    if (!normalizedCompleted.has(phase)) {
      current = phase;
      break;
    }
  }

  if (enforcedCurrent && orderSeen.has(enforcedCurrent)) {
    current = enforcedCurrent;
  }

  let next = null;
  if (current) {
    const startIndex = sanitizedSequence.indexOf(current);
    for (let i = startIndex + 1; i < sanitizedSequence.length; i += 1) {
      const candidate = sanitizedSequence[i];
      if (!normalizedCompleted.has(candidate)) {
        next = candidate;
        break;
      }
    }
  }

  return {
    sequence: sanitizedSequence,
    available: sanitizedSequence.slice(),
    completed,
    current,
    next,
    index: current ? sanitizedSequence.indexOf(current) : -1,
    previous: null,
    raw: raw && typeof raw === 'object' ? { ...raw } : null,
    diagnostics: Array.isArray(diagnostics) ? diagnostics.slice() : []
  };
}

function snapshotsEqual(a, b) {
  if (a === b) return true;
  if (!a || !b) return false;
  if (a.current !== b.current) return false;
  if (a.next !== b.next) return false;
  if (a.index !== b.index) return false;
  if (a.sequence.length !== b.sequence.length) return false;
  for (let i = 0; i < a.sequence.length; i += 1) {
    if (a.sequence[i] !== b.sequence[i]) return false;
  }
  if (a.completed.length !== b.completed.length) return false;
  for (let i = 0; i < a.completed.length; i += 1) {
    if (a.completed[i] !== b.completed[i]) return false;
  }
  return true;
}

export function normalizeRewardProgression(
  payload,
  { hints = {}, fallbackSequence = DEFAULT_SEQUENCE, logger = defaultLogger } = {}
) {
  const diagnostics = [];
  const availableSet = new Set();
  const completedSet = new Set();
  let current = null;

  const readPhaseList = (values, collector, label) => {
    if (!Array.isArray(values)) {
      if (values !== undefined) diagnostics.push(`invalid-${label}`);
      return;
    }
    for (const entry of values) {
      const normalized = normalizePhase(entry);
      if (normalized) collector.add(normalized);
    }
  };

  if (payload && typeof payload === 'object') {
    readPhaseList(payload.available, availableSet, 'available');
    readPhaseList(payload.completed, completedSet, 'completed');
    current = normalizePhase(payload.current_step);
  } else if (payload != null) {
    diagnostics.push('invalid-payload');
  }

  const fallbackHintSet = new Set();
  if (Array.isArray(hints?.fallbackPhases)) {
    for (const entry of hints.fallbackPhases) {
      const normalized = normalizePhase(entry);
      if (normalized) fallbackHintSet.add(normalized);
    }
  }

  const candidatePhases = new Set();
  for (const phase of availableSet) candidatePhases.add(phase);
  for (const phase of completedSet) candidatePhases.add(phase);
  if (current) candidatePhases.add(current);
  for (const phase of fallbackHintSet) candidatePhases.add(phase);

  if (candidatePhases.size === 0) {
    diagnostics.push('empty-available-fallback');
    for (const phase of fallbackSequence) {
      candidatePhases.add(phase);
    }
  }

  const ordered = orderPhases(candidatePhases, fallbackSequence);
  if (ordered.length === 0) {
    diagnostics.push('empty-sequence');
    const snapshot = createSnapshot({
      sequence: [],
      completedSet: new Set(),
      raw: null,
      diagnostics,
      forceCurrent: null
    });
    if (diagnostics.length > 0 && typeof logger === 'function') {
      try {
        logger('rewardPhaseMachine: empty progression sequence', { diagnostics, payload });
      } catch {}
    }
    return snapshot;
  }

  const snapshot = createSnapshot({
    sequence: ordered,
    completedSet,
    raw: payload && typeof payload === 'object' ? payload : null,
    diagnostics,
    forceCurrent: current
  });

  if (!snapshot.current && ordered.length > 0) {
    diagnostics.push('no-active-phase');
    snapshot.diagnostics = diagnostics.slice();
    if (typeof logger === 'function') {
      try {
        logger('rewardPhaseMachine: missing active phase', { diagnostics, payload });
      } catch {}
    }
    return snapshot;
  }

  snapshot.diagnostics = diagnostics.slice();
  if (diagnostics.length > 0 && typeof logger === 'function') {
    try {
      logger('rewardPhaseMachine: normalized with fallbacks', { diagnostics, payload });
    } catch {}
  }
  return snapshot;
}

export function createRewardPhaseController({
  logger = defaultLogger,
  fallbackSequence = DEFAULT_SEQUENCE
} = {}) {
  const store = writable(
    createSnapshot({
      sequence: [],
      completedSet: new Set(),
      raw: null,
      diagnostics: [],
      forceCurrent: null
    })
  );
  const listeners = new Map();

  function emit(event, detail) {
    const handlers = listeners.get(event);
    if (!handlers) return;
    for (const handler of handlers) {
      try {
        handler(detail);
      } catch (error) {
        if (typeof logger === 'function') {
          try {
            logger('rewardPhaseMachine: listener error', {
              event,
              message: error?.message || String(error)
            });
          } catch {}
        }
      }
    }
  }

  function getSnapshot() {
    return get(store);
  }

  function applySnapshot(nextSnapshot, reason) {
    const previous = getSnapshot();
    if (snapshotsEqual(previous, nextSnapshot)) {
      return previous;
    }
    const current = { ...nextSnapshot, previous: previous.current ?? null };
    store.set(current);

    if (previous.current && previous.current !== current.current) {
      emit('exit', {
        phase: previous.current,
        to: current.current,
        reason,
        snapshot: current
      });
    }

    if (current.current && previous.current !== current.current) {
      emit('enter', {
        phase: current.current,
        from: previous.current,
        reason,
        snapshot: current
      });
    }

    emit('change', {
      previous,
      current,
      reason
    });

    return current;
  }

  function ingest(progression, { hints, reason = 'ingest' } = {}) {
    const normalized = normalizeRewardProgression(progression, {
      hints,
      fallbackSequence,
      logger
    });
    return applySnapshot(normalized, reason);
  }

  function advance() {
    const snapshot = getSnapshot();
    if (!snapshot.current) return snapshot;
    const completedSet = new Set(snapshot.completed);
    completedSet.add(snapshot.current);
    const nextSnapshot = createSnapshot({
      sequence: snapshot.sequence,
      completedSet,
      raw: snapshot.raw,
      diagnostics: [],
      forceCurrent: null
    });
    return applySnapshot(nextSnapshot, 'advance');
  }

  function skipTo(phase) {
    const target = normalizePhase(phase);
    if (!target) return getSnapshot();
    const snapshot = getSnapshot();
    let sequence = snapshot.sequence;
    if (!sequence.includes(target)) {
      const candidateSet = new Set([...sequence, target]);
      sequence = orderPhases(candidateSet, fallbackSequence);
    }
    const completedSet = new Set(snapshot.completed);
    for (const step of sequence) {
      if (step === target) break;
      completedSet.add(step);
    }
    completedSet.delete(target);
    const nextSnapshot = createSnapshot({
      sequence,
      completedSet,
      raw: snapshot.raw,
      diagnostics: [],
      forceCurrent: target
    });
    return applySnapshot(nextSnapshot, 'skip');
  }

  function reset() {
    const nextSnapshot = createSnapshot({
      sequence: [],
      completedSet: new Set(),
      raw: null,
      diagnostics: [],
      forceCurrent: null
    });
    return applySnapshot(nextSnapshot, 'reset');
  }

  function on(event, handler) {
    if (typeof handler !== 'function') return () => {};
    if (!listeners.has(event)) {
      listeners.set(event, new Set());
    }
    const bucket = listeners.get(event);
    bucket.add(handler);
    return () => off(event, handler);
  }

  function off(event, handler) {
    const bucket = listeners.get(event);
    if (!bucket) return;
    bucket.delete(handler);
    if (bucket.size === 0) listeners.delete(event);
  }

  return {
    subscribe: store.subscribe,
    getSnapshot,
    ingest,
    advance,
    skipTo,
    reset,
    on,
    off
  };
}
