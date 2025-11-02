# Main Menu

The main menu uses a Lucide-driven action column anchored to the right side of the viewport. Buttons are rendered by
`RunButtons.svelte`, which exposes a single ordered list of actions rather than the legacy 2×3 grid.

## Layout
- Primary actions (Run, Warp, Inventory, Battle Review, Guidebook, Settings) should appear in that order with consistent spacing
  and keyboard navigation. The Run entry remains first so players immediately start or resume runs.
- Append Feedback, Discord, and Website quick links after the primary actions. They open external tabs and must remain visually
  distinct as secondary entries.
- The PartyPicker panel stays on the left alongside the viewport banner; editing the lineup only happens inside the Run flow and
  no longer has a dedicated main-menu button.
- The PartyPicker overlay keeps the roster column as the sole scrollable region. The glass panel itself stays fixed height, and
  gradient fades appear when the roster overflows to hint that more heroes are available off-screen.
- Leave room for the Daily Login Rewards banner above the panel stack.
- Keep Lucide icons at 48px with text labels below for readability across desktop and tablet breakpoints.

## Navigation
- Highlight the focused item with the same glassmorphism hover state used elsewhere in the UI.
- Ensure keyboard focus order follows the list order and wraps predictably when navigating with a gamepad.

## Background
- Maintain the drifting glass background so icons stand out while the viewport renders behind the overlay.
