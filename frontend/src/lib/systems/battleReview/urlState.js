const ID_PATTERN = /[^a-zA-Z0-9._:-]/g;
const DEFAULT_STATE = Object.freeze({
  battleIndex: 1,
  tab: 'overview',
  filters: [],
  comparison: [],
  pins: [],
  window: null
});

function sanitizeIdentifier(value) {
  if (value == null) return '';
  return String(value).replace(ID_PATTERN, '').slice(0, 64);
}

function sanitizeList(value, max = 8) {
  if (!value) return [];
  const list = Array.isArray(value) ? value : String(value).split(',');
  const seen = new Set();
  const out = [];
  for (const entry of list) {
    const id = sanitizeIdentifier(entry);
    if (!id || seen.has(id)) continue;
    seen.add(id);
    out.push(id);
    if (out.length >= max) break;
  }
  return out;
}

function parseWindow(raw) {
  if (!raw) return null;
  const parts = String(raw).split(':');
  if (parts.length !== 2) return null;
  const start = Number(parts[0]);
  const end = Number(parts[1]);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
    return null;
  }
  return {
    start: Math.round(start * 1000) / 1000,
    end: Math.round(end * 1000) / 1000
  };
}

function formatWindow(window) {
  if (!window || typeof window !== 'object') return null;
  const start = Number(window.start);
  const end = Number(window.end);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
    return null;
  }
  const format = (value) => (Math.round(value * 1000) / 1000).toString();
  return `${format(start)}:${format(end)}`;
}

export function parseBattleReviewSearchParams(params) {
  const search = params instanceof URLSearchParams ? params : new URLSearchParams(params);
  const state = { ...DEFAULT_STATE };

  const battle = Number(search.get('battle'));
  if (Number.isFinite(battle) && battle > 0 && battle < 10000) {
    state.battleIndex = Math.floor(battle);
  }

  const tab = sanitizeIdentifier(search.get('tab'));
  if (tab) {
    state.tab = tab;
  }

  state.filters = sanitizeList(search.get('filters'), 12);
  state.comparison = sanitizeList(search.get('compare'), 6);
  state.pins = sanitizeList(search.get('pins'), 10);
  state.window = parseWindow(search.get('window'));

  return state;
}

export function buildBattleReviewSearchParams(state = DEFAULT_STATE) {
  const params = new URLSearchParams();
  const merged = {
    ...DEFAULT_STATE,
    ...(state || {})
  };

  const battle = Number(merged.battleIndex);
  if (Number.isFinite(battle) && battle > 0) {
    params.set('battle', Math.floor(battle).toString());
  }

  const tab = sanitizeIdentifier(merged.tab);
  if (tab && tab !== DEFAULT_STATE.tab) {
    params.set('tab', tab);
  }

  const filters = sanitizeList(merged.filters, 12);
  if (filters.length) {
    params.set('filters', filters.join(','));
  }

  const comparison = sanitizeList(merged.comparison, 6);
  if (comparison.length) {
    params.set('compare', comparison.join(','));
  }

  const pins = sanitizeList(merged.pins, 10);
  if (pins.length) {
    params.set('pins', pins.join(','));
  }

  const window = formatWindow(merged.window);
  if (window) {
    params.set('window', window);
  }

  return params;
}

function sanitizePathSegment(value) {
  const clean = sanitizeIdentifier(value);
  return clean || 'unknown-run';
}

export function buildBattleReviewLink(runId, state = DEFAULT_STATE, { origin = '' } = {}) {
  const params = buildBattleReviewSearchParams(state);
  const query = params.toString();
  const base = origin ? origin.replace(/\/$/, '') : '';
  const path = `/logs/${encodeURIComponent(sanitizePathSegment(runId))}`;
  return `${base}${path}${query ? `?${query}` : ''}`;
}

export const DEFAULT_BATTLE_REVIEW_STATE = DEFAULT_STATE;
