# Playable Web Flow

The Svelte frontend starts a run by calling the Quart backend's `/run/start`
endpoint with the selected party. The backend creates a run in the encrypted
`save.db` (path set by `AF_DB_PATH` and key from `AF_DB_KEY` or
`AF_DB_PASSWORD`) and returns a `run_id` with the initial map layout.

After confirming the lineup in a modal PartyPicker, the client immediately
switches to the map view showing upcoming rooms. The confirmation buttons sit in a stained-glass row so they match other UI controls. A matching stained-glass bar in the top-left now provides quick navigation: the diamond icon returns home, the user icon opens the Character Editor, the cog opens Settings, and the arrow steps back to the prior view. Players can reopen the map at
any time via the **Map** button, which fetches the latest floor state and
renders nodes in `MapDisplay.svelte` with the boss at the top, the current room highlighted at the bottom, and future rooms grayed out. The **Edit** button loads the player's
configuration and opens `PlayerEditor` so pronouns, damage type, and starting
stats can be adjusted outside a run. The **Pulls** menu opens a gacha panel that
shares pity and upgrade-item currency with other pull sources. The **Craft** menu
lists upgrade items, calls `/gacha/craft` to convert materials, and toggles
auto-crafting. Selecting a room posts `{ "action": "" }` to the matching
endpoint (`/rooms/{run_id}/battle`, `/shop`, or `/boss`) and the map
refreshes from the backend to reflect progress. Rooms without dedicated routes
can call `/rooms/{run_id}/{room_id}/action`, which simply echoes the provided
`action`. The backend auto-resolves fights
until either the party or the foe falls, handling passives, cards, relics, and
status-effect ticks before returning updated party stats, card choices, and
foes. When `card_choices` are present, `OverlayHost` opens a reward overlay so
players can pick one option before advancing.

Every menu opener checks `/map/{run_id}` for an active `battle` flag. When a
fight is running, the Settings and Inventory menus remain accessible and a placeholder
message covers the viewport until combat finishes.

This minimal loop lets the web build start a run, navigate the floor, and
trigger room logic while persisting state between HTTP calls and sessions.
