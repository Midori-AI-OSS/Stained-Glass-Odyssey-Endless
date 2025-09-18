Coder, expose login reward progress and claiming through backend APIs.

## Requirements
- Create an endpoint to fetch current streak length, today's reward items, and time until next reset.
- Provide an endpoint to claim the day's reward once eligible.
- Enforce the 3-room completion requirement before allowing claims.
- Reset streak and rewards if claim occurs after daily deadline.
- Return reward details for frontend display (item names, star ratings, damage types).

## Notes
- Ensure endpoints integrate with authentication and existing backend framework.
- Use PT for reset timers to match backend streak logic.

task ready for review
