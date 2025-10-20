# Reward Overlay

`src/lib/components/RewardOverlay.svelte` presents battle rewards using a four-phase flow when `reward_progression` metadata is provided by the backend: **Drops → Cards → Relics → Battle Review**.

## Four-Phase Flow

When the backend provides `reward_progression` metadata with `current_step`, `available`, and `completed` fields, the overlay transitions through distinct reward phases:

### 1. Drops Phase (`current_step: 'drops'`)

Shows only loot tiles (gold, damage-type items, pulls) with a prominent "Advance" button styled with stained-glass aesthetics matching the main menu. The button displays a visible 10-second countdown timer that auto-advances when it completes, though players can click early to proceed immediately. Card and relic UI remains hidden until drops are acknowledged.

### 2. Cards Phase (`current_step: 'cards'`)

Presents card choices with enhanced interaction:
- **First click** highlights the selected card and starts a subtle looping wiggle animation with slightly randomized timing
- The wiggle persists until the selection is confirmed or a different card is chosen
- A themed **Confirm** button appears directly beneath the highlighted card (reusing stained-glass + icon-btn styling)
- **Second click** on the same highlighted card behaves identically to pressing the Confirm button
- Keyboard activation moves focus to the confirm button when it appears

The existing preview panel and cancel button are **not shown** in phase-based flow, simplifying the confirmation workflow.

### 3. Relics Phase (`current_step: 'relics'`)

Mirrors card phase behavior: highlight on first click, wiggle animation with randomized offsets, on-card confirm button with the same stained-glass styling, and second-click confirmation. Backend cancel flows clear any local highlight state.

### 4. Battle Review Phase (`current_step: 'battle_review'`)

Once all reward selections finish, the overlay transitions into the battle review phase. If the user's settings allow it, the review overlay opens automatically. Otherwise, the flow advances immediately to the next room.

## Legacy Compatibility

When `reward_progression` is not provided, the overlay falls back to the original behavior: showing all rewards simultaneously (drops, cards, relics) with the traditional staged confirmation flow including preview panels and cancel buttons.

## Components

`RewardCard.svelte` renders cards and `CurioChoice.svelte` renders relics. Both wrap `CardArt.svelte`, which builds the Star Rail–style frame with star-colored header, centered icon, star count, and description.

`OverlayHost.svelte` spawns `FloatingLoot.svelte` elements when `roomData.loot` is present, so gold and item drops briefly rise on screen before being shown in the Drops phase. Assets are resolved by star folder and id through the centralized registry re-exported from `assetLoader.js`.

## Inputs

`RewardOverlay.svelte` receives the player's audio and motion preferences:

- `sfxVolume` (default `5`) clamps to the 0–10 slider range. When the value is `0`, `CardArt` is placed in `quiet` mode to suppress twinkles.
- `reducedMotion` (default `false`) removes the reveal animation delay and toggles `CardArt` into `quiet` mode. The wiggle animation is also suppressed when reduced motion is enabled.
- `rewardProgression` (optional) – Backend metadata with `current_step`, `available`, and `completed` fields that drives phase-based flow

Both `sfxVolume` and `reducedMotion` are forwarded from `OverlayHost.svelte`, which normalizes the viewport's overlay settings before rendering.

Loot items surface backend-provided `ui` metadata. `RewardOverlay.svelte` and the overlay host prefer `item.ui.label` over hard-coded ids when announcing drops, allowing gacha tickets, seasonal items, or future upgrade bundles to define their own copy without frontend updates.

Drops render as a horizontal row of inventory-style tiles with stack counts, `aria-label`s, and visually hidden text for assistive technologies. Failed lookups fall back to the shared material placeholder via `onMaterialIconError`.

## Wiggle Animation

The wiggle effect uses a CSS keyframe animation that applies subtle rotation and scale changes with a 2.2-second loop. Each card or relic receives a randomized `--wiggle-delay` CSS variable to prevent synchronized motion across multiple items, making the animation feel more organic.

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

## Styled Controls

The Drops phase Advance button and inline Confirm buttons reuse shared CSS tokens from `settings-shared.css`:
- `--glass-bg`: Semi-transparent background with glassmorphism effect
- `--glass-border`, `--glass-shadow`, `--glass-filter`: Stained-glass styling matching main menu and side panels
- `.icon-btn` aesthetics: Consistent hover states and transitions

These controls maintain the cohesive visual language used throughout the main menu, warp panel, and inventory screens.

## Idle Mode Automation

Idle-mode automation follows the new phase-based flow. The overlay dispatches `advancePhase` events that the parent handles by calling the backend's `advance_room` endpoint, progressing through each stage without skipping unconfirmed rewards. The automation engages confirm actions as needed and respects the phase gates.

## Accessibility

Keyboard users can navigate and select cards/relics without relying on pointer hover. When a card or relic is highlighted, focus automatically moves to the newly revealed Confirm button, ensuring seamless keyboard-only operation. The wiggle animation respects `reducedMotion` settings and is disabled when motion reduction is active.

## Confirmation Flow for Staged Rewards (Legacy Mode)

When not using phase-based flow, the overlay surfaces a dedicated confirmation block for staged rewards. The selected card or relic renders in a disabled state alongside **Confirm** and **Cancel** buttons. Clicking **Confirm** dispatches a `confirm` event, while **Cancel** triggers a `cancel` event that restores the choice list once the staging bucket is cleared.

Idle mode relies on these events in legacy flow, confirming staged rewards instead of calling `advance_room`, keeping the overlay visible until the backend reports `awaiting_next`.

### Preview Metadata Panels (Legacy Mode Only)

Staged entries render preview panels derived from the backend's `preview` payload, with `about` text as a fallback. `formatRewardPreview` normalizes the metadata into labelled stat deltas, stack summaries, and trigger bullet lists. The overlay shows up to three panels per reward bucket for reconnecting clients.

## Auto-Advance and Next Room Controls

In legacy mode, `RewardOverlay` delays auto-advancing until there are no choices, no staged confirmations, and no loot awaiting acknowledgement. When `awaitingNext` arrives alongside `awaitingLoot === false`, the overlay surfaces a **Next Room** button that dispatches a `lootAcknowledge` event. A separate five-second timer fires a `next` event when the popup is empty, keeping fast loot pickups from stalling the run.

Each pickup triggers the shared `createRewardDropSfx` helper so coins or materials play the reward-drop sound at the player's current `sfxVolume`. Reduced-motion mode bypasses timers, shows all icons immediately, and skips audio.

`createRewardDropSfx` wraps the generic `createSequentialSfxPlayer` utility, which caches audio elements and clones them if playback requests arrive mid-sound. The helper clamps volume updates, respects `reducedMotion`, and pulls clips from the registry's `'ui/reward/drop'` alias before falling back to Kenney samples. Browsers that block autoplayed media wait for a pointer/keyboard gesture before enabling loot SFX.

Ambient effects from `EnrageIndicator.svelte` continue to render while the rewards overlay is shown and fade out gracefully, ensuring a smooth transition from combat to rewards.

`handleLootAcknowledge()` stops any active battle polling timers before calling the backend so lingering snapshot requests cannot mark the run as ended mid-acknowledgement.
