# Reward Overlay

`src/lib/components/RewardOverlay.svelte` presents the four-phase reward flow using `RewardCard.svelte` for cards and `CurioChoice.svelte` for relics.
Both components wrap `CardArt.svelte`, which builds the Star Rail–style frame with a star-colored header, centered icon, star count, and description.
`OverlayHost.svelte` spawns `FloatingLoot.svelte` elements when `roomData.loot` is present, so gold and item drops briefly rise on screen and are omitted from the reward overlay.
Assets are resolved by star folder and id through the centralized registry
re-exported from `assetLoader.js`, so card, relic, and material lookups share
the same caching and fallback logic as the rest of the UI.

## Inputs

`RewardOverlay.svelte` receives the player's audio and motion preferences so
icons and entry animations match accessibility expectations:

- `sfxVolume` (default `5`) clamps to the 0–10 slider range. When the value is
  `0`, `CardArt` is placed in `quiet` mode to suppress twinkles while the player
  has sound effects muted.
- `reducedMotion` (default `false`) removes the reveal animation delay and also
  toggles `CardArt` into `quiet` mode so the overlay respects motion-reduction
  settings end to end.

Both props are forwarded from `OverlayHost.svelte`, which normalizes the
viewport's overlay settings before rendering.

Loot items now surface backend-provided `ui` metadata. `RewardOverlay.svelte`
and the overlay host both prefer `item.ui.label` over hard-coded ids when
announcing drops so gacha tickets, seasonal items, or future upgrade bundles can
define their own copy without frontend updates.

Drops render as a horizontal row of inventory-style tiles so rewards mirror the
materials grid from the main inventory. Each entry resolves its art through
`getMaterialIcon`, accumulates stack counts when duplicates appear, and exposes
both `aria-label`s and visually hidden text for assistive technologies. Failed
lookups and network errors fall back to the shared material placeholder via
`onMaterialIconError` so the overlay never shows broken images.

## Four-phase progression overview

The overlay ingests the backend's `reward_progression` payload and walks through
four explicit phases:

| Phase key        | UI surface                                                                      |
| ---------------- | ------------------------------------------------------------------------------- |
| `drops`          | Drops grid, sequential reveal, no confirm controls.                              |
| `cards`          | Card staging grid with highlight, wiggle animation, and on-card confirm button.  |
| `relics`         | Relic staging grid mirroring the card interaction model.                         |
| `battle_review`  | Post-battle graphs and summary shell mounted via `BattleReview.svelte`.          |

`normalizeRewardProgression()` collapses aliases, removes duplicates, and
falls back to the canonical order above whenever metadata arrives missing or in
an unexpected sequence. Fallback activations log `rewardPhaseMachine:`
diagnostics in development builds so QA can flag malformed responses without
blocking players.

Each phase emits an `enter` event through the reward phase controller. The
overlay listens for `exit`/`enter` pairs to toggle countdown timers, announce
phase transitions to screen readers, and publish analytics through
`emitRewardTelemetry`.

## Confirmation flow for staged rewards

When the backend marks `awaiting_card` or `awaiting_relic` as `true` and
provides staged entries under `reward_staging`, the overlay now surfaces a
dedicated confirmation block. The highlighted card or relic keeps the primary
grid visible so re-selection can happen without cancelling, auto-selects the
first available option on entry, and renders a stained-glass **Confirm** button
directly beneath the highlighted tile. The highlight applies a looping wiggle
animation defined in `frontend/src/lib/constants/rewardAnimationTokens.js`;
motion honours the player's reduced-motion preference. Second clicks (or
keyboard activation) on the highlighted tile dispatch the confirm event
immediately, matching the on-card button.

### Stained-glass theme alignment

The overlay now mirrors the stained-glass palette used by the navigation
bar and settings surfaces. Panels layer warm and cool gradients over the
shared `--glass-bg`, `--glass-border`, `--glass-shadow`, and
`--glass-filter` tokens so the right rail, preview panes, and drop tiles all
read as part of the same frosted-glass family. Primary actions (cancel,
advance, next room) reuse pill-shaped glass buttons with warm accent glows,
while the confirm buttons inherit refreshed `reward-confirm.css` tokens that
blend the warm overlay accent with the run's cooler highlight. The result is
a cohesive reward surface without the neon gradients that previously clashed
with the rest of the UI.

- `RewardOverlay` receives `stagedCards`, `stagedRelics`, and the
  `awaiting_*` flags from `OverlayHost`. Both grids stay visible while a staged
  entry is pending so players can reselect without cancelling.
- Clicking **Confirm** (either the on-card button or the highlighted card a
  second time) dispatches a `confirm` event with the reward metadata so the
  caller can invoke `/ui?action=confirm_card` or `/ui?action=confirm_relic`.
  The detail includes the reward `type`, currently staged `key`, resolved
  `id`, a human-readable `label`, the originating `phase`, and the staged
  `entry` object (if available) alongside the `respond({ ok })` callback.
  Buttons stay disabled until the parent responds via the provided callback.
  After a successful confirmation the frontend immediately prunes the resolved
  choice bucket so the overlay transitions to the next reward step without
  briefly reopening the spent selection view.
- Clicking **Cancel** dispatches a matching `cancel` event that triggers the
  `/ui?action=cancel_*` endpoints and restores the choice list once the staging
  bucket is cleared.
- Idle mode relies on these events as well. Automation confirms staged rewards
  instead of calling `advance_room`, keeping the overlay visible until the
  backend reports `awaiting_next`.
- The overlay's auto-advance timer and "Next Room" button now respect staged
  confirmations so players cannot accidentally skip unconfirmed rewards.

This UI contract mirrors the backend guardrails introduced for staged rewards,
keeping the frontend in sync with the confirmation lifecycle without forcing a
full map refresh between each step.

### Shared animation tokens

`frontend/src/lib/constants/rewardAnimationTokens.js` exports
`rewardSelectionAnimationTokens` alongside
`selectionAnimationCssVariables()`, translating the shared timing, scale, and
rotation values into CSS custom properties that `RewardCard` and `CurioChoice`
consume. Keeping the helper pure allows other overlays to reuse the tokens
without cloning the wiggle constants or hand-maintaining style fragments.

### Preview metadata panels

Staged entries render preview panels derived from the backend's `preview`
payload (with `about` text as a fallback). `formatRewardPreview` normalises the
metadata into labelled stat deltas, stack summaries, and trigger bullet lists so
cards and relics share the same presentation. The overlay shows up to three
panels for each reward bucket, ensuring reconnecting clients still surface the
context for every staged selection.

### Auto-advance and Next Room controls

`RewardOverlay` delays auto-advancing the run until there are no available
choices, no staged confirmations, and no loot awaiting acknowledgement. When
`awaitingNext` arrives alongside `awaitingLoot === false`, the overlay surfaces a
**Next Room** button that dispatches a `lootAcknowledge` event so idle-mode
automation can finish the encounter immediately. A separate five-second timer
fires a `next` event when the popup is otherwise empty, which keeps fast loot
pickups from stalling the run.

The overlay now accepts an `advanceBusy` prop that is toggled while the client
is waiting on the `/ui?action=advance_room` response. When `advanceBusy` is
true the advance panel switches its status copy to **“Advancing to the next
room…”**, disables the **Advance** button, pauses the auto-advance countdown,
and also disables the **Next Room** button so additional clicks do not refire
the request. `OverlayHost.svelte` pipes this flag through from `+page.svelte`
once the next-room flow begins, keeping the UI in sync with the server call.

`uiApi.advanceRoom()` re-validates reward state against the latest
`runState`/`rewardProgression` snapshot before surfacing the blocking overlay.
The overlay copy now enumerates the pending reward buckets (card, relic, or
loot) and only displays when selections or confirmations genuinely remain.

### Phase advance panel and countdown

The right rail now renders a stained-glass panel that mirrors the reward phase
sequence and exposes a shared **Advance** button. When the current phase has no
remaining selections or confirmations, the button activates, a 10-second
countdown appears, and both manual clicks and the timer call the
`rewardPhaseController.advance()` helper. The component dispatches an
`advance` event with `{ reason: 'manual' | 'auto', from, target, snapshot }` so
automation tasks can observe transitions without reimplementing controller
logic. The countdown automatically pauses if new choices arrive, resets when the
controller skips phases, and restarts once the next phase is ready. Styling for
the panel reuses the shared stained-glass tokens to match other right-rail UI.

## Reward phase controller

`frontend/src/lib/systems/rewardProgression.js` defines the finite state
machine that drives the overlay flow. `createRewardPhaseController()` returns a
Svelte store with `{ subscribe, getSnapshot, ingest, advance, skipTo, reset }`
plus `on(event, handler)`/`off(event, handler)` helpers. Snapshot objects expose

```ts
type RewardPhaseSnapshot = {
  order: ('drops' | 'cards' | 'relics' | 'battle_review')[];
  current: RewardPhase;
  previous?: RewardPhase;
  pending?: RewardPhase;
  completed: RewardPhase[];
  awaiting: Set<RewardPhase>; // phases awaiting confirmation or payloads
};
```

Key helpers:

| Helper                | Purpose                                                                                      |
| --------------------- | -------------------------------------------------------------------------------------------- |
| `ingest(payload)`     | Normalises backend `reward_progression` responses and updates the snapshot.                   |
| `advance({ reason })` | Moves to the next completable phase, emitting `advance` events with `reason: 'manual' \| 'auto'`. |
| `skipTo(phase)`       | Jumps ahead when the backend omits a phase; used for empty cards/relics buckets.             |
| `reset()`             | Clears progression and returns to the canonical order.                                       |
| `getSnapshot()`       | Returns the current snapshot without requiring a subscription.                               |

`frontend/src/lib/systems/overlayState.js` instantiates this machine as
`rewardPhaseController` and re-exports `rewardPhaseState` for reactive
consumers. The controller emits:

- `enter` — dispatched when a phase becomes active. UI components subscribe to
  focus the **Advance** button and fire telemetry for automation logs.
- `exit` — dispatched before leaving a phase. `RewardOverlay` listens for
  `exit` events where `detail.phase === 'drops'` to trigger
  `emitRewardTelemetry('drops-complete', …)` and to freeze countdown timers
  until the next phase confirms its payload.
- `change` — dispatched on every snapshot update so automation and analytics
  can mirror the controller's view without diffing raw payloads. Automation
  scripts reuse this to log `phase-change` breadcrumbs.

Wrapper helpers such as `advanceRewardPhase()`, `skipToRewardPhase()`, and
`resetRewardProgression()` live in `overlayState.js`, keeping the controller API
consistent for UI components, tests, and automation scripts. The helper file
also re-exports `rewardPhaseEvents` so idle automation can attach handlers
without importing the controller singleton directly.

To emphasise each pickup, the component keeps a `visibleDrops` array separate
from the aggregated `dropEntries`. When motion reduction is disabled the list
is populated one entry at a time on a timed interval; each reveal triggers the
shared `createRewardDropSfx` helper so coins or materials play the reward-drop
sound at the player's current `sfxVolume`. Reduced-motion mode bypasses the
timers, shows all icons immediately, and skips the audio so accessibility
preferences are respected. Pop-in scale transitions mirror the sequential
animation while guarding against prop changes by clearing timers and audio
handles whenever the loot payload updates or the overlay unmounts.

`createRewardDropSfx` now wraps the generic `createSequentialSfxPlayer`
utility, which keeps a cached audio element ready and clones it if another
playback request arrives mid-sound. The helper clamps volume updates, respects
`reducedMotion`, and pulls clips from the registry's `'ui/reward/drop'` alias
before falling back to the Kenney coin and satchel samples. The pull-results
overlay reuses the same utility through `createDealSfx`, so both overlays share
identical clone-and-retry behaviour when the user mashes through reward queues.
Browsers that block autoplayed media now wait for a pointer/keyboard gesture
inside the overlay before enabling the loot SFX guard. If playback still
rejects with a `NotAllowedError`, the overlay logs a single console info line
and disables further attempts until the player interacts again, ensuring the
first real click unlocks audio without spamming retries.

Ambient effects from `EnrageIndicator.svelte` continue to render while the
rewards overlay is shown and fade out gracefully, so the transition from
combat to rewards remains smooth.

`handleLootAcknowledge()` now stops any active battle polling timers before
calling the backend so lingering snapshot requests cannot mark the run as ended
mid‑acknowledgement.

## Accessibility notes

- Phase and countdown changes are announced through visually hidden
  `aria-live` regions (`aria-live="assertive"` for the phase summary and
  `aria-live="polite"` for the countdown) so screen readers hear when a new
  step becomes active and how long remains before auto-advance triggers.
- Drop tiles expose descriptive `aria-label`s and redundant hidden text so
  assistive tech hears item names and stack counts alongside the visual badges.
- Focus automatically shifts to the **Advance** button when a phase becomes
  actionable and falls back to the overlay container when auto-advance fires,
  keeping keyboard flows predictable.
- Confirm buttons reuse the stained-glass styling tokens but retain native
  button semantics, so keyboard activation, focus rings, and screen reader
  labelling stay consistent across cards and relics.
- Live regions announce when confirm buttons appear or disappear so screen
  reader users hear when staged selections are ready or cleared.
- Countdown updates respect Reduced Motion; when motion is disabled the timer
  posts updates every two seconds instead of animating per-second fades.

## Manual QA checklist

- Trigger a full Drops → Cards → Relics → Review sequence using mocked
  `reward_progression` data; confirm controller logs only appear when phases are
  skipped or reordered.
- Start a countdown in the Drops phase, then stage a card to ensure the timer
  pauses until confirmations complete.
- Confirm that automation hooks (`advance` events) log both manual and auto
  reasons during idle-mode runs.
- Navigate the overlay using only the keyboard: verify focus order is
  Drops grid → **Advance** → staged confirm → **Advance** again after each phase.
- With a screen reader, listen for announcements when confirm buttons appear,
  disappear, and when the countdown reaches zero.
