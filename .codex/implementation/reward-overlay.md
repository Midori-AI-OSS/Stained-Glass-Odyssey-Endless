# Reward Overlay

After a battle resolves, the backend returns a `loot` object summarizing gold and any reward options. `OverlayHost.svelte` keeps `BattleView` mounted and stops its polling loop so the last snapshot remains visible. A `PopupWindow` inside `OverlaySurface` then presents `RewardOverlay.svelte`, which receives the battle's `card_choices`, `relic_choices`, and gold gain. The reward popup loads art from `src/lib/assets` and displays card options with a background tinted to the card's star rank and the name overlaid at the top. Clicking a choice opens a status panel below with the card's description and a confirm button so players can verify their selection. Relic and item rewards reuse the same component and asset pipeline.

`RewardOverlay` also accepts a `partyStats` array derived from `_serialize`, rendering a right-hand table listing each party member and their `damage_dealt`. Placeholder columns reserve space for future metrics like damage taken or healing.

The overlay now subscribes to the shared reward phase state machine so the experience plays out as a deterministic Drops → Cards → Relics → Battle Review flow. While the controller reports `current === 'drops'`, only loot tiles and gold summaries render and later-phase controls are kept out of the DOM. A right-rail "Reward Flow" panel reflects the active phase and upcoming steps without exposing the advance button (that arrives with the countdown task) so screen readers and automation can follow progress. Once the phase machine advances past Drops the usual card and relic widgets mount just as before.

When Drops finishes, `RewardOverlay` emits an `autofighter:reward-phase` telemetry event with the `drops-complete` kind so regression automation can confirm the transition before proceeding with card or relic checks.

Selecting a card posts to `/cards/<run_id>` via the `chooseCard` API helper once the player confirms, clearing `card_choices`. The "Next Room" button remains disabled until all selections are resolved. Clicking it dismisses the popup, unmounts `BattleView`, and calls `/run/<id>/next` to advance the map.

When a relic reward is selected, the overlay shows its `about` text so players
see the effect with the next stack applied.

## Confirm control styling & accessibility

Card and relic confirm buttons now share a stained-glass token set defined in
`src/lib/styles/reward-confirm.css`, with matching design values exposed through
`src/lib/constants/rewardConfirmTokens.js` for any logic that needs to read or
override the CSS variables. Both `RewardCard.svelte` and `CurioChoice.svelte`
apply the shared `reward-confirm-button` class alongside their component-level
layout hooks so hover/disabled states remain visually consistent between phases.

Each confirm control exposes an explicit `aria-label` (`Confirm card …` /
`Confirm relic …`) while the overlay announces selection changes and confirm
availability via the `selectionAnnouncement` live region. Announcements fire
when highlights move, confirms become available, or staged rewards clear so
screen readers receive timely updates during the Cards and Relics phases.

## Confirmation responses

Confirmed selections now return an `activation_record` with `activation_id`, `activated_at`, `bucket`, and the committed payload so reconnecting clients can surface what was just accepted. The backend also streams a bounded `reward_activation_log` array alongside the usual `awaiting_*` flags, letting the overlay highlight historical confirmations for audit trails. Because confirmations operate under a per-run mutex, retries that arrive after the staging bucket has been cleared raise an error instead of duplicating rewards.

## Preview metadata

Staged cards and relics now surface preview metadata returned by the backend. `RewardOverlay` renders a preview panel beneath the Confirm/Cancel controls whenever a staged entry includes a `preview` payload (or an `about` fallback). The panel highlights:

- A summary line (either from `preview.summary` or the staged `about` text).
- Per-stat deltas formatted according to the preview `mode` (percent, flat, multiplier) and scoped to the target audience (party, foes, allies, etc.). Each stat line also lists stack counts and previous totals when supplied.
- Trigger hooks with the normalized event name and optional description.

Preview data is normalised on receipt so the frontend can render it idempotently across reconnects. `normalizeRewardStagingPayload`
performs a deep clone of the staging buckets, normalises each `preview` block, and keeps the UI resilient when the backend omits
buckets from incremental responses.【F:frontend/src/lib/utils/rewardStagingPayload.js†L1-L61】 The formatter then converts preview
stats into readable labels (`Attack`, `Crit Rate`, etc.), handles stack math, and renders per-target banners before the confirm
controls.【F:frontend/src/lib/utils/rewardPreviewFormatter.js†L1-L129】【F:frontend/src/lib/utils/rewardPreviewFormatter.js†L144-L200】

Backends populating previews should leverage `autofighter.reward_preview.build_preview_from_effects` or return a custom payload
with `summary`, `stats`, and `triggers`. `merge_preview_payload` fills in any missing fields from the staged plugin's `effects`
dict so reconnects and automation observe the same description every time.【F:backend/autofighter/reward_preview.py†L55-L189】【F:backend/services/reward_service.py†L42-L169】

Worked examples for authors live alongside the battle endpoint payload reference; card and relic contributors should review that
document before overriding `build_preview`. The Task Master board links this overlay to the preview schema work so the docs stay
aligned with `b30ad6a1-reward-preview-schema.md` (backend) and `f2622706-reward-preview-frontend.md` (frontend).

Screenshot references:

- Card preview — see `.codex/screenshots/reward-overlay-card-preview.png`.
- Relic preview — see `.codex/screenshots/reward-overlay-relic-preview.png`.

## Testing
- `bun test frontend/tests/rewardoverlay.test.js`

## Visual notes
- Card/relic artwork now renders at full opacity. Heavy darkening over the glyph image was removed from `CardArt.svelte` to avoid the gray overlay appearance while keeping a subtle highlight and border twinkles.
