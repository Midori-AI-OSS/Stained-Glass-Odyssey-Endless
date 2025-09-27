# Shop auto-close reproduction log

Date: 2025-09-27
Target URL: http://192.168.10.27:59001/

Steps performed (automated via Playwright):
- Opened main menu
- Started run
- Picked reward card (Keen Goggles)
- Picked reward relic (Wooden Idol)
- Battle Review opened as expected
- Advanced through map until encountering a shop room
- Observed Shop overlay appear, then unexpectedly close and the UI returned to main battle/reward flow

Observed events (Playwright DOM watcher):
- shop-closed at 2025-09-27T07:20:37.236Z
- Last captured overlay heading: `Choose a Relic`

DOM snapshot snippets captured by the automated run (trimmed):

When loot selection opened:

```
<h3 class="...">Choose a Card</h3>
... buttons: Select card Keen Goggles, Spiked Shield, Sturdy Vest
Gold +19
Drops: Light Upgrade (1), Wind Upgrade (1), Wind Upgrade (1)
```

After selecting relic:

```
<h3 class="...">Battle Review</h3>
... Battle Timeline section present
Button: Next Room
```

Notes:
- Playwright screenshots timed out when attempting full-page PNG capture. The DOM snapshots and logs above show the shop overlay was removed and the Battle Review opened immediately after loot selection. This reproduces the 'shop appears then immediately closes and returns to main menu / battle review' behaviour.

Next recommended steps (in order):
1. Add temporary debug logging in frontend `OverlayHost.svelte` and ShopMenu to log open/close events (timestamp + room id + roomData.result) into console and backend when overlays open/close.
2. Inspect `ui` polling code on frontend (`uiApi`, `runState` store) to see if incoming UI state messages are setting room/result to `battle` or `boss` mistakenly after reward choice.
3. Instrument backend `rooms` utils to log when room transitions are emitted to the client around shops and reward selection.
4. Re-run Playwright to capture screenshots once logging is enabled.
