# Party UI Improvements

This release improves clarity and accessibility in the Party overlay:

- Selected members are highlighted by a subtle, element‑tinted sweep placed
  beneath row content (photo, name, type). The effect starts smoothly, runs at
  a slow, randomized pace, and respects Reduced Motion (animation disabled,
  faint static highlight remains).
- The roster list no longer renders gray side borders; the stats panel on the
  right now fills its column.
- The Stats panel displays HP as `current/max` to make HP investment visible.

Implementation details:

- `PartyRoster.svelte` sets `--el-color` per row and derives `--el-dark`,
  `--el-5darker`, and `--el-5lighter` for a smooth gradient. The animated
  background is applied via `::before` and transitions opacity on selection to
  avoid abrupt starts.
- `PartyPicker.svelte` loads `/players` metadata into
  `replaceCharacterMetadata()` so roster filtering and portrait rendering can
  rely on backend-provided `ui` flags (e.g., `non_selectable`, `portrait_pool`)
  instead of comparing raw ids.
- `PartyRoster.svelte` adds a header showing the number of selected party
  members (`X / 5`) and provides sorting controls for name, element, or id with
  an ascending/descending toggle. Selected members are always grouped at the
  top and sorted within their section.
- `PartyRoster.svelte` wraps roster rows in a flip transition group so items
  slide smoothly when their order changes. Choosing a character slides it out
  and back in from the left with an element‑colored sparkle trail that is
  skipped entirely when Reduced Motion is enabled.
- `PartyRoster.svelte` arms roster rows on the first tap/click. A follow-up tap
  (or a long-press) toggles party membership so players no longer have to
  perform three clicks to add/remove someone.
- `PartyPicker.svelte` propagates `reducedMotion` to the roster so the effect
  can be disabled via Settings.
- `StatTabs.svelte` uses flexible sizing so the panel fills its side and now
  surfaces a read-only stat summary alongside upgrade controls rather than
  embedding the inline Character Editor.
- The stat upgrade section pulls `/players/<id>/upgrade` to show remaining
  points, per-stat totals, and next costs, dispatches `open-upgrade-mode` /
  `close-upgrade-mode` events for `PartyPicker.svelte`, and issues upgrade
  requests through the API helper that lets the server determine point costs.
- `PartyPicker.svelte` tracks the preview pane mode in a local store. Upgrade
  interactions toggle an inline upgrade sheet, which bubbles events back to the
  overlay so stat spend requests can be handled alongside the existing upgrade
  panel.
- `PlayerPreview.svelte` renders both the portrait and the upgrade sheet. The
  upgrade sheet reuses damage-type colors/icons, respects Reduced Motion, and
  exposes `open-upgrade`, `close-upgrade`, and `request-upgrade` events for the
  picker to handle.

## Party seeding and hydration

- The root page now waits for `/players` roster metadata before seeding
  `selectedParty`. When metadata is available, the store keeps any persisted
  selections (with placeholder ids stripped) or falls back to the first
  selectable roster entry (preferring the main player).
- Placeholder ids such as `sample_player` are removed during hydration so saved
  runs created before this change still load cleanly. If no playable roster
  entries are returned, the UI leaves the party empty until the user chooses a
  lineup.
