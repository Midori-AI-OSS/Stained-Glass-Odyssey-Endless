// OverlayController.js
// Central store for managing overlay view state with a simple stack.
// Components can open overlays, go back, or return home.
import { writable, get } from 'svelte/store';

export const overlayView = writable('main');
export const overlayData = writable({});
const stack = [];

function normalizeErrorPayload(data = {}) {
  try {
    const out = { ...(data || {}) };
    let msg = out.message;
    // Accept numbers or strings; trim whitespace/newlines
    if (msg == null) msg = '';
    msg = String(msg).trim();
    // If it's just digits (possibly very large), present a clearer message
    if (/^\d+$/.test(msg)) {
      msg = `An unexpected error occurred (code ${msg}).`;
    }
    out.message = msg;
    if (typeof out.traceback === 'string') out.traceback = out.traceback.trim();
    const context = out.context;
    if (context && typeof context === 'object') {
      const source = Array.isArray(context.source)
        ? context.source.map((line = {}) => ({
            line: typeof line.line === 'number' ? line.line : Number.parseInt(line.line, 10) || 0,
            code: typeof line.code === 'string' ? line.code : '',
            highlight: Boolean(line.highlight)
          }))
        : [];
      out.context = {
        file: typeof context.file === 'string' ? context.file : '',
        line: typeof context.line === 'number' ? context.line : Number.parseInt(context.line, 10) || 0,
        function: typeof context.function === 'string' ? context.function : '',
        source
      };
    } else {
      out.context = null;
    }
    // Always log normalized errors to aid debugging
    try { console.error('openOverlay(error):', out); } catch {}
    return out;
  } catch {
    return data || {};
  }
}

export function openOverlay(view, data = {}) {
  const prev = { view: get(overlayView), data: get(overlayData) };
  stack.push(prev);
  overlayView.set(view);
  overlayData.set(view === 'error' ? normalizeErrorPayload(data) : data);
}

export function backOverlay() {
  const prev = stack.pop() || { view: 'main', data: {} };
  overlayView.set(prev.view);
  overlayData.set(prev.data);
}

export function homeOverlay() {
  stack.length = 0;
  overlayView.set('main');
  overlayData.set({});
}
