# Pulls Menu

The `PullsMenu.svelte` component lets players spend gacha tickets. It shows
current pity and ticket counts and provides buttons for one, five, or ten
pulls. Each button disables when the player lacks enough tickets. After a
successful pull it opens `PullResultsOverlay.svelte`, which queues the
returned items and reveals them one at a time. The menu remembers the last
selected banner via `localStorage` when available, gracefully skipping
persistence if storage access is blocked. On reload, the banner is restored if
possible; if that banner is no longer available, the first available banner is
selected instead.
