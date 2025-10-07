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

To emphasise each pickup, the component keeps a `visibleDrops` array separate
from the aggregated `dropEntries`. When motion reduction is disabled the list
is populated one entry at a time on a timed interval; each reveal triggers the
shared `createRewardDropSfx` helper so coins or materials play the reward-drop
sound at the player's current `sfxVolume`. Reduced-motion mode bypasses the
timers, shows all icons immediately, and skips the audio so accessibility
preferences are respected. Pop-in scale transitions mirror the sequential
animation while guarding against prop changes by clearing timers and audio
handles whenever the loot payload updates or the overlay unmounts.

Ambient effects from `EnrageIndicator.svelte` continue to render while the
rewards overlay is shown and fade out gracefully, so the transition from
combat to rewards remains smooth.

`handleLootAcknowledge()` now stops any active battle polling timers before
calling the backend so lingering snapshot requests cannot mark the run as ended
mid‑acknowledgement.
