# Reward Overlay

`src/lib/components/RewardOverlay.svelte` presents battle rewards using `RewardCard.svelte` for cards and `CurioChoice.svelte` for relics.
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

## Four-Phase Reward Flow

When the backend provides `reward_progression` metadata (with `current_step`, `available`, and `completed` fields), the overlay sequences rewards through four distinct phases: **Drops → Cards → Relics → Battle Review**. This phase-based flow prevents soft-lock behavior and provides clearer visual affordances.

### Phase 1: Drops (`current_step: 'drops'`)

Shows only loot tiles (gold, damage-type items, pulls). A stained-glass styled "Advance" button (using `--glass-bg`, `--glass-border`, `--glass-shadow` tokens) appears with a visible 10-second countdown timer. The timer auto-advances when it completes, but players can click early to proceed immediately. Card and relic UI remains hidden until drops are acknowledged.

The overlay dispatches an `advancePhase` event when the Advance button is clicked or the countdown completes, which triggers the parent to call the backend's `advance_room` endpoint.

### Phase 2: Cards (`current_step: 'cards'`)

Presents card choices with enhanced interaction:
- **First click** highlights the selected card and starts a subtle looping wiggle animation (2.2s cycle with small rotation -1.5° to 1.5° and scale 1.01-1.02)
- Each card receives a randomized `--wiggle-delay` CSS variable to prevent synchronized motion
- A themed **Confirm** button appears directly beneath the highlighted card (reusing stained-glass styling)
- **Second click** on the same card confirms the selection (equivalent to clicking Confirm)
- Keyboard activation moves focus to the confirm button when it appears

In phase-based mode, the preview panel and cancel button are hidden to streamline the workflow.

### Phase 3: Relics (`current_step: 'relics'`)

Mirrors the card phase behavior:
- Highlight on first click with wiggle animation (same randomized timing)
- Inline confirm button beneath highlighted relic
- Second-click confirmation
- Backend cancel flows clear local highlight state

### Phase 4: Battle Review (`current_step: 'battle_review'`)

Once all reward selections finish, the overlay transitions to the battle review phase. If user settings allow it, the review overlay opens automatically. Otherwise, the flow advances immediately to the next room.

### Backward Compatibility

When `reward_progression` is not provided, the overlay falls back to the legacy behavior: showing all rewards simultaneously (drops, cards, relics) with the traditional staged confirmation flow including preview panels and cancel buttons. This ensures compatibility with existing backend versions.

## Confirmation flow for staged rewards

When the backend marks `awaiting_card` or `awaiting_relic` as `true` and
provides staged entries under `reward_staging`, the overlay now surfaces a
dedicated confirmation block. The selected card or relic renders in a disabled
state alongside **Confirm** and **Cancel** buttons so players can commit or
undo their choice before advancing the run.

- `RewardOverlay` receives `stagedCards`, `stagedRelics`, and the
  `awaiting_*` flags from `OverlayHost`. The component hides the original card
  or relic choice grid while a staged entry is pending.
- Clicking **Confirm** dispatches a `confirm` event with the reward type so the
  caller can invoke `/ui?action=confirm_card` or `/ui?action=confirm_relic`.
  Buttons stay disabled until the parent responds via the provided
  `respond({ ok })` callback. After a successful confirmation the frontend
  immediately prunes the resolved choice bucket so the overlay transitions to
  the next reward step without briefly reopening the spent selection view.
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

## Wiggle Animation

The wiggle effect for highlighted cards/relics uses a CSS keyframe animation defined in `RewardOverlay.svelte`:

```css
@keyframes wiggle {
  0% { transform: rotate(0deg) scale(1); }
  10% { transform: rotate(-1.5deg) scale(1.02); }
  20% { transform: rotate(1.5deg) scale(1.02); }
  30% { transform: rotate(-1deg) scale(1.01); }
  40% { transform: rotate(1deg) scale(1.01); }
  50% { transform: rotate(0deg) scale(1); }
  100% { transform: rotate(0deg) scale(1); }
}
```

The animation loops every 2.2 seconds with subtle rotation and scale changes. Each card or relic receives a randomized `--wiggle-delay` CSS variable (e.g., `0ms`, `100ms`, `200ms`) to create organic, non-synchronized motion. The wiggle animation is disabled when `reducedMotion` is enabled, ensuring accessibility compliance.

## Idle Mode Automation

Idle-mode automation follows the phase-based flow when `reward_progression` is present. The overlay dispatches `advancePhase` events that the parent handles by calling the backend's `advance_room` endpoint, progressing through each stage (Drops → Cards → Relics → Battle Review) without skipping unconfirmed rewards. The automation respects phase gates and engages confirm actions as needed.
