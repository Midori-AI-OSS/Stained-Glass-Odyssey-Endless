# Suppress Benign Console Warnings and Error Overlay Triggers

## Problem Statement

The frontend currently logs two types of benign warnings that clutter the console and trigger unnecessary error overlays:

1. **Portrait-fallback warnings** from `assetRegistry.js` (line 1021):
   - Logged via `emitTelemetry('portrait-fallback', ...)` at line 52
   - Appears as `[assetRegistry] portrait-fallback` with detailed metadata
   - Triggers on legitimate fallback scenarios when character portraits aren't found
   - Not an error condition—the system is working as designed

2. **ResizeObserver loop warnings**:
   - Browser-generated: "ResizeObserver loop completed with undelivered notifications."
   - Benign performance warning that occurs when ResizeObserver callbacks take slightly longer than the frame budget
   - Currently triggers the error overlay via `hooks.client.js` (lines 24-33)
   - Not a real error—just a browser timing notification

## Current Behavior

From the error log:
```
[assetRegistry] portrait-fallback {kind: 'portrait-fallback', detail: {…}, timestamp: 1762466756605}
warn @ client.js?v=8508bbe4:3088
...
OverlayController.js:42 openOverlay(error): {message: 'ResizeObserver loop completed with undelivered notifications.', traceback: '', context: null}
...
hooks.client.js:32 Window error event: ErrorEvent {isTrusted: true, message: 'ResizeObserver loop completed with undelivered notifications.', ...}
```

## Desired Behavior

1. **Portrait-fallback telemetry**: Reduce console noise while preserving telemetry for debugging
   - Keep telemetry events for custom listeners and browser CustomEvents
   - Suppress or downgrade the `console.warn` call for portrait-fallback events
   - Optionally: Make console logging conditional on a debug flag

2. **ResizeObserver errors**: Filter out from error overlay system
   - Detect ResizeObserver messages in `hooks.client.js`
   - Log to console for debugging but don't trigger error overlay
   - Allow other legitimate errors to continue triggering overlays

## Implementation Details

### File 1: `frontend/src/lib/systems/assetRegistry.js`

**Location**: Lines 42-54 (in `emitTelemetry` function)

**Current code**:
```javascript
try {
  console.warn(`[assetRegistry] ${kind}`, payload);
} catch {}
```

**Suggested changes**:
1. Add a check to suppress console logging for `portrait-fallback` events, OR
2. Downgrade to `console.debug` for portrait-fallback, OR
3. Make console logging conditional on a debug/verbose flag

**Example approach**:
```javascript
try {
  // Only log portrait-fallback in verbose mode to reduce console noise
  if (kind !== 'portrait-fallback' || globalThis.__assetRegistryVerbose === true) {
    console.warn(`[assetRegistry] ${kind}`, payload);
  }
} catch {}
```

### File 2: `frontend/src/hooks.client.js`

**Location**: Lines 24-33 (window error handler)

**Current code**:
```javascript
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
```

**Suggested changes**:
Add a filter to detect and handle ResizeObserver warnings differently:

```javascript
window.addEventListener('error', (ev) => {
  let msg = ev?.error?.message || ev?.message || 'Unexpected error';
  msg = String(msg ?? '').trim();
  
  // Filter out benign ResizeObserver warnings - log but don't show overlay
  if (/ResizeObserver loop/i.test(msg)) {
    try { console.debug('ResizeObserver notification (benign):', msg); } catch {}
    return; // Don't trigger error overlay
  }
  
  if (/^\d+$/.test(msg)) {
    msg = `Unexpected error (code ${msg})`;
  }
  const stack = (ev?.error?.stack || '').trim();
  openOverlay('error', { message: msg, traceback: stack, context: ev?.error?.context ?? null });
  try { console.error('Window error event:', ev?.error || ev); } catch {}
});
```

## Testing

1. **Manual verification**:
   - Start the frontend dev server: `cd frontend && bun run dev`
   - Navigate to the Party Picker component
   - Open browser console
   - Verify portrait-fallback warnings are suppressed or downgraded
   - Verify ResizeObserver warnings don't trigger error overlay
   - Verify other legitimate errors still trigger overlays

2. **Existing tests**:
   - Run frontend tests: `cd frontend && bun test`
   - Ensure no regressions in error handling or asset loading

## Acceptance Criteria

- [ ] Portrait-fallback telemetry warnings no longer clutter console (or are downgraded to debug level)
- [ ] ResizeObserver warnings are logged to console but don't trigger error overlay
- [ ] Telemetry events for portrait-fallback are still emitted for custom listeners
- [ ] Other legitimate errors continue to trigger error overlays as expected
- [ ] No regressions in error handling or asset loading
- [ ] All existing frontend tests pass

## Notes

- This is a UI polish task—functionality is working correctly, we're just reducing noise
- The asset registry's fallback behavior is intentional and working as designed
- ResizeObserver warnings are well-documented browser performance notifications, not errors
- Consider adding a debug mode flag for verbose asset registry logging if needed in the future

## Related Files

- `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/frontend/src/lib/systems/assetRegistry.js`
- `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/frontend/src/hooks.client.js`
- `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/frontend/src/lib/systems/OverlayController.js` (context only)
- `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/frontend/src/lib/components/PartyPicker.svelte` (context only)
