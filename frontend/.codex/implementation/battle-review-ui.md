# Battle Review Icon Layout

The Battle Review interface uses a vertical icon column and a persistent side panel:

- Navigation icons appear in a left-side column. The overview uses a Swords icon, while party and foe entries show their portraits.
- Foe tabs keep the label to the foe's name; rank badges render inside the portrait via `LegacyFighterPortrait` while the tab's aria-label still includes the rank for screen readers.
- Selecting an icon swaps the main content without hiding statistics; the right-side stats panel updates for the active entry.
- `.battle-review-tabs` arranges three columns: `icon-column`, `content-area`, and `stats-panel`.
- `.icon-btn` provides a square click target with hover and active states.
- The stats panel hosts the `entity-stats-grid`, ensuring key metrics stay visible during navigation.
- Colors should match the UI's stained-glass palette, using vibrant hues such as those returned by `getElementBarColor` in `frontend/src/lib/BattleReview.svelte`.
- The overview and entity panels surface detailed metrics like kills, DoT kills, ultimates used or failed, resources spent and gained, and healing prevented.
- Damage graphs, reward lists, and the overlay wrapper are provided by subcomponents in `components/battle-review/` (`DamageGraphs.svelte`, `RewardList.svelte`, `ReviewOverlay.svelte`).
