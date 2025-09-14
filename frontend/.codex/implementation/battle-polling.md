# Battle polling

The `pollBattle` routine in `routes/+page.svelte` continuously polls the backend
for combat snapshots. It now tracks consecutive polls where combat has ended but
no rewards or completion flags have arrived. After roughly three seconds of
such stalled polling, the function stops the battle, records an error on the
snapshot, and logs a warning so the reward overlay or reset flow can proceed.

If the UI reports an active battle but provides no snapshot data, `pollBattle`
polls a dedicated snapshot endpoint until a snapshot is returned. After the
same three‑second timeout without a snapshot, polling halts and an error overlay
prompts the player to reconnect rather than silently starting a new battle.

Battle snapshot polling halts any time the rewards or battle review overlays are
visible. `window.afRewardOpen` and `window.afReviewOpen` flags stop the poller,
clear its timer, and prevent rescheduling until the "Next Room" action closes
the overlay and explicitly restarts polling via `startBattlePoll()`.

If a snapshot includes an `error` field, polling halts immediately and the
error state is surfaced without waiting for combat-over indicators.

Snapshots reporting `result: 'defeat'` are treated as complete even if an
`ended` flag is missing. The poller stops immediately and the defeat overlay
is shown.

Unexpected network errors are logged and retried. `handleRunEnd()` now fires
only when `pollBattle` or `pollState` receive an error with a `404` status or a
message containing `"run ended"`; other errors allow the poll to continue.
`handleLootAcknowledge` and `handleNextRoom` call `stopBattlePoll()` before
acknowledging loot to prevent lingering timers from racing ahead and flagging
the run as ended.

All pollers (`pollState`, `pollBattle`, and `pollUIState`) also check the
overlay flags and refrain from starting or rescheduling while either overlay is
active. Additionally, UI state polling no longer reschedules itself when
`uiState.mode === 'menu'` to reduce network traffic while in the main menu.

Additionally, ending a run from Settings now immediately sets a global
`window.afHaltSync = true` flag and clears timers to prevent any further
`snapshot` polls during teardown. The same flag is set again in
`handleRunEnd()` before clearing run state and returning home.

When a battle completes with no rewards or choices (no cards/relics/loot) and
the backend marks `awaiting_next = true`, the UI now auto‑advances to the next
room without requiring the rewards overlay.
