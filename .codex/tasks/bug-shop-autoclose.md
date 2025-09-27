# Bug: Shop overlay opens then immediately closes / returns to main menu

Status: needs triage

Reproduction (automated):
- Using Playwright against http://192.168.10.27:59001/ I started a run and progressed until a Shop room appeared.
- The Shop overlay rendered briefly (loot selection), then the overlay removed and the Battle Review/main UI returned.
- Playwright log shows `shop-closed` event and the overlay heading changed to `Choose a Relic` then to `Battle Review`.

Symptoms:
- The Shop overlay appears (ShopMenu) then is removed without user action.
- The player is returned to the main UI flow (battle review or main menu).
- Not related to `fullIdleMode` per user's note; appears to be an unexpected UI state change.

Hypothesis / likely causes:
1. Frontend UI polling or background `ui` state updates are receiving a `room` or `result` message from the backend that indicates a non-shop state (e.g., `battle` or `review`) immediately after reward selection, causing `OverlayHost.svelte` to unmount the `ShopMenu` when it evaluates `roomData.result`.
2. The backend emits a room transition event prematurely when reward selection completes (race between loot selection acknowledgement and room transition); the frontend handles the event by closing overlays.
3. A timing issue in ShopMenu's reroll/awaitingReroll logic or in OverlayController could be misinterpreting catalog reloads as a shop unload.

Files of interest:
- `frontend/src/lib/components/OverlayHost.svelte` — mounts `ShopMenu` when `roomData.result === 'shop'` and dispatches `shopLeave` when `on:close` occurs.
- `frontend/src/lib/components/ShopMenu.svelte` — provides `close()` that dispatches `close` and clears local state; may be invoked via parent `overlayView` or `roomData` changes.
- `frontend/src/lib/systems/uiApi.js` and `frontend/src/lib/systems/OverlayController.js` (search for `applyUIState`, `poll` functions) — sources of incoming UI state updates.
- Backend rooms/utils and room transition emitters (backend/autofighter/rooms/*) — where server might send room transitions.

Proposed fix (safe, incremental):
1. Add debug logging in the frontend: log when `OverlayHost` mounts/unmounts overlays and when `roomData` changes (timestamp + current `roomData.result` + `battle_index` + `runId`). Save logs to console and expose a debug endpoint if needed.
2. Temporarily prevent auto-closing the shop while the overlay has active user interaction (e.g., if `ShopMenu` has any unacknowledged choices or `processing` flag). In `OverlayHost.svelte`, gate unmounting `ShopMenu` for a short grace period (1000–1500ms) after `roomData` changes to allow the frontend to resolve the reward selection event without immediately closing overlays.
3. Instrument backend to log and, if necessary, delay emitting a room transition until reward selection is acknowledged by the server-side run state.
4. Add a unit/integration test: simulate reward selection and ensure `roomData.result` remains `shop` until an explicit 'leave' event or confirmed room transition is sent.

Acceptance criteria:
- Reproduction steps show Shop overlay remains open until the player clicks 'Leave' or buys/rerolls and then opt-in to leave; no automatic close to main menu without user action.
- Frontend logs show no premature `roomData.result` change to non-shop states during reward selection.

Notes for triage:
- Start with frontend logging; the Playwright run reproduced the issue quickly and will be useful to verify fixes.
- Avoid UI changes that break expected automatic transitions (e.g., reward -> review flow) — aim for graceful gating only.
