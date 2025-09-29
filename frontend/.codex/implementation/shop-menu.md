# Shop Menu

`ShopMenu.svelte` renders the shop carousel used in combat rooms. Cards and relics
are enriched with catalog metadata, organized into a visible wheel, and surfaced
with price and tax summaries. Players can queue one or more items via the
"Add to list" buttons and submit the group with **Buy Selected**, which marks
items as sold and dispatches purchase payloads to the overlay host.

Double-clicking any visible slot now triggers an immediate purchase for that
entry when it is still available. The handler is suppressed while buys are
processing or when the item has already been sold/disabled so the gesture does
not interfere with the existing single-click selection controls.
