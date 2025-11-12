# Task: Update Ryne's Character Appearance Description

## Background
Ryne Waters is a 6★ Oracle of Light character with an existing detailed `looks` field in `backend/plugins/characters/ryne.py` (lines 24-50+). The current description covers her youthful appearance, distinctive red hair, Oracle of Light attire, and twin daggers. This task updates that description with new visual direction provided by the project owner.

## Problem
The current `looks` description needs to be updated to reflect new character design direction or artistic refinement. The existing content provides detailed visual specifications but may need adjustment to align with updated visual references or narrative direction.

## Requested Changes
- Replace the existing `looks` field in `backend/plugins/characters/ryne.py` (starting at line 24) with the new description provided below.
- Ensure the new description maintains proper Python string formatting (triple-quoted string).
- Preserve all other character attributes (id, name, full_about, summarized_about, char_type, etc.) unchanged.
- The description should focus on Ryne's visual appearance, Oracle attire, and characteristic presence.

## New Looks Description
**[PLACEHOLDER - Project owner will provide the updated appearance description here]**

Replace the current `looks` field starting at line 24 with the provided description.

## Acceptance Criteria
- The `looks` field in `backend/plugins/characters/ryne.py` has been updated with the new description.
- The Python file syntax remains valid (no linting errors).
- All other character fields remain unchanged.
- The character still loads correctly in the game.
- Backend tests continue to pass without errors related to Ryne's definition.

## Files to Modify
- `backend/plugins/characters/ryne.py` - Update the `looks` field (line 24)

## Testing Notes
After updating:
```bash
cd backend
uv tool run ruff check backend/plugins/characters/ryne.py
uv run pytest tests/ -k ryne -v
```
