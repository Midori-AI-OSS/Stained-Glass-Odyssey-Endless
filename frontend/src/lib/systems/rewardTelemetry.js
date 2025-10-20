const TELEMETRY_EVENT_NAME = 'autofighter:reward-phase';
let telemetryListener = null;
const onceCache = new Set();

function normalizeKind(kind) {
  if (!kind) return 'unknown';
  return String(kind);
}

function emitToListener(payload) {
  if (typeof telemetryListener !== 'function') {
    return;
  }
  try {
    telemetryListener(payload);
  } catch (error) {
    try {
      console.error('[rewardTelemetry] listener error', error);
    } catch {}
  }
}

function emitBrowserEvent(payload) {
  try {
    if (
      typeof window !== 'undefined' &&
      typeof window.dispatchEvent === 'function' &&
      typeof window.CustomEvent === 'function'
    ) {
      window.dispatchEvent(new window.CustomEvent(TELEMETRY_EVENT_NAME, { detail: payload }));
    }
  } catch {}
}

function emitConsole(payload) {
  try {
    console.info('[rewardTelemetry]', payload);
  } catch {}
}

export function setRewardTelemetry(handler) {
  telemetryListener = typeof handler === 'function' ? handler : null;
}

export function resetRewardTelemetry() {
  onceCache.clear();
  telemetryListener = null;
}

export function emitRewardTelemetry(kind, detail = {}, options = {}) {
  const payload = {
    kind: normalizeKind(kind),
    detail: { ...detail },
    timestamp: Date.now()
  };

  const onceKey = options.onceKey === false ? null : options.onceKey ?? null;
  if (onceKey) {
    if (onceCache.has(onceKey)) {
      return payload;
    }
    onceCache.add(onceKey);
  }

  emitToListener(payload);
  emitBrowserEvent(payload);
  emitConsole(payload);
  return payload;
}

export const rewardTelemetryEventName = TELEMETRY_EVENT_NAME;
