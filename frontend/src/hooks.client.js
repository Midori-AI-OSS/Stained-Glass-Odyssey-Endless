// Global client-side error handler for SvelteKit
// Converts unhandled load/navigation errors into our error overlay.
import { openOverlay } from '$lib';

/** @type {import('@sveltejs/kit').HandleClientError} */
export function handleError({ error, event }) {
  try {
    let message = error?.message ?? String(error ?? 'Unknown error');
    // If the message looks like a bare number, wrap it with context for clarity
    if (/^\d+$/.test(String(message || ''))) {
      message = `Unexpected error (code ${message})`;
    }
    const traceback = error?.stack ?? '';
    openOverlay('error', { message, traceback, context: error?.context ?? null });
    console.error('Client error:', message, '\n', traceback, '\nAt:', event?.url?.href);
  } catch (e) {
    console.error('Failed to open error overlay', e);
  }
  return { message: error?.message ?? 'An unexpected error occurred.' };
}

// As an additional safety net, capture window-level errors
if (typeof window !== 'undefined') {
  window.addEventListener('error', (ev) => {
    let msg = ev?.error?.message || ev?.message || 'Unexpected error';
    msg = String(msg ?? '').trim();
    if (/^\d+$/.test(msg)) {
      msg = `Unexpected error (code ${msg})`;
    }
    const stack = (ev?.error?.stack || '').trim();
    openOverlay('error', { message: msg, traceback: stack, context: ev?.error?.context ?? null });
    try { console.error('Window error event:', ev?.error || ev); } catch {}
  });
  window.addEventListener('unhandledrejection', (ev) => {
    const reason = ev?.reason;
    let msg = reason?.message || String(reason || 'Unhandled rejection');
    if (/^\d+$/.test(String(msg || ''))) {
      msg = `Unhandled rejection (code ${msg})`;
    }
    const stack = reason?.stack || '';
    openOverlay('error', { message: msg, traceback: stack, context: reason?.context ?? null });
    // Also log the raw reason object for debugging odd cases
    try { console.error('Unhandled rejection raw reason:', reason); } catch {}
  });
}
