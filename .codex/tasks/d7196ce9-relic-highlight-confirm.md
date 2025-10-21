# Mirror relic highlight & confirm interactions

## Summary
Apply the refreshed highlight, wiggle, and confirm flow to relic rewards, including reset handling when the backend cancels or modifies the selection.

## Requirements
- Reuse the shared animation tokens and confirm button styling from the card phase for relic tiles.
- Ensure backend-driven reset/cancel events clear the highlight, stop animations, and hide the confirm button until a new relic is selected.
- Support keyboard focus traversal between relic tiles and the confirm button, ensuring focus returns to the tile grid after confirmation.
- Wire relic confirms into the overlay controller advance hooks so subsequent phases trigger reliably.
- Provide regression tests covering reset flows and double-confirm guards.

## Coordination notes
- Verify with backend maintainers whether relic rewards can be absent or multi-select; adapt the UI accordingly.
- Share any additional ARIA labels or accessibility copy updates with the accessibility-focused task owner.
ready for review
