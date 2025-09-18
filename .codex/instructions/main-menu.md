# Main Menu

The main menu uses an Arknights-style grid of large [Lucide](https://lucide.dev) icons with matching text labels.

## Layout
- Arrange buttons in a 2×3 grid anchored near the bottom edge.
- Provide icons and labels for **Run**, **Map**, **Party**, **Edit**, **Pulls**, **Craft**, **Settings**, **Feedback**, and **Stats**.
- Reserve space for a centered banner above the grid and a top bar displaying the player avatar, name, and currencies.
- The centered banner now hosts the **Daily Login Rewards** panel. It should
  fetch `/rewards/login` on load, highlight the active streak day, and offer a
  claim button wired to `POST /rewards/login/claim` once the three-room
  requirement is fulfilled.
- Place quick-access corner icons (notifications, mail, etc.) away from main content.
- Show a short tooltip on hover repeating each label for clarity.

## Give Feedback
- Include a **Give Feedback** button in the grid.
- Selecting it opens the user's browser to the `FEEDBACK_URL` constant in `src/lib/constants.js`, launching a pre-filled GitHub issue in a new tab.

## Navigation
- Highlight the focused icon and support keyboard or mouse selection.
- Ensure Lucide icons remain readable at large sizes across desktop and mobile resolutions.

## Background
- Fill the screen with slowly drifting, dark color clouds that subtly shift hues so icons stay legible.
